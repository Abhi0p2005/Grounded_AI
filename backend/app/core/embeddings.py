"""Embedding model singleton for vector generation."""
import logging
from typing import List

from sentence_transformers import SentenceTransformer

from app.settings import settings

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """Singleton embedding model."""
    
    _instance = None
    _model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._model is None:
            logger.info(f"Loading embedding model: {settings.embedding_model}")
            self._model = SentenceTransformer(settings.embedding_model)
            logger.info(f"Embedding model loaded (dim={settings.embedding_dim})")
    
    def encode_documents(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Encode documents (no prefix for MiniLM).
        
        Args:
            texts: List of text strings to encode
            batch_size: Batch size for encoding
            
        Returns:
            List of embedding vectors
        """
        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return embeddings.tolist()
    
    def encode_query(self, query: str) -> List[float]:
        """
        Encode a search query.
        
        For some models like BGE, queries should be prefixed.
        For MiniLM, no prefix needed.
        
        Args:
            query: Query string
            
        Returns:
            Embedding vector
        """
        # Add prefix for BGE models
        if "bge" in settings.embedding_model.lower():
            query = f"Represent this sentence for searching relevant passages: {query}"
        
        embedding = self._model.encode(
            query,
            convert_to_numpy=True,
        )
        return embedding.tolist()


# Global instance
_embedding_model = None


def get_embedding_model() -> EmbeddingModel:
    """Get the global embedding model instance."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = EmbeddingModel()
    return _embedding_model
