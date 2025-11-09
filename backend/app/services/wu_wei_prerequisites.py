"""
Wu Wei Prerequisites Evaluator - Implements pure dependency graph logic

🌟 Wu Wei Architecture:
- No phases, no completeness thresholds
- Just: What exists? What's ready? Prerequisites met?
- Qualitative checks (knowledge_is_rich) not quantitative (>= 80%)
- Continuous conversation, capabilities unlock naturally

This service implements the prerequisite evaluation logic from lifecycle_events.yaml
"""

import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PrerequisiteEvaluation:
    """Result of evaluating prerequisites"""
    met: bool
    missing: List[str]  # List of missing prerequisite names
    details: Dict[str, Any]  # Detailed breakdown for debugging


class WuWeiPrerequisites:
    """
    Wu Wei prerequisite evaluator

    Implements qualitative, artifact-based prerequisite checks
    from lifecycle_events.yaml dependency graph.
    """

    def __init__(self):
        """Initialize Wu Wei prerequisite evaluator"""
        logger.info("WuWeiPrerequisites initialized - pure dependency graph mode")

    def evaluate_knowledge_richness(self, context: Dict[str, Any]) -> PrerequisiteEvaluation:
        """
        🌟 Wu Wei: Qualitative check - Is knowledge rich enough for guidelines?

        Returns true if conversation has accumulated enough understanding.
        This is NOT a percentage check - it's qualitative assessment.

        Criteria (from lifecycle_events.yaml):
        - Has child basic info (name, age)
        - Has at least 2 concerns OR developmental history
        - Has at least 2 strengths
        - Has some contextual info (family, environment)
        OR:
        - Message count > 15 AND has concerns AND has strengths

        Args:
            context: Session context with extracted data

        Returns:
            PrerequisiteEvaluation with met=True/False
        """
        # Extract what we know
        has_child_name = bool(context.get("child_name"))
        has_age = bool(context.get("age") or context.get("child_age"))

        # Concerns (can be in different fields depending on extraction schema)
        concerns = context.get("primary_concerns") or context.get("concerns") or []
        if isinstance(concerns, str):
            concerns = [concerns]
        has_concerns = len(concerns) >= 2

        # Check for developmental history in concern_description
        concern_description = context.get("concern_description") or ""
        has_developmental_history = len(concern_description) > 50  # Has substantial concern details

        # Strengths
        strengths = context.get("strengths") or []
        if isinstance(strengths, str):
            strengths = [strengths]
        has_strengths = len(strengths) >= 2

        # Contextual info
        other_info = context.get("other_info") or ""
        has_context = len(other_info) > 30  # Has some context

        # Message count
        message_count = context.get("message_count", 0)

        # Evaluate using Wu Wei qualitative criteria
        # Path 1: Rich structured knowledge
        path_1_met = (
            has_child_name and
            has_age and
            (has_concerns or has_developmental_history) and
            has_strengths and
            has_context
        )

        # Path 2: Extensive conversation (fallback)
        path_2_met = (
            message_count > 15 and
            (has_concerns or has_developmental_history) and
            has_strengths
        )

        met = path_1_met or path_2_met

        # Build details for debugging
        details = {
            "has_child_name": has_child_name,
            "has_age": has_age,
            "concerns_count": len(concerns),
            "has_developmental_history": has_developmental_history,
            "strengths_count": len(strengths),
            "has_context": has_context,
            "message_count": message_count,
            "path_1_met": path_1_met,
            "path_2_met": path_2_met,
        }

        missing = []
        if not met:
            if not has_child_name:
                missing.append("child_name")
            if not has_age:
                missing.append("age")
            if not (has_concerns or has_developmental_history):
                missing.append("concerns_or_history")
            if not has_strengths:
                missing.append("strengths")
            if not has_context and message_count <= 15:
                missing.append("contextual_info_or_more_conversation")

        logger.info(
            f"Knowledge richness evaluation: {met} "
            f"(path1={path_1_met}, path2={path_2_met}, "
            f"concerns={len(concerns)}, strengths={len(strengths)}, "
            f"messages={message_count})"
        )

        return PrerequisiteEvaluation(
            met=met,
            missing=missing,
            details=details
        )

    def check_artifact_exists(
        self,
        artifact_name: str,
        context: Dict[str, Any]
    ) -> PrerequisiteEvaluation:
        """
        Check if an artifact exists.

        Supports dotted notation: "baseline_parent_report.exists"

        Args:
            artifact_name: Name like "baseline_parent_report" or "baseline_parent_report.exists"
            context: Session context

        Returns:
            PrerequisiteEvaluation
        """
        # Handle dotted notation
        if ".exists" in artifact_name:
            artifact_name = artifact_name.replace(".exists", "")

        # Check in artifacts dict
        artifacts = context.get("artifacts", {})

        # Support nested access
        exists = False
        if "." in artifact_name:
            # e.g., "artifacts.video_guidelines.status"
            parts = artifact_name.split(".")
            value = artifacts
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                    if value is None:
                        break
                else:
                    value = None
                    break
            exists = value is not None
        else:
            # Simple check: does artifact exist in artifacts dict?
            artifact = artifacts.get(artifact_name)
            exists = artifact is not None and artifact.get("status") != "error"

        missing = [] if exists else [artifact_name]

        return PrerequisiteEvaluation(
            met=exists,
            missing=missing,
            details={"artifact_name": artifact_name, "exists": exists}
        )

    def check_artifact_status(
        self,
        artifact_name: str,
        expected_status: str,
        context: Dict[str, Any]
    ) -> PrerequisiteEvaluation:
        """
        Check if artifact has specific status.

        Args:
            artifact_name: Artifact name
            expected_status: Expected status (e.g., "ready", "generating")
            context: Session context

        Returns:
            PrerequisiteEvaluation
        """
        artifacts = context.get("artifacts", {})
        artifact = artifacts.get(artifact_name, {})
        actual_status = artifact.get("status")

        met = actual_status == expected_status
        missing = [] if met else [f"{artifact_name}.status={expected_status}"]

        return PrerequisiteEvaluation(
            met=met,
            missing=missing,
            details={
                "artifact_name": artifact_name,
                "expected_status": expected_status,
                "actual_status": actual_status
            }
        )

    def check_flag(
        self,
        flag_name: str,
        expected_value: bool,
        context: Dict[str, Any]
    ) -> PrerequisiteEvaluation:
        """
        Check if a flag has expected value.

        Supports dotted notation: "re_assessment.active"

        Args:
            flag_name: Flag name (e.g., "re_assessment.active")
            expected_value: Expected boolean value
            context: Session context

        Returns:
            PrerequisiteEvaluation
        """
        # Handle dotted notation
        if "." in flag_name:
            parts = flag_name.split(".")
            value = context
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                    if value is None:
                        break
                else:
                    value = None
                    break
            actual_value = bool(value)
        else:
            actual_value = bool(context.get(flag_name, False))

        met = actual_value == expected_value
        missing = [] if met else [f"{flag_name}={expected_value}"]

        return PrerequisiteEvaluation(
            met=met,
            missing=missing,
            details={
                "flag_name": flag_name,
                "expected_value": expected_value,
                "actual_value": actual_value
            }
        )

    def evaluate_prerequisites(
        self,
        prerequisites: Dict[str, Any],
        context: Dict[str, Any]
    ) -> PrerequisiteEvaluation:
        """
        Evaluate a prerequisites dict from lifecycle_events.yaml

        Supports:
        - knowledge_is_rich: true
        - baseline_parent_report.exists: false
        - artifacts.video_guidelines.status: "ready"
        - re_assessment.active: true
        - uploaded_video_count: ">= 3"
        - OR/AND logic

        Args:
            prerequisites: Prerequisites dict from lifecycle_events.yaml
            context: Session context

        Returns:
            PrerequisiteEvaluation combining all checks
        """
        if not prerequisites:
            # No prerequisites = always available
            return PrerequisiteEvaluation(met=True, missing=[], details={})

        # Handle OR logic
        if "OR" in prerequisites:
            or_conditions = prerequisites["OR"]
            for condition in or_conditions:
                result = self.evaluate_prerequisites(condition, context)
                if result.met:
                    return PrerequisiteEvaluation(
                        met=True,
                        missing=[],
                        details={"matched_or_branch": result.details}
                    )
            # None matched
            return PrerequisiteEvaluation(
                met=False,
                missing=["one_of_or_conditions"],
                details={"or_conditions_all_failed": True}
            )

        # Default: AND logic (all must be met)
        all_met = True
        all_missing = []
        all_details = {}

        for key, value in prerequisites.items():
            # Special qualitative check
            if key == "knowledge_is_rich" and value is True:
                result = self.evaluate_knowledge_richness(context)
                all_details["knowledge_is_rich"] = result.details
                if not result.met:
                    all_met = False
                    all_missing.extend(result.missing)

            # Artifact existence check
            elif ".exists" in key:
                artifact_name = key.replace(".exists", "")
                expected_exists = bool(value)
                result = self.check_artifact_exists(artifact_name, context)
                # Invert if checking for "exists: false"
                if not expected_exists:
                    result.met = not result.met
                all_details[key] = result.details
                if not result.met:
                    all_met = False
                    all_missing.extend(result.missing)

            # Artifact status check
            elif ".status" in key:
                artifact_name = key.split(".status")[0]
                expected_status = value
                result = self.check_artifact_status(artifact_name, expected_status, context)
                all_details[key] = result.details
                if not result.met:
                    all_met = False
                    all_missing.extend(result.missing)

            # Flag check (re_assessment.active, etc.)
            elif ".active" in key or isinstance(value, bool):
                result = self.check_flag(key, bool(value), context)
                all_details[key] = result.details
                if not result.met:
                    all_met = False
                    all_missing.extend(result.missing)

            # Numeric comparison check
            elif isinstance(value, str) and any(op in value for op in [">=", "<=", ">", "<", "!="]):
                result = self._evaluate_numeric_condition(key, value, context)
                all_details[key] = result.details
                if not result.met:
                    all_met = False
                    all_missing.extend(result.missing)

            # Direct value check
            else:
                actual_value = context.get(key)
                met = actual_value == value
                all_details[key] = {"expected": value, "actual": actual_value}
                if not met:
                    all_met = False
                    all_missing.append(f"{key}={value}")

        return PrerequisiteEvaluation(
            met=all_met,
            missing=all_missing,
            details=all_details
        )

    def _evaluate_numeric_condition(
        self,
        key: str,
        condition: str,
        context: Dict[str, Any]
    ) -> PrerequisiteEvaluation:
        """
        Evaluate numeric condition like ">= 3" or "< 0.80"

        Args:
            key: Context key to check
            condition: Condition string like ">= 3"
            context: Session context

        Returns:
            PrerequisiteEvaluation
        """
        actual_value = context.get(key, 0)

        try:
            condition = condition.strip()

            if condition.startswith(">="):
                threshold = float(condition[2:].strip())
                met = float(actual_value) >= threshold
            elif condition.startswith("<="):
                threshold = float(condition[2:].strip())
                met = float(actual_value) <= threshold
            elif condition.startswith(">"):
                threshold = float(condition[1:].strip())
                met = float(actual_value) > threshold
            elif condition.startswith("<"):
                threshold = float(condition[1:].strip())
                met = float(actual_value) < threshold
            elif condition.startswith("!="):
                expected = condition[2:].strip()
                met = str(actual_value) != expected
            else:
                met = False

        except (ValueError, TypeError):
            met = False

        missing = [] if met else [f"{key} {condition}"]

        return PrerequisiteEvaluation(
            met=met,
            missing=missing,
            details={
                "key": key,
                "condition": condition,
                "actual_value": actual_value
            }
        )


# Singleton
_wu_wei_prerequisites: Optional[WuWeiPrerequisites] = None


def get_wu_wei_prerequisites() -> WuWeiPrerequisites:
    """Get singleton WuWeiPrerequisites instance"""
    global _wu_wei_prerequisites
    if _wu_wei_prerequisites is None:
        _wu_wei_prerequisites = WuWeiPrerequisites()
    return _wu_wei_prerequisites
