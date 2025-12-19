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

# === Timeline Generation ===

