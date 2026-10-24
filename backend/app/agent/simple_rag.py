"""Simple RAG implementation without full agent graph (MVP)."""
import json
import logging
import re
from typing import Dict, List, Optional

from app.core.llm import LLMClient, LLMUnavailable
from app.core.workspace_config import load_guardrails_config, load_workspace_config
from app.db import db_session
from app.models import Workspace
from app.retrieval.confidence import is_confident
from app.retrieval.vector_search import search

from . import prompts

logger = logging.getLogger(__name__)


def verify_citations(cited_ids: List[int], retrieved_ids: List[int]) -> tuple[List[int], bool]:
    """
    Verify that cited chunk IDs were actually retrieved.
    
    Returns:
        (valid_ids, had_invalid)
    """
    valid_ids = [cid for cid in cited_ids if cid in retrieved_ids]
    had_invalid = len(valid_ids) < len(cited_ids)
    return valid_ids, had_invalid


def mask_pii_simple(text: str, patterns: Dict[str, str]) -> tuple[str, List[str]]:
    """
    Simple PII masking.
    
    Returns:
        (masked_text, detected_types)
    """
    masked = text
    detected = []
    
    for name, pattern in patterns.items():
        if re.search(pattern, masked):
            masked = re.sub(pattern, f"[{name.upper()}_MASKED]", masked)
            detected.append(f"pii:{name}")
    
    return masked, detected


def check_blocked_topics(text: str, blocked: List[str]) -> Optional[str]:
    """Check if text contains blocked topics."""
    text_lower = text.lower()
    for topic in blocked:
        if topic.lower() in text_lower:
            return topic
    return None


def check_injection_heuristics(text: str, patterns: List[str]) -> bool:
    """Check for prompt injection attempts."""
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def simple_rag_answer(workspace_slug: str, question: str) -> Dict:
    """
    Simple RAG answer without full agent graph.
    
    This is a minimal MVP implementation for Phase 1.
    """
    import time
    start_time = time.time()
    
    flags = []
    
    try:
        # Load configs
        ws_config = load_workspace_config(workspace_slug)
        gr_config = load_guardrails_config(workspace_slug)
        
        # Get workspace from DB
        with db_session() as db:
            workspace = db.query(Workspace).filter(Workspace.slug == workspace_slug).first()
            if not workspace:
                raise ValueError(f"Workspace not found: {workspace_slug}")
            workspace_id = workspace.id
        
        # Mask PII
        masked_question, pii_detected = mask_pii_simple(
            question,
            gr_config.pii.patterns if gr_config.pii.enabled else {}
        )
        flags.extend(pii_detected)
        
        # Input guardrails
        blocked_topic = check_blocked_topics(masked_question, gr_config.input.blocked_topics)
        if blocked_topic:
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "answer": ws_config.handoff_message,
                "refused": True,
                "refusal_reason": "blocked_topic",
                "route": None,
                "citations": [],
                "tool_calls": [],
                "flags": flags + ["blocked_topic"],
                "cache_hit": False,
                "latency_ms": latency_ms,
            }
        
        if check_injection_heuristics(masked_question, gr_config.input.injection_heuristics):
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "answer": "I can't help with that request.",
                "refused": True,
                "refusal_reason": "prompt_injection",
                "route": None,
                "citations": [],
                "tool_calls": [],
                "flags": flags + ["prompt_injection"],
                "cache_hit": False,
                "latency_ms": latency_ms,
            }
        
        # Retrieve chunks
        logger.info(f"Retrieving chunks for: {masked_question[:100]}")
        chunks = search(workspace_id, masked_question, k=ws_config.retrieval.top_k)
        
        if not chunks:
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "answer": "I couldn't find any relevant information in the documents.",
                "refused": True,
                "refusal_reason": "no_results",
                "route": "knowledge",
                "citations": [],
                "tool_calls": [],
                "flags": flags,
                "cache_hit": False,
                "latency_ms": latency_ms,
            }
        
        # Confidence check
        if not is_confident(chunks, ws_config.retrieval.min_score):
            top_docs = list(set([c.document for c in chunks[:2]]))
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "answer": f"I couldn't find this information with confidence in the documents. You might check: {', '.join(top_docs)}",
                "refused": True,
                "refusal_reason": "low_confidence",
                "route": "knowledge",
                "citations": [],
                "tool_calls": [],
                "flags": flags + ["low_confidence"],
                "cache_hit": False,
                "latency_ms": latency_ms,
            }
        
        # Build RAG prompt
        excerpts = ""
        retrieved_ids = []
        for i, chunk in enumerate(chunks):
            excerpts += f"\n[{i+1}] [chunk_id={chunk.id} | {chunk.document} p.{chunk.page}]\n{chunk.text[:500]}\n"
            retrieved_ids.append(chunk.id)
        
        rag_prompt_text = prompts.RAG_PROMPT.format(
            workspace_name=ws_config.name,
            assistant_persona=ws_config.assistant_persona,
            excerpts=excerpts,
            question=masked_question,
        )
        
        # Call LLM
        llm = LLMClient()
        messages = [{"role": "user", "content": rag_prompt_text}]
        
        try:
            response = llm.chat_json(messages)
        except LLMUnavailable as e:
            logger.error(f"LLM unavailable: {e}")
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "answer": gr_config.safe_fallback_message,
                "refused": True,
                "refusal_reason": "llm_unavailable",
                "route": "knowledge",
                "citations": [],
                "tool_calls": [],
                "flags": flags + ["llm_unavailable"],
                "cache_hit": False,
                "latency_ms": latency_ms,
            }
        
        # Extract response
        answer = response.get("answer", "")
        cited_ids = response.get("cited_chunk_ids", [])
        answerable = response.get("answerable", True)
        
        if not answerable:
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "answer": "I don't have enough information in the documents to answer that.",
                "refused": True,
                "refusal_reason": "llm_unanswerable",
                "route": "knowledge",
                "citations": [],
                "tool_calls": [],
                "flags": flags + ["llm_unanswerable"],
                "cache_hit": False,
                "latency_ms": latency_ms,
            }
        
        # Verify citations
        valid_ids, had_invalid = verify_citations(cited_ids, retrieved_ids)
        if had_invalid:
            flags.append("invalid_citation")
        
        if not valid_ids and gr_config.output.require_citation_for_knowledge:
            flags.append("no_valid_citation")
            answer = gr_config.safe_fallback_message
        
        # Build citations
        citations = []
        for chunk in chunks:
            if chunk.id in valid_ids:
                citations.append({
                    "chunk_id": chunk.id,
                    "document": chunk.document,
                    "page": chunk.page,
                    "score": chunk.score,
                    "snippet": chunk.text[:200],
                })
        
        # Check forbidden phrases
        for phrase in gr_config.output.forbidden_phrases:
            if phrase.lower() in answer.lower():
                flags.append(f"forbidden_phrase:{phrase}")
                answer = gr_config.safe_fallback_message
                break
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return {
            "answer": answer,
            "refused": False,
            "refusal_reason": None,
            "route": "knowledge",
            "citations": citations,
            "tool_calls": [],
            "flags": flags,
            "cache_hit": False,
            "latency_ms": latency_ms,
        }
        
    except Exception as e:
        logger.error(f"RAG error: {e}", exc_info=True)
        latency_ms = int((time.time() - start_time) * 1000)
        return {
            "answer": "An error occurred while processing your question.",
            "refused": True,
            "refusal_reason": "error",
            "route": None,
            "citations": [],
            "tool_calls": [],
            "flags": flags + [f"error:{type(e).__name__}"],
            "cache_hit": False,
            "latency_ms": latency_ms,
        }
