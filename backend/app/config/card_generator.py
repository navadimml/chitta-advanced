"""
Card generator for context card management.

Generates and manages context cards based on session state,
using context_cards.yaml configuration.
"""

from typing import Dict, Any, List, Optional
import logging

from app.config.config_loader import load_context_cards

logger = logging.getLogger(__name__)


class CardGenerator:
    """
    Generator for context cards.

    Evaluates display conditions and generates appropriate cards
    based on current session state.
    """

    def __init__(self):
        """Initialize card generator."""
        self._card_config = load_context_cards()
        self._cards: Dict[str, Dict[str, Any]] = {}
        self._load_cards()

    def _load_cards(self) -> None:
        """Load card definitions from configuration."""
        cards_config = self._card_config.get("cards", {})
        self._cards = cards_config
        logger.info(f"Loaded {len(self._cards)} card definitions")

    def get_card(self, card_id: str) -> Optional[Dict[str, Any]]:
        """
        Get card definition by ID.

        Args:
            card_id: Card identifier

        Returns:
            Card configuration dict or None
        """
        return self._cards.get(card_id)

    def get_all_cards(self) -> Dict[str, Dict[str, Any]]:
        """Get all card definitions."""
        return self._cards.copy()

    def evaluate_display_conditions(
        self,
        card_id: str,
        context: Dict[str, Any]
    ) -> bool:
        """
        Evaluate if a card should be displayed based on display_conditions.

        Args:
            card_id: Card identifier
            context: Session context

        Returns:
            True if card should be displayed
        """
        card = self.get_card(card_id)
        if not card:
            return False

        conditions = card.get("display_conditions", {})
        if not conditions:
            return True  # No conditions = always show

        # Check phase
        required_phase = conditions.get("phase")
        current_phase = context.get("phase", "screening")

        if required_phase:
            if isinstance(required_phase, list):
                if current_phase not in required_phase:
                    return False
            elif required_phase != current_phase:
                return False

        # Behavioral flags that should not be evaluated as context conditions
        behavioral_flags = {
            "show_once",
            "auto_dismiss_when",
            "re_show_after_days",
            "updates_dynamically",
        }

        # Check all other conditions
        for condition_key, condition_value in conditions.items():
            if condition_key == "phase":
                continue  # Already checked above

            # Skip behavioral flags - they control card behavior, not display
            if condition_key in behavioral_flags:
                continue

            # Get context value
            context_value = context.get(condition_key)

            # Handle string conditions with operators (e.g., "< 0.80", ">= 3", "!= ready")
            if isinstance(condition_value, str):
                if not self._evaluate_string_condition(condition_value, context_value):
                    return False
            # Handle boolean conditions
            elif isinstance(condition_value, bool):
                if context_value != condition_value:
                    return False
            # Handle numeric conditions
            elif isinstance(condition_value, (int, float)):
                if context_value != condition_value:
                    return False
            # Handle list conditions (value must be in list)
            elif isinstance(condition_value, list):
                if context_value not in condition_value:
                    return False

        return True

    def _translate_concerns(self, concerns: List[str]) -> List[str]:
        """Translate concern categories to Hebrew"""
        translations = {
            "speech": "דיבור",
            "social": "חברתי",
            "attention": "קשב",
            "motor": "מוטורי",
            "sensory": "חושי",
            "emotional": "רגשי",
            "behavioral": "התנהגות",
            "learning": "למידה",
            "sleep": "שינה",
            "eating": "אכילה",
            "other": "אחר"
        }
        return [translations.get(c, c) for c in concerns]

    def _replace_template_vars(
        self,
        text: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Replace template variables in text with values from context.

        Args:
            text: Text with template variables like {child_name}
            context: Session context with values

        Returns:
            Text with variables replaced
        """
        if not text:
            return text

        # Build replacement dict
        replacements = {
            "parent_name": context.get("parent_name", "הורה"),
            "child_name": context.get("child_name", "הילד/ה"),
            "child_age": str(context.get("child_age", "")),
            "completeness_percentage": f"{int(context.get('completeness', 0) * 100)}",
            "uploaded_count": str(context.get("uploaded_video_count", 0)),
            "journal_entry_count": str(context.get("journal_entry_count", 0)),
            "phase": context.get("phase", "screening"),
        }

        # Replace all variables
        result = text
        for var_name, var_value in replacements.items():
            result = result.replace(f"{{{var_name}}}", var_value)

        return result

    def _evaluate_string_condition(
        self,
        condition: str,
        context_value: Any
    ) -> bool:
        """
        Evaluate a string condition that may contain operators.

        Args:
            condition: Condition string (e.g., "< 0.80", ">= 3", "!= ready")
            context_value: Actual value from context

        Returns:
            True if condition matches
        """
        condition = condition.strip()

        # Check for operators
        if condition.startswith(">="):
            threshold = float(condition[2:].strip())
            return context_value is not None and float(context_value) >= threshold
        elif condition.startswith("<="):
            threshold = float(condition[2:].strip())
            return context_value is not None and float(context_value) <= threshold
        elif condition.startswith(">"):
            threshold = float(condition[1:].strip())
            return context_value is not None and float(context_value) > threshold
        elif condition.startswith("<"):
            threshold = float(condition[1:].strip())
            return context_value is not None and float(context_value) < threshold
        elif condition.startswith("!="):
            expected = condition[2:].strip()

            # Handle special cases
            if expected == "None":
                # Check if value exists and is not empty
                if context_value is None:
                    return False
                # Also check for empty strings
                if isinstance(context_value, str) and not context_value.strip():
                    return False
                return True
            elif expected == "[]":
                return context_value != [] and context_value is not None and len(context_value) > 0

            # Try to parse as number if possible
            try:
                expected_num = float(expected)
                return context_value != expected_num
            except ValueError:
                return context_value != expected
        else:
            # Direct string equality
            return context_value == condition

    def get_visible_cards(
        self,
        context: Dict[str, Any],
        max_cards: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Get cards that should be visible in current context.

        Args:
            context: Session context
            max_cards: Maximum number of cards to return

        Returns:
            List of card configurations in frontend-compatible format
        """
        visible = []

        # Card type to frontend status mapping (for colors/animations)
        card_type_to_status = {
            "progress": "processing",
            "action_needed": "action",
            "success": "new",
            "guidance": "instruction",
            "ongoing_support": "processing",
        }

        # Card type to icon mapping (from YAML card_types config)
        card_type_icons = {
            "progress": "CheckCircle",
            "action_needed": "AlertCircle",
            "success": "CheckCircle",
            "guidance": "Info",
            "ongoing_support": "Heart",
        }

        for card_id, card in self._cards.items():
            if self.evaluate_display_conditions(card_id, context):
                card_type = card.get("card_type", "guidance")

                # Get content (could be content dict or content_by_state dict)
                content = card.get("content", {})

                # Handle content_by_state (like journal_card)
                if not content and "content_by_state" in card:
                    # Use first state as default (should be improved to check actual state)
                    content_by_state = card.get("content_by_state", {})
                    if content_by_state:
                        first_state_key = list(content_by_state.keys())[0]
                        content = content_by_state[first_state_key]

                # Extract title and subtitle
                title = content.get("title", card.get("name", ""))
                body = content.get("body", content.get("body_template", ""))

                # Handle progress_description_by_range (for interview_progress_card)
                if "progress_description_by_range" in content:
                    completeness = context.get("completeness", 0)
                    progress_pct = int(completeness * 100)

                    # Determine which range applies
                    progress_desc = ""
                    if progress_pct < 30:
                        progress_desc = content["progress_description_by_range"].get("0-30", {}).get("text", "")
                    elif progress_pct < 60:
                        progress_desc = content["progress_description_by_range"].get("30-60", {}).get("text", "")
                    else:
                        progress_desc = content["progress_description_by_range"].get("60-80", {}).get("text", "")

                    # Replace {progress_description} in body
                    body = body.replace("{progress_description}", progress_desc)

                # Handle concerns_summary for child_profile_card
                if "{concerns_summary}" in body:
                    primary_concerns = context.get("primary_concerns", [])
                    if primary_concerns:
                        concerns_hebrew = self._translate_concerns(primary_concerns)
                        concerns_count = len(concerns_hebrew)
                        if concerns_count == 1:
                            summary = f"{concerns_count} תחום התפתחות"
                        else:
                            summary = f"{concerns_count} תחומי התפתחות"
                        body = body.replace("{concerns_summary}", summary)
                    else:
                        # Remove concerns_summary and any trailing comma/space
                        body = body.replace(", {concerns_summary}", "")
                        body = body.replace("{concerns_summary}", "")

                # Handle concerns_list for concerns_card
                if "{concerns_list}" in body:
                    primary_concerns = context.get("primary_concerns", [])
                    if primary_concerns:
                        concerns_hebrew = self._translate_concerns(primary_concerns)
                        concerns_str = ", ".join(concerns_hebrew[:3])  # Show max 3
                        body = body.replace("{concerns_list}", concerns_str)
                    else:
                        body = body.replace("{concerns_list}", "")

                # Handle strengths_preview for strengths_card
                if "{strengths_preview}" in body:
                    strengths = context.get("strengths", "")
                    if strengths:
                        # Take first 2-3 sentences or first 150 chars
                        preview = strengths[:150]
                        if len(strengths) > 150:
                            # Try to cut at sentence boundary
                            last_period = preview.rfind(".")
                            if last_period > 50:  # At least some content
                                preview = preview[:last_period + 1]
                            else:
                                preview = preview + "..."
                        body = body.replace("{strengths_preview}", preview)
                    else:
                        body = body.replace("{strengths_preview}", "")

                # Remove unimplemented placeholders (like {missing_areas})
                # TODO: Implement full dynamic content generation
                body = body.replace("{missing_areas}", "")

                # Replace template variables in title and body
                title = self._replace_template_vars(title, context)
                body = self._replace_template_vars(body, context)

                # Use first meaningful line of body as subtitle
                subtitle = ""
                for line in body.split("\n"):
                    line = line.strip()
                    # Skip empty lines and markdown headers
                    if line and not line.startswith("#"):
                        # Remove markdown formatting
                        line = line.replace("**", "").replace("*", "")
                        # Skip bullet points with just placeholders
                        if not line.startswith("•") and not line.startswith("-"):
                            subtitle = line
                            break
                        elif len(line) > 3:  # Has content after bullet
                            subtitle = line
                            break

                # Limit subtitle length
                if len(subtitle) > 100:
                    subtitle = subtitle[:97] + "..."

                # Build card in OLD frontend format
                card_data = {
                    "type": card_id,  # Card identifier
                    "title": title,
                    "subtitle": subtitle,
                    "icon": card_type_icons.get(card_type, "Info"),
                    "status": card_type_to_status.get(card_type, "instruction"),
                    "action": card.get("available_actions", [None])[0] if card.get("available_actions") else None,
                }

                visible.append(card_data)

        # Sort by priority (higher priority first)
        # Get priority from original card config
        visible.sort(key=lambda c: self._cards.get(c["type"], {}).get("priority", 0), reverse=True)

        return visible[:max_cards]


# Global singleton
_card_generator: Optional[CardGenerator] = None


def get_card_generator() -> CardGenerator:
    """Get global CardGenerator instance."""
    global _card_generator
    if _card_generator is None:
        _card_generator = CardGenerator()
    return _card_generator
