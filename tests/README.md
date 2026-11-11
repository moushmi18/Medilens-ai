# Tests

Test suite for MediLens AI.

## Structure

- `backend/` - Backend unit and integration tests
  - `test_health.py` - Health endpoint tests
  - `test_auth.py` - Auth tests (Phase 2)
  - `test_reports.py` - Report tests (Phase 3+)
  - `test_safety.py` - Safety engine tests (Phase 8)
- `frontend/` - Frontend tests
- `integration/` - End-to-end integration tests

## Running Tests

```bash
# Backend tests
cd backend
pytest ../tests/backend -v

# Frontend tests
cd frontend
npm test

# All tests
pytest tests/ -v
```
