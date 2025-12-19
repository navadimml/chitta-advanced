"""
Journal API Routes - Journal entry endpoints

Includes:
- /journal/entry - Add journal entry
- /journal/entries/{family_id} - Get journal entries
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
import uuid
import logging

from app.core.app_state import app_state

router = APIRouter(prefix="/journal", tags=["journal"])
logger = logging.getLogger(__name__)


# === Request/Response Models ===

class JournalEntryRequest(BaseModel):
    family_id: str
    content: str
    category: str  # "התקדמות", "תצפית", "אתגר"


class JournalEntryResponse(BaseModel):
    entry_id: str
    timestamp: str
    success: bool


# === Endpoints ===

@router.post("/entry", response_model=JournalEntryResponse)
async def add_journal_entry(request: JournalEntryRequest):
    """
    Add entry to child's journal.

    Processes the journal entry into Chitta's understanding:
    - Extracts facts with ABSOLUTE timestamps
    - Detects developmental milestones
    - Boosts related curiosities
    - Stores in gestalt for persistence
    """
    entry_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()

    from app.chitta.service import get_chitta_service
    chitta = get_chitta_service()

    try:
        result = await chitta.process_parent_journal_entry(
            family_id=request.family_id,
            entry_text=request.content,
            entry_type=request.category,
        )

        return JournalEntryResponse(
            entry_id=entry_id,
            timestamp=timestamp,
            success=True
        )
    except Exception as e:
        logger.error(f"Failed to process journal entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entries/{family_id}")
async def get_journal_entries(family_id: str, limit: int = 10):
    """
    Get recent journal entries.
    """
    session = app_state.get_or_create_session(family_id)

    entries = session.get("journal_entries", [])
    entries_sorted = sorted(entries, key=lambda x: x["timestamp"], reverse=True)

    return {
        "entries": entries_sorted[:limit],
        "total": len(entries_sorted)
    }
