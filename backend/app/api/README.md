# API Layer

FastAPI route definitions for MediLens AI.

## Structure

- `routes/` - Route modules organized by feature
  - `health.py` - Health check endpoints
  - `auth.py` - Authentication endpoints (Phase 2)
  - `reports.py` - Report management endpoints (Phase 3+)
  - `chat.py` - Chat endpoints (Phase 6+)
  - `compare.py` - Comparison endpoints (Phase 10)
  - `summary.py` - Doctor summary endpoints (Phase 10)
  - `sources.py` - Knowledge sources endpoints (Phase 5)
  - `feedback.py` - Feedback endpoints (Phase 9)
- `deps.py` - Dependency injection utilities
