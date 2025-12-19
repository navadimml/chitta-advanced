"""
Configuration management layer for Wu Wei architecture.

This package provides configuration loaders for the domain-agnostic workflow system.
All workflow configurations (schemas, actions, artifacts, cards, views, moments) are
loaded from YAML files and made available to services.

Key modules:
- config_loader: Base YAML loading and caching
- schema_registry: Extraction schema management
- action_registry: Action graph and prerequisites
- artifact_manager: Artifact lifecycle
- card_generator: Context card generation
- view_manager: Deep view routing

Note: Phase-based workflow (phases.yaml, phase_manager.py) has been removed.
Wu Wei architecture uses artifact-based state inference instead of explicit phases.
"""

__version__ = "1.1.0"
