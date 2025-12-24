"""
API Routes Package

Modular route organization:
- chat.py: Conversation endpoints (v1 and v2)
- darshan.py: Cards, actions, insights, and summary
- family.py: Family space, child-space, and family management endpoints
- child.py: Child data and gestalt endpoints
- user.py: User-centric endpoints (family, children)
- artifacts.py: Artifact management, threads, and session endpoints
- test.py: Test mode and dev endpoints
- state.py: SSE subscriptions and state endpoints
- views.py: Deep views endpoints
- video.py: Video upload and analysis
- journal.py: Journal entry endpoints
- timeline.py: Timeline generation and retrieval
- legacy_routes.py: Root, interview, and reports endpoints
"""

from fastapi import APIRouter

# Import modular routers
from .chat import router as chat_router
from .darshan import router as darshan_router
from .family import router as family_router
from .child import router as child_router
from .artifacts import router as artifacts_router
from .test import router as test_router
from .state import router as state_router
from .views import router as views_router
from .video import router as video_router
from .journal import router as journal_router
from .timeline import router as timeline_router
from .user import router as user_router
from .dashboard import router as dashboard_router

# Import legacy router (endpoints not yet migrated)
from ..legacy_routes import router as legacy_router

# Create main router for this package
router = APIRouter()

# Include modular routers first (take precedence)
router.include_router(chat_router)
router.include_router(darshan_router)
router.include_router(family_router)
router.include_router(child_router)
router.include_router(artifacts_router)
router.include_router(test_router)
router.include_router(state_router)
router.include_router(views_router)
router.include_router(video_router)
router.include_router(journal_router)
router.include_router(timeline_router)
router.include_router(user_router)
router.include_router(dashboard_router)

# Include legacy routes (endpoints not yet in modular files)
router.include_router(legacy_router)

# Export for external use
__all__ = [
    "router", "chat_router", "darshan_router", "family_router",
    "child_router", "artifacts_router", "test_router", "state_router",
    "views_router", "video_router", "journal_router", "timeline_router",
    "user_router", "dashboard_router"
]
