"""
Session Service - Manages conversation session state and completeness calculation

🌟 MIGRATION NOTE: This module now delegates to UnifiedStateService internally
while maintaining backwards-compatible APIs. The ExtractedData and SessionState
classes are kept for compatibility with existing code.

🌟 Wu Wei: Renamed from InterviewService - reflects continuous conversation, not staged interview

This service:
1. Stores extracted conversation data per family
2. Calculates conversation completeness (using schema_registry)
3. Tracks conversation history
4. Manages artifacts (video guidelines, reports, etc.)
5. No phases - state emerges from artifacts and prerequisites
6. Persists sessions to survive server restarts (interim solution)
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator
import json
import os
import asyncio

# Wu Wei Architecture: Import schema registry for config-driven completeness
from app.config.schema_registry import get_schema_registry, calculate_completeness as config_calculate_completeness

# Wu Wei Architecture: Import artifact models
from app.models.artifact import Artifact

# LLM for semantic completeness verification
from app.services.llm.factory import create_llm_provider
from app.services.llm.base import Message

# Completeness verification prompt
from app.prompts.completeness_verification import build_completeness_verification_prompt

logger = logging.getLogger(__name__)


class ExtractedData(BaseModel):
    """Structured conversation data extracted from ongoing dialogue

    🔒 Wu Wei Robustness: Validates extraction data to prevent garbage from entering the system
    """
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

    # Parent preferences and decisions
    filming_preference: Optional[str] = None  # "wants_videos" | "report_only" | None

    # Metadata
    last_updated: datetime = datetime.now()
    extraction_count: int = 0  # How many times data was extracted

    @validator('child_name')
    def validate_child_name(cls, v):
        """Reject placeholder values and invalid names"""
        if v is None:
            return None

        # List of placeholder values that should be rejected
        placeholders = [
            'unknown', 'not mentioned', 'null', 'none',
            'לא צוין', 'לא ידוע', 'לא נמסר',
            '(not mentioned yet)', '(unknown)',
            'not specified', 'n/a', 'na'
        ]

        if v.lower().strip() in placeholders:
            logger.warning(f"🚫 Rejected placeholder child_name: '{v}'")
            return None

        # Name must be at least 2 characters
        if len(v.strip()) < 2:
            logger.warning(f"🚫 Rejected too-short child_name: '{v}'")
            return None

        # Reject gibberish: Check if name contains only non-alphabetic characters
        cleaned = v.strip()
        alpha_chars = sum(1 for c in cleaned if c.isalpha())
        if alpha_chars == 0:
            logger.warning(f"🚫 Rejected gibberish child_name (no letters): '{v}'")
            return None

        # Reject if more than 50% non-alphabetic (too much gibberish)
        if len(cleaned) > 0 and alpha_chars / len(cleaned) < 0.5:
            logger.warning(f"🚫 Rejected gibberish child_name (too many non-letters): '{v}'")
            return None

        # Return cleaned name
        return cleaned

    @validator('age')
    def validate_age(cls, v):
        """Ensure age is in valid range for child development (0-18 years)"""
        if v is None:
            return None

        # Age must be between 0 and 18 for child development
        if v < 0 or v > 18:
            logger.warning(f"🚫 Rejected out-of-range age: {v} (must be 0-18)")
            return None

        return v

    @validator('gender')
    def validate_gender(cls, v):
        """Ensure gender is one of valid values"""
        if v is None:
            return None

        valid_genders = ['male', 'female', 'unknown']
        if v.lower() not in valid_genders:
            logger.warning(f"🚫 Rejected invalid gender: '{v}' (must be male/female/unknown)")
            return 'unknown'  # Default to unknown for invalid values

        return v.lower()

    @validator('primary_concerns')
    def validate_primary_concerns(cls, v):
        """Ensure concerns are from valid enum and not placeholders"""
        if not v:
            return []

        valid_concerns = [
            'speech', 'social', 'attention', 'motor', 'sensory',
            'emotional', 'behavioral', 'learning', 'sleep', 'eating', 'other'
        ]

        # Filter out invalid concerns
        validated = []
        for concern in v:
            if concern.lower() in valid_concerns:
                validated.append(concern.lower())
            else:
                logger.warning(f"🚫 Rejected invalid concern: '{concern}'")

        # CRITICAL: Reject 'other' if it's the ONLY concern (likely gibberish/off-topic)
        # 'other' should only be valid when combined with specific concerns
        if validated == ['other']:
            logger.warning("🚫 Rejected 'other' as sole concern (likely off-topic or gibberish)")
            return []

        return validated


class SessionState(BaseModel):
    """Complete conversation session state for a family"""
    family_id: str
    extracted_data: ExtractedData = ExtractedData()
    completeness: float = 0.0  # 0.0 to 1.0 (character-based heuristic)
    conversation_history: List[Dict[str, str]] = []  # List of {role, content}

    # 🌟 Wu Wei: Artifact storage (replaces boolean flags)
    artifacts: Dict[str, Artifact] = Field(default_factory=dict, description="Generated artifacts keyed by artifact_id")

    # 🔍 Semantic completeness verification (LLM-based quality assessment)
    semantic_verification: Optional[Dict[str, Any]] = None  # Result from verify_semantic_completeness()
    semantic_verification_turn: int = 0  # Last turn when semantic verification was run

    # 🔄 Background completeness check (non-blocking)
    pending_completeness_check: Optional[Dict[str, Any]] = None  # Metadata about running background check
    completed_check_result: Optional[Dict[str, Any]] = None  # Completed check result waiting to be used

    # 🌟 Wu Wei: Moment context tracking (for persistent moment guidance)
    last_triggered_moment: Optional[Dict[str, Any]] = None  # Last triggered moment {id, context, ...}

    # 🎥 Domain: Video analysis tracking
    guideline_scenario_count: Optional[int] = None  # Number of video scenarios in generated guidelines (for comparison)
    video_analysis_status: Optional[str] = None  # "pending", "analyzing", "complete"

    # 🌟 Wu Wei: No phases - continuous conversation flow
    # DEPRECATED: phase field removed - workflow state derived from artifacts and context
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
        """
        🌟 Wu Wei: Add or update an artifact.

        State is derived from artifacts - no need for separate flags.
        """
        self.artifacts[artifact.artifact_id] = artifact
        self.updated_at = datetime.now()


class SessionService:
    """
    🌟 Wu Wei: Manages conversation session state and data extraction

    Renamed from InterviewService to reflect continuous conversation flow.
    In production, integrates with Graphiti for persistent storage.
    For now, uses in-memory storage with file/Redis persistence backup.
    """

    def __init__(self, llm_provider=None):
        # In-memory storage: family_id -> SessionState
        self.sessions: Dict[str, SessionState] = {}

        # 🌟 Persistence layer for surviving server restarts
        self._persistence = None
        self._persistence_enabled = os.getenv("SESSION_PERSISTENCE_ENABLED", "true").lower() == "true"

        # LLM for semantic completeness verification
        if llm_provider is None:
            # Create strong LLM for completeness verification
            strong_model = os.getenv("STRONG_LLM_MODEL", "gemini-2.0-flash-exp")
            provider_type = os.getenv("LLM_PROVIDER", "gemini")
            self.verification_llm = create_llm_provider(
                provider_type=provider_type,
                model=strong_model,
                use_enhanced=False
            )
            logger.info(f"🔍 Created verification LLM: {strong_model}")
        else:
            self.verification_llm = llm_provider

        # Initialize persistence if enabled
        if self._persistence_enabled:
            self._init_persistence()

        logger.info(f"SessionService initialized (persistence: {self._persistence_enabled})")

    def _init_persistence(self):
        """Initialize persistence layer"""
        try:
            from app.services.session_persistence import get_session_persistence
            self._persistence = get_session_persistence()
            logger.info("Session persistence layer initialized")
        except Exception as e:
            logger.warning(f"Could not initialize persistence: {e}")
            self._persistence = None

    async def _persist_session(self, family_id: str):
        """Persist session to storage (non-blocking)"""
        if not self._persistence or family_id not in self.sessions:
            return

        try:
            session = self.sessions[family_id]
            # Convert to dict for persistence
            session_data = {
                "family_id": session.family_id,
                "extracted_data": session.extracted_data.model_dump(),
                "completeness": session.completeness,
                "conversation_history": session.conversation_history,
                "artifacts": {k: v.model_dump() if hasattr(v, 'model_dump') else v for k, v in session.artifacts.items()},
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "semantic_verification": session.semantic_verification,
                "semantic_verification_turn": session.semantic_verification_turn,
            }

            # Save asynchronously
            await self._persistence.save_session(family_id, session_data)

        except Exception as e:
            logger.warning(f"Failed to persist session {family_id}: {e}")

    async def _load_persisted_session(self, family_id: str) -> Optional[SessionState]:
        """Load session from persistent storage"""
        if not self._persistence:
            return None

        try:
            data = await self._persistence.load_session(family_id)
            if not data:
                return None

            # Reconstruct SessionState from persisted data
            extracted_data = ExtractedData(**data.get("extracted_data", {}))

            session = SessionState(
                family_id=family_id,
                extracted_data=extracted_data,
                completeness=data.get("completeness", 0.0),
                conversation_history=data.get("conversation_history", []),
                semantic_verification=data.get("semantic_verification"),
                semantic_verification_turn=data.get("semantic_verification_turn", 0),
            )

            # Restore timestamps
            if data.get("created_at"):
                session.created_at = datetime.fromisoformat(data["created_at"])
            if data.get("updated_at"):
                session.updated_at = datetime.fromisoformat(data["updated_at"])

            # Restore artifacts
            for artifact_id, artifact_data in data.get("artifacts", {}).items():
                if isinstance(artifact_data, dict):
                    session.artifacts[artifact_id] = Artifact(**artifact_data)

            logger.info(f"Restored persisted session for {family_id}")
            return session

        except Exception as e:
            logger.warning(f"Failed to load persisted session {family_id}: {e}")
            return None

    def get_or_create_session(self, family_id: str) -> SessionState:
        """Get existing session or create new one"""
        if family_id not in self.sessions:
            # Try to load from persistence first
            if self._persistence_enabled:
                # Use asyncio to run async load in sync context
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # We're in an async context, schedule the coroutine
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(
                                asyncio.run,
                                self._load_persisted_session(family_id)
                            )
                            persisted = future.result(timeout=5)
                    else:
                        persisted = loop.run_until_complete(
                            self._load_persisted_session(family_id)
                        )

                    if persisted:
                        self.sessions[family_id] = persisted
                        logger.info(f"Restored session from persistence for family: {family_id}")
                        return self.sessions[family_id]
                except Exception as e:
                    logger.warning(f"Could not load persisted session: {e}")

            # Create new session
            self.sessions[family_id] = SessionState(family_id=family_id)
            logger.info(f"Created new conversation session for family: {family_id}")
        return self.sessions[family_id]

    async def get_or_create_session_async(self, family_id: str) -> SessionState:
        """Async version: Get existing session or create new one"""
        if family_id not in self.sessions:
            # Try to load from persistence first
            if self._persistence_enabled:
                persisted = await self._load_persisted_session(family_id)
                if persisted:
                    self.sessions[family_id] = persisted
                    logger.info(f"Restored session from persistence for family: {family_id}")
                    return self.sessions[family_id]

            # Create new session
            self.sessions[family_id] = SessionState(family_id=family_id)
            logger.info(f"Created new conversation session for family: {family_id}")
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
        # Reject string literals that represent null/missing values
        invalid_values = ['None', 'null', 'NULL', 'unknown', '(not mentioned yet)']
        for field in ['child_name', 'age', 'gender', 'filming_preference']:
            if field not in new_data:
                continue  # Field not provided in this extraction

            value = new_data[field]

            # 🔍 DEBUG: Trace filming_preference processing
            if field == 'filming_preference':
                logger.info(f"🔍 DEBUG filming_preference:")
                logger.info(f"   BEFORE: current.filming_preference = {getattr(current, field, 'ATTR_NOT_FOUND')}")
                logger.info(f"   VALUE TO SET: {value} (type: {type(value).__name__})")

            # Skip if None (field not mentioned in conversation yet)
            if value is None:
                if field == 'filming_preference':
                    logger.info(f"   SKIPPED: value is None")
                continue

            # For string fields, reject invalid placeholder strings
            if isinstance(value, str) and value in invalid_values:
                if field == 'filming_preference':
                    logger.info(f"   SKIPPED: value in invalid_values")
                continue

            # Save the valid value
            setattr(current, field, value)

            # 🔍 DEBUG: Confirm filming_preference was set
            if field == 'filming_preference':
                logger.info(f"   AFTER setattr: current.filming_preference = {getattr(current, field, 'ATTR_NOT_FOUND')}")

        # Merge arrays (concerns, urgent_flags)
        if 'primary_concerns' in new_data:
            new_concerns = new_data['primary_concerns']
            # Skip if None or empty
            if new_concerns:
                # Ensure it's a list (LLM sometimes returns string)
                if isinstance(new_concerns, str):
                    new_concerns = [new_concerns]
                concerns = set(current.primary_concerns + new_concerns)
                current.primary_concerns = list(concerns)

        if 'urgent_flags' in new_data:
            new_flags = new_data['urgent_flags']
            # Skip if None or empty
            if new_flags:
                # Ensure it's a list (LLM sometimes returns string)
                if isinstance(new_flags, str):
                    new_flags = [new_flags]
                flags = set(current.urgent_flags + new_flags)
                current.urgent_flags = list(flags)

        # Append or merge text fields
        text_fields = [
            'concern_details', 'strengths', 'developmental_history',
            'family_context', 'daily_routines', 'parent_goals'
        ]

        for field in text_fields:
            if field not in new_data:
                continue  # Field not provided in this extraction

            new_text = new_data[field]

            # Skip if None or empty
            if not new_text:
                continue

            current_text = getattr(current, field) or ""

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

        # 🔍 Wu Wei Robustness: Verify extraction quality
        self._verify_extraction_quality(family_id, session, current)

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

    def _verify_extraction_quality(
        self,
        family_id: str,
        session: 'SessionState',
        data: ExtractedData
    ):
        """
        🔍 Wu Wei Robustness: Verify extraction quality and warn about missing critical data

        This helps catch extraction failures early and provides visibility into data quality.
        """
        turns = len(session.conversation_history)

        # After first few turns, we should have basic info
        if turns >= 6:  # After 3 exchanges (user + assistant = 2 messages per exchange)
            warnings = []

            if not data.child_name:
                warnings.append("⚠️ Child name not extracted after 3+ turns")

            if not data.age:
                warnings.append("⚠️ Child age not extracted after 3+ turns")

            if not data.primary_concerns or len(data.primary_concerns) == 0:
                warnings.append("⚠️ No primary concerns extracted after 3+ turns")

            for warning in warnings:
                logger.warning(f"[{family_id}] {warning}")

    def get_extraction_quality(self, family_id: str) -> dict:
        """
        🔍 Wu Wei Robustness: Check extraction quality and completeness

        Returns quality metrics showing what's been extracted and what's missing.
        Useful for monitoring and debugging extraction issues.
        """
        session = self.get_or_create_session(family_id)
        data = session.extracted_data
        turns = len(session.conversation_history)

        quality = {
            'has_name': bool(data.child_name),
            'has_age': bool(data.age),
            'has_gender': bool(data.gender and data.gender != 'unknown'),
            'has_concerns': len(data.primary_concerns) > 0,
            'concern_count': len(data.primary_concerns),
            'has_concern_details': bool(data.concern_details),
            'has_strengths': bool(data.strengths),
            'has_developmental_history': bool(data.developmental_history),
            'has_family_context': bool(data.family_context),
            'turns_count': turns,
            'extraction_count': data.extraction_count,
            'completeness': session.completeness,
            'warnings': []
        }

        # Quality warnings after sufficient conversation
        if turns >= 6:  # After 3+ exchanges
            if not quality['has_name']:
                quality['warnings'].append("Child name not extracted after 3+ turns")
            if not quality['has_age']:
                quality['warnings'].append("Child age not extracted after 3+ turns")
            if not quality['has_concerns']:
                quality['warnings'].append("No primary concerns extracted after 3+ turns")

        # Success indicators
        quality['basic_info_complete'] = quality['has_name'] and quality['has_age']
        quality['concerns_captured'] = quality['has_concerns'] and quality['has_concern_details']

        return quality

    async def verify_semantic_completeness(self, family_id: str) -> dict:
        """
        🔍 Wu Wei Robustness: Verify completeness using LLM semantic understanding

        Instead of counting characters, this uses an LLM to evaluate whether we have
        enough USEFUL information for:
        1. Generating effective video guidelines
        2. Creating a comprehensive assessment report

        Returns:
            dict with completeness scores, gaps, and recommendations
        """
        session = self.get_or_create_session(family_id)
        data = session.extracted_data

        # Build extracted data dict
        extracted_dict = {
            'child_name': data.child_name,
            'age': data.age,
            'gender': data.gender,
            'primary_concerns': data.primary_concerns,
            'concern_details': data.concern_details,
            'strengths': data.strengths,
            'developmental_history': data.developmental_history,
            'family_context': data.family_context,
            'daily_routines': data.daily_routines,
            'parent_goals': data.parent_goals,
        }

        # Build verification prompt
        prompt = build_completeness_verification_prompt(
            extracted_data=extracted_dict,
            conversation_history=session.conversation_history
        )

        try:
            logger.info(f"🔍 Running semantic completeness verification for {family_id}")

            # Call LLM with JSON mode
            response = await self.verification_llm.chat(
                messages=[Message(role="user", content=prompt)],
                temperature=0.1,  # Low temp for consistent evaluation
                max_tokens=2000,
                response_format="json"  # Request JSON output
            )

            # Parse JSON response
            result = json.loads(response.content)

            logger.info(f"✅ Semantic verification complete:")
            logger.info(f"   Overall: {result.get('overall_completeness', 0)}%")
            logger.info(f"   Video guidelines ready: {result.get('video_guidelines_readiness', 0)}%")
            logger.info(f"   Report ready: {result.get('comprehensive_report_readiness', 0)}%")
            logger.info(f"   Recommendation: {result.get('recommendation', 'unknown')}")

            # Log critical gaps
            critical_gaps = result.get('critical_gaps', [])
            if critical_gaps:
                logger.warning(f"   Critical gaps: {len(critical_gaps)}")
                for gap in critical_gaps:
                    logger.warning(f"      - {gap.get('field')}: {gap.get('issue')}")

            # Store result in session state
            turn_count = len([msg for msg in session.conversation_history if msg.get('role') == 'user'])
            session.semantic_verification = result
            session.semantic_verification_turn = turn_count
            session.updated_at = datetime.now()

            return result

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse LLM response as JSON: {e}")
            logger.error(f"   Response content: {response.content[:200]}")
            # Return fallback result
            return {
                "overall_completeness": session.completeness * 100,
                "video_guidelines_readiness": session.completeness * 100,
                "comprehensive_report_readiness": session.completeness * 100,
                "recommendation": "continue_conversation",
                "error": "Failed to parse LLM response"
            }

        except Exception as e:
            logger.error(f"❌ Error in semantic completeness verification: {e}", exc_info=True)
            # Return fallback result
            return {
                "overall_completeness": session.completeness * 100,
                "video_guidelines_readiness": session.completeness * 100,
                "comprehensive_report_readiness": session.completeness * 100,
                "recommendation": "continue_conversation",
                "error": str(e)
            }

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

        # 🌟 Persist session after each turn (fire and forget)
        if self._persistence_enabled:
            asyncio.create_task(self._persist_session(family_id))

    async def add_conversation_turn_async(
        self,
        family_id: str,
        role: str,
        content: str
    ):
        """Async version: Add a message to conversation history"""
        session = await self.get_or_create_session_async(family_id)
        session.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        session.updated_at = datetime.now()

        # 🌟 Persist session after each turn
        if self._persistence_enabled:
            await self._persist_session(family_id)

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
            "video_guidelines_ready": session.has_artifact("baseline_video_guidelines"),
            "has_child_name": bool(data.child_name),
            "has_age": bool(data.age),
            "concerns_count": len(data.primary_concerns),
            "urgent_flags_count": len(data.urgent_flags),
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat()
        }


# Singleton instance
_session_service = None

def get_session_service() -> SessionService:
    """Get singleton SessionService instance"""
    global _session_service
    if _session_service is None:
        _session_service = SessionService()
    return _session_service

# DEPRECATED: Backwards compatibility - remove in future
def get_interview_service() -> SessionService:
    """DEPRECATED: Use get_session_service() instead"""
    return get_session_service()
