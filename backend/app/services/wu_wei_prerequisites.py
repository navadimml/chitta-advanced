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

        🔍 Wu Wei Robustness Enhancement:
        - First checks semantic_verification result if available (LLM-based quality)
        - Falls back to heuristics if semantic verification not yet run

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

        # 🔍 NEW: Check semantic verification result first (if available)
        semantic_verification = context.get("semantic_verification")
        if semantic_verification:
            video_readiness = semantic_verification.get('video_guidelines_readiness', 0)
            recommendation = semantic_verification.get('recommendation', '')

            logger.info(f"🔍 Using semantic verification result:")
            logger.info(f"   Video guidelines readiness: {video_readiness}%")
            logger.info(f"   Recommendation: {recommendation}")

            # If semantic check says ready for video guidelines, trust it!
            if video_readiness >= 75 or recommendation == 'ready_for_video_guidelines':
                logger.info(f"✅ Semantic verification: READY for video guidelines ({video_readiness}%)")
                return PrerequisiteEvaluation(
                    met=True,
                    missing=[],
                    details={
                        "method": "semantic_verification",
                        "video_readiness": video_readiness,
                        "recommendation": recommendation
                    }
                )

            # If semantic check says not ready, check WHY and return specific feedback
            elif video_readiness < 60:
                critical_gaps = semantic_verification.get('critical_gaps', [])
                missing = [gap.get('field', 'unknown') for gap in critical_gaps]

                logger.info(f"❌ Semantic verification: NOT ready ({video_readiness}%)")
                logger.info(f"   Critical gaps: {missing}")

                return PrerequisiteEvaluation(
                    met=False,
                    missing=missing,
                    details={
                        "method": "semantic_verification",
                        "video_readiness": video_readiness,
                        "critical_gaps": [gap.get('issue') for gap in critical_gaps]
                    }
                )

            # If in middle range (60-74%), fall through to heuristic check as tiebreaker
            logger.info(f"⚠️ Semantic verification: UNCERTAIN ({video_readiness}%), using heuristic tiebreaker")

        # FALLBACK: Use existing heuristic check (character-based)
        # Extract what we know
        # Treat 'unknown', '(not mentioned yet)', and Hebrew placeholders as missing
        child_name = context.get("child_name")
        invalid_names = ['unknown', '(not mentioned yet)', 'לא צוין', 'לא ידוע', 'לא נמסר', 'None', 'null', 'NULL']
        has_child_name = bool(child_name and child_name not in invalid_names)

        age = context.get("age") or context.get("child_age")
        invalid_ages = ['unknown', '(not mentioned yet)', 'לא צוין', 'לא ידוע']
        has_age = bool(age and str(age) not in invalid_ages)

        # Concerns (can be in different fields depending on extraction schema)
        concerns = context.get("primary_concerns") or context.get("concerns") or []
        if isinstance(concerns, str):
            concerns = [concerns]
        # Filter out invalid/placeholder concerns
        invalid_concerns = ['unknown', '(not mentioned yet)', 'לא צוין', 'לא ידוע', 'לא נמסר', 'None', 'null', 'NULL', '']
        valid_concerns = [c for c in concerns if c and str(c).strip() not in invalid_concerns]
        # Has concerns if we have any valid concerns (even single categories like 'eating', 'speech', etc.)
        has_concerns = len(valid_concerns) >= 1

        # Check for developmental history in concern_description
        concern_description = context.get("concern_description") or ""
        has_developmental_history = len(concern_description) > 50  # Has substantial concern details

        # Strengths (can be text or list)
        strengths = context.get("strengths")
        if strengths is None:
            strengths = []

        # Handle different formats:
        # - If string: Check if substantial (30+ chars - lowered threshold)
        # - If list: Check if 1+ items (lowered from 2+)
        if isinstance(strengths, str):
            # Substantial text with strengths described (lowered from 50 to 30 chars)
            has_strengths = len(strengths) > 30
        elif isinstance(strengths, list):
            # List of individual strengths (lowered from 2+ to 1+)
            has_strengths = len(strengths) >= 1
        else:
            has_strengths = False

        # Contextual info
        other_info = context.get("other_info") or ""
        has_context = len(other_info) > 30  # Has some context

        # Message count
        message_count = context.get("message_count", 0)

        # Evaluate using Wu Wei qualitative criteria
        # Path 1: Rich structured knowledge (name is optional, age is critical)
        path_1_met = (
            has_age and  # Age is critical for developmental assessment
            (has_concerns or has_developmental_history) and
            has_strengths and
            has_context
        )

        # Path 2: Extensive conversation (fallback) - lowered threshold
        path_2_met = (
            message_count > 12 and  # Lowered from 15
            (has_concerns or has_developmental_history) and
            has_strengths
        )

        # Path 3: Good enough - basic info + substantial concern details
        path_3_met = (
            has_age and  # Age is critical, name can be asked later
            has_concerns and
            has_developmental_history and  # This means >50 chars in concern_description
            message_count > 8
        )

        met = path_1_met or path_2_met or path_3_met

        # Build details for debugging
        strengths_info = f"string ({len(strengths)} chars)" if isinstance(strengths, str) else f"list ({len(strengths)} items)"
        details = {
            "has_child_name": has_child_name,
            "has_age": has_age,
            "concerns_count": len(concerns) if isinstance(concerns, list) else f"text ({len(concerns)} chars)",
            "has_developmental_history": has_developmental_history,
            "strengths_format": strengths_info,
            "has_strengths": has_strengths,
            "has_context": has_context,
            "message_count": message_count,
            "path_1_met": path_1_met,
            "path_2_met": path_2_met,
            "path_3_met": path_3_met,
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
            f"🌟 KNOWLEDGE RICHNESS EVALUATION:"
        )
        logger.info(f"   Result: {met}")
        logger.info(f"   Path 1 (structured): {path_1_met}")
        logger.info(f"   Path 2 (extensive conversation): {path_2_met}")
        logger.info(f"   Path 3 (good enough): {path_3_met}")
        logger.info(f"   Details:")
        logger.info(f"     - has_child_name: {has_child_name} ('{context.get('child_name')}')")
        logger.info(f"     - has_age: {has_age} ({context.get('age') or context.get('child_age')})")
        logger.info(f"     - concerns: {concerns[:3] if isinstance(concerns, list) else str(concerns)[:100]}")
        logger.info(f"     - has_concerns: {has_concerns}")
        logger.info(f"     - has_developmental_history: {has_developmental_history} (concern_description length: {len(concern_description)})")
        logger.info(f"     - strengths type: {type(strengths).__name__}")
        logger.info(f"     - strengths value: {str(strengths)[:200] if strengths else None}")
        logger.info(f"     - has_strengths: {has_strengths} (string needs 30+ chars OR list needs 1+ items)")
        logger.info(f"     - has_context: {has_context} (other_info length: {len(other_info)})")
        logger.info(f"     - message_count: {message_count}")
        logger.info(f"   Why Path 1 {'PASSED' if path_1_met else 'FAILED'}:")
        if not path_1_met:
            if not has_age:
                logger.info(f"     ❌ Missing age (critical for developmental assessment)")
            if not (has_concerns or has_developmental_history):
                logger.info(f"     ❌ Missing concerns OR developmental history")
            if not has_strengths:
                logger.info(f"     ❌ Missing strengths (need 1+ items OR 30+ chars)")
            if not has_context:
                logger.info(f"     ❌ Missing context (other_info < 30 chars)")
        logger.info(f"   Why Path 2 {'PASSED' if path_2_met else 'FAILED'}:")
        if not path_2_met:
            if message_count <= 12:
                logger.info(f"     ❌ Not enough messages ({message_count} <= 12)")
            if not (has_concerns or has_developmental_history):
                logger.info(f"     ❌ Missing concerns OR developmental history")
            if not has_strengths:
                logger.info(f"     ❌ Missing strengths")
        logger.info(f"   Why Path 3 {'PASSED' if path_3_met else 'FAILED'}:")
        if not path_3_met:
            if not has_age:
                logger.info(f"     ❌ Missing age")
            if not has_concerns:
                logger.info(f"     ❌ Missing concerns")
            if not has_developmental_history:
                logger.info(f"     ❌ Missing substantial concern details (< 50 chars)")
            if message_count <= 8:
                logger.info(f"     ❌ Not enough messages ({message_count} <= 8)")

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
                # Extract artifact name, handling "artifacts.X.exists" format
                artifact_name = key.replace(".exists", "")
                # Strip "artifacts." prefix if present (card format includes it)
                if artifact_name.startswith("artifacts."):
                    artifact_name = artifact_name[len("artifacts."):]
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
                # Extract artifact name, handling "artifacts.X.status" format
                artifact_name = key.split(".status")[0]
                # Strip "artifacts." prefix if present (card format includes it)
                if artifact_name.startswith("artifacts."):
                    artifact_name = artifact_name[len("artifacts."):]
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
