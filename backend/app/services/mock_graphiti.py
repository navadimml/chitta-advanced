"""
Mock Graphiti - Simulates Temporal Knowledge Graph
Actually just smart state management that looks like Graphiti
"""
from typing import Dict, Optional
from datetime import datetime
import json
from ..models.family_state import FamilyState, Message, Artifact


class MockGraphiti:
    """
    Simulates Graphiti's temporal knowledge graph.
    Provides Graphiti-like query interface but uses simple state storage.
    """

    def __init__(self):
        self.states: Dict[str, FamilyState] = {}

    def get_or_create_state(self, family_id: str) -> FamilyState:
        """Get existing state or create new one"""
        if family_id not in self.states:
            self.states[family_id] = FamilyState(
                family_id=family_id,
                created_at=datetime.now(),
                last_active=datetime.now()
            )
        return self.states[family_id]

    async def add_message(
        self,
        family_id: str,
        role: str,
        content: str,
        timestamp: Optional[datetime] = None
    ):
        """Add a message to conversation"""
        state = self.get_or_create_state(family_id)

        message = Message(
            role=role,
            content=content,
            timestamp=timestamp or datetime.now()
        )

        state.conversation.append(message)
        state.last_active = datetime.now()

        # Extract entities from message
        await self._extract_entities(state, content)

    async def add_artifact(
        self,
        family_id: str,
        artifact_type: str,
        content: dict
    ):
        """Add an artifact to state"""
        state = self.get_or_create_state(family_id)

        artifact = Artifact(
            type=artifact_type,
            content=content,
            created_at=datetime.now()
        )

        state.artifacts[artifact_type] = artifact
        state.last_active = datetime.now()

    async def query(
        self,
        family_id: str,
        query: str
    ) -> dict:
        """
        Simulate Graphiti's semantic search.
        Returns relevant parts of state based on query.
        """
        state = self.states.get(family_id)
        if not state:
            return {}

        query_lower = query.lower()

        # Query interpretation
        if "video" in query_lower:
            return {
                "videos_uploaded": [v.dict() for v in state.videos_uploaded],
                "videos_count": len(state.videos_uploaded),
                "videos_needed": 3 - len(state.videos_uploaded)
            }

        if "guideline" in query_lower:
            guidelines = state.artifacts.get("baseline_video_guidelines")
            return {
                "guidelines": guidelines.dict() if guidelines else None
            }

        if "conversation" in query_lower or "history" in query_lower:
            return {
                "messages": [m.dict() for m in state.conversation[-10:]]
            }

        if "artifact" in query_lower or "report" in query_lower:
            return {
                "artifacts": {k: v.dict() for k, v in state.artifacts.items()}
            }

        # Return full state for complex queries
        return state.dict()

    async def _extract_entities(self, state: FamilyState, text: str):
        """Extract entities from text and update state (simplified)"""
        text_lower = text.lower()

        # Extract child name
        if "שמו" in text or "שמה" in text:
            # Simple extraction - in real version would use LLM
            words = text.split()
            for i, word in enumerate(words):
                if word in ["שמו", "שמה"] and i + 1 < len(words):
                    child_name = words[i + 1].rstrip(',').rstrip('.')
                    if not state.child:
                        state.child = {}
                    state.child["name"] = child_name
                    break

        # Extract age
        if "בן" in text or "בת" in text:
            words = text.split()
            for i, word in enumerate(words):
                if word in ["בן", "בת"] and i + 1 < len(words):
                    try:
                        age_str = words[i + 1].rstrip(',').rstrip('.')
                        # Handle "3.5" or "3 וחצי"
                        if "וחצי" in text:
                            age = float(age_str) + 0.5
                        else:
                            age = float(age_str)
                        if not state.child:
                            state.child = {}
                        state.child["age"] = age
                    except ValueError:
                        pass
                    break


# Global instance
_mock_graphiti_instance = None


def get_mock_graphiti() -> MockGraphiti:
    """Get singleton instance"""
    global _mock_graphiti_instance
    if _mock_graphiti_instance is None:
        _mock_graphiti_instance = MockGraphiti()
    return _mock_graphiti_instance
