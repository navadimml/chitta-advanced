"""
Active Card Model - Runtime state of card instances.

Part of the Card Lifecycle system that decouples:
- CREATION: Event-driven (moment transitions)
- DISPLAY: State-driven (active_cards list)
- CONTENT: Dynamic updates without recreation
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import uuid


class CardDisplayMode(str, Enum):
    """Where and how a card is displayed."""
    FLOATING = "floating"      # Above chat input (default context cards)
    TOAST = "toast"            # Brief notification, auto-dismiss
    DRAWER_ITEM = "drawer_item"  # In artifact drawer (future)


class ActiveCard(BaseModel):
    """
    Runtime state of a card instance.

    Cards are created by moments (event-driven) and persist until
    dismissed by conditions, user action, or timeout.
    """
    # Identity
    card_id: str
    instance_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])

    # Lifecycle
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by_moment: Optional[str] = None
    dismissed: bool = False
    dismissed_at: Optional[datetime] = None
    dismissed_by: Optional[str] = None  # "condition", "user", "action", "timeout"

    # Display
    display_mode: CardDisplayMode = CardDisplayMode.FLOATING
    priority: int = 50  # Higher = more important

    # Content (rendered from template + context)
    content: Dict[str, Any] = Field(default_factory=dict)

    # Dynamic content fields that update without recreating card
    dynamic_fields: List[str] = Field(default_factory=list)

    # Dismissal rules (copied from config at creation time)
    dismiss_when: Optional[Dict[str, Any]] = None
    auto_dismiss_seconds: Optional[int] = None
    dismiss_on_action: Optional[str] = None

    # Actions available on this card (can be action IDs or action dicts)
    actions: List[Any] = Field(default_factory=list)  # List[str | Dict[str, Any]]

    class Config:
        use_enum_values = True

    def should_auto_dismiss(self) -> bool:
        """Check if card has exceeded its auto-dismiss timeout."""
        if not self.auto_dismiss_seconds:
            return False
        elapsed = (datetime.utcnow() - self.created_at).total_seconds()
        return elapsed >= self.auto_dismiss_seconds

    def dismiss(self, by: str = "condition") -> None:
        """Mark this card as dismissed."""
        self.dismissed = True
        self.dismissed_at = datetime.utcnow()
        self.dismissed_by = by

    def update_content(self, updates: Dict[str, Any]) -> bool:
        """
        Update dynamic content fields.
        Returns True if any content changed.
        """
        changed = False
        for field, value in updates.items():
            if field in self.dynamic_fields:
                if self.content.get(field) != value:
                    self.content[field] = value
                    changed = True
        return changed


def create_active_card(
    card_config: Dict[str, Any],
    moment_id: str,
    context: Dict[str, Any]
) -> ActiveCard:
    """
    Factory function to create an ActiveCard from config and context.

    Args:
        card_config: Card configuration from workflow.yaml
        moment_id: The moment that triggered this card
        context: Current session context for rendering content

    Returns:
        New ActiveCard instance
    """
    content_config = card_config.get("content", {})
    lifecycle_config = card_config.get("lifecycle", {})

    # Render static content
    content = {
        "title": content_config.get("title", ""),
        "body": content_config.get("body", ""),
        "footer": content_config.get("footer", ""),
    }

    # Track dynamic fields and render initial values
    dynamic_fields = []
    dynamic_config = content_config.get("dynamic", {})
    for field, path in dynamic_config.items():
        value = _resolve_path(path, context)
        content[field] = value
        dynamic_fields.append(field)

    # Get actions
    actions = card_config.get("actions", [])

    return ActiveCard(
        card_id=card_config["card_id"],
        created_by_moment=moment_id,
        display_mode=CardDisplayMode(card_config.get("display_mode", "floating")),
        priority=card_config.get("priority", 50),
        content=content,
        dynamic_fields=dynamic_fields,
        dismiss_when=lifecycle_config.get("dismiss_when"),
        auto_dismiss_seconds=lifecycle_config.get("auto_dismiss_seconds"),
        dismiss_on_action=lifecycle_config.get("dismiss_on_action"),
        actions=actions,
    )


def _resolve_path(path: str, context: Dict[str, Any]) -> Any:
    """Resolve a dot-notation path against context."""
    parts = path.split(".")
    value = context
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part)
        elif hasattr(value, part):
            value = getattr(value, part)
        else:
            return None
        if value is None:
            return None
    return value
