"""
API Routes for Chitta
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# Authentication dependencies
from app.db.dependencies import get_current_user_optional, get_current_user, RequireAuth
from app.db.models_auth import User
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
# State-based architecture (UnifiedStateService replaces MockGraphiti)
from app.services.unified_state_service import get_unified_state_service
from app.services.state_derivation import (
    derive_active_cards,
    derive_contextual_greeting,
    derive_suggestions
)
# Darshan: Card derivation via ChittaService
from app.chitta import get_chitta_service
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

# NOTE: /chat/send moved to routes/chat.py

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
    file: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    🌟 Darshan: Upload video file and update gestalt state

    This endpoint:
    1. Saves video file to uploads/{family_id}/{video_id}.{ext}
    2. Updates VideoScenario status in gestalt to 'uploaded'
    3. Sends SSE notifications for card updates
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    if current_user:
        logger.info(f"🎥 Video upload by: {current_user.email}")

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

    # 🌟 Darshan: Record video upload in gestalt state
    from app.chitta.service import get_chitta_service
    chitta = get_chitta_service()

    # scenario is the scenario_id from the video guidelines
    result = await chitta.record_video_upload(
        family_id=family_id,
        scenario_id=scenario,  # This is the VideoScenario.id
        file_path=str(file_path),
        duration_seconds=duration_seconds
    )

    if "error" in result:
        logger.warning(f"⚠️ Could not record video in gestalt: {result['error']}")

    # Get updated cards and send SSE
    gestalt = await chitta._get_gestalt(family_id)
    updated_cards = []
    if gestalt:
        updated_cards = chitta._derive_cards(gestalt)
        logger.info(f"📇 Updated cards after video upload: {[c['type'] for c in updated_cards]}")
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

@router.post("/video/analyze")
async def analyze_videos(
    family_id: str,
    confirmed: bool = False,
    auth: RequireAuth = Depends(RequireAuth())
):
    """
    🎥 Wu Wei: Holistic Clinical Video Analysis

    Analyzes uploaded videos using comprehensive clinical + holistic framework.
    Each video is analyzed separately with its specific analyst_context.

    Args:
        family_id: Family identifier
        confirmed: True if user already confirmed action (skip confirmation check)

    Requires authentication.
    """
    # Verify user has access to this family
    auth.verify_access(family_id)

    from app.services.video_analysis_service import VideoAnalysisService
    from app.config.action_registry import get_action_registry
    from app.services.prerequisite_service import get_prerequisite_service

    # Get services
    state_service = get_unified_state_service()
    session_service = get_session_service()
    action_registry = get_action_registry()
    prerequisite_service = get_prerequisite_service()

    # Get state and session
    state = state_service.get_family_state(family_id)
    session = session_service.get_or_create_session(family_id)

    # Check if there are videos to analyze
    if not state.videos_uploaded:
        raise HTTPException(status_code=400, detail="No videos uploaded yet")

    # ⚠️ Check if confirmation is needed (unless already confirmed)
    if not confirmed:
        # Build general context (same pattern used throughout the app)
        session_data = {
            "family_id": family_id,
            "extracted_data": session.extracted_data.model_dump(),
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
                "extracted_data": session.extracted_data.model_dump(),
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
async def generate_reports(
    family_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    יצירת דוחות (מקצועי + להורה)
    """
    if current_user:
        logger.info(f"📄 Report generation requested by: {current_user.email}")

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

    Processes the journal entry into Chitta's understanding:
    - Extracts facts with ABSOLUTE timestamps (relative expressions converted)
    - Detects developmental milestones
    - Boosts related curiosities
    - Stores in gestalt for persistence

    Temporal data enables future time-based queries and developmental tracking.
    """
    import uuid
    entry_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()

    # Process into Chitta's understanding
    from app.chitta.service import get_chitta_service
    chitta = get_chitta_service()

    try:
        result = await chitta.process_parent_journal_entry(
            family_id=request.family_id,
            entry_text=request.content,
            entry_type=request.category,
        )

        return JournalEntryResponse(
            entry_id=entry_id,
            timestamp=timestamp,
            success=True
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to process journal entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

    Supports both Darshan data (new) and legacy session data.
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    try:
        from app.services.timeline_image_service import get_timeline_service
        from pathlib import Path
        import json

        timeline_service = get_timeline_service()
        child_name = "הילד/ה"
        events = []

        # Try Darshan data first (data/children/{family_id}.json)
        gestalt_file = Path("data/children") / f"{request.family_id}.json"
        if gestalt_file.exists():
            try:
                with open(gestalt_file, "r", encoding="utf-8") as f:
                    gestalt_data = json.load(f)

                child_name = gestalt_data.get("name", "הילד/ה")
                events = timeline_service.build_events_from_gestalt(gestalt_data)
                logger.info(f"📊 Building timeline from gestalt data for {request.family_id}")
            except Exception as e:
                logger.warning(f"Failed to load gestalt data for timeline: {e}")

        # Fallback to legacy session data
        if not events:
            session_service = get_session_service()
            session = session_service.get_or_create_session(request.family_id)

            # Get child name from extracted data (SessionState has extracted_data directly)
            extracted = session.extracted_data
            if extracted and extracted.child_name:
                child_name = extracted.child_name

            # Build events from session state
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

        # Store as artifact (only if we have a session)
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

        # Add to session if available (legacy path)
        if 'session' in locals():
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
async def get_family_state(
    family_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    🌟 Darshan: Get complete family state.
    Cards and curiosity state are derived from Darshan explorations.
    """
    if current_user:
        logger.debug(f"📊 State request from user: {current_user.email}")

    state_service = get_unified_state_service()
    state = state_service.get_family_state(family_id)

    # 🌟 Darshan - use ChittaService for cards and curiosity
    from app.chitta.service import get_chitta_service
    chitta = get_chitta_service()
    gestalt = await chitta._get_gestalt(family_id)

    cards = []
    curiosity_state = {"active_curiosities": [], "open_questions": []}
    child_space_data = None

    if gestalt:
        cards = chitta._derive_cards(gestalt)
        curiosity_state = await chitta.get_curiosity_state(family_id)
        child_space_data = chitta._derive_child_space(gestalt)
        logger.info(f"🌟 Darshan cards for {family_id}: {[c['type'] for c in cards]}")
        logger.info(f"🌟 Curiosities: {len(curiosity_state.get('active_curiosities', []))}")

    # Derive other UI elements
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



