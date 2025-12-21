"""
State API Routes - SSE subscriptions and state endpoints

Includes:
- /state/subscribe - SSE real-time updates
- /state/{family_id} - Complete family state
"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from typing import Optional
import asyncio
import json
import logging

from app.db.dependencies import get_current_user_optional
from app.db.models_auth import User
from app.services.sse_notifier import get_sse_notifier
from app.services.unified_state_service import get_unified_state_service
from app.services.state_derivation import derive_contextual_greeting, derive_suggestions

router = APIRouter(prefix="/state", tags=["state"])
logger = logging.getLogger(__name__)


@router.get("/subscribe")
async def subscribe_to_state_updates(family_id: str):
    """
    SSE: Subscribe to real-time state updates.

    Frontend connects to this endpoint and receives Server-Sent Events when:
    - Cards change (artifact status updates, lifecycle moments)
    - Artifacts complete background generation
    - Any state change that affects UI

    Usage:
        const eventSource = new EventSource('/api/state/subscribe?family_id=xyz');
        eventSource.onmessage = (event) => {
            const update = JSON.parse(event.data);
            // update.type: "cards" | "artifact" | "lifecycle_event"
        };
    """
    logger.info(f"SSE: New connection from family_id={family_id}")
    notifier = get_sse_notifier()
    queue = await notifier.subscribe(family_id)

    async def event_generator():
        """Generate SSE events from the queue"""
        try:
            while True:
                event_data = await queue.get()
                yield f"data: {json.dumps(event_data)}\n\n"

        except asyncio.CancelledError:
            await notifier.unsubscribe(family_id, queue)
            raise

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/{family_id}")
async def get_family_state(
    family_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get complete family state.
    Cards and curiosity state are derived from Darshan explorations.
    """
    if current_user:
        logger.debug(f"State request from user: {current_user.email}")

    state_service = get_unified_state_service()
    state = state_service.get_family_state(family_id)

    from app.chitta.service import get_chitta_service
    chitta = get_chitta_service()

    # Use public APIs instead of private methods
    cards = await chitta.get_cards(family_id)
    curiosity_state = await chitta.get_curiosity_state(family_id)
    child_space_data = await chitta.get_child_space(family_id)

    logger.info(f"Darshan cards for {family_id}: {[c['type'] for c in cards]}")
    logger.info(f"Curiosities: {len(curiosity_state.get('active_curiosities', []))}")

    greeting = derive_contextual_greeting(state)
    suggestions = derive_suggestions(state)

    return {
        "state": state.model_dump(),
        "ui": {
            "greeting": greeting,
            "cards": cards,
            "suggestions": suggestions,
            "curiosity_state": curiosity_state,
            "child_space": child_space_data,
        }
    }
