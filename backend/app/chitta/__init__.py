"""
Chitta Core - Simplified, AI-trusting conversation system

This package implements the new philosophy:
- Trust the AI's intelligence to guide conversations
- Simple tools with natural-language prerequisites
- Child-centric Gestalt as context
- No complex state machines or prerequisite code

Key components:
- ChittaService: Main orchestration for conversations
- Gestalt: Holistic understanding of the child (data only)
- Tools: Available actions with natural-language prerequisites
- Prompt: System prompt builder (English, Chitta-leads)
"""

from .service import ChittaService, get_chitta_service
from .gestalt import build_gestalt, Gestalt, get_what_we_know, get_what_we_need
from .tools import CHITTA_TOOLS, get_chitta_tools
from .prompt import build_system_prompt

__all__ = [
    # Service
    "ChittaService",
    "get_chitta_service",
    # Gestalt
    "build_gestalt",
    "Gestalt",
    "get_what_we_know",
    "get_what_we_need",
    # Tools
    "CHITTA_TOOLS",
    "get_chitta_tools",
    # Prompt
    "build_system_prompt",
]
