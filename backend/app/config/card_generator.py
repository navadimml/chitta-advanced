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
        Evaluate if a card should be displayed.

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

        # Check phase
        required_phase = conditions.get("phase")
        current_phase = context.get("phase", "screening")

        if required_phase:
            if isinstance(required_phase, list):
                if current_phase not in required_phase:
                    return False
            elif required_phase != current_phase:
                return False

        # Check other conditions (simplified for now)
        # In full implementation, would evaluate all conditions

        return True

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
