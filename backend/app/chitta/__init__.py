"""
Chitta Core - Darshan Architecture

Darshan is the **observing intelligence** - not a data container.
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

# === Darshan Architecture ===

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


__all__ = [
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
]
