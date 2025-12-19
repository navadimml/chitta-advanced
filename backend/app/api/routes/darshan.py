"""
Darshan API Routes - Cards, actions, insights, and summary endpoints

Darshan (Sanskrit: "seeing") - the observing intelligence that holds,
notices, and acts on understanding about each child.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging

from app.core.app_state import app_state
from app.chitta import get_chitta_service
from app.services.unified_state_service import get_unified_state_service
from app.services.sse_notifier import get_sse_notifier

router = APIRouter(prefix="/gestalt", tags=["darshan"])
logger = logging.getLogger(__name__)


# === Response Models ===

class GestaltCardsResponse(BaseModel):
    """Response model for gestalt cards"""
    family_id: str
    cards: List[dict]
    has_active_cycles: bool
    pending_insights_count: int


class CardActionRequest(BaseModel):
    """Request model for card action"""
    family_id: str
    action: str
    params: dict = {}


class CardActionResponse(BaseModel):
    """Response model for card action"""
    success: bool
    result: dict


class GestaltSummaryResponse(BaseModel):
    """Response model for gestalt summary"""
    family_id: str
    child_name: Optional[str]
    child_age: Optional[float]
    completeness: float
    active_cycles_count: int
    videos_total: int
    videos_analyzed: int
    artifacts_count: int


class VideoValidationResult(BaseModel):
    """Video validation result"""
    is_usable: bool = True
    scenario_matches: Optional[bool] = None
    what_video_shows: Optional[str] = None
    child_visible: Optional[bool] = None
    child_appears_consistent: Optional[bool] = None
    validation_issues: List[str] = []
    recommendation: Optional[str] = None


class VideoScenarioInsights(BaseModel):
    """Insights from a single video scenario"""
    scenario_id: str
    title: str
    verdict: Optional[str] = None
    confidence_level: Optional[str] = None
    insights_for_parent: List[str] = []
    strengths_observed: List[str] = []
    analyzed_at: Optional[str] = None
    video_validation: Optional[VideoValidationResult] = None


class VideoInsightsResponse(BaseModel):
    """Response model for video insights"""
    family_id: str
    cycle_id: str
    focus: str
    insights: List[VideoScenarioInsights]
    total_analyzed: int


# === Endpoints ===

@router.get("/{family_id}/cards", response_model=GestaltCardsResponse)
async def get_gestalt_cards(family_id: str, language: str = "he"):
    """
    Get cards derived from explorations and understanding.
    """
    try:
        chitta = get_chitta_service()
        cards = await chitta.get_cards(family_id)

        unified = get_unified_state_service()
        child = unified.get_child(family_id)

        return GestaltCardsResponse(
            family_id=family_id,
            cards=cards,
            has_active_cycles=len(child.active_exploration_cycles()) > 0,
            pending_insights_count=len(child.understanding.unshared_insights()),
        )

    except Exception as e:
        logger.error(f"Error getting gestalt cards: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/card-action", response_model=CardActionResponse)
async def execute_card_action(request: CardActionRequest):
    """
    Execute an action from a card.
    """
    from app.chitta.service import get_chitta_service

    try:
        chitta = get_chitta_service()
        action = request.action
        params = request.params
        family_id = request.family_id
        cycle_id = params.get("cycle_id")

        if action == "accept_video":
            if not cycle_id:
                return CardActionResponse(success=False, result={"error": "cycle_id required"})
            result = await chitta.accept_video_suggestion(family_id, cycle_id)

        elif action == "decline_video":
            if not cycle_id:
                return CardActionResponse(success=False, result={"error": "cycle_id required"})
            result = await chitta.decline_video_suggestion(family_id, cycle_id)

        elif action == "view_guidelines":
            if not cycle_id:
                return CardActionResponse(success=False, result={"error": "cycle_id required"})
            result = await chitta.get_video_guidelines(family_id, cycle_id)
            result["action"] = "navigate"
            result["target"] = "guidelines_view"

        elif action == "analyze_videos":
            result = {"action": "navigate", "target": "video_analysis", "cycle_id": cycle_id}

        elif action == "view_insights":
            result = {"action": "navigate", "target": "insights_view", "cycle_id": cycle_id}

        elif action == "dismiss":
            card_type = params.get("card_type")
            scenario_ids = params.get("scenario_ids", [])

            if card_type == "video_analyzed" and scenario_ids:
                result = await chitta.acknowledge_video_insights(family_id, scenario_ids)
            else:
                result = {"status": "dismissed"}

        elif action == "confirm_video":
            scenario_id = params.get("scenario_id")
            if not scenario_id:
                return CardActionResponse(success=False, result={"error": "scenario_id required"})
            result = await chitta.confirm_video(family_id, scenario_id)

        elif action == "reject_video":
            scenario_id = params.get("scenario_id")
            if not scenario_id:
                return CardActionResponse(success=False, result={"error": "scenario_id required"})
            result = await chitta.reject_confirmed_video(family_id, scenario_id)

        elif action == "dismiss_reminder":
            scenario_ids = params.get("scenario_ids", [])
            if not scenario_ids:
                return CardActionResponse(success=False, result={"error": "scenario_ids required"})
            result = await chitta.dismiss_scenario_reminders(family_id, scenario_ids)

        elif action == "reject_guidelines":
            scenario_ids = params.get("scenario_ids", [])
            if not scenario_ids:
                return CardActionResponse(success=False, result={"error": "scenario_ids required"})
            result = await chitta.reject_scenarios(family_id, scenario_ids)

        elif action == "accept_baseline_video":
            result = await chitta.accept_baseline_video(family_id)

        elif action == "dismiss_baseline_video":
            result = await chitta.dismiss_baseline_video(family_id)

        else:
            result = {"error": f"Unknown action: {action}"}

        # Send SSE to update cards
        gestalt = await chitta._get_gestalt(family_id)
        if gestalt:
            updated_cards = chitta._derive_cards(gestalt)
            await get_sse_notifier().notify_cards_updated(family_id, updated_cards)

        return CardActionResponse(
            success="error" not in result,
            result=result,
        )

    except Exception as e:
        logger.error(f"Error executing card action: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{family_id}/summary", response_model=GestaltSummaryResponse)
async def get_gestalt_summary(family_id: str):
    """
    Get high-level summary of understanding.
    """
    try:
        unified = get_unified_state_service()
        child = unified.get_child(family_id)

        return GestaltSummaryResponse(
            family_id=family_id,
            child_name=child.name,
            child_age=child.age,
            completeness=len(child.understanding.active_hypotheses()) * 0.1,
            active_cycles_count=len(child.active_exploration_cycles()),
            videos_total=child.video_count,
            videos_analyzed=len(child.analyzed_videos()),
            artifacts_count=sum(len(c.artifacts) for c in child.exploration_cycles),
        )

    except Exception as e:
        logger.error(f"Error getting gestalt summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{family_id}/insights/{cycle_id}", response_model=VideoInsightsResponse)
async def get_video_insights(family_id: str, cycle_id: str):
    """
    Get video analysis insights for a specific exploration cycle.
    """
    try:
        from app.chitta.service import get_chitta_service
        chitta = get_chitta_service()
        gestalt = await chitta._get_gestalt(family_id)

        if not gestalt:
            raise HTTPException(status_code=404, detail=f"Family {family_id} not found")

        # Find the cycle
        cycle = None
        for c in gestalt.explorations:
            if c.id == cycle_id:
                cycle = c
                break

        if not cycle:
            raise HTTPException(status_code=404, detail=f"Cycle {cycle_id} not found")

        def normalize_list(items: list, key: str = None) -> List[str]:
            """Convert list items to strings, handling dict format."""
            result = []
            for item in items:
                if isinstance(item, str):
                    result.append(item)
                elif isinstance(item, dict):
                    for k in [key, 'strength', 'insight', 'text', 'content']:
                        if k and k in item:
                            result.append(item[k])
                            break
                    else:
                        for v in item.values():
                            if isinstance(v, str):
                                result.append(v)
                                break
            return result

        # Extract insights from analyzed video scenarios
        insights = []
        for scenario in cycle.video_scenarios:
            if scenario.status == "analyzed" and scenario.analysis_result:
                result = scenario.analysis_result

                validation_data = result.get("video_validation")
                video_validation = None
                if validation_data:
                    video_validation = VideoValidationResult(
                        is_usable=validation_data.get("is_usable", True),
                        scenario_matches=validation_data.get("scenario_matches"),
                        what_video_shows=validation_data.get("what_video_shows"),
                        child_visible=validation_data.get("child_visible"),
                        child_appears_consistent=validation_data.get("child_appears_consistent"),
                        validation_issues=validation_data.get("validation_issues", []),
                        recommendation=validation_data.get("recommendation"),
                    )

                insights.append(VideoScenarioInsights(
                    scenario_id=scenario.id,
                    title=scenario.title,
                    verdict=result.get("verdict"),
                    confidence_level=result.get("confidence_level"),
                    insights_for_parent=normalize_list(result.get("insights_for_parent", []), "insight"),
                    strengths_observed=normalize_list(result.get("strengths_observed", []), "strength"),
                    analyzed_at=scenario.analyzed_at.isoformat() if scenario.analyzed_at else None,
                    video_validation=video_validation,
                ))

        return VideoInsightsResponse(
            family_id=family_id,
            cycle_id=cycle_id,
            focus=cycle.focus,
            insights=insights,
            total_analyzed=len(insights),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting video insights: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
