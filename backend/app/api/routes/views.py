"""
Views API Routes - Deep views endpoints

Includes:
- /views/available - Get available views for current session
- /views/{view_id} - Get specific view content
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import logging

from app.core.app_state import app_state
from app.services.session_service import get_session_service
from app.config.view_manager import get_view_manager

router = APIRouter(prefix="/views", tags=["views"])
logger = logging.getLogger(__name__)


# === Response Models ===

class AvailableViewsResponse(BaseModel):
    """Response model for available views"""
    family_id: str
    available_views: List[str]


class ViewContentResponse(BaseModel):
    """Response model for view content"""
    view_id: str
    view_name: str
    view_name_en: str
    available: bool
    content: Optional[dict] = None
    reason_unavailable: Optional[str] = None


# === Endpoints ===

@router.get("/available", response_model=AvailableViewsResponse)
async def get_available_views(family_id: str):
    """
    Get available deep views for current session.

    Returns list of view IDs that are available based on current session state.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    session_service = get_session_service()
    view_manager = get_view_manager()

    session = session_service.get_or_create_session(family_id)
    data = session.extracted_data

    artifacts = {}
    for artifact_id, artifact in session.artifacts.items():
        artifacts[artifact_id] = {
            "exists": artifact.exists,
            "status": artifact.status
        }

    context = {
        "completeness": session.completeness,
        "child_name": data.child_name,
        "artifacts": artifacts,
        "reports_ready": session.has_artifact("baseline_parent_report"),
        "video_count": 0,
    }

    available_views = view_manager.get_available_views(context)

    return AvailableViewsResponse(
        family_id=family_id,
        available_views=available_views
    )


@router.get("/{view_id}", response_model=ViewContentResponse)
async def get_view_content(view_id: str, family_id: str):
    """
    Get specific view content.

    Returns view definition and content if available, or reason if unavailable.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    session_service = get_session_service()
    view_manager = get_view_manager()

    view = view_manager.get_view(view_id)
    if not view:
        raise HTTPException(status_code=404, detail=f"View '{view_id}' not found")

    session = session_service.get_or_create_session(family_id)
    data = session.extracted_data

    artifacts = {}
    for artifact_id, artifact in session.artifacts.items():
        artifacts[artifact_id] = {
            "exists": artifact.exists,
            "status": artifact.status,
            "content": artifact.content if artifact.is_ready else None
        }

    context = {
        "completeness": session.completeness,
        "child_name": data.child_name,
        "artifacts": artifacts,
        "reports_ready": session.has_artifact("baseline_parent_report"),
        "video_count": 0,
    }

    is_available = view_manager.check_view_availability(view_id, context)

    if is_available:
        view_content = view.copy()

        data_sources = view.get("data_sources", {})
        primary_source = data_sources.get("primary")

        if primary_source:
            artifact_map = {
                "video_guidelines": "baseline_video_guidelines",
                "parent_report": "baseline_parent_report",
                "professional_report": "baseline_professional_report",
                "updated_parent_report": "updated_parent_report"
            }

            artifact_id = artifact_map.get(primary_source, primary_source)
            artifact = session.get_artifact(artifact_id)

            if artifact and artifact.is_ready:
                view_content["artifact_content"] = artifact.content
                view_content["artifact_metadata"] = {
                    "created_at": artifact.created_at.isoformat(),
                    "ready_at": artifact.ready_at.isoformat() if artifact.ready_at else None
                }

        view_content["context"] = {
            "child_name": data.child_name,
            "artifacts_available": list(artifacts.keys())
        }

        return ViewContentResponse(
            view_id=view_id,
            view_name=view.get("name", ""),
            view_name_en=view.get("name_en", ""),
            available=True,
            content=view_content
        )
    else:
        return ViewContentResponse(
            view_id=view_id,
            view_name=view.get("name", ""),
            view_name_en=view.get("name_en", ""),
            available=False,
            reason_unavailable="View not available in current phase or missing required data"
        )
