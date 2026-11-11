# RAG Module

RAG pipeline orchestration and generation.

## Components (Phase 6-8)

- `pipeline.py` - Main 16-step RAG pipeline
- `query_processor.py` - Query classification and rewriting
- `context_builder.py` - Context assembly from retrieved docs
- `generator.py` - LLM generation with OpenAI
- `citation_validator.py` - Citation verification
- `response_formatter.py` - Output formatting with source separation
