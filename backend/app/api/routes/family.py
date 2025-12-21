"""
Family API Routes - Family space and child-space endpoints

Includes:
- /family/{family_id}/space/* (Living Dashboard)
- /family/{family_id}/child-space/* (Living Portrait + Sharing)
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging

from app.core.app_state import app_state
from app.db.dependencies import get_current_user, RequireAuth
from app.db.models_auth import User
from app.services.unified_state_service import get_unified_state_service
from app.services.session_service import get_session_service
from app.services.child_space_service import get_child_space_service

router = APIRouter(prefix="/family", tags=["family"])
logger = logging.getLogger(__name__)


# === Family Management Endpoints ===

class AddChildResponse(BaseModel):
    """Response for add child endpoint."""
    child_id: str


@router.post("/{family_id}/children", response_model=AddChildResponse)
async def add_child_to_family(
    family_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Add a new child placeholder to family.

    Creates an empty child that will be filled via conversation.
    """
    from app.services.family_service import get_family_service

    logger.info(f"Adding child to family {family_id} by user {current_user.email}")

    family_service = get_family_service()

    # Verify user has access to this family
    user_family_id = await family_service.get_user_family_id(str(current_user.id))
    if user_family_id != family_id:
        raise HTTPException(
            status_code=403,
            detail="You don't have access to this family"
        )

    # Create new child placeholder
    child_id = await family_service.add_child_to_family(family_id)

    return AddChildResponse(child_id=child_id)


# === Living Dashboard (Space) Endpoints ===

@router.get("/{family_id}/space")
async def get_child_space(
    family_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get complete child space with all artifact slots.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    state_service = get_unified_state_service()
    child_space_service = get_child_space_service()

    state = state_service.get_family_state(family_id)

    # Sync artifacts from session to family state
    session_service = get_session_service()
    session = session_service.get_or_create_session(family_id)

    for artifact_id, artifact in session.artifacts.items():
        if artifact.is_ready or artifact.status == "generating":
            state.artifacts[artifact_id] = artifact

    space = child_space_service.get_child_space(state)

    return {
        "family_id": space.family_id,
        "child_name": space.child_name,
        "slots": [slot.model_dump() for slot in space.slots],
        "header_badges": space.header_badges,
        "last_updated": space.last_updated.isoformat() if space.last_updated else None
    }


@router.get("/{family_id}/space/header")
async def get_child_space_header(
    family_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get header badges only (lightweight endpoint).
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    state_service = get_unified_state_service()
    child_space_service = get_child_space_service()

    state = state_service.get_family_state(family_id)

    session_service = get_session_service()
    session = session_service.get_or_create_session(family_id)
    for artifact_id, artifact in session.artifacts.items():
        if artifact.is_ready or artifact.status == "generating":
            state.artifacts[artifact_id] = artifact

    badges = child_space_service.get_header_summary(state)

    return {
        "family_id": family_id,
        "badges": badges
    }


@router.get("/{family_id}/space/slot/{slot_id}")
async def get_slot_detail(
    family_id: str,
    slot_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed slot info including version history.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    state_service = get_unified_state_service()
    child_space_service = get_child_space_service()

    state = state_service.get_family_state(family_id)

    session_service = get_session_service()
    session = session_service.get_or_create_session(family_id)
    for artifact_id, artifact in session.artifacts.items():
        if artifact.is_ready or artifact.status == "generating":
            state.artifacts[artifact_id] = artifact

    slot = child_space_service.get_slot_detail(state, slot_id)

    if not slot:
        raise HTTPException(status_code=404, detail=f"Slot '{slot_id}' not found")

    return {"slot": slot.model_dump()}


# === Living Portrait (Child-Space) Endpoints ===

@router.get("/{family_id}/child-space")
async def get_child_space_full(
    family_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get complete ChildSpace data for the Living Portrait UI.
    """
    from app.chitta.service import get_chitta_service
    chitta = get_chitta_service()
    gestalt = await chitta.get_gestalt(family_id)

    if not gestalt:
        raise HTTPException(status_code=404, detail="Family not found")

    await chitta.ensure_crystal_fresh(family_id)
    gestalt = await chitta.get_gestalt(family_id)

    return chitta.derive_child_space_full(gestalt)


# === Summary Readiness & Guided Collection ===

@router.get("/{family_id}/child-space/share/readiness/{recipient_type}")
async def check_summary_readiness(
    family_id: str,
    recipient_type: str,
    current_user: User = Depends(get_current_user)
):
    """
    Check if we have enough data to generate a useful summary.
    """
    from app.chitta.service import get_chitta_service
    from app.chitta.clinical_gaps import ClinicalGaps

    chitta = get_chitta_service()
    gestalt = await chitta.get_gestalt(family_id)

    if not gestalt:
        raise HTTPException(status_code=404, detail="Family not found")

    child = await chitta._child_service.get_or_create_child_async(family_id)

    gap_detector = ClinicalGaps()
    readiness = gap_detector.check_readiness(
        recipient_type=recipient_type,
        understanding=gestalt.understanding,
        child=child,
    )

    return {
        "status": readiness.status,
        "missing_critical": [
            {"field": g.field, "description": g.parent_description, "clinical_term": g.clinical_term}
            for g in readiness.missing_critical
        ],
        "missing_important": [
            {"field": g.field, "description": g.parent_description, "clinical_term": g.clinical_term}
            for g in readiness.missing_important
        ],
        "can_generate": readiness.can_generate,
        "guidance_message": readiness.guidance_message,
    }


class StartGuidedCollectionRequest(BaseModel):
    """Request to start guided collection mode."""
    recipient_type: str


@router.post("/{family_id}/child-space/share/guided-collection/start")
async def start_guided_collection(
    family_id: str,
    request: StartGuidedCollectionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Start guided collection mode for preparing a summary.
    """
    from app.chitta.service import get_chitta_service
    from app.chitta.clinical_gaps import ClinicalGaps

    chitta = get_chitta_service()
    gestalt = await chitta.get_gestalt(family_id)

    if not gestalt:
        raise HTTPException(status_code=404, detail="Family not found")

    child = await chitta._child_service.get_or_create_child_async(family_id)

    gap_detector = ClinicalGaps()
    readiness = gap_detector.check_readiness(
        recipient_type=request.recipient_type,
        understanding=gestalt.understanding,
        child=child,
    )

    gaps_list = [
        {"field": g.field, "description": g.parent_description, "question": g.parent_question}
        for g in readiness.missing_critical + readiness.missing_important
    ]
    gestalt.session_flags["preparing_summary_for"] = request.recipient_type
    gestalt.session_flags["guided_collection_gaps"] = gaps_list

    await chitta._persist_gestalt(family_id, gestalt)

    first_gap = gaps_list[0] if gaps_list else None
    if first_gap:
        field = first_gap.get("field", "")
        if field == "birth_history":
            greeting = "הי! לפני שנכין את הסיכום, ספרי לי קצת על הלידה - איך היא הייתה?"
        elif field == "milestones":
            greeting = "הי! בואי נדבר רגע על ההתחלות שלו - זוכרת מתי התחיל ללכת? ומה עם מילים ראשונות?"
        elif field == "family_developmental_history":
            greeting = "הי! יש משהו שהייתי רוצה לשאול - יש במשפחה עוד מישהו שהוא קצת דומה לו?"
        else:
            question = first_gap.get("question", "")
            greeting = f"הי! רציתי לשאול משהו לפני שנכין את הסיכום. {question}"
    else:
        greeting = "הי! יש משהו שתרצי לספר לי לפני שנכין את הסיכום?"

    return {
        "status": "guided_collection_started",
        "recipient_type": request.recipient_type,
        "gaps_to_collect": [
            {"field": g.field, "description": g.parent_description}
            for g in readiness.missing_critical + readiness.missing_important
        ],
        "greeting": greeting,
    }


@router.post("/{family_id}/child-space/share/guided-collection/end")
async def end_guided_collection(
    family_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    End guided collection mode.
    """
    from app.chitta.service import get_chitta_service

    chitta = get_chitta_service()
    gestalt = await chitta.get_gestalt(family_id)

    if not gestalt:
        raise HTTPException(status_code=404, detail="Family not found")

    gestalt.session_flags.pop("preparing_summary_for", None)
    gestalt.session_flags.pop("guided_collection_gaps", None)

    await chitta._persist_gestalt(family_id, gestalt)

    return {"status": "guided_collection_ended"}


class GenerateSummaryRequest(BaseModel):
    """Request to generate shareable summary."""
    expert: Optional[Dict[str, Any]] = None
    expert_description: Optional[str] = None
    context: Optional[str] = None
    crystal_insights: Optional[Dict[str, Any]] = None
    comprehensive: bool = False
    missing_gaps: Optional[List[Dict[str, Any]]] = None
    recipient_type: Optional[str] = None
    recipient_subtype: Optional[str] = None
    time_available: str = "standard"


@router.post("/{family_id}/child-space/share/generate")
async def generate_shareable_summary(
    family_id: str,
    request: GenerateSummaryRequest,
    auth: RequireAuth = Depends(RequireAuth())
):
    """
    Generate a shareable summary adapted for the recipient.
    """
    auth.verify_access(family_id)

    from app.chitta.service import get_chitta_service
    chitta = get_chitta_service()

    result = await chitta.generate_shareable_summary(
        family_id=family_id,
        expert=request.expert,
        expert_description=request.expert_description,
        crystal_insights=request.crystal_insights,
        additional_context=request.context,
        comprehensive=request.comprehensive,
        missing_gaps=request.missing_gaps,
    )

    if result.get("error") and not result.get("content"):
        raise HTTPException(status_code=500, detail=result["error"])

    return result


@router.get("/{family_id}/child-space/share/summaries/{summary_id}")
async def get_saved_summary(
    family_id: str,
    summary_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get a previously saved summary by ID.
    """
    from app.chitta.service import get_chitta_service
    chitta = get_chitta_service()

    gestalt = await chitta.get_gestalt(family_id)
    if not gestalt:
        raise HTTPException(status_code=404, detail="Family not found")

    # Find the summary in shared_summaries
    for summary in getattr(gestalt, 'shared_summaries', []):
        if summary.get('id') == summary_id:
            return summary

    raise HTTPException(status_code=404, detail=f"Summary {summary_id} not found")
