"""
Configuration management layer for Wu Wei architecture.

This package provides configuration loaders for the domain-agnostic workflow system.
All workflow configurations (schemas, actions, phases, artifacts, cards, views) are
loaded from YAML files and made available to services.

Key modules:
- config_loader: Base YAML loading and caching
- schema_registry: Extraction schema management
- action_registry: Action graph and prerequisites
- phase_manager: Phase transitions and behavior
- artifact_manager: Artifact lifecycle
- card_generator: Context card generation
- view_manager: Deep view routing
"""

__version__ = "1.0.0"
