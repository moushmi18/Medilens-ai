"""API routes aggregation."""
from fastapi import APIRouter

from .health import router as health_router
from .auth import router as auth_router
from .reports import router as reports_router
from .knowledge import router as knowledge_router
from .chat import router as chat_router
from .chat_stream import router as chat_stream_router
from .comparison import router as comparison_router, reports_router as comparison_reports_router
from .dashboard import router as dashboard_router
from .feedback import router as feedback_router
from .privacy import router as privacy_router

router = APIRouter()

router.include_router(health_router, tags=["health"])
router.include_router(auth_router, tags=["auth"])
router.include_router(dashboard_router, tags=["dashboard"])
router.include_router(reports_router, tags=["reports"])
router.include_router(comparison_reports_router, tags=["comparison"])
router.include_router(comparison_router, tags=["comparison"])
router.include_router(knowledge_router, tags=["knowledge"])
router.include_router(chat_router, tags=["chat"])
router.include_router(chat_stream_router, tags=["chat"])
router.include_router(feedback_router, tags=["feedback"])
router.include_router(privacy_router, tags=["privacy"])
