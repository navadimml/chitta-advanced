"""
API Routes Package

Modular route organization:
- chat.py: Conversation endpoints (v1 and v2)
- darshan.py: Cards, actions, insights, and summary
- family.py: Family space and child-space endpoints
- child.py: Child data and gestalt endpoints
- artifacts.py: Artifact management, threads, and session endpoints
- test.py: Test mode and dev endpoints
- legacy_routes.py: Remaining endpoints (being migrated)
"""

from fastapi import APIRouter

# Import modular routers
from .chat import router as chat_router
from .darshan import router as darshan_router
from .family import router as family_router
from .child import router as child_router
from .artifacts import router as artifacts_router
from .test import router as test_router

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

# Include legacy routes (endpoints not yet in modular files)
router.include_router(legacy_router)

# Export for external use
__all__ = ["router", "chat_router", "darshan_router", "family_router", "child_router", "artifacts_router", "test_router"]
