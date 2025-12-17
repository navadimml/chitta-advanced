"""
Professional Summary Schema - Structured Output

Defines the structure for professional summaries that will be
beautifully rendered in the frontend.

Design principles:
- Clear separation of source (parent vs Chitta observations)
- Hierarchical information architecture
- Print-friendly structure
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class SourceType(str, Enum):
    """Who provided this information."""
    PARENT = "parent"      # "ההורים סיפרו..."
    CHITTA = "chitta"      # "שמנו לב ש..."
    CLINICAL = "clinical"  # From structured clinical data


class ObservationItem(BaseModel):
    """A single observation or piece of information."""
    text: str = Field(description="The observation text in Hebrew")
    source: SourceType = Field(description="Who provided this information")
    domain: Optional[str] = Field(default=None, description="Developmental domain if relevant")


class SceneDescription(BaseModel):
    """A concrete scene/example that helps professionals visualize."""
    title: str = Field(description="Brief title for the scene (e.g., 'סיום משחק')")
    description: str = Field(description="What happens - concrete, specific")
    what_helps: Optional[str] = Field(default=None, description="What helps in this situation")
    what_doesnt_help: Optional[str] = Field(default=None, description="What doesn't help")


class PatternInsight(BaseModel):
    """A pattern or connection Chitta noticed."""
    observation: str = Field(description="The pattern described tentatively")
    domains_involved: List[str] = Field(default_factory=list, description="Domains this crosses")
    confidence: str = Field(description="How confident: 'נראה ש...', 'יכול להיות ש...', 'שמנו לב ש...'")


class OpenQuestion(BaseModel):
    """Something worth investigating further."""
    question: str = Field(description="The question in Hebrew")
    why_relevant: Optional[str] = Field(default=None, description="Why this matters for this professional")


class StrengthBridge(BaseModel):
    """A strength that can serve as a bridge/tool."""
    strength: str = Field(description="The strength or interest")
    how_to_use: str = Field(description="How it can be leveraged therapeutically/educationally")


class DevelopmentalNote(BaseModel):
    """Timeline/developmental information."""
    event: str = Field(description="What happened")
    timing: str = Field(description="When (age or relative time)")
    significance: Optional[str] = Field(default=None, description="Why this matters")


class MissingInfo(BaseModel):
    """Information we don't have yet."""
    item: str = Field(description="What's missing (clinical term)")
    why_relevant: str = Field(description="Why this would be useful for this professional")


class PracticalTip(BaseModel):
    """
    A practical tip connecting strength to challenge - מה יכול לעזור.

    For teachers: everyday language, classroom-applicable
    For therapists: can use professional terms
    """
    what_works: str = Field(
        description="What the child responds to / what opens them up (the hook)"
    )
    challenge: str = Field(
        description="The challenge this addresses (in everyday words)"
    )
    suggestion: str = Field(
        description="Concrete, actionable tip the professional can try"
    )


class ProfessionalSummary(BaseModel):
    """
    Complete structured summary for a professional.

    This structure ensures:
    1. Clear separation of sources (parent vs Chitta)
    2. Professional presentation
    3. Actionable information
    4. Honest about limitations
    """

    # === HEADER INFO ===
    child_first_name: str = Field(description="Child's first name")
    child_age_description: str = Field(description="Age description (e.g., 'בן 3.5')")
    recipient_type: str = Field(description="Type of professional")
    recipient_title: str = Field(description="How to address (e.g., 'נוירולוג ילדים')")
    summary_date: str = Field(description="Date in format DD/MM/YYYY")

    # === THREAD 1: WHO IS THIS CHILD ===
    essence_paragraph: str = Field(
        description="2-3 sentences capturing who this child IS - their essence, not their problems. Written warmly but professionally."
    )

    # === THREAD 2: STRENGTHS AS BRIDGES ===
    strengths: List[StrengthBridge] = Field(
        default_factory=list,
        description="Strengths that can serve as therapeutic/educational bridges"
    )

    # === THREAD 3: WHAT PARENTS SHARED ===
    parent_observations: List[ObservationItem] = Field(
        default_factory=list,
        description="Key information from parents - factual, not interpreted"
    )

    # === THREAD 4: CONCRETE SCENES ===
    scenes: List[SceneDescription] = Field(
        default_factory=list,
        description="1-3 concrete scenes that help visualize. Critical for professionals."
    )

    # === THREAD 5: PATTERNS CHITTA NOTICED ===
    patterns: List[PatternInsight] = Field(
        default_factory=list,
        description="Connections and patterns - framed tentatively as hypotheses"
    )

    # === THREAD 6: DEVELOPMENTAL TIMELINE ===
    developmental_notes: List[DevelopmentalNote] = Field(
        default_factory=list,
        description="Key developmental milestones and timeline"
    )

    # === THREAD 7: OPEN QUESTIONS ===
    open_questions: List[OpenQuestion] = Field(
        default_factory=list,
        description="Questions for the professional to investigate"
    )

    # === THREAD 8: WHAT WE DON'T KNOW ===
    missing_info: List[MissingInfo] = Field(
        default_factory=list,
        description="Information we don't have yet - honest about gaps"
    )

    # === THREAD 9: PRACTICAL TIPS (מה יכול לעזור) ===
    practical_tips: List[PracticalTip] = Field(
        default_factory=list,
        description="Practical tips connecting strengths to challenges. MOST USEFUL FOR TEACHERS - everyday tips they can use immediately. For specialists: can be more professional."
    )

    # === CLOSING ===
    closing_note: Optional[str] = Field(
        default=None,
        description="Brief closing - invitation to contact, thanks, etc."
    )


# Schema for Gemini structured output
def get_summary_schema():
    """Get the JSON schema for structured output."""
    return ProfessionalSummary.model_json_schema()
