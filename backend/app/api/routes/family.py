"""
Family API Routes - Family management and child-space endpoints

Includes:
- /family/{family_id}/children (Family management - uses actual family_id)
- /family/{child_id}/child-space/* (Living Portrait + Sharing - uses child_id)
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging

from app.db.dependencies import get_current_user, get_uow, RequireAuth
from app.db.models_auth import User
from app.db.repositories import UnitOfWork

router = APIRouter(prefix="/family", tags=["family"])
logger = logging.getLogger(__name__)


# === Family Management Endpoints ===

class AddChildResponse(BaseModel):
    """Response for add child endpoint."""
    child_id: str


@router.post("/{family_id}/children", response_model=AddChildResponse)
async def add_child_to_family(
    family_id: str,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Add a new child placeholder to family.

    Creates an empty child that will be filled via conversation.
    """
    from app.services.family_service import get_family_service

    logger.info(f"Adding child to family {family_id} by user {current_user.email}")

    family_service = get_family_service()

    # Verify user has access to this family
    user_family_id = await family_service.get_user_family_id(str(current_user.id), uow)
    if user_family_id != family_id:
        raise HTTPException(
            status_code=403,
            detail="You don't have access to this family"
        )

    # Create new child placeholder
    child_id = await family_service.add_child_to_family(family_id, uow)

    return AddChildResponse(child_id=child_id)


# === Living Portrait (Child-Space) Endpoints ===

@router.get("/{child_id}/child-space")
async def get_child_space_full(
    child_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get complete ChildSpace data for the Living Portrait UI.
    """
    from app.chitta.service import get_chitta_service
    chitta = get_chitta_service()
    gestalt = await chitta.get_gestalt(child_id)

    if not gestalt:
        raise HTTPException(status_code=404, detail="Child not found")

    await chitta.ensure_crystal_fresh(child_id)
    gestalt = await chitta.get_gestalt(child_id)

    return chitta.derive_child_space_full(gestalt)


# === Summary Readiness & Guided Collection ===

@router.get("/{child_id}/child-space/share/readiness/{recipient_type}")
async def check_summary_readiness(
    child_id: str,
    recipient_type: str,
    current_user: User = Depends(get_current_user)
):
    """
    Check if we have enough data to generate a useful summary.
    """
    from app.chitta.service import get_chitta_service
    from app.chitta.clinical_gaps import ClinicalGaps

    chitta = get_chitta_service()
    gestalt = await chitta.get_gestalt(child_id)

    if not gestalt:
        raise HTTPException(status_code=404, detail="Child not found")

    child = await chitta._child_service.get_or_create_child_async(child_id)

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


@router.post("/{child_id}/child-space/share/guided-collection/start")
async def start_guided_collection(
    child_id: str,
    request: StartGuidedCollectionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Start guided collection mode for preparing a summary.
    """
    from app.chitta.service import get_chitta_service
    from app.chitta.clinical_gaps import ClinicalGaps

    chitta = get_chitta_service()
    gestalt = await chitta.get_gestalt(child_id)

    if not gestalt:
        raise HTTPException(status_code=404, detail="Child not found")

    child = await chitta._child_service.get_or_create_child_async(child_id)

    gap_detector = ClinicalGaps()
    readiness = gap_detector.check_readiness(
        recipient_type=request.recipient_type,
        understanding=gestalt.understanding,
        child=child,
    )

    # Convert gaps to list for storage
    all_gaps = readiness.missing_critical + readiness.missing_important
    gaps_list = [
        {"field": g.field, "description": g.parent_description, "question": g.parent_question}
        for g in all_gaps
    ]
    gestalt.session_flags["preparing_summary_for"] = request.recipient_type
    gestalt.session_flags["guided_collection_gaps"] = gaps_list

    await chitta._gestalt_manager.persist_darshan(child_id, gestalt)

    # Generate personalized opening question using LLM
    from app.chitta.guided_questions import (
        GuidedQuestionGenerator,
        ChildContext,
        calculate_age_months,
    )

    child_gender = gestalt.child_gender or (child.identity.gender if child and child.identity else None)
    child_birth_date = gestalt.child_birth_date or (child.identity.birth_date if child and child.identity else None)

    question_generator = GuidedQuestionGenerator()
    greeting = await question_generator.generate_opening_question(
        gaps=all_gaps,
        child_context=ChildContext(
            name=gestalt.child_name,
            gender=child_gender,
            age_months=calculate_age_months(child_birth_date),
        ),
        understanding=gestalt.understanding,
        recipient_type=request.recipient_type,
    )

    return {
        "status": "guided_collection_started",
        "recipient_type": request.recipient_type,
        "gaps_to_collect": [
            {"field": g.field, "description": g.parent_description}
            for g in readiness.missing_critical + readiness.missing_important
        ],
        "greeting": greeting,
    }


@router.post("/{child_id}/child-space/share/guided-collection/end")
async def end_guided_collection(
    child_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    End guided collection mode.
    """
    from app.chitta.service import get_chitta_service

    chitta = get_chitta_service()
    gestalt = await chitta.get_gestalt(child_id)

    if not gestalt:
        raise HTTPException(status_code=404, detail="Child not found")

    gestalt.session_flags.pop("preparing_summary_for", None)
    gestalt.session_flags.pop("guided_collection_gaps", None)

    await chitta._gestalt_manager.persist_darshan(child_id, gestalt)

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


@router.post("/{child_id}/child-space/share/generate")
async def generate_shareable_summary(
    child_id: str,
    request: GenerateSummaryRequest,
    auth: RequireAuth = Depends(RequireAuth())
):
    """
    Generate a shareable summary adapted for the recipient.
    """
    auth.verify_access(child_id)

    from app.chitta.service import get_chitta_service
    chitta = get_chitta_service()

    result = await chitta.generate_shareable_summary(
        family_id=child_id,
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


@router.get("/{child_id}/child-space/share/summaries/{summary_id}")
async def get_saved_summary(
    child_id: str,
    summary_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get a previously saved summary by ID.
    """
    from app.chitta.service import get_chitta_service
    chitta = get_chitta_service()

    gestalt = await chitta.get_gestalt(child_id)
    if not gestalt:
        raise HTTPException(status_code=404, detail="Child not found")

    # Find the summary in shared_summaries
    for summary in getattr(gestalt, 'shared_summaries', []):
        if summary.get('id') == summary_id:
            return summary

    raise HTTPException(status_code=404, detail=f"Summary {summary_id} not found")
