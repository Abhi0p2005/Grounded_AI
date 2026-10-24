"""Chat endpoint."""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agent.simple_rag import simple_rag_answer
from app.db import get_db
from app.models import Workspace
from app.schemas import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/{slug}/chat", response_model=ChatResponse)
def chat(slug: str, request: ChatRequest, db: Session = Depends(get_db)):
    """
    Chat with the workspace assistant.
    
    Args:
        slug: Workspace slug
        request: Chat request with message and history
        
    Returns:
        Chat response with answer, citations, flags, etc.
    """
    # Verify workspace exists
    workspace = db.query(Workspace).filter(Workspace.slug == slug).first()
    if not workspace:
        raise HTTPException(status_code=404, detail=f"Workspace not found: {slug}")
    
    # Get answer using simple RAG
    try:
        result = simple_rag_answer(slug, request.message)
        
        return ChatResponse(
            answer=result["answer"],
            refused=result["refused"],
            refusal_reason=result.get("refusal_reason"),
            route=result.get("route"),
            citations=result.get("citations", []),
            tool_calls=result.get("tool_calls", []),
            flags=result.get("flags", []),
            cache_hit=result.get("cache_hit", False),
            latency_ms=result.get("latency_ms", 0),
        )
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")
