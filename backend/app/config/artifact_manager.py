"""
Artifact manager for artifact lifecycle management.

Provides access to artifact definitions and lifecycle management
from artifacts.yaml configuration.
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
    name_en: str
    type: str
    description: str
    created_by: str  # system or user
    trigger: Dict[str, Any]
    states: List[str]
    storage_pattern: str
    available_in_phases: List[str]


class ArtifactManager:
    """
    Manager for artifact definitions and lifecycle.

    Provides access to artifact metadata and lifecycle information.
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
        logger.info(f"Loaded {len(self._artifacts)} artifact definitions")

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

    def get_artifacts_for_phase(self, phase: str) -> List[str]:
        """
        Get artifacts available in a phase.

        Args:
            phase: Phase identifier

        Returns:
            List of artifact IDs available in this phase
        """
        return [
            artifact_id
            for artifact_id, artifact in self._artifacts.items()
            if phase in artifact.get("available_in_phases", [])
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
