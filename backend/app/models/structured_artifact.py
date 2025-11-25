"""
Structured Artifact Model - Artifacts with identifiable sections.

Part of Living Dashboard Phase 3: Artifacts are structured into
sections that can have threads attached to them.

This enables:
- Section-level navigation
- Thread attachment points
- Contextual Q&A about specific parts
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class SectionType(str, Enum):
    """Types of sections within artifacts."""
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    OBSERVATION = "observation"
    RECOMMENDATION = "recommendation"
    TIMESTAMP = "timestamp"  # For video artifacts
    LIST = "list"
    SUMMARY = "summary"


class ArtifactSection(BaseModel):
    """
    A section within an artifact that can have threads.

    Sections are the building blocks of structured artifacts.
    Each section has a unique ID for thread attachment.
    """
    section_id: str
    section_type: SectionType = SectionType.PARAGRAPH
    order: int = 0  # Display order within artifact

    # Content
    title: Optional[str] = None  # For headings
    title_en: Optional[str] = None
    content: str  # The actual text content
    content_html: Optional[str] = None  # Optional HTML formatting

    # For nested sections (subsections)
    parent_section_id: Optional[str] = None
    level: int = 1  # Heading level (1, 2, 3...)

    # For video/timeline artifacts
    timestamp_start: Optional[float] = None  # Seconds
    timestamp_end: Optional[float] = None
    video_id: Optional[str] = None

    # Thread info (populated from ArtifactThreads)
    thread_count: int = 0
    has_unread: bool = False
    thread_ids: List[str] = Field(default_factory=list)

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def is_heading(self) -> bool:
        return self.section_type == SectionType.HEADING

    @property
    def is_timestamp(self) -> bool:
        return self.section_type == SectionType.TIMESTAMP

    @property
    def has_threads(self) -> bool:
        return self.thread_count > 0

    def get_timestamp_display(self) -> Optional[str]:
        """Format timestamp for display (e.g., '1:23')."""
        if self.timestamp_start is None:
            return None
        minutes = int(self.timestamp_start // 60)
        seconds = int(self.timestamp_start % 60)
        return f"{minutes}:{seconds:02d}"


class StructuredArtifact(BaseModel):
    """
    An artifact with sections for threading.

    Wraps regular artifact content with section structure.
    Enables:
    - Section navigation
    - Thread attachment
    - Contextual AI responses
    """
    artifact_id: str
    artifact_type: str  # "report", "guidelines", "video_analysis"
    family_id: str

    # Display info
    title: str
    title_en: Optional[str] = None
    subtitle: Optional[str] = None

    # The structured content
    sections: List[ArtifactSection] = Field(default_factory=list)

    # Original content (for fallback/compatibility)
    raw_content: Optional[str] = None
    content_format: str = "markdown"  # "markdown", "json", "html"

    # Thread summary (populated from ArtifactThreads)
    total_threads: int = 0
    unread_threads: int = 0
    sections_with_threads: List[str] = Field(default_factory=list)

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    version: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def get_section(self, section_id: str) -> Optional[ArtifactSection]:
        """Get a section by ID."""
        for section in self.sections:
            if section.section_id == section_id:
                return section
        return None

    def get_sections_by_type(self, section_type: SectionType) -> List[ArtifactSection]:
        """Get all sections of a specific type."""
        return [s for s in self.sections if s.section_type == section_type]

    def get_headings(self) -> List[ArtifactSection]:
        """Get all heading sections (for navigation/TOC)."""
        return self.get_sections_by_type(SectionType.HEADING)

    def update_thread_counts(self, thread_counts: Dict[str, int]) -> None:
        """Update thread counts from ArtifactThreads data."""
        total = 0
        sections_with = []

        for section in self.sections:
            count = thread_counts.get(section.section_id, 0)
            section.thread_count = count
            if count > 0:
                total += count
                sections_with.append(section.section_id)

        self.total_threads = total
        self.sections_with_threads = sections_with


def parse_markdown_to_sections(
    artifact_id: str,
    markdown_content: str,
    artifact_type: str = "report"
) -> List[ArtifactSection]:
    """
    Parse markdown content into sections.

    Uses simple heading detection to split content.
    Each heading starts a new section.

    Args:
        artifact_id: The artifact ID for section ID generation
        markdown_content: Raw markdown content
        artifact_type: Type of artifact for section naming

    Returns:
        List of ArtifactSection objects
    """
    import re

    sections = []
    lines = markdown_content.split('\n')

    current_section = None
    current_content = []
    section_order = 0

    # Heading pattern: # Heading, ## Subheading, ### Sub-subheading
    heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$')

    for line in lines:
        match = heading_pattern.match(line)

        if match:
            # Save previous section
            if current_section or current_content:
                if current_section is None:
                    # Content before first heading - create intro section
                    current_section = ArtifactSection(
                        section_id=f"{artifact_id}_intro",
                        section_type=SectionType.PARAGRAPH,
                        order=section_order,
                        content='\n'.join(current_content).strip()
                    )
                else:
                    current_section.content = '\n'.join(current_content).strip()

                if current_section.content:  # Only add non-empty sections
                    sections.append(current_section)
                    section_order += 1

            # Start new section for heading
            level = len(match.group(1))
            title = match.group(2).strip()

            # Generate section ID from title
            section_id = re.sub(r'[^\w\s]', '', title.lower())
            section_id = re.sub(r'\s+', '_', section_id)
            section_id = f"{artifact_id}_{section_id}"

            current_section = ArtifactSection(
                section_id=section_id,
                section_type=SectionType.HEADING,
                order=section_order,
                title=title,
                level=level,
                content=""
            )
            current_content = []

        else:
            current_content.append(line)

    # Don't forget the last section
    if current_section or current_content:
        if current_section is None:
            current_section = ArtifactSection(
                section_id=f"{artifact_id}_content",
                section_type=SectionType.PARAGRAPH,
                order=section_order,
                content='\n'.join(current_content).strip()
            )
        else:
            current_section.content = '\n'.join(current_content).strip()

        if current_section.content or current_section.title:
            sections.append(current_section)

    return sections


def parse_json_to_sections(
    artifact_id: str,
    json_content: Dict[str, Any],
    section_mapping: Optional[Dict[str, str]] = None
) -> List[ArtifactSection]:
    """
    Parse JSON artifact content into sections.

    Used for structured artifacts like video_guidelines.

    Args:
        artifact_id: The artifact ID
        json_content: Parsed JSON content
        section_mapping: Optional mapping of JSON keys to section titles

    Returns:
        List of ArtifactSection objects
    """
    sections = []
    order = 0

    # Default section mapping for common artifact types
    default_mapping = {
        "summary": "סיכום",
        "focus_areas": "תחומי התמקדות",
        "scenarios": "תרחישי צילום",
        "recommendations": "המלצות",
        "observations": "תצפיות",
        "strengths": "חוזקות",
        "areas_for_development": "תחומים לפיתוח"
    }

    mapping = section_mapping or default_mapping

    for key, value in json_content.items():
        if key.startswith('_'):  # Skip private/meta fields
            continue

        title = mapping.get(key, key.replace('_', ' ').title())
        section_id = f"{artifact_id}_{key}"

        # Handle different value types
        if isinstance(value, str):
            content = value
        elif isinstance(value, list):
            if all(isinstance(item, str) for item in value):
                content = '\n'.join(f"• {item}" for item in value)
            else:
                # Complex list items - format as JSON-like
                content = '\n'.join(
                    f"• {item.get('title', item.get('name', str(item)))}"
                    for item in value
                    if isinstance(item, dict)
                )
        elif isinstance(value, dict):
            # Nested object - create subsections or format
            content = '\n'.join(
                f"**{k}**: {v}"
                for k, v in value.items()
                if not k.startswith('_')
            )
        else:
            content = str(value)

        if content:
            sections.append(ArtifactSection(
                section_id=section_id,
                section_type=SectionType.HEADING,
                order=order,
                title=title,
                content=content,
                level=2
            ))
            order += 1

    return sections


def create_structured_artifact(
    artifact_id: str,
    artifact_type: str,
    family_id: str,
    title: str,
    content: Any,
    content_format: str = "markdown"
) -> StructuredArtifact:
    """
    Factory function to create a StructuredArtifact from content.

    Automatically parses content into sections based on format.

    Args:
        artifact_id: Unique artifact identifier
        artifact_type: Type (report, guidelines, etc.)
        family_id: Family this artifact belongs to
        title: Display title
        content: Raw content (string or dict)
        content_format: Format of content ("markdown", "json")

    Returns:
        StructuredArtifact with parsed sections
    """
    # Parse content into sections
    if content_format == "markdown" and isinstance(content, str):
        sections = parse_markdown_to_sections(artifact_id, content, artifact_type)
        raw_content = content
    elif content_format == "json" and isinstance(content, dict):
        sections = parse_json_to_sections(artifact_id, content)
        raw_content = None
    elif isinstance(content, str):
        # Single section fallback
        sections = [
            ArtifactSection(
                section_id=f"{artifact_id}_main",
                section_type=SectionType.PARAGRAPH,
                order=0,
                content=content
            )
        ]
        raw_content = content
    else:
        sections = []
        raw_content = str(content) if content else None

    return StructuredArtifact(
        artifact_id=artifact_id,
        artifact_type=artifact_type,
        family_id=family_id,
        title=title,
        sections=sections,
        raw_content=raw_content,
        content_format=content_format,
        created_at=datetime.utcnow()
    )
