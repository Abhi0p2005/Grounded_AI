"""Text chunking with token-aware splitting."""
import logging
import re
from typing import List, Tuple

import tiktoken

logger = logging.getLogger(__name__)

# Use tiktoken for approximate token counting
try:
    tokenizer = tiktoken.get_encoding("cl100k_base")
except Exception:
    logger.warning("Failed to load tiktoken, using rough approximation")
    tokenizer = None


def count_tokens(text: str) -> int:
    """Count tokens in text."""
    if tokenizer:
        return len(tokenizer.encode(text))
    else:
        # Rough approximation: ~4 chars per token
        return len(text) // 4


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences (simple heuristic)."""
    # Split on period, exclamation, question mark followed by space
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


class ChunkInfo:
    """Information about a chunk."""
    
    def __init__(self, text: str, page_number: int, chunk_index: int, token_count: int):
        self.text = text
        self.page_number = page_number
        self.chunk_index = chunk_index
        self.token_count = token_count


def chunk_pages(
    pages: List[Tuple[int, str]],
    target_tokens: int = 500,
    overlap_tokens: int = 80
) -> List[ChunkInfo]:
    """
    Chunk pages into smaller pieces with overlap.
    
    Args:
        pages: List of (page_number, text) tuples
        target_tokens: Target size for each chunk
        overlap_tokens: Number of tokens to overlap between chunks
        
    Returns:
        List of ChunkInfo objects
        
    Notes:
        - Tries to split on sentence boundaries
        - Deterministic output for same input
        - No empty chunks produced
        - Page number = page where chunk starts
    """
    chunks = []
    chunk_index = 0
    
    for page_num, page_text in pages:
        sentences = split_into_sentences(page_text)
        
        current_chunk = []
        current_tokens = 0
        
        for sentence in sentences:
            sentence_tokens = count_tokens(sentence)
            
            # If single sentence exceeds target, add it as its own chunk
            if sentence_tokens > target_tokens and not current_chunk:
                chunk_text = sentence
                token_count = sentence_tokens
                chunks.append(ChunkInfo(chunk_text, page_num, chunk_index, token_count))
                chunk_index += 1
                continue
            
            # If adding this sentence exceeds target, finalize current chunk
            if current_tokens + sentence_tokens > target_tokens and current_chunk:
                chunk_text = " ".join(current_chunk)
                token_count = count_tokens(chunk_text)
                chunks.append(ChunkInfo(chunk_text, page_num, chunk_index, token_count))
                chunk_index += 1
                
                # Keep last few sentences for overlap
                overlap_sentences = []
                overlap_token_count = 0
                for s in reversed(current_chunk):
                    s_tokens = count_tokens(s)
                    if overlap_token_count + s_tokens <= overlap_tokens:
                        overlap_sentences.insert(0, s)
                        overlap_token_count += s_tokens
                    else:
                        break
                
                current_chunk = overlap_sentences
                current_tokens = overlap_token_count
            
            current_chunk.append(sentence)
            current_tokens += sentence_tokens
        
        # Add remaining chunk for this page
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            token_count = count_tokens(chunk_text)
            chunks.append(ChunkInfo(chunk_text, page_num, chunk_index, token_count))
            chunk_index += 1
    
    logger.info(f"Created {len(chunks)} chunks from {len(pages)} pages")
    return chunks
