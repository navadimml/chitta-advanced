"""
Timeline API Routes - Timeline generation and retrieval

Includes:
- /timeline/generate - Generate timeline infographic
- /timeline/{child_id} - Get latest timeline artifact
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import logging

from app.core.app_state import app_state
from app.services.session_service import get_session_service

router = APIRouter(prefix="/timeline", tags=["timeline"])
logger = logging.getLogger(__name__)


# === Request Models ===

class TimelineGenerateRequest(BaseModel):
    """Request to generate a timeline infographic."""
    family_id: str
    style: Optional[str] = "warm"


# === Endpoints ===

@router.post("/generate")
async def generate_timeline(request: TimelineGenerateRequest):
    """
    Generate a visual timeline infographic for a child's journey.

    Uses Gemini image generation to create a beautiful infographic
    showing key moments and milestones.

    Supports both Darshan data (new) and legacy session data.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    try:
        from app.services.timeline_image_service import get_timeline_service
        from app.chitta import get_chitta_service

        timeline_service = get_timeline_service()
        child_name = "הילד/ה"
        events = []

        # Load gestalt data from database via ChittaService
        try:
            chitta = get_chitta_service()
            gestalt = await chitta.get_gestalt(request.family_id)
            if gestalt:
                child_name = gestalt.child_name or "הילד/ה"
                gestalt_data = gestalt.get_state_for_persistence()
                events = timeline_service.build_events_from_gestalt(gestalt_data)
                logger.info(f"Building timeline from gestalt data for {request.family_id}")
        except Exception as e:
            logger.warning(f"Failed to load gestalt data for timeline: {e}")

        if not events:
            session_service = get_session_service()
            session = session_service.get_or_create_session(request.family_id)

            extracted = session.extracted_data
            if extracted and extracted.child_name:
                child_name = extracted.child_name

            events = timeline_service.build_events_from_family_state(
                session.model_dump()
            )

        if not events:
            return {
                "success": False,
                "error": "לא נמצאו אירועים ליצירת ציר זמן",
                "message": "יש להמשיך בשיחה כדי ליצור ציר זמן"
            }

        result = await timeline_service.generate_timeline_image(
            child_name=child_name,
            events=events,
            family_id=request.family_id,
            style=request.style
        )

        if not result:
            return {
                "success": False,
                "error": "שגיאה ביצירת ציר הזמן",
                "message": "נסה שוב מאוחר יותר"
            }

        from app.models.artifact import Artifact

        artifact = Artifact(
            artifact_id=f"timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            artifact_type="timeline_infographic",
            status="ready",
            content=result["image_url"],
            metadata={
                "image_url": result["image_url"],
                "image_path": result["image_path"],
                "child_name": child_name,
                "event_count": result["event_count"],
                "style": result["style"],
                "generated_at": result["generated_at"],
                "mime_type": result["mime_type"]
            }
        )

        if 'session' in locals():
            session.add_artifact(artifact)

        logger.info(f"Timeline generated for {child_name}: {result['image_url']}")

        return {
            "success": True,
            "artifact_id": artifact.artifact_id,
            "image_url": result["image_url"],
            "child_name": child_name,
            "event_count": result["event_count"],
            "message": f"ציר הזמן של {child_name} נוצר בהצלחה!"
        }

    except Exception as e:
        logger.error(f"Timeline generation error: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "שגיאה ביצירת ציר הזמן"
        }


@router.get("/{child_id}")
async def get_timeline(child_id: str):
    """Get the latest timeline artifact for a child."""
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    session_service = get_session_service()
    session = session_service.get_or_create_session(child_id)

    timelines = [
        a for a in session.family_state.artifacts.values()
        if a.artifact_type == "timeline_infographic"
    ]

    if not timelines:
        return {
            "success": False,
            "has_timeline": False,
            "message": "לא נמצא ציר זמן"
        }

    latest = max(timelines, key=lambda a: a.created_at or "")

    return {
        "success": True,
        "has_timeline": True,
        "artifact_id": latest.artifact_id,
        "image_url": latest.data.get("image_url"),
        "child_name": latest.data.get("child_name"),
        "event_count": latest.data.get("event_count"),
        "generated_at": latest.metadata.get("generated_at")
    }
