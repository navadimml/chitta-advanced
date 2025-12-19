"""
Moment Context Builder Service

Wu Wei: Builds dynamic context that grounds Chitta in current reality.
- Journey context: What capabilities are unlocked, what's coming next
- Available now: What exists, what actions are possible
- No stages, just continuous conversation with progressive unlocking

Configuration-first: All domain knowledge from YAML configs, no hardcoded logic.
🌟 Uses i18n for all context text templates
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .i18n_service import t, t_section

logger = logging.getLogger(__name__)


@dataclass
class MomentContext:
    """Context for a triggered moment"""
    moment_id: str
    context: str


class MomentContextBuilder:
    """
    Builds comprehensive context for Chitta about the current state.

    Wu Wei Principles:
    - Configuration-first: Derive from YAML configs only
    - No domain-specific code: Use artifact/action IDs directly
    - Focus on capabilities (not stages)
    - Continuous conversation with progressive unlocking
    """

    def __init__(self, prerequisite_service, lifecycle_manager, action_registry):
        self.prerequisite_service = prerequisite_service
        self.lifecycle_manager = lifecycle_manager
        self.action_registry = action_registry

    def build_comprehensive_context(
        self,
        session_state,
        family_id: str
    ) -> str:
        """
        Build complete two-layer context:
        1. Journey context (capabilities unlocked/will unlock + current moment)
        2. Available now (artifacts, actions, boundaries)
        """
        journey_ctx = self.build_journey_context(session_state, family_id)
        available_ctx = self.build_available_now_context(session_state, family_id)

        return f"{journey_ctx}\n\n{available_ctx}"

    def build_journey_context(self, session_state, family_id: str) -> str:
        """
        Build journey context showing:
        - Unlocked capabilities (from lifecycle_events.yaml)
        - Capabilities that will unlock (from moment prerequisites)
        - Current moment context (persists until next moment)

        Wu Wei: No stages, just continuous flow with progressive unlocking
        """
        # Get unlocked capabilities (from lifecycle_events always_available + unlocks)
        unlocked = self._get_unlocked_capabilities(session_state)

        # Get next capabilities to unlock (from lifecycle_events moments)
        next_capabilities = self._get_next_unlockable_capabilities(session_state)

        # Get active moment context (persists)
        active_moment = self._get_active_moment_context(session_state)

        # Build context
        parts = ["<journey_context>"]

        # Unlocked capabilities
        if unlocked:
            parts.append("<unlocked_capabilities>")
            parts.append(self._format_unlocked_capabilities(unlocked))
            parts.append("</unlocked_capabilities>")
            parts.append("")

        # Next to unlock
        if next_capabilities:
            parts.append("<will_unlock>")
            for cap in next_capabilities:
                parts.append(f"⏳ {cap}")
            parts.append("</will_unlock>")
            parts.append("")

        # Active moment context (if exists)
        if active_moment:
            parts.append(f"<current_moment type=\"{active_moment.moment_id}\">")
            parts.append(active_moment.context)
            parts.append("</current_moment>")
            parts.append("")

        # Philosophy reminder (from i18n)
        parts.append(t("context.journey.continuous_conversation"))
        parts.append(t("context.journey.no_stages"))
        parts.append(t("context.journey.guide_by_available"))
        parts.append("</journey_context>")

        return "\n".join(parts)

    def build_available_now_context(self, session_state, family_id: str) -> str:
        """
        Build context about what exists and what's possible RIGHT NOW.

        Wu Wei: Derive from session state + config-driven prerequisite checks
        - Available artifacts (from session.artifacts)
        - Available actions (from action_registry + prerequisite_service)
        - Blocked actions (with explanations from prerequisite_service)
        """
        # Get artifacts that exist
        existing_artifacts = list(session_state.artifacts.keys())

        # Get available and blocked actions (config-driven)
        available_actions, blocked_actions = self._get_action_status(session_state)

        # Build context using i18n templates
        parts = ["<available_now>"]

        # Artifacts (use IDs directly)
        parts.append(t("context.available.existing_artifacts"))
        if existing_artifacts:
            for artifact_id in existing_artifacts:
                parts.append(f"  - {artifact_id}")
        else:
            parts.append(f"  - {t('context.available.none_yet')}")
        parts.append("")

        # Available actions (from action_registry)
        parts.append(t("context.available.available_actions"))
        if available_actions:
            for action_id in available_actions:
                parts.append(f"  - {action_id}")
        else:
            parts.append(f"  - {t('context.available.none_yet')}")
        parts.append("")

        # Blocked actions (with reasons from prerequisite_service)
        if blocked_actions:
            parts.append(t("context.available.blocked_actions"))
            for action in blocked_actions:
                parts.append(f"  - {action['id']} → {action['reason']}")
            parts.append("")

        # Guidance for using IDs (from i18n)
        parts.append(t("context.available.translation_note"))

        # Get artifact translation example from i18n
        artifact_translations = t_section("context.artifact_translations")
        if artifact_translations:
            # Use first translation as example
            example_id = next(iter(artifact_translations.keys()), "baseline_video_guidelines")
            example_translation = artifact_translations.get(example_id, "")
            if example_translation:
                parts.append(t("context.available.translation_example",
                              id=example_id, translation=example_translation))
        parts.append("")

        # Critical boundaries (from i18n)
        parts.append(f"🛡️ {t('context.boundaries.title')}")
        parts.append(f"1. {t('context.boundaries.rule_only_listed')}")
        parts.append(f"2. {t('context.boundaries.rule_not_exist')}")
        parts.append(f"3. {t('context.boundaries.rule_never_promise')}")
        parts.append(f"4. {t('context.boundaries.rule_explain_unlock')}")
        parts.append("")

        # Proactive guidance (from i18n)
        parts.append(f"✨ {t('context.proactive.title')}")
        parts.append(f"1. {t('context.proactive.suggest_capabilities')}")
        parts.append(f"2. {t('context.proactive.connect_concerns')}")
        parts.append(f"3. {t('context.proactive.natural_helpful')}")
        parts.append(f"4. Example: \"{t('context.proactive.example')}\"")
        parts.append("</available_now>")

        return "\n".join(parts)

    # ==================== Helper Methods ====================

    def _get_unlocked_capabilities(self, session_state) -> List[str]:
        """
        Get capabilities that are currently unlocked.

        Wu Wei: Read from lifecycle_events.yaml
        - always_available (base capabilities)
        - Capabilities from triggered moments (moment.unlocks)
        """
        capabilities = []

        # Get always available from lifecycle_events
        lifecycle_config = self.lifecycle_manager.get_lifecycle_config()

        if 'always_available' in lifecycle_config:
            capabilities.extend(lifecycle_config['always_available'])

        # Get unlocked capabilities from triggered moments
        # (moments that have been reached based on session state)
        triggered_moments = self._get_triggered_moments(session_state)

        for moment in triggered_moments:
            if 'unlocks' in moment:
                capabilities.extend(moment['unlocks'])

        return capabilities

    def _get_next_unlockable_capabilities(self, session_state) -> List[str]:
        """
        Get capabilities that will unlock next.

        Wu Wei: Read from lifecycle_events.yaml moments
        Check which moments haven't triggered yet but could be next
        """
        next_caps = []

        # Get all moments from lifecycle_events
        lifecycle_config = self.lifecycle_manager.get_lifecycle_config()
        moments = lifecycle_config.get('moments', {})

        # Find moments that could unlock soon
        for moment_id, moment_config in moments.items():
            # Skip if already triggered
            if self._is_moment_triggered(moment_id, session_state):
                continue

            # Check if this moment has unlocks
            if 'unlocks' in moment_config:
                # Add description of what will unlock
                unlocks_list = ', '.join(moment_config['unlocks'])
                next_caps.append(f"{unlocks_list} (from {moment_id})")

        return next_caps[:3]  # Limit to next 3 for brevity

    def _get_active_moment_context(self, session_state) -> Optional[MomentContext]:
        """
        Get the most recent triggered moment's context.
        Persists until next moment triggers.

        Wu Wei: Context comes from lifecycle_events.yaml moment.context field
        """
        # Get last triggered moment from session state
        last_moment_data = getattr(session_state, 'last_triggered_moment', None)

        if last_moment_data:
            moment_id = last_moment_data.get('id') if isinstance(last_moment_data, dict) else None

            if moment_id:
                # Get moment config from lifecycle_events
                lifecycle_config = self.lifecycle_manager.get_lifecycle_config()
                moment_config = lifecycle_config.get('moments', {}).get(moment_id, {})

                # Get context from config
                context_text = moment_config.get('context', '')

                if context_text:
                    return MomentContext(
                        moment_id=moment_id,
                        context=context_text
                    )

        return None

    def _get_action_status(self, session_state) -> tuple:
        """
        Get available and blocked actions.

        Wu Wei:
        - Get ALL actions from action_registry (from action_graph.yaml)
        - Check feasibility using prerequisite_service (config-driven)

        Returns: (available_action_ids, blocked_actions_with_reasons)
        """
        # Build context for prerequisite checks
        session_data = self._build_session_data_for_prerequisites(session_state)
        context = self.prerequisite_service.get_context_for_cards(session_data)

        available = []
        blocked = []

        # Get ALL actions from action_registry (config-driven, no hardcoded list!)
        all_actions_dict = self.action_registry.get_all_actions()

        for action_id, action in all_actions_dict.items():
            try:
                # Check feasibility (prerequisite_service uses wu_wei_prerequisites.py)
                check = self.prerequisite_service.check_action_feasible(
                    action=action_id,
                    context=context
                )

                if check.feasible:
                    available.append(action_id)  # Just ID, no description needed
                else:
                    blocked.append({
                        "id": action_id,
                        "reason": check.explanation_to_user or "Prerequisites not met"
                    })
            except Exception as e:
                # Log but don't fail - just skip this action
                logger.warning(f"Failed to check action '{action_id}': {e}")
                # Assume blocked if check fails
                blocked.append({
                    "id": action_id,
                    "reason": "Could not determine prerequisites"
                })

        return available, blocked

    def _build_session_data_for_prerequisites(self, session_state) -> Dict[str, Any]:
        """Build session data dict for prerequisite service"""
        extracted_dict = session_state.extracted_data.model_dump()

        return {
            "extracted_data": extracted_dict,
            "artifacts": session_state.artifacts,
            "completeness": session_state.completeness,
        }

    def _get_triggered_moments(self, session_state) -> List[Dict]:
        """
        Get moments that have been triggered based on session state.

        Wu Wei: Check which moments' prerequisites are met
        """
        triggered = []

        lifecycle_config = self.lifecycle_manager.get_lifecycle_config()
        moments = lifecycle_config.get('moments', {})

        for moment_id, moment_config in moments.items():
            if self._is_moment_triggered(moment_id, session_state):
                triggered.append(moment_config)

        return triggered

    def _is_moment_triggered(self, moment_id: str, session_state) -> bool:
        """
        Check if a moment has been triggered.

        Simple heuristic: If moment generates an artifact, check if artifact exists
        """
        lifecycle_config = self.lifecycle_manager.get_lifecycle_config()
        moment_config = lifecycle_config.get('moments', {}).get(moment_id, {})

        # If moment generates artifact, check if it exists
        if 'artifact' in moment_config:
            artifact_id = moment_config['artifact']
            return artifact_id in session_state.artifacts

        # For moments without artifacts, assume not triggered
        # (could be enhanced with more sophisticated tracking)
        return False

    def _format_unlocked_capabilities(self, capabilities: List[str]) -> str:
        """Format unlocked capabilities as simple list"""
        if not capabilities:
            return ""

        parts = []
        for cap in capabilities:
            parts.append(f"  ✅ {cap}")

        return "\n".join(parts)


# Singleton instance
_moment_context_builder = None


def get_moment_context_builder():
    """Get singleton instance of MomentContextBuilder"""
    global _moment_context_builder

    if _moment_context_builder is None:
        from app.services.prerequisite_service import get_prerequisite_service
        from app.services.lifecycle_manager import get_lifecycle_manager
        from app.config.action_registry import get_action_registry

        _moment_context_builder = MomentContextBuilder(
            prerequisite_service=get_prerequisite_service(),
            lifecycle_manager=get_lifecycle_manager(),
            action_registry=get_action_registry()
        )

    return _moment_context_builder
