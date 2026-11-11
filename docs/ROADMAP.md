# MediLens AI - Development Roadmap

## Overview

MediLens AI is built in 12 phases, each adding functionality while preserving working features from previous phases.

---

## Phase Summary

| Phase | Name | Status | Description |
|-------|------|--------|-------------|
| 1 | Project Initialization | ✅ Complete | Frontend/backend setup, infrastructure, health checks |
| 2 | Database & Auth | ⏳ Pending | PostgreSQL schema, Qdrant setup, user authentication |
| 3 | Upload & Parsing | ⏳ Pending | File upload, PDF/image parsing, OCR |
| 4 | Structured Extraction | ⏳ Pending | Lab result extraction, verification flags |
| 5 | Knowledge Ingestion | ⏳ Pending | Trusted source ingestion pipeline |
| 6 | Basic RAG | ⏳ Pending | Vector search, basic retrieval, generation |
| 7 | Hybrid Retrieval | ⏳ Pending | BM25, RRF, cross-encoder reranking |
| 8 | Safety & Citations | ⏳ Pending | Safety engine, citation validation |
| 9 | Chat Frontend | ⏳ Pending | Full chat UI, streaming, history |
| 10 | Comparison & Summary | ⏳ Pending | Report comparison, doctor summary PDF |
| 11 | Evaluation & Testing | ⏳ Pending | RAGAS evaluation, safety tests |
| 12 | Production Deployment | ⏳ Pending | Docker deployment, documentation |

---

## Detailed Phase Descriptions

### Phase 1: Project Initialization ✅ Complete
**Status:** ✅ Complete

**Deliverables:**
- [x] Architecture documentation (docs/ARCHITECTURE.md)
- [x] Roadmap documentation (docs/ROADMAP.md)
- [x] Complete folder structure with README stubs
- [x] Frontend: Vite + React + TypeScript + Tailwind
  - [x] App shell with premium healthcare SaaS design
  - [x] React Router with 11 routes
  - [x] Typed Axios API client
  - [x] "Coming in Phase N" placeholder pages
- [x] Backend: FastAPI with modular layout
  - [x] Pydantic-settings configuration
  - [x] Structured logging
  - [x] CORS middleware
  - [x] Error handling middleware
  - [x] Health endpoints (/api/health, /api/health/ready)
- [x] Database setup
  - [x] SQLAlchemy initialization
  - [x] Alembic migrations initialized
- [x] Task queue setup
  - [x] Celery app with Redis
  - [x] Trivial ping task
- [x] Infrastructure
  - [x] Docker Compose configuration
  - [x] Dockerfiles for frontend and backend
  - [x] .env.example
  - [x] .gitignore
  - [x] README.md with setup instructions
- [x] Testing
  - [x] Pytest tests for health endpoints (3 tests passing)
  - [x] Frontend lint/typecheck/build passing

---

### Phase 2: Database & Authentication
**Status:** ⏳ Pending

**Deliverables:**
- [ ] PostgreSQL schema implementation
  - [ ] users table
  - [ ] All indexes
- [ ] Qdrant collections setup
  - [ ] trusted_knowledge collection
  - [ ] user_reports collection
- [ ] Authentication system
  - [ ] POST /api/auth/register
  - [ ] POST /api/auth/login
  - [ ] POST /api/auth/logout
  - [ ] POST /api/auth/refresh
  - [ ] GET /api/auth/me
  - [ ] JWT token handling
  - [ ] Password hashing with bcrypt
- [ ] Frontend auth pages
  - [ ] Login page (functional)
  - [ ] Register page (functional)
  - [ ] Auth context/state management
  - [ ] Protected route wrapper

---

### Phase 3: Upload & Parsing
**Status:** ⏳ Pending

**Deliverables:**
- [ ] Database tables
  - [ ] medical_reports table
- [ ] File upload system
  - [ ] POST /api/reports/upload
  - [ ] File validation (type, size)
  - [ ] Duplicate detection
  - [ ] Secure file storage
- [ ] Document parsing
  - [ ] PyMuPDF for digital PDFs
  - [ ] PaddleOCR for scanned documents
  - [ ] python-docx for Word files
- [ ] Celery tasks
  - [ ] process_document task
  - [ ] extract_text_from_pdf task
  - [ ] perform_ocr task
- [ ] Frontend upload page
  - [ ] Drag-and-drop interface
  - [ ] Upload progress
  - [ ] Status display
  - [ ] File preview

---

### Phase 4: Structured Extraction
**Status:** ⏳ Pending

**Deliverables:**
- [ ] Database tables
  - [ ] extracted_results table
- [ ] Extraction pipeline
  - [ ] Patient details extraction
  - [ ] Report metadata extraction
  - [ ] Lab result extraction
  - [ ] Reference range parsing
  - [ ] Confidence scoring
- [ ] Verification system
  - [ ] Flag uncertain OCR results
  - [ ] User verification interface
- [ ] API endpoints
  - [ ] GET /api/reports/{id}/results
  - [ ] PATCH /api/reports/{id}/results/{result_id} (verification)
- [ ] Frontend
  - [ ] Report viewer with extracted data
  - [ ] Verification UI for flagged values

---

### Phase 5: Knowledge Ingestion
**Status:** ⏳ Pending

**Deliverables:**
- [ ] Database tables
  - [ ] knowledge_sources table
- [ ] Ingestion pipeline
  - [ ] MedlinePlus ingestion
  - [ ] WHO ingestion
  - [ ] NHS ingestion
  - [ ] NIH ingestion
  - [ ] NIDDK ingestion
- [ ] Processing
  - [ ] Content parsing and cleaning
  - [ ] Semantic chunking
  - [ ] Metadata extraction
  - [ ] Deduplication
- [ ] Embedding and storage
  - [ ] BGE-small-en-v1.5 embeddings
  - [ ] Qdrant trusted_knowledge indexing
- [ ] Celery tasks
  - [ ] ingest_knowledge_source task
  - [ ] refresh_knowledge_base task (scheduled)
- [ ] API endpoints
  - [ ] GET /api/sources

---

### Phase 6: Basic RAG
**Status:** ⏳ Pending

**Deliverables:**
- [ ] Database tables
  - [ ] conversations table
  - [ ] messages table
  - [ ] citations table
- [ ] Report embeddings
  - [ ] Generate embeddings for processed reports
  - [ ] Store in user_reports collection
  - [ ] User isolation enforcement
- [ ] RAG pipeline (basic)
  - [ ] Query processing
  - [ ] Vector search (trusted_knowledge)
  - [ ] Vector search (user_reports with auth)
  - [ ] Context assembly
  - [ ] LLM generation (OpenAI)
- [ ] API endpoints
  - [ ] POST /api/chat (non-streaming first)
  - [ ] GET /api/conversations
  - [ ] GET /api/conversations/{id}

---

### Phase 7: Hybrid Retrieval
**Status:** ⏳ Pending

**Deliverables:**
- [ ] BM25 implementation
  - [ ] BM25 index for trusted_knowledge
  - [ ] BM25 index for user_reports
- [ ] Hybrid retrieval
  - [ ] Reciprocal Rank Fusion
  - [ ] Metadata filtering
- [ ] Reranking
  - [ ] BGE cross-encoder integration
  - [ ] Relevance score threshold
- [ ] Evidence sufficiency
  - [ ] Check before generation
  - [ ] Handle insufficient evidence gracefully

---

### Phase 8: Safety & Citations
**Status:** ⏳ Pending

**Deliverables:**
- [ ] Safety engine
  - [ ] Intent classification
  - [ ] Safety rule enforcement
  - [ ] Emergency detection
  - [ ] Prompt injection defense
- [ ] Citation validation
  - [ ] Verify all claims have sources
  - [ ] Link citations to retrieved chunks
- [ ] Response formatting
  - [ ] Separate report facts / knowledge / uncertainty
  - [ ] Add appropriate disclaimers (not as substitute for controls)
- [ ] Adversarial testing
  - [ ] Test embedded instructions in documents
  - [ ] Test prompt injection attempts

---

### Phase 9: Chat Frontend
**Status:** ⏳ Pending

**Deliverables:**
- [ ] Streaming implementation
  - [ ] Backend streaming response
  - [ ] Frontend streaming display
- [ ] Chat UI
  - [ ] Message history display
  - [ ] Report context selector
  - [ ] Suggested questions
  - [ ] Citation display with links
  - [ ] Terminology explanations
  - [ ] Copy functionality
- [ ] Conversation management
  - [ ] Create new conversation
  - [ ] Switch between conversations
  - [ ] Delete conversation
- [ ] Feedback system
  - [ ] Thumbs up/down on messages
  - [ ] POST /api/feedback

---

### Phase 10: Comparison & Summary
**Status:** ⏳ Pending

**Deliverables:**
- [ ] Report comparison
  - [ ] POST /api/reports/compare
  - [ ] Test matching logic
  - [ ] Unit compatibility checking
  - [ ] Value change calculation (without judgment)
- [ ] Comparison UI
  - [ ] Side-by-side view
  - [ ] Matched test display
  - [ ] Charts (Recharts)
- [ ] Doctor summary
  - [ ] POST /api/doctor-summary
  - [ ] PDF generation
  - [ ] Include: results, explanations, questions
  - [ ] Exclude: diagnosis, treatment
- [ ] Privacy center
  - [ ] Delete report + vectors
  - [ ] Delete conversations
  - [ ] Retention settings
  - [ ] Audit log view (admin)

---

### Phase 11: Evaluation & Testing
**Status:** ⏳ Pending

**Deliverables:**
- [ ] Test dataset
  - [ ] 50+ synthetic questions
  - [ ] Diverse test types
  - [ ] Edge cases
- [ ] Retrieval evaluation
  - [ ] Recall@K
  - [ ] MRR
  - [ ] Context precision/recall
- [ ] Generation evaluation (RAGAS)
  - [ ] Faithfulness
  - [ ] Answer relevancy
  - [ ] Citation correctness
- [ ] Safety evaluation
  - [ ] Diagnosis request tests
  - [ ] Prescription request tests
  - [ ] Emergency detection tests
  - [ ] Prompt injection tests
- [ ] RAG comparison
  - [ ] Baseline vs hybrid vs reranked
  - [ ] Document findings

---

### Phase 12: Production Deployment
**Status:** ⏳ Pending

**Deliverables:**
- [ ] Production Dockerfiles
  - [ ] Multi-stage builds
  - [ ] Security hardening
- [ ] Production Docker Compose
  - [ ] Resource limits
  - [ ] Healthchecks
  - [ ] Restart policies
- [ ] Environment configuration
  - [ ] Production .env template
  - [ ] Secrets management guidance
- [ ] Database migrations
  - [ ] Migration scripts for production
  - [ ] Rollback procedures
- [ ] Monitoring
  - [ ] Logging aggregation
  - [ ] Error monitoring setup
  - [ ] Health dashboard
- [ ] Documentation
  - [ ] Deployment guide
  - [ ] Operations runbook
  - [ ] API documentation

---

## Post-Launch Considerations

Items to address after the 12-phase build:
- User onboarding flow
- Email notifications
- Report sharing (with privacy controls)
- Multi-language support
- Mobile app consideration
- Performance optimization based on real usage
- Knowledge base expansion
- Model fine-tuning based on feedback

---

*Document Version: 1.0*  
*Last Updated: Phase 1*
