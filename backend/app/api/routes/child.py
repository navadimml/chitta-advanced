"""
Child API Routes - Child data and gestalt endpoints

Includes:
- /child/{child_id} - Child data for debugging/X-Ray
- /child/{child_id}/gestalt - Complete gestalt for debugging/X-Ray
"""

from fastapi import APIRouter, HTTPException
import logging

from app.chitta import get_chitta_service

router = APIRouter(prefix="/child", tags=["child"])
logger = logging.getLogger(__name__)


@router.get("/{child_id}")
async def get_child_data(child_id: str):
    """
    Get complete child data including investigations and hypotheses.

    This endpoint exposes the full Darshan data for X-Ray testing
    and debugging the temporal design system.

    Returns:
    - investigations: All active investigations with their curiosities
    - curiosities: All curiosities (wondering, investigating, understood)
    - understanding: Patterns and pending insights
    """
    try:
        chitta = get_chitta_service()
        gestalt = await chitta.get_gestalt(child_id)

        if not gestalt:
            raise HTTPException(status_code=404, detail=f"Child {child_id} not found")

        # Get curiosities with their investigations
        curiosities_data = []
        for c in gestalt._curiosities._dynamic:
            c_dict = {
                "focus": c.focus,
                "type": c.type,
                "status": c.status,
                "pull": c.pull,
                "certainty": c.certainty,
                "theory": c.theory,
                "video_appropriate": c.video_appropriate,
                "video_value": c.video_value,
            }
            if c.investigation:
                c_dict["investigation"] = {
                    "id": c.investigation.id,
                    "status": c.investigation.status,
                    "video_accepted": c.investigation.video_accepted,
                    "video_scenarios": [s.to_dict() for s in c.investigation.video_scenarios],
                    "evidence_count": len(c.investigation.evidence),
                }
            curiosities_data.append(c_dict)

        return {
            "child_id": child_id,
            "name": gestalt._child_name,
            "age": gestalt._child_age,
            "curiosities": curiosities_data,
            "understanding": {
                "hypotheses": [h.to_dict() for h in gestalt._understanding._hypotheses],
                "patterns": [p.to_dict() for p in gestalt._understanding._patterns],
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting child data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{child_id}/gestalt")
async def get_child_gestalt(child_id: str):
    """
    Get complete child gestalt data for X-Ray testing.

    Returns the full Darshan structure including:
    - curiosities: all curiosities with their investigations
    - understanding: hypotheses, patterns, insights
    - stories: captured developmental stories
    - observations: what we've noticed
    """
    try:
        chitta = get_chitta_service()
        gestalt = await chitta.get_gestalt(child_id)

        if not gestalt:
            raise HTTPException(status_code=404, detail=f"Child {child_id} not found")

        # Build curiosities with full investigation data
        curiosities_data = []
        for c in gestalt._curiosities._dynamic:
            c_dict = c.to_dict()
            curiosities_data.append(c_dict)

        return {
            "child_id": child_id,
            "child_name": gestalt._child_name,
            "child_age": gestalt._child_age,

            # Curiosities (the unified model)
            "curiosities": {
                "dynamic": curiosities_data,
                "baseline": [c.to_dict() for c in gestalt._curiosities._baseline],
            },

            # Understanding (hypotheses, patterns)
            "understanding": {
                "hypotheses": [h.to_dict() for h in gestalt._understanding._hypotheses],
                "patterns": [p.to_dict() for p in gestalt._understanding._patterns],
                "pending_insights": [i.to_dict() for i in gestalt._understanding._pending_insights],
            },

            # Stories
            "stories": [s.to_dict() for s in gestalt._stories],

            # Observations
            "observations": [o.to_dict() for o in gestalt._observations],

            # Video info
            "video_count": gestalt._video_count,
            "analyzed_videos": [v.to_dict() for v in gestalt.analyzed_videos()],

            # Portrait if exists
            "portrait": gestalt._portrait.to_dict() if gestalt._portrait else None,

            # Session info
            "session_id": gestalt._session_id,
            "last_activity": gestalt._last_activity.isoformat() if gestalt._last_activity else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting child gestalt: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
