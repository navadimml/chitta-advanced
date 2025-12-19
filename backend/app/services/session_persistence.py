"""
Session Persistence - Interim file-based storage for session state

🌟 Wu Wei: Simple persistence layer to survive server restarts
This is a temporary solution until Graphiti integration is complete.

Storage options (configured via environment):
- FILE: JSON files in data directory (default, simplest)
- REDIS: Redis key-value store (faster, production-ready)

This module provides:
1. Save/load session state to persistent storage
2. Automatic backup on each update
3. Recovery on server startup
"""

import logging
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)

# Storage configuration
STORAGE_TYPE = os.getenv("SESSION_STORAGE_TYPE", "file")  # "file" or "redis"
DATA_DIR = os.getenv("SESSION_DATA_DIR", "data/sessions")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Ensure data directory exists
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)


class SessionPersistence:
    """
    Handles persistent storage of session state

    Supports file-based storage (default) or Redis (production)
    """

    def __init__(self, storage_type: str = None):
        self.storage_type = storage_type or STORAGE_TYPE
        self._redis_client = None

        if self.storage_type == "redis":
            self._init_redis()

        logger.info(f"SessionPersistence initialized with {self.storage_type} storage")

    def _init_redis(self):
        """Initialize Redis connection if using Redis storage"""
        try:
            import redis
            self._redis_client = redis.from_url(REDIS_URL, decode_responses=True)
            self._redis_client.ping()
            logger.info(f"Connected to Redis at {REDIS_URL}")
        except ImportError:
            logger.warning("Redis package not installed, falling back to file storage")
            self.storage_type = "file"
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}, falling back to file storage")
            self.storage_type = "file"

    def _get_file_path(self, family_id: str) -> Path:
        """Get file path for a family's session"""
        # Sanitize family_id for filesystem
        safe_id = "".join(c if c.isalnum() or c in "_-" else "_" for c in family_id)
        return Path(DATA_DIR) / f"{safe_id}.json"

    async def save_session(self, family_id: str, session_data: Dict[str, Any]) -> bool:
        """
        Save session data to persistent storage

        Args:
            family_id: Unique family identifier
            session_data: Session state to persist

        Returns:
            True if saved successfully
        """
        try:
            # Add metadata
            session_data["_persisted_at"] = datetime.now().isoformat()
            session_data["_family_id"] = family_id

            if self.storage_type == "redis":
                return await self._save_to_redis(family_id, session_data)
            else:
                return await self._save_to_file(family_id, session_data)

        except Exception as e:
            logger.error(f"Error saving session {family_id}: {e}")
            return False

    async def _save_to_file(self, family_id: str, session_data: Dict[str, Any]) -> bool:
        """Save session to JSON file"""
        file_path = self._get_file_path(family_id)

        try:
            # Convert datetime objects to ISO strings
            serializable_data = self._make_serializable(session_data)

            # Write to temp file first, then rename (atomic operation)
            temp_path = file_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(serializable_data, f, ensure_ascii=False, indent=2)

            # Atomic rename
            temp_path.rename(file_path)

            logger.debug(f"Saved session to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving to file {file_path}: {e}")
            return False

    async def _save_to_redis(self, family_id: str, session_data: Dict[str, Any]) -> bool:
        """Save session to Redis"""
        try:
            serializable_data = self._make_serializable(session_data)
            key = f"chitta:session:{family_id}"

            # Store as JSON string with 30-day TTL
            self._redis_client.setex(
                key,
                30 * 24 * 60 * 60,  # 30 days in seconds
                json.dumps(serializable_data, ensure_ascii=False)
            )

            logger.debug(f"Saved session to Redis: {key}")
            return True

        except Exception as e:
            logger.error(f"Error saving to Redis: {e}")
            return False

    async def load_session(self, family_id: str) -> Optional[Dict[str, Any]]:
        """
        Load session data from persistent storage

        Args:
            family_id: Unique family identifier

        Returns:
            Session data dict or None if not found
        """
        try:
            if self.storage_type == "redis":
                return await self._load_from_redis(family_id)
            else:
                return await self._load_from_file(family_id)

        except Exception as e:
            logger.error(f"Error loading session {family_id}: {e}")
            return None

    async def _load_from_file(self, family_id: str) -> Optional[Dict[str, Any]]:
        """Load session from JSON file"""
        file_path = self._get_file_path(family_id)

        if not file_path.exists():
            logger.debug(f"No persisted session found for {family_id}")
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Convert ISO strings back to datetime
            data = self._restore_datetimes(data)

            logger.info(f"Loaded persisted session for {family_id}")
            return data

        except Exception as e:
            logger.error(f"Error loading from file {file_path}: {e}")
            return None

    async def _load_from_redis(self, family_id: str) -> Optional[Dict[str, Any]]:
        """Load session from Redis"""
        try:
            key = f"chitta:session:{family_id}"
            data_str = self._redis_client.get(key)

            if not data_str:
                logger.debug(f"No persisted session found in Redis for {family_id}")
                return None

            data = json.loads(data_str)
            data = self._restore_datetimes(data)

            logger.info(f"Loaded persisted session from Redis for {family_id}")
            return data

        except Exception as e:
            logger.error(f"Error loading from Redis: {e}")
            return None

    async def delete_session(self, family_id: str) -> bool:
        """Delete a persisted session"""
        try:
            if self.storage_type == "redis":
                key = f"chitta:session:{family_id}"
                self._redis_client.delete(key)
            else:
                file_path = self._get_file_path(family_id)
                if file_path.exists():
                    file_path.unlink()

            logger.info(f"Deleted persisted session for {family_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting session {family_id}: {e}")
            return False

    async def list_sessions(self) -> list[str]:
        """List all persisted session family IDs"""
        try:
            if self.storage_type == "redis":
                keys = self._redis_client.keys("chitta:session:*")
                return [k.replace("chitta:session:", "") for k in keys]
            else:
                files = Path(DATA_DIR).glob("*.json")
                return [f.stem for f in files]

        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return []

    def _make_serializable(self, obj: Any) -> Any:
        """Convert object to JSON-serializable format"""
        if isinstance(obj, datetime):
            return {"_type": "datetime", "_value": obj.isoformat()}
        elif isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(v) for v in obj]
        elif hasattr(obj, "model_dump"):
            return self._make_serializable(obj.model_dump())
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
_session_persistence: Optional[SessionPersistence] = None


def get_session_persistence() -> SessionPersistence:
    """Get singleton SessionPersistence instance"""
    global _session_persistence
    if _session_persistence is None:
        _session_persistence = SessionPersistence()
    return _session_persistence


async def save_session_state(family_id: str, session_data: Dict[str, Any]) -> bool:
    """Convenience function to save session state"""
    persistence = get_session_persistence()
    return await persistence.save_session(family_id, session_data)


async def load_session_state(family_id: str) -> Optional[Dict[str, Any]]:
    """Convenience function to load session state"""
    persistence = get_session_persistence()
    return await persistence.load_session(family_id)
