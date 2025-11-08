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
            List of card configurations sorted by priority, with flattened structure
        """
        visible = []

        for card_id, card in self._cards.items():
            if self.evaluate_display_conditions(card_id, context):
                # Create flattened card structure for frontend consumption
                card_data = {
                    "card_id": card_id,
                    "name": card.get("name", ""),
                    "name_en": card.get("name_en", ""),
                    "card_type": card.get("card_type", ""),
                    "priority": card.get("priority", 0),
                }

                # Flatten content to top level for easier frontend access
                content = card.get("content", {})
                if isinstance(content, dict):
                    card_data["title"] = content.get("title", "")
                    card_data["body"] = content.get("body", "")
                    card_data["footer"] = content.get("footer", "")
                    # Keep other content fields as-is
                    for key, value in content.items():
                        if key not in ["title", "body", "footer"]:
                            card_data[f"content_{key}"] = value

                # Add available actions
                card_data["available_actions"] = card.get("available_actions", [])

                # Add behavior flags
                card_data["dismissible"] = card.get("dismissible", True)
                card_data["auto_dismiss_after_action"] = card.get("auto_dismiss_after_action")

                visible.append(card_data)

        # Sort by priority (higher priority first)
        visible.sort(key=lambda c: c.get("priority", 0), reverse=True)

        return visible[:max_cards]


# Global singleton
_card_generator: Optional[CardGenerator] = None


def get_card_generator() -> CardGenerator:
    """Get global CardGenerator instance."""
    global _card_generator
    if _card_generator is None:
        _card_generator = CardGenerator()
    return _card_generator
