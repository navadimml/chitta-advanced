"""
Family State Model - The DNA of the System
Everything derives from this single source of truth.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from app.models.active_card import ActiveCard


class Message(BaseModel):
    """A conversation message"""
    role: str  # "assistant" | "user"
    content: str
    timestamp: datetime


class Artifact(BaseModel):
    """A generated artifact (report, guidelines, etc)"""
    type: str  # "baseline_video_guidelines" | "parent_report" | etc
    content: dict
    created_at: datetime


class Video(BaseModel):
    """
    An uploaded behavioral observation video with holistic analysis context.

    Stores both the video metadata and the analyst_context from the guideline
    that this video was filmed for, enabling context-aware analysis.
    """
    id: str
    scenario: str  # Scenario title from guideline (e.g., "משחק קופסה במטבח")
    uploaded_at: datetime
    duration_seconds: int = 0

    # File storage
    file_path: Optional[str] = None  # Path to video file
    file_url: Optional[str] = None  # URL for video playback (if using blob storage)

    # Analyst Context (from video_guidelines scenario)
    analyst_context: Optional[Dict[str, Any]] = None  # Full context from guideline
    # Contains: {clinical_goal, guideline_title, instruction_given_to_parent, internal_focus_points, parent_persona_data}

    # Analysis tracking
    analysis_status: str = "pending"  # "pending" | "analyzing" | "ready" | "error"
    analysis_artifact_id: Optional[str] = None  # Reference to analysis artifact if complete
    analysis_error: Optional[str] = None  # Error message if analysis failed


class JournalEntry(BaseModel):
    """A parent journal entry"""
    id: str
    content: str
    timestamp: datetime


class FamilyState(BaseModel):
    """
    The complete DNA - everything derives from this.
    No stages. No remembered cards. Just pure state.
    """
    family_id: str

    # Identity
    child: Optional[dict] = None  # { name, age }
    parent: Optional[dict] = None  # { name }

    # All interactions (temporal memory)
    conversation: List[Message] = Field(default_factory=list)

    # Generated artifacts
    artifacts: Dict[str, Artifact] = Field(default_factory=dict)

    # Activities
    videos_uploaded: List[Video] = Field(default_factory=list)
    journal_entries: List[JournalEntry] = Field(default_factory=list)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    last_active: datetime = Field(default_factory=datetime.now)

    # Card Lifecycle State (Phase 1: Living Dashboard)
    # Cards are created by moments and persist until dismissed
    active_cards: List[Any] = Field(default_factory=list)  # List[ActiveCard]

    # Track dismissed moments to prevent re-triggering
    dismissed_card_moments: Dict[str, datetime] = Field(default_factory=dict)

    # Context snapshot for detecting transitions (FALSE → TRUE)
    previous_context_snapshot: Optional[Dict[str, Any]] = None
