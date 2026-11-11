"""Evaluation module for RAG pipeline metrics.

Implements retrieval and generation quality metrics:
- Recall@K
- MRR (Mean Reciprocal Rank)
- Context precision/recall
- Faithfulness
- Answer relevancy
- Citation correctness
"""
from .metrics import RetrievalMetrics, GenerationMetrics
from .evaluator import RAGEvaluator

__all__ = ["RetrievalMetrics", "GenerationMetrics", "RAGEvaluator"]
