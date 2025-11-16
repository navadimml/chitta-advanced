"""
Family State Model - The DNA of the System
Everything derives from this single source of truth.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime


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
    """An uploaded video"""
    id: str
    scenario: str  # "free_play" | "mealtime" | "social"
    uploaded_at: datetime
    duration_seconds: int = 0


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
