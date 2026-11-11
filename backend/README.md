# MediLens AI Backend

FastAPI backend for the MediLens AI medical report explainer.

## Development Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8247
```

## API Endpoints

### Health Checks
- `GET /api/health` - Liveness probe
- `GET /api/health/ready` - Readiness probe (checks Postgres, Redis, Qdrant)

### Documentation (debug mode only)
- `GET /api/docs` - Swagger UI
- `GET /api/redoc` - ReDoc
- `GET /api/openapi.json` - OpenAPI schema

## Environment Variables

See `.env.example` for configuration options.

## Running Tests

```bash
pytest ../tests/backend -v
```
