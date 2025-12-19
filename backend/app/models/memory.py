"""
Conversation Memory Models

The Gestalt captures the child's journey.
Memory captures the relationship's journey - how we converse with this parent.

This is distilled from conversation, not stored verbatim.
Old messages become structured understanding.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class TopicCovered(BaseModel):
    """A topic we've discussed with this parent."""
    topic: str  # "motor_concerns", "strengths", "family_history", "transitions"
    discussed_at: datetime = Field(default_factory=datetime.now)
    depth: str = "mentioned"  # "mentioned", "explored", "deep_dive"

    def deepen(self, new_depth: str):
        """Update depth if going deeper."""
        depth_order = {"mentioned": 0, "explored": 1, "deep_dive": 2}
        if depth_order.get(new_depth, 0) > depth_order.get(self.depth, 0):
            self.depth = new_depth
            self.discussed_at = datetime.now()


class ConversationMemory(BaseModel):
    """
    What we remember about conversing with this parent.

    This is relationship memory - how they communicate, what we've covered.
    Updated by reflection, not every message.
    """

    # Communication style (discovered through reflection)
    parent_style: Optional[str] = None  # "anxious, needs reassurance", "direct, practical"
    emotional_patterns: Optional[str] = None  # "opens up slowly", "shares deeply when comfortable"

    # Vocabulary they use (for mirroring)
    vocabulary_preferences: List[str] = Field(default_factory=list)  # ["מתפוצץ", "מרחף"]

    # What we've covered (prevents repetition)
    topics_discussed: List[TopicCovered] = Field(default_factory=list)

    # Relationship notes
    rapport_notes: Optional[str] = None  # "Built trust after discussing fears openly"

    # Context assets mentioned (specific toys, people, places)
    context_assets: List[str] = Field(default_factory=list)  # ["סבתא רחל", "לגו נינג'ה"]

    # Updated by reflection
    updated_at: datetime = Field(default_factory=datetime.now)

    def get_topic(self, topic: str) -> Optional[TopicCovered]:
        """Get topic if discussed."""
        return next((t for t in self.topics_discussed if t.topic == topic), None)

    def mark_topic_discussed(self, topic: str, depth: str = "mentioned"):
        """Mark a topic as discussed or deepen existing."""
        existing = self.get_topic(topic)
        if existing:
            existing.deepen(depth)
        else:
            self.topics_discussed.append(TopicCovered(topic=topic, depth=depth))
        self.updated_at = datetime.now()

    def topics_at_depth(self, min_depth: str = "mentioned") -> List[str]:
        """Get topics discussed at minimum depth."""
        depth_order = {"mentioned": 0, "explored": 1, "deep_dive": 2}
        min_order = depth_order.get(min_depth, 0)
        return [
            t.topic for t in self.topics_discussed
            if depth_order.get(t.depth, 0) >= min_order
        ]

    def add_vocabulary(self, word: str):
        """Add parent's vocabulary if not already tracked."""
        if word not in self.vocabulary_preferences:
            self.vocabulary_preferences.append(word)
            self.updated_at = datetime.now()

    def add_context_asset(self, asset: str):
        """Add context asset if not already tracked."""
        if asset not in self.context_assets:
            self.context_assets.append(asset)
            self.updated_at = datetime.now()

    def update_style(self, style: str):
        """Update communication style observation."""
        self.parent_style = style
        self.updated_at = datetime.now()

    def update_emotional_patterns(self, patterns: str):
        """Update emotional patterns observation."""
        self.emotional_patterns = patterns
        self.updated_at = datetime.now()

    def update_rapport(self, notes: str):
        """Update rapport notes."""
        self.rapport_notes = notes
        self.updated_at = datetime.now()
