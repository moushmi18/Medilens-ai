"""RAG (Retrieval-Augmented Generation) module.

Implements the 16-step RAG pipeline from ARCHITECTURE.md:
1. Query received
2. Intent classification
3. Safety check
4. Query embedding
5. Vector search (trusted knowledge)
6. Vector search (user reports - with strict isolation)
7. BM25 retrieval
8. RRF fusion
9. Cross-encoder reranking
10. Evidence sufficiency check
11. Context assembly
12. Prompt generation
13. LLM generation
14. Citation validation
15. Response formatting
16. Response logging
"""
from .retrieval import RetrievalService
from .pipeline import RAGPipeline

__all__ = ["RetrievalService", "RAGPipeline"]
