"""Confidence thresholding for retrieval."""
from typing import List

from app.retrieval.vector_search import RetrievedChunk


def is_confident(chunks: List[RetrievedChunk], min_score: float) -> bool:
    """
    Check if retrieval confidence meets threshold.
    
    Args:
        chunks: List of retrieved chunks
        min_score: Minimum similarity score threshold
        
    Returns:
        True if confident (top score >= min_score), False otherwise
    """
    if not chunks:
        return False
    
    return chunks[0].score >= min_score
