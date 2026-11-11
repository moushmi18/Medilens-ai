"""API routes aggregation."""
from fastapi import APIRouter

from .health import router as health_router
from .auth import router as auth_router

router = APIRouter()

router.include_router(health_router, tags=["health"])
router.include_router(auth_router, tags=["auth"])
