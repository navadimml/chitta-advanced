"""
Card Lifecycle Service - Manages card creation, updates, and dismissal.

Decouples:
- CREATION: Event-driven (moment transitions FALSE → TRUE)
- DISPLAY: State-driven (active_cards list in FamilyState)
- CONTENT: Dynamic updates without recreating cards

This is the core of the Living Dashboard Phase 1.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from app.models.active_card import ActiveCard, CardDisplayMode, create_active_card
from app.models.family_state import FamilyState
from app.config.config_loader import load_workflow
from app.services.wu_wei_prerequisites import WuWeiPrerequisites

logger = logging.getLogger(__name__)


class CardLifecycleService:
    """
    Manages the lifecycle of context cards.

    Cards are created when moment prerequisites transition from FALSE to TRUE.
    Cards persist in FamilyState.active_cards until:
    - dismiss_when conditions are met
    - User explicitly dismisses
    - dismiss_on_action is triggered
    - auto_dismiss_seconds timeout expires
    """

    def __init__(self):
        self.workflow_config = load_workflow()
        self.moments = self.workflow_config.get("moments", {})
        self.prerequisite_evaluator = WuWeiPrerequisites()

    def process_transitions(
        self,
        family_state: FamilyState,
        previous_context: Dict[str, Any],
        current_context: Dict[str, Any]
    ) -> List[ActiveCard]:
        """
        Check for moment transitions and create cards.

        Only fires on FALSE → TRUE transitions, not on every evaluation.
        This prevents card flicker and recreation.

        Args:
            family_state: Current family state (will be modified)
            previous_context: Context from previous evaluation
            current_context: Current context

        Returns:
            List of newly created cards
        """
        new_cards = []

        for moment_id, moment_config in self.moments.items():
            if not isinstance(moment_config, dict):
                continue

            card_config = moment_config.get("card")
            if not card_config:
                continue

            lifecycle = card_config.get("lifecycle", {})
            trigger = lifecycle.get("trigger", "transition")

            # Only process transition-triggered cards
            if trigger != "transition":
                continue

            # Check if this moment was dismissed and prevent_re_trigger is set
            if lifecycle.get("prevent_re_trigger", False):
                if moment_id in family_state.dismissed_card_moments:
                    logger.debug(f"Skipping {moment_id}: previously dismissed")
                    continue

            # Check if card is already active
            card_id = card_config.get("card_id")
            if self._card_already_active(family_state, card_id):
                logger.debug(f"Skipping {moment_id}: card {card_id} already active")
                continue

            # Evaluate transition
            when_conditions = moment_config.get("when", {})
            was_met = self._evaluate_conditions(when_conditions, previous_context)
            is_met = self._evaluate_conditions(when_conditions, current_context)

            if not was_met and is_met:
                # TRANSITION DETECTED: FALSE → TRUE
                new_card = create_active_card(
                    card_config=card_config,
                    moment_id=moment_id,
                    context=current_context
                )
                family_state.active_cards.append(new_card)
                new_cards.append(new_card)
                logger.info(f"Card created: {new_card.card_id} (moment: {moment_id})")

        return new_cards

    def update_active_cards(
        self,
        family_state: FamilyState,
        context: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """
        Update existing cards: check dismissals, update dynamic content.

        Does NOT create new cards - only manages existing ones.

        Args:
            family_state: Current family state (will be modified)
            context: Current context for evaluation

        Returns:
            Dict with "dismissed" and "updated" card_id lists
        """
        changes = {"dismissed": [], "updated": []}

        for card in family_state.active_cards:
            if card.dismissed:
                continue

            # Check auto-dismiss timeout
            if card.should_auto_dismiss():
                card.dismiss(by="timeout")
                self._record_dismissal(family_state, card)
                changes["dismissed"].append(card.card_id)
                logger.info(f"Card auto-dismissed (timeout): {card.card_id}")
                continue

            # Check dismiss_when conditions
            if self._should_dismiss(card, context):
                card.dismiss(by="condition")
                self._record_dismissal(family_state, card)
                changes["dismissed"].append(card.card_id)
                logger.info(f"Card dismissed (condition): {card.card_id}")
                continue

            # Update dynamic content
            if card.dynamic_fields:
                updated = self._update_dynamic_content(card, context)
                if updated:
                    changes["updated"].append(card.card_id)
                    logger.debug(f"Card content updated: {card.card_id}")

        return changes

    def dismiss_card(
        self,
        family_state: FamilyState,
        card_id: str,
        by_action: Optional[str] = None
    ) -> bool:
        """
        Manually dismiss a card.

        Called when user dismisses or when an action triggers dismissal.

        Args:
            family_state: Current family state (will be modified)
            card_id: ID of card to dismiss
            by_action: Optional action that triggered dismissal

        Returns:
            True if card was found and dismissed
        """
        for card in family_state.active_cards:
            if card.card_id == card_id and not card.dismissed:
                dismiss_by = f"action:{by_action}" if by_action else "user"
                card.dismiss(by=dismiss_by)
                self._record_dismissal(family_state, card)
                logger.info(f"Card manually dismissed: {card_id} (by: {dismiss_by})")
                return True

        logger.warning(f"Card not found or already dismissed: {card_id}")
        return False

    def dismiss_by_action(
        self,
        family_state: FamilyState,
        action_id: str
    ) -> List[str]:
        """
        Dismiss all cards that have dismiss_on_action matching the given action.

        Args:
            family_state: Current family state (will be modified)
            action_id: The action that was executed

        Returns:
            List of dismissed card_ids
        """
        dismissed = []
        for card in family_state.active_cards:
            if card.dismissed:
                continue
            if card.dismiss_on_action == action_id:
                card.dismiss(by=f"action:{action_id}")
                self._record_dismissal(family_state, card)
                dismissed.append(card.card_id)
                logger.info(f"Card dismissed by action: {card.card_id} (action: {action_id})")

        return dismissed

    def get_visible_cards(
        self,
        family_state: FamilyState,
        display_mode: Optional[CardDisplayMode] = None
    ) -> List[ActiveCard]:
        """
        Get cards that should be displayed.

        Args:
            family_state: Current family state
            display_mode: Optional filter by display mode

        Returns:
            List of visible cards, sorted by priority (highest first)
        """
        visible = [
            card for card in family_state.active_cards
            if not card.dismissed
        ]

        if display_mode:
            visible = [c for c in visible if c.display_mode == display_mode]

        # Sort by priority (higher first)
        visible.sort(key=lambda c: c.priority, reverse=True)

        return visible

    def get_visible_cards_serialized(
        self,
        family_state: FamilyState,
        display_mode: Optional[CardDisplayMode] = None
    ) -> List[Dict[str, Any]]:
        """
        Get visible cards as serializable dicts for API response.

        Args:
            family_state: Current family state
            display_mode: Optional filter by display mode

        Returns:
            List of card dicts ready for JSON serialization
        """
        cards = self.get_visible_cards(family_state, display_mode)
        return [
            {
                "card_id": card.card_id,
                "instance_id": card.instance_id,
                "display_mode": card.display_mode,
                "priority": card.priority,
                "content": card.content,
                "actions": card.actions,
                "created_at": card.created_at.isoformat(),
            }
            for card in cards
        ]

    def cleanup_old_cards(
        self,
        family_state: FamilyState,
        max_dismissed_age_hours: int = 24
    ) -> int:
        """
        Remove old dismissed cards to prevent state bloat.

        Args:
            family_state: Current family state (will be modified)
            max_dismissed_age_hours: Remove cards dismissed longer than this

        Returns:
            Number of cards removed
        """
        cutoff = datetime.utcnow()
        original_count = len(family_state.active_cards)

        family_state.active_cards = [
            card for card in family_state.active_cards
            if not card.dismissed or (
                card.dismissed_at and
                (cutoff - card.dismissed_at).total_seconds() < max_dismissed_age_hours * 3600
            )
        ]

        removed = original_count - len(family_state.active_cards)
        if removed:
            logger.info(f"Cleaned up {removed} old dismissed cards")

        return removed

    def _card_already_active(self, family_state: FamilyState, card_id: str) -> bool:
        """Check if a card with this ID is already active (not dismissed)."""
        return any(
            c.card_id == card_id and not c.dismissed
            for c in family_state.active_cards
        )

    def _should_dismiss(self, card: ActiveCard, context: Dict[str, Any]) -> bool:
        """Check if card should be dismissed based on dismiss_when conditions."""
        if not card.dismiss_when:
            return False
        return self._evaluate_conditions(card.dismiss_when, context)

    def _update_dynamic_content(self, card: ActiveCard, context: Dict[str, Any]) -> bool:
        """Update dynamic fields in card content. Returns True if changed."""
        changed = False
        for field in card.dynamic_fields:
            # Get the path from original config (stored during creation)
            # For now, simplified: assume field name matches context key
            if field in context:
                if card.content.get(field) != context[field]:
                    card.content[field] = context[field]
                    changed = True
        return changed

    def _evaluate_conditions(self, conditions: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate prerequisite conditions against context."""
        if not conditions:
            return True
        return self.prerequisite_evaluator.evaluate_prerequisites(conditions, context)

    def _record_dismissal(self, family_state: FamilyState, card: ActiveCard) -> None:
        """Record dismissal to prevent re-triggering if configured."""
        if card.created_by_moment:
            family_state.dismissed_card_moments[card.created_by_moment] = (
                card.dismissed_at or datetime.utcnow()
            )


# Global singleton
_card_lifecycle_service: Optional[CardLifecycleService] = None


def get_card_lifecycle_service() -> CardLifecycleService:
    """Get global CardLifecycleService instance."""
    global _card_lifecycle_service
    if _card_lifecycle_service is None:
        _card_lifecycle_service = CardLifecycleService()
    return _card_lifecycle_service
