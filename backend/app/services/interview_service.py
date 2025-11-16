"""
Interview Service - Manages interview state and completeness calculation

This service:
1. Stores extracted interview data per family
2. Calculates interview completeness (now using schema_registry!)
3. Tracks conversation history
4. Determines which prompt/functions to use
5. Generates video guidelines when ready
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

# Wu Wei Architecture: Import schema registry for config-driven completeness
from app.config.schema_registry import get_schema_registry, calculate_completeness as config_calculate_completeness

# Wu Wei Architecture: Import artifact models
from app.models.artifact import Artifact

logger = logging.getLogger(__name__)


class ExtractedData(BaseModel):
    """Structured interview data extracted from conversation"""
    child_name: Optional[str] = None
    age: Optional[float] = None
    gender: Optional[str] = None  # "male", "female", "unknown"
    primary_concerns: List[str] = []
    concern_details: Optional[str] = None
    strengths: Optional[str] = None
    developmental_history: Optional[str] = None
    family_context: Optional[str] = None
    daily_routines: Optional[str] = None
    parent_goals: Optional[str] = None
    urgent_flags: List[str] = []

    # Metadata
    last_updated: datetime = datetime.now()
    extraction_count: int = 0  # How many times data was extracted


class InterviewState(BaseModel):
    """Complete interview state for a family"""
    family_id: str
    extracted_data: ExtractedData = ExtractedData()
    completeness: float = 0.0  # 0.0 to 1.0
    conversation_history: List[Dict[str, str]] = []  # List of {role, content}

    # 🌟 Wu Wei: Artifact storage (replaces boolean flags)
    artifacts: Dict[str, Artifact] = Field(default_factory=dict, description="Generated artifacts keyed by artifact_id")

    # DEPRECATED: Use artifacts["video_guidelines"].exists instead
    video_guidelines_generated: bool = False

    phase: str = "screening"  # 🌟 Wu Wei: Current workflow phase (screening, ongoing, re_assessment)
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        """Get artifact by ID, return None if doesn't exist."""
        return self.artifacts.get(artifact_id)

    def has_artifact(self, artifact_id: str) -> bool:
        """Check if artifact exists and is ready."""
        artifact = self.get_artifact(artifact_id)
        return artifact is not None and artifact.is_ready

    def add_artifact(self, artifact: Artifact):
        """Add or update an artifact."""
        self.artifacts[artifact.artifact_id] = artifact
        self.updated_at = datetime.now()

        # DEPRECATED: Maintain backwards compatibility
        if artifact.artifact_id == "baseline_video_guidelines" and artifact.is_ready:
            self.video_guidelines_generated = True


class InterviewService:
    """
    Manages interview state and data extraction for families

    In production, this would integrate with Graphiti for persistent storage.
    For now, we use in-memory storage.
    """

    def __init__(self):
        # In-memory storage: family_id -> InterviewState
        self.sessions: Dict[str, InterviewState] = {}
        logger.info("InterviewService initialized (in-memory mode)")

    def get_or_create_session(self, family_id: str) -> InterviewState:
        """Get existing session or create new one"""
        if family_id not in self.sessions:
            self.sessions[family_id] = InterviewState(family_id=family_id)
            logger.info(f"Created new interview session for family: {family_id}")
        return self.sessions[family_id]

    def update_extracted_data(
        self,
        family_id: str,
        new_data: Dict[str, Any]
    ) -> ExtractedData:
        """
        Update extracted data with new information (additive merge)

        Rules:
        - Scalars: new value overrides if not empty
        - Arrays: merge and deduplicate
        - Strings: append if significantly different
        """
        session = self.get_or_create_session(family_id)
        current = session.extracted_data

        # ========================================================================
        # FIELD NAME NORMALIZATION: Handle both LITE and FULL function schemas
        # ========================================================================
        # LITE schema uses: concerns, concern_description, other_info
        # FULL schema uses: primary_concerns, concern_details
        #
        # This normalization allows the system to handle both transparently.
        # ========================================================================

        # Normalize: concerns → primary_concerns
        if 'concerns' in new_data and 'primary_concerns' not in new_data:
            new_data['primary_concerns'] = new_data.pop('concerns')
            logger.info(f"📝 Normalized 'concerns' → 'primary_concerns': {new_data['primary_concerns']}")

        # Normalize: concern_description → concern_details
        if 'concern_description' in new_data and 'concern_details' not in new_data:
            new_data['concern_details'] = new_data.pop('concern_description')
            details_preview = (new_data['concern_details'][:100] if new_data['concern_details'] else 'None')
            logger.info(f"📝 Normalized 'concern_description' → 'concern_details': {details_preview}")

        # Discard other_info (LITE field for miscellaneous demographic data)
        # This is usually redundant info already captured in other fields (age, gender, etc.)
        # DO NOT put it in concern_details - that's for actual concerns only!
        if 'other_info' in new_data:
            other_text = new_data.pop('other_info')
            other_preview = (other_text[:100] if other_text else 'None')
            logger.info(f"📝 Got 'other_info' (LITE field): {other_preview}")
            logger.info("   → Discarded (usually redundant demographic data)")
            # Note: other_info is intentionally NOT stored anywhere
            # It contains misc demographic info that's already in name/age/gender fields

        # Update scalar fields
        for field in ['child_name', 'age', 'gender']:
            if field in new_data and new_data[field]:
                setattr(current, field, new_data[field])

        # Merge arrays (concerns, urgent_flags)
        if 'primary_concerns' in new_data and new_data['primary_concerns']:
            concerns = set(current.primary_concerns + new_data['primary_concerns'])
            current.primary_concerns = list(concerns)

        if 'urgent_flags' in new_data and new_data['urgent_flags']:
            flags = set(current.urgent_flags + new_data['urgent_flags'])
            current.urgent_flags = list(flags)

        # Append or merge text fields
        text_fields = [
            'concern_details', 'strengths', 'developmental_history',
            'family_context', 'daily_routines', 'parent_goals'
        ]

        for field in text_fields:
            if field in new_data and new_data[field]:
                current_text = getattr(current, field) or ""
                new_text = new_data[field]

                # Only append if new info is significantly different
                if new_text.lower() not in current_text.lower():
                    combined = f"{current_text}. {new_text}".strip(". ")
                    setattr(current, field, combined)

        # Update metadata
        current.last_updated = datetime.now()
        current.extraction_count += 1

        # Recalculate completeness
        session.completeness = self.calculate_completeness(family_id)
        session.updated_at = datetime.now()

        logger.info(
            f"Updated data for {family_id}: "
            f"completeness={session.completeness:.1%}, "
            f"extractions={current.extraction_count}"
        )

        return current

    def calculate_completeness(self, family_id: str) -> float:
        """
        Calculate interview completeness (0.0 to 1.0)

        🌟 Wu Wei Architecture: Now uses schema_registry for config-driven calculation!

        Previously hardcoded weights are now defined in:
        backend/config/schemas/extraction_schema.yaml

        This means:
        - Weights can be adjusted without code changes
        - Easy to experiment with different weightings
        - Consistent with other services using the same schema
        - Documented in YAML (human-readable)

        Weighting (defined in extraction_schema.yaml):
        - Basic info (name, age, gender): 5%
        - Primary concerns with details: 50% (MAIN focus)
        - Strengths: 10%
        - Developmental context: 15%
        - Family/routines/goals: 20%
        """
        session = self.get_or_create_session(family_id)
        data = session.extracted_data

        # Convert ExtractedData to dict for schema_registry
        extracted_dict = {
            "child_name": data.child_name,
            "age": data.age,
            "gender": data.gender,
            "primary_concerns": data.primary_concerns,
            "concern_details": data.concern_details,
            "strengths": data.strengths,
            "developmental_history": data.developmental_history,
            "family_context": data.family_context,
            "daily_routines": data.daily_routines,
            "parent_goals": data.parent_goals,
            "urgent_flags": data.urgent_flags,
        }

        # Use config-driven completeness calculation
        completeness = config_calculate_completeness(extracted_dict)

        logger.debug(
            f"Calculated completeness for {family_id}: {completeness:.1%} "
            f"(using schema_registry)"
        )

        return completeness

    def add_conversation_turn(
        self,
        family_id: str,
        role: str,
        content: str
    ):
        """Add a message to conversation history"""
        session = self.get_or_create_session(family_id)
        session.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        session.updated_at = datetime.now()

    def get_conversation_history(
        self,
        family_id: str,
        last_n: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """Get conversation history (optionally last N messages)"""
        session = self.get_or_create_session(family_id)
        history = session.conversation_history

        if last_n:
            return history[-last_n:]
        return history

    def get_context_summary(self, family_id: str) -> str:
        """Get a text summary of what's been collected so far"""
        session = self.get_or_create_session(family_id)
        data = session.extracted_data

        parts = []

        if data.child_name:
            parts.append(f"Child's name: {data.child_name}")
        if data.age:
            parts.append(f"Age: {data.age} years")
        if data.gender and data.gender != "unknown":
            parts.append(f"Gender: {data.gender}")

        if data.primary_concerns:
            concerns_str = ", ".join(data.primary_concerns)
            parts.append(f"Concerns: {concerns_str}")

        if data.strengths:
            parts.append(f"Strengths: {data.strengths[:100]}")

        if not parts:
            return "No information collected yet."

        return ". ".join(parts)

    def should_use_lite_mode(self, family_id: str, model_name: str) -> bool:
        """
        Determine if lite mode should be used

        Lite mode for:
        - Flash models (ONLY if LLM_USE_ENHANCED is true)
        - Early in conversation (< 20% complete, ONLY if LLM_USE_ENHANCED is true)

        If LLM_USE_ENHANCED=false, NEVER use lite mode regardless of model.
        """
        import os
        from .llm.gemini_provider_enhanced import GeminiProviderEnhanced

        # Check if enhanced mode is enabled
        use_enhanced_env = os.getenv("LLM_USE_ENHANCED", "true").lower()
        use_enhanced = use_enhanced_env in ["true", "1", "yes"]

        # If enhanced mode is disabled, NEVER use lite mode
        if not use_enhanced:
            return False

        # Check model name (only if enhanced mode is on)
        if "flash" in model_name.lower():
            return True

        # Check conversation progress (only if enhanced mode is on)
        session = self.get_or_create_session(family_id)
        if session.completeness < 0.20:
            # Early conversation - use simpler prompts
            return True

        return False

    def mark_video_guidelines_generated(self, family_id: str):
        """Mark that video guidelines have been generated"""
        session = self.get_or_create_session(family_id)
        session.video_guidelines_generated = True
        session.updated_at = datetime.now()
        logger.info(f"Video guidelines generated for {family_id}")

    def get_session_stats(self, family_id: str) -> Dict[str, Any]:
        """Get statistics about the session"""
        session = self.get_or_create_session(family_id)
        data = session.extracted_data

        return {
            "family_id": family_id,
            "completeness": session.completeness,
            "completeness_pct": f"{session.completeness:.1%}",
            "extraction_count": data.extraction_count,
            "conversation_turns": len(session.conversation_history),
            "video_guidelines_ready": session.video_guidelines_generated,
            "has_child_name": bool(data.child_name),
            "has_age": bool(data.age),
            "concerns_count": len(data.primary_concerns),
            "urgent_flags_count": len(data.urgent_flags),
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat()
        }


# Singleton instance
_interview_service = None

def get_interview_service() -> InterviewService:
    """Get singleton InterviewService instance"""
    global _interview_service
    if _interview_service is None:
        _interview_service = InterviewService()
    return _interview_service
