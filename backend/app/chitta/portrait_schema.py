"""
Portrait Schema - Pydantic models for LLM structured output

These models define the schema for Gemini's structured output feature.
They mirror the dataclass models in models.py but are Pydantic for JSON schema generation.

Usage:
    from portrait_schema import PortraitOutput

    response = await llm.chat_with_structured_output(
        messages=[...],
        response_schema=PortraitOutput.model_json_schema()
    )
    portrait = PortraitOutput.model_validate(response)
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class PortraitSectionSchema(BaseModel):
    """A thematic section in the child's portrait."""
    title: str = Field(description="Meaningful Hebrew title for the section")
    icon: str = Field(description="Single emoji that matches the theme")
    content: str = Field(description="1-3 sentences or bullet points (with bullet prefix)")
    content_type: str = Field(
        default="paragraph",
        description="Type of content: 'paragraph' or 'bullets'"
    )


class PatternSchema(BaseModel):
    """A cross-domain pattern - the clinical insight gift."""
    description: str = Field(
        description="Pattern description using situational language"
    )
    domains: List[str] = Field(
        description="Domains involved: behavioral, emotional, sensory, social, motor, cognitive, communication"
    )


class InterventionPathwaySchema(BaseModel):
    """A pathway connecting strength to challenge."""
    hook: str = Field(description="What the child loves/responds to")
    concern: str = Field(description="The challenge in parent words")
    suggestion: str = Field(description="Concrete actionable tip")


class ProfessionalSummarySchema(BaseModel):
    """
    Holistic-first summary for a professional.

    Every recipient gets the WHOLE child - that's Chitta's core value.
    The lens (emphasis) changes based on recipient_type.
    """
    # Core holistic content (same for all recipients)
    who_this_child_is: str = Field(
        description="2-3 sentences about who this child IS as a whole person"
    )
    strengths_and_interests: str = Field(
        description="What opens them up, what they love"
    )
    what_parents_shared: str = Field(
        description="Thread 1: Parent observations in their words"
    )
    what_we_noticed: str = Field(
        description="Thread 2: Patterns and connections - frame as offerings"
    )
    what_remains_open: str = Field(
        description="Thread 3: Questions worth exploring"
    )

    # Recipient-specific lens
    recipient_type: str = Field(
        description="'teacher' | 'specialist' | 'medical'"
    )
    role_specific_section: str = Field(
        description="teacher: daily strategies, specialist: investigation questions, medical: observable patterns"
    )

    # The invitation
    invitation: str = Field(
        description="What we hope they'll help explore"
    )


class ExpertRecommendationSchema(BaseModel):
    """
    Professional recommendation - preparing the ground, not a referral.

    The key insight: match by WHO THIS CHILD IS, not just what they struggle with.
    """
    profession: str = Field(description="Hebrew profession name")
    specialization: str = Field(
        description="REAL clinical specialization that resonates with child's STRENGTHS"
    )
    why_this_match: str = Field(
        description="Connect child's strength to why this professional would reach them"
    )
    recommended_approach: str = Field(
        description="What approach would work based on how child connects"
    )
    why_this_approach: str = Field(
        description="Based on how the child opens up"
    )
    what_to_look_for: List[str] = Field(
        description="2-3 things to ask when choosing a professional"
    )
    professional_summaries: List[ProfessionalSummarySchema] = Field(
        description="Holistic summaries for different recipients (teacher, specialist, medical)"
    )
    when_to_consider: str = Field(
        default="כשתרגישו מוכנים",
        description="Parent-centered timing suggestion"
    )


class PortraitOutput(BaseModel):
    """
    Complete portrait output from LLM.

    This is the root schema for structured output.
    """
    # Portrait sections - the thematic cards
    portrait_sections: List[PortraitSectionSchema] = Field(
        description="3-5 thematic cards capturing who this child is"
    )

    # Essence fields (merged directly, not nested)
    narrative: str = Field(
        description="2-3 sentences about who this child IS as a whole person"
    )
    temperament: List[str] = Field(
        default_factory=list,
        description="Everyday Hebrew descriptions of temperament traits"
    )
    core_qualities: List[str] = Field(
        default_factory=list,
        description="Core qualities like 'curious', 'creative'"
    )

    # Clinical insights
    patterns: List[PatternSchema] = Field(
        default_factory=list,
        description="Cross-domain insights - the clinical gift"
    )
    intervention_pathways: List[InterventionPathwaySchema] = Field(
        default_factory=list,
        description="Strength-to-challenge bridges"
    )
    open_questions: List[str] = Field(
        default_factory=list,
        description="Questions we're still curious about, phrased in parent language. Frame as curiosity not gaps. e.g., 'למה דווקא בבוקר יותר קשה?' not 'חסר מידע על בקרים'"
    )
    expert_recommendations: List[ExpertRecommendationSchema] = Field(
        default_factory=list,
        description="Professional recommendations (only if genuinely helpful)"
    )
