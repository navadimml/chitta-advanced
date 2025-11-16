"""
Phase manager for workflow phase management and transitions.

Handles phase definitions, transitions, and phase-specific behavior
from phases.yaml configuration.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from enum import Enum
import logging

from app.config.config_loader import load_phases

logger = logging.getLogger(__name__)


class PhaseDefinition(BaseModel):
    """Definition of a workflow phase."""
    phase_id: str
    name: str
    name_en: str
    description: str
    focus: str
    duration_estimate: str
    order: int
    extraction_priority: str  # high, medium, low
    completeness_threshold: Optional[float]
    conversation_mode: str  # interview, consultation
    available_actions: List[str]
    goals: List[str]
    produces_artifacts: List[str]
    transitions_to: str
    transition_trigger: Dict[str, Any]
    ui_focus: str
    show_completeness_percentage: bool


class PhaseTransition(BaseModel):
    """Definition of a phase transition."""
    transition_id: str
    from_phase: str
    to_phase: str
    trigger: str
    actions_on_transition: List[str]
    message_to_user: str


class PhaseManager:
    """
    Manager for workflow phases.

    Handles:
    - Phase definitions
    - Phase transitions
    - Phase-specific behavior
    - Transition triggers
    """

    def __init__(self):
        """Initialize phase manager."""
        self._phase_config = load_phases()
        self._phases: Dict[str, PhaseDefinition] = {}
        self._transitions: Dict[str, PhaseTransition] = {}
        self._initial_phase: str = ""
        self._load_phases()
        self._load_transitions()

    def _load_phases(self) -> None:
        """Load phase definitions from configuration."""
        phases_config = self._phase_config.get("phases", {})

        for phase_id, phase_config in phases_config.items():
            try:
                self._phases[phase_id] = PhaseDefinition(
                    phase_id=phase_id,
                    **phase_config
                )
            except Exception as e:
                logger.error(f"Error loading phase {phase_id}: {e}")
                raise

        self._initial_phase = self._phase_config.get("initial_phase", "screening")

        logger.info(f"Loaded {len(self._phases)} phase definitions")

    def _load_transitions(self) -> None:
        """Load transition definitions from configuration."""
        transitions_config = self._phase_config.get("transition_events", {})

        for transition_id, transition_config in transitions_config.items():
            try:
                self._transitions[transition_id] = PhaseTransition(
                    transition_id=transition_id,
                    from_phase=transition_config.get("from"),
                    to_phase=transition_config.get("to"),
                    trigger=transition_config.get("trigger"),
                    actions_on_transition=transition_config.get(
                        "actions_on_transition",
                        []
                    ),
                    message_to_user=transition_config.get("message_to_user", "")
                )
            except Exception as e:
                logger.error(f"Error loading transition {transition_id}: {e}")
                raise

        logger.info(f"Loaded {len(self._transitions)} transition definitions")

    def get_phase(self, phase_id: str) -> Optional[PhaseDefinition]:
        """
        Get phase definition by ID.

        Args:
            phase_id: Phase identifier

        Returns:
            PhaseDefinition or None if not found
        """
        return self._phases.get(phase_id)

    def get_all_phases(self) -> Dict[str, PhaseDefinition]:
        """
        Get all phase definitions.

        Returns:
            Dictionary of phase ID to PhaseDefinition
        """
        return self._phases.copy()

    def get_initial_phase(self) -> str:
        """
        Get initial phase ID.

        Returns:
            Initial phase identifier
        """
        return self._initial_phase

    def get_phase_order(self, phase_id: str) -> int:
        """
        Get order/sequence number of a phase.

        Args:
            phase_id: Phase identifier

        Returns:
            Order number (1, 2, 3, etc.)
        """
        phase = self.get_phase(phase_id)
        return phase.order if phase else 0

    def check_transition_trigger(
        self,
        current_phase: str,
        context: Dict[str, Any]
    ) -> Optional[PhaseTransition]:
        """
        Check if a phase transition should occur.

        Args:
            current_phase: Current phase ID
            context: Context dictionary with session state

        Returns:
            PhaseTransition if transition should occur, None otherwise
        """
        # Find transitions from current phase
        possible_transitions = [
            t for t in self._transitions.values()
            if t.from_phase == current_phase
        ]

        for transition in possible_transitions:
            if self._evaluate_trigger(transition.trigger, context):
                return transition

        return None

    def _evaluate_trigger(
        self,
        trigger: str,
        context: Dict[str, Any]
    ) -> bool:
        """
        Evaluate if a transition trigger is satisfied.

        Args:
            trigger: Trigger identifier
            context: Context dictionary

        Returns:
            True if trigger satisfied
        """
        # Map trigger names to conditions
        triggers = {
            "reports_generated": lambda c: c.get("reports_ready", False),
            "user_requests_re_assessment": lambda c: c.get(
                "user_requested_re_assessment",
                False
            ),
            "re_assessment_complete": lambda c: c.get(
                "updated_reports_ready",
                False
            )
        }

        trigger_fn = triggers.get(trigger)
        if trigger_fn:
            try:
                return trigger_fn(context)
            except Exception as e:
                logger.error(f"Error evaluating trigger {trigger}: {e}")
                return False

        logger.warning(f"Unknown trigger: {trigger}")
        return False

    def get_transition_message(
        self,
        transition: PhaseTransition,
        context: Dict[str, Any]
    ) -> str:
        """
        Get transition message with variable substitution.

        Args:
            transition: PhaseTransition
            context: Context with variables

        Returns:
            Formatted message
        """
        message = transition.message_to_user

        # Replace {child_name} and other variables
        child_name = context.get("child_name", "")
        message = message.replace("{child_name}", child_name)

        return message

    def get_available_actions_for_phase(
        self,
        phase_id: str
    ) -> List[str]:
        """
        Get actions available in a phase.

        Args:
            phase_id: Phase identifier

        Returns:
            List of action IDs available in this phase
        """
        phase = self.get_phase(phase_id)
        return phase.available_actions if phase else []

    def get_completeness_threshold(self, phase_id: str) -> Optional[float]:
        """
        Get completeness threshold for a phase.

        Args:
            phase_id: Phase identifier

        Returns:
            Completeness threshold or None if not applicable
        """
        phase = self.get_phase(phase_id)
        return phase.completeness_threshold if phase else None

    def get_conversation_mode(self, phase_id: str) -> str:
        """
        Get conversation mode for a phase.

        Args:
            phase_id: Phase identifier

        Returns:
            Conversation mode (interview, consultation)
        """
        phase = self.get_phase(phase_id)
        return phase.conversation_mode if phase else "consultation"

    def should_show_completeness(self, phase_id: str) -> bool:
        """
        Check if completeness percentage should be shown in this phase.

        Args:
            phase_id: Phase identifier

        Returns:
            True if should show completeness
        """
        phase = self.get_phase(phase_id)
        return phase.show_completeness_percentage if phase else False

    def get_phase_goals(self, phase_id: str) -> List[str]:
        """
        Get goals for a phase.

        Args:
            phase_id: Phase identifier

        Returns:
            List of goal descriptions
        """
        phase = self.get_phase(phase_id)
        return phase.goals if phase else []

    def get_expected_artifacts(self, phase_id: str) -> List[str]:
        """
        Get artifacts that should be produced in a phase.

        Args:
            phase_id: Phase identifier

        Returns:
            List of artifact IDs
        """
        phase = self.get_phase(phase_id)
        return phase.produces_artifacts if phase else []


# Global singleton instance
_phase_manager: Optional[PhaseManager] = None


def get_phase_manager() -> PhaseManager:
    """
    Get global PhaseManager instance (singleton pattern).

    Returns:
        PhaseManager instance
    """
    global _phase_manager

    if _phase_manager is None:
        _phase_manager = PhaseManager()

    return _phase_manager


# Convenience functions
def get_phase(phase_id: str) -> Optional[PhaseDefinition]:
    """Get phase definition by ID."""
    return get_phase_manager().get_phase(phase_id)


def get_initial_phase() -> str:
    """Get initial phase ID."""
    return get_phase_manager().get_initial_phase()


def check_phase_transition(
    current_phase: str,
    context: Dict[str, Any]
) -> Optional[PhaseTransition]:
    """Check if phase transition should occur."""
    return get_phase_manager().check_transition_trigger(current_phase, context)


def get_completeness_threshold(phase_id: str) -> Optional[float]:
    """Get completeness threshold for phase."""
    return get_phase_manager().get_completeness_threshold(phase_id)


def get_conversation_mode(phase_id: str) -> str:
    """Get conversation mode for phase."""
    return get_phase_manager().get_conversation_mode(phase_id)
