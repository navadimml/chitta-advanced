"""
Lifecycle Manager - Wu Wei Architecture Core

This is the heart of the Wu Wei system. It:
1. Reads lifecycle_events.yaml (the simplified moments configuration)
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

from app.config.config_loader import load_lifecycle_events
from app.services.wu_wei_prerequisites import WuWeiPrerequisites
from app.services.artifact_generation_service import ArtifactGenerationService
from app.services.sse_notifier import get_sse_notifier

logger = logging.getLogger(__name__)


class LifecycleManager:
    """
    🌟 Wu Wei: Configuration-driven moment lifecycle manager (פשוט - נטול חלקים עודפים)

    This manager reads lifecycle_events.yaml and automatically:
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
        self.config = load_lifecycle_events()
        self.prerequisite_evaluator = WuWeiPrerequisites()
        self.artifact_service = artifact_service or ArtifactGenerationService()

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
            session: InterviewState session

        Returns:
            Dict with:
                - artifacts_generated: List[str] of artifact IDs
                - events_triggered: List[dict] of moment events with messages/UI
                - capabilities_unlocked: List[str] of capability names
        """
        artifacts_generated = []
        events_triggered = []
        capabilities_unlocked = []

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
                    message = message_template.format(
                        child_name=context.get("child_name", "הילד/ה")
                    )

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

                    events_triggered.append(event_data)
                    logger.info(f"🎉 Triggered moment event: {moment_id}")

                # Check if this moment unlocks capabilities
                # Unlock IMMEDIATELY on FIRST transition (don't wait for artifact)
                unlocked = moment_config.get("unlocks", [])
                if unlocked and just_became_ready:  # Only on first transition, not retries
                    capabilities_unlocked.extend(unlocked)
                    logger.info(f"🔓 Unlocked capabilities: {unlocked}")

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
            "capabilities_unlocked": capabilities_unlocked
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
            # This was already evaluated and added to context
            return context.get("knowledge_is_rich", False) == expected_value

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
        Generate an artifact based on its ID and moment configuration.

        This routes to the appropriate generation method based on artifact type.
        """
        logger.info(f"🎬 Generating artifact: {artifact_id}")

        # Route to appropriate generation method
        if artifact_id == "baseline_video_guidelines":
            return await self.artifact_service.generate_video_guidelines(context)

        elif artifact_id == "re_assessment_video_guidelines":
            return await self.artifact_service.generate_video_guidelines(context)

        # Add more artifact types here as they're implemented
        else:
            logger.warning(
                f"⚠️ No generation method defined for artifact: {artifact_id}. "
                f"Add it to LifecycleManager._generate_artifact()"
            )
            return None

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

                logger.info(
                    f"✅ Background generation complete: {artifact_id} "
                    f"({len(artifact.content)} chars) - artifact now available in session"
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
            else:
                logger.error(
                    f"❌ Background generation failed: {artifact_id}: "
                    f"{artifact.error_message if artifact else 'Unknown error'}"
                )

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


# Singleton instance
_lifecycle_manager: Optional[LifecycleManager] = None


def get_lifecycle_manager() -> LifecycleManager:
    """Get global LifecycleManager instance (singleton)."""
    global _lifecycle_manager
    if _lifecycle_manager is None:
        _lifecycle_manager = LifecycleManager()
    return _lifecycle_manager
