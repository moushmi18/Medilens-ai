# MediLens AI - Development Roadmap

## Overview

MediLens AI is built in 12 phases. Status below reflects what is **actually implemented and verified** in this repository (educational build; no real patient data).

---

## Phase Summary

| Phase | Name | Status | Notes |
|-------|------|--------|-------|
| 1 | Project Initialization | Complete | Vite/React + FastAPI scaffold, health checks |
| 2 | Database & Auth | Complete | Postgres schema, JWT auth, Qdrant collections |
| 3 | Upload & Parsing | Complete | PDF/DOCX/image; **PaddleOCR primary**, Tesseract fallback |
| 4 | Structured Extraction | Complete | Lab extraction + verification flags + report vector index |
| 5 | Knowledge Ingestion | Complete | Permitted sources; LlamaIndex chunking + curated sample docs |
| 6 | Basic RAG | Complete | Vector search + LLM provider interface (key optional) |
| 7 | Hybrid Retrieval | Complete | BM25 + RRF + BGE rerank + context-aware default |
| 8 | Safety & Citations | Complete | Intent/safety engine + disclaimer/citation helpers |
| 9 | Chat Frontend | Complete | Chat UI + streaming endpoint + conversation CRUD |
| 10 | Comparison & Summary | Complete | Recharts compare, PDF summary, privacy center |
| 11 | Evaluation & Testing | Complete* | 50Q dataset + scripts; *LLM/RAGAS metrics NOT RUN without key |
| 12 | Docs & Verification | Complete* | Local direct services (no Docker in this env); bundle + screenshots |

---

## Remaining / Partial Items (honest)

- **LLM generation metrics (RAGAS faithfulness / answer relevancy / citation correctness):** NOT RUN — no `OPENAI_API_KEY` in this environment.
- **Automatic retention purge jobs:** retention preference is stored (`PUT /api/privacy/retention`); scheduled purge is not implemented.
- **Settings notification toggles:** stored in browser `localStorage`, not a full server preferences API.
- **Celery scheduled knowledge refresh:** Celery app exists; scheduled production refresh is not required for the educational slice.
- **Admin audit log UI:** `audit_logs` table exists; no admin UI shipped.

---

## Detailed Deliverables (implemented)

### Phase 1–2
- [x] Architecture + roadmap docs, folder structure
- [x] Frontend shell (11 routes), typed API client
- [x] FastAPI health `/api/health`, `/api/health/ready`
- [x] Postgres tables + Alembic; JWT register/login/refresh/me/logout
- [x] Qdrant `trusted_knowledge` + `user_reports`

### Phase 3–4
- [x] Upload validation, duplicate hash, report list/get/status/delete
- [x] PaddleOCR primary + Tesseract fallback
- [x] Extraction + process/results/verify endpoints
- [x] Report text indexed into `user_reports` on process

### Phase 5–8
- [x] Knowledge ingestion from permitted sources only
- [x] LlamaIndex document processor used in ingestion path
- [x] Basic + hybrid + hybrid+rerank + context-aware retrieval
- [x] Safety engine + educational constraints (no diagnose/prescribe)

### Phase 9–10
- [x] Chat + streaming + conversations
- [x] `POST /api/feedback`, `GET /api/dashboard`
- [x] Compare + doctor summary PDF
- [x] Privacy delete reports (vectors removed) + conversations + retention API

### Phase 11–12
- [x] 50+ synthetic eval questions + runnable evaluation script
- [x] Committed `backend/evaluation_results.json` with non-LLM metrics
- [x] Sample synthetic reports + curated knowledge JSON
- [x] Deployment docs for local/direct services and Docker Compose option
- [x] End-to-end verification artifacts under `/opt/cursor/artifacts/`
