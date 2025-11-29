"""
Mock Graphiti - Simulates Temporal Knowledge Graph

🌟 MIGRATION NOTE: This module now delegates to UnifiedStateService for
the actual state storage. FamilyState is now a view that combines data
from Child (shared) and UserSession (per-user).

This maintains backwards compatibility with existing code while using
the new unified storage underneath.
"""
from typing import Dict, Optional
from datetime import datetime
import json
import logging
from ..models.family_state import FamilyState, Message, Artifact

logger = logging.getLogger(__name__)


class MockGraphiti:
    """
    Simulates Graphiti's temporal knowledge graph.

    🌟 MIGRATION: Now delegates to UnifiedStateService internally.
    FamilyState is built dynamically from Child + UserSession.
    """

    def __init__(self):
        # Cache for FamilyState views (rebuilt from unified service on access)
        self._state_cache: Dict[str, FamilyState] = {}
        self._unified_service = None  # Lazy initialization to avoid circular imports

    def _get_unified_service(self):
        """Lazy load unified service to avoid circular imports"""
        if self._unified_service is None:
            from app.services.unified_state_service import get_unified_state_service
            self._unified_service = get_unified_state_service()
        return self._unified_service

    def get_or_create_state(self, family_id: str) -> FamilyState:
        """
        Get existing state or create new one.

        🌟 MIGRATION: Now builds FamilyState from Child + UserSession data
        """
        # Get unified service
        unified = self._get_unified_service()

        # Get child and session data
        child = unified.get_child(family_id)
        session = unified.get_or_create_session(family_id)

        # Check if we have a cached state and if it's current
        if family_id in self._state_cache:
            cached = self._state_cache[family_id]
            # Use cached version if it exists and was updated recently
            # (within same request cycle - we update on each access)
            logger.debug(f"♻️ Using cached state for {family_id}")
        else:
            logger.info(f"🔄 Building state from unified service for {family_id}")

        # Build/update FamilyState from unified data
        state = self._build_family_state(family_id, child, session)
        self._state_cache[family_id] = state

        conv_count = len(state.conversation)
        if conv_count > 0:
            logger.info(f"♻️ State loaded for {family_id} ({conv_count} messages)")
        else:
            logger.info(f"🆕 New state for {family_id}")

        return state

    def _build_family_state(self, family_id: str, child, session) -> FamilyState:
        """Build FamilyState view from Child and UserSession"""
        data = child.developmental_data

        # Build child dict for profile
        child_dict = None
        if data.child_name or data.age:
            child_dict = {
                "name": data.child_name,
                "age": data.age,
            }
            if data.gender:
                child_dict["gender"] = data.gender

        # Convert messages to FamilyState Message format
        conversation = []
        for msg in session.messages:
            conversation.append(Message(
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp
            ))

        # Convert artifacts
        artifacts = {}
        for artifact_id, artifact in child.artifacts.items():
            artifacts[artifact_id] = Artifact(
                type=artifact.artifact_type,
                content=artifact.content if isinstance(artifact.content, dict) else {"data": artifact.content},
                created_at=artifact.created_at
            )

        # Convert videos
        from ..models.family_state import Video as FamilyVideo
        videos = []
        for video in child.videos:
            videos.append(FamilyVideo(
                id=video.id,
                scenario=video.scenario,
                uploaded_at=video.uploaded_at,
                duration_seconds=video.duration_seconds,
                file_path=video.file_path,
                file_url=video.file_url,
                analyst_context=video.observation_context,
                analysis_status=video.analysis_status,
                analysis_artifact_id=video.analysis_artifact_id,
                analysis_error=video.analysis_error,
            ))

        # Build FamilyState
        state = FamilyState(
            family_id=family_id,
            child=child_dict,
            parent=None,  # Not used in current implementation
            conversation=conversation,
            artifacts=artifacts,
            videos_uploaded=videos,
            journal_entries=[],  # TODO: Convert journal entries if needed
            created_at=child.created_at,
            last_active=session.updated_at,
            active_cards=session.active_cards,
            dismissed_card_moments={
                k: v for k, v in session.dismissed_card_moments.items()
            },
            previous_context_snapshot=session.previous_context_snapshot,
        )

        return state

    async def add_message(
        self,
        family_id: str,
        role: str,
        content: str,
        timestamp: Optional[datetime] = None
    ):
        """
        Add a message to conversation.

        🌟 MIGRATION: Delegates to unified service
        """
        unified = self._get_unified_service()
        await unified.add_conversation_turn_async(family_id, role, content)

        # Invalidate cache so next access rebuilds state
        if family_id in self._state_cache:
            del self._state_cache[family_id]

        # Note: Entity extraction is now handled by the conversation service
        # through the extraction functions, not here

    async def add_artifact(
        self,
        family_id: str,
        artifact_type: str,
        content: dict
    ):
        """
        Add an artifact to state.

        🌟 MIGRATION: Delegates to unified service
        """
        from app.models.artifact import Artifact as ArtifactModel

        unified = self._get_unified_service()

        # Create artifact using the proper model
        artifact = ArtifactModel(
            artifact_id=artifact_type,
            artifact_type=artifact_type,
            content=content,
            created_at=datetime.now(),
            is_ready=True
        )

        unified.add_artifact(family_id, artifact)

        # Invalidate cache
        if family_id in self._state_cache:
            del self._state_cache[family_id]

    async def query(
        self,
        family_id: str,
        query: str
    ) -> dict:
        """
        Simulate Graphiti's semantic search.
        Returns relevant parts of state based on query.

        🌟 MIGRATION: Uses unified service data
        """
        unified = self._get_unified_service()
        child = unified.get_child(family_id)
        session = unified.get_or_create_session(family_id)

        query_lower = query.lower()

        # Query interpretation
        if "video" in query_lower:
            return {
                "videos_uploaded": [v.dict() for v in child.videos],
                "videos_count": child.video_count,
                "videos_needed": max(0, 3 - child.video_count)
            }

        if "guideline" in query_lower:
            guidelines = child.get_artifact("baseline_video_guidelines")
            return {
                "guidelines": guidelines.dict() if guidelines else None
            }

        if "conversation" in query_lower or "history" in query_lower:
            return {
                "messages": session.get_conversation_history(last_n=10)
            }

        if "artifact" in query_lower or "report" in query_lower:
            return {
                "artifacts": {k: v.dict() for k, v in child.artifacts.items()}
            }

        # Return full context for complex queries
        return unified.build_full_context(family_id)

    async def _extract_entities(self, state: FamilyState, text: str):
        """
        DEPRECATED: Entity extraction is now handled by conversation service.
        This method is kept for backwards compatibility but does nothing.
        """
        # Entity extraction is now done by the conversation service
        # through its extraction functions and stored in Child.developmental_data
        pass


# Global instance
_mock_graphiti_instance = None


def get_mock_graphiti() -> MockGraphiti:
    """Get singleton instance"""
    global _mock_graphiti_instance
    if _mock_graphiti_instance is None:
        _mock_graphiti_instance = MockGraphiti()
    return _mock_graphiti_instance
