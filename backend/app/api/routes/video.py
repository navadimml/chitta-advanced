"""
Video API Routes - Video upload and analysis endpoints

Includes:
- /video/upload - Upload video file
- /video/analyze - Analyze uploaded videos
"""

from fastapi import APIRouter, HTTPException, Depends, Form, File, UploadFile
from typing import Optional
from pathlib import Path
import logging

from app.core.app_state import app_state
from app.db.dependencies import get_current_user_optional, RequireAuth
from app.db.models_auth import User
from app.services.unified_state_service import get_unified_state_service
from app.services.session_service import get_session_service
from app.services.sse_notifier import get_sse_notifier
from app.config.card_generator import get_card_generator

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

    gestalt = await chitta._get_gestalt(family_id)
    updated_cards = []
    if gestalt:
        updated_cards = chitta._derive_cards(gestalt)
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


@router.post("/analyze")
async def analyze_videos(
    family_id: str,
    confirmed: bool = False,
    auth: RequireAuth = Depends(RequireAuth())
):
    """
    Holistic Clinical Video Analysis.

    Analyzes uploaded videos using comprehensive clinical + holistic framework.
    Each video is analyzed separately with its specific analyst_context.

    Args:
        family_id: Family identifier
        confirmed: True if user already confirmed action (skip confirmation check)

    Requires authentication.
    """
    auth.verify_access(family_id)

    from app.services.video_analysis_service import VideoAnalysisService
    from app.config.action_registry import get_action_registry
    from app.services.prerequisite_service import get_prerequisite_service

    state_service = get_unified_state_service()
    session_service = get_session_service()
    action_registry = get_action_registry()
    prerequisite_service = get_prerequisite_service()

    state = state_service.get_family_state(family_id)
    session = session_service.get_or_create_session(family_id)

    if not state.videos_uploaded:
        raise HTTPException(status_code=400, detail="No videos uploaded yet")

    if not confirmed:
        session_data = {
            "family_id": family_id,
            "extracted_data": session.extracted_data.model_dump(),
            "message_count": len(session.conversation_history),
            "artifacts": session.artifacts,
            "uploaded_video_count": len(state.videos_uploaded),
            "guideline_scenario_count": session.guideline_scenario_count,
        }
        context = prerequisite_service.get_context_for_cards(session_data)

        confirmation_message = action_registry.check_confirmation_needed("analyze_videos", context)

        if confirmation_message:
            logger.info(f"Action requires confirmation: analyze_videos")
            return {
                "needs_confirmation": True,
                "confirmation_message": confirmation_message
            }

    child_data = {
        "name": session.extracted_data.child_name,
        "age": session.extracted_data.age,
        "gender": session.extracted_data.gender,
        "concerns": session.extracted_data.primary_concerns or [],
    }

    logger.info(f"Holistic video analysis for {family_id} ({len(state.videos_uploaded)} videos)")

    video_analysis_service = VideoAnalysisService()

    videos_to_analyze = []
    for video in state.videos_uploaded:
        if not video.analyst_context:
            logger.warning(f"Video {video.id} missing analyst_context")
            continue

        videos_to_analyze.append({
            "id": video.id,
            "path": video.file_path or f"./uploads/{video.id}",
            "guideline_title": video.analyst_context.get("guideline_title", video.scenario),
            "analyst_context": video.analyst_context
        })

    if not videos_to_analyze:
        raise HTTPException(status_code=400, detail="No videos with context found")

    session.video_analysis_status = "analyzing"
    logger.info(f"Setting video_analysis_status to 'analyzing'")

    card_generator = get_card_generator()

    session_data = {
        "family_id": family_id,
        "extracted_data": session.extracted_data.model_dump(),
        "message_count": len(session.conversation_history),
        "artifacts": session.artifacts,
        "uploaded_video_count": len(state.videos_uploaded),
        "video_analysis_status": "analyzing",
        "guideline_scenario_count": session.guideline_scenario_count,
    }

    context = prerequisite_service.get_context_for_cards(session_data)
    updated_cards = card_generator.get_visible_cards(context, max_cards=4)

    logger.info(f"Sending {len(updated_cards)} cards with 'analyzing' state via SSE")
    await get_sse_notifier().notify_cards_updated(family_id, updated_cards)

    try:
        analysis_artifact = await video_analysis_service.analyze_multiple_videos(
            videos=videos_to_analyze,
            child_data=child_data,
            extracted_data=session.extracted_data.model_dump(mode='json')
        )

        if analysis_artifact.status == "ready":
            session.artifacts["baseline_video_analysis"] = analysis_artifact
            session.video_analysis_status = "complete"
            logger.info(f"Setting video_analysis_status to 'complete'")

            for video in state.videos_uploaded:
                video.analysis_status = "ready"
                video.analysis_artifact_id = "baseline_video_analysis"

            logger.info(f"Video analysis complete for {family_id}")

            from app.services.lifecycle_manager import get_lifecycle_manager

            lifecycle_manager = get_lifecycle_manager()

            session_data = {
                "family_id": family_id,
                "extracted_data": session.extracted_data.model_dump(),
                "message_count": len(session.conversation_history),
                "artifacts": session.artifacts,
                "uploaded_video_count": len(state.videos_uploaded),
                "video_analysis_status": session.video_analysis_status,
            }

            context = prerequisite_service.get_context_for_cards(session_data)

            lifecycle_result = await lifecycle_manager.process_lifecycle_events(
                family_id=family_id,
                context=context,
                session=session
            )

            if lifecycle_result.get("events_triggered"):
                logger.info(f"Lifecycle events triggered: {[e['event_name'] for e in lifecycle_result['events_triggered']]}")

            if lifecycle_result.get("artifacts_generated"):
                logger.info(f"Artifacts generated: {lifecycle_result['artifacts_generated']}")

            await get_sse_notifier().notify_cards_updated(family_id, [])

            return {
                "success": True,
                "artifact_id": "baseline_video_analysis",
                "videos_analyzed": len(videos_to_analyze),
                "next_steps": "Reports can now be generated"
            }
        else:
            session.video_analysis_status = "pending"
            logger.error(f"Video analysis failed: {analysis_artifact.error_message}")
            await get_sse_notifier().notify_cards_updated(family_id, [])
            raise HTTPException(status_code=500, detail=analysis_artifact.error_message)

    except Exception as e:
        session.video_analysis_status = "pending"
        logger.error(f"Error in video analysis: {e}", exc_info=True)
        await get_sse_notifier().notify_cards_updated(family_id, [])
        raise HTTPException(status_code=500, detail=str(e))
