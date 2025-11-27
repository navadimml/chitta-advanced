"""
Domain Text Builder - Chitta-Specific Text Construction

🌟 Wu Wei: Bridge between generic i18n and Chitta domain.

This service knows:
- What context fields exist (child_name, concerns, etc.)
- How to build summaries from extracted data
- How to select the right greeting based on state

It uses i18n_service for actual text, keeping this layer
focused on domain logic only.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .i18n_service import get_i18n, t, t_section

logger = logging.getLogger(__name__)


class DomainTextBuilder:
    """
    Builds domain-specific text using i18n translations.

    This class encapsulates Chitta's domain knowledge:
    - What concerns look like
    - What journey stages exist
    - How to build user-friendly summaries
    """

    def __init__(self, language: str = None):
        self.i18n = get_i18n(language)

    def build_returning_user_summary(self, context: Dict[str, Any]) -> str:
        """
        Build a localized summary for returning users.

        Args:
            context: Must contain extracted_data with child info

        Returns:
            Localized summary string
        """
        extracted = context.get("extracted_data", {})
        if not extracted:
            return t("domain.summary_templates.getting_started")

        lines = []

        # Child info
        child_name = extracted.get("child_name")
        age = extracted.get("child_age")
        if child_name:
            if age:
                lines.append(t("domain.summary_templates.child_info",
                              child_name=child_name, age=age))
            else:
                lines.append(child_name)

        # Concerns - translate each one
        concerns = extracted.get("concerns", [])
        if concerns:
            translated_concerns = self._translate_concerns(concerns)
            if translated_concerns:
                lines.append(t("domain.summary_templates.concerns_discussed",
                              concerns=", ".join(translated_concerns)))

        # Strengths - abbreviated
        strengths = extracted.get("strengths")
        if strengths:
            # Truncate if too long
            short_strengths = strengths[:50] + "..." if len(strengths) > 50 else strengths
            lines.append(t("domain.summary_templates.strengths_noted",
                          strengths=short_strengths))

        # Journey stage indicators
        artifacts = context.get("artifacts", {})
        videos_count = len(context.get("videos_uploaded", []))

        if "parent_report" in artifacts:
            lines.append(t("domain.summary_templates.report_ready"))
        elif videos_count > 0:
            lines.append(t("domain.summary_templates.videos_uploaded", count=videos_count))
        elif "baseline_video_guidelines" in artifacts:
            lines.append(t("domain.summary_templates.guidelines_ready"))

        if not lines:
            return t("domain.summary_templates.getting_started")

        return "\n".join(lines)

    def _translate_concerns(self, concerns: List[str]) -> List[str]:
        """Translate concern keys to localized labels"""
        concern_translations = t_section("domain.concerns")
        translated = []

        for concern in concerns:
            # Normalize concern key
            key = concern.lower().strip()
            if key in concern_translations:
                translated.append(concern_translations[key])
            else:
                # Fallback: use original
                translated.append(concern)

        return translated

    def get_greeting(self, context: Dict[str, Any]) -> str:
        """
        Select and build appropriate greeting based on context.

        Args:
            context: Session context with time_gap, extracted_data, artifacts, etc.

        Returns:
            Localized greeting string
        """
        # First visit - no conversation history
        conversation = context.get("conversation", [])
        if not conversation:
            return t("greetings.first_visit")

        child_name = self._get_child_name(context)
        time_gap = context.get("time_gap", {})
        category = time_gap.get("category", "same_session")
        days = time_gap.get("days", 0)
        artifacts = context.get("artifacts", {})
        videos_count = len(context.get("videos_uploaded", []))

        # Long absence (7+ days)
        if category == "long_absence":
            return t("greetings.returning.long_absence", child_name=child_name)

        # Returning after 1-7 days
        if category == "returning":
            time_ago = self.i18n.format_time_ago(days)

            # Check journey stage for stage-specific greeting
            if "baseline_video_guidelines" in artifacts and videos_count == 0:
                return t("greetings.stage.guidelines_ready",
                        child_name=child_name, time_ago=time_ago)

            return t("greetings.returning.after_days",
                    child_name=child_name, time_ago=time_ago)

        # Same session or short break - use stage-based greetings
        return self._get_stage_greeting(context, child_name)

    def _get_stage_greeting(self, context: Dict[str, Any], child_name: str) -> str:
        """Get greeting based on current journey stage"""
        artifacts = context.get("artifacts", {})
        videos_count = len(context.get("videos_uploaded", []))

        # Report ready
        if "parent_report" in artifacts:
            return t("greetings.stage.report_ready", child_name=child_name)

        # Videos analyzing (3+ uploaded, no report yet)
        if videos_count >= 3 and "parent_report" not in artifacts:
            return t("greetings.stage.videos_analyzing", child_name=child_name)

        # Partial videos uploaded
        if videos_count > 0 and videos_count < 3:
            return t("greetings.stage.videos_partial",
                    child_name=child_name,
                    videos_uploaded=videos_count,
                    videos_remaining=3 - videos_count)

        # Guidelines ready, no videos
        if "baseline_video_guidelines" in artifacts and videos_count == 0:
            return t("greetings.stage.guidelines_ready",
                    child_name=child_name, time_ago="")

        # Mid-interview (default)
        return t("greetings.returning.short_break", child_name=child_name)

    def _get_child_name(self, context: Dict[str, Any]) -> str:
        """Extract child name from context, with fallback"""
        extracted = context.get("extracted_data", {})
        return extracted.get("child_name", "הילד/ה")

    def get_card_content(self, card_key: str, context: Dict[str, Any]) -> Dict[str, str]:
        """
        Build localized card content.

        Args:
            card_key: Card identifier (e.g., "returning_user", "guidelines_ready")
            context: Session context for placeholders

        Returns:
            Dict with title, body, footer
        """
        child_name = self._get_child_name(context)
        videos_count = len(context.get("videos_uploaded", []))

        # Build placeholders based on card type
        placeholders = {
            "child_name": child_name,
            "videos_uploaded": videos_count,
            "videos_total": 3,
            "videos_remaining": max(0, 3 - videos_count),
        }

        # Add summary for returning user cards
        if "returning" in card_key:
            placeholders["summary"] = self.build_returning_user_summary(context)

        return {
            "title": t(f"cards.{card_key}.title", **placeholders),
            "body": t(f"cards.{card_key}.body", **placeholders),
            "footer": t(f"cards.{card_key}.footer", **placeholders)
        }

    def get_moment_message(self, moment_key: str, context: Dict[str, Any]) -> str:
        """
        Get localized moment message.

        Args:
            moment_key: Moment identifier (e.g., "knowledge_rich", "offer_filming")
            context: Session context for placeholders

        Returns:
            Localized message string
        """
        child_name = self._get_child_name(context)
        videos_count = len(context.get("videos_uploaded", []))

        placeholders = {
            "child_name": child_name,
            "count": videos_count,
            "remaining": max(0, 3 - videos_count)
        }

        return t(f"moments.{moment_key}", **placeholders)

    def get_error_message(self, error_key: str) -> str:
        """Get localized error message"""
        return t(f"errors.{error_key}")

    def get_button_text(self, button_key: str) -> str:
        """Get localized button text"""
        return t(f"ui.buttons.{button_key}")


# Singleton instance
_builder: Optional[DomainTextBuilder] = None


def get_text_builder(language: str = None) -> DomainTextBuilder:
    """Get domain text builder instance"""
    global _builder
    if _builder is None or (language and _builder.i18n.language != language):
        _builder = DomainTextBuilder(language)
    return _builder
