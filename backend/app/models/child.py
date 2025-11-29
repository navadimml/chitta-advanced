"""
Child Model - The Core Entity

The child is the invariant center of Chitta. Everything else orbits around it.
Child data accumulates over time and is shared across all users with access.

Design principles:
- Child data is invariant (doesn't change based on who's viewing)
- Artifacts, videos, journal entries belong to the child
- Developmental understanding evolves continuously
- No workflow states - just evolving understanding
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
from datetime import datetime, date
from enum import Enum

from .artifact import Artifact


class Video(BaseModel):
    """
    A behavioral observation video with analysis context.

    Videos are requested by Chitta to observe specific behaviors,
    and include the context needed for meaningful analysis.
    """
    id: str
    scenario: str  # What Chitta asked to observe (e.g., "משחק קופסה במטבח")
    uploaded_at: datetime
    duration_seconds: int = 0

    # File storage
    file_path: Optional[str] = None
    file_url: Optional[str] = None

    # Context from request (what Chitta wanted to see)
    observation_context: Optional[Dict[str, Any]] = None
    # Contains: {clinical_goal, instruction_given_to_parent, focus_points}

    # Analysis tracking
    analysis_status: str = "pending"  # "pending" | "analyzing" | "ready" | "error"
    analysis_artifact_id: Optional[str] = None
    analysis_error: Optional[str] = None


class JournalEntry(BaseModel):
    """
    A moment captured by the parent in conversation.

    Note: In Chitta, the conversation IS the journal. These entries
    are extracted from conversation when the parent shares stories
    or observations worth preserving.
    """
    id: str
    content: str  # The story/observation
    context: Optional[str] = None  # What prompted this (question asked, etc.)
    extracted_from_turn: Optional[int] = None  # Which conversation turn
    timestamp: datetime = Field(default_factory=datetime.now)

    # Optional categorization (extracted by LLM)
    themes: List[str] = Field(default_factory=list)  # ["speech", "social", etc.]
    sentiment: Optional[str] = None  # "positive", "concern", "neutral"


class DevelopmentalData(BaseModel):
    """
    Structured understanding of the child's development.

    This is extracted and accumulated from all conversations.
    It grows richer over time as we learn more.

    Validation ensures we don't store placeholder values.
    """
    # Basic profile
    child_name: Optional[str] = None
    age: Optional[float] = None
    gender: Optional[str] = None  # "male", "female", "unknown"
    birth_date: Optional[date] = None  # For accurate age calculation

    # Core developmental picture
    primary_concerns: List[str] = Field(default_factory=list)
    concern_details: Optional[str] = None
    strengths: Optional[str] = None
    developmental_history: Optional[str] = None

    # Context
    family_context: Optional[str] = None
    daily_routines: Optional[str] = None
    parent_goals: Optional[str] = None

    # Flags
    urgent_flags: List[str] = Field(default_factory=list)

    # Parent preferences
    filming_preference: Optional[str] = None  # "wants_videos" | "report_only" | None

    # Metadata
    last_updated: datetime = Field(default_factory=datetime.now)
    extraction_count: int = 0

    @validator('child_name')
    def validate_child_name(cls, v):
        """Reject placeholder values and invalid names"""
        if v is None:
            return None

        placeholders = [
            'unknown', 'not mentioned', 'null', 'none',
            'לא צוין', 'לא ידוע', 'לא נמסר',
            '(not mentioned yet)', '(unknown)',
            'not specified', 'n/a', 'na'
        ]

        if v.lower().strip() in placeholders:
            return None

        if len(v.strip()) < 2:
            return None

        # Reject gibberish
        cleaned = v.strip()
        alpha_chars = sum(1 for c in cleaned if c.isalpha())
        if alpha_chars == 0 or (len(cleaned) > 0 and alpha_chars / len(cleaned) < 0.5):
            return None

        return cleaned

    @validator('age')
    def validate_age(cls, v):
        """Ensure age is valid for child development (0-18 years)"""
        if v is None:
            return None
        if v < 0 or v > 18:
            return None
        return v

    @validator('gender')
    def validate_gender(cls, v):
        """Ensure gender is valid"""
        if v is None:
            return None
        valid_genders = ['male', 'female', 'unknown']
        if v.lower() not in valid_genders:
            return 'unknown'
        return v.lower()

    @validator('primary_concerns')
    def validate_primary_concerns(cls, v):
        """Ensure concerns are from valid set"""
        if not v:
            return []

        valid_concerns = [
            'speech', 'social', 'attention', 'motor', 'sensory',
            'emotional', 'behavioral', 'learning', 'sleep', 'eating', 'other'
        ]

        validated = [c.lower() for c in v if c.lower() in valid_concerns]

        # Reject 'other' as sole concern
        if validated == ['other']:
            return []

        return validated


class Child(BaseModel):
    """
    The Child - the invariant core entity.

    Everything in Chitta orbits around the child. This model contains:
    - Profile and developmental data (extracted from conversations)
    - Artifacts (generated reports, guidelines, analyses)
    - Videos (behavioral observations)
    - Journal (extracted meaningful moments from conversations)

    This data is shared across all users with access to this child.
    """
    child_id: str = Field(description="Unique identifier for the child")

    # Developmental understanding (evolves over time)
    developmental_data: DevelopmentalData = Field(default_factory=DevelopmentalData)

    # Generated artifacts (reports, guidelines, analyses)
    artifacts: Dict[str, Artifact] = Field(
        default_factory=dict,
        description="Generated artifacts keyed by artifact_id"
    )

    # Behavioral observation videos
    videos: List[Video] = Field(default_factory=list)

    # Journal entries (extracted from conversations)
    journal_entries: List[JournalEntry] = Field(default_factory=list)

    # Completeness tracking
    data_completeness: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="How much we know about this child (0-1)"
    )

    # LLM quality assessment
    semantic_verification: Optional[Dict[str, Any]] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # === Convenience properties ===

    @property
    def name(self) -> Optional[str]:
        """Child's name for easy access"""
        return self.developmental_data.child_name

    @property
    def age(self) -> Optional[float]:
        """Child's age for easy access"""
        return self.developmental_data.age

    @property
    def profile_summary(self) -> str:
        """Brief profile for display"""
        parts = []
        if self.name:
            parts.append(self.name)
        if self.age:
            parts.append(f"גיל {self.age}")
        return " ".join(parts) if parts else "ילד/ה חדש/ה"

    # === Artifact management ===

    def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        """Get artifact by ID"""
        return self.artifacts.get(artifact_id)

    def has_artifact(self, artifact_id: str) -> bool:
        """Check if artifact exists and is ready"""
        artifact = self.get_artifact(artifact_id)
        return artifact is not None and artifact.is_ready

    def add_artifact(self, artifact: Artifact):
        """Add or update an artifact"""
        self.artifacts[artifact.artifact_id] = artifact
        self.updated_at = datetime.now()

    # === Video management ===

    def add_video(self, video: Video):
        """Add a video observation"""
        self.videos.append(video)
        self.updated_at = datetime.now()

    def get_video(self, video_id: str) -> Optional[Video]:
        """Get video by ID"""
        return next((v for v in self.videos if v.id == video_id), None)

    def get_videos_pending_analysis(self) -> List[Video]:
        """Get videos that need analysis"""
        return [v for v in self.videos if v.analysis_status == "pending"]

    def get_analyzed_videos(self) -> List[Video]:
        """Get videos with completed analysis"""
        return [v for v in self.videos if v.analysis_status == "ready"]

    @property
    def video_count(self) -> int:
        """Total video count"""
        return len(self.videos)

    @property
    def analyzed_video_count(self) -> int:
        """Count of analyzed videos"""
        return len(self.get_analyzed_videos())

    # === Journal management ===

    def add_journal_entry(self, entry: JournalEntry):
        """Add a journal entry"""
        self.journal_entries.append(entry)
        self.updated_at = datetime.now()

    def get_recent_journal_entries(self, limit: int = 10) -> List[JournalEntry]:
        """Get most recent journal entries"""
        sorted_entries = sorted(
            self.journal_entries,
            key=lambda e: e.timestamp,
            reverse=True
        )
        return sorted_entries[:limit]
