"""
Unified State Service - Single source of truth for state management

This service unifies Child (invariant data) and UserSession (interaction state)
into a single interface. It replaces both:
- SessionService (conversation + extracted data)
- MockGraphiti/FamilyState (UI state + in-memory data)

Design:
- Child data is shared across users (one child_id = one Child)
- Session data is per-user (user_id + child_id = one UserSession)
- For now, user_id defaults to child_id (single-user mode)

The service provides backwards-compatible APIs so existing code continues to work
while we migrate to the new architecture.
"""

import logging
import os
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.models.child import Child, DevelopmentalData, Video, JournalEntry
from app.models.user_session import UserSession, ConversationMessage, create_session_id
from app.models.active_card import ActiveCard
from app.models.artifact import Artifact
from app.models.family_state import (
    FamilyState,
    Message as FamilyMessage,
    Artifact as FamilyArtifact,
    Video as FamilyVideo,
)
from app.services.child_service import get_child_service, ChildService
from app.services.session_persistence import get_session_persistence, SessionPersistence
from app.services.llm.factory import create_llm_provider
from app.services.llm.base import Message
from app.prompts.completeness_verification import build_completeness_verification_prompt

logger = logging.getLogger(__name__)


class UnifiedStateService:
    """
    Unified state management combining Child and UserSession.

    Provides:
    - Child data management (developmental data, artifacts, videos)
    - Session management (conversation, UI state)
    - Backwards-compatible APIs for existing code

    This is the SINGLE source of truth, replacing both SessionService and MockGraphiti.
    """

    def __init__(self):
        # Services
        self._child_service = get_child_service()
        self._persistence = get_session_persistence()

        # In-memory session cache: session_id -> UserSession
        self._sessions: Dict[str, UserSession] = {}

        # LLM for semantic verification
        strong_model = os.getenv("STRONG_LLM_MODEL", "gemini-2.0-flash-exp")
        provider_type = os.getenv("LLM_PROVIDER", "gemini")
        self._verification_llm = create_llm_provider(
            provider_type=provider_type,
            model=strong_model,
            use_enhanced=False
        )

        logger.info("UnifiedStateService initialized")

    # === Session Management ===

    def get_or_create_session(
        self,
        family_id: str,
        user_id: Optional[str] = None
    ) -> UserSession:
        """
        Get or create a user session.

        Args:
            family_id: Child identifier (for backwards compatibility)
            user_id: User identifier (defaults to family_id for single-user mode)

        Returns:
            UserSession for this user and child
        """
        # For now, user_id defaults to family_id (single-user mode)
        user_id = user_id or family_id
        child_id = family_id

        session_id = create_session_id(user_id, child_id)

        if session_id not in self._sessions:
            # Try to load from persistence
            session = self._load_session_sync(session_id)
            if session:
                self._sessions[session_id] = session
                logger.info(f"Loaded session {session_id} from persistence")
            else:
                # Create new session
                self._sessions[session_id] = UserSession(
                    session_id=session_id,
                    user_id=user_id,
                    child_id=child_id
                )
                logger.info(f"Created new session: {session_id}")

        return self._sessions[session_id]

    async def get_or_create_session_async(
        self,
        family_id: str,
        user_id: Optional[str] = None
    ) -> UserSession:
        """Async version of get_or_create_session"""
        user_id = user_id or family_id
        child_id = family_id
        session_id = create_session_id(user_id, child_id)

        if session_id not in self._sessions:
            session = await self._load_session(session_id)
            if session:
                self._sessions[session_id] = session
            else:
                self._sessions[session_id] = UserSession(
                    session_id=session_id,
                    user_id=user_id,
                    child_id=child_id
                )

        return self._sessions[session_id]

    # === Child Data Access (Convenience Methods) ===

    def get_child(self, family_id: str) -> Child:
        """Get child data (creates if not exists)"""
        return self._child_service.get_or_create_child(family_id)

    def get_extracted_data(self, family_id: str) -> DevelopmentalData:
        """Get child's developmental data (backwards compatible with SessionState.extracted_data)"""
        return self.get_child(family_id).developmental_data

    def get_completeness(self, family_id: str) -> float:
        """Get data completeness score"""
        return self.get_child(family_id).data_completeness

    # === Backwards-Compatible APIs ===
    # These match the old SessionService API for easy migration

    def update_extracted_data(
        self,
        family_id: str,
        new_data: Dict[str, Any]
    ) -> DevelopmentalData:
        """Update extracted data (backwards compatible)"""
        return self._child_service.update_developmental_data(family_id, new_data)

    def calculate_completeness(self, family_id: str) -> float:
        """Calculate completeness (backwards compatible)"""
        return self._child_service.calculate_completeness(family_id)

    def add_conversation_turn(
        self,
        family_id: str,
        role: str,
        content: str
    ):
        """Add a conversation turn (backwards compatible)"""
        session = self.get_or_create_session(family_id)
        session.add_message(role, content)

        # Persist asynchronously
        asyncio.create_task(self._persist_session(session))

    async def add_conversation_turn_async(
        self,
        family_id: str,
        role: str,
        content: str
    ):
        """Async version: Add a conversation turn"""
        session = await self.get_or_create_session_async(family_id)
        session.add_message(role, content)
        await self._persist_session(session)

    def get_conversation_history(
        self,
        family_id: str,
        last_n: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """Get conversation history (backwards compatible)"""
        session = self.get_or_create_session(family_id)
        return session.get_conversation_history(last_n)

    def get_context_summary(self, family_id: str) -> str:
        """Get text summary of what's been collected (backwards compatible)"""
        data = self.get_extracted_data(family_id)

        parts = []
        if data.child_name:
            parts.append(f"Child's name: {data.child_name}")
        if data.age:
            parts.append(f"Age: {data.age} years")
        if data.gender and data.gender != "unknown":
            parts.append(f"Gender: {data.gender}")
        if data.primary_concerns:
            parts.append(f"Concerns: {', '.join(data.primary_concerns)}")
        if data.strengths:
            parts.append(f"Strengths: {data.strengths[:100]}")

        return ". ".join(parts) if parts else "No information collected yet."

    # === Artifact Management (Backwards Compatible) ===

    def get_artifact(self, family_id: str, artifact_id: str) -> Optional[Artifact]:
        """Get artifact by ID"""
        return self._child_service.get_artifact(family_id, artifact_id)

    def has_artifact(self, family_id: str, artifact_id: str) -> bool:
        """Check if artifact exists and is ready"""
        return self._child_service.has_artifact(family_id, artifact_id)

    def add_artifact(self, family_id: str, artifact: Artifact):
        """Add an artifact"""
        self._child_service.add_artifact(family_id, artifact)

    # === UI State Management ===

    def get_active_cards(self, family_id: str) -> List[ActiveCard]:
        """Get active UI cards"""
        session = self.get_or_create_session(family_id)
        return session.active_cards

    def add_active_card(self, family_id: str, card: ActiveCard):
        """Add an active card"""
        session = self.get_or_create_session(family_id)
        session.add_card(card)
        asyncio.create_task(self._persist_session(session))

    def remove_active_card(self, family_id: str, card_id: str):
        """Remove an active card"""
        session = self.get_or_create_session(family_id)
        session.remove_card(card_id)
        asyncio.create_task(self._persist_session(session))

    def dismiss_moment(self, family_id: str, moment_id: str):
        """Mark a moment as dismissed"""
        session = self.get_or_create_session(family_id)
        session.dismiss_moment(moment_id)
        asyncio.create_task(self._persist_session(session))

    def is_moment_dismissed(self, family_id: str, moment_id: str) -> bool:
        """Check if moment has been dismissed"""
        session = self.get_or_create_session(family_id)
        return session.is_moment_dismissed(moment_id)

    def get_dismissed_card_moments(self, family_id: str) -> Dict[str, datetime]:
        """Get all dismissed moments"""
        session = self.get_or_create_session(family_id)
        return session.dismissed_card_moments

    def get_previous_context_snapshot(self, family_id: str) -> Optional[Dict[str, Any]]:
        """Get previous context snapshot for transition detection"""
        session = self.get_or_create_session(family_id)
        return session.previous_context_snapshot

    def set_previous_context_snapshot(self, family_id: str, snapshot: Dict[str, Any]):
        """Set previous context snapshot"""
        session = self.get_or_create_session(family_id)
        session.previous_context_snapshot = snapshot
        asyncio.create_task(self._persist_session(session))

    def get_last_triggered_moment(self, family_id: str) -> Optional[Dict[str, Any]]:
        """Get last triggered moment"""
        session = self.get_or_create_session(family_id)
        return session.last_triggered_moment

    def set_last_triggered_moment(self, family_id: str, moment: Dict[str, Any]):
        """Set last triggered moment"""
        session = self.get_or_create_session(family_id)
        session.last_triggered_moment = moment
        asyncio.create_task(self._persist_session(session))

    # === Video Management ===

    def add_video(self, family_id: str, video: Video):
        """Add a video"""
        self._child_service.add_video(family_id, video)

    def get_video(self, family_id: str, video_id: str) -> Optional[Video]:
        """Get video by ID"""
        return self._child_service.get_video(family_id, video_id)

    def get_videos(self, family_id: str) -> List[Video]:
        """Get all videos"""
        return self.get_child(family_id).videos

    def get_videos_pending_analysis(self, family_id: str) -> List[Video]:
        """Get videos pending analysis"""
        return self._child_service.get_videos_pending_analysis(family_id)

    # === FamilyState View (replaces MockGraphiti.get_or_create_state) ===

    def get_family_state(self, family_id: str) -> FamilyState:
        """
        Build FamilyState view from Child and UserSession.

        This replaces MockGraphiti.get_or_create_state() and provides
        the same FamilyState model for backwards compatibility.
        """
        child = self.get_child(family_id)
        session = self.get_or_create_session(family_id)
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
            conversation.append(FamilyMessage(
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp
            ))

        # Convert artifacts from exploration cycles
        artifacts = {}
        for cycle in child.exploration_cycles:
            for artifact in cycle.artifacts:
                artifacts[artifact.id] = FamilyArtifact(
                    type=artifact.type,
                    content=artifact.content,
                    created_at=artifact.created_at
                )

        # Convert videos
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

        # Build and return FamilyState
        return FamilyState(
            family_id=family_id,
            child=child_dict,
            parent=None,
            conversation=conversation,
            artifacts=artifacts,
            videos_uploaded=videos,
            journal_entries=[],
            created_at=child.created_at,
            last_active=session.updated_at,
            active_cards=session.active_cards,
            dismissed_card_moments={
                k: v for k, v in session.dismissed_card_moments.items()
            },
            previous_context_snapshot=session.previous_context_snapshot,
        )

    # === Semantic Verification ===

    async def verify_semantic_completeness(self, family_id: str) -> Dict[str, Any]:
        """Verify completeness using LLM semantic understanding"""
        child = self.get_child(family_id)
        session = self.get_or_create_session(family_id)
        data = child.developmental_data

        extracted_dict = {
            'child_name': data.child_name,
            'age': data.age,
            'gender': data.gender,
            'primary_concerns': data.primary_concerns,
            'concern_details': data.concern_details,
            'strengths': data.strengths,
            'developmental_history': data.developmental_history,
            'family_context': data.family_context,
            'daily_routines': data.daily_routines,
            'parent_goals': data.parent_goals,
        }

        conversation_history = session.get_conversation_history()

        prompt = build_completeness_verification_prompt(
            extracted_data=extracted_dict,
            conversation_history=conversation_history
        )

        try:
            logger.info(f"Running semantic completeness verification for {family_id}")

            response = await self._verification_llm.chat(
                messages=[Message(role="user", content=prompt)],
                temperature=0.1,
                max_tokens=2000,
                response_format="json"
            )

            import json
            result = json.loads(response.content)

            logger.info(f"Semantic verification complete: {result.get('overall_completeness', 0)}%")

            # Cache result in session
            turn_count = session.turn_count
            session.semantic_verification = result
            session.semantic_verification_turn = turn_count

            # Also update child's semantic verification
            child.semantic_verification = result

            return result

        except Exception as e:
            logger.error(f"Error in semantic verification: {e}")
            return {
                "overall_completeness": child.data_completeness * 100,
                "recommendation": "continue_conversation",
                "error": str(e)
            }

    # === Session Stats (Backwards Compatible) ===

    def get_session_stats(self, family_id: str) -> Dict[str, Any]:
        """Get session statistics (backwards compatible)"""
        child = self.get_child(family_id)
        session = self.get_or_create_session(family_id)
        data = child.developmental_data

        return {
            "family_id": family_id,
            "completeness": child.data_completeness,
            "completeness_pct": f"{child.data_completeness:.1%}",
            "extraction_count": data.extraction_count,
            "conversation_turns": session.message_count,
            "video_guidelines_ready": child.has_artifact("baseline_video_guidelines"),
            "has_child_name": bool(data.child_name),
            "has_age": bool(data.age),
            "concerns_count": len(data.primary_concerns),
            "urgent_flags_count": len(data.urgent_flags),
            "created_at": child.created_at.isoformat(),
            "updated_at": child.updated_at.isoformat()
        }

    def get_extraction_quality(self, family_id: str) -> Dict[str, Any]:
        """Get extraction quality metrics (backwards compatible)"""
        child = self.get_child(family_id)
        session = self.get_or_create_session(family_id)
        data = child.developmental_data
        turns = session.message_count

        quality = {
            'has_name': bool(data.child_name),
            'has_age': bool(data.age),
            'has_gender': bool(data.gender and data.gender != 'unknown'),
            'has_concerns': len(data.primary_concerns) > 0,
            'concern_count': len(data.primary_concerns),
            'has_concern_details': bool(data.concern_details),
            'has_strengths': bool(data.strengths),
            'has_developmental_history': bool(data.developmental_history),
            'has_family_context': bool(data.family_context),
            'turns_count': turns,
            'extraction_count': data.extraction_count,
            'completeness': child.data_completeness,
            'warnings': []
        }

        if turns >= 6:
            if not quality['has_name']:
                quality['warnings'].append("Child name not extracted after 3+ turns")
            if not quality['has_age']:
                quality['warnings'].append("Child age not extracted after 3+ turns")
            if not quality['has_concerns']:
                quality['warnings'].append("No primary concerns extracted after 3+ turns")

        quality['basic_info_complete'] = quality['has_name'] and quality['has_age']
        quality['concerns_captured'] = quality['has_concerns'] and quality['has_concern_details']

        return quality

    # === Context Building (For Conversation Service) ===

    def build_full_context(self, family_id: str) -> Dict[str, Any]:
        """
        Build complete context for the conversation service.

        This replaces the need for separate FamilyState and SessionState.
        """
        child = self.get_child(family_id)
        session = self.get_or_create_session(family_id)
        data = child.developmental_data

        return {
            # Child profile
            "child": {
                "name": data.child_name,
                "age": data.age,
                "gender": data.gender,
            },
            # Developmental data
            "extracted_data": {
                "child_name": data.child_name,
                "age": data.age,
                "gender": data.gender,
                "primary_concerns": data.primary_concerns,
                "concern_details": data.concern_details,
                "strengths": data.strengths,
                "developmental_history": data.developmental_history,
                "family_context": data.family_context,
                "daily_routines": data.daily_routines,
                "parent_goals": data.parent_goals,
                "filming_preference": data.filming_preference,
            },
            # Completeness
            "completeness": child.data_completeness,
            # Artifacts - built from exploration cycles
            "artifacts": {
                artifact.id: artifact.model_dump()
                for cycle in child.exploration_cycles
                for artifact in cycle.artifacts
            },
            "has_video_guidelines": child.has_artifact("baseline_video_guidelines"),
            # Videos
            "videos": [v.model_dump() for v in child.videos],
            "video_count": child.video_count,
            "analyzed_video_count": child.analyzed_video_count,
            # UI state
            "active_cards": [c.model_dump() for c in session.active_cards],
            "dismissed_card_moments": {
                k: v.isoformat() for k, v in session.dismissed_card_moments.items()
            },
            # Session info
            "conversation_turns": session.message_count,
            "last_triggered_moment": session.last_triggered_moment,
        }

    # === Persistence Helpers ===

    def _load_session_sync(self, session_id: str) -> Optional[UserSession]:
        """Synchronous load for initialization"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._load_session(session_id))
                    return future.result(timeout=5)
            else:
                return loop.run_until_complete(self._load_session(session_id))
        except Exception as e:
            logger.warning(f"Could not load session synchronously: {e}")
            return None

    async def _load_session(self, session_id: str) -> Optional[UserSession]:
        """Load session from persistence"""
        data = await self._persistence.load_session(session_id)
        if not data:
            return None

        try:
            # Reconstruct UserSession
            session = UserSession(
                session_id=session_id,
                user_id=data.get("user_id", session_id.split(":")[0]),
                child_id=data.get("child_id", session_id.split(":")[-1]),
            )

            # Restore messages
            for msg_data in data.get("messages", []):
                session.messages.append(ConversationMessage(**msg_data))

            # Restore UI state
            for card_data in data.get("active_cards", []):
                session.active_cards.append(ActiveCard(**card_data))

            session.dismissed_card_moments = data.get("dismissed_card_moments", {})
            session.previous_context_snapshot = data.get("previous_context_snapshot")
            session.last_triggered_moment = data.get("last_triggered_moment")
            session.semantic_verification = data.get("semantic_verification")
            session.semantic_verification_turn = data.get("semantic_verification_turn", 0)

            # Restore timestamps
            if data.get("created_at"):
                session.created_at = datetime.fromisoformat(data["created_at"])
            if data.get("updated_at"):
                session.updated_at = datetime.fromisoformat(data["updated_at"])
            if data.get("last_message_at"):
                session.last_message_at = datetime.fromisoformat(data["last_message_at"])

            return session

        except Exception as e:
            logger.error(f"Error reconstructing session {session_id}: {e}")
            return None

    async def _persist_session(self, session: UserSession):
        """Persist session to storage"""
        try:
            session_data = {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "child_id": session.child_id,
                "messages": [m.model_dump() for m in session.messages],
                "active_cards": [c.model_dump() for c in session.active_cards],
                "dismissed_card_moments": {
                    k: v.isoformat() for k, v in session.dismissed_card_moments.items()
                },
                "previous_context_snapshot": session.previous_context_snapshot,
                "last_triggered_moment": session.last_triggered_moment,
                "semantic_verification": session.semantic_verification,
                "semantic_verification_turn": session.semantic_verification_turn,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "last_message_at": session.last_message_at.isoformat() if session.last_message_at else None,
            }

            await self._persistence.save_session(session.session_id, session_data)

        except Exception as e:
            logger.warning(f"Failed to persist session: {e}")


# Singleton
_unified_service: Optional[UnifiedStateService] = None


def get_unified_state_service() -> UnifiedStateService:
    """Get singleton UnifiedStateService instance"""
    global _unified_service
    if _unified_service is None:
        _unified_service = UnifiedStateService()
    return _unified_service


# Backwards compatibility aliases
def get_session_service() -> UnifiedStateService:
    """DEPRECATED: Use get_unified_state_service() instead"""
    return get_unified_state_service()
