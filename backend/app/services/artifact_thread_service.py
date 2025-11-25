"""
Artifact Thread Service - Living Documents conversation management.

Part of Living Dashboard Phase 3: Manages threaded conversations
attached to artifact sections.

This service:
1. Creates threads on artifact sections
2. Manages thread messages
3. Provides context for LLM responses
4. Persists threads alongside artifacts
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import json
from pathlib import Path

from app.models.artifact_thread import (
    ArtifactThread,
    ArtifactThreads,
    ThreadMessage,
    ThreadSummary
)
from app.models.structured_artifact import (
    StructuredArtifact,
    ArtifactSection,
    create_structured_artifact,
    parse_markdown_to_sections
)
from app.services.session_service import get_session_service

logger = logging.getLogger(__name__)


class ArtifactThreadService:
    """
    Service for managing threaded conversations on artifacts.

    Provides:
    - Thread creation on artifact sections
    - Message management within threads
    - Context building for LLM responses
    - Thread persistence
    """

    def __init__(self):
        self._threads_cache: Dict[str, ArtifactThreads] = {}  # artifact_id -> threads
        self._structured_cache: Dict[str, StructuredArtifact] = {}  # artifact_id -> structured

    # ==================
    # Thread Management
    # ==================

    async def create_thread(
        self,
        family_id: str,
        artifact_id: str,
        section_id: str,
        initial_question: str,
        section_title: Optional[str] = None,
        section_text: Optional[str] = None
    ) -> ArtifactThread:
        """
        Start a new thread on an artifact section.

        Args:
            family_id: Family identifier
            artifact_id: Artifact to attach thread to
            section_id: Section within artifact
            initial_question: User's first question
            section_title: Optional section title for context
            section_text: Optional section text for context

        Returns:
            Created ArtifactThread with first message
        """
        # Get or create threads collection for this artifact
        threads = self._get_or_create_threads(artifact_id, family_id)

        # Create new thread
        thread = ArtifactThread(
            family_id=family_id,
            artifact_id=artifact_id,
            section_id=section_id,
            section_title=section_title,
            section_text=section_text
        )

        # Add initial question
        thread.add_message("user", initial_question)

        # Add to collection
        threads.add_thread(thread)

        # Persist
        await self._save_threads(artifact_id, threads)

        logger.info(
            f"📝 Created thread {thread.thread_id} on {artifact_id}/{section_id} "
            f"for family {family_id}"
        )

        return thread

    async def add_message(
        self,
        thread_id: str,
        artifact_id: str,
        role: str,
        content: str
    ) -> Optional[ThreadMessage]:
        """
        Add a message to an existing thread.

        Args:
            thread_id: Thread to add message to
            artifact_id: Artifact the thread belongs to
            role: "user" or "assistant"
            content: Message content

        Returns:
            Created ThreadMessage or None if thread not found
        """
        threads = self._threads_cache.get(artifact_id)
        if not threads:
            logger.warning(f"No threads found for artifact {artifact_id}")
            return None

        thread = threads.get_thread(thread_id)
        if not thread:
            logger.warning(f"Thread {thread_id} not found")
            return None

        message = thread.add_message(role, content)

        # Update unresolved count
        threads.unresolved_threads = sum(1 for t in threads.threads if not t.is_resolved)

        # Persist
        await self._save_threads(artifact_id, threads)

        logger.info(f"💬 Added {role} message to thread {thread_id}")

        return message

    async def resolve_thread(
        self,
        thread_id: str,
        artifact_id: str
    ) -> bool:
        """
        Mark a thread as resolved (user understood/got it).

        Args:
            thread_id: Thread to resolve
            artifact_id: Artifact the thread belongs to

        Returns:
            True if resolved, False if not found
        """
        threads = self._threads_cache.get(artifact_id)
        if not threads:
            return False

        thread = threads.get_thread(thread_id)
        if not thread:
            return False

        thread.is_resolved = True
        thread.updated_at = datetime.utcnow()

        # Update count
        threads.unresolved_threads = sum(1 for t in threads.threads if not t.is_resolved)

        await self._save_threads(artifact_id, threads)

        logger.info(f"✅ Resolved thread {thread_id}")
        return True

    # ==================
    # Thread Retrieval
    # ==================

    async def get_thread(
        self,
        thread_id: str,
        artifact_id: str
    ) -> Optional[ArtifactThread]:
        """Get a specific thread by ID."""
        threads = await self.get_threads_for_artifact(artifact_id)
        return threads.get_thread(thread_id) if threads else None

    async def get_threads_for_artifact(
        self,
        artifact_id: str,
        family_id: Optional[str] = None
    ) -> Optional[ArtifactThreads]:
        """
        Get all threads for an artifact.

        Args:
            artifact_id: Artifact to get threads for
            family_id: Optional family ID (needed if not cached)

        Returns:
            ArtifactThreads collection or None
        """
        # Check cache first
        if artifact_id in self._threads_cache:
            return self._threads_cache[artifact_id]

        # Try to load from storage
        if family_id:
            threads = await self._load_threads(artifact_id, family_id)
            if threads:
                self._threads_cache[artifact_id] = threads
                return threads

        return None

    async def get_threads_for_section(
        self,
        artifact_id: str,
        section_id: str
    ) -> List[ArtifactThread]:
        """Get all threads for a specific section."""
        threads = self._threads_cache.get(artifact_id)
        if not threads:
            return []
        return threads.get_threads_for_section(section_id)

    async def get_thread_summaries(
        self,
        artifact_id: str
    ) -> List[ThreadSummary]:
        """Get lightweight summaries for all threads on an artifact."""
        threads = self._threads_cache.get(artifact_id)
        if not threads:
            return []
        return threads.get_summaries()

    # ==================
    # Structured Artifacts
    # ==================

    async def get_structured_artifact(
        self,
        family_id: str,
        artifact_id: str
    ) -> Optional[StructuredArtifact]:
        """
        Get a structured version of an artifact with sections and thread counts.

        Args:
            family_id: Family identifier
            artifact_id: Artifact to structure

        Returns:
            StructuredArtifact with sections and thread info
        """
        # Check cache
        cache_key = f"{family_id}_{artifact_id}"
        if cache_key in self._structured_cache:
            structured = self._structured_cache[cache_key]
            # Update thread counts
            threads = await self.get_threads_for_artifact(artifact_id, family_id)
            if threads:
                thread_counts = {
                    section_id: len(thread_ids)
                    for section_id, thread_ids in threads.threads_by_section.items()
                }
                structured.update_thread_counts(thread_counts)
            return structured

        # Get artifact from session
        session_service = get_session_service()
        session = session_service.get_or_create_session(family_id)
        artifact = session.get_artifact(artifact_id)

        if not artifact or not artifact.is_ready:
            return None

        # Determine artifact title
        title_map = {
            "baseline_parent_report": "דוח הורים",
            "baseline_professional_report": "דוח מקצועי",
            "baseline_video_guidelines": "הנחיות צילום",
            "baseline_video_analysis": "ניתוח וידאו",
            "baseline_interview_summary": "סיכום ראיון"
        }
        title = title_map.get(artifact_id, artifact_id)

        # Create structured artifact
        content = artifact.content
        content_format = artifact.content_format

        # Try to parse JSON content
        if content_format == "json" or (isinstance(content, str) and content.strip().startswith('{')):
            try:
                if isinstance(content, str):
                    content = json.loads(content)
                content_format = "json"
            except json.JSONDecodeError:
                content_format = "markdown"

        structured = create_structured_artifact(
            artifact_id=artifact_id,
            artifact_type=artifact.artifact_type,
            family_id=family_id,
            title=title,
            content=content,
            content_format=content_format
        )

        # Add thread counts
        threads = await self.get_threads_for_artifact(artifact_id, family_id)
        if threads:
            thread_counts = {
                section_id: len(thread_ids)
                for section_id, thread_ids in threads.threads_by_section.items()
            }
            structured.update_thread_counts(thread_counts)

        # Cache
        self._structured_cache[cache_key] = structured

        return structured

    # ==================
    # LLM Context
    # ==================

    async def get_thread_context(
        self,
        thread_id: str,
        artifact_id: str,
        family_id: str
    ) -> Dict[str, Any]:
        """
        Get full context for LLM when responding in a thread.

        Returns artifact info, section text, and thread history
        for contextual AI response.

        Args:
            thread_id: Thread being responded in
            artifact_id: Artifact the thread belongs to
            family_id: Family identifier

        Returns:
            Context dict with artifact, section, and thread info
        """
        thread = await self.get_thread(thread_id, artifact_id)
        if not thread:
            return {}

        # Get structured artifact for section info
        structured = await self.get_structured_artifact(family_id, artifact_id)

        section = None
        if structured:
            section = structured.get_section(thread.section_id)

        context = {
            "artifact_id": artifact_id,
            "artifact_type": structured.artifact_type if structured else "unknown",
            "artifact_title": structured.title if structured else artifact_id,
            "section_id": thread.section_id,
            "section_title": thread.section_title or (section.title if section else None),
            "section_text": thread.section_text or (section.content if section else None),
            "thread_history": thread.get_conversation_for_llm(),
            "thread_message_count": thread.message_count
        }

        return context

    def build_thread_prompt(self, context: Dict[str, Any], user_message: str) -> str:
        """
        Build a prompt for LLM response in thread context.

        Args:
            context: From get_thread_context()
            user_message: User's new message

        Returns:
            Formatted prompt string
        """
        section_title = context.get("section_title", "קטע זה")
        section_text = context.get("section_text", "")
        thread_history = context.get("thread_history", [])

        # Format thread history
        history_text = ""
        if thread_history:
            history_lines = []
            for msg in thread_history[:-1]:  # Exclude last message (it's the current one)
                role_name = "הורה" if msg["role"] == "user" else "צ'יטה"
                history_lines.append(f"{role_name}: {msg['content']}")
            if history_lines:
                history_text = "\n".join(history_lines)

        prompt = f"""את עונה לשאלה על קטע ספציפי מדוח ההתפתחות של הילד.

קטע בדיון:
---
{section_title}

{section_text}
---
"""

        if history_text:
            prompt += f"""
היסטוריית השיחה בנושא זה:
{history_text}
"""

        prompt += f"""
שאלת ההורה:
{user_message}

ענה בקצרה וברלוונטיות לקטע הספציפי. היה חם ותומך.
ההורה מנסה להבין את התפתחות הילד שלהם."""

        return prompt

    # ==================
    # Persistence
    # ==================

    def _get_or_create_threads(
        self,
        artifact_id: str,
        family_id: str
    ) -> ArtifactThreads:
        """Get or create threads collection for an artifact."""
        if artifact_id not in self._threads_cache:
            self._threads_cache[artifact_id] = ArtifactThreads(
                artifact_id=artifact_id,
                family_id=family_id
            )
        return self._threads_cache[artifact_id]

    async def _save_threads(
        self,
        artifact_id: str,
        threads: ArtifactThreads
    ) -> None:
        """
        Persist threads to storage.

        Saves threads JSON alongside the artifact.
        """
        # For now, just keep in memory cache
        # TODO: Implement file/DB persistence
        self._threads_cache[artifact_id] = threads

        # Optional: Save to file for persistence
        try:
            storage_dir = Path("sessions") / threads.family_id / "threads"
            storage_dir.mkdir(parents=True, exist_ok=True)

            file_path = storage_dir / f"{artifact_id}_threads.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(threads.model_dump(mode='json'), f, ensure_ascii=False, indent=2)

            logger.debug(f"💾 Saved threads to {file_path}")
        except Exception as e:
            logger.warning(f"Could not persist threads to file: {e}")

    async def _load_threads(
        self,
        artifact_id: str,
        family_id: str
    ) -> Optional[ArtifactThreads]:
        """Load threads from storage."""
        try:
            file_path = Path("sessions") / family_id / "threads" / f"{artifact_id}_threads.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return ArtifactThreads.model_validate(data)
        except Exception as e:
            logger.warning(f"Could not load threads from file: {e}")
        return None


# Global singleton
_artifact_thread_service: Optional[ArtifactThreadService] = None


def get_artifact_thread_service() -> ArtifactThreadService:
    """Get global ArtifactThreadService instance."""
    global _artifact_thread_service
    if _artifact_thread_service is None:
        _artifact_thread_service = ArtifactThreadService()
    return _artifact_thread_service
