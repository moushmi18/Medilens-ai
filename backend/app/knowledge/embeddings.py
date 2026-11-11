"""Embedding service using sentence-transformers.

Uses BGE-small-en-v1.5 (384 dimensions) as specified in ARCHITECTURE.md.
"""
from typing import List

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIM = 384


class EmbeddingService:
    """Service for generating embeddings from text."""
    
    _model = None
    
    def __init__(self):
        self.model_name = EMBEDDING_MODEL
        self.dimension = EMBEDDING_DIM
    
    @classmethod
    def get_model(cls):
        """Lazy load embedding model."""
        if cls._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                cls._model = SentenceTransformer(EMBEDDING_MODEL)
                logger.info("embedding_model_loaded", model=EMBEDDING_MODEL)
            except ImportError:
                logger.warning("sentence_transformers not installed")
                raise RuntimeError(
                    "sentence-transformers is required for embeddings. "
                    "Install with: pip install sentence-transformers"
                )
        return cls._model
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats (384 dimensions)
        """
        model = self.get_model()
        embedding = model.encode(text, normalize_embeddings=True)
        return embedding.tolist()
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings (each 384 dimensions)
        """
        if not texts:
            return []
        
        model = self.get_model()
        embeddings = model.encode(texts, normalize_embeddings=True)
        
        logger.debug("texts_embedded", count=len(texts))
        return [emb.tolist() for emb in embeddings]
    
    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a search query.
        
        Uses query prefix for BGE models as recommended.
        
        Args:
            query: Search query
            
        Returns:
            Query embedding (384 dimensions)
        """
        prefixed_query = f"Represent this sentence for searching relevant passages: {query}"
        return self.embed_text(prefixed_query)
