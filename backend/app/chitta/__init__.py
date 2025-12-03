"""
Chitta Core - Simplified, AI-trusting conversation system

This package implements the new philosophy:
- Trust the AI's intelligence to guide conversations
- Simple tools with natural-language prerequisites
- Child-centric Gestalt as context
- No complex state machines or prerequisite code

Key components:
- ChittaService: Main orchestration for conversations (fast path)
- ReflectionService: Background processing for patterns/memory (slow path)
- Gestalt: Holistic understanding of the child (data only)
- Tools: Available actions with natural-language prerequisites
- Prompt: System prompt builder (English, Chitta-leads)

Two Cognitive Modes:
- Fast Path (ChittaService): 1-2 second responses during conversation
- Slow Path (ReflectionService): Background processing for deep analysis
"""

from .service import ChittaService, get_chitta_service
from .gestalt import build_gestalt, Gestalt, get_what_we_know, get_what_we_need
from .tools import CHITTA_TOOLS, get_chitta_tools, get_core_extraction_tools
from .prompt import build_system_prompt
from .reflection import ReflectionService, get_reflection_service
from .cards import derive_cards_from_child, handle_card_action
from .api_transform import (
    transform_child_for_api,
    transform_session_for_api,
    transform_card_for_api,
    build_api_response,
    strip_internal_fields,
)

__all__ = [
    # Service (fast path)
    "ChittaService",
    "get_chitta_service",
    # Reflection (slow path)
    "ReflectionService",
    "get_reflection_service",
    # Gestalt
    "build_gestalt",
    "Gestalt",
    "get_what_we_know",
    "get_what_we_need",
    # Tools
    "CHITTA_TOOLS",
    "get_chitta_tools",
    "get_core_extraction_tools",
    # Prompt
    "build_system_prompt",
    # Cards
    "derive_cards_from_child",
    "handle_card_action",
    # API Transformation
    "transform_child_for_api",
    "transform_session_for_api",
    "transform_card_for_api",
    "build_api_response",
    "strip_internal_fields",
]
