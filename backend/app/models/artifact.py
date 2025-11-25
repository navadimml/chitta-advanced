"""
Artifact models for Wu Wei architecture.

Artifacts are tangible outputs that emerge from the conversation:
- video_guidelines: Personalized recording instructions
- parent_report: Comprehensive assessment report
- professional_report: Clinical assessment document
- video_analysis: Structured observations from videos

Each artifact has a lifecycle: pending → generating → ready (or error)
"""

from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class Artifact(BaseModel):
    """
    A single artifact in the system.

    Represents a generated document or output that has emerged
    from the conversation or analysis process.
    """

    artifact_id: str = Field(..., description="Unique identifier (e.g., 'video_guidelines', 'baseline_parent_report')")
    artifact_type: str = Field(..., description="Type category (guidelines, report, analysis, journal)")
    status: str = Field(default="pending", description="Lifecycle status: pending, generating, ready, error")

    # Content
    content: Optional[str] = Field(None, description="The actual artifact content (markdown, JSON, etc.)")
    content_format: str = Field(default="markdown", description="Content format: markdown, json, pdf")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the artifact")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    ready_at: Optional[datetime] = Field(None, description="When artifact became ready")

    # Generation info
    generation_inputs: Dict[str, Any] = Field(default_factory=dict, description="Inputs used to generate this artifact")
    generation_model: Optional[str] = Field(None, description="LLM model used for generation")
    generation_duration_seconds: Optional[float] = Field(None, description="How long generation took")

    # Error tracking
    error_message: Optional[str] = Field(None, description="Error details if status is 'error'")

    def mark_generating(self):
        """Mark artifact as currently being generated."""
        self.status = "generating"
        self.updated_at = datetime.now()

    def mark_ready(self, content: str):
        """Mark artifact as ready with content."""
        self.status = "ready"
        self.content = content
        self.ready_at = datetime.now()
        self.updated_at = datetime.now()

    def mark_error(self, error_message: str):
        """Mark artifact as failed with error message."""
        self.status = "error"
        self.error_message = error_message
        self.updated_at = datetime.now()

    @property
    def exists(self) -> bool:
        """
        Check if artifact exists in the system.

        Returns True if the artifact has been created (regardless of status).
        Use is_ready to check if content is available.
        """
        # Artifact exists if it has any valid status (pending, generating, ready, or error)
        # Only "not_created" or missing artifact should return False
        return self.status in ("pending", "generating", "ready", "error")

    @property
    def is_pending(self) -> bool:
        """Check if artifact is pending generation."""
        return self.status == "pending"

    @property
    def is_generating(self) -> bool:
        """Check if artifact is currently being generated."""
        return self.status == "generating"

    @property
    def is_ready(self) -> bool:
        """Check if artifact is ready."""
        return self.status == "ready"

    @property
    def has_error(self) -> bool:
        """Check if artifact generation failed."""
        return self.status == "error"


class ArtifactReference(BaseModel):
    """
    A reference to an artifact used in prerequisite checks.

    This is what gets embedded in session context for card evaluation.
    """
    exists: bool
    status: str
    artifact_id: Optional[str] = None
    ready_at: Optional[datetime] = None

    @classmethod
    def from_artifact(cls, artifact: Artifact) -> "ArtifactReference":
        """Create reference from full artifact."""
        return cls(
            exists=artifact.exists,
            status=artifact.status,
            artifact_id=artifact.artifact_id,
            ready_at=artifact.ready_at
        )

    @classmethod
    def not_exists(cls) -> "ArtifactReference":
        """Create reference for non-existent artifact."""
        return cls(
            exists=False,
            status="not_created",
            artifact_id=None,
            ready_at=None
        )
