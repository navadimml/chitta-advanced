"""
Artifact Thread Model - Living Documents conversation threads.

Part of Living Dashboard Phase 3: Enables threaded conversations
attached to specific sections of artifacts.

Parents can ask questions about specific parts of reports, guidelines,
or video analysis, and the conversation persists with that context.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


class ThreadMessage(BaseModel):
    """
    A single message in an artifact thread.

    Messages are either from the user (parent) or assistant (Chitta).
    Each message is timestamped for conversation history.
    """
    message_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    role: str  # "user" or "assistant"
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Optional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ArtifactThread(BaseModel):
    """
    A conversation thread attached to an artifact section.

    Threads provide contextual Q&A within artifacts:
    - User highlights/taps a section
    - User asks a question
    - Chitta responds with section context
    - Conversation persists for later reference

    Example:
        User taps "Motor Development" section in parent report
        User asks: "What exercises can help with this?"
        Chitta responds knowing the specific motor findings
    """
    thread_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    family_id: str
    artifact_id: str

    # What section this thread is attached to
    section_id: str  # e.g., "motor_development", "0:43" for video timestamp
    section_type: str = "paragraph"  # "heading", "paragraph", "observation", "timestamp"
    section_title: Optional[str] = None  # e.g., "התפתחות מוטורית"
    section_text: Optional[str] = None  # The actual text being discussed

    # The conversation
    messages: List[ThreadMessage] = Field(default_factory=list)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # State
    is_resolved: bool = False  # User can mark as "understood" / "got it"
    is_collapsed: bool = True  # UI state

    # Summary for display
    preview: Optional[str] = None  # First few words of first question
    message_count: int = 0

    def add_message(self, role: str, content: str) -> ThreadMessage:
        """Add a message to the thread."""
        message = ThreadMessage(role=role, content=content)
        self.messages.append(message)
        self.message_count = len(self.messages)
        self.updated_at = datetime.utcnow()

        # Update preview from first user message
        if role == "user" and not self.preview:
            self.preview = content[:50] + "..." if len(content) > 50 else content

        return message

    def get_conversation_for_llm(self) -> List[Dict[str, str]]:
        """Get messages formatted for LLM context."""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.messages
        ]


class ThreadSummary(BaseModel):
    """
    Lightweight thread info for artifact display.

    Shows thread indicator on sections without loading full conversations.
    """
    thread_id: str
    section_id: str
    preview: Optional[str] = None
    message_count: int = 0
    is_resolved: bool = False
    updated_at: Optional[datetime] = None


class ArtifactThreads(BaseModel):
    """
    Collection of all threads for an artifact.

    Stored alongside the artifact for persistence.
    """
    artifact_id: str
    family_id: str
    threads: List[ArtifactThread] = Field(default_factory=list)

    # Quick lookup
    threads_by_section: Dict[str, List[str]] = Field(default_factory=dict)  # section_id -> [thread_ids]

    # Summary stats
    total_threads: int = 0
    unresolved_threads: int = 0

    def add_thread(self, thread: ArtifactThread) -> None:
        """Add a thread to the collection."""
        self.threads.append(thread)
        self.total_threads = len(self.threads)
        self.unresolved_threads = sum(1 for t in self.threads if not t.is_resolved)

        # Update section lookup
        if thread.section_id not in self.threads_by_section:
            self.threads_by_section[thread.section_id] = []
        self.threads_by_section[thread.section_id].append(thread.thread_id)

    def get_thread(self, thread_id: str) -> Optional[ArtifactThread]:
        """Get a specific thread by ID."""
        for thread in self.threads:
            if thread.thread_id == thread_id:
                return thread
        return None

    def get_threads_for_section(self, section_id: str) -> List[ArtifactThread]:
        """Get all threads for a specific section."""
        return [t for t in self.threads if t.section_id == section_id]

    def get_summaries(self) -> List[ThreadSummary]:
        """Get lightweight summaries for all threads."""
        return [
            ThreadSummary(
                thread_id=t.thread_id,
                section_id=t.section_id,
                preview=t.preview,
                message_count=t.message_count,
                is_resolved=t.is_resolved,
                updated_at=t.updated_at
            )
            for t in self.threads
        ]
