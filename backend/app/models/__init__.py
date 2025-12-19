"""
Chitta Data Models

Child-centric architecture:
- Child: The invariant core entity
- Understanding: Hypothesis-driven developmental understanding (Living Gestalt)
- Exploration: Cycles of exploration with artifacts
- Memory: Conversation/relationship memory
- UserSession: Per-user interaction state (conversation, UI state)
- ActiveCard: UI card state for the living dashboard
- Artifact: Generated reports, guidelines, analyses
"""

from .child import (
    Child,
    ChildIdentity,
    Essence,
    Strengths,
    Concerns,
    ConcernDetail,
    BirthHistory,
    PreviousEvaluation,
    DevelopmentalHistory,
    Sibling,
    FamilyContext,
    Video,
    JournalEntry,
)
from .understanding import (
    Evidence,
    Hypothesis,
    Pattern,
    PendingInsight,
    DevelopmentalUnderstanding,
)
from .exploration import (
    ExplorationCycle,
    CycleArtifact,
    VideoScenario,
    ConversationMethod,
    ConversationQuestion,
    VideoMethod,
)
from .memory import ConversationMemory, TopicCovered
from .user_session import UserSession, ConversationMessage, create_session_id
from .active_card import ActiveCard, CardDisplayMode, create_active_card
from .artifact import Artifact

__all__ = [
    # Core entities
    "Child",
    "ChildIdentity",
    "Essence",
    "Strengths",
    "Concerns",
    "ConcernDetail",
    "BirthHistory",
    "PreviousEvaluation",
    "DevelopmentalHistory",
    "Sibling",
    "FamilyContext",
    "Video",
    "JournalEntry",
    # Understanding (Living Gestalt)
    "Evidence",
    "Hypothesis",
    "Pattern",
    "PendingInsight",
    "DevelopmentalUnderstanding",
    # Exploration
    "ExplorationCycle",
    "CycleArtifact",
    "VideoScenario",
    "ConversationMethod",
    "ConversationQuestion",
    "VideoMethod",
    # Memory
    "ConversationMemory",
    "TopicCovered",
    # Session
    "UserSession",
    "ConversationMessage",
    "create_session_id",
    # UI state
    "ActiveCard",
    "CardDisplayMode",
    "create_active_card",
    # Artifacts
    "Artifact",
]
