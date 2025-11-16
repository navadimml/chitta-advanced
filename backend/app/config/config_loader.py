"""
Base configuration loader for YAML-based workflow configurations.

This module provides the foundation for loading, validating, and caching
all workflow configuration files.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration loading or validation fails."""
    pass


class ConfigLoader:
    """
    Base configuration loader for YAML files.

    Provides:
    - Safe YAML loading
    - Path resolution
    - Caching
    - Validation
    - Error handling
    """

    def __init__(self, config_base_path: Optional[Path] = None):
        """
        Initialize configuration loader.

        Args:
            config_base_path: Base directory for config files.
                            Defaults to backend/config/
        """
        if config_base_path is None:
            # Resolve path relative to this file
            # backend/app/config/config_loader.py -> backend/config/
            self.config_base_path = Path(__file__).parent.parent.parent / "config"
        else:
            self.config_base_path = Path(config_base_path)

        if not self.config_base_path.exists():
            raise ConfigurationError(
                f"Configuration directory not found: {self.config_base_path}"
            )

        logger.info(f"ConfigLoader initialized with base path: {self.config_base_path}")

    def load_yaml(self, relative_path: str) -> Dict[str, Any]:
        """
        Load a YAML configuration file.

        Args:
            relative_path: Path relative to config_base_path

        Returns:
            Parsed YAML as dictionary

        Raises:
            ConfigurationError: If file not found or invalid YAML
        """
        file_path = self.config_base_path / relative_path

        if not file_path.exists():
            raise ConfigurationError(
                f"Configuration file not found: {file_path}"
            )

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            if config is None:
                raise ConfigurationError(f"Empty configuration file: {file_path}")

            logger.debug(f"Loaded configuration from: {relative_path}")
            return config

        except yaml.YAMLError as e:
            raise ConfigurationError(
                f"Invalid YAML in {file_path}: {str(e)}"
            ) from e
        except Exception as e:
            raise ConfigurationError(
                f"Error loading {file_path}: {str(e)}"
            ) from e

    def validate_required_fields(
        self,
        config: Dict[str, Any],
        required_fields: list[str],
        config_name: str
    ) -> None:
        """
        Validate that required fields exist in configuration.

        Args:
            config: Configuration dictionary
            required_fields: List of required field names
            config_name: Name of configuration (for error messages)

        Raises:
            ConfigurationError: If required fields missing
        """
        missing = [field for field in required_fields if field not in config]

        if missing:
            raise ConfigurationError(
                f"{config_name} missing required fields: {', '.join(missing)}"
            )

    def validate_version(
        self,
        config: Dict[str, Any],
        expected_version: str,
        config_name: str
    ) -> None:
        """
        Validate configuration version.

        Args:
            config: Configuration dictionary
            expected_version: Expected version string
            config_name: Name of configuration (for error messages)

        Raises:
            ConfigurationError: If version mismatch
        """
        actual_version = config.get("version")

        if actual_version != expected_version:
            logger.warning(
                f"{config_name} version mismatch: "
                f"expected {expected_version}, got {actual_version}"
            )


class WorkflowConfigLoader(ConfigLoader):
    """
    Specialized loader for workflow configurations.

    Loads all workflow-related configs:
    - extraction_schema.yaml
    - action_graph.yaml
    - phases.yaml
    - artifacts.yaml
    - context_cards.yaml
    - deep_views.yaml
    """

    def __init__(self):
        super().__init__()
        self.workflows_path = "workflows"
        self.schemas_path = "schemas"
        self._cache: Dict[str, Dict[str, Any]] = {}

    @lru_cache(maxsize=1)
    def load_extraction_schema(self) -> Dict[str, Any]:
        """Load extraction schema configuration."""
        if "extraction_schema" not in self._cache:
            config = self.load_yaml(f"{self.schemas_path}/extraction_schema.yaml")
            self.validate_required_fields(
                config,
                ["version", "schema_name", "fields"],
                "extraction_schema.yaml"
            )
            self._cache["extraction_schema"] = config

        return self._cache["extraction_schema"]

    @lru_cache(maxsize=1)
    def load_action_graph(self) -> Dict[str, Any]:
        """Load action graph configuration."""
        if "action_graph" not in self._cache:
            config = self.load_yaml(f"{self.workflows_path}/action_graph.yaml")
            self.validate_required_fields(
                config,
                ["version", "graph_name", "actions"],
                "action_graph.yaml"
            )
            self._cache["action_graph"] = config

        return self._cache["action_graph"]

    @lru_cache(maxsize=1)
    def load_phases(self) -> Dict[str, Any]:
        """Load phases configuration."""
        if "phases" not in self._cache:
            config = self.load_yaml(f"{self.workflows_path}/phases.yaml")
            self.validate_required_fields(
                config,
                ["version", "workflow_name", "phases", "initial_phase"],
                "phases.yaml"
            )
            self._cache["phases"] = config

        return self._cache["phases"]

    @lru_cache(maxsize=1)
    def load_artifacts(self) -> Dict[str, Any]:
        """Load artifacts configuration."""
        if "artifacts" not in self._cache:
            config = self.load_yaml(f"{self.workflows_path}/artifacts.yaml")
            self.validate_required_fields(
                config,
                ["version", "artifact_catalog_name", "artifacts"],
                "artifacts.yaml"
            )
            self._cache["artifacts"] = config

        return self._cache["artifacts"]

    @lru_cache(maxsize=1)
    def load_context_cards(self) -> Dict[str, Any]:
        """Load context cards configuration."""
        if "context_cards" not in self._cache:
            config = self.load_yaml(f"{self.workflows_path}/context_cards.yaml")
            self.validate_required_fields(
                config,
                ["version", "card_system_name", "cards"],
                "context_cards.yaml"
            )
            self._cache["context_cards"] = config

        return self._cache["context_cards"]

    @lru_cache(maxsize=1)
    def load_deep_views(self) -> Dict[str, Any]:
        """Load deep views configuration."""
        if "deep_views" not in self._cache:
            config = self.load_yaml(f"{self.workflows_path}/deep_views.yaml")
            self.validate_required_fields(
                config,
                ["version", "view_system_name", "views"],
                "deep_views.yaml"
            )
            self._cache["deep_views"] = config

        return self._cache["deep_views"]

    @lru_cache(maxsize=1)
    def load_lifecycle_events(self) -> Dict[str, Any]:
        """Load lifecycle events configuration (Wu Wei simplified moments structure)."""
        if "lifecycle_events" not in self._cache:
            config = self.load_yaml(f"{self.workflows_path}/lifecycle_events.yaml")
            self.validate_required_fields(
                config,
                ["version", "workflow_name", "moments", "always_available"],
                "lifecycle_events.yaml"
            )
            self._cache["lifecycle_events"] = config

        return self._cache["lifecycle_events"]

    def load_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Load all workflow configurations.

        Returns:
            Dictionary containing all loaded configurations
        """
        return {
            "extraction_schema": self.load_extraction_schema(),
            "action_graph": self.load_action_graph(),
            "phases": self.load_phases(),
            "artifacts": self.load_artifacts(),
            "context_cards": self.load_context_cards(),
            "deep_views": self.load_deep_views(),
            "lifecycle_events": self.load_lifecycle_events(),
        }

    def clear_cache(self) -> None:
        """Clear configuration cache. Useful for development/testing."""
        self._cache.clear()
        self.load_extraction_schema.cache_clear()
        self.load_action_graph.cache_clear()
        self.load_phases.cache_clear()
        self.load_artifacts.cache_clear()
        self.load_context_cards.cache_clear()
        self.load_deep_views.cache_clear()
        self.load_lifecycle_events.cache_clear()
        logger.info("Configuration cache cleared")


# Global singleton instance
_workflow_config_loader: Optional[WorkflowConfigLoader] = None


def get_workflow_config_loader() -> WorkflowConfigLoader:
    """
    Get global WorkflowConfigLoader instance (singleton pattern).

    Returns:
        WorkflowConfigLoader instance
    """
    global _workflow_config_loader

    if _workflow_config_loader is None:
        _workflow_config_loader = WorkflowConfigLoader()

    return _workflow_config_loader


# Convenience functions for direct config access
def load_extraction_schema() -> Dict[str, Any]:
    """Load extraction schema configuration."""
    return get_workflow_config_loader().load_extraction_schema()


def load_action_graph() -> Dict[str, Any]:
    """Load action graph configuration."""
    return get_workflow_config_loader().load_action_graph()


def load_phases() -> Dict[str, Any]:
    """Load phases configuration."""
    return get_workflow_config_loader().load_phases()


def load_artifacts() -> Dict[str, Any]:
    """Load artifacts configuration."""
    return get_workflow_config_loader().load_artifacts()


def load_context_cards() -> Dict[str, Any]:
    """Load context cards configuration."""
    return get_workflow_config_loader().load_context_cards()


def load_deep_views() -> Dict[str, Any]:
    """Load deep views configuration."""
    return get_workflow_config_loader().load_deep_views()


def load_lifecycle_events() -> Dict[str, Any]:
    """Load lifecycle events configuration (Wu Wei dependency graph)."""
    return get_workflow_config_loader().load_lifecycle_events()


# === App Configuration Loader ===

class AppConfigLoader(ConfigLoader):
    """
    Loader for application-level configuration.

    Loads app_config.yaml for runtime settings like:
    - Conversation architecture mode
    - Feature flags
    - LLM provider settings
    """

    def __init__(self):
        # Config base path is backend/config/
        super().__init__()
        self._cache: Dict[str, Any] = {}

    @lru_cache(maxsize=1)
    def load_app_config(self) -> Dict[str, Any]:
        """Load application configuration."""
        if "app_config" not in self._cache:
            config = self.load_yaml("app_config.yaml")
            self.validate_required_fields(
                config,
                ["version", "app_name", "conversation"],
                "app_config.yaml"
            )
            self._cache["app_config"] = config

        return self._cache["app_config"]

    def get_conversation_architecture(self) -> str:
        """Get conversation architecture mode: 'simplified' or 'full'"""
        config = self.load_app_config()
        return config.get("conversation", {}).get("architecture", "simplified")

    def is_simplified_architecture(self) -> bool:
        """Check if simplified architecture is enabled"""
        return self.get_conversation_architecture() == "simplified"

    def get_feature_flag(self, feature_name: str, default: bool = False) -> bool:
        """Get feature flag value"""
        config = self.load_app_config()
        return config.get("features", {}).get(feature_name, default)

    def clear_cache(self) -> None:
        """Clear configuration cache."""
        self._cache.clear()
        self.load_app_config.cache_clear()
        logger.info("App configuration cache cleared")


# Global singleton instance for app config
_app_config_loader: Optional[AppConfigLoader] = None


def get_app_config_loader() -> AppConfigLoader:
    """
    Get global AppConfigLoader instance (singleton pattern).

    Returns:
        AppConfigLoader instance
    """
    global _app_config_loader

    if _app_config_loader is None:
        _app_config_loader = AppConfigLoader()

    return _app_config_loader


def load_app_config() -> Dict[str, Any]:
    """Load application configuration."""
    return get_app_config_loader().load_app_config()


def get_conversation_architecture() -> str:
    """Get conversation architecture mode: 'simplified' or 'full'"""
    return get_app_config_loader().get_conversation_architecture()


def is_simplified_architecture() -> bool:
    """Check if simplified architecture is enabled"""
    return get_app_config_loader().is_simplified_architecture()
