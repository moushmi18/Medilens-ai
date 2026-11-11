# MediLens AI

**RAG-powered Medical Report Explainer**

MediLens AI helps patients understand their medical reports through AI-powered explanations. It provides **educational and informational content only** — it never diagnoses, prescribes medications, or provides medical advice.

## Features

- **Report Upload** - Support for PDF, scanned documents, images, and DOCX files
- **AI Explanations** - Natural language explanations of lab results and medical terms
- **Trusted Sources** - Information backed by MedlinePlus, WHO, NHS, and other verified sources
- **Report Comparison** - Track changes between reports over time
- **Doctor Summary** - Generate summaries to discuss with your healthcare provider
- **Privacy-First** - Your data is encrypted and you control its deletion

## Quick Start

### Prerequisites

- Node.js 22+
- Python 3.11+
- Docker & Docker Compose (recommended)

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd medilens-ai

# Copy environment file
cp .env.example .env

# Start all services
docker compose up -d

# View logs
docker compose logs -f
```

Access the application:
- Frontend: http://localhost:5847
- Backend API: http://localhost:8247
- API Docs: http://localhost:8247/api/docs (debug mode)

### Local Development

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at http://localhost:5847

#### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8247
```

Backend runs at http://localhost:8247

### Running Tests

```bash
# Backend tests
cd backend
source .venv/bin/activate
pytest ../tests/backend -v

# Frontend lint and typecheck
cd frontend
npm run lint
npm run typecheck
npm run build
```

## Project Structure

```
medilens-ai/
├── frontend/           # React + TypeScript + Vite
│   └── src/
│       ├── components/ # Reusable UI components
│       ├── pages/      # Page components (11 routes)
│       ├── layouts/    # Layout wrappers
│       ├── hooks/      # Custom React hooks
│       ├── services/   # API client
│       └── types/      # TypeScript types
├── backend/            # FastAPI + Python
│   └── app/
│       ├── api/        # API routes
│       ├── core/       # Config, logging, exceptions
│       ├── database/   # SQLAlchemy models
│       ├── schemas/    # Pydantic schemas
│       ├── services/   # Business logic
│       ├── workers/    # Celery tasks
│       └── ...         # RAG, safety, etc.
├── tests/              # Test suite
├── docs/               # Documentation
├── evaluation/         # RAG evaluation framework
└── sample_data/        # Synthetic test data
```

## Development Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Project setup, frontend shell, backend health checks | ✅ Complete |
| 2 | Database, Qdrant, authentication | 🔲 Pending |
| 3 | Upload, parsing, OCR | 🔲 Pending |
| 4 | Structured extraction, verification | 🔲 Pending |
| 5 | Knowledge base ingestion | 🔲 Pending |
| 6 | Basic RAG pipeline | 🔲 Pending |
| 7 | Hybrid retrieval + reranking | 🔲 Pending |
| 8 | Safety engine, citations | 🔲 Pending |
| 9 | Chat frontend | 🔲 Pending |
| 10 | Comparison, doctor summary | 🔲 Pending |
| 11 | Evaluation, testing | 🔲 Pending |
| 12 | Production deployment | 🔲 Pending |

See [docs/ROADMAP.md](docs/ROADMAP.md) for detailed phase information.

## API Endpoints

### Health Checks
- `GET /api/health` - Liveness probe
- `GET /api/health/ready` - Readiness probe (checks Postgres, Redis, Qdrant)

### Coming in Later Phases
- Authentication (Phase 2)
- Report management (Phase 3+)
- Chat (Phase 6+)
- Comparison & Summary (Phase 10)

## Tech Stack

- **Frontend**: React, TypeScript, Vite, Tailwind CSS, React Router, Recharts
- **Backend**: Python, FastAPI, SQLAlchemy, Alembic, Pydantic
- **AI/RAG**: LlamaIndex, OpenAI, BGE embeddings, Qdrant
- **Infrastructure**: PostgreSQL, Redis, Celery, Docker

## Important Notes

⚠️ **This application is for educational purposes only.**

- Never provides medical diagnoses
- Never prescribes medications or dosages
- Never interprets results as conditions
- Always recommends consulting healthcare professionals

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
