"""
User Session Model - Per-User Interaction State

Each user has their own session for each child they interact with.
This keeps conversation history and UI state separate between users.

Design principles:
- Sessions are per-user, per-child
- Conversation history is personal (each user has their own)
- UI state (cards, dismissed items) is personal
- Child data is shared (referenced, not duplicated)
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime

from .active_card import ActiveCard


class ConversationMessage(BaseModel):
    """A single message in the conversation"""
    role: str  # "user" | "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class UserSession(BaseModel):
    """
    A user's interaction session with a specific child.

    Stores:
    - Conversation history (this user's chat with Chitta about this child)
    - UI state (active cards, dismissed items, view preferences)
    - Moment tracking (for preventing duplicate triggers)

    Does NOT store:
    - Child data (that's in the Child model)
    - Artifacts (those belong to the child)
    """
    session_id: str = Field(description="Unique session identifier")
    user_id: str = Field(description="User identifier (device ID for now)")
    child_id: str = Field(description="Child this session is about")

    # === Conversation ===
    messages: List[ConversationMessage] = Field(
        default_factory=list,
        description="This user's conversation history about this child"
    )

    # === UI State (per-user, per-child) ===
    active_cards: List[ActiveCard] = Field(
        default_factory=list,
        description="Currently active UI cards for this user"
    )
    dismissed_card_moments: Dict[str, datetime] = Field(
        default_factory=dict,
        description="Moments that have been dismissed (moment_id -> dismissed_at)"
    )
    current_view: Optional[str] = Field(
        default=None,
        description="Current UI view/screen"
    )
    expanded_sections: List[str] = Field(
        default_factory=list,
        description="UI sections that are expanded"
    )

    # === Context Tracking ===
    previous_context_snapshot: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Snapshot for detecting state transitions"
    )
    last_triggered_moment: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Last triggered moment for continuity"
    )

    # === Semantic Verification Cache ===
    # (Cached per-session to avoid redundant LLM calls)
    semantic_verification: Optional[Dict[str, Any]] = None
    semantic_verification_turn: int = 0

    # === Metadata ===
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_message_at: Optional[datetime] = None

    # === Conversation Management ===

    def add_message(self, role: str, content: str) -> ConversationMessage:
        """Add a message to the conversation"""
        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=datetime.now()
        )
        self.messages.append(message)
        self.last_message_at = message.timestamp
        self.updated_at = datetime.now()
        return message

    def get_conversation_history(
        self,
        last_n: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """Get conversation history as list of dicts"""
        messages = self.messages[-last_n:] if last_n else self.messages
        return [
            {
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp.isoformat()
            }
            for m in messages
        ]

    @property
    def message_count(self) -> int:
        """Total number of messages"""
        return len(self.messages)

    @property
    def turn_count(self) -> int:
        """Number of conversation turns (user messages)"""
        return len([m for m in self.messages if m.role == "user"])

    # === Card Management ===

    def add_card(self, card: ActiveCard):
        """Add an active card"""
        # Remove existing card with same ID if present
        self.active_cards = [c for c in self.active_cards if c.card_id != card.card_id]
        self.active_cards.append(card)
        self.updated_at = datetime.now()

    def remove_card(self, card_id: str):
        """Remove a card by ID"""
        self.active_cards = [c for c in self.active_cards if c.card_id != card_id]
        self.updated_at = datetime.now()

    def get_card(self, card_id: str) -> Optional[ActiveCard]:
        """Get a card by ID"""
        return next((c for c in self.active_cards if c.card_id == card_id), None)

    def dismiss_moment(self, moment_id: str):
        """Mark a moment as dismissed"""
        self.dismissed_card_moments[moment_id] = datetime.now()
        self.updated_at = datetime.now()

    def is_moment_dismissed(self, moment_id: str) -> bool:
        """Check if a moment has been dismissed"""
        return moment_id in self.dismissed_card_moments

    # === Serialization helpers ===

    def to_legacy_conversation_history(self) -> List[Dict[str, str]]:
        """
        Convert to legacy format for compatibility.

        The old SessionState used a different format - this helps
        during the migration period.
        """
        return [
            {
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp.isoformat()
            }
            for m in self.messages
        ]


def create_session_id(user_id: str, child_id: str) -> str:
    """
    Create a session ID from user and child IDs.

    Session IDs are deterministic so we can find existing sessions.
    """
    return f"{user_id}:{child_id}"
