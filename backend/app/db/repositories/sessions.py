"""
Session Repository - Conversation Management.

Handles:
- Session lifecycle (create, end, resume)
- Message storage and retrieval
- Session memory distillation
- Turn management
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Sequence

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.base import SessionType
from app.db.models_core import Session, Message
from app.db.repositories.base import BaseRepository


class SessionRepository(BaseRepository[Session]):
    """Repository for Session operations."""

    def __init__(self, db_session: AsyncSession):
        super().__init__(Session, db_session)

    async def create_session(
        self,
        child_id: uuid.UUID,
        user_id: uuid.UUID,
        session_type: SessionType = SessionType.PARENT
    ) -> Session:
        """Create a new conversation session."""
        now = datetime.now(timezone.utc)
        return await self.create(
            child_id=child_id,
            user_id=user_id,
            session_type=session_type.value,
            started_at=now,
            last_activity_at=now
        )

    async def get_active_session(
        self,
        child_id: uuid.UUID,
        user_id: uuid.UUID,
        *,
        hours_threshold: int = 4
    ) -> Optional[Session]:
        """
        Get active session for child/user if one exists.

        A session is active if:
        - Not explicitly ended
        - Last activity within threshold hours
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_threshold)

        stmt = select(Session).where(
            and_(
                Session.child_id == child_id,
                Session.user_id == user_id,
                Session.ended_at.is_(None),
                Session.last_activity_at > cutoff
            )
        ).order_by(Session.last_activity_at.desc())

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create_session(
        self,
        child_id: uuid.UUID,
        user_id: uuid.UUID,
        session_type: SessionType = SessionType.PARENT,
        *,
        hours_threshold: int = 4
    ) -> tuple[Session, bool]:
        """
        Get active session or create new one.

        Returns:
            Tuple of (session, is_new)
        """
        existing = await self.get_active_session(
            child_id, user_id, hours_threshold=hours_threshold
        )
        if existing:
            return existing, False

        new_session = await self.create_session(child_id, user_id, session_type)
        return new_session, True

    async def get_with_messages(
        self,
        session_id: uuid.UUID,
        *,
        message_limit: Optional[int] = None
    ) -> Optional[Session]:
        """Get session with messages eagerly loaded."""
        stmt = select(Session).where(
            Session.id == session_id
        ).options(selectinload(Session.messages))

        result = await self.session.execute(stmt)
        session = result.scalar_one_or_none()

        # Sort and limit messages in Python if needed
        if session and message_limit and len(session.messages) > message_limit:
            session.messages = sorted(
                session.messages,
                key=lambda m: m.sequence_number
            )[-message_limit:]

        return session

    async def get_child_sessions(
        self,
        child_id: uuid.UUID,
        *,
        limit: int = 10,
        include_ended: bool = True
    ) -> Sequence[Session]:
        """Get sessions for a child."""
        stmt = select(Session).where(Session.child_id == child_id)

        if not include_ended:
            stmt = stmt.where(Session.ended_at.is_(None))

        stmt = stmt.order_by(Session.last_activity_at.desc()).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_user_sessions(
        self,
        user_id: uuid.UUID,
        *,
        limit: int = 20
    ) -> Sequence[Session]:
        """Get recent sessions for a user across all children."""
        stmt = select(Session).where(
            Session.user_id == user_id
        ).order_by(Session.last_activity_at.desc()).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_activity(
        self,
        session_id: uuid.UUID,
        *,
        current_focus: Optional[str] = None,
        exploration_depth: Optional[int] = None
    ) -> Optional[Session]:
        """Update session activity timestamp and optional state."""
        updates = {"last_activity_at": datetime.now(timezone.utc)}

        if current_focus is not None:
            updates["current_focus"] = current_focus
        if exploration_depth is not None:
            updates["exploration_depth"] = exploration_depth

        return await self.update(session_id, **updates)

    async def end_session(self, session_id: uuid.UUID) -> Optional[Session]:
        """Mark session as ended."""
        return await self.update(
            session_id,
            ended_at=datetime.now(timezone.utc)
        )

    async def save_memory_summary(
        self,
        session_id: uuid.UUID,
        summary: str
    ) -> Optional[Session]:
        """Save distilled memory summary for session."""
        return await self.update(
            session_id,
            memory_summary=summary,
            memory_distilled_at=datetime.now(timezone.utc)
        )

    async def get_sessions_needing_distillation(
        self,
        hours_since_activity: int = 4
    ) -> Sequence[Session]:
        """Get sessions that need memory distillation."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_since_activity)

        stmt = select(Session).where(
            and_(
                Session.memory_distilled_at.is_(None),
                Session.last_activity_at < cutoff
            )
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()


class MessageRepository(BaseRepository[Message]):
    """Repository for Message operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Message, session)

    async def add_message(
        self,
        session_id: uuid.UUID,
        role: str,
        content: str,
        *,
        model_used: Optional[str] = None,
        tokens_input: Optional[int] = None,
        tokens_output: Optional[int] = None
    ) -> Message:
        """Add a message to a session."""
        # Get next sequence number
        stmt = select(func.coalesce(func.max(Message.sequence_number), 0)).where(
            Message.session_id == session_id
        )
        result = await self.session.execute(stmt)
        next_seq = result.scalar_one() + 1

        return await self.create(
            session_id=session_id,
            role=role,
            content=content,
            sequence_number=next_seq,
            sent_at=datetime.now(timezone.utc),
            model_used=model_used,
            tokens_input=tokens_input,
            tokens_output=tokens_output
        )

    async def get_session_messages(
        self,
        session_id: uuid.UUID,
        *,
        limit: Optional[int] = None,
        offset: int = 0,
        order_asc: bool = True
    ) -> Sequence[Message]:
        """Get messages for a session."""
        stmt = select(Message).where(Message.session_id == session_id)

        if order_asc:
            stmt = stmt.order_by(Message.sequence_number.asc())
        else:
            stmt = stmt.order_by(Message.sequence_number.desc())

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_recent_messages(
        self,
        session_id: uuid.UUID,
        count: int = 10
    ) -> Sequence[Message]:
        """Get most recent messages from a session."""
        # Get in descending order then reverse for chronological
        messages = await self.get_session_messages(
            session_id,
            limit=count,
            order_asc=False
        )
        return list(reversed(messages))

    async def get_message_count(self, session_id: uuid.UUID) -> int:
        """Get count of messages in a session."""
        return await self.count(filters={"session_id": session_id})

    async def get_user_messages(
        self,
        session_id: uuid.UUID
    ) -> Sequence[Message]:
        """Get only user messages from a session."""
        stmt = select(Message).where(
            and_(
                Message.session_id == session_id,
                Message.role == "user"
            )
        ).order_by(Message.sequence_number)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_token_usage(
        self,
        session_id: uuid.UUID
    ) -> dict:
        """Get total token usage for a session."""
        stmt = select(
            func.sum(Message.tokens_input).label("total_input"),
            func.sum(Message.tokens_output).label("total_output")
        ).where(
            and_(
                Message.session_id == session_id,
                Message.role == "assistant"
            )
        )

        result = await self.session.execute(stmt)
        row = result.one()

        return {
            "total_input": row.total_input or 0,
            "total_output": row.total_output or 0,
            "total": (row.total_input or 0) + (row.total_output or 0)
        }
