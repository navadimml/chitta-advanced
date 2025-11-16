"""
API Routes for Chitta
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.core.app_state import app_state
from app.services.llm.base import Message
from app.services.conversation_service import get_conversation_service
from app.services.interview_service import get_interview_service
# Wu Wei Architecture: Import config-driven UI components
from app.config.card_generator import get_card_generator
from app.config.view_manager import get_view_manager
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

router = APIRouter()

# === Request/Response Models ===

class SendMessageRequest(BaseModel):
    family_id: str
    message: str
    parent_name: Optional[str] = "הורה"

class SendMessageResponse(BaseModel):
    response: str
    stage: str
    ui_data: dict

class CompleteInterviewResponse(BaseModel):
    success: bool
    video_guidelines: dict
    next_stage: str

class UploadVideoRequest(BaseModel):
    family_id: str
    video_id: str
    scenario: str
    duration_seconds: int

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
    phase: str
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

    # Get services
    conversation_service = get_conversation_service()
    graphiti = get_mock_graphiti()
    knowledge_service = conversation_service.knowledge_service

    # 🎯 LLM-based Intent Detection: Check for system actions (test/demo mode)
    # Use the intelligent intent detector instead of primitive string matching
    from app.prompts.intent_types import IntentCategory
    detected_intent = await knowledge_service.detect_unified_intent(request.message)

    # Handle system/developer actions
    if detected_intent.category == IntentCategory.ACTION_REQUEST:
        action = detected_intent.specific_action

        # 🎬 Demo Mode
        if action == "start_demo":
            demo_orchestrator = get_demo_orchestrator()
            # Use demo orchestrator's logic to pick scenario
            scenario_id = "language_delay"  # Default scenario
            demo_result = await demo_orchestrator.start_demo(scenario_id)

            return SendMessageResponse(
                response=demo_result["first_message"]["content"],
                stage="demo",
                ui_data={
                    "demo_mode": True,
                    "demo_family_id": demo_result["demo_family_id"],
                    "demo_scenario": demo_result["scenario"],
                    "cards": [demo_result["demo_card"]],
                    "suggestions": ["המשך דמו", "עצור דמו", "דלג לשלב הבא"],
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

            return SendMessageResponse(
                response=f"🧪 מצב בדיקה\n\nהבנתי שאת רוצה לבדוק את המערכת! יש לי {len(personas)} פרסונות הורים מוכנות:\n\n{persona_list}\n\nכדי להתחיל, השתמשי ב-API של מצב הבדיקה (/test/start) או בממשק המיוחד למפתחים.",
                stage="interview",
                ui_data={
                    "test_mode_available": True,
                    "personas": personas,
                    "suggestions": ["המשך שיחה רגילה"],
                    "cards": [],
                    "progress": 0
                }
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

        # Update session stage based on completeness
        if result["completeness"] >= 80:
            session["current_stage"] = "video_upload"
        else:
            session["current_stage"] = "interview"

        # 🌟 Wu Wei: Get artifacts for frontend
        interview_service = get_interview_service()
        interview_session = interview_service.get_or_create_session(request.family_id)

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

        # Get current state and derive UI elements
        state = graphiti.get_or_create_state(request.family_id)
        derived_cards = derive_active_cards(state)
        derived_suggestions = derive_suggestions(state)

        # Build UI data with real data from conversation service + derived UI
        ui_data = {
            "suggestions": derived_suggestions,  # Derived from state
            "cards": derived_cards,  # Derived from state
            "progress": result["completeness"] / 100,  # Convert to 0-1 scale
            "extracted_data": result.get("extracted_data", {}),
            "stats": result.get("stats", {}),
            "artifacts": artifacts_for_ui  # 🌟 Wu Wei: Include artifacts
        }

        return SendMessageResponse(
            response=result["response"],
            stage=session["current_stage"],
            ui_data=ui_data
        )

    except Exception as e:
        # Log error and return graceful fallback
        import logging
        logging.error(f"Error in send_message: {e}", exc_info=True)

        return SendMessageResponse(
            response="מצטערת, נתקלתי בבעיה טכנית. בואי ננסה שוב.",
            stage="interview",
            ui_data={
                "suggestions": ["נסה שוב", "דבר עם תמיכה"],
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
async def upload_video(request: UploadVideoRequest):
    """
    העלאת וידאו (simulated)
    """
    session = app_state.get_or_create_session(request.family_id)

    # הוסף וידאו לsession
    video_data = {
        "video_id": request.video_id,
        "scenario": request.scenario,
        "duration_seconds": request.duration_seconds,
        "uploaded_at": datetime.now().isoformat()
    }

    session["videos"].append(video_data)

    # שמירה ב-Graphiti
    await app_state.graphiti.add_episode(
        name=f"video_upload_{request.video_id}",
        episode_body=video_data,
        group_id=request.family_id
    )

    total_videos = len(session["videos"])

    # בדיקה אם הושלמו כל הסרטונים הנדרשים
    num_required = len(session.get("video_guidelines", {}).get("scenarios", []))
    if num_required == 0:
        num_required = 3  # ברירת מחדל

    analysis_started = False
    if total_videos >= num_required:
        # מעבר אוטומטי לשלב ניתוח
        session["current_stage"] = "video_analysis"
        analysis_started = True

    return {
        "success": True,
        "video_id": request.video_id,
        "total_videos": total_videos,
        "required_videos": num_required,
        "analysis_started": analysis_started,
        "next_stage": session["current_stage"]
    }

@router.post("/video/analyze")
async def analyze_videos(family_id: str):
    """
    ניתוח כל הוידאואים
    """
    session = app_state.get_or_create_session(family_id)

    if not session["videos"]:
        raise HTTPException(status_code=400, detail="No videos to analyze")

    # קריאה ל-LLM לניתוח
    analysis_result = await app_state.llm.chat_with_structured_output(
        messages=[Message(
            role="system",
            content=f"נתח {len(session['videos'])} וידאואים"
        )],
        response_schema={"behavioral_observations": [], "key_findings_summary": ""}
    )

    # שמירה ב-Graphiti
    await app_state.graphiti.add_episode(
        name=f"video_analysis_{family_id}",
        episode_body=analysis_result,
        group_id=family_id,
        reference_time=datetime.now()
    )

    # שמירת תוצאות ניתוח ב-session
    session["video_analysis"] = analysis_result

    # מעבר אוטומטי ליצירת דוחות
    session["current_stage"] = "report_generation"

    # יצירה אוטומטית של דוחות
    await _generate_reports_internal(family_id, session)

    return {
        "success": True,
        "analysis": analysis_result,
        "next_stage": session["current_stage"]
    }

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
    interview_service = get_interview_service()
    view_manager = get_view_manager()

    # Get session state
    session = interview_service.get_or_create_session(family_id)
    data = session.extracted_data

    # 🌟 Wu Wei: Build artifacts for view availability checks
    artifacts = {}
    for artifact_id, artifact in session.artifacts.items():
        artifacts[artifact_id] = {
            "exists": artifact.exists,
            "status": artifact.status
        }

    # Build context for view availability checks
    context = {
        "phase": session.phase,
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
        phase=session.phase,
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
    interview_service = get_interview_service()
    view_manager = get_view_manager()

    # Get view definition
    view = view_manager.get_view(view_id)
    if not view:
        raise HTTPException(status_code=404, detail=f"View '{view_id}' not found")

    # Get session state
    session = interview_service.get_or_create_session(family_id)
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
    context = {
        "phase": session.phase,
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
        view_content["context"] = {
            "child_name": data.child_name,
            "phase": session.phase,
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

    interview_service = get_interview_service()
    session = interview_service.get_or_create_session(family_id)

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

    interview_service = get_interview_service()
    session = interview_service.get_or_create_session(family_id)

    # Get artifact
    artifact = session.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(
            status_code=404,
            detail=f"Artifact '{artifact_id}' not found for family {family_id}"
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

    interview_service = get_interview_service()
    session = interview_service.get_or_create_session(request.family_id)

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

@router.get("/state/{family_id}")
async def get_family_state(family_id: str):
    """
    Get complete family state - the DNA of the system.
    Everything (cards, greeting, suggestions) derives from this.
    """
    graphiti = get_mock_graphiti()
    state = graphiti.get_or_create_state(family_id)

    # Derive UI elements from state
    greeting = derive_contextual_greeting(state)
    cards = derive_active_cards(state)
    suggestions = derive_suggestions(state)

    return {
        "state": state.dict(),
        "ui": {
            "greeting": greeting,
            "cards": cards,
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

    # Generate family ID if not provided
    family_id = request.family_id or f"test_{request.persona_id}_{int(datetime.now().timestamp())}"

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

    try:
        response = await simulator.generate_response(
            family_id=request.family_id,
            chitta_question=request.chitta_question,
            llm_provider=app_state.llm,
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
