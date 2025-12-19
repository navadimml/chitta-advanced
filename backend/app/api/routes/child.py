"""
Child API Routes - Child data and gestalt endpoints

Includes:
- /child/{family_id} - Child data for debugging/X-Ray
- /child/{family_id}/gestalt - Complete gestalt for debugging/X-Ray
"""

from fastapi import APIRouter, HTTPException
import logging

from app.services.unified_state_service import get_unified_state_service

router = APIRouter(prefix="/child", tags=["child"])
logger = logging.getLogger(__name__)


@router.get("/{family_id}")
async def get_child_data(family_id: str):
    """
    Get complete child data including exploration cycles and hypotheses.

    This endpoint exposes the full Child model data for X-Ray testing
    and debugging the temporal design system.

    Returns:
    - exploration_cycles: All cycles with their hypotheses
    - developmental_data: Backward-compatible child profile
    - understanding: Patterns and pending insights
    """
    try:
        unified = get_unified_state_service()
        child = unified.get_child(family_id)

        cycles_data = [cycle.model_dump() for cycle in child.exploration_cycles]
        dev_data = child.developmental_data
        understanding_dict = child.understanding.model_dump()

        return {
            "family_id": family_id,
            "name": child.name,
            "age": child.age,
            "gender": child.identity.gender,
            "exploration_cycles": cycles_data,
            "developmental_data": dev_data,
            "understanding": understanding_dict,
        }

    except Exception as e:
        logger.error(f"Error getting child data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{family_id}/gestalt")
async def get_child_gestalt(family_id: str):
    """
    Get complete child gestalt data for X-Ray testing.

    Returns the full Darshan structure including:
    - identity: name, birth_date, gender
    - essence: temperament, energy, core qualities
    - strengths: abilities, interests, what lights them up
    - concerns: primary areas, details, parent narrative
    - history: birth, early development, milestones
    - family: structure, siblings, languages
    - understanding: hypotheses, patterns, insights
    - exploration_cycles: full cycle data with hypotheses and artifacts
    """
    try:
        unified = get_unified_state_service()
        child = unified.get_child(family_id)

        return {
            "family_id": family_id,
            "child_id": child.id,

            # Core identity
            "identity": child.identity.model_dump(),

            # The Darshan
            "essence": child.essence.model_dump(),
            "strengths": child.strengths.model_dump(),
            "concerns": child.concerns.model_dump(),
            "history": child.history.model_dump(),
            "family": child.family.model_dump(),

            # Understanding (hypotheses, patterns)
            "understanding": child.understanding.model_dump(),

            # Exploration cycles with full data
            "exploration_cycles": [c.model_dump() for c in child.exploration_cycles],

            # Synthesis reports
            "synthesis_reports": [r.model_dump() for r in child.synthesis_reports],

            # Videos and journal
            "videos": [v.model_dump() for v in child.videos],
            "journal_entries": [j.model_dump() for j in child.journal_entries],

            # Metadata
            "created_at": child.created_at.isoformat() if child.created_at else None,
            "updated_at": child.updated_at.isoformat() if child.updated_at else None,

            # Convenience properties
            "name": child.name,
            "age": child.age,
            "profile_summary": child.profile_summary,
        }

    except Exception as e:
        logger.error(f"Error getting child gestalt: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
