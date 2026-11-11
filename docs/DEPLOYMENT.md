# MediLens AI - Deployment Guide

## Overview

MediLens AI is a RAG-powered medical report explainer for **educational purposes only**. This guide covers deploying the application in production.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│     Backend     │────▶│   PostgreSQL    │
│   (React/Vite)  │     │    (FastAPI)    │     │   (User data)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │     Qdrant      │     │      Redis      │
                        │  (Vectors)      │     │    (Cache)      │
                        └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   OpenAI API    │
                        │   (Optional)    │
                        └─────────────────┘
```

## Prerequisites

- Docker and Docker Compose
- At least 4GB RAM
- 10GB disk space
- OpenAI API key (optional, for AI answers)

## Quick Start with Docker

### 1. Clone and Configure

```bash
# Clone repository
git clone <repository>
cd medilens-ai

# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env
```

### 2. Required Environment Variables

```bash
# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=medilens
POSTGRES_PASSWORD=<strong-password>
POSTGRES_DB=medilens

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# JWT (generate a secure key)
JWT_SECRET_KEY=<32-char-random-string>

# OpenAI (optional - without this, AI answers won't work)
OPENAI_API_KEY=sk-...
```

### 3. Start Services

```bash
# Build and start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
```

### 4. Initialize Database

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Create Qdrant collections
docker-compose exec backend python -c "
from app.embeddings.qdrant_client import initialize_collections
from qdrant_client import QdrantClient
client = QdrantClient(host='qdrant', port=6333)
initialize_collections(client)
print('Collections created!')
"
```

## Manual Deployment

### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start with gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Build for production
npm run build

# Serve with nginx or any static file server
# Point to dist/ directory
```

## Security Considerations

### Critical Security Measures

1. **Never expose database directly** - Use internal Docker networking
2. **Use strong passwords** - All service credentials should be strong
3. **Enable HTTPS** - Use a reverse proxy with TLS
4. **JWT Secret** - Use a cryptographically secure random string
5. **Rate Limiting** - Configure rate limits in production

### No Real Patient Data

⚠️ **CRITICAL**: MediLens AI should only be used with synthetic test data for educational purposes. Never upload real patient medical records.

### API Keys

- Store OpenAI API key securely
- Never commit secrets to version control
- Use environment variables or secret management

## Monitoring

### Health Checks

```bash
# Backend health
curl http://localhost:8000/api/health

# Ready check (includes database/services)
curl http://localhost:8000/api/health/ready
```

### Logs

```bash
# Backend logs (structured JSON)
docker-compose logs -f backend

# All service logs
docker-compose logs -f
```

## Scaling Considerations

### Horizontal Scaling

- Backend: Stateless - can run multiple instances
- Redis: Single instance for Celery broker
- Qdrant: Can be clustered for high availability
- PostgreSQL: Read replicas for scaling reads

### Resource Requirements

| Service    | Min RAM | Recommended |
|------------|---------|-------------|
| Backend    | 512MB   | 2GB         |
| PostgreSQL | 256MB   | 1GB         |
| Redis      | 128MB   | 512MB       |
| Qdrant     | 512MB   | 2GB         |
| Frontend   | N/A     | N/A (static)|

## Backup & Recovery

### Database Backup

```bash
# Create backup
docker-compose exec postgres pg_dump -U medilens medilens > backup.sql

# Restore
docker-compose exec -T postgres psql -U medilens medilens < backup.sql
```

### Qdrant Backup

```bash
# Qdrant supports snapshots
curl -X POST 'http://localhost:6333/collections/trusted_knowledge/snapshots'
```

## Troubleshooting

### Common Issues

1. **"AI answer service not configured"**
   - Set `OPENAI_API_KEY` environment variable

2. **Database connection errors**
   - Check `POSTGRES_*` environment variables
   - Ensure PostgreSQL is running

3. **Vector search not working**
   - Ensure Qdrant is running and collections are initialized
   - Check `QDRANT_HOST` and `QDRANT_PORT`

4. **Frontend can't reach backend**
   - Check CORS settings in backend
   - Verify API_BASE_URL in frontend

## Support

For issues, please check:
1. Application logs
2. Health endpoint responses
3. Service connectivity

---

**Disclaimer**: MediLens AI is for educational purposes only and should not be used for medical diagnosis or treatment decisions.
