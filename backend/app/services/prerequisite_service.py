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

logger = logging.getLogger(__name__)


@dataclass
class PrerequisiteCheckResult:
    """Result of checking if an action is feasible"""
    feasible: bool
    action: str  # Wu Wei: String action ID, not enum
    missing_prerequisites: List[str]  # Wu Wei: String prerequisite IDs, not enums
    explanation_to_user: str  # Hebrew explanation
    enhanced_by: List[str]  # Wu Wei: String prerequisite IDs, not enums


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
        conversation_history = session_data.get("conversation_history", [])

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
        # 🌟 Wu Wei: Map extraction fields to context format for prerequisite evaluation
        # other_info should combine family_context + daily_routines (from extraction schema)
        family_context = extracted_data.get("family_context") or ""
        daily_routines = extracted_data.get("daily_routines") or ""
        other_info_combined = f"{family_context}\n{daily_routines}".strip()

        context = {
            # Extracted data fields
            "child_name": extracted_data.get("child_name"),
            "age": extracted_data.get("age") or extracted_data.get("child_age"),
            "primary_concerns": extracted_data.get("primary_concerns"),
            "concerns": extracted_data.get("concerns"),
            # Map concern_details (from extraction schema) to concern_description (expected by evaluator)
            "concern_description": extracted_data.get("concern_details") or extracted_data.get("concern_description"),
            "strengths": extracted_data.get("strengths"),
            "other_info": other_info_combined or extracted_data.get("other_info"),  # Fallback to old field if exists
            "filming_preference": extracted_data.get("filming_preference"),  # 🎬 For filming decision flow

            # Conversation state
            "message_count": message_count,
            "conversation_history": conversation_history,  # For artifact generation

            # Artifacts (for prerequisite checking)
            "artifacts": artifacts,

            # Flags
            "re_assessment": {
                "active": re_assessment_active
            },

            # Video counts
            "uploaded_video_count": session_data.get("uploaded_video_count", 0),
            "guideline_scenario_count": session_data.get("guideline_scenario_count"),  # Number of scenarios in guidelines

            # User actions tracking
            "user_actions": {
                "viewed_guidelines": session_data.get("viewed_guidelines", False),
                "declined_guidelines_offer": session_data.get("declined_guidelines_offer", False),
                "declined_video_recording": session_data.get("declined_video_recording", False),
            },

            # Report status
            "reports_status": "ready" if session_data.get("parent_report_id") else "pending",

            # Video analysis status
            "video_analysis_status": session_data.get("video_analysis_status", "pending"),

            # Derived boolean for lifecycle event checking
            # videos_analyzed: true when video_analysis_status == "complete"
            "videos_analyzed": session_data.get("video_analysis_status") == "complete",

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

    def check_action_feasible(
        self,
        action: str,
        context: Dict[str, Any]
    ) -> PrerequisiteCheckResult:
        """
        Check if an action is currently feasible

        🌟 Wu Wei Architecture: Config-driven via action_registry!

        Args:
            action: Action ID (string, e.g., "view_video_guidelines")
            context: Current state dict

        Returns:
            PrerequisiteCheckResult with feasibility and explanation
        """
        # Build context for action_registry
        registry_context = self._build_registry_context(context)

        # Use action_registry for config-driven check
        availability = config_check_availability(action, registry_context)

        feasible = availability["available"]
        missing_prereq_ids = availability.get("missing_prerequisites", [])

        # Get enhanced_by from action definition
        action_def = get_action_registry().get_action(action)
        enhanced_by = action_def.enhanced_by if action_def else []

        # Wu Wei: Get explanation directly from action_graph.yaml
        explanation = availability.get("explanation") or ""

        # Personalize explanation with child_name if available
        if explanation and "{child_name}" in explanation:
            child_name = context.get("child_name") or "הילד/ה"  # Ensure default is used if None
            explanation = explanation.replace("{child_name}", child_name)

        logger.info(
            f"Action '{action}' feasibility check: {feasible} "
            f"(missing: {missing_prereq_ids if not feasible else 'none'}) "
            f"[config-driven via action_registry]"
        )

        return PrerequisiteCheckResult(
            feasible=feasible,
            action=action,
            missing_prerequisites=missing_prereq_ids,
            explanation_to_user=explanation,
            enhanced_by=enhanced_by
        )

    def get_available_actions(self, context: Dict[str, Any]) -> List[str]:
        """
        Get list of actions that are currently available

        🌟 Wu Wei Architecture: Config-driven via action_registry!

        Args:
            context: Current state

        Returns:
            List of action IDs (strings) that are feasible right now
        """
        # Build context for action_registry
        registry_context = self._build_registry_context(context)

        # Use config-driven available actions check
        available_action_ids = config_get_available_actions(registry_context)

        logger.debug(
            f"Available actions: {available_action_ids} "
            f"[config-driven via action_registry]"
        )
        return available_action_ids

    def get_next_logical_step(self, context: Dict[str, Any]) -> Optional[str]:
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

        # DEPRECATED: Hardcoded logic, violates Wu Wei - consider removing
        # Logic for next step
        if completeness < 0.80:
            return "continue_interview"

        elif video_count == 0:
            return "view_video_guidelines"

        elif video_count < 3:
            return "upload_video"

        elif not analysis_complete:
            # Waiting for analysis - suggest journal or consultation
            return "add_journal_entry"

        elif reports_available:
            return "view_report"

        return None

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

# Singleton instance
_prerequisite_service = None

def get_prerequisite_service() -> PrerequisiteService:
    """Get singleton PrerequisiteService instance"""
    global _prerequisite_service
    if _prerequisite_service is None:
        _prerequisite_service = PrerequisiteService()
    return _prerequisite_service
