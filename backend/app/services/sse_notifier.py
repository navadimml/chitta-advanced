"""
Server-Sent Events (SSE) Notifier Service

Provides real-time updates to frontend for:
- Card changes when artifacts update
- State changes during background processing
- Lifecycle events

Wu Wei Philosophy: Frontend observes state changes naturally,
no polling needed.
"""

import asyncio
import logging
from typing import Dict, Set, Optional, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class SSENotifier:
    """
    Manages SSE connections and broadcasts state updates.

    Usage:
        notifier = get_sse_notifier()
        await notifier.notify_state_change(family_id, {"cards": [...], "artifacts": {...}})
    """

    def __init__(self):
        # Map: family_id -> Set of asyncio.Queue objects (one per client connection)
        self.connections: Dict[str, Set[asyncio.Queue]] = {}
        logger.info("SSE Notifier initialized")

    async def subscribe(self, family_id: str) -> asyncio.Queue:
        """
        Subscribe to state updates for a family.

        Returns:
            Queue that will receive state update events
        """
        queue = asyncio.Queue()

        if family_id not in self.connections:
            self.connections[family_id] = set()

        self.connections[family_id].add(queue)
        logger.info(f"📡 New SSE subscription for {family_id} (total: {len(self.connections[family_id])})")

        return queue

    async def unsubscribe(self, family_id: str, queue: asyncio.Queue):
        """
        Unsubscribe from state updates.
        """
        if family_id in self.connections:
            self.connections[family_id].discard(queue)

            # Clean up empty sets
            if not self.connections[family_id]:
                del self.connections[family_id]

            logger.info(f"📡 SSE unsubscribed for {family_id}")

    async def notify_state_change(
        self,
        family_id: str,
        update_type: str,
        data: Dict[str, Any]
    ):
        """
        Notify all subscribers of a state change.

        Args:
            family_id: Family to notify
            update_type: Type of update ("cards", "artifacts", "lifecycle_event")
            data: Update payload
        """
        if family_id not in self.connections or not self.connections[family_id]:
            logger.debug(f"📡 No SSE subscribers for {family_id}, skipping notification")
            return

        event_data = {
            "type": update_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }

        # Broadcast to all connected clients for this family
        dead_queues = set()
        for queue in self.connections[family_id]:
            try:
                await queue.put(event_data)
                logger.debug(f"📡 SSE sent {update_type} to {family_id}")
            except Exception as e:
                logger.warning(f"📡 Failed to send SSE to {family_id}: {e}")
                dead_queues.add(queue)

        # Clean up dead connections
        for queue in dead_queues:
            self.connections[family_id].discard(queue)

    async def notify_cards_updated(self, family_id: str, cards: list):
        """
        Convenience method: Notify that cards have been updated.
        """
        await self.notify_state_change(family_id, "cards", {"cards": cards})

    async def notify_artifact_updated(
        self,
        family_id: str,
        artifact_id: str,
        status: str,
        content: Optional[Any] = None
    ):
        """
        Convenience method: Notify that an artifact status changed.
        """
        await self.notify_state_change(
            family_id,
            "artifact",
            {
                "artifact_id": artifact_id,
                "status": status,
                "content": content
            }
        )


# Singleton instance
_sse_notifier: Optional[SSENotifier] = None


def get_sse_notifier() -> SSENotifier:
    """Get singleton SSE notifier instance"""
    global _sse_notifier
    if _sse_notifier is None:
        _sse_notifier = SSENotifier()
    return _sse_notifier
