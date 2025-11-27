"""
API Routes for Chitta
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import asyncio
import json
import logging
import os
from pathlib import Path

from app.core.app_state import app_state
from app.services.llm.base import Message
from app.services.conversation_service_simplified import get_simplified_conversation_service
from app.services.session_service import get_session_service
# Wu Wei Architecture: Import config-driven UI components
from app.config.card_generator import get_card_generator
from app.config.view_manager import get_view_manager
from app.config.config_loader import load_app_messages
# Demo Mode: Import demo orchestrator
from app.services.demo_orchestrator_service import get_demo_orchestrator
# State-based architecture
from app.services.mock_graphiti import get_mock_graphiti
from app.services.state_derivation import (
    derive_active_cards,
    derive_contextual_greeting,
    derive_suggestions
)
# Parent Simulator (Test Mode)
from app.services.parent_simulator import get_parent_simulator
# SSE for real-time updates
from app.services.sse_notifier import get_sse_notifier
# Dev routes for testing
from app.api import dev_routes

router = APIRouter()
logger = logging.getLogger(__name__)

# Include dev routes (only in development)
if os.getenv("ENVIRONMENT", "development") == "development":
    router.include_router(dev_routes.router)


# 🌟 Wu Wei: Helper function for config-driven trigger detection
def detect_system_trigger(message: str) -> Optional[str]:
    """
    Detect system triggers from user message using app_messages.yaml config.

    Returns trigger action name (e.g., "start_demo") or None.
    """
    import re

    messages_config = load_app_messages()
    triggers = messages_config.get("system_triggers", {})
    message_lower = message.lower()

    for trigger_action, trigger_config in triggers.items():
        keywords = trigger_config.get("keywords", {})
        pattern_type = trigger_config.get("pattern", "word_boundary")

        # Check English keywords
        for keyword in keywords.get("en", []):
            if pattern_type == "word_boundary":
                if re.search(r'\b' + re.escape(keyword) + r'\b', message_lower):
                    return trigger_action

        # Check Hebrew keywords
        for keyword in keywords.get("he", []):
            # Hebrew word boundary: beginning/end of string or whitespace
            if re.search(r'(?:^|[\s])' + re.escape(keyword) + r'(?:[\s]|$)', message_lower):
                return trigger_action

    return None


# === Request/Response Models ===

class UIStateUpdate(BaseModel):
    """UI state sent with each message from frontend"""
    current_view: Optional[str] = None  # chat, guidelines, upload, report, etc.
    progress: Optional[dict] = None  # {"videos_uploaded": 2, "videos_required": 3}
    recent_interactions: Optional[List[str]] = None  # ["viewed_guidelines", "clicked_upload"]
    dismissed_cards: Optional[List[str]] = None
    expanded_cards: Optional[List[str]] = None
    current_deep_view: Optional[str] = None


class SendMessageRequest(BaseModel):
    family_id: str
    message: str
    parent_name: Optional[str] = "הורה"
    ui_state: Optional[UIStateUpdate] = None  # 🌟 Wu Wei: UI awareness

class SendMessageResponse(BaseModel):
    response: str
    ui_data: dict  # Wu Wei: No stages - progressive unlocking via prerequisites

class CompleteInterviewResponse(BaseModel):
    success: bool
    video_guidelines: dict
    next_stage: str

class JournalEntryRequest(BaseModel):
    family_id: str
    content: str
    category: str  # "התקדמות", "תצפית", "אתגר"

class JournalEntryResponse(BaseModel):
    entry_id: str
    timestamp: str
    success: bool

class AvailableViewsResponse(BaseModel):
    """Response model for available views"""
    family_id: str
    # Wu Wei: No phases - removed phase field
    available_views: List[str]

class ViewContentResponse(BaseModel):
    """Response model for view content"""
    view_id: str
    view_name: str
    view_name_en: str
    available: bool
    content: Optional[dict] = None
    reason_unavailable: Optional[str] = None

# === Wu Wei: Artifact Response Models ===

class ArtifactResponse(BaseModel):
    """Response model for artifact"""
    artifact_id: str
    artifact_type: str
    status: str  # pending, generating, ready, error
    content: Optional[str] = None
    content_format: str = "markdown"
    created_at: str
    ready_at: Optional[str] = None
    error_message: Optional[str] = None

class SessionArtifactsResponse(BaseModel):
    """Response model for session artifacts list"""
    family_id: str
    artifacts: List[dict]

class ArtifactActionRequest(BaseModel):
    """Request model for artifact user actions"""
    family_id: str
    action: str  # "view", "download", "decline"

# === Demo Mode Response Models ===

class DemoStartRequest(BaseModel):
    """Request to start demo mode"""
    scenario_id: Optional[str] = "language_concerns"

class DemoStartResponse(BaseModel):
    """Response when starting demo"""
    demo_family_id: str
    scenario: dict
    first_message: dict
    demo_card: dict

class DemoNextResponse(BaseModel):
    """Response for next demo step"""
    step: int
    total_steps: int
    message: dict
    artifact_generated: Optional[dict] = None
    card_hint: Optional[str] = None
    demo_card: dict
    is_complete: bool

class DemoStopResponse(BaseModel):
    """Response when stopping demo"""
    success: bool
    message: str

# === Endpoints ===

@router.get("/")
async def root():
    """API root"""
    return {"message": "Chitta API", "version": "1.0.0"}

@router.post("/chat/send", response_model=SendMessageResponse)
async def send_message(request: SendMessageRequest):
    """
    שליחת הודעה לצ'יטה - Real AI Conversation with Function Calling
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    # Get services (Wu Wei: simplified architecture only)
    conversation_service = get_simplified_conversation_service()
    graphiti = get_mock_graphiti()

    # 🌟 Wu Wei: Config-driven trigger detection (replaces hardcoded keywords)
    action = detect_system_trigger(request.message)

    # 🚨 Check if already in test mode (prevents recursive triggering)
    simulator = get_parent_simulator()
    is_in_test_mode = request.family_id in simulator.active_simulations

    # Don't trigger test mode if already in it
    if action == "start_test_mode" and is_in_test_mode:
        action = None

    # Handle system/developer actions
    if action:

        # 🎬 Demo Mode
        if action == "start_demo":
            demo_orchestrator = get_demo_orchestrator()
            # Use demo orchestrator's logic to pick scenario
            scenario_id = "language_concerns"  # Default scenario
            demo_result = await demo_orchestrator.start_demo(scenario_id)

            # 🌟 Wu Wei: Load demo mode UI data from config
            messages_config = load_app_messages()
            demo_config = messages_config.get("demo_mode", {})
            demo_ui = demo_config.get("ui_data", {})

            return SendMessageResponse(
                response=demo_result["first_message"]["content"],
                stage="demo",
                ui_data={
                    "demo_mode": demo_ui.get("demo_mode", True),
                    "demo_family_id": demo_result["demo_family_id"],
                    "demo_scenario": demo_result["scenario"],
                    "cards": [demo_result["demo_card"]],
                    "suggestions": demo_ui.get("suggestions", ["המשך דמו"]),
                    "hint": demo_ui.get("hint"),
                    "progress": 0
                }
            )

        # 🧪 Test Mode
        elif action == "start_test_mode":
            simulator = get_parent_simulator()
            personas = simulator.list_personas()

            # Build persona list
            persona_list = "\n".join([
                f"- {p['parent']}: {p['child']} - {p['concern']}"
                for p in personas[:5]  # Show first 5
            ])

            # 🌟 Wu Wei: Load test mode message from config
            messages_config = load_app_messages()
            test_config = messages_config.get("test_mode", {})
            response_template = test_config.get("response_template", "🧪 מצב בדיקה")
            test_ui = test_config.get("ui_data", {})

            # Format response with persona data
            response = response_template.format(
                persona_count=len(personas),
                persona_list=persona_list
            )

            return SendMessageResponse(
                response=response,
                stage="interview",
                ui_data={
                    "test_mode_available": test_ui.get("test_mode_available", True),
                    "personas": personas,
                    "suggestions": test_ui.get("suggestions", ["המשך שיחה רגילה"]),
                    "hint": test_ui.get("hint"),
                    "cards": [],
                    "progress": 0
                }
            )

    # 🌟 Wu Wei: Update UI state from frontend (if provided)
    if request.ui_state:
        from app.services.ui_state_tracker import get_ui_state_tracker
        ui_tracker = get_ui_state_tracker()
        ui_tracker.update_from_request(
            family_id=request.family_id,
            ui_state_data=request.ui_state.model_dump(exclude_none=True)
        )

    # Save user message to state
    await graphiti.add_message(
        family_id=request.family_id,
        role="user",
        content=request.message
    )

    try:
        # Process message with real LLM and function calling
        result = await conversation_service.process_message(
            family_id=request.family_id,
            user_message=request.message,
            temperature=0.7
        )

        # Save assistant response to state
        await graphiti.add_message(
            family_id=request.family_id,
            role="assistant",
            content=result["response"]
        )

        # Get or create session for backward compatibility
        session = app_state.get_or_create_session(request.family_id)

        # Wu Wei: No stages - capabilities unlock via prerequisites defined in YAML

        # 🌟 Wu Wei: Get artifacts for frontend
        session_service = get_session_service()
        interview_session = session_service.get_or_create_session(request.family_id)

        # Sync artifacts to graphiti state (CRITICAL FIX!)
        # The state derivation checks state.artifacts, so we must sync them
        for artifact_id, artifact in interview_session.artifacts.items():
            if artifact.is_ready:  # Only sync ready artifacts
                await graphiti.add_artifact(
                    family_id=request.family_id,
                    artifact_type=artifact_id,
                    content={"status": "ready", "content": artifact.content}
                )

        # Convert artifacts to simplified format for UI
        artifacts_for_ui = {}
        for artifact_id, artifact in interview_session.artifacts.items():
            artifacts_for_ui[artifact_id] = {
                "exists": artifact.exists,
                "status": artifact.status,
                "artifact_type": artifact.artifact_type,
                "ready_at": artifact.ready_at.isoformat() if artifact.ready_at else None
            }

        # Get current state for derived suggestions (keep legacy compatibility)
        state = graphiti.get_or_create_state(request.family_id)
        derived_suggestions = derive_suggestions(state)

        # 🌟 Wu Wei: Use YAML-driven cards from conversation_service (not hardcoded derive_active_cards)
        # conversation_service already evaluated cards using card_generator.get_visible_cards()
        cards_from_conversation = result.get("context_cards", [])

        # Build UI data with real data from conversation service + derived UI
        ui_data = {
            "suggestions": derived_suggestions,  # Derived from state
            "cards": cards_from_conversation,  # 🌟 Wu Wei: YAML-driven cards from conversation_service
            "progress": result["completeness"] / 100,  # Convert to 0-1 scale
            "extracted_data": result.get("extracted_data", {}),
            "stats": result.get("stats", {}),
            "artifacts": artifacts_for_ui  # 🌟 Wu Wei: Include artifacts
        }

        return SendMessageResponse(
            response=result["response"],
            ui_data=ui_data
        )

    except Exception as e:
        # Log error and return graceful fallback
        import logging
        logging.error(f"Error in send_message: {e}", exc_info=True)

        # 🌟 Wu Wei: Load error message from config
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

@router.post("/interview/complete", response_model=CompleteInterviewResponse)
async def complete_interview(family_id: str):
    """
    סיום ראיון ויצירת הנחיות וידאו
    """
    session = app_state.get_or_create_session(family_id)

    # קריאה ל-LLM לסיכום
    summary_result = await app_state.llm.chat_with_structured_output(
        messages=[Message(
            role="system",
            content="סכם את הראיון"
        )],
        response_schema={"interview_summary": {}, "video_guidelines": {}}
    )

    # שמירה ב-Graphiti
    child_uuid = session["child_uuid"]

    await app_state.graphiti.add_episode(
        name=f"interview_summary_{family_id}",
        episode_body=summary_result["interview_summary"],
        group_id=family_id
    )

    await app_state.graphiti.add_episode(
        name=f"video_guidelines_{family_id}",
        episode_body=summary_result["video_guidelines"],
        group_id=family_id
    )

    # עדכן session
    session["current_stage"] = "video_upload"
    session["video_guidelines"] = summary_result["video_guidelines"]

    return CompleteInterviewResponse(
        success=True,
        video_guidelines=summary_result["video_guidelines"],
        next_stage="video_upload"
    )

@router.post("/video/upload")
async def upload_video(
    family_id: str = Form(...),
    video_id: str = Form(...),
    scenario: str = Form(...),
    duration_seconds: int = Form(...),
    file: UploadFile = File(...)
):
    """
    🌟 Wu Wei: Upload actual video file and trigger lifecycle moments

    This endpoint:
    1. Saves video file to uploads/{family_id}/{video_id}.{ext}
    2. Adds video to FamilyState with file_path and analyst_context
    3. Checks lifecycle moments (e.g., videos_ready when count >= 3)
    4. Sends SSE notifications for card updates
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    # Get services
    graphiti = get_mock_graphiti()
    session_service = get_session_service()

    # Get state
    state = graphiti.get_or_create_state(family_id)
    session = session_service.get_or_create_session(family_id)

    # Create uploads directory structure
    uploads_dir = Path("uploads") / family_id
    uploads_dir.mkdir(parents=True, exist_ok=True)

    # Get file extension
    file_ext = Path(file.filename).suffix or ".mp4"
    file_path = uploads_dir / f"{video_id}{file_ext}"

    # Save uploaded file
    try:
        logger.info(f"📤 Saving video file: {file_path}")
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        logger.info(f"✅ Video file saved: {file_path} ({len(content) / 1024 / 1024:.2f} MB)")
    except Exception as e:
        logger.error(f"❌ Error saving video file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save video: {str(e)}")

    # Get analyst_context from video guidelines artifact if available
    analyst_context = None
    guidelines_artifact = session.artifacts.get("baseline_video_guidelines")
    if guidelines_artifact and guidelines_artifact.status == "ready":
        try:
            guidelines_data = json.loads(guidelines_artifact.content)
            # Find matching scenario in guidelines
            for guideline_scenario in guidelines_data.get("scenarios", []):
                if guideline_scenario.get("title") == scenario or guideline_scenario.get("scenario") == scenario:
                    analyst_context = guideline_scenario.get("analyst_context")
                    logger.info(f"✅ Found analyst_context for scenario: {scenario}")
                    break
        except Exception as e:
            logger.warning(f"⚠️ Could not extract analyst_context from guidelines: {e}")

    # Add video to state
    from app.models.family_state import Video
    video = Video(
        id=video_id,
        scenario=scenario,
        uploaded_at=datetime.now(),
        duration_seconds=duration_seconds,
        file_path=str(file_path),
        analyst_context=analyst_context
    )
    state.videos_uploaded.append(video)
    state.last_active = datetime.now()

    total_videos = len(state.videos_uploaded)
    logger.info(f"📹 Video uploaded: {scenario} (total: {total_videos})")

    # 🌟 Wu Wei: Generate updated cards (moments will trigger on next conversation turn)
    from app.services.prerequisite_service import get_prerequisite_service
    from app.config.card_generator import get_card_generator

    prerequisite_service = get_prerequisite_service()
    card_generator = get_card_generator()

    # Build context for card evaluation
    session_data = {
        "family_id": family_id,
        "extracted_data": session.extracted_data.model_dump() if hasattr(session.extracted_data, 'model_dump') else session.extracted_data.dict(),
        "message_count": len(session.conversation_history),
        "artifacts": session.artifacts,
        "uploaded_video_count": total_videos,  # 🌟 Key for Wu Wei moments!
    }

    context = prerequisite_service.get_context_for_cards(session_data)
    updated_cards = card_generator.get_visible_cards(context)

    logger.info(f"📇 Updated cards after video upload: {len(updated_cards)} cards")

    # 🌟 Wu Wei: Send SSE notification for card update
    await get_sse_notifier().notify_cards_updated(family_id, updated_cards)

    return {
        "success": True,
        "video_id": video_id,
        "total_videos": total_videos,
        "file_path": str(file_path),
        "file_size_mb": len(content) / 1024 / 1024,
        "cards_updated": len(updated_cards)
    }

@router.post("/video/analyze")
async def analyze_videos(family_id: str, confirmed: bool = False):
    """
    🎥 Wu Wei: Holistic Clinical Video Analysis

    Analyzes uploaded videos using comprehensive clinical + holistic framework.
    Each video is analyzed separately with its specific analyst_context.

    Args:
        family_id: Family identifier
        confirmed: True if user already confirmed action (skip confirmation check)
    """
    from app.services.video_analysis_service import VideoAnalysisService
    from app.config.action_registry import get_action_registry
    from app.services.prerequisite_service import get_prerequisite_service

    # Get services
    graphiti = get_mock_graphiti()
    session_service = get_session_service()
    action_registry = get_action_registry()
    prerequisite_service = get_prerequisite_service()

    # Get state and session
    state = graphiti.get_or_create_state(family_id)
    session = session_service.get_or_create_session(family_id)

    # Check if there are videos to analyze
    if not state.videos_uploaded:
        raise HTTPException(status_code=400, detail="No videos uploaded yet")

    # ⚠️ Check if confirmation is needed (unless already confirmed)
    if not confirmed:
        # Build general context (same pattern used throughout the app)
        session_data = {
            "family_id": family_id,
            "extracted_data": session.extracted_data.model_dump() if hasattr(session.extracted_data, 'model_dump') else session.extracted_data.dict(),
            "message_count": len(session.conversation_history),
            "artifacts": session.artifacts,
            "uploaded_video_count": len(state.videos_uploaded),
            "guideline_scenario_count": session.guideline_scenario_count,
        }
        context = prerequisite_service.get_context_for_cards(session_data)

        # Check if action requires confirmation (generic check for any action)
        confirmation_message = action_registry.check_confirmation_needed("analyze_videos", context)

        if confirmation_message:
            logger.info(f"⚠️ Action requires confirmation: analyze_videos")
            return {
                "needs_confirmation": True,
                "confirmation_message": confirmation_message
            }

    # Get child data from extracted_data (Pydantic object)
    child_data = {
        "name": session.extracted_data.child_name,
        "age": session.extracted_data.age,
        "gender": session.extracted_data.gender,
        "concerns": session.extracted_data.primary_concerns or [],
    }

    logger.info(f"🎬 Holistic video analysis for {family_id} ({len(state.videos_uploaded)} videos)")

    # Initialize service
    video_analysis_service = VideoAnalysisService()

    # Prepare videos with analyst_context
    videos_to_analyze = []
    for video in state.videos_uploaded:
        if not video.analyst_context:
            logger.warning(f"⚠️ Video {video.id} missing analyst_context")
            continue

        videos_to_analyze.append({
            "id": video.id,
            "path": video.file_path or f"./uploads/{video.id}",
            "guideline_title": video.analyst_context.get("guideline_title", video.scenario),
            "analyst_context": video.analyst_context
        })

    if not videos_to_analyze:
        raise HTTPException(status_code=400, detail="No videos with context found")

    # Update status to "analyzing" and notify frontend
    session.video_analysis_status = "analyzing"
    logger.info(f"📊 Setting video_analysis_status to 'analyzing'")

    # Generate updated cards to show "analyzing" state
    from app.services.prerequisite_service import get_prerequisite_service

    prerequisite_service = get_prerequisite_service()
    card_generator = get_card_generator()

    session_data = {
        "family_id": family_id,
        "extracted_data": session.extracted_data.model_dump(),
        "message_count": len(session.conversation_history),
        "artifacts": session.artifacts,
        "uploaded_video_count": len(state.videos_uploaded),
        "video_analysis_status": "analyzing",  # Updated status
        "guideline_scenario_count": session.guideline_scenario_count,
    }

    context = prerequisite_service.get_context_for_cards(session_data)
    updated_cards = card_generator.get_visible_cards(context, max_cards=4)

    logger.info(f"📤 Sending {len(updated_cards)} cards with 'analyzing' state via SSE")

    # Notify frontend with updated cards showing analyzing state
    await get_sse_notifier().notify_cards_updated(family_id, updated_cards)

    try:
        # Analyze all videos
        analysis_artifact = await video_analysis_service.analyze_multiple_videos(
            videos=videos_to_analyze,
            child_data=child_data,
            extracted_data=session.extracted_data.model_dump(mode='json')
        )

        # Store analysis artifact (as Artifact object, not dict!)
        if analysis_artifact.status == "ready":
            session.artifacts["baseline_video_analysis"] = analysis_artifact

            # Update session status to "complete" (triggers card auto-dismiss)
            session.video_analysis_status = "complete"
            logger.info(f"📊 Setting video_analysis_status to 'complete'")

            # Update video statuses
            for video in state.videos_uploaded:
                video.analysis_status = "ready"
                video.analysis_artifact_id = "baseline_video_analysis"

            logger.info(f"✅ Video analysis complete for {family_id}")

            # 🌟 Process lifecycle events to check for "video_analysis_complete" moment
            from app.services.lifecycle_manager import get_lifecycle_manager
            from app.services.prerequisite_service import get_prerequisite_service

            lifecycle_manager = get_lifecycle_manager()
            prerequisite_service = get_prerequisite_service()

            # Build context for lifecycle evaluation
            session_data = {
                "family_id": family_id,
                "extracted_data": session.extracted_data.model_dump() if hasattr(session.extracted_data, 'model_dump') else session.extracted_data.dict(),
                "message_count": len(session.conversation_history),
                "artifacts": session.artifacts,
                "uploaded_video_count": len(state.videos_uploaded),
                "video_analysis_status": session.video_analysis_status,  # Now "complete"!
            }

            context = prerequisite_service.get_context_for_cards(session_data)

            # Process lifecycle events (will trigger "video_analysis_complete" moment)
            lifecycle_result = await lifecycle_manager.process_lifecycle_events(
                family_id=family_id,
                context=context,
                session=session
            )

            if lifecycle_result.get("events_triggered"):
                logger.info(f"🌟 Lifecycle events triggered: {[e['event_name'] for e in lifecycle_result['events_triggered']]}")

            if lifecycle_result.get("artifacts_generated"):
                logger.info(f"🌟 Artifacts generated: {lifecycle_result['artifacts_generated']}")

            # Trigger card update (now with potential new cards from lifecycle events)
            await get_sse_notifier().notify_cards_updated(family_id, [])

            return {
                "success": True,
                "artifact_id": "baseline_video_analysis",
                "videos_analyzed": len(videos_to_analyze),
                "next_steps": "Reports can now be generated"
            }
        else:
            # Analysis failed - reset status to pending
            session.video_analysis_status = "pending"
            logger.error(f"❌ Video analysis failed: {analysis_artifact.error_message}")

            # Notify frontend of failure
            await get_sse_notifier().notify_cards_updated(family_id, [])

            raise HTTPException(status_code=500, detail=analysis_artifact.error_message)

    except Exception as e:
        # Error occurred - reset status to pending
        session.video_analysis_status = "pending"
        logger.error(f"❌ Error in video analysis: {e}", exc_info=True)

        # Notify frontend of error
        await get_sse_notifier().notify_cards_updated(family_id, [])

        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reports/generate")
async def generate_reports(family_id: str):
    """
    יצירת דוחות (מקצועי + להורה)
    """
    session = app_state.get_or_create_session(family_id)

    # יצירת דוחות באמצעות הפונקציה הפנימית
    await _generate_reports_internal(family_id, session)

    return {
        "success": True,
        "professional_report": session.get("professional_report"),
        "parent_report": session.get("parent_report"),
        "next_stage": session["current_stage"]
    }

@router.get("/timeline/{family_id}")
async def get_timeline(family_id: str):
    """
    קבלת timeline של כל המסע + UI state עדכני
    """
    # קבלת session
    session = app_state.get_or_create_session(family_id)

    # קבלת כל ה-episodes
    episodes = app_state.graphiti.get_all_episodes(group_id=family_id)

    # המרה לפורמט timeline
    timeline = []
    for episode in episodes:
        timeline.append({
            "date": episode.reference_time.isoformat() if episode.reference_time else None,
            "type": _classify_episode_type(episode.name),
            "title": _generate_event_title(episode),
            "data": episode.body
        })

    # מיון לפי תאריך
    timeline.sort(key=lambda x: x["date"] if x["date"] else "", reverse=True)

    # יצירת contextual cards לפי stage הנוכחי
    current_stage = session.get("current_stage", "welcome")
    cards = _generate_cards(session)

    return {
        "timeline": timeline,
        "ui_data": {
            "cards": cards,
            "stage": current_stage
        }
    }

@router.post("/journal/entry", response_model=JournalEntryResponse)
async def add_journal_entry(request: JournalEntryRequest):
    """
    הוספת רשומה ליומן הילד
    """
    session = app_state.get_or_create_session(request.family_id)

    # צור entry ID ייחודי
    import uuid
    entry_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()

    # יצירת entry
    entry = {
        "entry_id": entry_id,
        "content": request.content,
        "category": request.category,
        "timestamp": timestamp
    }

    # הוספה ל-session
    if "journal_entries" not in session:
        session["journal_entries"] = []
    session["journal_entries"].append(entry)

    # שמירה ב-Graphiti
    await app_state.graphiti.add_episode(
        name=f"journal_entry_{entry_id}",
        episode_body={
            "type": "journal",
            "category": request.category,
            "content": request.content,
            "family_id": request.family_id
        },
        group_id=request.family_id,
        reference_time=datetime.now()
    )

    return JournalEntryResponse(
        entry_id=entry_id,
        timestamp=timestamp,
        success=True
    )

@router.get("/journal/entries/{family_id}")
async def get_journal_entries(family_id: str, limit: int = 10):
    """
    קבלת רשומות יומן אחרונות
    """
    session = app_state.get_or_create_session(family_id)

    # קבל entries מה-session
    entries = session.get("journal_entries", [])

    # מיון לפי תאריך (חדש לישן)
    entries_sorted = sorted(entries, key=lambda x: x["timestamp"], reverse=True)

    # החזר את המספר המבוקש
    return {
        "entries": entries_sorted[:limit],
        "total": len(entries_sorted)
    }

# === Helper Functions ===

async def _generate_reports_internal(family_id: str, session: dict):
    """פונקציה פנימית ליצירת דוחות"""
    # דוח מקצועי
    prof_report = await app_state.llm.chat_with_structured_output(
        messages=[Message(
            role="system",
            content="צור דוח מקצועי"
        )],
        response_schema={"report_markdown": "", "professional_recommendations_data": []}
    )

    # דוח להורה
    parent_report = await app_state.llm.chat_with_structured_output(
        messages=[Message(
            role="system",
            content="צור מכתב להורה"
        )],
        response_schema={"parent_letter": "", "actionable_next_steps": []}
    )

    # שמירה ב-Graphiti
    await app_state.graphiti.add_episode(
        name=f"professional_report_{family_id}",
        episode_body=prof_report,
        group_id=family_id,
        reference_time=datetime.now()
    )

    await app_state.graphiti.add_episode(
        name=f"parent_report_{family_id}",
        episode_body=parent_report,
        group_id=family_id,
        reference_time=datetime.now()
    )

    # שמירה ב-session
    session["professional_report"] = prof_report
    session["parent_report"] = parent_report

    # לא עוברים אוטומטית ל-consultation - נשאר ב-report_generation
    # כדי שהמשתמש יוכל לראות את הכרטיסים ולגשת לדוחות

def _generate_suggestions(session: dict) -> List[str]:
    """יצירת הצעות לפי שלב"""
    stage = session["current_stage"]

    if stage == "welcome":
        return [
            "שמו יוני והוא בן 3.5",
            "הילדה שלי בת 5",
            "אני רוצה לדבר על הבן שלי"
        ]
    elif len(session["interview_messages"]) < 5:
        return [
            "הוא מאוד אוהב פאזלים",
            "יש לי דאגות לגבי התקשורת",
            "ספרי לי מה עוד חשוב"
        ]

    return []

def _generate_suggestions_from_state(result: dict) -> List[str]:
    """
    Generate suggestions based on conversation service result

    Args:
        result: Result dict from conversation_service.process_message()
    """
    completeness = result.get("completeness", 0)
    stats = result.get("stats", {})

    # Early conversation (<20% complete)
    if completeness < 20:
        return [
            "שמו יוני והוא בן 3.5",
            "יש לי דאגות לגבי הדיבור שלו",
            "ספרי לי מה עוד חשוב"
        ]

    # Mid conversation (20-60% complete)
    elif completeness < 60:
        return [
            "הוא מאוד אוהב פאזלים ומשחקי בנייה",
            "איך הוא מתנהג בגן?",
            "יש עוד משהו שחשוב לדעת?"
        ]

    # Late conversation (60-80% complete)
    elif completeness < 80:
        return [
            "מה המטרה שלי עבורו?",
            "איך המשפחה מתמודדת?",
            "אני חושבת שזה הכל"
        ]

    # Ready for next stage (>80% complete)
    else:
        return [
            "איך מעלים סרטון?",
            "תראי לי את ההנחיות",
            "מה הצעדים הבאים?"
        ]

def _generate_cards(session: dict) -> List[dict]:
    """יצירת כרטיסים דינמיים"""
    cards = []

    # הגדרת שלבי המסע
    journey_stages = {
        "welcome": {"step": 1, "name": "ראיון התפתחותי", "emoji": "🗣️"},
        "video_upload": {"step": 2, "name": "צילום סרטונים", "emoji": "🎬"},
        "video_analysis": {"step": 3, "name": "ניתוח סרטונים", "emoji": "🔍"},
        "report_generation": {"step": 4, "name": "יצירת דוחות", "emoji": "📊"},
        "consultation": {"step": 5, "name": "ייעוץ מקצועי", "emoji": "💬"}
    }
    total_stages = 5
    current_stage = session["current_stage"]
    stage_info = journey_stages.get(current_stage, {"step": 1, "name": "התחלה", "emoji": "✨"})

    # כרטיסים לשלב הראיון
    if session["current_stage"] == "welcome":
        num_messages = len(session.get("interview_messages", []))

        # כרטיס 0: הנחיה ראשונית - מה הולך לקרות? (ציאן - instruction)
        if num_messages == 0:
            cards.append({
                "type": "welcome_guide",
                "title": "👋 ברוכה הבאה! בואי נכיר את הילד/ה שלך",
                "subtitle": "אני הולכת לשאול אותך כמה שאלות על הילד/ה - חוזקות, אתגרים, דברים שמעניינים אותו/ה. זה ייקח בערך 10-15 דקות. בסוף אכין לך המלצות מותאמות אישית",
                "icon": "Info",
                "status": "instruction",
                "action": None
            })

        # כרטיס 1: מתנהל ראיון (צהוב - processing)
        if num_messages > 0:
            progress_stage = "מידע בסיסי" if num_messages <= 3 else "תובנות עמוקות" if num_messages <= 6 else "סיכום"
            cards.append({
                "type": "interview_status",
                "title": "מתנהל ראיון",
                "subtitle": f"התקדמות: {progress_stage}",
                "icon": "MessageCircle",
                "status": "processing",
                "action": None
            })

        # כרטיס 2: נושאים שנדונו (ציאן - progress)
        if num_messages >= 2:
            topics = []
            # ניתוח פשוט של הנושאים מההודעות
            messages_text = " ".join([m.get("content", "") for m in session.get("interview_messages", []) if m.get("role") == "user"])
            if "גיל" in messages_text or "שנ" in messages_text:
                topics.append("גיל")
            if "דיבור" in messages_text or "מדבר" in messages_text or "תקשורת" in messages_text:
                topics.append("תקשורת")
            if "חוזק" in messages_text or "אוהב" in messages_text:
                topics.append("חוזקות")
            if "דאגה" in messages_text or "קושי" in messages_text:
                topics.append("דאגות")

            topics_text = ", ".join(topics) if topics else "בניית פרופיל"
            cards.append({
                "type": "interview_topics",
                "title": "נושאים שנדונו",
                "subtitle": topics_text,
                "icon": "CheckCircle",
                "status": "progress",
                "action": None
            })

        # כרטיס 3: זמן משוער (כתום - pending)
        if num_messages >= 3 and num_messages < 7:
            estimated_time = max(5, 15 - (num_messages * 2))
            cards.append({
                "type": "interview_time",
                "title": "זמן משוער",
                "subtitle": f"עוד {estimated_time}-{estimated_time + 5} דקות",
                "icon": "Clock",
                "status": "pending",
                "action": None
            })

    # כרטיסים לשלב צילום הווידאו
    elif session["current_stage"] == "video_upload" and "video_guidelines" in session:
        num_scenarios = len(session["video_guidelines"].get("scenarios", []))
        num_videos = len(session.get("videos", []))

        # כרטיס 0: הנחיה ומוטיבציה - למה לצלם? (ציאן בולט - instruction)
        if num_videos == 0:
            # טקסט מלא ומוטיבציוני בפעם הראשונה
            cards.append({
                "type": "video_upload_guide",
                "title": "🎬 שלב הצילום - למה זה חשוב?",
                "subtitle": "הסרטונים יעזרו לי להבין את ההתפתחות של הילד/ה שלך בצורה מעמיקה ומדויקת. זה כמו שאלך איתך הביתה ואראה את הילד/ה בפעולה - רק שאת קובעת מתי ואיך",
                "icon": "Info",
                "status": "instruction",
                "action": None
            })

        # כרטיס 1: ההתקדמות שלך (ציאן - progress) + breadcrumbs
        cards.append({
            "type": "overall_progress",
            "title": "ההתקדמות שלך",
            "subtitle": f"ראיון ✓ | סרטונים ({num_videos}/{num_scenarios})",
            "icon": "CheckCircle",
            "status": "progress",
            "action": None,
            "journey_step": stage_info["step"],
            "journey_total": total_stages
        })

        # כרטיס 2: הוראות לצילום (כחול - action)
        # ההוראות יופיעו בתוך טופס ההעלאה עצמו
        cards.append({
            "type": "upload_video",
            "title": "הוראות לצילום",
            "subtitle": f"צילום: {num_scenarios} תרחישים | הועלו: {num_videos}",
            "icon": "Video",
            "status": "action",
            "action": "upload"
        })

        # כרטיס 3: מה קורה אחרי? (מידע - instruction) - מופיע רק אחרי סרטון ראשון
        if num_videos >= 1:
            if num_videos >= num_scenarios:
                next_step_text = "כל הסרטונים הועלו! אני אתחיל בניתוח בקרוב"
            else:
                remaining = num_scenarios - num_videos
                next_step_text = f"נהדר! עוד {remaining} סרטונים ואני אוכל להתחיל בניתוח"

            cards.append({
                "type": "next_steps_info",
                "title": "מה הלאה?",
                "subtitle": next_step_text,
                "icon": "MessageCircle",
                "status": "instruction",
                "action": None
            })

    # כרטיסים לשלב ניתוח (analysis)
    elif session["current_stage"] == "video_analysis":
        # כרטיס 0: הנחיה - מה קורה עכשיו? (ציאן - instruction)
        cards.append({
            "type": "analysis_guide",
            "title": "🔍 מנתח את הסרטונים",
            "subtitle": "אני עובר על הסרטונים והראיון שלנו, מחפש דפוסים והתנהגויות. זה לוקח בדרך כלל כ-24 שעות. אעדכן אותך כשאסיים - אין צורך לחכות כאן",
            "icon": "Info",
            "status": "instruction",
            "action": None
        })

        # כרטיס 1: ניתוח בתהליך (צהוב - processing)
        cards.append({
            "type": "analysis_status",
            "title": "ניתוח בתהליך",
            "subtitle": "משוער: 24 שעות",
            "icon": "Clock",
            "status": "processing",
            "action": None
        })

        # כרטיס DEBUG: דלג לשלב הבא (כחול - action)
        cards.append({
            "type": "debug_skip",
            "title": "🔧 סימולציה: דלג לדוחות",
            "subtitle": "רק לפיתוח - מריץ ניתוח ומייצר דוחות",
            "icon": "FastForward",
            "status": "action",
            "action": "skipAnalysis"
        })

        # כרטיס 2: צפייה בסרטונים (כחול - action)
        num_videos = len(session.get("videos", []))
        cards.append({
            "type": "video_gallery",
            "title": "צפייה בסרטונים",
            "subtitle": f"{num_videos} סרטונים",
            "icon": "Video",
            "status": "action",
            "action": "videoGallery"
        })

        # כרטיס 3: יומן (ציאן - action)
        cards.append({
            "type": "journal",
            "title": "יומן יוני",
            "subtitle": "הוסיפי הערות מהימים האחרונים",
            "icon": "MessageCircle",
            "status": "action",
            "action": "journal"
        })

    # כרטיסים לשלב יצירת דוחות (report_generation)
    elif session["current_stage"] == "report_generation":
        # כרטיס 0: הנחיה - מה עכשיו? (ירוק בולט - new)
        cards.append({
            "type": "reports_ready_guide",
            "title": "🎉 הניתוח הושלם - הדוחות מוכנים!",
            "subtitle": "ניתחתי את הראיון והסרטונים. עכשיו יש לך 2 דוחות לקריאה + המלצות למומחים. הכל מוכן - פשוט לחצי על הכרטיסים למטה",
            "icon": "Sparkles",
            "status": "new",
            "action": None
        })

        # כרטיס 1: מדריך להורים (ירוק - new)
        cards.append({
            "type": "parent_report",
            "title": "📄 מדריך להורים",
            "subtitle": "לחצי לקריאה - הסברים ברורים בשפה פשוטה",
            "icon": "FileText",
            "status": "new",
            "action": "parentReport"
        })

        # כרטיס 2: דוח מקצועי (כחול - new)
        cards.append({
            "type": "professional_report",
            "title": "📋 דוח מקצועי",
            "subtitle": "לחצי לצפייה - דוח טכני לשיתוף עם מומחים",
            "icon": "FileText",
            "status": "action",
            "action": "proReport"
        })

        # כרטיס 3: מציאת מומחים (ציאן - action)
        cards.append({
            "type": "find_experts",
            "title": "🔍 מציאת מומחים",
            "subtitle": "המלצות מותאמות אישית על סמך הממצאים",
            "icon": "Search",
            "status": "action",
            "action": "experts"
        })

    # כרטיסים לשלב ייעוץ (consultation)
    elif session["current_stage"] == "consultation":
        # כרטיס 0: הנחיה - מה השלב הזה? (ציאן - instruction)
        cards.append({
            "type": "consultation_guide",
            "title": "💬 שלב הייעוץ - אני כאן בשבילך",
            "subtitle": "קראת את הדוחות? יש לך שאלות? רוצה לדון בממצאים או לקבל המלצות נוספות? פשוט שאלי אותי בצ'אט. אפשר גם להעלות מסמכים נוספים אם יש",
            "icon": "Info",
            "status": "instruction",
            "action": None
        })

        # כרטיס 1: מצב התייעצות (סגול - processing)
        cards.append({
            "type": "consultation",
            "title": "מצב התייעצות",
            "subtitle": "שאלי כל שאלה",
            "icon": "Brain",
            "status": "processing",
            "action": "consultDoc"
        })

        # כרטיס 2: העלאת מסמכים (כתום - action)
        cards.append({
            "type": "upload_document",
            "title": "העלאת מסמכים",
            "subtitle": "אבחונים, סיכומים, דוחות",
            "icon": "FileText",
            "status": "action",
            "action": "uploadDoc"
        })

        # כרטיס 3: יומן (ציאן - action)
        cards.append({
            "type": "journal",
            "title": "יומן יוני",
            "subtitle": "הערות והתבוננויות",
            "icon": "Book",
            "status": "action",
            "action": "journal"
        })

    return cards

def _classify_episode_type(name: str) -> str:
    """זיהוי סוג episode"""
    if "interview" in name:
        return "interview"
    elif "video_guidelines" in name:
        return "guidelines"
    elif "video_upload" in name:
        return "video_upload"
    elif "video_analysis" in name:
        return "analysis"
    elif "report" in name:
        return "report"
    elif "journal_entry" in name:
        return "journal"
    else:
        return "other"

def _generate_event_title(episode) -> str:
    """יצירת כותרת לevent"""
    episode_type = _classify_episode_type(episode.name)

    titles = {
        "interview": "ראיון התפתחותי",
        "guidelines": "הנחיות צילום נוצרו",
        "video_upload": "העלאת וידאו",
        "analysis": "ניתוח וידאו הושלם",
        "report": "דוח מוכן",
        "journal": "רשומת יומן"
    }

    return titles.get(episode_type, "אירוע")

# === Wu Wei Architecture: Deep Views Endpoints ===

@router.get("/views/available", response_model=AvailableViewsResponse)
async def get_available_views(family_id: str):
    """
    🌟 Wu Wei Architecture: Get available deep views for current session

    Returns list of view IDs that are available based on current session state.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    # Get services
    session_service = get_session_service()
    view_manager = get_view_manager()

    # Get session state
    session = session_service.get_or_create_session(family_id)
    data = session.extracted_data

    # 🌟 Wu Wei: Build artifacts for view availability checks
    artifacts = {}
    for artifact_id, artifact in session.artifacts.items():
        artifacts[artifact_id] = {
            "exists": artifact.exists,
            "status": artifact.status
        }

    # Build context for view availability checks
    # Wu Wei: No phases - removed phase from context
    context = {
        "completeness": session.completeness,
        "child_name": data.child_name,
        "artifacts": artifacts,  # 🌟 Wu Wei: Include artifacts
        "reports_ready": session.has_artifact("baseline_parent_report"),  # DEPRECATED: for backwards compatibility
        "video_count": 0,  # TODO: Get from video storage
    }

    # Get available views from view_manager
    available_views = view_manager.get_available_views(context)

    return AvailableViewsResponse(
        family_id=family_id,
        available_views=available_views
    )


@router.get("/views/{view_id}", response_model=ViewContentResponse)
async def get_view_content(view_id: str, family_id: str):
    """
    🌟 Wu Wei Architecture: Get specific view content

    Returns view definition and content if available, or reason if unavailable.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    # Get services
    session_service = get_session_service()
    view_manager = get_view_manager()

    # Get view definition
    view = view_manager.get_view(view_id)
    if not view:
        raise HTTPException(status_code=404, detail=f"View '{view_id}' not found")

    # Get session state
    session = session_service.get_or_create_session(family_id)
    data = session.extracted_data

    # 🌟 Wu Wei: Build artifacts for view availability check
    artifacts = {}
    for artifact_id, artifact in session.artifacts.items():
        artifacts[artifact_id] = {
            "exists": artifact.exists,
            "status": artifact.status,
            "content": artifact.content if artifact.is_ready else None
        }

    # Build context for availability check
    # Wu Wei: No phases - removed phase from context
    context = {
        "completeness": session.completeness,
        "child_name": data.child_name,
        "artifacts": artifacts,  # 🌟 Wu Wei: Include artifacts
        "reports_ready": session.has_artifact("baseline_parent_report"),  # DEPRECATED
        "video_count": 0,  # TODO: Get from video storage
    }

    # Check if view is available
    is_available = view_manager.check_view_availability(view_id, context)

    if is_available:
        # 🌟 Wu Wei: Enrich view content with artifact data
        view_content = view.copy()

        # Map view data sources to artifacts
        data_sources = view.get("data_sources", {})
        primary_source = data_sources.get("primary")

        if primary_source:
            # Map artifact names to actual artifact IDs
            artifact_map = {
                "video_guidelines": "baseline_video_guidelines",
                "parent_report": "baseline_parent_report",
                "professional_report": "baseline_professional_report",
                "updated_parent_report": "updated_parent_report"
            }

            artifact_id = artifact_map.get(primary_source, primary_source)
            artifact = session.get_artifact(artifact_id)

            if artifact and artifact.is_ready:
                # Include artifact content in view
                view_content["artifact_content"] = artifact.content
                view_content["artifact_metadata"] = {
                    "created_at": artifact.created_at.isoformat(),
                    "ready_at": artifact.ready_at.isoformat() if artifact.ready_at else None
                }

        # Enrich with context variables
        # Wu Wei: No phases - removed phase from context
        view_content["context"] = {
            "child_name": data.child_name,
            "artifacts_available": list(artifacts.keys())
        }

        return ViewContentResponse(
            view_id=view_id,
            view_name=view.get("name", ""),
            view_name_en=view.get("name_en", ""),
            available=True,
            content=view_content
        )
    else:
        return ViewContentResponse(
            view_id=view_id,
            view_name=view.get("name", ""),
            view_name_en=view.get("name_en", ""),
            available=False,
            reason_unavailable="View not available in current phase or missing required data"
        )


# === Wu Wei Architecture: Daniel's Space (Child Space) Endpoints ===

# Import child space service
from app.services.child_space_service import get_child_space_service


@router.get("/family/{family_id}/space")
async def get_child_space(family_id: str):
    """
    🌟 Living Dashboard Phase 2: Get Daniel's Space

    Returns the complete child space with:
    - All artifact slots (report, guidelines, videos, journal)
    - Header badges for quick status display
    - Current/latest items in each slot
    - Slot metadata (icons, names, actions)

    This is the "Memory Drawer" / "Living Header" for quick artifact access.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    # Get services
    graphiti = get_mock_graphiti()
    child_space_service = get_child_space_service()

    # Get family state
    state = graphiti.get_or_create_state(family_id)

    # Sync artifacts from session to family state
    session_service = get_session_service()
    session = session_service.get_or_create_session(family_id)

    # Copy artifacts to state for slot population
    for artifact_id, artifact in session.artifacts.items():
        if artifact.is_ready or artifact.status == "generating":
            state.artifacts[artifact_id] = artifact

    # Get child space
    space = child_space_service.get_child_space(state)

    return {
        "family_id": space.family_id,
        "child_name": space.child_name,
        "slots": [slot.model_dump() for slot in space.slots],
        "header_badges": space.header_badges,
        "last_updated": space.last_updated.isoformat() if space.last_updated else None
    }


@router.get("/family/{family_id}/space/header")
async def get_child_space_header(family_id: str):
    """
    🌟 Living Dashboard Phase 2: Get header badges only

    Lightweight endpoint for header pill display.
    Returns only slots with content as compact badges.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    graphiti = get_mock_graphiti()
    child_space_service = get_child_space_service()

    state = graphiti.get_or_create_state(family_id)

    # Sync artifacts from session
    session_service = get_session_service()
    session = session_service.get_or_create_session(family_id)
    for artifact_id, artifact in session.artifacts.items():
        if artifact.is_ready or artifact.status == "generating":
            state.artifacts[artifact_id] = artifact

    badges = child_space_service.get_header_summary(state)

    return {
        "family_id": family_id,
        "badges": badges
    }


@router.get("/family/{family_id}/space/slot/{slot_id}")
async def get_slot_detail(family_id: str, slot_id: str):
    """
    🌟 Living Dashboard Phase 2: Get detailed slot info

    Returns full slot details including version history.
    Used when user expands a slot in the UI.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    graphiti = get_mock_graphiti()
    child_space_service = get_child_space_service()

    state = graphiti.get_or_create_state(family_id)

    # Sync artifacts from session
    session_service = get_session_service()
    session = session_service.get_or_create_session(family_id)
    for artifact_id, artifact in session.artifacts.items():
        if artifact.is_ready or artifact.status == "generating":
            state.artifacts[artifact_id] = artifact

    slot = child_space_service.get_slot_detail(state, slot_id)

    if not slot:
        raise HTTPException(status_code=404, detail=f"Slot '{slot_id}' not found")

    return {
        "slot": slot.model_dump()
    }


# === Wu Wei Architecture: Living Documents (Threaded Conversations) ===

# Import thread service
from app.services.artifact_thread_service import get_artifact_thread_service


class CreateThreadRequest(BaseModel):
    """Request to create a new thread on an artifact section."""
    family_id: str
    initial_question: str
    section_title: Optional[str] = None
    section_text: Optional[str] = None


class ThreadMessageRequest(BaseModel):
    """Request to add a message to a thread."""
    family_id: str
    content: str


@router.get("/artifact/{artifact_id}/structured")
async def get_structured_artifact(artifact_id: str, family_id: str):
    """
    🌟 Living Dashboard Phase 3: Get artifact with sections

    Returns the artifact structured into sections with thread counts.
    Used for rendering Living Documents with thread indicators.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    thread_service = get_artifact_thread_service()
    structured = await thread_service.get_structured_artifact(family_id, artifact_id)

    if not structured:
        raise HTTPException(
            status_code=404,
            detail=f"Artifact '{artifact_id}' not found or not ready"
        )

    return {
        "artifact_id": structured.artifact_id,
        "artifact_type": structured.artifact_type,
        "title": structured.title,
        "sections": [s.model_dump() for s in structured.sections],
        "total_threads": structured.total_threads,
        "sections_with_threads": structured.sections_with_threads,
        "raw_content": structured.raw_content,
        "content_format": structured.content_format
    }


@router.get("/artifact/{artifact_id}/threads")
async def get_artifact_threads(artifact_id: str, family_id: str):
    """
    🌟 Living Dashboard Phase 3: Get all threads for an artifact

    Returns thread summaries for display on the artifact.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    thread_service = get_artifact_thread_service()

    # Ensure threads are loaded
    await thread_service.get_threads_for_artifact(artifact_id, family_id)

    summaries = await thread_service.get_thread_summaries(artifact_id)

    return {
        "artifact_id": artifact_id,
        "threads": [s.model_dump() for s in summaries],
        "total_threads": len(summaries)
    }


@router.post("/artifact/{artifact_id}/section/{section_id}/thread")
async def create_thread(
    artifact_id: str,
    section_id: str,
    request: CreateThreadRequest
):
    """
    🌟 Living Dashboard Phase 3: Start a new thread on a section

    Creates a new conversation thread attached to a specific section
    of an artifact. Returns the created thread with initial message.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    thread_service = get_artifact_thread_service()

    thread = await thread_service.create_thread(
        family_id=request.family_id,
        artifact_id=artifact_id,
        section_id=section_id,
        initial_question=request.initial_question,
        section_title=request.section_title,
        section_text=request.section_text
    )

    return {
        "thread_id": thread.thread_id,
        "artifact_id": artifact_id,
        "section_id": section_id,
        "messages": [m.model_dump() for m in thread.messages],
        "created_at": thread.created_at.isoformat()
    }


@router.get("/thread/{thread_id}")
async def get_thread(thread_id: str, artifact_id: str, family_id: str):
    """
    🌟 Living Dashboard Phase 3: Get a specific thread

    Returns full thread with all messages.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    thread_service = get_artifact_thread_service()

    # Ensure threads are loaded
    await thread_service.get_threads_for_artifact(artifact_id, family_id)

    thread = await thread_service.get_thread(thread_id, artifact_id)

    if not thread:
        raise HTTPException(status_code=404, detail=f"Thread '{thread_id}' not found")

    return {
        "thread_id": thread.thread_id,
        "artifact_id": thread.artifact_id,
        "section_id": thread.section_id,
        "section_title": thread.section_title,
        "section_text": thread.section_text,
        "messages": [m.model_dump() for m in thread.messages],
        "is_resolved": thread.is_resolved,
        "created_at": thread.created_at.isoformat(),
        "updated_at": thread.updated_at.isoformat()
    }


@router.post("/thread/{thread_id}/message")
async def add_thread_message(
    thread_id: str,
    request: ThreadMessageRequest
):
    """
    🌟 Living Dashboard Phase 3: Add message to thread and get AI response

    Adds user message to thread and generates contextual AI response.
    Returns both messages.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    thread_service = get_artifact_thread_service()

    # First, find the thread to get artifact_id
    # We need to search through cached threads
    artifact_id = None
    for aid, threads in thread_service._threads_cache.items():
        if threads.get_thread(thread_id):
            artifact_id = aid
            break

    if not artifact_id:
        raise HTTPException(status_code=404, detail=f"Thread '{thread_id}' not found")

    # Add user message
    user_msg = await thread_service.add_message(
        thread_id=thread_id,
        artifact_id=artifact_id,
        role="user",
        content=request.content
    )

    if not user_msg:
        raise HTTPException(status_code=500, detail="Failed to add message")

    # Get context for AI response
    context = await thread_service.get_thread_context(
        thread_id=thread_id,
        artifact_id=artifact_id,
        family_id=request.family_id
    )

    # Generate AI response using LLM
    try:
        from app.services.llm.factory import create_llm_provider
        from app.services.llm.base import Message

        llm = create_llm_provider()
        prompt = thread_service.build_thread_prompt(context, request.content)

        response = await llm.chat(
            messages=[Message(role="user", content=prompt)],
            temperature=0.7
        )

        ai_content = response.content

        # Add AI response to thread
        ai_msg = await thread_service.add_message(
            thread_id=thread_id,
            artifact_id=artifact_id,
            role="assistant",
            content=ai_content
        )

        return {
            "user_message": user_msg.model_dump(),
            "assistant_message": ai_msg.model_dump() if ai_msg else None,
            "thread_id": thread_id
        }

    except Exception as e:
        logger.error(f"Error generating thread response: {e}", exc_info=True)
        # Return user message even if AI fails
        return {
            "user_message": user_msg.model_dump(),
            "assistant_message": None,
            "error": str(e),
            "thread_id": thread_id
        }


@router.post("/thread/{thread_id}/resolve")
async def resolve_thread(thread_id: str, artifact_id: str):
    """
    🌟 Living Dashboard Phase 3: Mark thread as resolved

    User indicates they understood/got it.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    thread_service = get_artifact_thread_service()
    success = await thread_service.resolve_thread(thread_id, artifact_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"Thread '{thread_id}' not found")

    return {"success": True, "thread_id": thread_id, "resolved": True}


# === Wu Wei Architecture: Artifact Endpoints ===

@router.get("/session/{family_id}/artifacts", response_model=SessionArtifactsResponse)
async def get_session_artifacts(family_id: str):
    """
    🌟 Wu Wei: Get all artifacts for a session

    Returns list of all artifacts (guidelines, reports, etc.) that have been
    generated for this family session.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    session_service = get_session_service()
    session = session_service.get_or_create_session(family_id)

    # Convert artifacts to dict format for response
    artifacts_list = []
    for artifact_id, artifact in session.artifacts.items():
        artifacts_list.append({
            "artifact_id": artifact.artifact_id,
            "artifact_type": artifact.artifact_type,
            "status": artifact.status,
            "content_format": artifact.content_format,
            "created_at": artifact.created_at.isoformat(),
            "ready_at": artifact.ready_at.isoformat() if artifact.ready_at else None,
            "exists": artifact.exists,
            "is_ready": artifact.is_ready,
            "has_error": artifact.has_error,
            "error_message": artifact.error_message
        })

    return SessionArtifactsResponse(
        family_id=family_id,
        artifacts=artifacts_list
    )


@router.get("/artifacts/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(artifact_id: str, family_id: str):
    """
    🌟 Wu Wei: Get specific artifact content

    Returns the full artifact including content if it's ready.
    Artifact IDs: baseline_video_guidelines, baseline_parent_report, etc.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    session_service = get_session_service()
    session = session_service.get_or_create_session(family_id)

    # Get artifact
    artifact = session.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(
            status_code=404,
            detail=f"Artifact '{artifact_id}' not found for family {family_id}"
        )

    # 🐛 DEBUG: Log artifact retrieval details
    logger.info(
        f"📦 API fetch artifact '{artifact_id}' for {family_id}: "
        f"status={artifact.status}, is_ready={artifact.is_ready}, "
        f"has_content={artifact.content is not None}, "
        f"session_id={id(session)}, artifacts_dict_id={id(session.artifacts)}"
    )

    return ArtifactResponse(
        artifact_id=artifact.artifact_id,
        artifact_type=artifact.artifact_type,
        status=artifact.status,
        content=artifact.content if artifact.is_ready else None,
        content_format=artifact.content_format,
        created_at=artifact.created_at.isoformat(),
        ready_at=artifact.ready_at.isoformat() if artifact.ready_at else None,
        error_message=artifact.error_message
    )


@router.post("/artifacts/{artifact_id}/action")
async def artifact_action(artifact_id: str, request: ArtifactActionRequest):
    """
    🌟 Wu Wei: Track user actions on artifacts

    Actions: "view", "download", "decline"
    This tracks user engagement with generated artifacts.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    session_service = get_session_service()
    session = session_service.get_or_create_session(request.family_id)

    # Verify artifact exists
    artifact = session.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(
            status_code=404,
            detail=f"Artifact '{artifact_id}' not found"
        )

    # Track action in metadata
    if "user_actions" not in artifact.metadata:
        artifact.metadata["user_actions"] = []

    artifact.metadata["user_actions"].append({
        "action": request.action,
        "timestamp": datetime.now().isoformat()
    })

    # Update artifact
    session.add_artifact(artifact)

    import logging
    logger = logging.getLogger(__name__)
    logger.info(
        f"📊 Artifact action tracked: {request.action} on {artifact_id} "
        f"for family {request.family_id}"
    )

    return {
        "success": True,
        "artifact_id": artifact_id,
        "action": request.action,
        "tracked_at": datetime.now().isoformat()
    }


# === Timeline Generation ===

class TimelineGenerateRequest(BaseModel):
    """Request to generate a timeline infographic."""
    family_id: str
    style: Optional[str] = "warm"  # warm, professional, playful


@router.post("/timeline/generate")
async def generate_timeline(request: TimelineGenerateRequest):
    """
    Generate a visual timeline infographic for a child's journey.

    Uses Gemini image generation to create a beautiful infographic
    showing key moments and milestones.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    try:
        from app.services.timeline_image_service import get_timeline_service

        session_service = get_session_service()
        session = session_service.get_or_create_session(request.family_id)

        # Get child name from extracted data (SessionState has extracted_data directly)
        extracted = session.extracted_data
        child_name = extracted.child_name if extracted and extracted.child_name else "הילד/ה"

        # Build events from session state
        timeline_service = get_timeline_service()
        events = timeline_service.build_events_from_family_state(
            session.model_dump()
        )

        if not events:
            return {
                "success": False,
                "error": "לא נמצאו אירועים ליצירת ציר זמן",
                "message": "יש להמשיך בשיחה כדי ליצור ציר זמן"
            }

        # Generate the timeline image
        result = await timeline_service.generate_timeline_image(
            child_name=child_name,
            events=events,
            family_id=request.family_id,
            style=request.style
        )

        if not result:
            return {
                "success": False,
                "error": "שגיאה ביצירת ציר הזמן",
                "message": "נסה שוב מאוחר יותר"
            }

        # Store as artifact
        from app.models.artifact import Artifact

        artifact = Artifact(
            artifact_id=f"timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            artifact_type="timeline_infographic",
            status="ready",
            content=result["image_url"],  # Store image URL as content
            metadata={
                "image_url": result["image_url"],
                "image_path": result["image_path"],
                "child_name": child_name,
                "event_count": result["event_count"],
                "style": result["style"],
                "generated_at": result["generated_at"],
                "mime_type": result["mime_type"]
            }
        )

        session.add_artifact(artifact)

        logger.info(f"📊 Timeline generated for {child_name}: {result['image_url']}")

        return {
            "success": True,
            "artifact_id": artifact.artifact_id,
            "image_url": result["image_url"],
            "child_name": child_name,
            "event_count": result["event_count"],
            "message": f"ציר הזמן של {child_name} נוצר בהצלחה!"
        }

    except Exception as e:
        logger.error(f"Timeline generation error: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "שגיאה ביצירת ציר הזמן"
        }


@router.get("/timeline/{family_id}")
async def get_timeline(family_id: str):
    """Get the latest timeline artifact for a family."""
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    session_service = get_session_service()
    session = session_service.get_or_create_session(family_id)

    # Find timeline artifacts
    timelines = [
        a for a in session.family_state.artifacts.values()
        if a.artifact_type == "timeline_infographic"
    ]

    if not timelines:
        return {
            "success": False,
            "has_timeline": False,
            "message": "לא נמצא ציר זמן"
        }

    # Get the most recent
    latest = max(timelines, key=lambda a: a.created_at or "")

    return {
        "success": True,
        "has_timeline": True,
        "artifact_id": latest.artifact_id,
        "image_url": latest.data.get("image_url"),
        "child_name": latest.data.get("child_name"),
        "event_count": latest.data.get("event_count"),
        "generated_at": latest.metadata.get("generated_at")
    }


# === Demo Mode Endpoints (DEPRECATED - Use Test Mode Instead) ===
# Demo mode has been replaced with Test Mode which uses real backend processing
# Old demo endpoints are disabled to prevent confusion

# @router.post("/demo/start", response_model=DemoStartResponse)
# async def start_demo(request: DemoStartRequest):
#     """🎬 DEPRECATED: Use /test/start instead"""
#     raise HTTPException(status_code=410, detail="Demo mode deprecated. Use test mode instead.")

# @router.get("/demo/{demo_family_id}/next", response_model=DemoNextResponse)
# async def get_next_demo_step(demo_family_id: str):
#     """🎬 DEPRECATED: Use test mode instead"""
#     raise HTTPException(status_code=410, detail="Demo mode deprecated. Use test mode instead.")

# @router.post("/demo/{demo_family_id}/stop", response_model=DemoStopResponse)
# async def stop_demo(demo_family_id: str):
#     """🎬 DEPRECATED: Use test mode instead"""
#     raise HTTPException(status_code=410, detail="Demo mode deprecated. Use test mode instead.")


# === State-Based Endpoints (Wu Wei Architecture) ===

# IMPORTANT: SSE subscribe endpoint must come BEFORE /state/{family_id} to avoid route conflict
@router.get("/state/subscribe")
async def subscribe_to_state_updates(family_id: str):
    """
    🌟 Wu Wei SSE: Subscribe to real-time state updates

    Frontend connects to this endpoint and receives Server-Sent Events when:
    - Cards change (artifact status updates, lifecycle moments)
    - Artifacts complete background generation
    - Any state change that affects UI

    Usage:
        const eventSource = new EventSource('/api/state/subscribe?family_id=xyz');
        eventSource.onmessage = (event) => {
            const update = JSON.parse(event.data);
            // update.type: "cards" | "artifact" | "lifecycle_event"
            // update.data: { ... }
        };
    """
    logger.info(f"📡 SSE: New connection from family_id={family_id}")
    notifier = get_sse_notifier()
    queue = await notifier.subscribe(family_id)

    async def event_generator():
        """Generate SSE events from the queue"""
        try:
            while True:
                # Wait for next state change
                event_data = await queue.get()

                # Format as SSE event
                yield f"data: {json.dumps(event_data)}\n\n"

        except asyncio.CancelledError:
            # Client disconnected
            await notifier.unsubscribe(family_id, queue)
            raise

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.get("/state/{family_id}")
async def get_family_state(family_id: str):
    """
    🌟 Wu Wei: Get complete family state - everything derives from this.
    Cards are YAML-driven, evaluated from current artifacts and context.
    """
    graphiti = get_mock_graphiti()
    state = graphiti.get_or_create_state(family_id)

    # Get session and build context for card evaluation
    session_service = get_session_service()
    session = session_service.get_or_create_session(family_id)

    # Build context for YAML-driven card evaluation
    from app.services.prerequisite_service import get_prerequisite_service
    from app.config.card_generator import get_card_generator

    prerequisite_service = get_prerequisite_service()
    card_generator = get_card_generator()

    # Build session data for prerequisite evaluation
    session_data = {
        "family_id": family_id,
        "extracted_data": session.extracted_data.model_dump() if hasattr(session.extracted_data, 'model_dump') else session.extracted_data.dict(),
        "message_count": len(session.conversation_history),
        "artifacts": session.artifacts,
        "uploaded_video_count": len(state.videos_uploaded),  # 🌟 Get actual video count from state
    }

    # Get Wu Wei context (includes artifacts, flags, etc.)
    context = prerequisite_service.get_context_for_cards(session_data)

    # 🌟 Use YAML-driven card evaluation (not hardcoded!)
    cards = card_generator.get_visible_cards(context)

    # Derive other UI elements
    greeting = derive_contextual_greeting(state)
    suggestions = derive_suggestions(state)

    return {
        "state": state.dict(),
        "ui": {
            "greeting": greeting,
            "cards": cards,  # 🌟 Wu Wei: YAML-driven cards
            "suggestions": suggestions
        }
    }


# === Test Mode Endpoints (Parent Simulator) ===

@router.get("/test/personas")
async def list_test_personas():
    """
    List available parent personas for testing.
    Each persona represents a realistic test case.
    """
    simulator = get_parent_simulator()
    return {
        "personas": simulator.list_personas()
    }


class StartTestRequest(BaseModel):
    """Request to start test mode"""
    persona_id: str
    family_id: Optional[str] = None  # If not provided, generate one


@router.post("/test/start")
async def start_test_mode(request: StartTestRequest):
    """
    Start test mode with a parent persona.
    System will simulate this parent interacting with real backend.
    """
    simulator = get_parent_simulator()

    # Check if there's already an active simulation for this persona
    existing_family_id = simulator.get_active_simulation_for_persona(request.persona_id)

    if existing_family_id:
        # Reuse existing simulation - maintain context across messages
        family_id = existing_family_id
        logger.info(f"♻️ Reusing existing simulation for {request.persona_id}: {family_id}")
    else:
        # Create new simulation - only when first entering test mode
        family_id = request.family_id or f"test_{request.persona_id}_{int(datetime.now().timestamp())}"
        logger.info(f"🆕 Creating new simulation for {request.persona_id}: {family_id}")

    try:
        result = simulator.start_simulation(request.persona_id, family_id)

        return {
            "success": True,
            "family_id": family_id,
            "persona": result["persona"],
            "message": f"Test mode started with persona: {result['persona']['parent_name']}"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


class GenerateResponseRequest(BaseModel):
    """Request to generate parent response"""
    family_id: str
    chitta_question: str


@router.post("/test/generate-response")
async def generate_parent_response(request: GenerateResponseRequest):
    """
    Generate realistic parent response using LLM.
    The LLM acts as the parent persona.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    simulator = get_parent_simulator()
    graphiti = get_mock_graphiti()

    # CRITICAL FIX: Use flash-lite for test simulation to avoid safety filters
    # gemini-2.5-pro blocks roleplay scenarios involving child behavioral concerns
    # flash-lite has more permissive safety settings for educational/clinical content
    from app.services.llm.factory import create_llm_provider
    test_llm = create_llm_provider(provider_type="gemini", model="gemini-flash-lite-latest")
    logger.info("🎭 Using gemini-flash-lite for test parent simulation (avoids safety blocks)")

    try:
        response = await simulator.generate_response(
            family_id=request.family_id,
            chitta_question=request.chitta_question,
            llm_provider=test_llm,  # Use flash-lite instead of pro
            graphiti=graphiti
        )

        # If response is None, interview has completed - parent stops responding
        if response is None:
            return {
                "parent_response": "",  # Empty string, not None (None triggers frontend error)
                "interview_complete": True,
                "conversation_ended": True  # Clear flag for frontend
            }

        return {
            "parent_response": response,
            "interview_complete": False
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import logging
        logging.error(f"Error generating parent response: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate response")


class StopTestRequest(BaseModel):
    """Request to stop test mode"""
    family_id: str


@router.post("/test/stop")
async def stop_test_mode(request: StopTestRequest):
    """
    Stop an active test simulation.
    This clears the simulation from memory, allowing you to start fresh with the same persona.
    """
    simulator = get_parent_simulator()

    try:
        simulator.stop_simulation(request.family_id)
        logger.info(f"🛑 Stopped simulation for {request.family_id}")

        return {
            "success": True,
            "message": f"Test simulation stopped for {request.family_id}"
        }
    except Exception as e:
        logger.error(f"Error stopping simulation: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop simulation")


@router.get("/dev/export-artifacts/{family_id}")
async def export_artifacts(family_id: str):
    """
    Export all artifacts for a family to JSON files for inspection.
    Files are saved to backend/artifacts_export/{family_id}/
    """
    import json
    import os
    from pathlib import Path
    
    # Get session with artifacts
    session_service = get_session_service()
    session = session_service.get_or_create_session(family_id)
    
    # Create export directory
    export_dir = Path(f"artifacts_export/{family_id}")
    export_dir.mkdir(parents=True, exist_ok=True)
    
    exported_files = []
    
    # Export each artifact
    for artifact_id, artifact in session.artifacts.items():
        # Convert Artifact object to dict for JSON serialization
        artifact_data = {
            "artifact_id": artifact_id,
            "status": artifact.status,
            "content": artifact.content,
            "error_message": artifact.error_message,
            "created_at": str(artifact.created_at) if hasattr(artifact, 'created_at') else None,
        }
        
        # Save to file
        file_path = export_dir / f"{artifact_id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(artifact_data, f, ensure_ascii=False, indent=2)
        
        exported_files.append(str(file_path))
        logger.info(f"📄 Exported {artifact_id} to {file_path}")
    
    return {
        "success": True,
        "family_id": family_id,
        "artifacts_exported": len(exported_files),
        "export_directory": str(export_dir.absolute()),
        "files": exported_files
    }
