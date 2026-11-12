# MediLens AI

A RAG-powered medical report explainer for **educational purposes only**.

## ⚠️ Important Disclaimer

MediLens AI is designed for **educational purposes only**. It:
- **NEVER** diagnoses conditions or diseases
- **NEVER** prescribes medications or treatments
- **NEVER** recommends specific dosages
- **ALWAYS** recommends consulting healthcare providers

This application should only be used with synthetic test data. Never upload real patient medical records.

## Features

- **Upload Medical Reports**: PDF, images, and DOCX support with OCR for scanned documents
- **Structured Extraction**: Automatic extraction of lab results with confidence scoring
- **AI-Powered Explanations**: Educational explanations using RAG with trusted sources
- **Knowledge Base**: Information from MedlinePlus, NIH, NHS, and WHO
- **Report Comparison**: Compare results across multiple reports
- **Doctor Summary**: Generate PDF summaries for healthcare provider review
- **Safety Engine**: Intent classification to prevent unsafe responses

## Tech Stack

- **Frontend**: React, TypeScript, Vite, Tailwind CSS
- **Backend**: FastAPI, Python 3.12
- **Database**: PostgreSQL (user data), Qdrant (vector search), Redis (cache/queue)
- **ML/AI**: sentence-transformers (BGE embeddings), OpenAI API (optional)
- **Document Processing**: PyMuPDF, **PaddleOCR (primary)** with Tesseract fallback, python-docx
- **Chunking / vectors**: LlamaIndex SentenceSplitter + BGE-small-en-v1.5; hybrid BM25+RRF+rerank retrieval

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL 15+
- Redis
- Qdrant

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your settings

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8247 --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

### Services

Start PostgreSQL, Redis, and Qdrant:

```bash
# PostgreSQL
sudo systemctl start postgresql
# or: pg_ctl -D /var/lib/postgresql/data start

# Redis
redis-server

# Qdrant
./qdrant
```

## Project Structure

```
medilens-ai/
├── backend/
│   ├── app/
│   │   ├── api/           # API routes
│   │   ├── core/          # Config, security, logging
│   │   ├── database/      # Models and session
│   │   ├── embeddings/    # Qdrant client
│   │   ├── extraction/    # Lab result extraction
│   │   ├── ingestion/     # Document parsing
│   │   ├── knowledge/     # Knowledge base
│   │   ├── llm/           # LLM providers
│   │   ├── rag/           # RAG pipeline
│   │   ├── safety/        # Safety engine
│   │   ├── evaluation/    # Metrics
│   │   ├── schemas/       # Pydantic models
│   │   └── services/      # Business logic
│   └── tests/             # Test suite
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── hooks/         # Custom hooks
│   │   └── services/      # API client
│   └── public/
└── docs/
    ├── ARCHITECTURE.md    # System design
    ├── ROADMAP.md         # Development phases
    └── DEPLOYMENT.md      # Deployment guide
```

## API Endpoints

### Health
- `GET /api/health` - Health check
- `GET /api/health/ready` - Readiness check (includes DB)

### Auth
- `POST /api/auth/register` - Register user
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout
- `POST /api/auth/refresh` - Refresh token
- `GET /api/auth/me` - Current user

### Reports
- `POST /api/reports/upload` - Upload report
- `GET /api/reports` - List reports
- `GET /api/reports/{id}` - Get report
- `GET /api/reports/{id}/results` - Get extracted results
- `POST /api/reports/{id}/process` - Extract data
- `DELETE /api/reports/{id}` - Delete report

### Chat
- `POST /api/chat` - Send message
- `GET /api/chat/stream` - Stream response (SSE)
- `GET /api/chat/conversations` - List conversations
- `GET /api/chat/conversations/{id}` - Get conversation

### Knowledge
- `GET /api/sources` - List knowledge sources
- `POST /api/sources` - Ingest content

### Comparison
- `POST /api/reports/compare` - Compare reports
- `POST /api/reports/{id}/summary` - Generate PDF summary

## Testing

```bash
cd backend
python -m pytest tests/ -v
```

Current test coverage: 71 tests passing

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `POSTGRES_HOST` | PostgreSQL host | Yes |
| `POSTGRES_PASSWORD` | PostgreSQL password | Yes |
| `REDIS_HOST` | Redis host | Yes |
| `QDRANT_HOST` | Qdrant host | Yes |
| `JWT_SECRET_KEY` | JWT signing key | Yes |
| `OPENAI_API_KEY` | OpenAI API key | No* |

*Without `OPENAI_API_KEY`, AI answers will return a "not configured" message.

## Safety Features

- **Intent Classification**: Detects diagnosis/medication requests
- **Emergency Detection**: Detects crisis/emergency queries
- **Response Validation**: Ensures responses don't contain unsafe content
- **Automatic Disclaimers**: Adds educational disclaimers to responses

## License

Educational use only. Not for commercial deployment with real patient data.

---

**Remember**: This is an educational tool. For medical advice, always consult a healthcare professional.
