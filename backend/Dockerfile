# Build stage
FROM python:3.12-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir build

COPY pyproject.toml README.md ./
COPY app ./app

RUN python -m build --wheel

# Production stage
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl

COPY alembic.ini ./
COPY alembic ./alembic

EXPOSE 8247

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8247"]
