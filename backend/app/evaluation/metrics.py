"""Evaluation metrics for RAG pipeline."""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RetrievalMetrics:
    """Metrics for retrieval quality."""
    
    recall_at_k: dict[int, float] = field(default_factory=dict)
    mrr: float = 0.0
    context_precision: float = 0.0
    context_recall: float = 0.0
    hit_rate: float = 0.0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "recall_at_k": self.recall_at_k,
            "mrr": self.mrr,
            "context_precision": self.context_precision,
            "context_recall": self.context_recall,
            "hit_rate": self.hit_rate,
        }


@dataclass
class GenerationMetrics:
    """Metrics for generation quality."""
    
    faithfulness: float = 0.0
    answer_relevancy: float = 0.0
    citation_correctness: float = 0.0
    safety_compliance: float = 0.0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "faithfulness": self.faithfulness,
            "answer_relevancy": self.answer_relevancy,
            "citation_correctness": self.citation_correctness,
            "safety_compliance": self.safety_compliance,
        }


def calculate_recall_at_k(
    retrieved_ids: list[str],
    relevant_ids: set[str],
    k: int,
) -> float:
    """Calculate Recall@K.
    
    Args:
        retrieved_ids: List of retrieved document IDs in order
        relevant_ids: Set of relevant document IDs
        k: Number of top results to consider
        
    Returns:
        Recall@K score (0.0 to 1.0)
    """
    if not relevant_ids:
        return 0.0
    
    retrieved_at_k = set(retrieved_ids[:k])
    hits = retrieved_at_k & relevant_ids
    
    return len(hits) / len(relevant_ids)


def calculate_mrr(
    retrieved_ids: list[str],
    relevant_ids: set[str],
) -> float:
    """Calculate Mean Reciprocal Rank.
    
    Args:
        retrieved_ids: List of retrieved document IDs in order
        relevant_ids: Set of relevant document IDs
        
    Returns:
        MRR score (0.0 to 1.0)
    """
    for rank, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in relevant_ids:
            return 1.0 / rank
    return 0.0


def calculate_hit_rate(
    retrieved_ids: list[str],
    relevant_ids: set[str],
) -> float:
    """Calculate hit rate (whether any relevant doc was retrieved).
    
    Args:
        retrieved_ids: List of retrieved document IDs
        relevant_ids: Set of relevant document IDs
        
    Returns:
        1.0 if any relevant doc found, 0.0 otherwise
    """
    return 1.0 if set(retrieved_ids) & relevant_ids else 0.0


def calculate_context_precision(
    retrieved_ids: list[str],
    relevant_ids: set[str],
) -> float:
    """Calculate precision of retrieved context.
    
    Args:
        retrieved_ids: List of retrieved document IDs
        relevant_ids: Set of relevant document IDs
        
    Returns:
        Precision score (0.0 to 1.0)
    """
    if not retrieved_ids:
        return 0.0
    
    hits = set(retrieved_ids) & relevant_ids
    return len(hits) / len(retrieved_ids)


def calculate_citation_correctness(
    cited_sources: list[str],
    answer_text: str,
    source_contents: dict[str, str],
) -> float:
    """Calculate whether citations support claims in the answer.
    
    This is a simplified heuristic check - for production,
    consider using an LLM judge.
    
    Args:
        cited_sources: List of cited source URLs
        answer_text: Generated answer text
        source_contents: Map of source URL to content
        
    Returns:
        Citation correctness score (0.0 to 1.0)
    """
    if not cited_sources:
        return 0.0
    
    answer_words = set(answer_text.lower().split())
    
    overlap_scores = []
    for source_url in cited_sources:
        content = source_contents.get(source_url, "")
        if not content:
            overlap_scores.append(0.0)
            continue
        
        source_words = set(content.lower().split())
        overlap = answer_words & source_words
        
        if answer_words:
            overlap_scores.append(len(overlap) / len(answer_words))
        else:
            overlap_scores.append(0.0)
    
    return sum(overlap_scores) / len(overlap_scores) if overlap_scores else 0.0
