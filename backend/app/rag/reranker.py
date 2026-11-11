"""Cross-encoder reranking for RAG.

Uses BGE reranker for more accurate relevance scoring.
"""
from dataclasses import dataclass
from typing import List, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)

RERANKER_MODEL = "BAAI/bge-reranker-base"


@dataclass
class RankedResult:
    """Result with reranker score."""
    id: str
    text: str
    original_score: float
    rerank_score: float
    metadata: dict | None = None


class CrossEncoderReranker:
    """Cross-encoder reranker using BGE model."""
    
    _model = None
    
    def __init__(self, model_name: str = RERANKER_MODEL):
        self.model_name = model_name
    
    @classmethod
    def get_model(cls, model_name: str):
        """Lazy load reranker model."""
        if cls._model is None:
            try:
                from sentence_transformers import CrossEncoder
                cls._model = CrossEncoder(model_name)
                logger.info("reranker_model_loaded", model=model_name)
            except ImportError:
                logger.warning("sentence_transformers not installed for reranking")
                return None
        return cls._model
    
    def rerank(
        self,
        query: str,
        results: List[tuple[str, str, float, dict | None]],
        top_k: int = 5,
    ) -> List[RankedResult]:
        """Rerank results using cross-encoder.
        
        Args:
            query: Search query
            results: List of (id, text, score, metadata) tuples
            top_k: Number of top results to return
            
        Returns:
            Reranked results
        """
        if not results:
            return []
        
        model = self.get_model(self.model_name)
        
        if model is None:
            logger.warning("reranker_unavailable_using_original_scores")
            return [
                RankedResult(
                    id=r[0],
                    text=r[1],
                    original_score=r[2],
                    rerank_score=r[2],
                    metadata=r[3],
                )
                for r in results[:top_k]
            ]
        
        pairs = [(query, r[1]) for r in results]
        
        try:
            scores = model.predict(pairs)
        except Exception as e:
            logger.error("reranking_failed", error=str(e))
            return [
                RankedResult(
                    id=r[0],
                    text=r[1],
                    original_score=r[2],
                    rerank_score=r[2],
                    metadata=r[3],
                )
                for r in results[:top_k]
            ]
        
        ranked = []
        for i, (id_, text, orig_score, meta) in enumerate(results):
            ranked.append(RankedResult(
                id=id_,
                text=text,
                original_score=orig_score,
                rerank_score=float(scores[i]),
                metadata=meta,
            ))
        
        ranked.sort(key=lambda x: x.rerank_score, reverse=True)
        
        logger.debug(
            "results_reranked",
            input_count=len(results),
            output_count=min(top_k, len(ranked)),
        )
        
        return ranked[:top_k]
