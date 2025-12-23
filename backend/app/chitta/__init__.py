"""
Chitta Core - Darshan Architecture

Darshan is the **observing intelligence** - not a data container.
Understanding emerges through **curiosity**, not checklists.

Key components:
- Darshan: The observing intelligence (gestalt.py)
- ChittaService: Thin orchestration layer (service.py)
- Curiosities: Manages what we're curious about

Specialized services (delegated from ChittaService):
- GestaltManager: Darshan lifecycle & persistence
- VideoService: Video consent → guidelines → upload → analysis
- ChildSpaceService: Living Portrait derivation
- SharingService: Shareable summary generation
- CardsService: Context card derivation
- JournalService: Parent journal processing
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

# === Specialized Services ===

from .gestalt_manager import GestaltManager, get_gestalt_manager
from .video_service import VideoService, get_video_service
from .child_space import ChildSpaceService, get_child_space_service
from .sharing import SharingService, get_sharing_service
from .cards import CardsService, get_cards_service
from .journal_service import JournalService, get_journal_service
from .models import (
    Understanding,
    TemporalFact,
    Evidence,
    Story,
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
    format_perception_summary,
)


__all__ = [
    # Service (thin orchestrator)
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
    # Specialized Services
    "GestaltManager",
    "get_gestalt_manager",
    "VideoService",
    "get_video_service",
    "ChildSpaceService",
    "get_child_space_service",
    "SharingService",
    "get_sharing_service",
    "CardsService",
    "get_cards_service",
    "JournalService",
    "get_journal_service",
    "SynthesisService",
    "get_synthesis_service",
    # Models
    "Understanding",
    "TemporalFact",
    "Evidence",
    "Story",
    "JournalEntry",
    "Pattern",
    "Response",
    "SynthesisReport",
    "ConversationMemory",
    "VideoScenario",
    # Formatting
    "format_understanding",
    "format_curiosities",
    "format_perception_summary",
]
