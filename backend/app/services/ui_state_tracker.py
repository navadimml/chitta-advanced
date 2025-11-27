"""
UI State Tracker - Tracks user's current view, progress, and interactions

🌟 Wu Wei: The LLM needs awareness of UI state to give accurate guidance.
This service tracks:
1. Current view/page the user is on
2. Progress states (video uploads, report generation)
3. Interaction history (what user viewed/clicked)

Usage:
    tracker = get_ui_state_tracker()
    tracker.update_from_request(family_id, ui_state_from_frontend)
    state = tracker.get_state(family_id)

The frontend sends UI state with each message request:
    {
        "current_view": "chat",
        "progress": {"videos_uploaded": 2, "videos_required": 3},
        "recent_interactions": ["viewed_guidelines", "clicked_upload"]
    }
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from enum import Enum

logger = logging.getLogger(__name__)


class ViewType(str, Enum):
    """Available views in the UI"""
    CHAT = "chat"
    GUIDELINES = "guidelines"
    UPLOAD = "upload"
    REPORT = "report"
    JOURNAL = "journal"
    EXPERTS = "experts"
    SETTINGS = "settings"
    CHILD_SPACE = "child_space"
    DEEP_VIEW = "deep_view"


class InteractionType(str, Enum):
    """Types of user interactions we track"""
    VIEWED_GUIDELINES = "viewed_guidelines"
    VIEWED_REPORT = "viewed_report"
    CLICKED_UPLOAD = "clicked_upload"
    UPLOADED_VIDEO = "uploaded_video"
    DISMISSED_CARD = "dismissed_card"
    EXPANDED_CARD = "expanded_card"
    CLICKED_ACTION = "clicked_action"
    OPENED_DEEP_VIEW = "opened_deep_view"
    SCROLLED_TO_BOTTOM = "scrolled_to_bottom"


class ProgressState(BaseModel):
    """Progress tracking for multi-step processes"""
    # Video upload progress
    videos_uploaded: int = 0
    videos_required: int = 3
    videos_analyzing: bool = False
    video_analysis_progress: int = 0  # 0-100%

    # Report generation progress
    report_generating: bool = False
    report_generation_progress: int = 0  # 0-100%

    # Guidelines
    guidelines_generating: bool = False

    # General
    last_action_at: Optional[datetime] = None


class UIState(BaseModel):
    """Complete UI state for a family session"""
    family_id: str
    current_view: ViewType = ViewType.CHAT
    previous_view: Optional[ViewType] = None

    # Progress tracking
    progress: ProgressState = Field(default_factory=ProgressState)

    # Recent interactions (last N interactions)
    recent_interactions: List[str] = Field(default_factory=list)
    max_interactions: int = 20  # Keep last 20 interactions

    # Timestamps
    view_entered_at: datetime = Field(default_factory=datetime.now)
    last_interaction_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.now)

    # Card state
    dismissed_cards: List[str] = Field(default_factory=list)
    expanded_cards: List[str] = Field(default_factory=list)

    # Deep view state
    current_deep_view: Optional[str] = None  # e.g., "guidelines_detail"

    class Config:
        use_enum_values = True


class UIStateTracker:
    """
    Tracks UI state per family session.

    State is updated by the frontend with each request and stored server-side.
    The LLM can query this state through the context buffer.
    """

    def __init__(self):
        self._states: Dict[str, UIState] = {}

    def get_state(self, family_id: str) -> UIState:
        """Get current UI state for a family"""
        if family_id not in self._states:
            self._states[family_id] = UIState(family_id=family_id)
        return self._states[family_id]

    def update_from_request(
        self,
        family_id: str,
        ui_state_data: Optional[Dict[str, Any]]
    ) -> UIState:
        """
        Update UI state from frontend request data.

        Args:
            family_id: Family identifier
            ui_state_data: UI state from frontend request, e.g.:
                {
                    "current_view": "upload",
                    "progress": {"videos_uploaded": 2},
                    "recent_interactions": ["clicked_upload"]
                }

        Returns:
            Updated UIState
        """
        state = self.get_state(family_id)

        if not ui_state_data:
            return state

        # Update current view
        if "current_view" in ui_state_data:
            new_view = ui_state_data["current_view"]
            if new_view != state.current_view:
                state.previous_view = state.current_view
                state.current_view = new_view
                state.view_entered_at = datetime.now()
                logger.debug(f"View changed: {state.previous_view} -> {state.current_view}")

        # Update progress
        if "progress" in ui_state_data:
            progress_data = ui_state_data["progress"]
            for key, value in progress_data.items():
                if hasattr(state.progress, key):
                    setattr(state.progress, key, value)
            state.progress.last_action_at = datetime.now()

        # Update recent interactions
        if "recent_interactions" in ui_state_data:
            new_interactions = ui_state_data["recent_interactions"]
            if isinstance(new_interactions, list):
                for interaction in new_interactions:
                    self._add_interaction(state, interaction)

        # Update card state
        if "dismissed_cards" in ui_state_data:
            state.dismissed_cards = ui_state_data["dismissed_cards"]
        if "expanded_cards" in ui_state_data:
            state.expanded_cards = ui_state_data["expanded_cards"]

        # Update deep view
        if "current_deep_view" in ui_state_data:
            state.current_deep_view = ui_state_data["current_deep_view"]

        state.updated_at = datetime.now()
        return state

    def _add_interaction(self, state: UIState, interaction: str):
        """Add an interaction to the history, maintaining max size"""
        state.recent_interactions.append(interaction)
        state.last_interaction_at = datetime.now()

        # Trim to max size
        if len(state.recent_interactions) > state.max_interactions:
            state.recent_interactions = state.recent_interactions[-state.max_interactions:]

    def record_interaction(self, family_id: str, interaction: str):
        """Record a single interaction"""
        state = self.get_state(family_id)
        self._add_interaction(state, interaction)
        state.updated_at = datetime.now()

    def set_view(self, family_id: str, view: str):
        """Set current view"""
        state = self.get_state(family_id)
        if view != state.current_view:
            state.previous_view = state.current_view
            state.current_view = view
            state.view_entered_at = datetime.now()
            state.updated_at = datetime.now()

    def update_progress(self, family_id: str, **progress_updates):
        """Update progress state"""
        state = self.get_state(family_id)
        for key, value in progress_updates.items():
            if hasattr(state.progress, key):
                setattr(state.progress, key, value)
        state.progress.last_action_at = datetime.now()
        state.updated_at = datetime.now()

    def has_viewed(self, family_id: str, item: str) -> bool:
        """Check if user has viewed a specific item"""
        state = self.get_state(family_id)
        view_interactions = [
            f"viewed_{item}",
            f"opened_{item}",
            f"clicked_{item}"
        ]
        return any(
            interaction in state.recent_interactions
            for interaction in view_interactions
        )

    def get_time_on_current_view(self, family_id: str) -> timedelta:
        """Get time spent on current view"""
        state = self.get_state(family_id)
        return datetime.now() - state.view_entered_at

    def get_context_dict(self, family_id: str) -> Dict[str, Any]:
        """
        Get UI state as a dictionary for context buffer.

        Returns flat key-value pairs suitable for context_buffer.set()
        """
        state = self.get_state(family_id)

        context = {
            # Current view
            "ui_state.current_view": state.current_view,
            "ui_state.previous_view": state.previous_view,
            "ui_state.time_on_view_seconds": int(self.get_time_on_current_view(family_id).total_seconds()),

            # Progress
            "ui_state.videos_uploaded": state.progress.videos_uploaded,
            "ui_state.videos_required": state.progress.videos_required,
            "ui_state.videos_remaining": state.progress.videos_required - state.progress.videos_uploaded,
            "ui_state.videos_analyzing": state.progress.videos_analyzing,
            "ui_state.video_analysis_progress": state.progress.video_analysis_progress,
            "ui_state.report_generating": state.progress.report_generating,
            "ui_state.report_generation_progress": state.progress.report_generation_progress,

            # Interaction summary
            "ui_state.has_viewed_guidelines": self.has_viewed(family_id, "guidelines"),
            "ui_state.has_viewed_report": self.has_viewed(family_id, "report"),
            "ui_state.recent_interactions": state.recent_interactions[-5:],  # Last 5

            # Deep view
            "ui_state.current_deep_view": state.current_deep_view,

            # Card state
            "ui_state.dismissed_cards": state.dismissed_cards,
        }

        return context

    def clear_state(self, family_id: str):
        """Clear UI state for a family"""
        if family_id in self._states:
            del self._states[family_id]


# Singleton instance
_ui_state_tracker: Optional[UIStateTracker] = None


def get_ui_state_tracker() -> UIStateTracker:
    """Get the UI state tracker singleton"""
    global _ui_state_tracker
    if _ui_state_tracker is None:
        _ui_state_tracker = UIStateTracker()
    return _ui_state_tracker
