"""
Chat API Routes - V1 and V2 conversation endpoints

Includes:
- /chat/send (v1)
- /chat/v2/* endpoints (init, send, curiosity, synthesis, video)
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from pathlib import Path
import logging

from app.core.app_state import app_state
from app.db.dependencies import get_current_user_optional, RequireAuth
from app.db.models_auth import User
from app.services.conversation_service_simplified import get_simplified_conversation_service
from app.services.unified_state_service import get_unified_state_service
from app.services.session_service import get_session_service
from app.services.state_derivation import derive_suggestions
from app.config.config_loader import load_app_messages

from .models import (
    UIStateUpdate,
    SendMessageRequest,
    SendMessageResponse,
)

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)


# === V2 Models (defined here as they're chat-specific) ===

class SendMessageV2Request(BaseModel):
    """Request model for v2 chat endpoint"""
    family_id: str
    message: str
    language: str = "he"
    ui_state: Optional[UIStateUpdate] = None


class SendMessageV2Response(BaseModel):
    """Response model for v2 chat endpoint"""
    response: str
    ui_data: dict


class ChatV2InitResponse(BaseModel):
    """Response model for v2 chat init"""
    greeting: str
    ui_data: dict


class VideoAcceptRequest(BaseModel):
    """Request to accept video suggestion"""
    family_id: str
    cycle_id: str


class VideoDeclineRequest(BaseModel):
    """Request to decline video suggestion"""
    family_id: str
    cycle_id: str


# === V1 Endpoints (DEPRECATED) ===

@router.post("/send", response_model=SendMessageResponse, deprecated=True)
async def send_message(
    request: SendMessageRequest,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    ⚠️  DEPRECATED: Use POST /chat/v2/send instead.

    V1 Chat - Send message to Chitta

    This endpoint uses the legacy Wu Wei architecture.
    New clients should use the Darshan/Chitta architecture via:
        POST /chat/v2/send
    """
    import warnings
    warnings.warn(
        "POST /chat/send is deprecated. Use /chat/v2/send instead.",
        DeprecationWarning,
        stacklevel=2
    )
    logger.warning(f"⚠️ DEPRECATED: /chat/send called for {request.family_id}. Use /chat/v2/send instead.")

    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    if current_user:
        logger.info(f"Chat from authenticated user: {current_user.email}")

    conversation_service = get_simplified_conversation_service()
    state_service = get_unified_state_service()

    # Update UI state from frontend (if provided)
    if request.ui_state:
        from app.services.ui_state_tracker import get_ui_state_tracker
        ui_tracker = get_ui_state_tracker()
        ui_tracker.update_from_request(
            family_id=request.family_id,
            ui_state_data=request.ui_state.model_dump(exclude_none=True)
        )

    # Save user message to state
    await state_service.add_conversation_turn_async(
        family_id=request.family_id,
        role="user",
        content=request.message
    )

    try:
        # Process message with LLM
        result = await conversation_service.process_message(
            family_id=request.family_id,
            user_message=request.message,
            temperature=0.7
        )

        # Save assistant response to state
        await state_service.add_conversation_turn_async(
            family_id=request.family_id,
            role="assistant",
            content=result["response"]
        )

        # Get session for backward compatibility
        session = app_state.get_or_create_session(request.family_id)

        # Get artifacts for frontend
        session_service = get_session_service()
        interview_session = session_service.get_or_create_session(request.family_id)

        # Sync artifacts to state service
        for artifact_id, artifact in interview_session.artifacts.items():
            if artifact.is_ready:
                state_service.add_artifact(request.family_id, artifact)

        # Convert artifacts to simplified format for UI
        artifacts_for_ui = {}
        for artifact_id, artifact in interview_session.artifacts.items():
            artifacts_for_ui[artifact_id] = {
                "exists": artifact.exists,
                "status": artifact.status,
                "artifact_type": artifact.artifact_type,
                "ready_at": artifact.ready_at.isoformat() if artifact.ready_at else None
            }

        # Get derived suggestions
        state = state_service.get_family_state(request.family_id)
        derived_suggestions = derive_suggestions(state)

        # Get cards from conversation service
        cards_from_conversation = result.get("context_cards", [])

        ui_data = {
            "suggestions": derived_suggestions,
            "cards": cards_from_conversation,
            "progress": result["completeness"] / 100,
            "extracted_data": result.get("extracted_data", {}),
            "stats": result.get("stats", {}),
            "artifacts": artifacts_for_ui
        }

        return SendMessageResponse(
            response=result["response"],
            ui_data=ui_data
        )

    except Exception as e:
        logger.error(f"Error in send_message: {e}", exc_info=True)

        messages_config = load_app_messages()
        error_config = messages_config.get("errors", {}).get("technical_error", {})

        return SendMessageResponse(
            response=error_config.get("response", "מצטערת, נתקלתי בבעיה טכנית."),
            ui_data={
                "suggestions": error_config.get("suggestions", ["נסה שוב"]),
                "cards": [],
                "progress": 0,
                "error": str(e)
            }
        )


# === V2 Endpoints ===

@router.get("/v2/init/{family_id}", response_model=ChatV2InitResponse)
async def chat_v2_init(
    family_id: str,
    language: str = "he",
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    V2 Chat Init - Get Chitta's opening message
    """
    from app.services.i18n_service import t, get_i18n
    from app.chitta import get_chitta_service

    if current_user:
        logger.info(f"Chat init for user: {current_user.email}")

    try:
        get_i18n(language)
        unified = get_unified_state_service()
        child = unified.get_child(family_id)
        session = await unified.get_or_create_session_async(family_id)

        chitta = get_chitta_service()
        returning_context = chitta._check_returning_user(session, child)

        child_name = child.name or t("common.child_default_name") if hasattr(child, 'name') else None

        # Generate appropriate greeting
        if returning_context:
            category = returning_context.get("category", "returning")
            days = returning_context.get("days_since", 0)

            if days == 1:
                time_ago = t("time.yesterday")
            elif days < 7:
                time_ago = t("time.days_ago", days=int(days))
            elif days < 14:
                time_ago = t("time.week_ago")
            else:
                time_ago = t("time.weeks_ago", weeks=int(days // 7))

            if category == "long_absence":
                greeting = t("greetings.returning.long_absence", child_name=child_name or "")
            elif category == "returning":
                greeting = t("greetings.returning.after_days", child_name=child_name or "", time_ago=time_ago)
            else:
                greeting = t("greetings.returning.short_break", child_name=child_name or "")

        elif session.turn_count > 0:
            greeting = t("greetings.returning.same_session")
        else:
            greeting = t("greetings.first_visit")

        cards = await chitta.get_cards(family_id)

        ui_data = {
            "cards": cards,
            "progress": child.data_completeness,
            "stats": {
                "family_id": family_id,
                "is_new": session.turn_count == 0,
                "is_returning": returning_context is not None,
                "conversation_turns": session.turn_count,
            },
            "architecture": "chitta_v2",
        }

        if session.turn_count == 0:
            session.add_message("assistant", greeting)
            await unified._persist_session(session)

        return ChatV2InitResponse(greeting=greeting, ui_data=ui_data)

    except Exception as e:
        logger.error(f"Error in chat_v2_init: {e}", exc_info=True)
        return ChatV2InitResponse(
            greeting=t("greetings.first_visit"),
            ui_data={"cards": [], "progress": 0, "error": str(e)},
        )


@router.get("/v2/curiosity/{family_id}")
async def get_curiosity_state_v2(family_id: str):
    """
    Get current curiosity state for a family.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    try:
        from app.chitta import get_chitta_service

        chitta = get_chitta_service()
        result = await chitta.get_curiosity_state(family_id)

        return {
            "family_id": family_id,
            "curiosity_state": result,
            "architecture": "living_gestalt",
        }

    except Exception as e:
        logger.error(f"Error getting curiosity state: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/v2/synthesis/{family_id}")
async def request_synthesis_v2(
    family_id: str,
    auth: RequireAuth = Depends(RequireAuth())
):
    """
    Request on-demand synthesis for a family.
    """
    auth.verify_access(family_id)

    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    try:
        from app.chitta import get_chitta_service

        chitta = get_chitta_service()
        result = await chitta.request_synthesis(family_id)

        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])

        return {
            "family_id": family_id,
            "synthesis": result,
            "architecture": "living_gestalt",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error requesting synthesis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/v2/send", response_model=SendMessageV2Response)
async def send_message_v2(
    request: SendMessageV2Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    V2 Chat Endpoint - Uses ChittaService with Darshan architecture
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    if current_user:
        logger.info(f"V2 Chat from authenticated user: {current_user.email}")

    try:
        from app.chitta import get_chitta_service

        chitta = get_chitta_service()

        result = await chitta.process_message(
            family_id=request.family_id,
            user_message=request.message,
        )

        ui_data = {
            "curiosity_state": result.get("curiosity_state", {
                "active_curiosities": [],
                "open_questions": [],
            }),
            "cards": result.get("cards", []),
            "stats": {
                "family_id": request.family_id,
                "curiosity_count": len(result.get("curiosity_state", {}).get("active_curiosities", [])),
            },
            "architecture": "living_gestalt",
        }

        return SendMessageV2Response(response=result["response"], ui_data=ui_data)

    except Exception as e:
        logger.error(f"Error in send_message_v2: {e}", exc_info=True)

        messages_config = load_app_messages()
        error_config = messages_config.get("errors", {}).get("technical_error", {})

        return SendMessageV2Response(
            response=error_config.get("response", "מצטערת, נתקלתי בבעיה טכנית."),
            ui_data={
                "cards": [],
                "curiosity_state": {"active_curiosities": [], "open_questions": []},
                "error": str(e),
                "architecture": "living_gestalt",
            },
        )


# === V2 Video Endpoints ===

@router.post("/v2/video/accept")
async def accept_video_suggestion(request: VideoAcceptRequest):
    """
    Parent accepts video suggestion - generate guidelines.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    try:
        from app.chitta import get_chitta_service

        chitta = get_chitta_service()
        result = await chitta.accept_video_suggestion(
            family_id=request.family_id,
            cycle_id=request.cycle_id,
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return {
            "status": "ready",
            "cycle_id": request.cycle_id,
            "guidelines": result.get("guidelines"),
            "message": "הנחיות הצילום מוכנות!",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accepting video suggestion: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/v2/video/decline")
async def decline_video_suggestion(request: VideoDeclineRequest):
    """
    Parent declines video suggestion.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    try:
        from app.chitta import get_chitta_service

        chitta = get_chitta_service()
        result = await chitta.decline_video_suggestion(
            family_id=request.family_id,
            cycle_id=request.cycle_id,
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return {
            "status": "declined",
            "cycle_id": request.cycle_id,
            "message": result.get("message", "בסדר גמור! נמשיך להכיר דרך השיחה."),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error declining video suggestion: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/v2/video/guidelines/{family_id}/{cycle_id}")
async def get_video_guidelines(family_id: str, cycle_id: str):
    """
    Get video guidelines for a cycle (after consent).
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    try:
        from app.chitta import get_chitta_service

        chitta = get_chitta_service()
        result = await chitta.get_video_guidelines(
            family_id=family_id,
            cycle_id=cycle_id,
        )

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting video guidelines: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/v2/video/upload")
async def upload_video_v2(
    family_id: str = Form(...),
    cycle_id: str = Form(...),
    scenario_id: str = Form(...),
    video: UploadFile = File(...),
):
    """
    Upload a video for a scenario.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    try:
        from app.chitta import get_chitta_service

        chitta = get_chitta_service()

        upload_dir = Path("data/videos") / family_id
        upload_dir.mkdir(parents=True, exist_ok=True)

        video_filename = f"{cycle_id}_{scenario_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        video_path = upload_dir / video_filename

        with open(video_path, "wb") as f:
            content = await video.read()
            f.write(content)

        result = await chitta.mark_video_uploaded(
            family_id=family_id,
            cycle_id=cycle_id,
            scenario_id=scenario_id,
            video_path=str(video_path),
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return {
            "status": "uploaded",
            "scenario_id": scenario_id,
            "video_path": str(video_path),
            "message": "הסרטון הועלה בהצלחה!",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading video: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/v2/video/analyze/{family_id}/{cycle_id}")
async def analyze_videos_v2(family_id: str, cycle_id: str):
    """
    Analyze uploaded videos for a cycle.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    try:
        from app.chitta import get_chitta_service

        chitta = get_chitta_service()
        result = await chitta.analyze_cycle_videos(
            family_id=family_id,
            cycle_id=cycle_id,
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return {
            "status": "analyzed",
            "cycle_id": cycle_id,
            "insights": result.get("insights", []),
            "evidence_added": result.get("evidence_added", 0),
            "confidence_update": result.get("confidence_update"),
            "message": "ניתחתי את הסרטון! יש לי כמה תובנות",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing videos: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
