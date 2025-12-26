"""
Dashboard API Routes - Team Dashboard for Expert Reviewers

All endpoints require admin access (is_admin=True on User).

Provides:
- /dashboard/children - List all children with stats
- /dashboard/children/{id}/full - Complete Darshan state
- /dashboard/children/{id}/curiosities - Curiosity explorer
- /dashboard/children/{id}/notes - Clinical notes CRUD
- /dashboard/children/{id}/flags - Inference flags
- /dashboard/analytics/* - Aggregate analytics
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import uuid

from app.db.dependencies import get_current_admin_user, get_uow
from app.db.repositories import UnitOfWork
from app.db.models_auth import User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
logger = logging.getLogger(__name__)


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class ChildListItem(BaseModel):
    """Summary of a child for the list view."""
    child_id: str
    child_name: Optional[str] = None
    child_age_months: Optional[float] = None
    observation_count: int = 0
    curiosity_count: int = 0
    pattern_count: int = 0
    last_activity: Optional[datetime] = None
    has_crystal: bool = False
    unresolved_flags: int = 0


class ChildListResponse(BaseModel):
    """Response for children list endpoint."""
    children: List[ChildListItem]
    total: int


class CuriosityDetail(BaseModel):
    """Detailed view of a curiosity."""
    focus: str
    type: str
    pull: float
    certainty: float
    status: str
    theory: Optional[str] = None
    domain: Optional[str] = None
    evidence: List[Dict[str, Any]] = []
    times_explored: int = 0
    last_activated: Optional[datetime] = None
    is_perpetual: bool = False
    # Video recommendation fields (for hypotheses)
    video_appropriate: bool = False
    video_value: Optional[str] = None
    video_value_reason: Optional[str] = None


class CuriositiesResponse(BaseModel):
    """Response for curiosities endpoint."""
    perpetual: List[CuriosityDetail]
    dynamic: List[CuriosityDetail]
    total: int


class CreateNoteRequest(BaseModel):
    """Request to create a clinical note."""
    target_type: str
    target_id: str
    content: str
    note_type: str = "annotation"


class NoteResponse(BaseModel):
    """Response for a clinical note."""
    id: str
    child_id: str
    target_type: str
    target_id: str
    content: str
    note_type: str
    author_name: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class CreateFlagRequest(BaseModel):
    """Request to create an inference flag."""
    target_type: str
    target_id: str
    target_label: Optional[str] = None  # Human-readable content of the flagged item
    flag_type: str
    reason: str
    suggested_correction: Optional[str] = None


class FlagResponse(BaseModel):
    """Response for an inference flag."""
    id: str
    child_id: str
    target_type: str
    target_id: str
    target_label: Optional[str] = None  # Human-readable content
    flag_type: str
    reason: str
    suggested_correction: Optional[str] = None
    author_name: str
    created_at: datetime
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by_name: Optional[str] = None
    resolution_notes: Optional[str] = None


class ResolveFlagRequest(BaseModel):
    """Request to resolve a flag."""
    resolution_notes: str


class AdjustCertaintyRequest(BaseModel):
    """Request to adjust curiosity certainty."""
    curiosity_focus: str  # Moved to body to avoid URL encoding issues with Hebrew
    new_certainty: float = Field(ge=0.0, le=1.0)
    reason: str


class AddEvidenceRequest(BaseModel):
    """Request to add expert evidence."""
    curiosity_focus: str  # Moved to body to avoid URL encoding issues with Hebrew
    content: str
    effect: str  # supports, contradicts, transforms


class TimelineEvent(BaseModel):
    """A single event in the child's timeline."""
    timestamp: datetime
    event_type: str  # message_sent, message_received, observation_extracted, curiosity_spawned, etc.
    category: str  # conversation, understanding, curiosity, video, synthesis
    title: str  # Human-readable title
    description: Optional[str] = None
    domain: Optional[str] = None
    data: Dict[str, Any] = {}  # Event-specific data


class TimelineResponse(BaseModel):
    """Response for timeline endpoint."""
    child_id: str
    child_name: Optional[str] = None
    events: List[TimelineEvent]
    total_events: int
    filters_applied: Dict[str, Any] = {}


# =============================================================================
# CHILDREN LIST ENDPOINTS
# =============================================================================

@router.get("/children", response_model=ChildListResponse)
async def list_all_children(
    search: Optional[str] = Query(None, description="Search by child name"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin: User = Depends(get_current_admin_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    List all children with summary stats.

    Admin access required - shows all children across all families.
    """
    from app.chitta.service import get_chitta_service

    logger.info(f"Dashboard: Admin {admin.email} listing children (search={search}, limit={limit})")

    chitta = get_chitta_service()

    # Get all children from database
    all_children = await uow.children.get_all()

    children = []
    for child in all_children:
        child_id = str(child.id)
        try:
            darshan = await chitta._gestalt_manager.get_darshan(child_id)
            if not darshan:
                continue

            # Apply search filter
            if search and darshan.child_name:
                if search.lower() not in darshan.child_name.lower():
                    continue
            elif search:
                continue  # Skip children without names when searching

            # Get flag count
            flags = await uow.dashboard.flags.get_by_child(child_id, include_resolved=False, limit=1000)

            children.append(ChildListItem(
                child_id=child_id,
                child_name=darshan.child_name,
                child_age_months=darshan.child_age_months if hasattr(darshan, 'child_age_months') else None,
                observation_count=len(darshan.understanding.observations) if darshan.understanding else 0,
                curiosity_count=len(darshan._curiosities._perpetual) + len(darshan._curiosities._dynamic) if darshan._curiosities else 0,
                pattern_count=len(darshan.understanding.patterns) if darshan.understanding else 0,
                last_activity=darshan.last_activity if hasattr(darshan, 'last_activity') else None,
                has_crystal=darshan.crystal is not None,
                unresolved_flags=len(flags),
            ))
        except Exception as e:
            logger.warning(f"Error loading child {child_id}: {e}")
            continue

    # Sort by last activity (most recent first), handle None
    children.sort(key=lambda c: c.last_activity or datetime.min, reverse=True)

    # Apply pagination
    total = len(children)
    children = children[offset:offset + limit]

    return ChildListResponse(children=children, total=total)


@router.get("/children/{child_id}/full")
async def get_child_full(
    child_id: str,
    admin: User = Depends(get_current_admin_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Get complete Darshan state for a child.

    Returns everything: understanding, curiosities, stories, crystal, etc.
    """
    from app.chitta.service import get_chitta_service

    logger.info(f"Dashboard: Admin {admin.email} viewing full state for child {child_id}")

    chitta = get_chitta_service()
    darshan = await chitta._gestalt_manager.get_darshan(child_id)

    if not darshan:
        raise HTTPException(status_code=404, detail="Child not found")

    # Get feedback data
    feedback_summary = await uow.dashboard.get_child_feedback_summary(child_id)

    return {
        "child_id": child_id,
        "child_name": darshan.child_name,
        "child_gender": darshan.child_gender,
        "understanding": {
            "observations": [
                {
                    "content": obs.content,
                    "domain": obs.domain,
                    "confidence": obs.confidence,
                    "source": obs.source,
                    "timestamp": obs.t_created.isoformat() if hasattr(obs, 't_created') and obs.t_created else None,
                }
                for obs in (darshan.understanding.observations if darshan.understanding else [])
            ],
            "patterns": [
                {
                    "description": p.description,
                    "domains": p.domains,
                    "confidence": p.confidence,
                    "detected_at": p.detected_at.isoformat() if hasattr(p, 'detected_at') and p.detected_at else None,
                }
                for p in (darshan.understanding.patterns if darshan.understanding else [])
            ],
            "milestones": [
                {
                    "description": m.description,
                    "domain": m.domain,
                    "type": m.type,
                    "age_months": m.age_months,
                    "recorded_at": m.recorded_at.isoformat() if hasattr(m, 'recorded_at') and m.recorded_at else None,
                }
                for m in (darshan.understanding.milestones if darshan.understanding else [])
            ],
        },
        "curiosities": {
            "perpetual": [_curiosity_to_dict(c, is_perpetual=True) for c in darshan._curiosities._perpetual],
            "dynamic": [_curiosity_to_dict(c, is_perpetual=False) for c in darshan._curiosities._dynamic],
        },
        "stories": [
            {
                "summary": s.summary,
                "domains": s.domains,
                "significance": s.significance,
                "timestamp": s.timestamp.isoformat() if s.timestamp else None,
            }
            for s in (darshan.stories or [])
        ],
        "crystal": _crystal_to_dict(darshan.crystal) if darshan.crystal else None,
        "session_history_length": len(darshan.session_history) if darshan.session_history else 0,
        "feedback": feedback_summary,
        "videos": _extract_videos_from_darshan(darshan),
    }


# =============================================================================
# CURIOSITIES ENDPOINTS
# =============================================================================

@router.get("/children/{child_id}/curiosities", response_model=CuriositiesResponse)
async def get_child_curiosities(
    child_id: str,
    admin: User = Depends(get_current_admin_user),
):
    """Get all curiosities for a child with full details."""
    from app.chitta.service import get_chitta_service

    chitta = get_chitta_service()
    darshan = await chitta._gestalt_manager.get_darshan(child_id)

    if not darshan:
        raise HTTPException(status_code=404, detail="Child not found")

    perpetual = [
        CuriosityDetail(**_curiosity_to_dict(c, is_perpetual=True))
        for c in darshan._curiosities._perpetual
    ]
    dynamic = [
        CuriosityDetail(**_curiosity_to_dict(c, is_perpetual=False))
        for c in darshan._curiosities._dynamic
    ]

    return CuriositiesResponse(
        perpetual=perpetual,
        dynamic=dynamic,
        total=len(perpetual) + len(dynamic),
    )


@router.post("/children/{child_id}/adjust-certainty")
async def adjust_curiosity_certainty(
    child_id: str,
    request: AdjustCertaintyRequest,
    admin: User = Depends(get_current_admin_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Adjust the certainty of a curiosity.

    Creates an audit record and updates Darshan state.
    Note: curiosity_focus is in request body to avoid URL encoding issues with Hebrew.
    """
    from app.chitta.service import get_chitta_service

    curiosity_focus = request.curiosity_focus
    logger.info(f"Dashboard: Admin {admin.email} adjusting certainty for '{curiosity_focus}' in child {child_id}")

    chitta = get_chitta_service()
    darshan = await chitta._gestalt_manager.get_darshan(child_id)

    if not darshan:
        raise HTTPException(status_code=404, detail="Child not found")

    # Find the curiosity
    curiosity = darshan._curiosities.get_by_focus(curiosity_focus)
    if not curiosity:
        raise HTTPException(status_code=404, detail="Curiosity not found")

    original_certainty = curiosity.certainty

    # Update the curiosity
    curiosity.certainty = request.new_certainty

    # Save Darshan state
    await chitta._gestalt_manager.persist_darshan(child_id, darshan)

    # Create audit record
    await uow.dashboard.adjustments.create_adjustment(
        child_id=child_id,
        curiosity_focus=curiosity_focus,
        original_certainty=original_certainty,
        adjusted_certainty=request.new_certainty,
        reason=request.reason,
        author_id=admin.id,
        author_name=admin.display_name,
    )
    await uow.commit()

    return {
        "success": True,
        "curiosity_focus": curiosity_focus,
        "original_certainty": original_certainty,
        "new_certainty": request.new_certainty,
    }


@router.post("/children/{child_id}/add-evidence")
async def add_expert_evidence(
    child_id: str,
    request: AddEvidenceRequest,
    admin: User = Depends(get_current_admin_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Add expert evidence to a curiosity.

    Updates certainty based on effect and records the evidence.
    Note: curiosity_focus is in request body to avoid URL encoding issues with Hebrew.
    """
    from app.chitta.service import get_chitta_service
    from app.chitta.models import Evidence

    curiosity_focus = request.curiosity_focus
    logger.info(f"Dashboard: Admin {admin.email} adding evidence to '{curiosity_focus}' in child {child_id}")

    chitta = get_chitta_service()
    darshan = await chitta._gestalt_manager.get_darshan(child_id)

    if not darshan:
        raise HTTPException(status_code=404, detail="Child not found")

    # Find the curiosity
    curiosity = darshan._curiosities.get_by_focus(curiosity_focus)
    if not curiosity:
        raise HTTPException(status_code=404, detail="Curiosity not found")

    # Create evidence and add to investigation
    evidence = Evidence(
        content=request.content,
        effect=request.effect,
        source="clinical_expert",
        timestamp=datetime.now(),
    )

    # Ensure investigation exists
    if not curiosity.investigation:
        from app.chitta.curiosity import InvestigationContext
        curiosity.investigation = InvestigationContext.create()

    curiosity.investigation.add_evidence(evidence)

    # Apply certainty effect
    original_certainty = curiosity.certainty
    if request.effect == "supports":
        curiosity.certainty = min(1.0, curiosity.certainty + 0.1)
    elif request.effect == "contradicts":
        curiosity.certainty = max(0.0, curiosity.certainty - 0.15)
    elif request.effect == "transforms":
        curiosity.certainty = 0.4

    # Save Darshan state
    await chitta._gestalt_manager.persist_darshan(child_id, darshan)

    # Record in database
    db_evidence = await uow.dashboard.evidence.create_evidence(
        child_id=child_id,
        curiosity_focus=curiosity_focus,
        content=request.content,
        effect=request.effect,
        author_id=admin.id,
        author_name=admin.display_name,
    )

    # Mark as applied
    await uow.dashboard.evidence.mark_applied(db_evidence.id)
    await uow.commit()

    return {
        "success": True,
        "evidence_id": str(db_evidence.id),
        "original_certainty": original_certainty,
        "new_certainty": curiosity.certainty,
    }


# =============================================================================
# OBSERVATIONS ENDPOINTS
# =============================================================================

class UpdateObservationDomainRequest(BaseModel):
    """Request to update an observation's domain."""
    observation_content: str  # Used to identify the observation
    new_domain: str
    reason: str


@router.post("/children/{child_id}/observations/update-domain")
async def update_observation_domain(
    child_id: str,
    request: UpdateObservationDomainRequest,
    admin: User = Depends(get_current_admin_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Update the domain of an observation.

    Finds the observation by content and updates its domain.
    Creates an audit record of the change.
    """
    from app.chitta.service import get_chitta_service

    logger.info(f"Dashboard: Admin {admin.email} updating observation domain for child {child_id}")

    chitta = get_chitta_service()
    darshan = await chitta._gestalt_manager.get_darshan(child_id)

    if not darshan:
        raise HTTPException(status_code=404, detail="Child not found")

    # Find the observation by content (try exact match first, then normalized)
    observation_found = None
    original_domain = None
    normalized_content = request.observation_content.strip()

    for obs in darshan.understanding.observations:
        obs_content = obs.content.strip() if obs.content else ""
        if obs_content == normalized_content or normalized_content in obs_content or obs_content in normalized_content:
            observation_found = obs
            original_domain = obs.domain
            break

    # If observation not in darshan.understanding (legacy data), add it
    if not observation_found:
        from app.chitta.models import TemporalFact
        observation_found = TemporalFact(
            content=normalized_content,
            domain=request.new_domain,  # Will be set to new domain
            source="conversation",
        )
        original_domain = "unknown"
        darshan.understanding.add_observation(observation_found)
        logger.info(f"Added missing observation to understanding: '{normalized_content[:50]}...'")

    # Update the domain in Darshan state
    observation_found.domain = request.new_domain

    # Save Darshan state
    await chitta._gestalt_manager.persist_darshan(child_id, darshan)

    # Also update the cognitive_turns table so timeline reflects the change
    try:
        from sqlalchemy.orm.attributes import flag_modified
        import json

        turns = await uow.dashboard.cognitive_turns.get_by_child(child_id, limit=200)
        for turn in turns:
            if not turn.tool_calls:
                continue
            tool_calls = turn.tool_calls if isinstance(turn.tool_calls, list) else json.loads(turn.tool_calls)
            updated = False
            for tc in tool_calls:
                tool_name = tc.get("name") or tc.get("tool_name")
                if tool_name == "notice":
                    obs_content = tc.get("arguments", {}).get("observation", "").strip()
                    if obs_content == normalized_content or normalized_content in obs_content or obs_content in normalized_content:
                        tc["arguments"]["domain"] = request.new_domain
                        updated = True
                        logger.info(f"Updated domain in cognitive_turn {turn.turn_id}")
            if updated:
                turn.tool_calls = tool_calls  # Assign the modified list/dict
                flag_modified(turn, "tool_calls")  # Tell SQLAlchemy the column changed
        await uow.session.flush()
    except Exception as e:
        logger.warning(f"Could not update cognitive_turns: {e}", exc_info=True)

    # Create audit record
    await uow.dashboard.corrections.create_correction(
        turn_id="manual_edit",
        child_id=child_id,
        target_type="observation",
        target_id=None,
        correction_type="domain_change",
        original_value={"content": request.observation_content, "domain": original_domain},
        corrected_value={"content": request.observation_content, "domain": request.new_domain},
        expert_reasoning=request.reason,
        expert_id=admin.id,
        expert_name=admin.display_name,
        severity="low",
    )
    await uow.commit()

    return {
        "success": True,
        "observation_content": request.observation_content,
        "original_domain": original_domain,
        "new_domain": request.new_domain,
    }


# =============================================================================
# VIDEOS ENDPOINTS
# =============================================================================

class VideoObservation(BaseModel):
    """An observation from video analysis."""
    content: str
    timestamp_start: Optional[str] = None
    timestamp_end: Optional[str] = None
    domain: Optional[str] = None
    effect: Optional[str] = None


class VideoScenarioResponse(BaseModel):
    """Full video scenario details."""
    id: str
    title: str
    status: str  # pending, uploaded, analyzed, validation_failed, needs_confirmation, acknowledged, rejected
    category: str = "hypothesis_test"  # hypothesis_test, pattern_exploration, strength_baseline, baseline, long_absence, returning
    what_to_film: Optional[str] = None
    rationale_for_parent: Optional[str] = None
    duration_suggestion: Optional[str] = None
    target_hypothesis_id: Optional[str] = None
    target_hypothesis_focus: Optional[str] = None
    what_we_hope_to_learn: Optional[str] = None
    focus_points: List[str] = []
    video_path: Optional[str] = None
    created_at: Optional[datetime] = None
    uploaded_at: Optional[datetime] = None
    analyzed_at: Optional[datetime] = None
    # Analysis results
    observations: List[VideoObservation] = []
    strengths_observed: List[str] = []
    insights: List[str] = []
    certainty_before: Optional[float] = None
    certainty_after: Optional[float] = None


class VideosResponse(BaseModel):
    """Response for videos list endpoint."""
    videos: List[VideoScenarioResponse]
    total: int


@router.get("/children/{child_id}/videos", response_model=VideosResponse)
async def get_child_videos(
    child_id: str,
    status: Optional[str] = Query(None, description="Filter by status"),
    admin: User = Depends(get_current_admin_user),
):
    """
    Get all video scenarios for a child.

    Extracts videos from all curiosities' investigation contexts.
    """
    from app.chitta.service import get_chitta_service

    logger.info(f"Dashboard: Admin {admin.email} getting videos for child {child_id}")

    chitta = get_chitta_service()
    darshan = await chitta._gestalt_manager.get_darshan(child_id)

    if not darshan:
        raise HTTPException(status_code=404, detail="Child not found")

    videos = []

    # Extract videos from all curiosities with investigations
    for curiosity in darshan._curiosities._dynamic:
        if not curiosity.investigation:
            continue

        for scenario in curiosity.investigation.video_scenarios:
            # Apply status filter
            if status and scenario.status != status:
                continue

            # Extract observations from analysis
            observations = []
            strengths = []
            insights = []

            if scenario.analysis_result and scenario.status == "analyzed":
                for obs in scenario.analysis_result.get("observations", []):
                    observations.append(VideoObservation(
                        content=obs.get("content", ""),
                        timestamp_start=obs.get("timestamp_start", obs.get("timestamp", "")),
                        timestamp_end=obs.get("timestamp_end", ""),
                        domain=obs.get("domain", "general"),
                        effect=obs.get("effect", "neutral"),
                    ))

                for s in scenario.analysis_result.get("strengths_observed", []):
                    if isinstance(s, dict):
                        strengths.append(s.get("strength", ""))
                    elif isinstance(s, str):
                        strengths.append(s)

                insights = scenario.analysis_result.get("insights", [])

            videos.append(VideoScenarioResponse(
                id=scenario.id,
                title=scenario.title,
                status=scenario.status,
                category=getattr(scenario, 'category', 'hypothesis_test'),
                what_to_film=scenario.what_to_film,
                rationale_for_parent=scenario.rationale_for_parent,
                duration_suggestion=scenario.duration_suggestion,
                target_hypothesis_id=scenario.target_hypothesis_id,
                target_hypothesis_focus=curiosity.focus,
                what_we_hope_to_learn=scenario.what_we_hope_to_learn,
                focus_points=scenario.focus_points or [],
                video_path=scenario.video_path,
                created_at=scenario.created_at,
                uploaded_at=scenario.uploaded_at,
                analyzed_at=scenario.analyzed_at,
                observations=observations,
                strengths_observed=strengths,
                insights=insights,
                certainty_before=None,  # TODO: Track this
                certainty_after=curiosity.certainty if scenario.status == "analyzed" else None,
            ))

    # Sort by most recent first
    videos.sort(key=lambda v: v.uploaded_at or v.created_at or datetime.min, reverse=True)

    return VideosResponse(videos=videos, total=len(videos))


@router.get("/children/{child_id}/videos/{video_id}")
async def get_video_detail(
    child_id: str,
    video_id: str,
    admin: User = Depends(get_current_admin_user),
):
    """Get detailed video scenario with analysis."""
    from app.chitta.service import get_chitta_service

    chitta = get_chitta_service()
    darshan = await chitta._gestalt_manager.get_darshan(child_id)

    if not darshan:
        raise HTTPException(status_code=404, detail="Child not found")

    # Find the video
    for curiosity in darshan._curiosities._dynamic:
        if not curiosity.investigation:
            continue

        for scenario in curiosity.investigation.video_scenarios:
            if scenario.id == video_id:
                # Build full response
                observations = []
                strengths = []
                insights = []

                if scenario.analysis_result and scenario.status == "analyzed":
                    for obs in scenario.analysis_result.get("observations", []):
                        observations.append({
                            "content": obs.get("content", ""),
                            "timestamp_start": obs.get("timestamp_start", obs.get("timestamp", "")),
                            "timestamp_end": obs.get("timestamp_end", ""),
                            "domain": obs.get("domain", "general"),
                            "effect": obs.get("effect", "neutral"),
                        })

                    for s in scenario.analysis_result.get("strengths_observed", []):
                        if isinstance(s, dict):
                            strengths.append(s.get("strength", ""))
                        elif isinstance(s, str):
                            strengths.append(s)

                    insights = scenario.analysis_result.get("insights", [])

                return {
                    "id": scenario.id,
                    "title": scenario.title,
                    "status": scenario.status,
                    "category": getattr(scenario, 'category', 'hypothesis_test'),
                    "what_to_film": scenario.what_to_film,
                    "rationale_for_parent": scenario.rationale_for_parent,
                    "duration_suggestion": scenario.duration_suggestion,
                    "target_hypothesis_id": scenario.target_hypothesis_id,
                    "target_hypothesis_focus": curiosity.focus,
                    "what_we_hope_to_learn": scenario.what_we_hope_to_learn,
                    "focus_points": scenario.focus_points or [],
                    "video_path": scenario.video_path,
                    "created_at": scenario.created_at.isoformat() if scenario.created_at else None,
                    "uploaded_at": scenario.uploaded_at.isoformat() if scenario.uploaded_at else None,
                    "analyzed_at": scenario.analyzed_at.isoformat() if scenario.analyzed_at else None,
                    "observations": observations,
                    "strengths_observed": strengths,
                    "insights": insights,
                    "analysis_result": scenario.analysis_result,
                    "hypothesis": {
                        "focus": curiosity.focus,
                        "theory": curiosity.theory,
                        "certainty": curiosity.certainty,
                        "domain": curiosity.domain,
                    },
                }

    raise HTTPException(status_code=404, detail="Video not found")


# =============================================================================
# VIDEO FEEDBACK ENDPOINTS
# =============================================================================

class VideoFeedbackRequest(BaseModel):
    """Request to save video feedback."""
    quality: str  # adequate, inadequate
    notes: Optional[str] = None


class VideoFeedbackResponse(BaseModel):
    """Response for video feedback."""
    id: str
    child_id: str
    video_id: str
    quality: str
    notes: Optional[str]
    author_name: str
    created_at: datetime
    updated_at: Optional[datetime]


@router.get("/children/{child_id}/videos/{video_id}/feedback", response_model=Optional[VideoFeedbackResponse])
async def get_video_feedback(
    child_id: str,
    video_id: str,
    admin: User = Depends(get_current_admin_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """Get existing feedback for a video."""
    from app.db.models_dashboard import VideoFeedback
    from sqlalchemy import select

    async with uow:
        result = await uow.session.execute(
            select(VideoFeedback).where(
                VideoFeedback.child_id == child_id,
                VideoFeedback.video_id == video_id
            )
        )
        feedback = result.scalar_one_or_none()

        if not feedback:
            return None

        return VideoFeedbackResponse(
            id=str(feedback.id),
            child_id=feedback.child_id,
            video_id=feedback.video_id,
            quality=feedback.quality,
            notes=feedback.notes,
            author_name=feedback.author_name,
            created_at=feedback.created_at,
            updated_at=feedback.updated_at,
        )


@router.post("/children/{child_id}/videos/{video_id}/feedback", response_model=VideoFeedbackResponse)
async def save_video_feedback(
    child_id: str,
    video_id: str,
    request: VideoFeedbackRequest,
    admin: User = Depends(get_current_admin_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """Save or update feedback for a video."""
    from app.db.models_dashboard import VideoFeedback
    from sqlalchemy import select
    import uuid

    logger.info(f"Dashboard: Admin {admin.email} saving feedback for video {video_id}")

    async with uow:
        # Check if feedback already exists
        result = await uow.session.execute(
            select(VideoFeedback).where(
                VideoFeedback.child_id == child_id,
                VideoFeedback.video_id == video_id
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing feedback
            existing.quality = request.quality
            existing.notes = request.notes
            existing.author_name = admin.display_name or admin.email
            existing.author_id = admin.id
            await uow.commit()
            await uow.session.refresh(existing)
            feedback = existing
        else:
            # Create new feedback
            feedback = VideoFeedback(
                id=uuid.uuid4(),
                child_id=child_id,
                video_id=video_id,
                quality=request.quality,
                notes=request.notes,
                author_id=admin.id,
                author_name=admin.display_name or admin.email,
            )
            uow.session.add(feedback)
            await uow.commit()
            await uow.session.refresh(feedback)

        return VideoFeedbackResponse(
            id=str(feedback.id),
            child_id=feedback.child_id,
            video_id=feedback.video_id,
            quality=feedback.quality,
            notes=feedback.notes,
            author_name=feedback.author_name,
            created_at=feedback.created_at,
            updated_at=feedback.updated_at,
        )


# =============================================================================
# NOTES ENDPOINTS
# =============================================================================

@router.get("/children/{child_id}/notes", response_model=List[NoteResponse])
async def get_child_notes(
    child_id: str,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    admin: User = Depends(get_current_admin_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """Get clinical notes for a child."""
    notes = await uow.dashboard.notes.get_by_child(
        child_id,
        target_type=target_type,
        target_id=target_id,
        limit=limit,
        offset=offset,
    )

    return [
        NoteResponse(
            id=str(n.id),
            child_id=n.child_id,
            target_type=n.target_type,
            target_id=n.target_id,
            content=n.content,
            note_type=n.note_type,
            author_name=n.author_name,
            created_at=n.created_at,
            updated_at=n.updated_at,
        )
        for n in notes
    ]


@router.post("/children/{child_id}/notes", response_model=NoteResponse)
async def create_note(
    child_id: str,
    request: CreateNoteRequest,
    admin: User = Depends(get_current_admin_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """Create a new clinical note."""
    note = await uow.dashboard.notes.create_note(
        child_id=child_id,
        target_type=request.target_type,
        target_id=request.target_id,
        content=request.content,
        note_type=request.note_type,
        author_id=admin.id,
        author_name=admin.display_name,
    )
    await uow.commit()

    return NoteResponse(
        id=str(note.id),
        child_id=note.child_id,
        target_type=note.target_type,
        target_id=note.target_id,
        content=note.content,
        note_type=note.note_type,
        author_name=note.author_name,
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


@router.put("/notes/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: str,
    content: str,
    admin: User = Depends(get_current_admin_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """Update a clinical note."""
    note = await uow.dashboard.notes.update(uuid.UUID(note_id), content=content)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    await uow.commit()

    return NoteResponse(
        id=str(note.id),
        child_id=note.child_id,
        target_type=note.target_type,
        target_id=note.target_id,
        content=note.content,
        note_type=note.note_type,
        author_name=note.author_name,
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


@router.delete("/notes/{note_id}")
async def delete_note(
    note_id: str,
    admin: User = Depends(get_current_admin_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """Soft delete a clinical note."""
    success = await uow.dashboard.notes.soft_delete(uuid.UUID(note_id))
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")

    await uow.commit()
    return {"success": True}


# =============================================================================
# FLAGS ENDPOINTS
# =============================================================================

@router.get("/children/{child_id}/flags", response_model=List[FlagResponse])
async def get_child_flags(
    child_id: str,
    include_resolved: bool = False,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    admin: User = Depends(get_current_admin_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """Get inference flags for a child."""
    flags = await uow.dashboard.flags.get_by_child(
        child_id,
        include_resolved=include_resolved,
        limit=limit,
        offset=offset,
    )

    return [
        FlagResponse(
            id=str(f.id),
            child_id=f.child_id,
            target_type=f.target_type,
            target_id=f.target_id,
            target_label=f.target_label,
            flag_type=f.flag_type,
            reason=f.reason,
            suggested_correction=f.suggested_correction,
            author_name=f.author_name,
            created_at=f.created_at,
            is_resolved=f.is_resolved,
            resolved_at=f.resolved_at,
            resolved_by_name=f.resolved_by_name,
            resolution_notes=f.resolution_notes,
        )
        for f in flags
    ]


@router.post("/children/{child_id}/flags", response_model=FlagResponse)
async def create_flag(
    child_id: str,
    request: CreateFlagRequest,
    admin: User = Depends(get_current_admin_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """Create a new inference flag."""
    flag = await uow.dashboard.flags.create_flag(
        child_id=child_id,
        target_type=request.target_type,
        target_id=request.target_id,
        target_label=request.target_label,
        flag_type=request.flag_type,
        reason=request.reason,
        suggested_correction=request.suggested_correction,
        author_id=admin.id,
        author_name=admin.display_name,
    )
    await uow.commit()

    return FlagResponse(
        id=str(flag.id),
        child_id=flag.child_id,
        target_type=flag.target_type,
        target_id=flag.target_id,
        target_label=flag.target_label,
        flag_type=flag.flag_type,
        reason=flag.reason,
        suggested_correction=flag.suggested_correction,
        author_name=flag.author_name,
        created_at=flag.created_at,
        is_resolved=False,
    )


@router.post("/flags/{flag_id}/resolve", response_model=FlagResponse)
async def resolve_flag(
    flag_id: str,
    request: ResolveFlagRequest,
    admin: User = Depends(get_current_admin_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """Resolve an inference flag."""
    flag = await uow.dashboard.flags.resolve(
        uuid.UUID(flag_id),
        resolved_by_id=admin.id,
        resolved_by_name=admin.display_name,
        resolution_notes=request.resolution_notes,
    )

    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found or already resolved")

    await uow.commit()

    return FlagResponse(
        id=str(flag.id),
        child_id=flag.child_id,
        target_type=flag.target_type,
        target_id=flag.target_id,
        target_label=flag.target_label,
        flag_type=flag.flag_type,
        reason=flag.reason,
        suggested_correction=flag.suggested_correction,
        author_name=flag.author_name,
        created_at=flag.created_at,
        is_resolved=True,
        resolved_at=flag.resolved_at,
        resolved_by_name=flag.resolved_by_name,
        resolution_notes=flag.resolution_notes,
    )


# =============================================================================
# TIMELINE / COGNITIVE TRACE ENDPOINTS
# =============================================================================


class CognitiveTurnDetail(BaseModel):
    """Detailed view of a cognitive turn for the dashboard."""
    turn_id: str
    turn_number: int
    timestamp: datetime
    # Input
    parent_message: str
    parent_role: Optional[str] = None
    # Phase 1: Perception
    tool_calls: List[Dict[str, Any]] = []
    perceived_intent: Optional[str] = None
    # State changes
    state_delta: Optional[Dict[str, Any]] = None
    # Phase 2: Response
    turn_guidance: Optional[str] = None
    active_curiosities: List[str] = []
    response_text: Optional[str] = None
    # Expert feedback
    corrections_count: int = 0
    missed_signals_count: int = 0


class CognitiveTimelineResponse(BaseModel):
    """Response for cognitive timeline endpoint."""
    child_id: str
    child_name: Optional[str] = None
    turns: List[CognitiveTurnDetail]
    total_turns: int
    total_corrections: int = 0
    total_missed_signals: int = 0


@router.get("/children/{child_id}/timeline", response_model=CognitiveTimelineResponse)
async def get_cognitive_timeline(
    child_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin: User = Depends(get_current_admin_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Get the cognitive timeline for a child.

    Returns all cognitive turns with their full traces,
    including tool calls, state deltas, and expert feedback.
    This is the primary view for the Cognitive Dashboard.
    """
    logger.info(f"Dashboard: Admin {admin.email} viewing cognitive timeline for child {child_id}")

    # Get child name if available (optional - timeline works without it)
    child_name = None
    try:
        from app.chitta.service import get_chitta_service
        chitta = get_chitta_service()
        darshan = await chitta._gestalt_manager.get_darshan(child_id)
        if darshan:
            child_name = darshan.child_name
    except Exception:
        pass  # Child name is optional for timeline view

    # Get cognitive turns from database
    db_turns = await uow.dashboard.cognitive_turns.get_by_child(
        child_id,
        limit=limit,
        offset=offset,
    )

    # Get counts for corrections and missed signals
    total_corrections = 0
    total_missed_signals = 0

    turns = []
    for turn in db_turns:
        # Get corrections and missed signals for this turn
        corrections = await uow.dashboard.corrections.get_by_turn(turn.turn_id)
        missed = await uow.dashboard.missed_signals.get_by_turn(turn.turn_id)

        total_corrections += len(corrections)
        total_missed_signals += len(missed)

        turns.append(CognitiveTurnDetail(
            turn_id=turn.turn_id,
            turn_number=turn.turn_number,
            timestamp=turn.timestamp,
            parent_message=turn.parent_message,
            parent_role=turn.parent_role,
            tool_calls=turn.tool_calls or [],
            perceived_intent=turn.perceived_intent,
            state_delta=turn.state_delta,
            turn_guidance=turn.turn_guidance,
            active_curiosities=turn.active_curiosities or [],
            response_text=turn.response_text,
            corrections_count=len(corrections),
            missed_signals_count=len(missed),
        ))

    # Get total count
    total = await uow.dashboard.cognitive_turns.count_by_child(child_id)

    return CognitiveTimelineResponse(
        child_id=child_id,
        child_name=child_name,
        turns=turns,
        total_turns=total,
        total_corrections=total_corrections,
        total_missed_signals=total_missed_signals,
    )


@router.get("/children/{child_id}/turns/{turn_id}")
async def get_cognitive_turn(
    child_id: str,
    turn_id: str,
    admin: User = Depends(get_current_admin_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Get a single cognitive turn with full details.

    Includes all corrections and missed signals for detailed review.
    """
    logger.info(f"Dashboard: Admin {admin.email} viewing turn {turn_id}")

    # Get the turn
    turn = await uow.dashboard.cognitive_turns.get_by_turn_id(turn_id)
    if not turn or turn.child_id != child_id:
        raise HTTPException(status_code=404, detail="Turn not found")

    # Get corrections
    corrections = await uow.dashboard.corrections.get_by_turn(turn_id)

    # Get missed signals
    missed_signals = await uow.dashboard.missed_signals.get_by_turn(turn_id)

    return {
        "turn": {
            "turn_id": turn.turn_id,
            "turn_number": turn.turn_number,
            "timestamp": turn.timestamp.isoformat(),
            "parent_message": turn.parent_message,
            "parent_role": turn.parent_role,
            "tool_calls": turn.tool_calls or [],
            "perceived_intent": turn.perceived_intent,
            "state_delta": turn.state_delta,
            "turn_guidance": turn.turn_guidance,
            "active_curiosities": turn.active_curiosities or [],
            "response_text": turn.response_text,
        },
        "corrections": [
            {
                "id": str(c.id),
                "target_type": c.target_type,
                "target_id": c.target_id,
                "correction_type": c.correction_type,
                "original_value": c.original_value,
                "corrected_value": c.corrected_value,
                "expert_reasoning": c.expert_reasoning,
                "expert_name": c.expert_name,
                "severity": c.severity,
                "created_at": c.created_at.isoformat(),
            }
            for c in corrections
        ],
        "missed_signals": [
            {
                "id": str(m.id),
                "signal_type": m.signal_type,
                "content": m.content,
                "domain": m.domain,
                "why_important": m.why_important,
                "expert_name": m.expert_name,
                "created_at": m.created_at.isoformat(),
            }
            for m in missed_signals
        ],
    }


class CreateCorrectionRequest(BaseModel):
    """Request to create an expert correction on a turn."""
    target_type: str  # observation, curiosity, hypothesis, evidence, video, response
    target_id: Optional[str] = None
    correction_type: str  # domain_change, extraction_error, hallucination, etc.
    original_value: Optional[Dict[str, Any]] = None
    corrected_value: Optional[Dict[str, Any]] = None
    expert_reasoning: str
    severity: str = "medium"  # low, medium, high, critical


@router.post("/children/{child_id}/turns/{turn_id}/corrections")
async def create_correction(
    child_id: str,
    turn_id: str,
    request: CreateCorrectionRequest,
    admin: User = Depends(get_current_admin_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Create an expert correction on a cognitive turn.

    This is the primary mechanism for experts to provide
    structured feedback that can be used for training.
    """
    logger.info(f"Dashboard: Admin {admin.email} creating correction on turn {turn_id}")

    # Verify turn exists
    turn = await uow.dashboard.cognitive_turns.get_by_turn_id(turn_id)
    if not turn or turn.child_id != child_id:
        raise HTTPException(status_code=404, detail="Turn not found")

    # Create correction
    correction = await uow.dashboard.corrections.create_correction(
        turn_id=turn_id,
        child_id=child_id,
        target_type=request.target_type,
        target_id=request.target_id,
        correction_type=request.correction_type,
        original_value=request.original_value,
        corrected_value=request.corrected_value,
        expert_reasoning=request.expert_reasoning,
        expert_id=admin.id,
        expert_name=admin.display_name,
        severity=request.severity,
    )
    await uow.commit()

    return {
        "success": True,
        "correction_id": str(correction.id),
        "message": "Correction recorded successfully",
    }


class CreateMissedSignalRequest(BaseModel):
    """Request to report a missed signal."""
    signal_type: str  # observation, curiosity, hypothesis
    content: str  # What should have been noticed
    domain: Optional[str] = None
    why_important: str


@router.post("/children/{child_id}/turns/{turn_id}/missed-signals")
async def create_missed_signal(
    child_id: str,
    turn_id: str,
    request: CreateMissedSignalRequest,
    admin: User = Depends(get_current_admin_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Report a signal that should have been caught.

    When an expert notices something important in the parent's
    message that the AI missed, they can document it here.
    """
    logger.info(f"Dashboard: Admin {admin.email} reporting missed signal on turn {turn_id}")

    # Verify turn exists
    turn = await uow.dashboard.cognitive_turns.get_by_turn_id(turn_id)
    if not turn or turn.child_id != child_id:
        raise HTTPException(status_code=404, detail="Turn not found")

    # Create missed signal
    missed = await uow.dashboard.missed_signals.create_missed_signal(
        turn_id=turn_id,
        child_id=child_id,
        signal_type=request.signal_type,
        content=request.content,
        domain=request.domain,
        why_important=request.why_important,
        expert_id=admin.id,
        expert_name=admin.display_name,
    )
    await uow.commit()

    return {
        "success": True,
        "missed_signal_id": str(missed.id),
        "message": "Missed signal recorded successfully",
    }


# =============================================================================
# ANALYTICS ENDPOINTS
# =============================================================================

@router.get("/analytics/overview")
async def get_analytics_overview(
    admin: User = Depends(get_current_admin_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """Get aggregate analytics overview."""
    from app.chitta.service import get_chitta_service

    chitta = get_chitta_service()

    # Get all children from database
    all_children = await uow.children.get_all()

    total_children = len(all_children)
    total_observations = 0
    total_curiosities = 0
    total_patterns = 0
    children_with_crystal = 0

    for child in all_children:
        child_id = str(child.id)
        try:
            darshan = await chitta._gestalt_manager.get_darshan(child_id)
            if darshan:
                if darshan.understanding:
                    total_observations += len(darshan.understanding.observations)
                    total_patterns += len(darshan.understanding.patterns)
                if darshan._curiosities:
                    total_curiosities += len(darshan._curiosities._perpetual) + len(darshan._curiosities._dynamic)
                if darshan.crystal:
                    children_with_crystal += 1
        except Exception:
            continue

    # Get flag stats
    total_unresolved_flags = await uow.dashboard.flags.count_unresolved()

    return {
        "total_children": total_children,
        "total_observations": total_observations,
        "total_curiosities": total_curiosities,
        "total_patterns": total_patterns,
        "children_with_crystal": children_with_crystal,
        "avg_observations_per_child": round(total_observations / total_children, 1) if total_children > 0 else 0,
        "avg_curiosities_per_child": round(total_curiosities / total_children, 1) if total_children > 0 else 0,
        "total_unresolved_flags": total_unresolved_flags,
    }


@router.get("/analytics/corrections")
async def get_correction_analytics(
    admin: User = Depends(get_current_admin_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Get detailed correction analytics.

    Returns breakdown by type, severity, and target with recent examples.
    """
    stats = await uow.dashboard.corrections.get_correction_stats()

    # Get recent corrections for examples
    recent = await uow.dashboard.corrections.get_all_with_context(used_in_training=False)
    recent_examples = [
        {
            "id": str(c.id),
            "child_id": c.child_id,
            "correction_type": c.correction_type,
            "target_type": c.target_type,
            "severity": c.severity,
            "expert_reasoning": c.expert_reasoning[:200] + "..." if len(c.expert_reasoning or "") > 200 else c.expert_reasoning,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in recent[:10]
    ]

    return {
        **stats,
        "recent_examples": recent_examples,
    }


@router.get("/analytics/missed-signals")
async def get_missed_signal_analytics(
    admin: User = Depends(get_current_admin_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Get missed signal analytics.

    Returns breakdown by signal type and domain.
    """
    stats = await uow.dashboard.missed_signals.get_signal_stats()

    # Get recent missed signals
    recent = await uow.dashboard.missed_signals.get_all()
    recent_examples = [
        {
            "id": str(s.id),
            "child_id": s.child_id,
            "signal_type": s.signal_type,
            "domain": s.domain,
            "content": s.content[:150] + "..." if len(s.content or "") > 150 else s.content,
            "why_important": s.why_important[:150] + "..." if len(s.why_important or "") > 150 else s.why_important,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in recent[:10]
    ]

    return {
        **stats,
        "recent_examples": recent_examples,
    }


@router.get("/analytics/flags")
async def get_flag_analytics(
    admin: User = Depends(get_current_admin_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Get inference flag analytics.

    Returns counts of resolved vs unresolved flags.
    """
    unresolved = await uow.dashboard.flags.count_unresolved()

    # Get all flags for stats
    all_flags = await uow.dashboard.flags.get_by_child(
        child_id="",  # We need a way to get all flags
        include_resolved=True,
        limit=1000,
    )

    # Count by flag type
    by_type = {}
    by_target = {}
    resolved_count = 0

    # Since get_by_child requires child_id, let's just use unresolved count for now
    # In a real implementation we'd add a get_all method

    return {
        "total_unresolved": unresolved,
        "by_flag_type": by_type,
        "by_target_type": by_target,
    }


@router.get("/analytics/patterns")
async def get_correction_patterns(
    admin: User = Depends(get_current_admin_user),
    uow: UnitOfWork = Depends(get_uow),
    min_occurrences: int = Query(2, description="Minimum occurrences to show pattern"),
):
    """
    Get aggregated correction patterns for training improvement.

    Identifies systematic issues by grouping similar corrections.
    """
    # Get all corrections
    all_corrections = await uow.dashboard.corrections.get_all_with_context()

    # Group by correction_type + target_type
    patterns = {}
    for c in all_corrections:
        key = f"{c.correction_type}:{c.target_type}"
        if key not in patterns:
            patterns[key] = {
                "correction_type": c.correction_type,
                "target_type": c.target_type,
                "count": 0,
                "examples": [],
                "severities": {"low": 0, "medium": 0, "high": 0},
            }
        patterns[key]["count"] += 1
        if c.severity:
            patterns[key]["severities"][c.severity] = patterns[key]["severities"].get(c.severity, 0) + 1
        if len(patterns[key]["examples"]) < 3:
            patterns[key]["examples"].append({
                "id": str(c.id),
                "child_id": c.child_id,
                "expert_reasoning": c.expert_reasoning[:200] if c.expert_reasoning else None,
            })

    # Filter by min_occurrences and sort by count
    filtered = [
        p for p in patterns.values()
        if p["count"] >= min_occurrences
    ]
    filtered.sort(key=lambda x: x["count"], reverse=True)

    # Calculate severity score for each pattern
    for p in filtered:
        total = p["count"]
        p["severity_score"] = round(
            (p["severities"].get("high", 0) * 3 + p["severities"].get("medium", 0) * 2 + p["severities"].get("low", 0)) / total,
            2
        ) if total > 0 else 0

    # Get missed signal patterns too
    missed = await uow.dashboard.missed_signals.get_all()
    missed_by_domain = {}
    for s in missed:
        domain = s.domain or "unknown"
        if domain not in missed_by_domain:
            missed_by_domain[domain] = {"count": 0, "examples": []}
        missed_by_domain[domain]["count"] += 1
        if len(missed_by_domain[domain]["examples"]) < 2:
            missed_by_domain[domain]["examples"].append(s.content[:100] if s.content else "")

    missed_patterns = [
        {"domain": k, **v}
        for k, v in missed_by_domain.items()
        if v["count"] >= min_occurrences
    ]
    missed_patterns.sort(key=lambda x: x["count"], reverse=True)

    return {
        "correction_patterns": filtered,
        "missed_signal_patterns": missed_patterns,
        "total_corrections": len(all_corrections),
        "total_missed_signals": len(missed),
    }


# =============================================================================
# TRAINING PIPELINE - PROMPT IMPROVEMENT
# =============================================================================


class PromptSuggestionResponse(BaseModel):
    """Response for a single prompt improvement suggestion."""
    priority: int
    section: str
    issue: str
    suggestion: str
    examples: List[Dict[str, Any]]
    correction_count: int
    severity_score: float


class PromptImprovementResponse(BaseModel):
    """Response for prompt improvement suggestions endpoint."""
    generated_at: datetime
    total_corrections: int
    total_missed_signals: int
    suggestion_count: int
    suggestions: List[PromptSuggestionResponse]
    stats: Dict[str, Any]


@router.get("/training/prompt-suggestions", response_model=PromptImprovementResponse)
async def get_prompt_suggestions(
    admin: User = Depends(get_current_admin_user),
    uow: UnitOfWork = Depends(get_uow),
    unused_only: bool = Query(True, description="Only analyze corrections not used in training"),
    min_corrections: int = Query(1, description="Minimum corrections to generate a suggestion"),
):
    """
    Generate prompt improvement suggestions based on expert corrections.

    Analyzes patterns in corrections to identify:
    - Which prompt sections need improvement
    - What specific issues are occurring
    - Expert reasoning examples for reference

    Suggestions are ranked by priority (severity × frequency).
    """
    from app.services.prompt_improvement import PromptImprovementService

    service = PromptImprovementService(uow)
    report = await service.generate_suggestions(
        unused_only=unused_only,
        min_corrections=min_corrections,
    )

    return report.to_dict()


@router.get("/training/correction-examples/{correction_type}")
async def get_correction_examples(
    correction_type: str,
    admin: User = Depends(get_current_admin_user),
    uow: UnitOfWork = Depends(get_uow),
    limit: int = Query(10, description="Maximum examples to return"),
):
    """
    Get detailed examples for a specific correction type.

    Useful for understanding patterns and creating training data.
    """
    from app.services.prompt_improvement import PromptImprovementService

    valid_types = [
        "domain_change", "extraction_error", "missed_signal", "hallucination",
        "evidence_reclassify", "timing_issue", "certainty_adjustment", "response_issue"
    ]

    if correction_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid correction type. Valid types: {valid_types}"
        )

    service = PromptImprovementService(uow)
    examples = await service.get_correction_examples_for_type(correction_type, limit)

    return {
        "correction_type": correction_type,
        "count": len(examples),
        "examples": examples,
    }


@router.get("/training/stats")
async def get_training_stats(
    admin: User = Depends(get_current_admin_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Get training data statistics.

    Shows correction and missed signal counts by type, severity, etc.
    """
    correction_stats = await uow.dashboard.corrections.get_correction_stats()
    signal_stats = await uow.dashboard.missed_signals.get_missed_signal_stats()

    return {
        "corrections": correction_stats,
        "missed_signals": signal_stats,
        "training_readiness": {
            "unused_corrections": correction_stats.get("unused_for_training", 0),
            "total_training_samples": correction_stats.get("total", 0) + signal_stats.get("total", 0),
        }
    }


class MarkUsedRequest(BaseModel):
    """Request to mark corrections as used in training."""
    correction_ids: List[str]
    batch_id: str


@router.post("/training/mark-used")
async def mark_corrections_used(
    request: MarkUsedRequest,
    admin: User = Depends(get_current_admin_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Mark corrections as used in training.

    Creates a training batch record.
    """
    marked = []
    for cid in request.correction_ids:
        try:
            correction = await uow.dashboard.corrections.mark_used_in_training(
                uuid.UUID(cid),
                request.batch_id,
            )
            if correction:
                marked.append(str(correction.id))
        except Exception as e:
            logger.warning(f"Failed to mark correction {cid}: {e}")

    await uow.commit()

    return {
        "batch_id": request.batch_id,
        "marked_count": len(marked),
        "marked_ids": marked,
    }


@router.get("/training/export")
async def export_training_data(
    admin: User = Depends(get_current_admin_user),
    uow: UnitOfWork = Depends(get_uow),
    unused_only: bool = Query(True, description="Only export unused corrections"),
    include_missed_signals: bool = Query(True, description="Include missed signals"),
):
    """
    Export training data as JSON.

    Returns corrections and missed signals in a format suitable for fine-tuning.
    """
    # Get corrections
    corrections = await uow.dashboard.corrections.get_all_with_context(
        used_in_training=False if unused_only else None
    )

    correction_data = []
    for c in corrections:
        correction_data.append({
            "id": str(c.id),
            "type": "correction",
            "correction_type": c.correction_type,
            "target_type": c.target_type,
            "original_value": c.original_value,
            "corrected_value": c.corrected_value,
            "expert_reasoning": c.expert_reasoning,
            "severity": c.severity,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })

    # Get missed signals
    missed_signal_data = []
    if include_missed_signals:
        missed = await uow.dashboard.missed_signals.get_all()
        for s in missed:
            missed_signal_data.append({
                "id": str(s.id),
                "type": "missed_signal",
                "signal_type": s.signal_type,
                "domain": s.domain,
                "content": s.content,
                "why_important": s.why_important,
                "context": s.context,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            })

    return {
        "exported_at": datetime.utcnow().isoformat(),
        "corrections_count": len(correction_data),
        "missed_signals_count": len(missed_signal_data),
        "corrections": correction_data,
        "missed_signals": missed_signal_data,
    }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _curiosity_to_dict(curiosity, is_perpetual: bool = False) -> Dict[str, Any]:
    """Convert a Curiosity object to a dict."""
    evidence = []
    if curiosity.investigation:
        evidence = [
            {
                "content": e.content,
                "effect": e.effect,
                "source": e.source,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            }
            for e in curiosity.investigation.evidence
        ]

    return {
        "focus": curiosity.focus,
        "type": curiosity.type,
        "pull": curiosity.pull,
        "certainty": curiosity.certainty,
        "status": curiosity.status if hasattr(curiosity, 'status') else "wondering",
        "theory": curiosity.theory if hasattr(curiosity, 'theory') else None,
        "domain": curiosity.domain if hasattr(curiosity, 'domain') else None,
        "evidence": evidence,
        "times_explored": curiosity.times_explored if hasattr(curiosity, 'times_explored') else 0,
        "last_activated": curiosity.last_activated.isoformat() if hasattr(curiosity, 'last_activated') and curiosity.last_activated else None,
        "is_perpetual": is_perpetual,
        # Video recommendation fields (for hypotheses)
        "video_appropriate": curiosity.video_appropriate if hasattr(curiosity, 'video_appropriate') else False,
        "video_value": curiosity.video_value if hasattr(curiosity, 'video_value') else None,
        "video_value_reason": curiosity.video_value_reason if hasattr(curiosity, 'video_value_reason') else None,
    }


def _crystal_to_dict(crystal) -> Dict[str, Any]:
    """Convert a Crystal object to a dict."""
    if not crystal:
        return None

    return {
        "essence_narrative": crystal.essence_narrative if hasattr(crystal, 'essence_narrative') else None,
        "temperament": crystal.temperament if hasattr(crystal, 'temperament') else [],
        "core_qualities": crystal.core_qualities if hasattr(crystal, 'core_qualities') else [],
        "patterns": [
            {
                "description": p.description if hasattr(p, 'description') else str(p),
                "domains": p.domains if hasattr(p, 'domains') else [],
                "confidence": p.confidence if hasattr(p, 'confidence') else 0.5,
            }
            for p in (crystal.patterns if hasattr(crystal, 'patterns') else [])
        ],
        "version": crystal.version if hasattr(crystal, 'version') else 1,
        "generated_at": crystal.generated_at.isoformat() if hasattr(crystal, 'generated_at') and crystal.generated_at else None,
    }


def _extract_videos_from_darshan(darshan) -> List[Dict[str, Any]]:
    """Extract all video scenarios from Darshan's curiosities."""
    videos = []

    for curiosity in darshan._curiosities._dynamic:
        if not curiosity.investigation:
            continue

        for scenario in curiosity.investigation.video_scenarios:
            # Extract observations from analysis
            observations = []
            strengths = []
            insights = []

            if scenario.analysis_result and scenario.status == "analyzed":
                for obs in scenario.analysis_result.get("observations", []):
                    observations.append({
                        "content": obs.get("content", ""),
                        "timestamp_start": obs.get("timestamp_start", obs.get("timestamp", "")),
                        "timestamp_end": obs.get("timestamp_end", ""),
                        "domain": obs.get("domain", "general"),
                        "effect": obs.get("effect", "neutral"),
                    })

                for s in scenario.analysis_result.get("strengths_observed", []):
                    if isinstance(s, dict):
                        strengths.append(s.get("strength", ""))
                    elif isinstance(s, str):
                        strengths.append(s)

                insights = scenario.analysis_result.get("insights", [])

            videos.append({
                "id": scenario.id,
                "title": scenario.title,
                "status": scenario.status,
                "category": getattr(scenario, 'category', 'hypothesis_test'),
                "what_to_film": scenario.what_to_film,
                "rationale_for_parent": scenario.rationale_for_parent,
                "duration_suggestion": scenario.duration_suggestion,
                "target_hypothesis_id": scenario.target_hypothesis_id,
                "target_hypothesis_focus": curiosity.focus,
                "what_we_hope_to_learn": scenario.what_we_hope_to_learn,
                "focus_points": scenario.focus_points or [],
                "video_path": scenario.video_path,
                "created_at": scenario.created_at.isoformat() if scenario.created_at else None,
                "uploaded_at": scenario.uploaded_at.isoformat() if scenario.uploaded_at else None,
                "analyzed_at": scenario.analyzed_at.isoformat() if scenario.analyzed_at else None,
                "observations": observations,
                "strengths_observed": strengths,
                "insights": insights,
                "certainty_after": curiosity.certainty if scenario.status == "analyzed" else None,
            })

    # Sort by most recent first
    videos.sort(key=lambda v: v.get("uploaded_at") or v.get("created_at") or "", reverse=True)

    return videos
