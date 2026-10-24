"""Vector search and retrieval."""
import logging
from typing import List

from sqlalchemy import text

from app.core.embeddings import get_embedding_model
from app.db import db_session
from app.models import Chunk, Document

logger = logging.getLogger(__name__)


class RetrievedChunk:
    """Retrieved chunk with metadata."""
    
    def __init__(self, chunk_id: int, text: str, document: str, page: int, score: float, chunk_index: int):
        self.id = chunk_id
        self.text = text
        self.document = document
        self.page = page
        self.score = score
        self.chunk_index = chunk_index


def search(workspace_id: int, query: str, k: int = 5) -> List[RetrievedChunk]:
    """
    Search for relevant chunks using vector similarity.
    
    Args:
        workspace_id: Workspace ID (MANDATORY - enforces isolation)
        query: Search query
        k: Number of results to return
        
    Returns:
        List of RetrievedChunk objects, sorted by score descending
    """
    # Embed the query
    embedding_model = get_embedding_model()
    query_embedding = embedding_model.encode_query(query)
    
    # Query database with pgvector cosine similarity
    # similarity = 1 - cosine_distance
    with db_session() as db:
        sql = text("""
            SELECT 
                c.id,
                c.text,
                c.page_number,
                c.chunk_index,
                d.filename,
                1 - (c.embedding <=> :query_vec) AS score
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE c.workspace_id = :workspace_id
            ORDER BY c.embedding <=> :query_vec
            LIMIT :k
        """)
        
        result = db.execute(
            sql,
            {
                "workspace_id": workspace_id,
                "query_vec": str(query_embedding),
                "k": k,
            }
        )
        
        rows = result.fetchall()
        
        retrieved = []
        for row in rows:
            chunk = RetrievedChunk(
                chunk_id=row[0],
                text=row[1],
                page=row[2],
                chunk_index=row[3],
                document=row[4],
                score=float(row[5]),
            )
            retrieved.append(chunk)
        
        logger.info(f"Retrieved {len(retrieved)} chunks for workspace {workspace_id}")
        if retrieved:
            logger.debug(f"Top score: {retrieved[0].score:.3f}")
        
        return retrieved
