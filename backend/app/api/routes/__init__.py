"""API routes aggregation."""
from fastapi import APIRouter

from .health import router as health_router
from .auth import router as auth_router
from .reports import router as reports_router

router = APIRouter()

router.include_router(health_router, tags=["health"])
router.include_router(auth_router, tags=["auth"])
router.include_router(reports_router, tags=["reports"])
