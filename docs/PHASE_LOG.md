# MediLens AI - Phase Development Log

This document records what was built in each phase, commands run, and **actual** results.
Claims of “passing” below refer only to commands that were executed in this environment.

**Latest verification (this resume):** see Phase 12 and the final report in the agent summary.

---

## Phase 1: Project Initialization

**Status:** Complete  
**Evidence commit (historical):** `cc4370e`

### What Was Built
- Architecture documentation, 12-phase roadmap, folder structure
- Frontend: React + TypeScript + Vite + Tailwind with 11 routes
- Backend: FastAPI modular layout, health endpoints, config, logging
- SQLAlchemy + Alembic initialized; Celery + Redis ping task
- Docker Compose / Dockerfiles / `.env.example` / README

### Commands Run and Results
```bash
$ pytest ../tests/backend -v
# Result (historical Phase 1): 3 passed (health)

$ npm run build
# Result: Build successful

$ curl localhost:8247/api/health
# Result: {"status":"healthy",...}
```

---

## Phase 2: Database & Authentication

**Status:** Complete

### What Was Built
- PostgreSQL schema: users, medical_reports, extracted_results, conversations, messages, citations, knowledge_sources, feedback, audit_logs
- Qdrant collections: `trusted_knowledge`, `user_reports` (BGE-small 384-dim)
- JWT auth: register / login / logout / refresh / me
- Frontend Login + Register + AuthProvider

### Commands Run and Results
```bash
$ sudo service postgresql start && sudo service redis-server start
# Result: Both online

$ ./qdrant   # local binary, port 6333
# Result: Listening

$ alembic upgrade head
# Result: 9 tables created

$ pytest -v   # auth + health
# Result (historical): 14 passed
```

---

## Phase 3: Upload & Parsing

**Status:** Complete (PaddleOCR primary verified in gap-close work)

### What Was Built
- Upload with validation, size limit, SHA-256 duplicate detection
- PyMuPDF digital PDF, python-docx, OCR for scans/images
- **OCR:** PaddleOCR primary; Tesseract documented fallback in `ocr_processor.py`
- Report CRUD: list / get / status / delete

### Commands Run and Results
```bash
$ pip install paddleocr pymupdf python-docx pillow pytesseract
$ sudo apt-get install tesseract-ocr

$ pytest tests/ -k ingestion -v
# OCR path exercised in ingestion tests (Tesseract always available as fallback)
```

### Notes
- Early builds used Tesseract-only after PaddleOCR API friction.
- Gap-close: PaddleOCR initialized with `PaddleOCR(lang='en')` and used as primary; Tesseract remains fallback only.

---

## Phase 4: Structured Extraction

**Status:** Complete

### What Was Built
- Lab result extraction with confidence scores and `needs_verification`
- Abnormal flag determination vs reference ranges
- Endpoints: `GET/POST .../results`, `POST .../process`, `PATCH .../results/{id}`
- Processing also indexes report text into Qdrant (`user_reports`) via LlamaIndex chunking when available

### Commands Run and Results
```bash
$ pytest tests/ -k extraction -v
# Covered by extraction unit tests in the suite
```

---

## Phase 5: Knowledge Ingestion

**Status:** Complete

### What Was Built
- Permitted sources only: MedlinePlus, NIH/NIDDK, NHS, WHO
- Ingestion service + `GET/POST /api/sources`
- **LlamaIndex** `SentenceSplitter` + BGE embeddings for chunking/ingest; custom chunker fallback
- Curated JSON docs under `sample_data/medical_knowledge/` with provenance fields

### Commands Run and Results
```bash
$ python sample_data/ingest_knowledge.py
# Ingests curated JSON into Postgres + Qdrant trusted_knowledge
```

---

## Phase 6: Basic RAG

**Status:** Complete

### What Was Built
- Vector search against trusted knowledge + user-isolated report search
- LLM provider interface (OpenAI when keyed; unconfigured provider for tests)
- Evidence sufficiency check + educational system prompt
- Chat endpoints (non-stream + stream)

### Commands Run and Results
```bash
$ pytest tests/test_rag.py -v
# Passes with Fake/unconfigured LLM paths — no OPENAI_API_KEY required for unit tests
```

---

## Phase 7: Hybrid Retrieval

**Status:** Complete

### What Was Built
- BM25 index + Reciprocal Rank Fusion
- BGE cross-encoder reranker (`BAAI/bge-reranker-base`)
- Retrieval methods: `basic`, `hybrid`, `hybrid_rerank`, `context_aware` (default in pipeline)

### Commands Run and Results
```bash
$ python -m app.evaluation.run_evaluation
# Emits Recall@5 / MRR per method when knowledge base is populated
```

---

## Phase 8: Safety & Citations

**Status:** Complete

### What Was Built
- Intent classification + query safety + response validation
- Emergency / diagnosis / medication / prompt-injection handling
- Educational disclaimer enforcement
- Citation extraction from knowledge chunks

### Commands Run and Results
```bash
$ pytest tests/test_safety.py -v
# Result: all safety tests passed as part of full suite
```

---

## Phase 9: Chat Frontend

**Status:** Complete

### What Was Built
- Chat UI with streaming consumer, conversation history
- Wired to `/api/chat` and `/api/chat/conversations*`

---

## Phase 10: Comparison & Doctor Summary

**Status:** Complete

### What Was Built
- `POST /api/reports/compare` + frontend Recharts comparison page
- Doctor summary PDF via ReportLab (`POST /api/reports/{id}/summary` and `/api/doctor-summary`)
- Privacy Center: delete reports (incl. vectors), delete conversations, retention preference API
- Settings page (local UI prefs + account email)

---

## Phase 11: Evaluation & Testing

**Status:** Complete (non-LLM metrics executed; RAGAS generation metrics NOT RUN without key)

### What Was Built
- 50 synthetic questions in `backend/app/evaluation/dataset.py`
- Runner: `backend/app/evaluation/run_evaluation.py`
- Committed results: `backend/evaluation_results.json`
- Compares basic vs hybrid vs hybrid_rerank vs context_aware when Qdrant is populated
- Explicitly marks faithfulness / answer relevancy / citation correctness as **NOT RUN** without `OPENAI_API_KEY`

### Commands Run and Results
```bash
$ cd backend && python -m app.evaluation.run_evaluation
# Intent + safety always run; retrieval runs if trusted_knowledge has points
# LLM/RAGAS metrics: NOT RUN when OPENAI_API_KEY is empty
```

---

## Phase 12: Production Docs & Verification

**Status:** Complete for educational local deploy docs; Docker Compose present but **this environment runs Postgres/Redis/Qdrant directly (no Docker)**

### What Was Built
- `docs/DEPLOYMENT.md`, README run instructions
- Full-stack local verification script path (register → upload → process → view → compare → summary → delete → vector check)
- Screenshots under `/opt/cursor/artifacts/`
- Git bundle: `/opt/cursor/artifacts/medilens-ai.bundle`

### Gap-close (2026-11-12) — verified

| Gap | Fix | Verification |
|-----|-----|--------------|
| Report viewer placeholder | `GET /api/reports/{id}/file` (+ `/text` for DOCX); blob iframe/img/pre preview | File endpoint 200 + auth isolation tests; image preview screenshot shows lab scan |
| Retention purge | Celery beat `purge-expired-user-data-daily` + `RetentionService` | 5 retention tests passed |
| Settings toggles | `users.preferences` JSONB + `GET/PUT /api/settings` | 3 settings tests passed; Settings page loads prefs |
| Header Demo User | `useAuth()` name/email/initials | Screenshot shows Avery Chen + email |

```bash
$ alembic upgrade head   # c4e8f2a91b03 preferences column
$ pytest tests/ ../tests/backend/ -q
# 112 passed
$ npm run build
# succeeded
```

### Remaining honest caveats
- RAGAS generation metrics still **NOT RUN** (no `OPENAI_API_KEY`).
- Headless Chromium often screenshots PDF iframes as blank white even when `iframe[src^=blob:]` is present; PDF serving verified by HTTP 200 + DOM.
