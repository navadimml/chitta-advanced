"""
Child Service - Manages Child entities with persistence

The Child is the invariant core of Chitta. This service:
1. Stores and retrieves Child data
2. Updates developmental understanding from conversation extractions
3. Manages artifacts, videos, and journal entries
4. Persists to file/Redis (like session_persistence)

Design principles:
- Child data is shared across all users with access
- Updates are additive (we accumulate understanding)
- Completeness is calculated from the data itself
"""

import logging
import json
import os
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from app.models.child import Child, DevelopmentalData, Video, JournalEntry
from app.models.artifact import Artifact
from app.config.schema_registry import calculate_completeness as config_calculate_completeness

logger = logging.getLogger(__name__)

# Storage configuration
STORAGE_TYPE = os.getenv("CHILD_STORAGE_TYPE", os.getenv("SESSION_STORAGE_TYPE", "file"))
DATA_DIR = os.getenv("CHILD_DATA_DIR", "data/children")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Ensure data directory exists
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)


class ChildService:
    """
    Manages Child entities - the core data that doesn't change based on who's viewing.

    Child data includes:
    - Developmental understanding (extracted from all conversations)
    - Artifacts (generated reports, guidelines)
    - Videos (behavioral observations)
    - Journal entries (extracted meaningful moments)
    """

    def __init__(self):
        # In-memory cache: child_id -> Child
        self._children: Dict[str, Child] = {}

        # Persistence configuration
        self._storage_type = STORAGE_TYPE
        self._redis_client = None

        if self._storage_type == "redis":
            self._init_redis()

        logger.info(f"ChildService initialized with {self._storage_type} storage")

    def _init_redis(self):
        """Initialize Redis connection if using Redis storage"""
        try:
            import redis
            self._redis_client = redis.from_url(REDIS_URL, decode_responses=True)
            self._redis_client.ping()
            logger.info(f"ChildService connected to Redis at {REDIS_URL}")
        except ImportError:
            logger.warning("Redis not installed, falling back to file storage")
            self._storage_type = "file"
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}, falling back to file storage")
            self._storage_type = "file"

    def _get_file_path(self, child_id: str) -> Path:
        """Get file path for a child's data"""
        safe_id = "".join(c if c.isalnum() or c in "_-" else "_" for c in child_id)
        return Path(DATA_DIR) / f"{safe_id}.json"

    # === Core CRUD Operations ===

    def get_or_create_child(self, child_id: str) -> Child:
        """Get existing child or create new one"""
        if child_id not in self._children:
            # Try to load from persistence
            child = self._load_child_sync(child_id)
            if child:
                self._children[child_id] = child
                logger.info(f"Loaded child {child_id} from persistence")
            else:
                # Create new child
                self._children[child_id] = Child(child_id=child_id)
                logger.info(f"Created new child: {child_id}")

        return self._children[child_id]

    async def get_or_create_child_async(self, child_id: str) -> Child:
        """Async version: Get existing child or create new one"""
        if child_id not in self._children:
            child = await self._load_child(child_id)
            if child:
                self._children[child_id] = child
                logger.info(f"Loaded child {child_id} from persistence")
            else:
                self._children[child_id] = Child(child_id=child_id)
                logger.info(f"Created new child: {child_id}")

        return self._children[child_id]

    async def save_child(self, child_id: str) -> bool:
        """Persist child data to storage"""
        if child_id not in self._children:
            return False

        child = self._children[child_id]
        child.updated_at = datetime.now()

        try:
            child_data = self._child_to_dict(child)

            if self._storage_type == "redis":
                return await self._save_to_redis(child_id, child_data)
            else:
                return await self._save_to_file(child_id, child_data)

        except Exception as e:
            logger.error(f"Error saving child {child_id}: {e}")
            return False

    # === Developmental Data Management ===

    def update_developmental_data(
        self,
        child_id: str,
        new_data: Dict[str, Any]
    ) -> DevelopmentalData:
        """
        Update child's developmental data from conversation extraction.

        Rules:
        - Scalars: new value overrides if not empty
        - Arrays: merge and deduplicate
        - Strings: append if significantly different
        """
        child = self.get_or_create_child(child_id)
        current = child.developmental_data

        # Normalize field names (LITE vs FULL schema)
        if 'concerns' in new_data and 'primary_concerns' not in new_data:
            new_data['primary_concerns'] = new_data.pop('concerns')

        if 'concern_description' in new_data and 'concern_details' not in new_data:
            new_data['concern_details'] = new_data.pop('concern_description')

        # Discard other_info (redundant demographic data)
        new_data.pop('other_info', None)

        # Update scalar fields
        invalid_values = ['None', 'null', 'NULL', 'unknown', '(not mentioned yet)']
        for field in ['child_name', 'age', 'gender', 'filming_preference']:
            if field not in new_data:
                continue

            value = new_data[field]
            if value is None:
                continue
            if isinstance(value, str) and value in invalid_values:
                continue

            setattr(current, field, value)

        # Merge arrays
        if 'primary_concerns' in new_data and new_data['primary_concerns']:
            new_concerns = new_data['primary_concerns']
            if isinstance(new_concerns, str):
                new_concerns = [new_concerns]
            concerns = set(current.primary_concerns + new_concerns)
            current.primary_concerns = list(concerns)

        if 'urgent_flags' in new_data and new_data['urgent_flags']:
            new_flags = new_data['urgent_flags']
            if isinstance(new_flags, str):
                new_flags = [new_flags]
            flags = set(current.urgent_flags + new_flags)
            current.urgent_flags = list(flags)

        # Append text fields
        text_fields = [
            'concern_details', 'strengths', 'developmental_history',
            'family_context', 'daily_routines', 'parent_goals'
        ]

        for field in text_fields:
            if field not in new_data or not new_data[field]:
                continue

            new_text = new_data[field]
            current_text = getattr(current, field) or ""

            if new_text.lower() not in current_text.lower():
                combined = f"{current_text}. {new_text}".strip(". ")
                setattr(current, field, combined)

        # Update metadata
        current.last_updated = datetime.now()
        current.extraction_count += 1

        # Recalculate completeness
        child.data_completeness = self.calculate_completeness(child_id)
        child.updated_at = datetime.now()

        # Persist asynchronously
        asyncio.create_task(self.save_child(child_id))

        logger.info(
            f"Updated developmental data for {child_id}: "
            f"completeness={child.data_completeness:.1%}"
        )

        return current

    def calculate_completeness(self, child_id: str) -> float:
        """Calculate how complete our understanding of this child is"""
        child = self.get_or_create_child(child_id)
        data = child.developmental_data

        extracted_dict = {
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
            "urgent_flags": data.urgent_flags,
        }

        return config_calculate_completeness(extracted_dict)

    # === Artifact Management ===

    def add_artifact(self, child_id: str, artifact: Artifact):
        """Add or update an artifact for this child"""
        child = self.get_or_create_child(child_id)
        child.add_artifact(artifact)
        asyncio.create_task(self.save_child(child_id))
        logger.info(f"Added artifact {artifact.artifact_id} for child {child_id}")

    def get_artifact(self, child_id: str, artifact_id: str) -> Optional[Artifact]:
        """Get an artifact by ID"""
        child = self.get_or_create_child(child_id)
        return child.get_artifact(artifact_id)

    def has_artifact(self, child_id: str, artifact_id: str) -> bool:
        """Check if artifact exists and is ready"""
        child = self.get_or_create_child(child_id)
        return child.has_artifact(artifact_id)

    # === Video Management ===

    def add_video(self, child_id: str, video: Video):
        """Add a video observation"""
        child = self.get_or_create_child(child_id)
        child.add_video(video)
        asyncio.create_task(self.save_child(child_id))
        logger.info(f"Added video {video.id} for child {child_id}")

    def get_video(self, child_id: str, video_id: str) -> Optional[Video]:
        """Get a video by ID"""
        child = self.get_or_create_child(child_id)
        return child.get_video(video_id)

    def get_videos_pending_analysis(self, child_id: str) -> List[Video]:
        """Get videos that need analysis"""
        child = self.get_or_create_child(child_id)
        return child.get_videos_pending_analysis()

    def update_video_analysis_status(
        self,
        child_id: str,
        video_id: str,
        status: str,
        artifact_id: Optional[str] = None,
        error: Optional[str] = None
    ):
        """Update a video's analysis status"""
        child = self.get_or_create_child(child_id)
        video = child.get_video(video_id)
        if video:
            video.analysis_status = status
            if artifact_id:
                video.analysis_artifact_id = artifact_id
            if error:
                video.analysis_error = error
            asyncio.create_task(self.save_child(child_id))

    # === Journal Management ===

    def add_journal_entry(self, child_id: str, entry: JournalEntry):
        """Add a journal entry"""
        child = self.get_or_create_child(child_id)
        child.add_journal_entry(entry)
        asyncio.create_task(self.save_child(child_id))
        logger.info(f"Added journal entry for child {child_id}")

    def get_recent_journal_entries(
        self,
        child_id: str,
        limit: int = 10
    ) -> List[JournalEntry]:
        """Get most recent journal entries"""
        child = self.get_or_create_child(child_id)
        return child.get_recent_journal_entries(limit)

    # === Context for LLM ===

    def get_child_context(self, child_id: str) -> Dict[str, Any]:
        """
        Get child context for LLM prompts.

        This is the gestalt - everything we know about this child.
        """
        child = self.get_or_create_child(child_id)
        data = child.developmental_data

        return {
            "child_id": child_id,
            "name": data.child_name,
            "age": data.age,
            "gender": data.gender,
            "primary_concerns": data.primary_concerns,
            "concern_details": data.concern_details,
            "strengths": data.strengths,
            "developmental_history": data.developmental_history,
            "family_context": data.family_context,
            "daily_routines": data.daily_routines,
            "parent_goals": data.parent_goals,
            "urgent_flags": data.urgent_flags,
            "filming_preference": data.filming_preference,
            "completeness": child.data_completeness,
            "video_count": child.video_count,
            "analyzed_video_count": child.analyzed_video_count,
            "artifact_ids": list(child.artifacts.keys()),
            "journal_entry_count": len(child.journal_entries),
        }

    def get_profile_summary(self, child_id: str) -> str:
        """Get brief profile for display"""
        child = self.get_or_create_child(child_id)
        return child.profile_summary

    # === Persistence Helpers ===

    def _load_child_sync(self, child_id: str) -> Optional[Child]:
        """Synchronous load for initialization"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._load_child(child_id))
                    return future.result(timeout=5)
            else:
                return loop.run_until_complete(self._load_child(child_id))
        except Exception as e:
            logger.warning(f"Could not load child synchronously: {e}")
            return None

    async def _load_child(self, child_id: str) -> Optional[Child]:
        """Load child from persistent storage"""
        try:
            if self._storage_type == "redis":
                data = await self._load_from_redis(child_id)
            else:
                data = await self._load_from_file(child_id)

            if not data:
                return None

            return self._dict_to_child(data)

        except Exception as e:
            logger.error(f"Error loading child {child_id}: {e}")
            return None

    async def _load_from_file(self, child_id: str) -> Optional[Dict[str, Any]]:
        """Load child from JSON file"""
        file_path = self._get_file_path(child_id)
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return self._restore_datetimes(data)
        except Exception as e:
            logger.error(f"Error loading from file {file_path}: {e}")
            return None

    async def _load_from_redis(self, child_id: str) -> Optional[Dict[str, Any]]:
        """Load child from Redis"""
        try:
            key = f"chitta:child:{child_id}"
            data_str = self._redis_client.get(key)
            if not data_str:
                return None
            data = json.loads(data_str)
            return self._restore_datetimes(data)
        except Exception as e:
            logger.error(f"Error loading from Redis: {e}")
            return None

    async def _save_to_file(self, child_id: str, data: Dict[str, Any]) -> bool:
        """Save child to JSON file"""
        file_path = self._get_file_path(child_id)
        try:
            serializable_data = self._make_serializable(data)
            temp_path = file_path.with_suffix(".tmp")

            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(serializable_data, f, ensure_ascii=False, indent=2)

            temp_path.rename(file_path)
            logger.debug(f"Saved child to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving to file {file_path}: {e}")
            return False

    async def _save_to_redis(self, child_id: str, data: Dict[str, Any]) -> bool:
        """Save child to Redis"""
        try:
            serializable_data = self._make_serializable(data)
            key = f"chitta:child:{child_id}"
            self._redis_client.setex(
                key,
                90 * 24 * 60 * 60,  # 90 days TTL
                json.dumps(serializable_data, ensure_ascii=False)
            )
            logger.debug(f"Saved child to Redis: {key}")
            return True
        except Exception as e:
            logger.error(f"Error saving to Redis: {e}")
            return False

    def _child_to_dict(self, child: Child) -> Dict[str, Any]:
        """Convert Child to dict for persistence"""
        return {
            "child_id": child.child_id,
            "developmental_data": child.developmental_data.dict(),
            "artifacts": {k: v.dict() for k, v in child.artifacts.items()},
            "videos": [v.dict() for v in child.videos],
            "journal_entries": [e.dict() for e in child.journal_entries],
            "data_completeness": child.data_completeness,
            "semantic_verification": child.semantic_verification,
            "created_at": child.created_at.isoformat(),
            "updated_at": child.updated_at.isoformat(),
        }

    def _dict_to_child(self, data: Dict[str, Any]) -> Child:
        """Convert dict to Child"""
        child = Child(
            child_id=data["child_id"],
            developmental_data=DevelopmentalData(**data.get("developmental_data", {})),
            data_completeness=data.get("data_completeness", 0.0),
            semantic_verification=data.get("semantic_verification"),
        )

        # Restore timestamps
        if data.get("created_at"):
            child.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            child.updated_at = datetime.fromisoformat(data["updated_at"])

        # Restore artifacts
        for artifact_id, artifact_data in data.get("artifacts", {}).items():
            child.artifacts[artifact_id] = Artifact(**artifact_data)

        # Restore videos
        for video_data in data.get("videos", []):
            child.videos.append(Video(**video_data))

        # Restore journal entries
        for entry_data in data.get("journal_entries", []):
            child.journal_entries.append(JournalEntry(**entry_data))

        return child

    def _make_serializable(self, obj: Any) -> Any:
        """Convert object to JSON-serializable format"""
        if isinstance(obj, datetime):
            return {"_type": "datetime", "_value": obj.isoformat()}
        elif isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(v) for v in obj]
        elif hasattr(obj, "dict"):
            return self._make_serializable(obj.dict())
        elif hasattr(obj, "__dict__"):
            return self._make_serializable(obj.__dict__)
        else:
            return obj

    def _restore_datetimes(self, obj: Any) -> Any:
        """Restore datetime objects from serialized format"""
        if isinstance(obj, dict):
            if obj.get("_type") == "datetime":
                return datetime.fromisoformat(obj["_value"])
            return {k: self._restore_datetimes(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._restore_datetimes(v) for v in obj]
        else:
            return obj


# Singleton
_child_service: Optional[ChildService] = None


def get_child_service() -> ChildService:
    """Get singleton ChildService instance"""
    global _child_service
    if _child_service is None:
        _child_service = ChildService()
    return _child_service
