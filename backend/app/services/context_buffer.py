"""
Context Buffer Service - Dynamic Context Store with Selective Query

🌟 Wu Wei: Instead of sending all context every turn, we store context
in a key-value buffer that can be selectively queried by the LLM.

The LLM calls get_context(keys=[...]) in Phase 1 to request only
the context it needs to answer the parent's question.

Context Categories:
- child.*: Child information (name, age, concerns, strengths)
- artifacts.*: Artifact existence and status
- ui.*: UI locations and guidance
- actions.*: Available/blocked actions
- moment.*: Active moment context
- session.*: Session state (returning user, message count)

Usage:
    buffer = get_context_buffer()
    buffer.update_from_session(session, family_id)

    # LLM requests specific keys
    context = buffer.query(["child.name", "ui.guidelines", "artifacts.guidelines"])
"""

import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime

logger = logging.getLogger(__name__)


class ContextBuffer:
    """
    Dynamic context buffer with selective query support.

    Stores all available context as flat key-value pairs.
    LLM can query specific keys to get only relevant context.
    """

    def __init__(self):
        self._buffer: Dict[str, Any] = {}
        self._updated_at: Optional[datetime] = None
        self._available_keys: Set[str] = set()

    def clear(self):
        """Clear all context from buffer"""
        self._buffer.clear()
        self._available_keys.clear()
        self._updated_at = None

    def set(self, key: str, value: Any):
        """Set a single context value"""
        self._buffer[key] = value
        self._available_keys.add(key)
        self._updated_at = datetime.now()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a single context value"""
        return self._buffer.get(key, default)

    def query(self, keys: List[str]) -> Dict[str, Any]:
        """
        Query multiple context keys.

        Supports:
        - Exact keys: "child.name"
        - Prefix wildcards: "child.*" returns all child.* keys
        - Category queries: "artifacts" returns all artifacts.* keys

        Args:
            keys: List of keys or patterns to query

        Returns:
            Dict with requested key-value pairs
        """
        result = {}

        for key in keys:
            if key.endswith(".*"):
                # Prefix wildcard: "child.*" -> all keys starting with "child."
                prefix = key[:-1]  # Remove "*"
                for k, v in self._buffer.items():
                    if k.startswith(prefix):
                        result[k] = v
            elif "." not in key and key in self._get_categories():
                # Category query: "artifacts" -> all artifacts.* keys
                prefix = f"{key}."
                for k, v in self._buffer.items():
                    if k.startswith(prefix):
                        result[k] = v
            else:
                # Exact key
                if key in self._buffer:
                    result[key] = self._buffer[key]

        logger.debug(f"Context query {keys} returned {len(result)} keys")
        return result

    def get_available_keys(self) -> List[str]:
        """Get list of all available context keys"""
        return sorted(list(self._available_keys))

    def _get_categories(self) -> Set[str]:
        """Get unique category prefixes"""
        categories = set()
        for key in self._available_keys:
            if "." in key:
                categories.add(key.split(".")[0])
        return categories

    def get_key_summary(self) -> Dict[str, List[str]]:
        """
        Get summary of available keys grouped by category.
        Useful for telling LLM what's available to query.
        """
        summary = {}
        for key in self._available_keys:
            if "." in key:
                category = key.split(".")[0]
                if category not in summary:
                    summary[category] = []
                summary[category].append(key)
            else:
                if "_other" not in summary:
                    summary["_other"] = []
                summary["_other"].append(key)

        # Sort keys within each category
        for category in summary:
            summary[category] = sorted(summary[category])

        return summary

    def update_from_session(
        self,
        session,
        family_id: str,
        prerequisite_service=None,
        lifecycle_manager=None
    ):
        """
        Update buffer with all context from current session state.

        This populates the buffer with all available context.
        The LLM will then query only what it needs.

        Args:
            session: SessionState object
            family_id: Family identifier
            prerequisite_service: For action availability checks
            lifecycle_manager: For moment/lifecycle context
        """
        self.clear()

        # === CHILD CONTEXT ===
        data = session.extracted_data
        if data.child_name:
            self.set("child.name", data.child_name)
        if data.age:
            self.set("child.age", data.age)
        if data.gender:
            self.set("child.gender", data.gender)
        if data.primary_concerns:
            self.set("child.concerns", data.primary_concerns)
            self.set("child.concerns_text", ", ".join(data.primary_concerns))
        if data.concern_details:
            self.set("child.concern_details", data.concern_details)
        if data.strengths:
            self.set("child.strengths", data.strengths)
        if data.developmental_history:
            self.set("child.developmental_history", data.developmental_history)
        if data.family_context:
            self.set("child.family_context", data.family_context)
        if data.daily_routines:
            self.set("child.daily_routines", data.daily_routines)
        if data.parent_goals:
            self.set("child.parent_goals", data.parent_goals)
        if data.filming_preference:
            self.set("child.filming_preference", data.filming_preference)

        # === ARTIFACT CONTEXT ===
        for artifact_id, artifact in session.artifacts.items():
            self.set(f"artifacts.{artifact_id}.exists", True)
            self.set(f"artifacts.{artifact_id}.status", artifact.status)
            if hasattr(artifact, 'created_at') and artifact.created_at:
                self.set(f"artifacts.{artifact_id}.created_at", artifact.created_at)

        # Common artifact checks (for convenience)
        self.set("artifacts.has_guidelines", "baseline_video_guidelines" in session.artifacts)
        self.set("artifacts.has_report", "baseline_parent_report" in session.artifacts)
        self.set("artifacts.has_interview_summary", "baseline_interview_summary" in session.artifacts)

        # === SESSION CONTEXT ===
        self.set("session.message_count", len(session.conversation_history))
        self.set("session.user_message_count", len([m for m in session.conversation_history if m.get("role") == "user"]))
        self.set("session.completeness", session.completeness)
        self.set("session.family_id", family_id)

        # Time context for returning users
        if session.updated_at:
            from .wu_wei_prerequisites import get_wu_wei_prerequisites
            wu_wei = get_wu_wei_prerequisites()
            time_context = wu_wei.calculate_time_gap_context({"last_active": session.updated_at})

            self.set("session.time_gap_category", time_context.get("time_gap_category"))
            self.set("session.hours_since_active", time_context.get("hours_since_last_active"))
            self.set("session.days_since_active", time_context.get("days_since_last_active"))
            self.set("session.is_returning_user", time_context.get("is_returning_user", False))

            if time_context.get("is_returning_user"):
                # Build returning user summary
                context_for_summary = {
                    "child_name": data.child_name,
                    "age": data.age,
                    "primary_concerns": data.primary_concerns,
                    "strengths": data.strengths,
                    "artifacts": {k: {"status": v.status} for k, v in session.artifacts.items()}
                }
                summary = wu_wei.build_returning_user_summary(context_for_summary)
                self.set("session.returning_user_summary", summary)

        # === UI CONTEXT ===
        # Load UI guidance from workflow.yaml moments
        if lifecycle_manager:
            self._load_ui_context(lifecycle_manager, session)

        # === UI STATE CONTEXT ===
        # Load current UI state (view, progress, interactions) from tracker
        self._load_ui_state_context(family_id)

        # === ACTION CONTEXT ===
        if prerequisite_service:
            self._load_action_context(prerequisite_service, session)

        # === MOMENT CONTEXT ===
        if lifecycle_manager:
            self._load_moment_context(lifecycle_manager, session)

        logger.info(f"Context buffer updated with {len(self._available_keys)} keys")

    def _load_ui_context(self, lifecycle_manager, session):
        """Load UI location guidance from lifecycle config"""
        try:
            config = lifecycle_manager.get_lifecycle_config()
            moments = config.get("moments", {})

            for moment_id, moment_config in moments.items():
                ui_config = moment_config.get("ui", {})
                if ui_config:
                    ui_type = ui_config.get("type", "")
                    ui_default = ui_config.get("default", "")
                    ui_mobile = ui_config.get("mobile", "")

                    if ui_default:
                        self.set(f"ui.{moment_id}.location", ui_default)
                    if ui_mobile:
                        self.set(f"ui.{moment_id}.location_mobile", ui_mobile)
                    if ui_type:
                        self.set(f"ui.{moment_id}.type", ui_type)

            # Add common UI locations
            if "baseline_video_guidelines" in session.artifacts:
                self.set("ui.guidelines.location", "הכרטיס 'הנחיות צילום' למטה")
            if "baseline_parent_report" in session.artifacts:
                self.set("ui.report.location", "הכרטיס 'מדריך להורים' למטה")

        except Exception as e:
            logger.warning(f"Failed to load UI context: {e}")

    def _load_ui_state_context(self, family_id: str):
        """
        Load current UI state from the UI state tracker.

        This provides awareness of:
        - Current view/page the user is on
        - Progress states (video uploads, report generation)
        - Recent interactions (what user viewed/clicked)
        """
        try:
            from .ui_state_tracker import get_ui_state_tracker

            tracker = get_ui_state_tracker()
            ui_context = tracker.get_context_dict(family_id)

            # Add all UI state context to buffer
            for key, value in ui_context.items():
                self.set(key, value)

            logger.debug(f"Loaded {len(ui_context)} UI state keys")

        except Exception as e:
            logger.warning(f"Failed to load UI state context: {e}")

    def _load_action_context(self, prerequisite_service, session):
        """Load action availability context"""
        try:
            # Build session data for prerequisite checks
            extracted_dict = session.extracted_data.model_dump()

            session_data = {
                "extracted_data": extracted_dict,
                "artifacts": {k: {"status": v.status} for k, v in session.artifacts.items()},
                "completeness": session.completeness,
            }

            context = prerequisite_service.get_context_for_cards(session_data)

            # Get all actions and check availability
            from app.config.action_registry import get_action_registry
            action_registry = get_action_registry()
            all_actions = action_registry.get_all_actions()

            available_actions = []
            blocked_actions = {}

            for action_id, action in all_actions.items():
                check = prerequisite_service.check_action_feasible(
                    action=action_id,
                    context=context
                )

                if check.feasible:
                    available_actions.append(action_id)
                    self.set(f"actions.{action_id}.available", True)
                    if hasattr(action, 'opens_view') and action.opens_view:
                        self.set(f"actions.{action_id}.opens_view", action.opens_view)
                else:
                    blocked_actions[action_id] = check.explanation_to_user or "Prerequisites not met"
                    self.set(f"actions.{action_id}.available", False)
                    self.set(f"actions.{action_id}.blocked_reason", check.explanation_to_user)

            self.set("actions.available_list", available_actions)
            self.set("actions.blocked_list", list(blocked_actions.keys()))

        except Exception as e:
            logger.warning(f"Failed to load action context: {e}")

    def _load_moment_context(self, lifecycle_manager, session):
        """Load active moment context"""
        try:
            config = lifecycle_manager.get_lifecycle_config()
            moments = config.get("moments", {})

            # Check which moments are currently active/triggered
            for moment_id, moment_config in moments.items():
                # Check if moment has context to provide
                context_text = moment_config.get("context", "")
                if context_text:
                    self.set(f"moment.{moment_id}.context", context_text)

                # Check for card configuration
                card_config = moment_config.get("card", {})
                if card_config:
                    self.set(f"moment.{moment_id}.has_card", True)
                    content = card_config.get("content", {})
                    if content.get("title"):
                        self.set(f"moment.{moment_id}.card_title", content["title"])

            # Track last triggered moment if available
            if hasattr(session, 'last_triggered_moment') and session.last_triggered_moment:
                moment_data = session.last_triggered_moment
                moment_id = moment_data.get('id') if isinstance(moment_data, dict) else None
                if moment_id:
                    self.set("moment.active", moment_id)
                    # Include full context for active moment
                    if moment_id in moments:
                        active_context = moments[moment_id].get("context", "")
                        if active_context:
                            self.set("moment.active_context", active_context)

        except Exception as e:
            logger.warning(f"Failed to load moment context: {e}")

    def format_for_llm(self, keys: List[str]) -> str:
        """
        Format queried context as a string for LLM injection.

        Args:
            keys: Keys that were queried

        Returns:
            Formatted string for system prompt injection
        """
        result = self.query(keys)

        if not result:
            return ""

        lines = ["<requested_context>"]

        # Group by category for readability
        categories = {}
        for key, value in result.items():
            if "." in key:
                category = key.split(".")[0]
            else:
                category = "_other"

            if category not in categories:
                categories[category] = {}
            categories[category][key] = value

        for category, items in sorted(categories.items()):
            if category != "_other":
                lines.append(f"\n[{category}]")
            for key, value in sorted(items.items()):
                # Format value appropriately
                if isinstance(value, list):
                    value_str = ", ".join(str(v) for v in value)
                elif isinstance(value, bool):
                    value_str = "yes" if value else "no"
                else:
                    value_str = str(value)

                # Use short key (without category prefix) for readability
                short_key = key.split(".", 1)[1] if "." in key else key
                lines.append(f"  {short_key}: {value_str}")

        lines.append("</requested_context>")

        return "\n".join(lines)


# Singleton instance per family
_context_buffers: Dict[str, ContextBuffer] = {}


def get_context_buffer(family_id: str = None) -> ContextBuffer:
    """
    Get context buffer instance.

    If family_id is provided, returns a family-specific buffer.
    Otherwise returns a new buffer instance.
    """
    if family_id:
        if family_id not in _context_buffers:
            _context_buffers[family_id] = ContextBuffer()
        return _context_buffers[family_id]
    return ContextBuffer()


def clear_context_buffer(family_id: str):
    """Clear context buffer for a specific family"""
    if family_id in _context_buffers:
        _context_buffers[family_id].clear()
        del _context_buffers[family_id]
