"""
View manager for deep view management.

Manages deep view definitions and routing from deep_views.yaml configuration.
"""

from typing import Dict, Any, List, Optional
import logging

from app.config.config_loader import load_deep_views

logger = logging.getLogger(__name__)


class ViewManager:
    """
    Manager for deep views.

    Provides access to view definitions and availability checks.
    """

    def __init__(self):
        """Initialize view manager."""
        self._view_config = load_deep_views()
        self._views: Dict[str, Dict[str, Any]] = {}
        self._load_views()

    def _load_views(self) -> None:
        """Load view definitions from configuration."""
        views_config = self._view_config.get("views", {})
        self._views = views_config
        logger.info(f"Loaded {len(self._views)} view definitions")

    def get_view(self, view_id: str) -> Optional[Dict[str, Any]]:
        """
        Get view definition by ID.

        Args:
            view_id: View identifier

        Returns:
            View configuration dict or None
        """
        return self._views.get(view_id)

    def get_all_views(self) -> Dict[str, Dict[str, Any]]:
        """Get all view definitions."""
        return self._views.copy()

    def check_view_availability(
        self,
        view_id: str,
        context: Dict[str, Any]
    ) -> bool:
        """
        Check if a view is available in current context.

        Args:
            view_id: View identifier
            context: Session context

        Returns:
            True if view is available
        """
        view = self.get_view(view_id)
        if not view:
            return False

        availability = view.get("availability", {})

        # Check phase
        phases = availability.get("phases", [])
        current_phase = context.get("phase", "screening")

        if phases and current_phase not in phases:
            return False

        # Check requires (simplified)
        requires = availability.get("requires", [])
        for req in requires:
            if req == "reports_available":
                if not context.get("reports_ready", False):
                    return False

        return True

    def get_available_views(
        self,
        context: Dict[str, Any]
    ) -> List[str]:
        """
        Get views available in current context.

        Args:
            context: Session context

        Returns:
            List of view IDs
        """
        return [
            view_id
            for view_id in self._views.keys()
            if self.check_view_availability(view_id, context)
        ]


# Global singleton
_view_manager: Optional[ViewManager] = None


def get_view_manager() -> ViewManager:
    """Get global ViewManager instance."""
    global _view_manager
    if _view_manager is None:
        _view_manager = ViewManager()
    return _view_manager
