"""
User Session Model - Per-User Interaction State

Each user has their own session for each child they interact with.
This keeps conversation history and UI state separate between users.

Design principles:
- Sessions are per-user, per-child
- Conversation history is personal (each user has their own)
- UI state (cards, dismissed items) is personal
- Child data is shared (referenced, not duplicated)

Sliding Window Architecture:
- Keep last WINDOW_SIZE messages in active history
- Older messages are archived (for reflection access)
- ConversationMemory stores distilled relationship knowledge
- Reflection updates memory periodically
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime

from .active_card import ActiveCard
from .memory import ConversationMemory

# Configuration
SLIDING_WINDOW_SIZE = 25  # Messages to keep in active context
REFLECTION_TRIGGER_TURNS = 5  # Trigger reflection every N turns


class ConversationMessage(BaseModel):
    """A single message in the conversation"""
    role: str  # "user" | "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    archived: bool = False  # True when moved out of active window


class UserSession(BaseModel):
    """
    A user's interaction session with a specific child.

    Stores:
    - Conversation history (sliding window + archived)
    - Conversation memory (distilled relationship knowledge)
    - UI state (active cards, dismissed items, view preferences)
    - Reflection tracking (when to trigger background processing)

    Does NOT store:
    - Child data (that's in the Child model)
    - Artifacts (those belong to the child)
    """
    session_id: str = Field(description="Unique session identifier")
    user_id: str = Field(description="User identifier (device ID for now)")
    child_id: str = Field(description="Child this session is about")

    # === Conversation (Sliding Window) ===
    messages: List[ConversationMessage] = Field(
        default_factory=list,
        description="All messages (active window + archived)"
    )

    # === Conversation Memory (Distilled Knowledge) ===
    memory: ConversationMemory = Field(
        default_factory=ConversationMemory,
        description="Distilled relationship memory from reflection"
    )

    # === Reflection Tracking ===
    last_reflection_turn: int = Field(
        default=0,
        description="Turn count at last reflection"
    )
    pending_reflection: bool = Field(
        default=False,
        description="Whether reflection is queued/in-progress"
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
        """Add a message to the conversation and manage window."""
        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=datetime.now()
        )
        self.messages.append(message)
        self.last_message_at = message.timestamp
        self.updated_at = datetime.now()

        # Manage sliding window - archive old messages
        self._apply_sliding_window()

        return message

    def _apply_sliding_window(self):
        """Archive messages outside the active window."""
        active_messages = [m for m in self.messages if not m.archived]
        if len(active_messages) > SLIDING_WINDOW_SIZE:
            # Mark oldest messages as archived
            to_archive = len(active_messages) - SLIDING_WINDOW_SIZE
            archived_count = 0
            for msg in self.messages:
                if not msg.archived and archived_count < to_archive:
                    msg.archived = True
                    archived_count += 1

    def active_messages(self) -> List[ConversationMessage]:
        """Get messages in active window (not archived)."""
        return [m for m in self.messages if not m.archived]

    def archived_messages(self) -> List[ConversationMessage]:
        """Get archived messages (for reflection access)."""
        return [m for m in self.messages if m.archived]

    def get_conversation_history(
        self,
        last_n: Optional[int] = None,
        include_archived: bool = False
    ) -> List[Dict[str, str]]:
        """Get conversation history as list of dicts."""
        if include_archived:
            messages = self.messages
        else:
            messages = self.active_messages()

        if last_n:
            messages = messages[-last_n:]

        return [
            {
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp.isoformat()
            }
            for m in messages
        ]

    def get_context_for_llm(self) -> List[Dict[str, str]]:
        """
        Get conversation context optimized for LLM.

        Returns active window messages formatted for LLM context.
        Memory summary is handled separately in prompt building.
        """
        return [
            {"role": m.role, "content": m.content}
            for m in self.active_messages()
        ]

    @property
    def message_count(self) -> int:
        """Total number of messages (including archived)."""
        return len(self.messages)

    @property
    def active_message_count(self) -> int:
        """Number of messages in active window."""
        return len(self.active_messages())

    @property
    def turn_count(self) -> int:
        """Number of conversation turns (user messages)."""
        return len([m for m in self.messages if m.role == "user"])

    # === Reflection Management ===

    def needs_reflection(self) -> bool:
        """Check if reflection should be triggered."""
        if self.pending_reflection:
            return False  # Already queued
        turns_since_reflection = self.turn_count - self.last_reflection_turn
        return turns_since_reflection >= REFLECTION_TRIGGER_TURNS

    def mark_reflection_queued(self):
        """Mark that reflection has been queued."""
        self.pending_reflection = True
        self.updated_at = datetime.now()

    def mark_reflection_complete(self):
        """Mark that reflection has completed."""
        self.pending_reflection = False
        self.last_reflection_turn = self.turn_count
        self.updated_at = datetime.now()

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
