"""
Configuration management layer for Wu Wei architecture.

This package provides configuration loaders for the domain-agnostic workflow system.
All workflow configurations (schemas, actions, views) are loaded from YAML files
and made available to services.

Key modules:
- config_loader: Base YAML loading and caching
- schema_registry: Extraction schema management
- action_registry: Action graph and prerequisites
- view_manager: Deep view routing
- app_information_service: FAQ and app help responses
"""

__version__ = "1.2.0"
