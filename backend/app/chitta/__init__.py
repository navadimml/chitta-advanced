"""
Chitta Core - Darshan Architecture

Darshan (दर्शन) is the **observing intelligence** - not a data container.
Understanding emerges through **curiosity**, not checklists.

Key components:
- Darshan: The observing intelligence with 3 public methods
- ChittaService: Thin orchestration layer
- Curiosities: Manages what we're curious about
- SynthesisService: On-demand deep analysis

Two-Phase LLM Architecture:
- Phase 1: Perception with tools (temp=0.0)
- Phase 2: Response without tools (temp=0.7)

Tool calls and text response CANNOT be reliably combined.
"""

# === New Architecture (Active) ===

from .service import ChittaService, get_chitta_service
from .gestalt import Darshan
from .curiosity import Curiosity, Curiosities, create_hypothesis, create_question, create_pattern, create_discovery
from .tools import get_perception_tools, PERCEPTION_TOOLS
from .synthesis import SynthesisService, get_synthesis_service
from .models import (
    Understanding,
    TemporalFact,
    Evidence,
    Story,
    Exploration,
    JournalEntry,
    Pattern,
    Response,
    SynthesisReport,
    ConversationMemory,
    VideoScenario,
)
from .formatting import (
    format_understanding,
    format_curiosities,
    format_explorations,
    format_perception_summary,
)

# === Deprecated (for backward compatibility) ===
# These imports allow existing code to continue working during transition

try:
    from .gestalt_deprecated import build_gestalt, Gestalt, get_what_we_know, get_what_we_need
except ImportError:
    build_gestalt = None
    Gestalt = None
    get_what_we_know = None
    get_what_we_need = None

try:
    from .tools_deprecated import CHITTA_TOOLS, get_chitta_tools, get_core_extraction_tools
except ImportError:
    CHITTA_TOOLS = None
    get_chitta_tools = None
    get_core_extraction_tools = None

try:
    from .prompt_deprecated import build_system_prompt
except ImportError:
    build_system_prompt = None

try:
    from .reflection_deprecated import ReflectionService as ReflectionServiceDeprecated, get_reflection_service
except ImportError:
    ReflectionServiceDeprecated = None
    get_reflection_service = None

try:
    from .cards_deprecated import derive_cards_from_child, handle_card_action
except ImportError:
    derive_cards_from_child = None
    handle_card_action = None

try:
    from .api_transform_deprecated import (
        transform_child_for_api,
        transform_session_for_api,
        transform_card_for_api,
        build_api_response,
        strip_internal_fields,
    )
except ImportError:
    transform_child_for_api = None
    transform_session_for_api = None
    transform_card_for_api = None
    build_api_response = None
    strip_internal_fields = None


__all__ = [
    # === Darshan Architecture ===
    # Service
    "ChittaService",
    "get_chitta_service",
    # Darshan
    "Darshan",
    # Curiosity
    "Curiosity",
    "Curiosities",
    "create_hypothesis",
    "create_question",
    "create_pattern",
    "create_discovery",
    # Tools
    "get_perception_tools",
    "PERCEPTION_TOOLS",
    # Synthesis
    "SynthesisService",
    "get_synthesis_service",
    # Models
    "Understanding",
    "TemporalFact",
    "Evidence",
    "Story",
    "Exploration",
    "JournalEntry",
    "Pattern",
    "Response",
    "SynthesisReport",
    "ConversationMemory",
    "VideoScenario",
    # Formatting
    "format_understanding",
    "format_curiosities",
    "format_explorations",
    "format_perception_summary",
    # === Deprecated (backward compatibility) ===
    "build_gestalt",
    "Gestalt",
    "get_what_we_know",
    "get_what_we_need",
    "CHITTA_TOOLS",
    "get_chitta_tools",
    "get_core_extraction_tools",
    "build_system_prompt",
    "ReflectionServiceDeprecated",
    "get_reflection_service",
    "derive_cards_from_child",
    "handle_card_action",
    "transform_child_for_api",
    "transform_session_for_api",
    "transform_card_for_api",
    "build_api_response",
    "strip_internal_fields",
]
