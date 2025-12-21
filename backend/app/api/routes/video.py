"""
Video API Routes - Video upload endpoint

Video analysis is handled by the Darshan/Chitta architecture:
    POST /chat/v2/video/analyze/{family_id}/{cycle_id}
"""

from fastapi import APIRouter, HTTPException, Depends, Form, File, UploadFile
from typing import Optional
from pathlib import Path
import logging

from app.core.app_state import app_state
from app.db.dependencies import get_current_user_optional
from app.db.models_auth import User
from app.services.sse_notifier import get_sse_notifier

router = APIRouter(prefix="/video", tags=["video"])
logger = logging.getLogger(__name__)


@router.post("/upload")
async def upload_video(
    family_id: str = Form(...),
    video_id: str = Form(...),
    scenario: str = Form(...),
    duration_seconds: int = Form(...),
    file: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Upload video file and update gestalt state.

    This endpoint:
    1. Saves video file to uploads/{family_id}/{video_id}.{ext}
    2. Updates VideoScenario status in gestalt to 'uploaded'
    3. Sends SSE notifications for card updates
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    if current_user:
        logger.info(f"Video upload by: {current_user.email}")

    uploads_dir = Path("uploads") / family_id
    uploads_dir.mkdir(parents=True, exist_ok=True)

    file_ext = Path(file.filename).suffix or ".mp4"
    file_path = uploads_dir / f"{video_id}{file_ext}"

    try:
        logger.info(f"Saving video file: {file_path}")
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        logger.info(f"Video file saved: {file_path} ({len(content) / 1024 / 1024:.2f} MB)")
    except Exception as e:
        logger.error(f"Error saving video file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save video: {str(e)}")

    from app.chitta.service import get_chitta_service
    chitta = get_chitta_service()

    result = await chitta.record_video_upload(
        family_id=family_id,
        scenario_id=scenario,
        file_path=str(file_path),
        duration_seconds=duration_seconds
    )

    if "error" in result:
        logger.warning(f"Could not record video in gestalt: {result['error']}")

    # Get updated cards and notify via SSE
    updated_cards = await chitta.get_cards(family_id)
    logger.info(f"Updated cards after video upload: {[c['type'] for c in updated_cards]}")
    await get_sse_notifier().notify_cards_updated(family_id, updated_cards)

    return {
        "success": True,
        "video_id": video_id,
        "scenario_id": scenario,
        "file_path": str(file_path),
        "file_size_mb": len(content) / 1024 / 1024,
        "gestalt_result": result,
        "cards_updated": len(updated_cards)
    }
