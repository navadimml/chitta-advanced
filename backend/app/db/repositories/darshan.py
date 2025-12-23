"""
Darshan Repository - Persistence for Darshan/Chitta data.

Handles all database operations for:
- Curiosities and Investigations
- Temporal Facts (Observations)
- Stories
- Journal entries
- Crystals (portraits)
- Session history
- Session flags
- Shared summaries
"""

import json
import uuid as uuid_module
from datetime import datetime
from typing import Optional, List, Dict, Any, Sequence, Union

from sqlalchemy import select, delete, cast, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models_supporting import (
    Curiosity,
    Investigation,
    InvestigationEvidence,
    DarshanJournal,
    DarshanCrystal,
    SessionHistoryEntry,
    SharedSummary,
    SessionFlags,
)


def _to_uuid(child_id: str) -> uuid_module.UUID:
    """Convert child_id string to UUID, handling both UUID strings and regular strings."""
    try:
        return uuid_module.UUID(child_id)
    except ValueError:
        # For non-UUID strings (like seed data), create a deterministic UUID
        return uuid_module.uuid5(uuid_module.NAMESPACE_DNS, child_id)


class DarshanRepository:
    """
    Repository for Darshan/Chitta data persistence.

    Provides a clean interface for loading and saving all Darshan-related data.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # =========================================================================
    # CURIOSITIES
    # =========================================================================

    async def get_curiosities(self, child_id: str) -> Sequence[Curiosity]:
        """Get all curiosities for a child."""
        child_uuid = _to_uuid(child_id)
        stmt = select(Curiosity).where(
            Curiosity.child_id == child_uuid
        ).order_by(Curiosity.pull.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_active_curiosities(self, child_id: str) -> Sequence[Curiosity]:
        """Get active curiosities for a child."""
        child_uuid = _to_uuid(child_id)
        stmt = select(Curiosity).where(
            Curiosity.child_id == child_uuid,
            Curiosity.is_active == True
        ).order_by(Curiosity.pull.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def save_curiosity(self, child_id: str, curiosity_data: Dict[str, Any]) -> Curiosity:
        """Save a curiosity (create or update)."""
        child_uuid = _to_uuid(child_id)
        # Check if exists by focus
        stmt = select(Curiosity).where(
            Curiosity.child_id == child_uuid,
            Curiosity.focus == curiosity_data.get("focus")
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing
            for key, value in curiosity_data.items():
                if hasattr(existing, key) and key not in ("id", "child_id"):
                    setattr(existing, key, value)
            await self.session.flush()
            await self.session.refresh(existing)
            return existing
        else:
            # Create new - remove fields that we set explicitly to avoid duplicates
            create_data = {k: v for k, v in curiosity_data.items()
                          if k not in ("id", "child_id", "opened_at", "last_activated")}
            curiosity = Curiosity(
                child_id=child_uuid,
                opened_at=curiosity_data.get("opened_at") or datetime.now(),
                last_activated=curiosity_data.get("last_activated") or datetime.now(),
                **create_data
            )
            self.session.add(curiosity)
            await self.session.flush()
            await self.session.refresh(curiosity)
            return curiosity

    async def save_curiosities_batch(self, child_id: str, curiosities_data: List[Dict[str, Any]]):
        """Save multiple curiosities."""
        for c_data in curiosities_data:
            await self.save_curiosity(child_id, c_data)

    async def delete_child_curiosities(self, child_id: str):
        """Delete all curiosities for a child."""
        child_uuid = _to_uuid(child_id)
        stmt = delete(Curiosity).where(Curiosity.child_id == child_uuid)
        await self.session.execute(stmt)

    # =========================================================================
    # INVESTIGATIONS
    # =========================================================================

    async def get_investigation(self, investigation_id: str) -> Optional[Investigation]:
        """Get investigation by ID with evidence loaded."""
        stmt = select(Investigation).where(
            Investigation.id == investigation_id
        ).options(selectinload(Investigation.evidence))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_investigations_by_curiosity(self, curiosity_id: str) -> Sequence[Investigation]:
        """Get all investigations for a curiosity."""
        stmt = select(Investigation).where(
            Investigation.curiosity_id == curiosity_id
        ).options(selectinload(Investigation.evidence))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def save_investigation(self, investigation_data: Dict[str, Any]) -> Investigation:
        """Save an investigation."""
        investigation_id = investigation_data.get("id")

        if investigation_id:
            # Check if exists
            existing = await self.get_investigation(investigation_id)
            if existing:
                # Update
                for key, value in investigation_data.items():
                    if hasattr(existing, key) and key not in ("id", "evidence"):
                        setattr(existing, key, value)
                await self.session.flush()
                await self.session.refresh(existing)
                return existing

        # Create new
        evidence_data = investigation_data.pop("evidence", [])
        investigation = Investigation(**investigation_data)
        self.session.add(investigation)
        await self.session.flush()

        # Add evidence
        for e_data in evidence_data:
            evidence = InvestigationEvidence(
                id=e_data.get("id", f"evi_{uuid_module.uuid4().hex[:8]}"),
                investigation_id=investigation.id,
                content=e_data["content"],
                effect=e_data.get("effect", "supports"),
                source=e_data.get("source", "conversation"),
                recorded_at=e_data.get("timestamp", datetime.now()),
            )
            self.session.add(evidence)

        await self.session.flush()
        await self.session.refresh(investigation)
        return investigation

    async def add_evidence(self, investigation_id: str, evidence_data: Dict[str, Any]) -> InvestigationEvidence:
        """Add evidence to an investigation."""
        evidence = InvestigationEvidence(
            id=evidence_data.get("id", f"evi_{uuid_module.uuid4().hex[:8]}"),
            investigation_id=investigation_id,
            content=evidence_data["content"],
            effect=evidence_data.get("effect", "supports"),
            source=evidence_data.get("source", "conversation"),
            recorded_at=evidence_data.get("timestamp", datetime.now()),
        )
        self.session.add(evidence)
        await self.session.flush()
        await self.session.refresh(evidence)
        return evidence

    # =========================================================================
    # DARSHAN JOURNAL
    # =========================================================================

    async def get_journal_entries(self, child_id: str) -> Sequence[DarshanJournal]:
        """Get journal entries for a child."""
        stmt = select(DarshanJournal).where(
            DarshanJournal.child_id == child_id
        ).order_by(DarshanJournal.timestamp.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def save_journal_entry(self, child_id: str, entry_data: Dict[str, Any]) -> DarshanJournal:
        """Save a journal entry."""
        # Serialize learned field if it's a list
        learned = entry_data.get("learned")
        if isinstance(learned, list):
            learned = json.dumps(learned, ensure_ascii=False)

        entry = DarshanJournal(
            id=entry_data.get("id", f"jrn_{uuid_module.uuid4().hex[:8]}"),
            child_id=child_id,
            summary=entry_data["summary"],
            learned=learned,
            significance=entry_data.get("significance", "routine"),
            entry_type=entry_data.get("entry_type", "observation"),
            timestamp=entry_data.get("timestamp", datetime.now()),
        )
        self.session.add(entry)
        await self.session.flush()
        await self.session.refresh(entry)
        return entry

    async def delete_child_journal(self, child_id: str):
        """Delete all journal entries for a child."""
        stmt = delete(DarshanJournal).where(DarshanJournal.child_id == child_id)
        await self.session.execute(stmt)

    # =========================================================================
    # CRYSTAL (Portrait)
    # =========================================================================

    async def get_crystal(self, child_id: str) -> Optional[DarshanCrystal]:
        """Get crystal for a child."""
        stmt = select(DarshanCrystal).where(DarshanCrystal.child_id == child_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def save_crystal(self, child_id: str, crystal_data: Dict[str, Any]) -> DarshanCrystal:
        """Save or update crystal for a child."""
        existing = await self.get_crystal(child_id)

        portrait_json = json.dumps(crystal_data.get("portrait_data", {}), ensure_ascii=False)

        if existing:
            existing.portrait_data = portrait_json
            existing.generated_at = crystal_data.get("generated_at", datetime.now())
            await self.session.flush()
            await self.session.refresh(existing)
            return existing
        else:
            crystal = DarshanCrystal(
                id=f"cry_{uuid_module.uuid4().hex[:8]}",
                child_id=child_id,
                portrait_data=portrait_json,
                generated_at=crystal_data.get("generated_at", datetime.now()),
            )
            self.session.add(crystal)
            await self.session.flush()
            await self.session.refresh(crystal)
            return crystal

    async def delete_crystal(self, child_id: str):
        """Delete crystal for a child."""
        stmt = delete(DarshanCrystal).where(DarshanCrystal.child_id == child_id)
        await self.session.execute(stmt)

    # =========================================================================
    # SESSION HISTORY
    # =========================================================================

    async def get_session_history(self, child_id: str, limit: int = 100) -> Sequence[SessionHistoryEntry]:
        """Get session history for a child."""
        stmt = select(SessionHistoryEntry).where(
            SessionHistoryEntry.child_id == child_id
        ).order_by(SessionHistoryEntry.turn_number.asc()).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def save_session_message(self, child_id: str, message_data: Dict[str, Any]) -> SessionHistoryEntry:
        """Save a session history message."""
        # Get next turn number
        stmt = select(SessionHistoryEntry).where(
            SessionHistoryEntry.child_id == child_id
        ).order_by(SessionHistoryEntry.turn_number.desc()).limit(1)
        result = await self.session.execute(stmt)
        last_entry = result.scalar_one_or_none()
        next_turn = (last_entry.turn_number + 1) if last_entry else 0

        entry = SessionHistoryEntry(
            id=f"msg_{uuid_module.uuid4().hex[:8]}",
            child_id=child_id,
            role=message_data["role"],
            content=message_data["content"],
            turn_number=message_data.get("turn_number", next_turn),
            timestamp=message_data.get("timestamp", datetime.now()),
        )
        self.session.add(entry)
        await self.session.flush()
        await self.session.refresh(entry)
        return entry

    async def save_session_history_batch(self, child_id: str, messages: List[Dict[str, Any]]):
        """Save multiple session history messages."""
        # Delete existing history for fresh save
        await self.delete_session_history(child_id)

        for i, msg_data in enumerate(messages):
            msg_data["turn_number"] = i
            await self.save_session_message(child_id, msg_data)

    async def delete_session_history(self, child_id: str):
        """Delete session history for a child."""
        stmt = delete(SessionHistoryEntry).where(SessionHistoryEntry.child_id == child_id)
        await self.session.execute(stmt)

    # =========================================================================
    # SESSION FLAGS
    # =========================================================================

    async def get_session_flags(self, child_id: str) -> Optional[SessionFlags]:
        """Get session flags for a child."""
        stmt = select(SessionFlags).where(SessionFlags.child_id == child_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def save_session_flags(self, child_id: str, flags_data: Dict[str, Any]) -> SessionFlags:
        """Save or update session flags for a child."""
        existing = await self.get_session_flags(child_id)

        if existing:
            existing.guided_collection_mode = flags_data.get("guided_collection_mode", False)
            existing.baseline_video_requested = flags_data.get("baseline_video_requested", False)
            if "flags_data" in flags_data:
                existing.flags_data = json.dumps(flags_data["flags_data"], ensure_ascii=False)
            await self.session.flush()
            await self.session.refresh(existing)
            return existing
        else:
            flags = SessionFlags(
                id=f"flg_{uuid_module.uuid4().hex[:8]}",
                child_id=child_id,
                guided_collection_mode=flags_data.get("guided_collection_mode", False),
                baseline_video_requested=flags_data.get("baseline_video_requested", False),
                flags_data=json.dumps(flags_data.get("flags_data", {}), ensure_ascii=False) if flags_data.get("flags_data") else None,
            )
            self.session.add(flags)
            await self.session.flush()
            await self.session.refresh(flags)
            return flags

    # =========================================================================
    # SHARED SUMMARIES
    # =========================================================================

    async def get_shared_summaries(self, child_id: str) -> Sequence[SharedSummary]:
        """Get shared summaries for a child."""
        stmt = select(SharedSummary).where(
            SharedSummary.child_id == child_id
        ).order_by(SharedSummary.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_shared_summary_by_type(self, child_id: str, summary_type: str) -> Optional[SharedSummary]:
        """Get shared summary by type."""
        stmt = select(SharedSummary).where(
            SharedSummary.child_id == child_id,
            SharedSummary.summary_type == summary_type
        ).order_by(SharedSummary.created_at.desc()).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def save_shared_summary(self, child_id: str, summary_data: Dict[str, Any]) -> SharedSummary:
        """Save a shared summary."""
        summary = SharedSummary(
            id=f"sum_{uuid_module.uuid4().hex[:8]}",
            child_id=child_id,
            summary_type=summary_data["summary_type"],
            content=summary_data["content"],
            extra_metadata=json.dumps(summary_data.get("metadata", {}), ensure_ascii=False) if summary_data.get("metadata") else None,
        )
        self.session.add(summary)
        await self.session.flush()
        await self.session.refresh(summary)
        return summary

    # =========================================================================
    # FULL DARSHAN STATE (Combined load/save)
    # =========================================================================

    async def load_darshan_data(self, child_id: str) -> Dict[str, Any]:
        """
        Load complete Darshan data for a child.

        Returns a dict with all Darshan-related data that can be used
        to reconstruct the Darshan object.
        """
        # Load curiosities
        curiosities = await self.get_active_curiosities(child_id)

        # Build curiosities data with investigations
        curiosities_data = []
        for c in curiosities:
            c_data = {
                "focus": c.focus,
                "type": c.curiosity_type,
                "pull": c.pull,
                "certainty": c.certainty,
                "domain": c.domain,
                "status": c.status or "wondering",
                "theory": c.theory,
                "video_appropriate": c.video_appropriate,
                "video_value": c.video_value,
                "video_value_reason": c.video_value_reason,
                "question": c.question,
                "domains_involved": json.loads(c.domains_involved) if c.domains_involved else [],
                "last_activated": c.last_activated.isoformat() if c.last_activated else None,
                "times_explored": c.times_explored,
            }

            # Load investigation if status is investigating
            if c.status == "investigating":
                investigations = await self.get_investigations_by_curiosity(str(c.id))
                if investigations:
                    inv = investigations[0]  # Get most recent
                    c_data["investigation"] = {
                        "id": inv.id,
                        "status": inv.status,
                        "started_at": inv.started_at.isoformat() if inv.started_at else None,
                        "video_accepted": inv.video_accepted,
                        "video_declined": inv.video_declined,
                        "video_suggested_at": inv.video_suggested_at.isoformat() if inv.video_suggested_at else None,
                        "guidelines_status": inv.guidelines_status,
                        "evidence": [
                            {
                                "content": e.content,
                                "effect": e.effect,
                                "source": e.source,
                                "timestamp": e.recorded_at.isoformat() if e.recorded_at else None,
                            }
                            for e in inv.evidence
                        ],
                        "video_scenarios": [],  # Would need to load from video_scenarios table
                    }

            curiosities_data.append(c_data)

        # Load journal
        journal_entries = await self.get_journal_entries(child_id)
        journal_data = []
        for e in journal_entries:
            # Deserialize learned field if it's a JSON string
            learned = e.learned
            if learned:
                try:
                    learned = json.loads(learned)
                except (json.JSONDecodeError, TypeError):
                    learned = [learned] if learned else []
            else:
                learned = []

            journal_data.append({
                "summary": e.summary,
                "learned": learned,
                "significance": e.significance,
                "entry_type": e.entry_type,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            })

        # Load crystal
        crystal = await self.get_crystal(child_id)
        crystal_data = None
        if crystal and crystal.portrait_data:
            try:
                crystal_data = json.loads(crystal.portrait_data)
                crystal_data["generated_at"] = crystal.generated_at.isoformat() if crystal.generated_at else None
            except json.JSONDecodeError:
                pass

        # Load session history
        history = await self.get_session_history(child_id)
        session_history_data = [
            {
                "role": h.role,
                "content": h.content,
                "timestamp": h.timestamp.isoformat() if h.timestamp else None,
            }
            for h in history
        ]

        # Load session flags
        flags = await self.get_session_flags(child_id)
        session_flags_data = None
        if flags:
            session_flags_data = {
                "guided_collection_mode": flags.guided_collection_mode,
                "baseline_video_requested": flags.baseline_video_requested,
            }
            if flags.flags_data:
                try:
                    session_flags_data.update(json.loads(flags.flags_data))
                except json.JSONDecodeError:
                    pass

        # Load shared summaries
        summaries = await self.get_shared_summaries(child_id)
        shared_summaries_data = {}
        for s in summaries:
            shared_summaries_data[s.summary_type] = {
                "content": s.content,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            if s.extra_metadata:
                try:
                    shared_summaries_data[s.summary_type]["metadata"] = json.loads(s.extra_metadata)
                except json.JSONDecodeError:
                    pass

        return {
            "curiosities": {"dynamic": curiosities_data, "baseline_video_requested": flags.baseline_video_requested if flags else False},
            "journal": journal_data,
            "crystal": crystal_data,
            "session_history": session_history_data,
            "session_flags": session_flags_data,
            "shared_summaries": shared_summaries_data,
        }

    async def save_darshan_data(self, child_id: str, darshan_data: Dict[str, Any]):
        """
        Save complete Darshan data for a child.

        Takes a dict from Darshan.get_state_for_persistence() and saves
        all data to the database.
        """
        # Save curiosities
        curiosities_data = darshan_data.get("curiosities", {})
        dynamic_curiosities = curiosities_data.get("dynamic", [])

        # Delete existing and save new (simpler than merge)
        await self.delete_child_curiosities(child_id)

        for c_data in dynamic_curiosities:
            # Map to DB format
            db_data = {
                "focus": c_data["focus"],
                "curiosity_type": c_data["type"],
                "pull": c_data.get("pull", 0.5),
                "certainty": c_data.get("certainty", 0.3),
                "domain": c_data.get("domain"),
                "status": c_data.get("status", "wondering"),
                "theory": c_data.get("theory"),
                "video_appropriate": c_data.get("video_appropriate", False),
                "video_value": c_data.get("video_value"),
                "video_value_reason": c_data.get("video_value_reason"),
                "question": c_data.get("question"),
                "domains_involved": json.dumps(c_data.get("domains_involved", []), ensure_ascii=False),
                "times_explored": c_data.get("times_explored", 0),
                "is_active": c_data.get("status") not in ("understood", "dormant"),
            }

            # Handle last_activated
            last_activated = c_data.get("last_activated")
            if isinstance(last_activated, str):
                db_data["last_activated"] = datetime.fromisoformat(last_activated)
            else:
                db_data["last_activated"] = last_activated or datetime.now()

            curiosity = await self.save_curiosity(child_id, db_data)

            # Save investigation if present
            if c_data.get("investigation"):
                inv_data = c_data["investigation"]
                investigation_data = {
                    "id": inv_data["id"],
                    "curiosity_id": str(curiosity.id),
                    "status": inv_data.get("status", "active"),
                    "video_accepted": inv_data.get("video_accepted", False),
                    "video_declined": inv_data.get("video_declined", False),
                    "guidelines_status": inv_data.get("guidelines_status"),
                    "evidence": inv_data.get("evidence", []),
                }

                started_at = inv_data.get("started_at")
                if isinstance(started_at, str):
                    investigation_data["started_at"] = datetime.fromisoformat(started_at)
                else:
                    investigation_data["started_at"] = started_at or datetime.now()

                video_suggested_at = inv_data.get("video_suggested_at")
                if video_suggested_at:
                    if isinstance(video_suggested_at, str):
                        investigation_data["video_suggested_at"] = datetime.fromisoformat(video_suggested_at)
                    else:
                        investigation_data["video_suggested_at"] = video_suggested_at

                await self.save_investigation(investigation_data)

        # Save journal
        journal_data = darshan_data.get("journal", [])
        if journal_data:
            await self.delete_child_journal(child_id)
            for entry in journal_data:
                timestamp = entry.get("timestamp")
                if isinstance(timestamp, str):
                    entry["timestamp"] = datetime.fromisoformat(timestamp)
                await self.save_journal_entry(child_id, entry)

        # Save crystal
        crystal_data = darshan_data.get("crystal")
        if crystal_data:
            await self.save_crystal(child_id, {"portrait_data": crystal_data})

        # Save session history
        session_history = darshan_data.get("session_history", [])
        if session_history:
            await self.save_session_history_batch(child_id, session_history)

        # Save session flags
        session_flags = darshan_data.get("session_flags", {})
        session_flags["baseline_video_requested"] = curiosities_data.get("baseline_video_requested", False)
        await self.save_session_flags(child_id, session_flags)

        # Save shared summaries
        shared_summaries = darshan_data.get("shared_summaries", {})
        for summary_type, summary_content in shared_summaries.items():
            if isinstance(summary_content, dict):
                await self.save_shared_summary(child_id, {
                    "summary_type": summary_type,
                    "content": summary_content.get("content", str(summary_content)),
                    "metadata": summary_content.get("metadata"),
                })
            else:
                await self.save_shared_summary(child_id, {
                    "summary_type": summary_type,
                    "content": str(summary_content),
                })
