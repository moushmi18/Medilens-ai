"""BM25 retrieval for hybrid search.

Implements BM25 ranking for keyword-based retrieval.
"""
import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import List, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class BM25Document:
    """Document for BM25 indexing."""
    id: str
    text: str
    metadata: dict | None = None


class BM25Index:
    """BM25 index for keyword retrieval."""
    
    def __init__(
        self,
        k1: float = 1.5,
        b: float = 0.75,
    ):
        self.k1 = k1
        self.b = b
        self.documents: List[BM25Document] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_length: float = 0.0
        self.term_doc_freqs: dict[str, int] = {}
        self.doc_term_freqs: List[dict[str, int]] = []
        self.corpus_size: int = 0
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization: lowercase, alphanumeric only."""
        text = text.lower()
        tokens = re.findall(r'\b[a-z0-9]+\b', text)
        return tokens
    
    def add_documents(self, documents: List[BM25Document]) -> None:
        """Add documents to the index."""
        for doc in documents:
            tokens = self._tokenize(doc.text)
            term_freqs = Counter(tokens)
            
            self.documents.append(doc)
            self.doc_lengths.append(len(tokens))
            self.doc_term_freqs.append(dict(term_freqs))
            
            for term in set(tokens):
                self.term_doc_freqs[term] = self.term_doc_freqs.get(term, 0) + 1
        
        self.corpus_size = len(self.documents)
        self.avg_doc_length = sum(self.doc_lengths) / max(1, self.corpus_size)
        
        logger.debug("bm25_documents_added", count=len(documents))
    
    def _idf(self, term: str) -> float:
        """Calculate inverse document frequency."""
        doc_freq = self.term_doc_freqs.get(term, 0)
        if doc_freq == 0:
            return 0.0
        return math.log((self.corpus_size - doc_freq + 0.5) / (doc_freq + 0.5) + 1)
    
    def _score_document(self, query_terms: List[str], doc_idx: int) -> float:
        """Calculate BM25 score for a single document."""
        score = 0.0
        doc_length = self.doc_lengths[doc_idx]
        term_freqs = self.doc_term_freqs[doc_idx]
        
        for term in query_terms:
            if term not in term_freqs:
                continue
            
            tf = term_freqs[term]
            idf = self._idf(term)
            
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_length / self.avg_doc_length)
            
            score += idf * (numerator / denominator)
        
        return score
    
    def search(
        self,
        query: str,
        limit: int = 10,
        score_threshold: float = 0.0,
    ) -> List[tuple[BM25Document, float]]:
        """Search for documents matching query.
        
        Args:
            query: Search query
            limit: Max results
            score_threshold: Minimum score
            
        Returns:
            List of (document, score) tuples
        """
        if not self.documents:
            return []
        
        query_terms = self._tokenize(query)
        if not query_terms:
            return []
        
        scores = []
        for idx in range(len(self.documents)):
            score = self._score_document(query_terms, idx)
            if score > score_threshold:
                scores.append((self.documents[idx], score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return scores[:limit]


def reciprocal_rank_fusion(
    rankings: List[List[tuple[str, float]]],
    k: int = 60,
) -> List[tuple[str, float]]:
    """Combine multiple rankings using Reciprocal Rank Fusion.
    
    Args:
        rankings: List of rankings, each is list of (doc_id, score)
        k: RRF parameter (default 60)
        
    Returns:
        Fused ranking as list of (doc_id, rrf_score)
    """
    rrf_scores: dict[str, float] = {}
    
    for ranking in rankings:
        for rank, (doc_id, _) in enumerate(ranking, start=1):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1 / (k + rank)
    
    fused = [(doc_id, score) for doc_id, score in rrf_scores.items()]
    fused.sort(key=lambda x: x[1], reverse=True)
    
    return fused
