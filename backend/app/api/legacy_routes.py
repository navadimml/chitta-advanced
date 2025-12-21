"""
Legacy API Routes for Chitta

DEPRECATED: These endpoints are from the old Wu Wei architecture.
Use the Darshan/Chitta endpoints in routes/chat.py instead:
- /chat/v2/send - Send message
- /chat/v2/synthesis/{family_id} - Request synthesis (replaces /reports/generate)
- /chat/v2/video/* - Video workflow

Only the dev_routes inclusion and root endpoint are kept here.
Legacy /interview/complete and /reports/generate are deprecated and will be removed.
"""

import warnings
import os
import logging

from fastapi import APIRouter

from app.api import dev_routes

router = APIRouter()
logger = logging.getLogger(__name__)

# Include dev routes (only in development)
if os.getenv("ENVIRONMENT", "development") == "development":
    router.include_router(dev_routes.router)


@router.get("/")
async def root():
    """API root"""
    return {"message": "Chitta API", "version": "2.0.0", "architecture": "darshan"}


# === DEPRECATED ENDPOINTS ===
# These are kept for backwards compatibility but should not be used.
# They will be removed in a future version.

@router.post("/interview/complete", deprecated=True)
async def complete_interview(family_id: str):
    """
    DEPRECATED: Use /chat/v2/synthesis/{family_id} instead.

    This endpoint was part of the Wu Wei stage-based architecture.
    The Darshan/Chitta architecture uses a continuous flow model.
    """
    warnings.warn(
        "POST /interview/complete is deprecated. "
        "Use POST /chat/v2/synthesis/{family_id} for synthesis.",
        DeprecationWarning,
        stacklevel=2
    )
    logger.warning(f"Deprecated endpoint /interview/complete called for family_id={family_id}")

    return {
        "success": False,
        "error": "This endpoint is deprecated. Use /chat/v2/synthesis/{family_id} instead.",
        "deprecated": True
    }


@router.post("/reports/generate", deprecated=True)
async def generate_reports(family_id: str):
    """
    DEPRECATED: Use /chat/v2/synthesis/{family_id} instead.

    This endpoint was part of the Wu Wei stage-based architecture.
    The Darshan/Chitta architecture uses synthesis for report generation.
    """
    warnings.warn(
        "POST /reports/generate is deprecated. "
        "Use POST /chat/v2/synthesis/{family_id} for synthesis.",
        DeprecationWarning,
        stacklevel=2
    )
    logger.warning(f"Deprecated endpoint /reports/generate called for family_id={family_id}")

    return {
        "success": False,
        "error": "This endpoint is deprecated. Use /chat/v2/synthesis/{family_id} instead.",
        "deprecated": True
    }
