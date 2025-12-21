"""
User API Routes - User-centric endpoints.

Includes:
- /user/me/family - Get user's family with children
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import logging

from app.db.dependencies import get_current_user
from app.db.models_auth import User
from app.services.family_service import get_family_service

router = APIRouter(prefix="/user", tags=["user"])
logger = logging.getLogger(__name__)


# === Response Models ===

class ChildSummaryResponse(BaseModel):
    """Child summary for family view."""
    id: str
    name: Optional[str] = None
    age_months: Optional[int] = None
    last_activity: Optional[str] = None  # ISO format datetime string


class FamilyResponse(BaseModel):
    """Family info."""
    id: str
    name: str


class FamilyWithChildrenResponse(BaseModel):
    """Response for /me/family endpoint."""
    family: FamilyResponse
    children: List[ChildSummaryResponse]


# === Endpoints ===

@router.get("/me/family", response_model=FamilyWithChildrenResponse)
async def get_my_family(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's family with all children.

    Auto-creates family + child placeholder for new users.
    """
    logger.info(f"Getting family for user: {current_user.email}")

    family_service = get_family_service()

    # Get or create family (auto-creates for new users)
    family = await family_service.get_or_create_family_for_user(str(current_user.id))

    # Get family with children summaries
    data = await family_service.get_family_with_children(family.id)

    # Convert last_activity datetime to string
    children = []
    for child in data["children"]:
        last_activity = child.get("last_activity")
        if last_activity and isinstance(last_activity, datetime):
            child["last_activity"] = last_activity.isoformat()
        children.append(ChildSummaryResponse(**child))

    return FamilyWithChildrenResponse(
        family=FamilyResponse(**data["family"]),
        children=children,
    )
