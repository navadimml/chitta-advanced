"""
Action registry for action graph and prerequisite management.

Provides access to the action graph defined in action_graph.yaml,
including action definitions, prerequisites, and availability checks.
"""

from typing import Dict, Any, List, Optional, Set
from pydantic import BaseModel
from enum import Enum
import logging

from app.config.config_loader import load_action_graph

logger = logging.getLogger(__name__)


class ActionDefinition(BaseModel):
    """Definition of a single action."""
    action_id: str
    description: str
    category: str
    requires: List[str] = []  # Prerequisite IDs
    enhanced_by: List[str] = []  # Optional prerequisites that enhance action
    phase: str  # "screening", "ongoing", "re_assessment", or "both"
    explanation_to_user: Optional[str] = None
    triggers_artifact: Optional[str] = None
    creates_artifact: Optional[str] = None
    opens_view: Optional[str] = None
    max_count: Optional[int] = None  # For upload_video etc.


class PrerequisiteCheck(BaseModel):
    """Definition of a prerequisite check."""
    prerequisite_id: str
    description: str
    check_expression: str  # Python expression to evaluate


class ActionRegistry:
    """
    Registry for action graph.

    Provides methods to check action availability, evaluate prerequisites,
    and get action definitions.
    """

    def __init__(self):
        """Initialize action registry."""
        self._action_config = load_action_graph()
        self._actions: Dict[str, ActionDefinition] = {}
        self._prerequisites: Dict[str, PrerequisiteCheck] = {}
        self._load_actions()
        self._load_prerequisites()

    def _load_actions(self) -> None:
        """Load action definitions from configuration."""
        actions_config = self._action_config.get("actions", {})

        for action_id, action_config in actions_config.items():
            try:
                self._actions[action_id] = ActionDefinition(
                    action_id=action_id,
                    **action_config
                )
            except Exception as e:
                logger.error(f"Error loading action {action_id}: {e}")
                raise

        logger.info(f"Loaded {len(self._actions)} action definitions")

    def _load_prerequisites(self) -> None:
        """Load prerequisite definitions from configuration."""
        prereq_config = self._action_config.get("prerequisite_types", {})

        for prereq_id, prereq_def in prereq_config.items():
            try:
                self._prerequisites[prereq_id] = PrerequisiteCheck(
                    prerequisite_id=prereq_id,
                    description=prereq_def.get("description", ""),
                    check_expression=prereq_def.get("check", "")
                )
            except Exception as e:
                logger.error(f"Error loading prerequisite {prereq_id}: {e}")
                raise

        logger.info(f"Loaded {len(self._prerequisites)} prerequisite checks")

    def get_action(self, action_id: str) -> Optional[ActionDefinition]:
        """
        Get action definition by ID.

        Args:
            action_id: Action identifier

        Returns:
            ActionDefinition or None if not found
        """
        return self._actions.get(action_id)

    def get_all_actions(self) -> Dict[str, ActionDefinition]:
        """
        Get all action definitions.

        Returns:
            Dictionary of action ID to ActionDefinition
        """
        return self._actions.copy()

    def get_actions_by_category(self, category: str) -> List[ActionDefinition]:
        """
        Get actions by category.

        Args:
            category: Category name (interview, video, reports, etc.)

        Returns:
            List of ActionDefinitions in that category
        """
        return [
            action for action in self._actions.values()
            if action.category == category
        ]

    def get_actions_by_phase(self, phase: str) -> List[ActionDefinition]:
        """
        Get actions available in a phase.

        Args:
            phase: Phase name (screening, ongoing, re_assessment)

        Returns:
            List of ActionDefinitions available in that phase
        """
        return [
            action for action in self._actions.values()
            if action.phase == phase or action.phase == "both"
        ]

    def check_prerequisite(
        self,
        prerequisite_id: str,
        context: Dict[str, Any]
    ) -> bool:
        """
        Check if a prerequisite is satisfied.

        Args:
            prerequisite_id: Prerequisite identifier
            context: Context dictionary with session state
                    (completeness, artifacts, phase, etc.)

        Returns:
            True if prerequisite satisfied, False otherwise
        """
        prereq = self._prerequisites.get(prerequisite_id)
        if not prereq:
            logger.warning(f"Unknown prerequisite: {prerequisite_id}")
            return False

        try:
            # Evaluate check expression
            # This is a simple eval - in production might want safer evaluation
            result = eval(prereq.check_expression, {"__builtins__": {}}, context)
            return bool(result)
        except Exception as e:
            logger.error(
                f"Error evaluating prerequisite {prerequisite_id}: {e}"
            )
            return False

    def check_action_availability(
        self,
        action_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check if an action is available in the current context.

        Args:
            action_id: Action identifier
            context: Context dictionary with session state

        Returns:
            Dictionary with:
            - available: bool
            - missing_prerequisites: List[str]
            - explanation: Optional[str]  # If not available
        """
        action = self.get_action(action_id)
        if not action:
            return {
                "available": False,
                "missing_prerequisites": [],
                "explanation": f"Unknown action: {action_id}"
            }

        # Check phase compatibility
        current_phase = context.get("phase", "screening")
        if action.phase not in [current_phase, "both"]:
            return {
                "available": False,
                "missing_prerequisites": [],
                "explanation": f"Action not available in {current_phase} phase"
            }

        # Check prerequisites
        missing = []
        for prereq_id in action.requires:
            if not self.check_prerequisite(prereq_id, context):
                missing.append(prereq_id)

        if missing:
            return {
                "available": False,
                "missing_prerequisites": missing,
                "explanation": action.explanation_to_user
            }

        # All checks passed
        return {
            "available": True,
            "missing_prerequisites": [],
            "explanation": None
        }

    def get_available_actions(
        self,
        context: Dict[str, Any]
    ) -> List[str]:
        """
        Get list of currently available action IDs.

        Args:
            context: Context dictionary with session state

        Returns:
            List of action IDs that are currently available
        """
        available = []

        for action_id in self._actions.keys():
            result = self.check_action_availability(action_id, context)
            if result["available"]:
                available.append(action_id)

        return available

    def get_blocked_actions_with_explanations(
        self,
        context: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Get blocked actions with user-facing explanations.

        Args:
            context: Context dictionary with session state

        Returns:
            Dictionary of action_id to explanation string
        """
        blocked = {}

        for action_id, action in self._actions.items():
            result = self.check_action_availability(action_id, context)
            if not result["available"] and result["explanation"]:
                blocked[action_id] = result["explanation"]

        return blocked

    def get_next_suggested_action(
        self,
        context: Dict[str, Any]
    ) -> Optional[str]:
        """
        Get suggested next action based on current state.

        This implements simple heuristics:
        - In screening: continue_interview if not complete
        - In screening: upload_video if interview complete but no videos
        - In screening: analyze_videos if videos uploaded
        - In ongoing: add_journal_entry if no recent entries
        - etc.

        Args:
            context: Context dictionary with session state

        Returns:
            Suggested action ID or None
        """
        phase = context.get("phase", "screening")
        completeness = context.get("completeness", 0.0)
        uploaded_videos = context.get("uploaded_video_count", 0)
        reports_ready = context.get("reports_ready", False)

        if phase == "screening":
            if completeness < 0.80:
                return "continue_interview"
            elif uploaded_videos < 3:
                return "upload_video"
            elif not reports_ready:
                return "analyze_videos"
            else:
                return "view_report"

        elif phase == "ongoing":
            if not reports_ready:
                return None  # Shouldn't be in ongoing without reports

            # Suggest journal if haven't added entry recently
            days_since_journal = context.get("days_since_last_journal_entry", 999)
            if days_since_journal > 7:
                return "add_journal_entry"

            return "consultation"  # Default to consultation

        elif phase == "re_assessment":
            if completeness < 0.60:  # Lower threshold
                return "continue_interview"
            elif uploaded_videos < 2:  # Fewer videos needed
                return "upload_video"
            else:
                return "analyze_videos"

        return None


# Global singleton instance
_action_registry: Optional[ActionRegistry] = None


def get_action_registry() -> ActionRegistry:
    """
    Get global ActionRegistry instance (singleton pattern).

    Returns:
        ActionRegistry instance
    """
    global _action_registry

    if _action_registry is None:
        _action_registry = ActionRegistry()

    return _action_registry


# Convenience functions
def get_action(action_id: str) -> Optional[ActionDefinition]:
    """Get action definition by ID."""
    return get_action_registry().get_action(action_id)


def check_action_availability(
    action_id: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Check if action is available."""
    return get_action_registry().check_action_availability(action_id, context)


def get_available_actions(context: Dict[str, Any]) -> List[str]:
    """Get list of available action IDs."""
    return get_action_registry().get_available_actions(context)
