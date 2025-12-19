"""
Artifact manager for artifact lifecycle management.

Provides access to artifact definitions and lifecycle management
from artifacts.yaml configuration.

🌟 Wu Wei v2.0: Generator config is now inline in artifacts.yaml
(artifact_generators.yaml has been merged)
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import logging

from app.config.config_loader import load_artifacts

logger = logging.getLogger(__name__)


class ArtifactDefinition(BaseModel):
    """Definition of an artifact."""
    artifact_id: str
    name: str
    name_en: Optional[str] = None
    type: str
    description: str
    states: List[str]
    storage: str
    generator: Optional[Dict[str, Any]] = None
    created_by: Optional[str] = None  # "user" for user-created artifacts
    validation: Optional[Dict[str, Any]] = None
    is_collection: bool = False


class ArtifactManager:
    """
    Manager for artifact definitions and lifecycle.

    🌟 Wu Wei v2.0: Generator config is now inline in each artifact definition
    (artifact_generators.yaml merged into artifacts.yaml)
    """

    def __init__(self):
        """Initialize artifact manager."""
        self._artifact_config = load_artifacts()
        self._artifacts: Dict[str, Dict[str, Any]] = {}
        self._load_artifacts()

    def _load_artifacts(self) -> None:
        """Load artifact definitions from configuration."""
        artifacts_config = self._artifact_config.get("artifacts", {})
        self._artifacts = artifacts_config

        # Count artifacts with generators
        generator_count = sum(1 for a in artifacts_config.values() if a.get("generator"))
        logger.info(f"Loaded {len(self._artifacts)} artifact definitions ({generator_count} with generators)")

    def get_generator_config(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """
        🌟 Wu Wei v2.0: Get generator configuration for an artifact.

        Generator config is now inline in each artifact definition.

        Args:
            artifact_id: Artifact identifier (e.g., "baseline_video_guidelines")

        Returns:
            Generator config dict with 'method', 'requires_artifacts', etc.
            or None if artifact is user-created or not found
        """
        artifact = self._artifacts.get(artifact_id)
        if artifact:
            return artifact.get("generator")
        return None

    def get_artifact(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """
        Get artifact definition by ID.

        Args:
            artifact_id: Artifact identifier

        Returns:
            Artifact configuration dict or None
        """
        return self._artifacts.get(artifact_id)

    def get_all_artifacts(self) -> Dict[str, Dict[str, Any]]:
        """Get all artifact definitions."""
        return self._artifacts.copy()

    def get_system_generated_artifacts(self) -> List[str]:
        """
        🌟 Wu Wei v2.0: Get artifacts that are system-generated (have generators).

        Returns:
            List of artifact IDs that have generator config
        """
        return [
            artifact_id
            for artifact_id, artifact in self._artifacts.items()
            if artifact.get("generator") is not None
        ]

    def get_user_created_artifacts(self) -> List[str]:
        """
        🌟 Wu Wei v2.0: Get artifacts that are user-created.

        Returns:
            List of artifact IDs created by users
        """
        return [
            artifact_id
            for artifact_id, artifact in self._artifacts.items()
            if artifact.get("created_by") == "user"
        ]

    def get_artifact_states(self, artifact_id: str) -> List[str]:
        """
        Get possible states for an artifact.

        Args:
            artifact_id: Artifact identifier

        Returns:
            List of state names
        """
        artifact = self.get_artifact(artifact_id)
        return artifact.get("states", []) if artifact else []


# Global singleton
_artifact_manager: Optional[ArtifactManager] = None


def get_artifact_manager() -> ArtifactManager:
    """Get global ArtifactManager instance."""
    global _artifact_manager
    if _artifact_manager is None:
        _artifact_manager = ArtifactManager()
    return _artifact_manager
