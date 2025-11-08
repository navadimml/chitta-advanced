"""
Prerequisite Service - Checks if actions are feasible based on current state

This service implements the "conversation over prerequisite graph" architecture:
- Maintains the dependency graph (what requires what)
- Checks current state against requirements
- Provides contextual explanations when actions aren't possible
- No stages - just dependencies and current capabilities

🌟 Wu Wei Architecture: Now uses action_registry for config-driven prerequisite checks!
"""

import logging
from typing import Dict, Any, Tuple, List, Optional
from dataclasses import dataclass

# Wu Wei Architecture: Import config-driven action registry
from app.config.action_registry import (
    get_action_registry,
    get_available_actions as config_get_available_actions,
    check_action_availability as config_check_availability
)

# Legacy imports for Action enum and Hebrew explanations
from ..prompts.prerequisites import (
    Action,
    PrerequisiteType,
    get_prerequisite_explanation,
)

logger = logging.getLogger(__name__)


@dataclass
class PrerequisiteCheckResult:
    """Result of checking if an action is feasible"""
    feasible: bool
    action: Action
    missing_prerequisites: List[PrerequisiteType]
    explanation_to_user: str  # Hebrew explanation
    enhanced_by: List[PrerequisiteType]  # Optional enhancements


class PrerequisiteService:
    """
    Service for checking action prerequisites against current state

    This is NOT a stage manager - it's a capability checker.
    Users can request anything; we check if it's technically possible.
    """

    def __init__(self):
        logger.info("PrerequisiteService initialized")

    def check_state(self, context: Dict[str, Any]) -> Dict[PrerequisiteType, bool]:
        """
        Check which prerequisites are currently met

        Args:
            context: Current interview/family state with:
                - completeness: float (0.0 to 1.0)
                - video_count: int
                - analysis_complete: bool
                - reports_available: bool

        Returns:
            Dict mapping each PrerequisiteType to True/False
        """
        completeness = context.get("completeness", 0.0)
        video_count = context.get("video_count", 0)
        analysis_complete = context.get("analysis_complete", False)
        reports_available = context.get("reports_available", False)

        state = {
            PrerequisiteType.INTERVIEW_COMPLETE: completeness >= 0.80,  # 80%+ = complete
            PrerequisiteType.VIDEOS_UPLOADED: video_count > 0,
            PrerequisiteType.MINIMUM_VIDEOS: video_count >= 3,
            PrerequisiteType.ANALYSIS_COMPLETE: analysis_complete,
            PrerequisiteType.REPORTS_AVAILABLE: reports_available,
        }

        logger.debug(f"Current state: {state}")
        return state

    def check_action_feasible(
        self,
        action: str,
        context: Dict[str, Any]
    ) -> PrerequisiteCheckResult:
        """
        Check if an action is currently feasible

        🌟 Wu Wei Architecture: Now uses action_registry for config-driven checks!

        Args:
            action: Action name (string)
            context: Current state dict

        Returns:
            PrerequisiteCheckResult with feasibility and explanation
        """
        # Convert string to Action enum
        try:
            action_enum = Action(action)
        except ValueError:
            logger.warning(f"Unknown action: {action}")
            return PrerequisiteCheckResult(
                feasible=False,
                action=action,
                missing_prerequisites=[],
                explanation_to_user=f"פעולה לא מוכרת: {action}",
                enhanced_by=[]
            )

        # Build context for action_registry
        # action_registry expects session object with attributes
        registry_context = self._build_registry_context(context)

        # Use action_registry for config-driven check
        availability = config_check_availability(action, registry_context)

        feasible = availability["available"]
        missing_prereq_ids = availability.get("missing_prerequisites", [])

        # Convert prerequisite IDs to PrerequisiteType enums for compatibility
        missing = self._convert_prerequisite_ids_to_enums(missing_prereq_ids)

        # Get enhanced_by from action definition
        action_def = get_action_registry().get_action(action)
        enhanced_by = []
        if action_def and action_def.enhanced_by:
            enhanced_by = self._convert_prerequisite_ids_to_enums(action_def.enhanced_by)

        # Get personalized Hebrew explanation if not feasible
        if not feasible:
            child_name = context.get("child_name", "הילד/ה")
            video_count = context.get("video_count", 0)
            completeness = context.get("completeness", 0.0)
            current_state = self.check_state(context)
            interview_complete = current_state.get(PrerequisiteType.INTERVIEW_COMPLETE, False)
            analysis_complete = current_state.get(PrerequisiteType.ANALYSIS_COMPLETE, False)

            # Use existing Hebrew explanation logic (from prerequisites.py)
            explanation = get_prerequisite_explanation(
                action_enum,
                child_name=child_name,
                video_count=video_count,
                required_videos=3,
                interview_complete=interview_complete,
                analysis_complete=analysis_complete,
                completeness=completeness
            )
        else:
            explanation = ""

        logger.info(
            f"Action '{action}' feasibility check: {feasible} "
            f"(missing: {missing if not feasible else 'none'}) "
            f"[config-driven via action_registry]"
        )

        return PrerequisiteCheckResult(
            feasible=feasible,
            action=action_enum,
            missing_prerequisites=missing,
            explanation_to_user=explanation,
            enhanced_by=enhanced_by
        )

    def get_available_actions(self, context: Dict[str, Any]) -> List[Action]:
        """
        Get list of actions that are currently available

        🌟 Wu Wei Architecture: Now uses action_registry for config-driven checks!

        Args:
            context: Current state

        Returns:
            List of Action enums that are feasible right now
        """
        # Build context for action_registry
        registry_context = self._build_registry_context(context)

        # Use config-driven available actions check
        available_action_ids = config_get_available_actions(registry_context)

        # Convert action IDs to Action enums
        available = []
        for action_id in available_action_ids:
            try:
                available.append(Action(action_id))
            except ValueError:
                logger.warning(f"Unknown action ID from config: {action_id}")

        logger.debug(
            f"Available actions: {[a.value for a in available]} "
            f"[config-driven via action_registry]"
        )
        return available

    def get_next_logical_step(self, context: Dict[str, Any]) -> Optional[Action]:
        """
        Suggest what user should do next based on current state

        This is for proactive guidance, not blocking.

        Args:
            context: Current state

        Returns:
            Suggested next action, or None if no clear next step
        """
        completeness = context.get("completeness", 0.0)
        video_count = context.get("video_count", 0)
        analysis_complete = context.get("analysis_complete", False)
        reports_available = context.get("reports_available", False)

        # Logic for next step
        if completeness < 0.80:
            return Action.CONTINUE_INTERVIEW

        elif video_count == 0:
            return Action.VIEW_VIDEO_GUIDELINES

        elif video_count < 3:
            return Action.UPLOAD_VIDEO

        elif not analysis_complete:
            # Waiting for analysis - suggest journal or consultation
            return Action.ADD_JOURNAL_ENTRY

        elif reports_available:
            return Action.VIEW_REPORT

        return None

    def build_prerequisite_context_for_prompt(
        self,
        context: Dict[str, Any]
    ) -> str:
        """
        Build a string describing current state for LLM prompt

        This tells the LLM what's currently possible so it can
        respond appropriately to user requests.

        Args:
            context: Current state

        Returns:
            String description for prompt
        """
        current_state = self.check_state(context)
        available_actions = self.get_available_actions(context)

        # Build human-readable description
        parts = ["## Current Capabilities\n"]

        parts.append("**User can currently:**")
        if available_actions:
            for action in available_actions:
                parts.append(f"- {action.value}")
        else:
            parts.append("- Continue interview")
            parts.append("- Ask questions (consultation)")
            parts.append("- Add journal entries")

        parts.append("\n**Current state:**")
        completeness = context.get("completeness", 0.0)
        parts.append(f"- Interview: {completeness:.0%} complete")

        if current_state[PrerequisiteType.INTERVIEW_COMPLETE]:
            parts.append("- ✅ Interview completed")
        else:
            parts.append(f"- ⏳ Interview in progress ({completeness:.0%})")

        video_count = context.get("video_count", 0)
        if video_count > 0:
            parts.append(f"- Videos: {video_count} uploaded")
        else:
            parts.append("- Videos: None yet")

        if current_state[PrerequisiteType.REPORTS_AVAILABLE]:
            parts.append("- ✅ Reports available")
        elif current_state[PrerequisiteType.ANALYSIS_COMPLETE]:
            parts.append("- ⏳ Analysis complete, generating reports")
        else:
            parts.append("- ⏳ Analysis pending")

        parts.append("\n**When responding to action requests:**")
        parts.append("- If action is available → facilitate it")
        parts.append("- If action is NOT available → explain warmly what's needed first")
        parts.append("- Use the explanations from prerequisites.py when appropriate")

        return "\n".join(parts)

    def _build_registry_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build context dict for action_registry from prerequisite service context.

        action_registry expects session object with attributes, but we can pass
        a dict with the same structure for prerequisite checking.

        Args:
            context: Prerequisite service context

        Returns:
            Context dict suitable for action_registry
        """
        # Create a mock session object structure for action_registry
        completeness = context.get("completeness", 0.0)
        video_count = context.get("video_count", 0)
        reports_ready = context.get("reports_available", False)

        # Build mock parent_report object with status attribute
        # action_graph.yaml checks: session.artifacts.parent_report.status == 'ready'
        parent_report = None
        if reports_ready:
            parent_report = type('obj', (object,), {
                "status": "ready"
            })()

        # Build session-like context
        return {
            "phase": context.get("phase", "screening"),
            "session": type('obj', (object,), {
                "completeness": completeness,
                "artifacts": type('obj', (object,), {
                    "parent_report": parent_report,
                    "videos": [{}] * video_count  # Mock video list
                })()
            })(),
            "completeness": completeness,
            "uploaded_video_count": video_count,
            "reports_ready": reports_ready,
        }

    def _convert_prerequisite_ids_to_enums(
        self,
        prerequisite_ids: List[str]
    ) -> List[PrerequisiteType]:
        """
        Convert prerequisite IDs from action_graph.yaml to PrerequisiteType enums.

        Maps config prerequisite names to Python enums for compatibility.

        Args:
            prerequisite_ids: List of prerequisite IDs from config

        Returns:
            List of PrerequisiteType enums
        """
        # Mapping from config IDs to PrerequisiteType enums
        id_to_enum = {
            "interview_complete": PrerequisiteType.INTERVIEW_COMPLETE,
            "videos_uploaded": PrerequisiteType.VIDEOS_UPLOADED,
            "minimum_videos": PrerequisiteType.MINIMUM_VIDEOS,
            "analysis_complete": PrerequisiteType.ANALYSIS_COMPLETE,
            "reports_available": PrerequisiteType.REPORTS_AVAILABLE,
        }

        result = []
        for prereq_id in prerequisite_ids:
            enum_val = id_to_enum.get(prereq_id)
            if enum_val:
                result.append(enum_val)
            else:
                logger.warning(f"Unknown prerequisite ID from config: {prereq_id}")

        return result


# Singleton instance
_prerequisite_service = None

def get_prerequisite_service() -> PrerequisiteService:
    """Get singleton PrerequisiteService instance"""
    global _prerequisite_service
    if _prerequisite_service is None:
        _prerequisite_service = PrerequisiteService()
    return _prerequisite_service
