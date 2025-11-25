"""
Development-only routes for testing and debugging
"""

from fastapi import APIRouter, HTTPException
from typing import Literal
import logging
from datetime import datetime

from app.services.session_service import get_session_service
from app.services.lifecycle_manager import get_lifecycle_manager
from app.services.prerequisite_service import get_prerequisite_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dev", tags=["Development"])


# Test scenarios with different stages of completion
TEST_SCENARIOS = {
    "early_conversation": {
        "description": "Early conversation - basic info only",
        "data": {
            "child_name": "דני",
            "age": 3,
            "gender": "male",
            "primary_concerns": ["speech"],
        },
        "completeness": 0.3,
        "message_count": 3,
    },
    "guidelines_ready": {
        "description": "Rich knowledge - guidelines should generate",
        "data": {
            "child_name": "דני",
            "age": 3,
            "gender": "male",
            "primary_concerns": ["speech", "social"],
            "concern_details": "דני לא מדבר הרבה ומתקשה לשחק עם ילדים אחרים. כשהוא משחק בגן, הוא נוטה לשחק לבד ולא מגיב כשילדים מנסים להצטרף אליו. הוא לא משתמש במילים הרבה, בעיקר מצביע או מושך אותי למה שהוא רוצה.",
            "strengths": "דני אוהב לבנות עם קוביות ויש לו דמיון מדהים. הוא יכול לבנות מגדלים גבוהים ומורכבים. הוא גם אוהב ספרים ויכול להתרכז בהם לזמן ארוך.",
            "developmental_history": "דני נולד בזמן, התפתחות תקינה עד גיל שנה וחצי, אז החלו הקשיים בשפה. הוא התחיל ללכת בזמן (13 חודשים) אבל המילים הראשונות הגיעו מאוחר (24 חודשים).",
            "family_context": "דני הוא הילד הראשון במשפחה, יש לו אח קטן בן שנה. אבא עובד הרבה, אמא בחופשת לידה. יש קשר טוב עם סבא וסבתא שעוזרים הרבה.",
            "daily_routines": "דני הולך לגן בבוקר (8:00-13:00), אוכל טוב, ישן היטב בלילה (20:00-7:00). אחר הצהריים משחק בבית או בפארק. אוהב מאוד את זמן האמבטיה.",
        },
        "completeness": 0.8,
        "message_count": 12,
    },
    "videos_uploaded": {
        "description": "Videos uploaded - ready for analysis",
        "data": {
            "child_name": "דני",
            "age": 3,
            "gender": "male",
            "primary_concerns": ["speech", "social"],
            "concern_details": "דני לא מדבר הרבה ומתקשה לשחק עם ילדים אחרים. כשהוא משחק בגן, הוא נוטה לשחק לבד ולא מגיב כשילדים מנסים להצטרף אליו.",
            "strengths": "דני אוהב לבנות עם קוביות ויש לו דמיון מדהים. הוא יכול לבנות מגדלים גבוהים ומורכבים.",
            "developmental_history": "דני נולד בזמן, התפתחות תקינה עד גיל שנה וחצי, אז החלו הקשיים בשפה.",
            "family_context": "דני הוא הילד הראשון במשפחה, יש לו אח קטן בן שנה.",
            "daily_routines": "דני הולך לגן בבוקר, אוכל טוב, ישן היטב בלילה.",
        },
        "completeness": 0.85,
        "message_count": 15,
        "uploaded_videos": 3,  # Simulate videos uploaded
    },
    "living_dashboard": {
        "description": "🌟 Living Dashboard demo - all artifacts ready",
        "data": {
            "child_name": "דני",
            "age": 3,
            "gender": "male",
            "primary_concerns": ["speech", "social"],
            "concern_details": "דני לא מדבר הרבה ומתקשה לשחק עם ילדים אחרים.",
            "strengths": "דני אוהב לבנות עם קוביות ויש לו דמיון מדהים.",
            "developmental_history": "דני נולד בזמן, התפתחות תקינה עד גיל שנה וחצי.",
            "family_context": "דני הוא הילד הראשון במשפחה.",
            "daily_routines": "דני הולך לגן בבוקר, אוכל טוב, ישן היטב.",
        },
        "completeness": 0.95,
        "message_count": 15,
        "uploaded_videos": 3,
        "seed_artifacts": True,  # Special flag to seed mock artifacts
    },
}


@router.post("/seed/{scenario}")
async def seed_test_scenario(
    scenario: Literal["early_conversation", "guidelines_ready", "videos_uploaded", "living_dashboard"],
    family_id: str = "dev_test_family",
    generate_artifacts: bool = False
):
    """
    🔧 DEV ONLY: Seed a test scenario with pre-populated data

    This allows you to quickly test features at different stages without
    going through the full conversation flow.

    Available scenarios:
    - early_conversation: Basic info only, no guidelines yet
    - guidelines_ready: Rich knowledge, triggers guideline generation
    - videos_uploaded: Simulates videos uploaded, ready for analysis

    Args:
        scenario: Which test scenario to seed
        family_id: Family ID to use (default: dev_test_family)
        generate_artifacts: If True, triggers artifact generation (SLOW - 2+ min)
                          If False (default), only seeds data (FAST - instant)

    Returns the seeded session state
    """

    scenario_config = TEST_SCENARIOS[scenario]

    logger.info(f"🌱 Seeding test scenario '{scenario}' for family '{family_id}'")

    # Get services
    session_service = get_session_service()
    lifecycle_manager = get_lifecycle_manager()
    prereq_service = get_prerequisite_service()

    # Create/update session
    session = session_service.get_or_create_session(family_id)
    session_service.update_extracted_data(family_id, scenario_config["data"])
    session.completeness = scenario_config["completeness"]

    # Add realistic conversation history based on extracted data
    # This allows artifact generation to extract meaningful content
    child_name = scenario_config["data"].get("child_name", "הילד/ה")
    age = scenario_config["data"].get("age", 3)
    concerns = scenario_config["data"].get("concern_details", "")
    strengths = scenario_config["data"].get("strengths", "")
    dev_history = scenario_config["data"].get("developmental_history", "")
    family_ctx = scenario_config["data"].get("family_context", "")
    routines = scenario_config["data"].get("daily_routines", "")

    # Build realistic conversation turns
    conversation_turns = [
        ("user", f"שלום, אני רוצה לדבר על {child_name}"),
        ("assistant", f"שלום! שמחה להכיר. {child_name} - שם יפה. בן כמה הוא/היא?"),
        ("user", f"{child_name} בן/בת {age}"),
        ("assistant", "תודה. מה הדאגה העיקרית שלך לגבי ההתפתחות שלו/ה?"),
        ("user", concerns if concerns else "יש לי כמה דאגות"),
        ("assistant", "אני מבינה. ספרי לי יותר על החוזקות שלו/ה - במה הוא/היא מצטיין/ת?"),
        ("user", strengths if strengths else "יש לו/ה הרבה חוזקות"),
        ("assistant", "נהדר. איך היתה ההתפתחות שלו/ה עד כה?"),
        ("user", dev_history if dev_history else "התפתחות תקינה בעיקרון"),
        ("assistant", "תודה. ספרי לי על המשפחה והסביבה שלכם"),
        ("user", family_ctx if family_ctx else "משפחה רגילה"),
        ("assistant", "מה נראה יום טיפוסי אצלכם?"),
        ("user", routines if routines else "יום רגיל, גן בבוקר"),
    ]

    # Add only the number of turns specified in scenario
    for i, (role, content) in enumerate(conversation_turns[:scenario_config["message_count"]]):
        session.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

    # Handle video upload simulation
    if scenario_config.get("uploaded_videos"):
        from app.models.family_state import Video
        from app.services.mock_graphiti import get_mock_graphiti

        graphiti = get_mock_graphiti()
        state = graphiti.get_or_create_state(family_id)

        for i in range(scenario_config["uploaded_videos"]):
            video = Video(
                id=f"vid_{i+1}",
                scenario=["ארוחת בוקר", "משחק חופשי", "זמן אמבטיה"][i % 3],
                uploaded_at=datetime.now(),
                duration_seconds=60 + i * 30,
            )
            state.videos_uploaded.append(video)

        logger.info(f"📹 Simulated {len(state.videos_uploaded)} videos uploaded")

    # 🌟 Living Dashboard: Seed mock artifacts for demo
    if scenario_config.get("seed_artifacts"):
        from app.models.artifact import Artifact

        logger.info("🌟 Seeding Living Dashboard demo artifacts...")

        # Mock Parent Report (markdown with sections for Living Documents)
        parent_report_content = """# דוח התפתחות - דני

## סיכום כללי

דני הוא ילד בן 3 עם יכולות קוגניטיביות טובות. הוא מראה עניין רב בפעילויות בנייה ומשחקי דמיון.
ישנם תחומים הדורשים תמיכה, במיוחד בתחום התקשורת והאינטראקציה החברתית.

## התפתחות מוטורית

דני מראה התפתחות מוטורית תקינה לגילו. הוא יכול לרוץ, לקפוץ ולטפס.
המוטוריקה העדינה שלו טובה - הוא בונה מגדלים גבוהים ומורכבים עם קוביות.

## תקשורת ושפה

זהו תחום שדורש תשומת לב. דני משתמש במילים בודדות ובעיקר מתקשר באמצעות הצבעה ומשיכה.
הוא מבין הוראות פשוטות אך מתקשה לבטא את עצמו מילולית.

### המלצות לתקשורת
- לעודד תקשורת מילולית בכל הזדמנות
- להשתמש בתמונות ומילים יחד
- לשיר שירים פשוטים עם חזרות

## התפתחות חברתית-רגשית

דני נוטה לשחק לבד ומתקשה להצטרף למשחק עם ילדים אחרים.
הוא לא תמיד מגיב כשילדים מנסים לשתף אותו במשחק.

## חוזקות

- דמיון עשיר ויכולת בנייה מרשימה
- יכולת ריכוז גבוהה בפעילויות שמעניינות אותו
- סקרנות והתעניינות בספרים

## המלצות

1. התייעצות עם קלינאית תקשורת
2. הצטרפות לקבוצת משחק קטנה
3. המשך עידוד פעילויות בנייה ויצירה
"""

        parent_report = Artifact(
            artifact_id="baseline_parent_report",
            artifact_type="report",
            status="ready",
            content=parent_report_content,
            content_format="markdown",
            created_at=datetime.now(),
            ready_at=datetime.now()
        )
        session.add_artifact(parent_report)

        # Mock Video Guidelines (JSON) - Structure matches VideoGuidelinesView component
        guidelines_content = {
            "child_name": "דני",
            "introduction": "הסרטונים שתצלמו יעזרו לנו להבין טוב יותר את דני בסביבה הטבעית שלו. אנחנו לא מחפשים 'ביצועים' - אלא רגעים אמיתיים מהחיים. הסרטונים האלה יאפשרו לנו לראות את החוזקות של דני, להבין את סגנון התקשורת שלו, ולזהות הזדמנויות לתמיכה בהתפתחות שלו.",
            "estimated_duration": "15-20 דקות סה״כ",
            "focus_areas": ["תקשורת", "אינטראקציה חברתית", "משחק"],
            "scenarios": [
                {
                    "title": "ארוחת בוקר",
                    "context": "רגע יומיומי שמאפשר לראות תקשורת טבעית",
                    "duration": "3-5 דקות",
                    "what_to_film": "צלמו את דני במהלך ארוחת הבוקר הרגילה. שימו את הטלפון במקום יציב (אפשר להישען על קופסה או ספר) כך שרואים את דני ואת מי שאוכל איתו. פשוט תנהגו כרגיל - דברו, אכלו, היו טבעיים.",
                    "why_matters": "ארוחות הן הזדמנות מצוינת לראות איך דני מתקשר כשהוא רוצה משהו, איך הוא מגיב לשיחה, ואיך הוא מתמודד עם שגרה יומיומית.",
                    "analyst_context": {
                        "guideline_title": "ארוחת בוקר",
                        "look_for": ["יוזמת תקשורת", "בקשות", "קשר עין", "תגובה לפניות"]
                    }
                },
                {
                    "title": "משחק חופשי",
                    "context": "הזדמנות לראות יצירתיות ודמיון",
                    "duration": "5-7 דקות",
                    "what_to_film": "תנו לדני לבחור במה לשחק - קוביות, בובות, מכוניות, כל מה שהוא אוהב. שבו לידו על הרצפה עם הטלפון. אתם יכולים לשחק איתו או פשוט לשבת ליד ולצפות. אל תכוונו את המשחק - תנו לו להוביל.",
                    "why_matters": "משחק חופשי מראה לנו את עולם הדמיון של דני, איך הוא פותר בעיות, ואיך הוא מתייחס לצעצועים ולאנשים סביבו.",
                    "analyst_context": {
                        "guideline_title": "משחק חופשי",
                        "look_for": ["משחק סימבולי", "ריכוז", "יצירתיות", "שיתוף"]
                    }
                },
                {
                    "title": "זמן אמבטיה",
                    "context": "רגע של קרבה וויסות חושי",
                    "duration": "3-5 דקות",
                    "what_to_film": "צלמו את דני בזמן האמבטיה או משחק עם מים. שימו לב לבטיחות - הטלפון צריך להיות במקום יבש ויציב. צלמו איך הוא מגיב למים, לבועות סבון, לצעצועי אמבטיה.",
                    "why_matters": "זמן אמבטיה מראה לנו איך דני מתמודד עם חוויות חושיות (מים, טמפרטורה, מגע) ואיך הוא משתף פעולה בשגרה יומיומית.",
                    "analyst_context": {
                        "guideline_title": "זמן אמבטיה",
                        "look_for": ["ויסות חושי", "שיתוף פעולה", "הנאה", "תקשורת"]
                    }
                }
            ],
            "general_tips": [
                "צלמו בסביבה טבעית ורגועה - לא צריך לסדר או להכין משהו מיוחד",
                "אל תנסו לכוון את דני או לבקש ממנו לעשות דברים - תנו לו להיות טבעי",
                "תאורה טובה חשובה - עדיף אור טבעי מהחלון",
                "אם דני שם לב למצלמה ומופרע - עצרו וחכו שיתרגל, או נסו שוב מאוחר יותר",
                "אין 'סרטון מושלם' - גם רגעים של תסכול או קושי הם בעלי ערך"
            ]
        }

        import json
        guidelines = Artifact(
            artifact_id="baseline_video_guidelines",
            artifact_type="guidelines",
            status="ready",
            content=json.dumps(guidelines_content, ensure_ascii=False),
            content_format="json",
            created_at=datetime.now(),
            ready_at=datetime.now()
        )
        session.add_artifact(guidelines)

        # Add journal entries to state
        from app.models.family_state import JournalEntry, Artifact as FamilyArtifact
        graphiti = get_mock_graphiti()
        state = graphiti.get_or_create_state(family_id)

        state.journal_entries = [
            JournalEntry(
                id="entry_1",
                content="היום דני אמר 'מים' בפעם הראשונה! התרגשתי מאוד.",
                timestamp=datetime.now()
            ),
            JournalEntry(
                id="entry_2",
                content="שיחקנו יחד בקוביות והוא בנה מגדל ענק.",
                timestamp=datetime.now()
            ),
        ]

        # Set child info
        state.child = {"name": "דני", "age": 3}

        # 🔧 CRITICAL: Also add artifacts to FamilyState.artifacts (for /state endpoint)
        # The frontend reads from state.artifacts, not session.artifacts
        state.artifacts["baseline_parent_report"] = FamilyArtifact(
            type="baseline_parent_report",
            content={"raw": parent_report_content, "format": "markdown"},
            created_at=datetime.now()
        )
        state.artifacts["baseline_video_guidelines"] = FamilyArtifact(
            type="baseline_video_guidelines",
            content=guidelines_content,  # Already a dict
            created_at=datetime.now()
        )

        # 📜 Add historical versions of artifacts for demo
        # This demonstrates the "version history" feature in ChildSpace
        from datetime import timedelta

        # Historical parent report (version 1 - older, shorter)
        old_report_content = """# דוח התפתחות ראשוני - דני

## סיכום כללי

דני הוא ילד בן 3. נצפו קשיים בתחום התקשורת והאינטראקציה החברתית.

## תחומים לבדיקה

- תקשורת ושפה
- התפתחות חברתית

## המלצות ראשוניות

1. להמשיך במעקב
2. לשקול הפניה להערכה מקצועית
"""
        old_report = Artifact(
            artifact_id="baseline_parent_report_v1",
            artifact_type="report",
            status="ready",
            content=old_report_content,
            content_format="markdown",
            created_at=datetime.now() - timedelta(days=7),
            ready_at=datetime.now() - timedelta(days=7)
        )
        session.add_artifact(old_report)

        # Even older report (version 0 - initial assessment)
        initial_report_content = """# הערכה ראשונית - דני

## פרטים בסיסיים

שם: דני
גיל: 3
דאגות עיקריות: תקשורת

## הערות

ממתין למידע נוסף מההורים.
"""
        initial_report = Artifact(
            artifact_id="baseline_parent_report_v0",
            artifact_type="report",
            status="ready",
            content=initial_report_content,
            content_format="markdown",
            created_at=datetime.now() - timedelta(days=14),
            ready_at=datetime.now() - timedelta(days=14)
        )
        session.add_artifact(initial_report)

        logger.info(f"✅ Seeded {len(session.artifacts)} artifacts (including history) for Living Dashboard demo")

    # Build context for card evaluation
    session_data = {
        "family_id": family_id,
        "extracted_data": session.extracted_data.model_dump(),
        "message_count": len(session.conversation_history),
        "artifacts": session.artifacts,
        "completeness": session.completeness,
    }
    context = prereq_service.get_context_for_cards(session_data)
    context["conversation_history"] = session.conversation_history

    # For guidelines_ready scenario, we need to pre-generate interview_summary
    # Otherwise the guidelines generation will fail due to missing dependency
    if scenario == "guidelines_ready" and not generate_artifacts:
        logger.info(f"📝 Pre-generating interview_summary for guidelines_ready scenario...")
        from app.services.artifact_generation_service import ArtifactGenerationService
        from app.services.llm.factory import create_llm_provider

        # Create artifact service
        llm_provider = create_llm_provider("gemini", "gemini-2.5-pro")
        artifact_service = ArtifactGenerationService(llm_provider)

        # Generate interview_summary artifact directly
        try:
            interview_summary_artifact = await artifact_service.generate_interview_summary(
                artifact_id="baseline_interview_summary",
                session_data={
                    "family_id": family_id,
                    "extracted_data": session.extracted_data.model_dump(),
                    "conversation_history": session.conversation_history,
                    "artifacts": {}
                }
            )
            session.add_artifact(interview_summary_artifact)
            logger.info(f"✅ Pre-generated interview_summary: {interview_summary_artifact.status}")
        except Exception as e:
            logger.error(f"❌ Failed to pre-generate interview_summary: {e}")
            import traceback
            traceback.print_exc()

    # Optionally trigger artifact generation (SLOW - 2+ min for guidelines)
    result = None
    if generate_artifacts:
        logger.info(f"⏳ Triggering artifact generation (this may take 2+ minutes)...")
        result = await lifecycle_manager.process_lifecycle_events(
            family_id=family_id,
            context=context,
            session=session
        )
        logger.info(f"✅ Seeded scenario '{scenario}': {result['artifacts_generated']}")
    else:
        logger.info(f"✅ Seeded scenario '{scenario}' (data only, artifacts pre-generated if needed)")

    return {
        "success": True,
        "scenario": scenario,
        "description": scenario_config["description"],
        "family_id": family_id,
        "generate_artifacts": generate_artifacts,
        "session_state": {
            "completeness": session.completeness,
            "message_count": len(session.conversation_history),
            "artifacts": [
                {
                    "artifact_id": a.artifact_id,
                    "status": a.status,
                    "is_ready": a.is_ready,
                }
                for a in session.artifacts.values()
            ],
        },
        "lifecycle_result": result,
    }


@router.get("/scenarios")
async def list_scenarios():
    """
    🔧 DEV ONLY: List all available test scenarios
    """
    return {
        "scenarios": {
            name: {
                "name": name,
                "description": config["description"],
                "completeness": config["completeness"],
                "message_count": config["message_count"],
            }
            for name, config in TEST_SCENARIOS.items()
        }
    }


@router.delete("/reset/{family_id}")
async def reset_session(family_id: str):
    """
    🔧 DEV ONLY: Reset a session completely
    """
    session_service = get_session_service()

    # For in-memory mode, just recreate the session
    session_service.sessions.pop(family_id, None)

    logger.info(f"🗑️ Reset session for family '{family_id}'")

    return {
        "success": True,
        "family_id": family_id,
        "message": "Session reset"
    }
