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
    """
    A pathway connecting strength to challenge - PARENT-FACING content.

    This is shown directly to parents, so write TO them, not ABOUT them.
    """
    hook: str = Field(description="What the child loves/responds to (e.g., 'אהבה למילים וטקסטים כתובים')")
    concern: str = Field(description="The situation this addresses - written TO parents, not ABOUT them. ❌ 'ההורים מודאגים מ...' ✅ 'כשרוצים לדעת מה עובר עליה'")
    suggestion: str = Field(description="Concrete actionable tip the parent can try")


class ProfessionalSummarySchema(BaseModel):
    """
    Summary for a professional - PREPARING THE GROUND, not delivering findings.

    AUTHOR: This summary is written by CHITTA (the system), not the parents.
    Chitta gathered information from conversations with parents AND video observations.

    You are NOT the one who names. You are the one who prepares the ground.
    The summary should make the clinician think: 'This helps me know where to look.'

    LANGUAGE BY RECIPIENT:
    - teacher: Everyday Hebrew, practical terms
    - specialist: Can use clinical terms they understand (רגישות אודיטורית, ויסות חושי)
    - medical: Clinical precision expected (היסטוריה התפתחותית, אבני דרך מוטוריות)

    The THREE THREADS principle applies to ALL - separation matters regardless of language.
    """
    # Core holistic content (same for all recipients)
    who_this_child_is: str = Field(
        description="2-3 sentences about who this child IS as a whole person - their essence, what makes them unique. Written by Chitta based on conversations and observations."
    )
    strengths_and_interests: str = Field(
        description="What opens them up, what they love - this is the bridge for ANY professional to reach them. Based on what we learned."
    )
    what_parents_shared: str = Field(
        description="Thread 1: What PARENTS told us. Report their observations: 'ההורים סיפרו לנו ש...', 'האמא שיתפה ש...'. Their words, not our interpretation."
    )
    what_we_noticed: str = Field(
        description="Thread 2: What CHITTA noticed - patterns and connections WE observed from conversations and videos. Use: 'שמנו לב ש...', 'תהינו אם יש קשר...'. These are OUR hypotheses, framed as offerings."
    )
    what_remains_open: str = Field(
        description="Thread 3: Questions WE (Chitta) are curious about. 'שווה לבדוק אם...', 'אנחנו סקרנים לגבי...'. Invite the professional to investigate what we couldn't."
    )

    # Recipient-specific lens
    recipient_type: str = Field(
        description="'teacher' (everyday Hebrew) | 'specialist' (clinical terms OK) | 'medical' (clinical precision expected)"
    )
    role_specific_section: str = Field(
        description="teacher: daily strategies, what helps at home, everyday language. specialist: investigation questions, clinical terms OK. medical: observable patterns, developmental timeline, clinical precision."
    )

    # The invitation
    invitation: str = Field(
        description="Chitta inviting the professional to help. e.g., 'נשמח שתעזרו לנו להבין...', 'נשמח לשמוע את ההתרשמות שלכם'"
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
