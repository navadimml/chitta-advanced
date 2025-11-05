"""
Prerequisite Service - Checks if actions are feasible based on current state

This service implements the "conversation over prerequisite graph" architecture:
- Maintains the dependency graph (what requires what)
- Checks current state against requirements
- Provides contextual explanations when actions aren't possible
- No stages - just dependencies and current capabilities
"""

import logging
from typing import Dict, Any, Tuple, List, Optional
from dataclasses import dataclass

from ..prompts.prerequisites import (
    Action,
    PrerequisiteType,
    get_action_prerequisites,
    get_prerequisite_explanation,
    is_always_available,
    PREREQUISITES
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

        # Get what this action requires
        prereq_info = get_action_prerequisites(action_enum)
        required = prereq_info.get("requires", [])
        enhanced_by = prereq_info.get("enhanced_by", [])

        # Check current state
        current_state = self.check_state(context)

        # Check if all requirements are met
        missing = [req for req in required if not current_state.get(req, False)]

        feasible = len(missing) == 0

        # Get personalized explanation if not feasible
        if not feasible:
            child_name = context.get("child_name", "הילד/ה")
            video_count = context.get("video_count", 0)
            explanation = get_prerequisite_explanation(
                action_enum,
                child_name=child_name,
                video_count=video_count,
                required_videos=3
            )
        else:
            explanation = ""

        logger.info(
            f"Action '{action}' feasibility check: {feasible} "
            f"(missing: {missing if not feasible else 'none'})"
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

        Args:
            context: Current state

        Returns:
            List of Action enums that are feasible right now
        """
        current_state = self.check_state(context)
        available = []

        for action in Action:
            prereq_info = PREREQUISITES.get(action, {})
            required = prereq_info.get("requires", [])

            # Check if all requirements met
            if all(current_state.get(req, False) for req in required):
                available.append(action)

        logger.debug(f"Available actions: {[a.value for a in available]}")
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


# Singleton instance
_prerequisite_service = None

def get_prerequisite_service() -> PrerequisiteService:
    """Get singleton PrerequisiteService instance"""
    global _prerequisite_service
    if _prerequisite_service is None:
        _prerequisite_service = PrerequisiteService()
    return _prerequisite_service
