"""
Lifecycle Manager - Wu Wei Architecture Core

This is the heart of the Wu Wei system. It:
1. Reads workflow.yaml (the simplified moments configuration)
2. Monitors prerequisite transitions
3. Auto-generates artifacts when moment prerequisites become met
4. Triggers moment messages and UI guidance
5. Is 100% configuration-driven - no hardcoded logic

Key Principle: EMERGENCE, NOT FORCE
- We don't force artifacts to be generated
- We check what's POSSIBLE now based on prerequisites
- When prerequisites transition from false→true, the moment happens
- Everything flows from the YAML configuration
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.config.config_loader import load_workflow
from app.services.wu_wei_prerequisites import WuWeiPrerequisites
from app.services.artifact_generation_service import ArtifactGenerationService
from app.services.sse_notifier import get_sse_notifier
from app.config.action_registry import get_available_actions as get_available_action_ids
from app.services.card_lifecycle_service import CardLifecycleService

logger = logging.getLogger(__name__)


class LifecycleManager:
    """
    🌟 Wu Wei: Configuration-driven moment lifecycle manager (פשוט - נטול חלקים עודפים)

    This manager reads workflow.yaml and automatically:
    - Detects when moment prerequisites are met
    - Generates artifacts at the right moment
    - Triggers moment messages and UI guidance
    - Unlocks capabilities

    NO HARDCODED LOGIC. Everything emerges from the simplified moments configuration.
    """

    def __init__(
        self,
        artifact_service: Optional[ArtifactGenerationService] = None
    ):
        """Initialize lifecycle manager with configuration."""
        self.config = load_workflow()
        self.prerequisite_evaluator = WuWeiPrerequisites()
        self.artifact_service = artifact_service or ArtifactGenerationService()

        # 🌟 Phase 1 Living Dashboard: Card Lifecycle Service
        self.card_lifecycle_service = CardLifecycleService()

        # Track previous state to detect transitions
        self._previous_states: Dict[str, Dict[str, bool]] = {}

        # Track generation attempts to prevent infinite loops
        self._generation_attempts: Dict[str, Dict[str, int]] = {}  # {family_id: {artifact_id: attempt_count}}
        self._max_generation_attempts = 3  # Maximum retry attempts per artifact

        logger.info(
            f"🌟 LifecycleManager initialized with simplified Wu Wei configuration: "
            f"{len(self.config.get('moments', {}))} moments, "
            f"{len(self.config.get('always_available', []))} always-available capabilities"
        )

    def get_lifecycle_config(self) -> Dict[str, Any]:
        """Get the lifecycle configuration (moments, always_available, etc.)"""
        return self.config

    async def process_lifecycle_events(
        self,
        family_id: str,
        context: Dict[str, Any],
        session: Any
    ) -> Dict[str, Any]:
        """
        🌟 Wu Wei: Check moments and auto-generate what emerges (פשוט - נטול חלקים עודפים)

        This is called AFTER each conversation turn. It:
        1. Evaluates all moment prerequisites
        2. Detects transitions (false → true)
        3. Auto-generates artifacts when moment prerequisites just became met
        4. Triggers moment messages and UI guidance
        5. Returns list of what changed

        Args:
            family_id: Family identifier
            context: Current context (flattened, includes extracted_data)
            session: SessionState session

        Returns:
            Dict with:
                - artifacts_generated: List[str] of artifact IDs
                - events_triggered: List[dict] of moment events with messages/UI
                - capabilities_unlocked: List[str] of capability names
        """
        artifacts_generated = []
        events_triggered = []
        capabilities_unlocked = []

        # 🌟 Event-Driven Discovery: Capture available actions BEFORE any moments trigger
        actions_before = set(get_available_action_ids(context))
        logger.info(f"📊 Actions available before moment processing: {actions_before}")

        # Get previous state for this family
        previous_state = self._previous_states.get(family_id, {})
        current_state = {}

        # 🌟 Wu Wei: Iterate through ALL moments defined in YAML
        moments = self.config.get("moments", {})

        logger.info(f"🔍 Wu Wei: Checking {len(moments)} moments for {family_id}")

        for moment_id, moment_config in moments.items():
            logger.info(f"🔍 Checking moment: {moment_id}")

            # Get artifact ID if this moment generates an artifact
            artifact_id = moment_config.get("artifact")

            # If moment generates artifact, check current status
            artifact = session.get_artifact(artifact_id) if artifact_id else None

            # Skip if artifact is currently being generated (avoid concurrent generations)
            if artifact and artifact.is_generating:
                logger.info(f"  ↳ Artifact {artifact_id} is currently generating, skipping")
                current_state[moment_id] = False  # Not yet ready
                continue

            # Check if ready artifact exists and is valid
            if artifact_id and session.has_artifact(artifact_id):
                # Artifact is ready - validate it's not empty
                if artifact and artifact_id == "baseline_video_guidelines":
                    # Parse content to check if scenarios exist
                    try:
                        import json
                        if isinstance(artifact.content, str):
                            content = json.loads(artifact.content)
                        else:
                            content = artifact.content

                        scenarios = content.get("scenarios", [])
                        if len(scenarios) == 0:
                            logger.info(f"  ↳ Artifact {artifact_id} exists but has 0 scenarios - forcing regeneration")
                            # Don't skip, allow regeneration
                        else:
                            logger.info(f"  ↳ Artifact {artifact_id} already exists with {len(scenarios)} scenarios, skipping")
                            current_state[moment_id] = True
                            continue
                    except Exception as e:
                        logger.warning(f"  ↳ Failed to validate artifact content: {e} - allowing regeneration")
                else:
                    logger.info(f"  ↳ Artifact {artifact_id} already exists, skipping")
                    current_state[moment_id] = True
                    continue

            # Get prerequisites from 'when' field
            prerequisites = moment_config.get("when")

            if not prerequisites:
                logger.info(f"  ↳ No prerequisites defined (always-available moment)")
                current_state[moment_id] = False
                continue

            # Log what we're evaluating
            logger.info(f"  ↳ Evaluating prerequisites: {prerequisites}")
            logger.debug(f"  ↳ Context keys available: {list(context.keys())}")

            # Evaluate prerequisites using Wu Wei evaluator
            prereqs_met = self._evaluate_prerequisites(prerequisites, context)
            current_state[moment_id] = prereqs_met

            logger.info(f"  ↳ Prerequisites met: {prereqs_met}")

            # Detect TRANSITION: false → true
            was_met = previous_state.get(moment_id, False)
            just_became_ready = prereqs_met and not was_met

            # SPECIAL CASE: If artifact doesn't exist OR is empty OR failed, retry generation
            # But limit retries to prevent infinite loops!
            artifact_is_invalid = False
            artifact_is_generating = artifact and artifact.is_generating if artifact else False

            # Only validate ready artifacts for emptiness
            if artifact_id and session.has_artifact(artifact_id):
                # Artifact is ready - check if it's empty (specific validation for guidelines)
                if artifact_id == "baseline_video_guidelines":
                    try:
                        import json
                        if isinstance(artifact.content, str):
                            content = json.loads(artifact.content)
                        else:
                            content = artifact.content
                        scenarios = content.get("scenarios", [])
                        if len(scenarios) == 0:
                            artifact_is_invalid = True
                            logger.info(f"  ↳ Artifact exists but is empty (0 scenarios)")
                    except Exception as e:
                        logger.warning(f"  ↳ Failed to validate artifact: {e}")
                        artifact_is_invalid = True

            # Check if artifact errored out
            artifact_has_error = artifact and artifact.has_error if artifact else False

            # Check retry attempts for this artifact
            if family_id not in self._generation_attempts:
                self._generation_attempts[family_id] = {}

            attempt_count = self._generation_attempts[family_id].get(artifact_id, 0)
            max_attempts_reached = attempt_count >= self._max_generation_attempts

            should_retry_artifact = (
                artifact_id and  # Moment generates artifact
                prereqs_met and  # Prerequisites are met
                not artifact_is_generating and  # NOT currently generating (avoid concurrent)
                (not session.has_artifact(artifact_id) or artifact_is_invalid or artifact_has_error) and  # Artifact missing, empty, or failed
                not max_attempts_reached  # Haven't exceeded retry limit
            )

            logger.info(f"  ↳ Was previously met: {was_met}, Just became ready: {just_became_ready}")
            logger.info(f"  ↳ Attempt count: {attempt_count}/{self._max_generation_attempts}")
            if artifact_is_generating:
                logger.info(f"  ↳ Artifact is currently generating - skipping retry to avoid concurrent generations")

            if should_retry_artifact and not just_became_ready:
                if max_attempts_reached:
                    logger.error(
                        f"  ⚠️ Max retry attempts ({self._max_generation_attempts}) reached for {artifact_id}. "
                        f"Skipping further retries. Check generation errors."
                    )
                elif artifact_is_invalid:
                    logger.info(f"  ↳ Artifact invalid (empty) despite prereqs met - will retry generation")
                else:
                    logger.info(f"  ↳ Artifact missing despite prereqs met - will retry generation")

            if just_became_ready or should_retry_artifact:
                if just_became_ready:
                    logger.info(
                        f"🌟 Wu Wei TRANSITION DETECTED: {moment_id} prerequisites just became met!"
                    )
                else:
                    retry_reason = "invalid/empty" if artifact_is_invalid else "missing"
                    logger.info(
                        f"🔄 Wu Wei RETRY: {moment_id} artifact {retry_reason}, retrying generation"
                    )

                # Check if this moment has a message (lifecycle event)
                # Send message IMMEDIATELY on FIRST transition (don't wait for artifact)
                message_template = moment_config.get("message")
                if message_template and just_became_ready:  # Only on first transition, not retries
                    # Format message with context variables
                    # Use fallback if child_name is None, empty, or placeholder
                    child_name_raw = context.get("child_name")
                    invalid_names = [None, "", "unknown", "Unknown", "לא צוין", "לא ידוע"]
                    child_name = child_name_raw if child_name_raw not in invalid_names else "הילד/ה"

                    # Prepare format kwargs with all common context variables
                    format_kwargs = {
                        "child_name": child_name,
                        "uploaded_video_count": context.get("uploaded_video_count", 0),
                    }

                    # Use safe formatting - only replace variables that exist in template
                    try:
                        message = message_template.format(**format_kwargs)
                    except KeyError as e:
                        # If template references a variable we don't have, log warning and use template as-is
                        logger.warning(f"⚠️ Message template for {moment_id} references undefined variable: {e}")
                        message = message_template

                    # 🌟 Wu Wei: Build event data (all in one place now!)
                    event_data = {
                        "event_name": moment_id,
                        "message": message
                    }

                    # Add ui context if defined (for UI guidance)
                    ui_context = moment_config.get("ui")
                    if ui_context:
                        event_data["ui_context"] = ui_context
                        logger.info(f"  📍 UI Context ({ui_context.get('type')}): {ui_context.get('default')[:50]}...")

                    # Add system context if defined (to prevent hallucinations)
                    system_context = moment_config.get("context")
                    if system_context:
                        event_data["system_context"] = system_context
                        logger.info(f"  🧠 System Context: Added {len(system_context)} chars to prevent hallucination")

                    # 🌟 Event-Driven Cards: Add card if moment defines one
                    card_config = moment_config.get("card")
                    if card_config:
                        event_data["card"] = card_config
                        logger.info(f"  💳 Card: {card_config.get('title', 'Untitled')[:50]}...")

                    events_triggered.append(event_data)
                    logger.info(f"🎉 Triggered moment event: {moment_id}")

                    # Wu Wei: Update session with last triggered moment (for persistent context)
                    session.last_triggered_moment = {
                        "id": moment_id,
                        "context": moment_config.get("context", ""),
                        "message": message
                    }

                # If this moment generates an artifact, generate it IN BACKGROUND!
                # Don't block the conversation - user gets response immediately
                if artifact_id:
                    import asyncio
                    from app.models.artifact import Artifact
                    from datetime import datetime

                    # Increment attempt counter
                    if family_id not in self._generation_attempts:
                        self._generation_attempts[family_id] = {}
                    self._generation_attempts[family_id][artifact_id] = attempt_count + 1
                    logger.info(f"📊 Incrementing attempt counter: {artifact_id} → {attempt_count + 1}")

                    # Create placeholder artifact with "generating" status
                    # This ensures the card appears IMMEDIATELY in the UI
                    placeholder = Artifact(
                        artifact_id=artifact_id,
                        artifact_type=artifact_id,
                        status="generating",
                        content=None,  # No content yet
                        metadata={
                            "message": "מכין הנחיות...",
                            "attempt_count": attempt_count + 1,
                            "max_attempts": self._max_generation_attempts
                        },
                        created_at=datetime.now()
                    )
                    session.add_artifact(placeholder)
                    logger.info(f"📋 Added placeholder artifact for {artifact_id} (card will show immediately)")

                    # 🌟 Event-Driven Discovery: Check what actions just became available!
                    # Rebuild context with new artifact
                    updated_context = {**context, "artifacts": session.artifacts}
                    actions_after = set(get_available_action_ids(updated_context))
                    newly_available = actions_after - actions_before

                    if newly_available:
                        logger.info(f"🔓 Auto-discovered newly available actions: {newly_available}")
                        capabilities_unlocked.extend(list(newly_available))

                        # Add to event data for LLM context
                        if events_triggered and just_became_ready:
                            events_triggered[-1]["newly_available_actions"] = list(newly_available)

                    # Create background task for artifact generation
                    task = asyncio.create_task(
                        self._generate_artifact_background(
                            artifact_id,
                            moment_config,
                            context,
                            session,
                            family_id
                        )
                    )

                    # Track that generation started (for logging)
                    artifacts_generated.append(f"{artifact_id}:generating")
                    logger.info(f"🚀 Started background generation of {artifact_id} (non-blocking, attempt {attempt_count + 1})")


            elif prereqs_met:
                logger.debug(f"  ↳ Prerequisites met but already processed before")
            else:
                logger.debug(f"  ↳ Prerequisites NOT met yet")

        # Save current state for next time
        self._previous_states[family_id] = current_state

        # 🌟 Phase 1 Living Dashboard: Process card lifecycle
        # Get family state for card management
        from app.services.unified_state_service import get_unified_state_service
        state_service = get_unified_state_service()
        family_state = state_service.get_family_state(family_id)

        # Build previous context from stored snapshot (or empty if first time)
        previous_card_context = family_state.previous_context_snapshot or {}

        # Process card transitions (creates new cards on FALSE→TRUE)
        new_cards = self.card_lifecycle_service.process_transitions(
            family_state=family_state,
            previous_context=previous_card_context,
            current_context=context
        )

        # Update existing cards (dismissals, dynamic content)
        card_changes = self.card_lifecycle_service.update_active_cards(
            family_state=family_state,
            context=context
        )

        # Store current context for next comparison
        family_state.previous_context_snapshot = context.copy()

        # Get visible cards for response
        visible_cards = self.card_lifecycle_service.get_visible_cards_serialized(family_state)

        # Log card lifecycle activity
        if new_cards or card_changes["dismissed"]:
            logger.info(
                f"💳 Card Lifecycle for {family_id}:\n"
                f"  - Cards created: {[c.card_id for c in new_cards]}\n"
                f"  - Cards dismissed: {card_changes['dismissed']}\n"
                f"  - Cards updated: {card_changes['updated']}\n"
                f"  - Visible cards: {len(visible_cards)}"
            )

        # Log summary
        if artifacts_generated or events_triggered or capabilities_unlocked:
            logger.info(
                f"🌟 Wu Wei Lifecycle Summary for {family_id}:\n"
                f"  - Artifacts generated: {artifacts_generated}\n"
                f"  - Moments triggered: {[e['event_name'] for e in events_triggered]}\n"
                f"  - Capabilities unlocked: {capabilities_unlocked}"
            )

        return {
            "artifacts_generated": artifacts_generated,
            "events_triggered": events_triggered,
            "capabilities_unlocked": capabilities_unlocked,
            # 🌟 Phase 1 Living Dashboard: Include card state
            "active_cards": visible_cards,
            "cards_created": [c.card_id for c in new_cards],
            "cards_dismissed": card_changes["dismissed"],
        }

    def _evaluate_prerequisites(
        self,
        prerequisites: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """
        Evaluate prerequisites from YAML against current context.

        Supports:
        - knowledge_is_rich: true
        - baseline_video_guidelines.exists: true
        - uploaded_video_count: ">= 3"
        - OR: {condition} (alternative path to satisfy prerequisites)
        - AND: {conditions} (all conditions in dict must be met)

        YAML Structure Interpretation:
        prerequisites:
          A: true
          B: true
          OR:
            C: true

        Means: (A AND B) OR (C)
        The OR provides an alternative path to satisfy prerequisites.

        Args:
            prerequisites: Prerequisites dict from YAML
            context: Current context

        Returns:
            True if all prerequisites met
        """
        if not isinstance(prerequisites, dict):
            logger.error(f"Prerequisites must be dict, got {type(prerequisites)}: {prerequisites}")
            return False

        # Handle OR conditions - provides alternative path
        if "OR" in prerequisites:
            or_condition = prerequisites["OR"]
            non_or_conditions = {k: v for k, v in prerequisites.items() if k != "OR"}

            # Evaluate OR condition
            or_met = False
            if isinstance(or_condition, dict):
                # Old format: OR is a single dict of alternative prerequisites
                or_met = self._evaluate_prerequisites(or_condition, context)
            elif isinstance(or_condition, list):
                # New format: OR is a list of condition dicts (any can satisfy)
                for condition_dict in or_condition:
                    if isinstance(condition_dict, dict):
                        if self._evaluate_prerequisites(condition_dict, context):
                            or_met = True
                            break
                    else:
                        logger.warning(f"OR list item has unexpected type: {type(condition_dict)}")
            else:
                # Unexpected structure
                logger.warning(f"OR condition has unexpected type: {type(or_condition)}")

            if or_met:
                return True  # Alternative path satisfied!

            # OR not met, check if all non-OR conditions met
            if not non_or_conditions:
                return False  # Only had OR, and it's not met

            # Evaluate non-OR conditions
            for key, expected_value in non_or_conditions.items():
                if not self._evaluate_single_prerequisite(key, expected_value, context):
                    return False
            return True

        # Handle AND conditions (explicit)
        if "AND" in prerequisites:
            and_conditions = prerequisites["AND"]
            if isinstance(and_conditions, dict):
                return self._evaluate_prerequisites(and_conditions, context)
            else:
                logger.warning(f"AND condition has unexpected type: {type(and_conditions)}")
                return False

        # Default: All key-value pairs must be met (implicit AND)
        for key, expected_value in prerequisites.items():
            if not self._evaluate_single_prerequisite(key, expected_value, context):
                return False

        return True

    def _evaluate_single_prerequisite(
        self,
        key: str,
        expected_value: Any,
        context: Dict[str, Any]
    ) -> bool:
        """
        Evaluate a single prerequisite.

        Examples:
        - knowledge_is_rich: true → Check context["knowledge_is_rich"]
        - baseline_video_guidelines.exists: true → Check artifact exists
        - uploaded_video_count: ">= 3" → Compare numbers
        """
        # Special case: knowledge_is_rich
        if key == "knowledge_is_rich":
            # Delegate to WuWeiPrerequisites for dynamic evaluation
            result = self.prerequisite_evaluator.evaluate_knowledge_richness(context)
            return result.met == expected_value

        # Special case: artifact.exists checks
        if ".exists" in key:
            artifact_id = key.replace(".exists", "")
            artifacts = context.get("artifacts", {})

            if artifact_id in artifacts:
                artifact_obj = artifacts[artifact_id]
                if hasattr(artifact_obj, 'exists'):
                    return artifact_obj.exists == expected_value
                else:
                    # Dict format
                    return artifact_obj.get("exists", False) == expected_value

            return False == expected_value  # Doesn't exist

        # Special case: numeric comparisons
        if isinstance(expected_value, str) and any(op in expected_value for op in [">", "<", ">=", "<=", "=="]):
            actual_value = context.get(key, 0)

            # Parse comparison
            if ">=" in expected_value:
                threshold = int(expected_value.split(">=")[1].strip())
                return actual_value >= threshold
            elif "<=" in expected_value:
                threshold = int(expected_value.split("<=")[1].strip())
                return actual_value <= threshold
            elif ">" in expected_value:
                threshold = int(expected_value.split(">")[1].strip())
                return actual_value > threshold
            elif "<" in expected_value:
                threshold = int(expected_value.split("<")[1].strip())
                return actual_value < threshold
            elif "==" in expected_value:
                threshold = int(expected_value.split("==")[1].strip())
                return actual_value == threshold

        # Special case: flag checks (re_assessment.active)
        if "." in key:
            parts = key.split(".")
            if len(parts) == 2:
                parent_key, child_key = parts
                parent_value = context.get(parent_key, {})
                if isinstance(parent_value, dict):
                    return parent_value.get(child_key, False) == expected_value

        # Default: simple equality
        return context.get(key, None) == expected_value

    def _find_event_for_artifact(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """
        Find the lifecycle event (moment) configuration that creates a specific artifact.

        This is used to get UI context for artifact awareness in conversations.

        Args:
            artifact_id: The artifact identifier to find

        Returns:
            Moment configuration dict with 'artifact', 'message', 'ui', etc.
            or None if not found
        """
        moments = self.config.get("moments", {})

        for moment_id, moment_config in moments.items():
            if moment_config.get("artifact") == artifact_id:
                return moment_config

        return None

    async def _generate_artifact(
        self,
        artifact_id: str,
        moment_config: Dict[str, Any],
        context: Dict[str, Any]
    ):
        """
        🌟 Wu Wei: Generate artifact using config-driven dispatch.

        No more hardcoded artifact IDs! The artifact_generators.yaml config
        determines which method to call and what dependencies are required.

        Args:
            artifact_id: Artifact identifier
            moment_config: Moment configuration from lifecycle_events.yaml
            context: Current context with artifacts and session data

        Returns:
            Generated Artifact or None if generation fails
        """
        logger.info(f"🎬 Config-driven generation for: {artifact_id}")

        # Get generator config from artifact_manager
        from app.config.artifact_manager import get_artifact_manager
        artifact_manager = get_artifact_manager()
        generator_config = artifact_manager.get_generator_config(artifact_id)

        if not generator_config:
            logger.warning(
                f"⚠️ No generator config found for: {artifact_id}. "
                f"Add it to artifact_generators.yaml"
            )
            return None

        # Check required artifacts exist
        required_artifacts = generator_config.get("requires_artifacts", [])
        for required_artifact_id in required_artifacts:
            required_artifact = context.get("artifacts", {}).get(required_artifact_id)
            if not required_artifact or not required_artifact.get("exists"):
                logger.error(
                    f"❌ Cannot generate {artifact_id}: "
                    f"required artifact {required_artifact_id} not available"
                )
                return None

        # Check optional artifacts (don't fail if missing, but log)
        optional_artifacts = generator_config.get("optional_artifacts", [])
        for optional_artifact_id in optional_artifacts:
            optional_artifact = context.get("artifacts", {}).get(optional_artifact_id)
            if optional_artifact and optional_artifact.get("exists"):
                logger.info(f"✅ Optional artifact {optional_artifact_id} available for {artifact_id}")
            else:
                logger.info(f"ℹ️ Optional artifact {optional_artifact_id} not available (OK)")

        # Call generic artifact generator with config params
        logger.info(f"✅ All dependencies met for {artifact_id}, calling generator...")
        return await self.artifact_service.generate_artifact(
            artifact_id=artifact_id,
            session_data=context,
            **generator_config.get("params", {})
        )

    async def _generate_artifact_background(
        self,
        artifact_id: str,
        moment_config: Dict[str, Any],
        context: Dict[str, Any],
        session: Any,
        family_id: str
    ):
        """
        Generate artifact in background without blocking conversation.

        This allows the user to get an immediate response while artifact
        generation happens asynchronously. The artifact will appear in the
        UI on the next conversation turn.

        Args:
            artifact_id: ID of artifact to generate
            moment_config: Moment configuration from lifecycle_events.yaml
            context: Current context for generation
            session: Interview session to update when complete
            family_id: Family identifier for logging
        """
        try:
            logger.info(f"🎬 Background generation started: {artifact_id} for {family_id}")

            # Generate the artifact (this is the slow LLM call)
            artifact = await self._generate_artifact(
                artifact_id,
                moment_config,
                context
            )

            if artifact and artifact.is_ready:
                # Store in session
                session.add_artifact(artifact)

                # 🌟 Wu Wei: Config-driven validation (if defined in artifact_generators.yaml)
                from app.config.artifact_manager import get_artifact_manager
                artifact_manager = get_artifact_manager()
                generator_config = artifact_manager.get_generator_config(artifact_id)

                if generator_config and "validation" in generator_config:
                    try:
                        self._validate_artifact(artifact, generator_config["validation"])
                    except Exception as e:
                        logger.warning(f"⚠️ Artifact validation warning for {artifact_id}: {e}")

                logger.info(
                    f"✅ Background generation complete: {artifact_id} "
                    f"({len(artifact.content)} chars) - artifact now available in session"
                )
                logger.info(
                    f"📦 Stored artifact status: {artifact.status}, "
                    f"exists: {artifact.exists}, is_ready: {artifact.is_ready}, "
                    f"session_id: {id(session)}, artifacts_dict_id: {id(session.artifacts)}"
                )

                # 🌟 Wu Wei: Notify SSE clients that artifact is ready
                import asyncio
                sse_notifier = get_sse_notifier()
                asyncio.create_task(
                    sse_notifier.notify_artifact_updated(
                        family_id,
                        artifact_id,
                        "ready",
                        artifact.content
                    )
                )

                # 🚨 CRITICAL: Re-evaluate cards now that artifact status changed
                # The preparing card should hide, the ready card should show
                from app.services.prerequisite_service import get_prerequisite_service
                from app.config.card_generator import get_card_generator

                prerequisite_service = get_prerequisite_service()
                card_generator = get_card_generator()

                # 🚨 FIX: Convert Artifact objects to dict format for card evaluation
                # Cards use dot notation (artifacts.baseline_video_guidelines.status)
                # which requires dict format, not Artifact objects
                artifacts_dict = {}
                for art_id, art_obj in session.artifacts.items():
                    if hasattr(art_obj, 'exists'):
                        # It's an Artifact object - convert to dict
                        artifacts_dict[art_id] = {
                            "exists": art_obj.exists,
                            "status": art_obj.status,
                            "artifact_id": art_obj.artifact_id
                        }
                    elif isinstance(art_obj, dict):
                        # Already a dict
                        artifacts_dict[art_id] = art_obj

                # 🌟 Wu Wei: Get video count from FamilyState
                from app.services.unified_state_service import get_unified_state_service
                state_service = get_unified_state_service()
                state = state_service.get_family_state(family_id)
                video_count = len(state.videos_uploaded)

                # Build context for card evaluation (same as conversation_service does)
                session_data = {
                    "family_id": family_id,
                    "extracted_data": session.extracted_data.model_dump() if hasattr(session.extracted_data, 'model_dump') else session.extracted_data.dict(),
                    "message_count": len(session.conversation_history),
                    "artifacts": artifacts_dict,  # 🚨 FIX: Dict format for card evaluation
                    "uploaded_video_count": video_count,  # 🌟 Wu Wei: From FamilyState
                }

                card_context = prerequisite_service.get_context_for_cards(session_data)
                updated_cards = card_generator.get_visible_cards(card_context, max_cards=4)

                # Notify frontend of card changes
                asyncio.create_task(
                    sse_notifier.notify_cards_updated(family_id, updated_cards)
                )
                logger.info(f"📡 SSE: Notified card update after {artifact_id} ready ({len(updated_cards)} cards)")
            else:
                logger.error(
                    f"❌ Background generation failed: {artifact_id}: "
                    f"{artifact.error_message if artifact else 'Unknown error'}"
                )

                # 🚨 CRITICAL FIX: Update session artifact status to "error"
                # Without this, the placeholder stays "generating" forever!
                from app.models.artifact import Artifact
                from datetime import datetime

                error_artifact = Artifact(
                    artifact_id=artifact_id,
                    artifact_type=artifact_id,
                    status="error",
                    content=None,
                    metadata={
                        "error": artifact.error_message if artifact else "Unknown error",
                        "failed_at": datetime.now().isoformat()
                    },
                    created_at=datetime.now()
                )
                session.add_artifact(error_artifact)
                logger.info(f"📋 Updated session artifact to status='error' for {artifact_id}")

                # Notify SSE clients of failure
                import asyncio
                sse_notifier = get_sse_notifier()
                asyncio.create_task(
                    sse_notifier.notify_artifact_updated(
                        family_id,
                        artifact_id,
                        "error"
                    )
                )

        except Exception as e:
            logger.error(
                f"❌ Background generation exception: {artifact_id}: {e}",
                exc_info=True
            )

            # 🚨 CRITICAL FIX: Update session artifact status to "error" on exception
            # Without this, the placeholder stays "generating" forever!
            from app.models.artifact import Artifact
            from datetime import datetime

            error_artifact = Artifact(
                artifact_id=artifact_id,
                artifact_type=artifact_id,
                status="error",
                content=None,
                metadata={
                    "error": str(e),
                    "failed_at": datetime.now().isoformat()
                },
                created_at=datetime.now()
            )
            session.add_artifact(error_artifact)
            logger.info(f"📋 Updated session artifact to status='error' after exception for {artifact_id}")

    def _validate_artifact(self, artifact: Any, validation_config: Dict[str, Any]) -> None:
        """
        🌟 Wu Wei: Validate artifact content using config-driven rules.

        Args:
            artifact: Generated artifact
            validation_config: Validation rules from artifact_generators.yaml

        Raises:
            ValueError: If validation fails
        """
        import json

        validation_type = validation_config.get("type")

        if validation_type == "json_structure":
            # Validate JSON structure
            try:
                if isinstance(artifact.content, str):
                    content = json.loads(artifact.content)
                else:
                    content = artifact.content

                # Check each validation rule
                checks = validation_config.get("checks", [])
                for check in checks:
                    path = check.get("path")
                    expected_type = check.get("type")
                    min_length = check.get("min_length")
                    error_message = check.get("error_message", f"Validation failed for {path}")

                    # Get value at path
                    value = content.get(path)

                    # Check type
                    if expected_type == "array" and not isinstance(value, list):
                        raise ValueError(f"{error_message}: expected array, got {type(value)}")

                    # Check minimum length
                    if min_length is not None and len(value) < min_length:
                        raise ValueError(f"{error_message}: length {len(value)} < minimum {min_length}")

                logger.info(f"✅ Artifact validation passed: {artifact.artifact_id}")

            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON content: {e}")
            except Exception as e:
                raise ValueError(f"Validation error: {e}")


# Singleton instance
_lifecycle_manager: Optional[LifecycleManager] = None


def get_lifecycle_manager() -> LifecycleManager:
    """Get global LifecycleManager instance (singleton)."""
    global _lifecycle_manager
    if _lifecycle_manager is None:
        _lifecycle_manager = LifecycleManager()
    return _lifecycle_manager
