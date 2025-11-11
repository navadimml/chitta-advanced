"""
Lifecycle Manager - Wu Wei Architecture Core

This is the heart of the Wu Wei system. It:
1. Reads lifecycle_events.yaml (the dependency graph)
2. Monitors prerequisite transitions
3. Auto-generates artifacts when prerequisites become met
4. Triggers lifecycle events
5. Is 100% configuration-driven - no hardcoded logic

Key Principle: EMERGENCE, NOT FORCE
- We don't force artifacts to be generated
- We check what's POSSIBLE now based on the dependency graph
- When prerequisites transition from false→true, we act
- Everything flows from the YAML configuration
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.config.config_loader import load_lifecycle_events
from app.services.wu_wei_prerequisites import WuWeiPrerequisites
from app.services.artifact_generation_service import ArtifactGenerationService

logger = logging.getLogger(__name__)


class LifecycleManager:
    """
    🌟 Wu Wei: Configuration-driven artifact lifecycle manager

    This manager reads lifecycle_events.yaml and automatically:
    - Detects when prerequisites are met
    - Generates artifacts at the right moment
    - Triggers lifecycle events
    - Unlocks capabilities

    NO HARDCODED LOGIC. Everything emerges from the dependency graph.
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

        logger.info(
            f"🌟 LifecycleManager initialized with Wu Wei dependency graph: "
            f"{len(self.config.get('artifacts', {}))} artifacts, "
            f"{len(self.config.get('capabilities', {}))} capabilities, "
            f"{len(self.config.get('lifecycle_events', {}))} events"
        )

    async def process_lifecycle_events(
        self,
        family_id: str,
        context: Dict[str, Any],
        session: Any
    ) -> Dict[str, Any]:
        """
        🌟 Wu Wei: Check dependency graph and auto-generate what emerges

        This is called AFTER each conversation turn. It:
        1. Evaluates all artifact prerequisites
        2. Detects transitions (false → true)
        3. Auto-generates artifacts whose prerequisites just became met
        4. Triggers lifecycle events
        5. Returns list of what changed

        Args:
            family_id: Family identifier
            context: Current context (flattened, includes extracted_data)
            session: InterviewState session

        Returns:
            Dict with:
                - artifacts_generated: List[str] of artifact IDs
                - events_triggered: List[str] of event names
                - capabilities_unlocked: List[str] of capability names
        """
        artifacts_generated = []
        events_triggered = []
        capabilities_unlocked = []

        # Get previous state for this family
        previous_state = self._previous_states.get(family_id, {})
        current_state = {}

        # 🌟 Wu Wei: Iterate through ALL artifacts defined in YAML
        artifacts_config = self.config.get("artifacts", {})

        logger.info(f"🔍 Wu Wei: Checking {len(artifacts_config)} artifacts for {family_id}")

        for artifact_id, artifact_def in artifacts_config.items():
            logger.info(f"🔍 Checking artifact: {artifact_id}")

            # Skip if artifact already exists
            if session.has_artifact(artifact_id):
                logger.info(f"  ↳ Already exists, skipping")
                current_state[artifact_id] = True
                continue

            # Get prerequisites from YAML
            prerequisites = artifact_def.get("prerequisites")

            if not prerequisites:
                logger.info(f"  ↳ No prerequisites defined")
                current_state[artifact_id] = False
                continue

            # Log what we're evaluating
            logger.info(f"  ↳ Evaluating prerequisites: {prerequisites}")
            logger.debug(f"  ↳ Context keys available: {list(context.keys())}")

            # Evaluate prerequisites using Wu Wei evaluator
            prereqs_met = self._evaluate_prerequisites(prerequisites, context)
            current_state[artifact_id] = prereqs_met

            logger.info(f"  ↳ Prerequisites met: {prereqs_met}")

            # Detect TRANSITION: false → true
            was_met = previous_state.get(artifact_id, False)
            just_became_ready = prereqs_met and not was_met

            logger.info(f"  ↳ Was previously met: {was_met}, Just became ready: {just_became_ready}")

            if just_became_ready:
                logger.info(
                    f"🌟 Wu Wei TRANSITION DETECTED: {artifact_id} prerequisites just became met!"
                )

                # 🎬 AUTO-GENERATE the artifact!
                try:
                    artifact = await self._generate_artifact(
                        artifact_id,
                        artifact_def,
                        context
                    )

                    if artifact and artifact.is_ready:
                        # Store in session
                        session.add_artifact(artifact)
                        artifacts_generated.append(artifact_id)

                        logger.info(
                            f"✅ Wu Wei: Auto-generated {artifact_id} "
                            f"({len(artifact.content)} chars)"
                        )

                        # Check if this unlocks capabilities
                        unlocked = artifact_def.get("unlocks", [])
                        if unlocked:
                            capabilities_unlocked.extend(unlocked)
                            logger.info(f"🔓 Unlocked capabilities: {unlocked}")

                        # Trigger lifecycle event if defined in artifact config
                        event_name = artifact_def.get("event")  # Get event name from YAML
                        if event_name:
                            lifecycle_events = self.config.get("lifecycle_events", {})
                            if event_name in lifecycle_events:
                                event_config = lifecycle_events[event_name]
                                # Format message with context variables
                                message = event_config.get("message", "").format(
                                    child_name=context.get("child_name", "הילד/ה")
                                )

                                # 🌟 Wu Wei: Include ui_context to prevent hallucinations
                                # This guides Chitta about actual UI elements (cards, buttons, modals, etc.)
                                event_data = {
                                    "event_name": event_name,
                                    "action": event_config.get("action"),
                                    "message": message
                                }

                                # Add ui_context if defined (for UI guidance)
                                ui_context = event_config.get("ui_context")
                                if ui_context:
                                    event_data["ui_context"] = ui_context
                                    logger.info(f"  📍 UI Context ({ui_context.get('type')}): {ui_context.get('default')[:50]}...")

                                events_triggered.append(event_data)
                                logger.info(f"🎉 Triggered lifecycle event: {event_name}")
                            else:
                                logger.warning(f"⚠️ Event '{event_name}' not found in lifecycle_events")

                    else:
                        logger.error(
                            f"❌ Wu Wei: Failed to generate {artifact_id}: "
                            f"{artifact.error_message if artifact else 'Unknown error'}"
                        )

                except Exception as e:
                    logger.error(
                        f"❌ Wu Wei: Exception generating {artifact_id}: {e}",
                        exc_info=True
                    )

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
                f"  - Events triggered: {events_triggered}\n"
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

            # Evaluate OR condition (it's a dict representing alternative prerequisites)
            if isinstance(or_condition, dict):
                or_met = self._evaluate_prerequisites(or_condition, context)
            else:
                # Fallback for unexpected structure
                or_met = False
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

    async def _generate_artifact(
        self,
        artifact_id: str,
        artifact_def: Dict[str, Any],
        context: Dict[str, Any]
    ):
        """
        Generate an artifact based on its ID and definition.

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


# Singleton instance
_lifecycle_manager: Optional[LifecycleManager] = None


def get_lifecycle_manager() -> LifecycleManager:
    """Get global LifecycleManager instance (singleton)."""
    global _lifecycle_manager
    if _lifecycle_manager is None:
        _lifecycle_manager = LifecycleManager()
    return _lifecycle_manager
