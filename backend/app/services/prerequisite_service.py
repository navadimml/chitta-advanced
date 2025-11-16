"""
Prerequisite Service - Checks if actions are feasible based on current state

This service implements the "conversation over prerequisite graph" architecture:
- Maintains the dependency graph (what requires what)
- Checks current state against requirements
- Provides contextual explanations when actions aren't possible
- No stages - just dependencies and current capabilities

🌟 Wu Wei Architecture: Now uses pure dependency graph evaluation!
"""

import logging
from typing import Dict, Any, Tuple, List, Optional
from dataclasses import dataclass

# 🌟 Wu Wei: Import pure dependency graph evaluator
from app.services.wu_wei_prerequisites import (
    get_wu_wei_prerequisites,
    PrerequisiteEvaluation
)

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
        self.wu_wei = get_wu_wei_prerequisites()
        logger.info("PrerequisiteService initialized with Wu Wei dependency graph")

    # ========================================
    # 🌟 Wu Wei Methods (Pure Dependency Graph)
    # ========================================

    def check_knowledge_richness(self, context: Dict[str, Any]) -> PrerequisiteEvaluation:
        """
        🌟 Wu Wei: Check if knowledge is rich enough for guidelines generation

        This is a QUALITATIVE check, not quantitative (no "completeness >= 80%")

        Args:
            context: Session context with extracted data

        Returns:
            PrerequisiteEvaluation with met=True/False
        """
        return self.wu_wei.evaluate_knowledge_richness(context)

    def check_artifact_prerequisites(
        self,
        prerequisites: Dict[str, Any],
        context: Dict[str, Any]
    ) -> PrerequisiteEvaluation:
        """
        🌟 Wu Wei: Check if prerequisites from lifecycle_events.yaml are met

        Supports all prerequisite types:
        - knowledge_is_rich: true
        - baseline_parent_report.exists: false
        - artifacts.video_guidelines.status: "ready"
        - uploaded_video_count: ">= 3"
        - OR/AND logic

        Args:
            prerequisites: Prerequisites dict from lifecycle_events.yaml
            context: Session context

        Returns:
            PrerequisiteEvaluation combining all checks
        """
        return self.wu_wei.evaluate_prerequisites(prerequisites, context)

    def check_capability_available(
        self,
        capability_name: str,
        capability_prerequisites: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        🌟 Wu Wei: Check if a capability is currently available

        Args:
            capability_name: Capability name from lifecycle_events.yaml
            capability_prerequisites: Prerequisites dict for this capability
            context: Session context

        Returns:
            Tuple of (available, missing_prerequisites)
        """
        if not capability_prerequisites:
            # No prerequisites = always available
            return (True, [])

        result = self.check_artifact_prerequisites(capability_prerequisites, context)

        logger.info(
            f"Capability '{capability_name}' check: "
            f"available={result.met}, missing={result.missing}"
        )

        return (result.met, result.missing)

    def get_context_for_cards(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        🌟 Wu Wei: Build context dict for card_generator to evaluate display_conditions

        This transforms session data into the format that cards expect for
        checking prerequisites like "baseline_parent_report.exists: false"

        Args:
            session_data: Raw session data from database

        Returns:
            Context dict with artifacts, flags, and extracted data
        """
        # Extract core info
        extracted_data = session_data.get("extracted_data", {})
        message_count = session_data.get("message_count", 0)

        # Build artifacts structure from session
        artifacts = {}

        # 🌟 Wu Wei: Check actual artifact objects from session
        session_artifacts = session_data.get("artifacts", {})

        # Build artifact references for card evaluation
        for artifact_id, artifact_obj in session_artifacts.items():
            if hasattr(artifact_obj, 'exists'):
                # It's an Artifact object
                artifacts[artifact_id] = {
                    "exists": artifact_obj.exists,
                    "status": artifact_obj.status,
                    "artifact_id": artifact_obj.artifact_id
                }
            elif isinstance(artifact_obj, dict):
                # It's already a dict reference
                artifacts[artifact_id] = artifact_obj

        # DEPRECATED: Backwards compatibility - check old field names
        if session_data.get("parent_report_id") and "baseline_parent_report" not in artifacts:
            artifacts["baseline_parent_report"] = {
                "exists": True,
                "status": "ready",
                "artifact_id": session_data.get("parent_report_id")
            }

        if session_data.get("video_guidelines") and "baseline_video_guidelines" not in artifacts:
            artifacts["baseline_video_guidelines"] = {
                "exists": True,
                "status": session_data.get("video_guidelines_status", "ready"),
                "content": session_data.get("video_guidelines")
            }

        # Build flags
        re_assessment_active = session_data.get("re_assessment_active", False)

        # Build comprehensive context
        context = {
            # Extracted data fields
            "child_name": extracted_data.get("child_name"),
            "age": extracted_data.get("age") or extracted_data.get("child_age"),
            "primary_concerns": extracted_data.get("primary_concerns"),
            "concerns": extracted_data.get("concerns"),
            "concern_description": extracted_data.get("concern_description"),
            "strengths": extracted_data.get("strengths"),
            "other_info": extracted_data.get("other_info"),

            # Conversation state
            "message_count": message_count,

            # Artifacts (for prerequisite checking)
            "artifacts": artifacts,

            # Flags
            "re_assessment": {
                "active": re_assessment_active
            },

            # Video counts
            "uploaded_video_count": session_data.get("uploaded_video_count", 0),

            # User actions tracking
            "user_actions": {
                "viewed_guidelines": session_data.get("viewed_guidelines", False),
                "declined_guidelines_offer": session_data.get("declined_guidelines_offer", False),
            },

            # Report status
            "reports_status": "ready" if session_data.get("parent_report_id") else "pending",

            # Video analysis status
            "video_analysis_status": session_data.get("video_analysis_status", "pending"),

            # DEPRECATED: Phase (for backwards compatibility)
            "phase": self._infer_emergent_state(session_data),
        }

        # Add knowledge depth indicator using Wu Wei evaluator
        logger.info(f"🔍 PrerequisiteService: Evaluating knowledge richness for context building...")
        knowledge_eval = self.check_knowledge_richness(context)
        context["knowledge_is_rich"] = knowledge_eval.met
        logger.info(f"🔍 PrerequisiteService: knowledge_is_rich = {knowledge_eval.met}")
        logger.info(f"🔍 PrerequisiteService: Context built with {len(context)} keys")

        return context

    def _infer_emergent_state(self, session_data: Dict[str, Any]) -> str:
        """
        🌟 Wu Wei: Infer emergent state from artifacts (for backwards compatibility)

        States are NOT enforced - they're just detected based on what exists.

        Returns:
            "screening" | "ongoing" | "re_assessment" (legacy phase names)
        """
        has_baseline_report = bool(session_data.get("parent_report_id"))
        re_assessment_active = session_data.get("re_assessment_active", False)

        if re_assessment_active:
            return "re_assessment"
        elif has_baseline_report:
            return "ongoing"
        else:
            return "screening"

    # ========================================
    # DEPRECATED Methods (Backwards Compatibility)
    # ========================================
    # These methods use the OLD phase-based, completeness-threshold logic.
    # They're kept for backwards compatibility but should NOT be used in new code.
    # Use Wu Wei methods above instead.

    def check_state(self, context: Dict[str, Any]) -> Dict[PrerequisiteType, bool]:
        """
        DEPRECATED: Check which prerequisites are currently met (old completeness-based logic)

        🌟 Wu Wei Alternative: Use check_knowledge_richness() or check_artifact_prerequisites()

        Args:
            context: Current interview/family state with:
                - completeness: float (0.0 to 1.0)  # DEPRECATED
                - video_count: int
                - analysis_complete: bool
                - reports_available: bool

        Returns:
            Dict mapping each PrerequisiteType to True/False
        """
        logger.warning(
            "check_state() is DEPRECATED - uses completeness thresholds. "
            "Use Wu Wei methods (check_knowledge_richness, check_artifact_prerequisites) instead."
        )

        completeness = context.get("completeness", 0.0)
        video_count = context.get("video_count", 0)
        analysis_complete = context.get("analysis_complete", False)
        reports_available = context.get("reports_available", False)

        state = {
            PrerequisiteType.INTERVIEW_COMPLETE: completeness >= 0.80,  # DEPRECATED: Quantitative threshold
            PrerequisiteType.VIDEOS_UPLOADED: video_count > 0,
            PrerequisiteType.MINIMUM_VIDEOS: video_count >= 3,
            PrerequisiteType.ANALYSIS_COMPLETE: analysis_complete,
            PrerequisiteType.REPORTS_AVAILABLE: reports_available,
        }

        logger.debug(f"[DEPRECATED] Current state: {state}")
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
