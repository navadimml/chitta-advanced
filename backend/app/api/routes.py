"""
API Routes for Chitta
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.core.app_state import app_state

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

# === Endpoints ===

@router.get("/")
async def root():
    """API root"""
    return {"message": "Chitta API", "version": "1.0.0"}

@router.post("/chat/send", response_model=SendMessageResponse)
async def send_message(request: SendMessageRequest):
    """
    שליחת הודעה לצ'יטה
    """
    if not app_state.initialized:
        raise HTTPException(status_code=500, detail="App not initialized")

    # קבל/צור session
    session = app_state.get_or_create_session(request.family_id)

    # הוסף הודעת משתמש
    session["interview_messages"].append({
        "role": "user",
        "content": request.message,
        "timestamp": datetime.now().isoformat()
    })

    # קבל תגובה מה-LLM
    messages = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in session["interview_messages"]
    ]

    # אם זו ההודעה הראשונה, הוסף system prompt
    if len(session["interview_messages"]) == 1:
        messages.insert(0, {
            "role": "system",
            "content": "אתה Chitta - עוזרת AI חמה שמנהלת ראיון התפתחותי עם הורה."
        })

    response = await app_state.llm.chat(messages)

    # בדיקה אם הראיון הסתיים
    if response == "INTERVIEW_COMPLETE":
        # השלמת ראיון אוטומטית
        summary_result = await app_state.llm.chat_with_structured_output(
            messages=[{"role": "system", "content": "סכם את הראיון"}],
            response_schema={"interview_summary": {}, "video_guidelines": {}}
        )

        # שמירה ב-session
        session["interview_summary"] = summary_result["interview_summary"]
        session["video_guidelines"] = summary_result["video_guidelines"]
        session["current_stage"] = "video_upload"

        # שמירה ב-Graphiti
        await app_state.graphiti.add_episode(
            name=f"interview_summary_{request.family_id}",
            episode_body=summary_result["interview_summary"],
            group_id=request.family_id
        )

        await app_state.graphiti.add_episode(
            name=f"video_guidelines_{request.family_id}",
            episode_body=summary_result["video_guidelines"],
            group_id=request.family_id
        )

        response = "מעולה! יצרתי עבורך הנחיות צילום מותאמות אישית. תראי אותן למטה. כשתהיי מוכנה, תוכלי להעלות את הסרטונים."

        # הוסף תגובה להיסטוריה
        session["interview_messages"].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })

        # UI data עם כרטיסי וידאו
        ui_data = {
            "suggestions": ["אעלה סרטון עכשיו", "אקרא את ההנחיות"],
            "cards": _generate_cards(session),
            "progress": 0.4,
            "video_guidelines": summary_result["video_guidelines"]
        }

        return SendMessageResponse(
            response=response,
            stage=session["current_stage"],
            ui_data=ui_data
        )

    # הוסף תגובה להיסטוריה
    session["interview_messages"].append({
        "role": "assistant",
        "content": response,
        "timestamp": datetime.now().isoformat()
    })

    # בנה UI data
    ui_data = {
        "suggestions": _generate_suggestions(session),
        "cards": _generate_cards(session),
        "progress": len(session["interview_messages"]) / 10  # Rough estimate
    }

    return SendMessageResponse(
        response=response,
        stage=session["current_stage"],
        ui_data=ui_data
    )

@router.post("/interview/complete", response_model=CompleteInterviewResponse)
async def complete_interview(family_id: str):
    """
    סיום ראיון ויצירת הנחיות וידאו
    """
    session = app_state.get_or_create_session(family_id)

    # קריאה ל-LLM לסיכום
    summary_result = await app_state.llm.chat_with_structured_output(
        messages=[{
            "role": "system",
            "content": "סכם את הראיון"
        }],
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

    return {
        "success": True,
        "video_id": request.video_id,
        "total_videos": len(session["videos"])
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
        messages=[{
            "role": "system",
            "content": f"נתח {len(session['videos'])} וידאואים"
        }],
        response_schema={"behavioral_observations": [], "key_findings_summary": ""}
    )

    # שמירה ב-Graphiti
    await app_state.graphiti.add_episode(
        name=f"video_analysis_{family_id}",
        episode_body=analysis_result,
        group_id=family_id
    )

    session["current_stage"] = "report_generation"

    return {
        "success": True,
        "analysis": analysis_result
    }

@router.post("/reports/generate")
async def generate_reports(family_id: str):
    """
    יצירת דוחות (מקצועי + להורה)
    """
    session = app_state.get_or_create_session(family_id)

    # דוח מקצועי
    prof_report = await app_state.llm.chat_with_structured_output(
        messages=[{
            "role": "system",
            "content": "צור דוח מקצועי"
        }],
        response_schema={"report_markdown": "", "professional_recommendations_data": []}
    )

    # דוח להורה
    parent_report = await app_state.llm.chat_with_structured_output(
        messages=[{
            "role": "system",
            "content": "צור מכתב להורה"
        }],
        response_schema={"parent_letter": "", "actionable_next_steps": []}
    )

    # שמירה ב-Graphiti
    await app_state.graphiti.add_episode(
        name=f"professional_report_{family_id}",
        episode_body=prof_report,
        group_id=family_id
    )

    await app_state.graphiti.add_episode(
        name=f"parent_report_{family_id}",
        episode_body=parent_report,
        group_id=family_id
    )

    session["current_stage"] = "consultation"

    return {
        "success": True,
        "professional_report": prof_report,
        "parent_report": parent_report
    }

@router.get("/timeline/{family_id}")
async def get_timeline(family_id: str):
    """
    קבלת timeline של כל המסע
    """
    # חיפוש בגרף
    episodes = await app_state.graphiti.search(
        query="all events",
        group_id=family_id,
        num_results=100
    )

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

    return {"timeline": timeline}

# === Helper Functions ===

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

def _generate_cards(session: dict) -> List[dict]:
    """יצירת כרטיסים דינמיים"""
    cards = []

    if session["current_stage"] == "video_upload" and "video_guidelines" in session:
        for scenario in session["video_guidelines"].get("scenarios", []):
            cards.append({
                "type": "video_guideline",
                "title": scenario["title"],
                "description": scenario["description"],
                "priority": scenario.get("priority", "recommended")
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
        "report": "דוח מוכן"
    }

    return titles.get(episode_type, "אירוע")
