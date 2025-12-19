"""
API Routes Package

Modular route organization:
- chat.py: Conversation endpoints (v1 and v2)
- darshan.py: Cards, actions, insights, and summary
- legacy_routes.py: Remaining endpoints (being migrated)
"""

from fastapi import APIRouter

# Import modular routers
from .chat import router as chat_router
from .darshan import router as darshan_router

# Import legacy router (endpoints not yet migrated)
from ..legacy_routes import router as legacy_router

# Create main router for this package
router = APIRouter()

# Include modular routers first (take precedence)
router.include_router(chat_router)
router.include_router(darshan_router)

# Include legacy routes (endpoints not yet in modular files)
router.include_router(legacy_router)

# Export for external use
__all__ = ["router", "chat_router", "darshan_router"]
