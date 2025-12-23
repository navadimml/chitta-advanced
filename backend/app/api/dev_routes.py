"""
Development-only routes for testing and debugging

Key endpoints:
- /dev/xray/personas - List available parent personas for testing
- /dev/xray/run/{persona} - Run dynamic X-Ray test with simulated parent
- /dev/xray/reports - List all X-Ray reports
- /dev/xray/html/{filename} - View HTML dashboard for a report
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from typing import Optional
import logging
import json
import asyncio
import sys
from pathlib import Path
from datetime import datetime

from app.services.session_service import get_session_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dev", tags=["Development"])

# X-Ray Dashboard paths
XRAY_OUTPUT_DIR = Path("/home/shlomi/projects/chitta/chitta-advanced/backend/tests/xray_outputs")
XRAY_TEST_SCRIPT = Path("/home/shlomi/projects/chitta/chitta-advanced/backend/tests/test_temporal_xray.py")

# Parent Personas (keep in sync with test_temporal_xray.py)
PARENT_PERSONAS = {
    "scattered_worried_mom": {
        "description": "אמא מודאגת שקופצת בין נושאים, מפקפקת בעצמה",
        "child_name": "יואב",
        "child_age": 4,
        "concerns": ["שונה מילדים אחרים", "מעברים קשים", "רגישות לרעשים"],
    },
    "focused_dad": {
        "description": "אבא ממוקד ועניני, מחפש תשובות ברורות",
        "child_name": "דניאל",
        "child_age": 3,
        "concerns": ["לא מדבר", "לא עונה לשם"],
    },
    "emotional_mom_motor": {
        "description": "אמא רגשית, מודאגת מהתפתחות מוטורית",
        "child_name": "מאיה",
        "child_age": 3.5,
        "concerns": ["נופלת הרבה", "מתעייפת מהר"],
    },
    "quick_test_parent": {
        "description": "הורה פשוט לבדיקה מהירה",
        "child_name": "דניאל",
        "child_age": 3,
        "concerns": ["לא מדבר"],
    },
}


@router.get("/xray/personas")
async def list_personas():
    """
    🧪 List available parent personas for X-Ray testing

    Each persona simulates a different type of parent with unique:
    - Communication style (scattered, focused, emotional)
    - Child profile (name, age, concerns)
    - Information to reveal during conversation
    """
    return {
        "personas": {
            name: {
                "name": name,
                **info
            }
            for name, info in PARENT_PERSONAS.items()
        },
        "usage": "POST /api/dev/xray/run/{persona}?max_turns=20"
    }


@router.get("/xray/reports")
async def list_xray_reports_detailed():
    """
    🧪 List all X-Ray reports with metadata

    Returns HTML dashboard links for each report
    """
    if not XRAY_OUTPUT_DIR.exists():
        return {"reports": []}

    reports = []
    # Sort by modification time (newest first)
    html_files = sorted(XRAY_OUTPUT_DIR.glob("*.html"), key=lambda f: f.stat().st_mtime, reverse=True)
    for html_file in html_files:
        json_file = html_file.with_suffix('.json')
        md_file = html_file.with_suffix('.md')

        # Extract info from filename: xray_{scenario}_{timestamp}.html
        parts = html_file.stem.split('_')
        if len(parts) >= 3:
            timestamp = parts[-2] + "_" + parts[-1]
            scenario = "_".join(parts[1:-2])
        else:
            timestamp = ""
            scenario = html_file.stem

        report_info = {
            "name": html_file.stem,
            "scenario": scenario,
            "timestamp": timestamp,
            "dashboard_url": f"/api/dev/xray/html/{html_file.name}",
            "json_url": f"/api/dev/xray/report/{json_file.name}" if json_file.exists() else None,
            "has_json": json_file.exists(),
            "has_md": md_file.exists(),
        }

        # Try to get summary from JSON
        if json_file.exists():
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    report_info["summary"] = {
                        "total_turns": data.get("summary", {}).get("total_turns", 0),
                        "hypotheses_formed": data.get("summary", {}).get("hypotheses_formed", 0),
                        "artifacts_created": data.get("summary", {}).get("artifacts_created", 0),
                    }
            except:
                pass

        reports.append(report_info)

    return {
        "reports": reports[:20],  # Limit to 20 most recent
        "total": len(reports),
    }


@router.get("/xray/html/{filename}", response_class=HTMLResponse)
async def get_xray_html_dashboard(filename: str):
    """
    🧪 Serve HTML dashboard for a specific X-Ray report

    This is the main way to view test results interactively.
    """
    # Sanitize filename
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    if not filename.endswith(".html"):
        filename = f"{filename}.html"

    file_path = XRAY_OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Dashboard not found: {filename}")

    return HTMLResponse(content=file_path.read_text(encoding='utf-8'))


# Track running tests
_running_tests = {}


@router.post("/xray/run/{persona}")
async def run_xray_test(
    persona: str,
    max_turns: int = 20,
):
    """
    🧪 Run a dynamic X-Ray test with simulated parent

    This starts a test in the background and returns immediately.
    The test uses LLM to generate realistic parent responses.

    Args:
        persona: One of the available personas (see /dev/xray/personas)
        max_turns: Maximum conversation turns (default: 20)

    Returns:
        test_id and status. Poll /dev/xray/status/{test_id} for results.
    """
    if persona not in PARENT_PERSONAS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown persona: {persona}. Available: {list(PARENT_PERSONAS.keys())}"
        )

    # Generate test ID
    test_id = f"{persona}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Mark as running
    _running_tests[test_id] = {
        "status": "running",
        "persona": persona,
        "max_turns": max_turns,
        "started_at": datetime.now().isoformat(),
        "output_file": None,
    }

    # Dynamic timeout: ~90 seconds per turn + 5 min base
    # 20 turns = 35 min, 10 turns = 20 min, 5 turns = 12.5 min
    timeout_seconds = 300 + (max_turns * 90)

    # Run test in background using asyncio (non-blocking)
    async def run_test():
        try:
            # Use async subprocess to avoid blocking the event loop
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                str(XRAY_TEST_SCRIPT),
                "--persona", persona,
                "--max-turns", str(max_turns),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=XRAY_OUTPUT_DIR.parent.parent,  # backend directory
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                _running_tests[test_id]["status"] = "timeout"
                _running_tests[test_id]["error"] = f"Test timed out after {timeout_seconds // 60} minutes"
                return

            # Find the generated files
            # Look for the most recent file matching the pattern
            pattern = f"xray_dynamic_{persona}_*.html"
            html_files = sorted(XRAY_OUTPUT_DIR.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True)

            if html_files:
                output_file = html_files[0].name
                _running_tests[test_id]["output_file"] = output_file
                _running_tests[test_id]["dashboard_url"] = f"/api/dev/xray/html/{output_file}"
                _running_tests[test_id]["status"] = "completed"
            else:
                _running_tests[test_id]["status"] = "completed_no_output"

            _running_tests[test_id]["completed_at"] = datetime.now().isoformat()
            _running_tests[test_id]["stdout"] = stdout.decode()[-2000:] if stdout else ""
            _running_tests[test_id]["stderr"] = stderr.decode()[-1000:] if stderr else ""

        except Exception as e:
            _running_tests[test_id]["status"] = "error"
            _running_tests[test_id]["error"] = str(e)

    # Schedule the task to run in the background
    asyncio.create_task(run_test())

    return {
        "test_id": test_id,
        "status": "started",
        "persona": persona,
        "max_turns": max_turns,
        "check_status_url": f"/api/dev/xray/status/{test_id}",
        "message": "Test started in background. Check status for results.",
    }


@router.get("/xray/status/{test_id}")
async def get_xray_test_status(test_id: str):
    """
    🧪 Check status of a running X-Ray test
    """
    if test_id not in _running_tests:
        raise HTTPException(status_code=404, detail=f"Test not found: {test_id}")

    return _running_tests[test_id]


@router.get("/xray/dashboard", response_class=HTMLResponse)
async def xray_dashboard():
    """
    Serve a simple dashboard index page listing all reports
    """
    # Generate a simple HTML page listing all reports
    if not XRAY_OUTPUT_DIR.exists():
        return HTMLResponse("<h1>No X-Ray reports found</h1>")

    html_files = sorted(XRAY_OUTPUT_DIR.glob("*.html"), key=lambda f: f.stat().st_mtime, reverse=True)[:20]

    html = """
<!DOCTYPE html>
<html dir="rtl">
<head>
    <meta charset="utf-8">
    <title>X-Ray Test Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; background: #fafafa; }
        h1 { color: #333; }
        h2 { color: #555; margin-top: 30px; }
        .report { padding: 15px; margin: 10px 0; background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .report a { color: #0066cc; text-decoration: none; font-size: 18px; font-weight: bold; }
        .report a:hover { text-decoration: underline; }
        .meta { color: #666; font-size: 14px; margin-top: 5px; }
        .personas { margin: 20px 0; padding: 20px; background: #e8f4ff; border-radius: 8px; }
        .persona { display: inline-block; margin: 5px; padding: 10px 18px; background: #0066cc; color: white; border-radius: 6px; cursor: pointer; font-size: 14px; }
        .persona:hover { background: #0055aa; }
        .settings { margin: 15px 0; padding: 15px; background: white; border-radius: 6px; }
        .settings label { font-weight: bold; margin-right: 10px; }
        .settings input { padding: 8px; border: 1px solid #ccc; border-radius: 4px; width: 80px; font-size: 16px; }
        .status-box { margin: 20px 0; padding: 20px; background: #fff3cd; border-radius: 8px; display: none; }
        .status-box.running { display: block; background: #cce5ff; }
        .status-box.completed { display: block; background: #d4edda; }
        .status-box.error { display: block; background: #f8d7da; }
        .status-box h4 { margin: 0 0 10px 0; }
        .status-box a { color: #0066cc; font-weight: bold; }
        .refresh-btn { padding: 8px 16px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; margin-left: 10px; }
        .refresh-btn:hover { background: #218838; }
    </style>
</head>
<body>
    <h1>🔬 X-Ray Test Dashboard</h1>

    <div class="personas">
        <h3>Run New Test:</h3>

        <div class="settings">
            <label for="maxTurns">Max Turns:</label>
            <input type="number" id="maxTurns" value="20" min="5" max="50">
            <span style="color: #666; font-size: 13px;">(5-50, more turns = longer test)</span>
        </div>

        <p>Click a persona to start:</p>
"""

    for name, info in PARENT_PERSONAS.items():
        html += f"""
        <div class="persona" onclick="runTest('{name}')">
            {info['child_name']} ({info['child_age']}y) - {info['description'][:30]}...
        </div>
"""

    html += """
        <p style="margin-top: 15px; font-size: 14px;">
            Or use API: <code>POST /api/dev/xray/run/{persona}?max_turns=20</code>
        </p>
    </div>

    <div id="statusBox" class="status-box">
        <h4 id="statusTitle">Test Status</h4>
        <p id="statusMessage"></p>
        <p id="statusLink"></p>
    </div>

    <h2>Recent Reports:</h2>
    <p style="color: #666; font-size: 14px;">Click any report to view the interactive dashboard with conversation timeline</p>
"""

    for html_file in html_files:
        name = html_file.stem
        html += f"""
    <div class="report">
        <a href="/api/dev/xray/html/{html_file.name}">{name}</a>
        <div class="meta">📊 Click to view interactive dashboard</div>
    </div>
"""

    html += """
    <script>
    let currentTestId = null;
    let pollInterval = null;

    async function runTest(persona) {
        const maxTurns = document.getElementById('maxTurns').value || 20;
        if (!confirm(`Run X-Ray test with persona: ${persona}?\\nMax turns: ${maxTurns}`)) return;

        // Show status box
        const statusBox = document.getElementById('statusBox');
        const statusTitle = document.getElementById('statusTitle');
        const statusMessage = document.getElementById('statusMessage');
        const statusLink = document.getElementById('statusLink');

        statusBox.className = 'status-box running';
        statusTitle.textContent = '🔄 Starting test...';
        statusMessage.textContent = `Persona: ${persona}, Max turns: ${maxTurns}`;
        statusLink.innerHTML = '';

        try {
            const response = await fetch(`/api/dev/xray/run/${persona}?max_turns=${maxTurns}`, { method: 'POST' });
            const data = await response.json();
            currentTestId = data.test_id;

            const timeoutMin = Math.round(5 + (maxTurns * 1.5));
            statusTitle.textContent = '🔄 Test running...';
            statusMessage.textContent = `Test ID: ${data.test_id}\\nExpected time: ~${timeoutMin} minutes (${maxTurns} turns).`;

            // Start polling for status
            pollInterval = setInterval(() => checkStatus(data.check_status_url), 5000);
        } catch (error) {
            statusBox.className = 'status-box error';
            statusTitle.textContent = '❌ Error starting test';
            statusMessage.textContent = error.message;
        }
    }

    async function checkStatus(statusUrl) {
        try {
            const response = await fetch(statusUrl);
            const data = await response.json();

            const statusBox = document.getElementById('statusBox');
            const statusTitle = document.getElementById('statusTitle');
            const statusMessage = document.getElementById('statusMessage');
            const statusLink = document.getElementById('statusLink');

            if (data.status === 'completed') {
                clearInterval(pollInterval);
                statusBox.className = 'status-box completed';
                statusTitle.textContent = '✅ Test completed!';
                statusMessage.textContent = `Finished at: ${data.completed_at}`;
                if (data.dashboard_url) {
                    statusLink.innerHTML = `<a href="${data.dashboard_url}" target="_blank">📊 View Results Dashboard</a>
                        <button class="refresh-btn" onclick="location.reload()">Refresh Page</button>`;
                }
            } else if (data.status === 'error' || data.status === 'timeout') {
                clearInterval(pollInterval);
                statusBox.className = 'status-box error';
                statusTitle.textContent = '❌ Test failed';
                statusMessage.textContent = data.error || 'Unknown error';
            } else {
                statusMessage.textContent = `Status: ${data.status}\\nStarted: ${data.started_at}`;
            }
        } catch (error) {
            console.error('Error checking status:', error);
        }
    }
    </script>
</body>
</html>
"""
    return HTMLResponse(html)


@router.get("/xray/list")
async def list_xray_reports():
    """
    List all available X-Ray JSON reports
    """
    if not XRAY_OUTPUT_DIR.exists():
        return []

    json_files = sorted(
        [f.name for f in XRAY_OUTPUT_DIR.glob("*.json")],
        reverse=True  # Most recent first
    )
    return json_files


@router.get("/xray/report/{filename}")
async def get_xray_report(filename: str):
    """
    Get a specific X-Ray report JSON
    """
    # Sanitize filename to prevent path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    if not filename.endswith(".json"):
        filename = f"{filename}.json"

    file_path = XRAY_OUTPUT_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Report not found: {filename}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Invalid JSON in report: {e}")


# ========================================
# 🗑️ DEPRECATED: Old seeding system removed
# ========================================
# The old TEST_SCENARIOS and /seed/{scenario} endpoint used deprecated
# services (session_service, lifecycle_manager, prerequisite_service).
# Use the new Darshan seeding system below instead:
# - GET /dev/seed/gestalt/scenarios - List available scenarios
# - POST /dev/seed/gestalt/{scenario} - Seed a scenario


@router.get("/session/{child_id}/memory")
async def get_session_memory(child_id: str):
    """
    🔧 DEV ONLY: Get session conversation memory (for X-Ray debugging)

    Returns the distilled relationship memory from reflection service.
    This shows what Chitta has learned about the parent's communication style
    and the conversation patterns - the "slow brain" processing.
    """
    from app.services.unified_state_service import get_unified_state_service

    unified = get_unified_state_service()
    session = unified.get_or_create_session(child_id)

    return {
        "child_id": child_id,
        "memory": session.memory.model_dump(),
        "turn_count": session.turn_count,
        "last_reflection_turn": session.last_reflection_turn,
        "pending_reflection": session.pending_reflection,
        "needs_reflection": session.needs_reflection()
    }


@router.delete("/reset/{child_id}")
async def reset_session(child_id: str):
    """
    🔧 DEV ONLY: Reset a session completely
    """
    session_service = get_session_service()

    # For in-memory mode, just recreate the session
    session_service.sessions.pop(child_id, None)

    logger.info(f"🗑️ Reset session for child '{child_id}'")

    return {
        "success": True,
        "child_id": child_id,
        "message": "Session reset"
    }


# ========================================
# 🧪 DARSHAN SEEDING SYSTEM
# ========================================
# These endpoints seed data for the Darshan architecture
# allowing manual testing of video flow and explorations

GESTALT_SCENARIOS = {
    "video_suggestion": {
        "name": "Video Suggestion Ready",
        "description": "השערה נוצרה ומתאימה לוידאו. כרטיס מציג כפתורי קבל/דחה.",
        "expected_cards": ["video_suggestion"],
        "next_action": "לחצו על 'כן, בבקשה' כדי לקבל הנחיות צילום",
    },
    "video_accepted": {
        "name": "Guidelines Generated",
        "description": "ההורה קיבל הצעת וידאו. הנחיות מוכנות לצפייה.",
        "expected_cards": ["video_guidelines_ready"],
        "next_action": "לחצו על 'צפה בהנחיות' ואז העלו סרטון",
    },
    "video_uploaded": {
        "name": "Video Uploaded",
        "description": "סרטון הועלה, מחכה לניתוח.",
        "expected_cards": ["video_uploaded"],
        "next_action": "לחצו על 'נתח את הסרטונים' להפעלת ניתוח",
    },
    "video_analyzed": {
        "name": "Video Analyzed",
        "description": "ניתוח הושלם - כרטיס פידבק (לא פעולה).",
        "expected_cards": ["video_analyzed"],  # Feedback card, not action card
        "next_action": "סגרו את הכרטיס והמשיכו בשיחה - התובנות כבר משולבות",
    },
    "multi_hypothesis": {
        "name": "Multiple Hypotheses",
        "description": "מספר השערות פעילות בשלבים שונים.",
        "expected_cards": ["video_suggestion"],  # Only cycle-bound cards
        "next_action": "בדקו טיפול במספר כרטיסים",
    },
    # NOTE: synthesis_ready scenario removed - synthesis is not a context card.
    # Synthesis is a HOLISTIC artifact that users pull from ChildSpace when ready.
    "rich_conversation": {
        "name": "Rich Conversation History",
        "description": "שיחה עשירה עם הרבה עובדות, סיפורים והשערות - אידיאלי לבדיקת זיכרון ותגובות.",
        "expected_cards": ["video_suggestion"],
        "next_action": "שלחו הודעה וראו שהמערכת מכירה את הילד",
    },
    "with_crystal": {
        "name": "Full Crystal (Static)",
        "description": "Crystal סטטי מוכן מראש - לבדיקת עיצוב לשונית המהות בלי להמתין ל-LLM.",
        "expected_cards": [],  # No cards - Crystal is holistic, user-initiated from Space
        "next_action": "פתחו את לשונית 'מהות' בממשק וראו את כל הנתונים",
    },
    "dynamic_crystal": {
        "name": "Dynamic Crystal (LLM Generated)",
        "description": "נתונים עשירים ללא Crystal - כשנפתח הפורטרט, ה-LLM יצור Crystal דינמי עם תובנות, מה יכול לעזור, והמלצות.",
        "expected_cards": ["video_suggestion"],
        "next_action": "פתחו את הפורטרט - ה-Crystal ייווצר דינמית ע\"י ה-LLM",
    },
}


def build_gestalt_seed_data(scenario: str, child_name: str = "דניאל") -> dict:
    """
    Build realistic gestalt data for a scenario.

    Returns data in the format expected by Darshan.from_child_data()
    """
    from datetime import datetime, timedelta

    # Base understanding - common to all scenarios
    base_understanding = {
        "facts": [
            {"content": f"{child_name} בן 3.5", "domain": "identity", "confidence": 1.0, "source": "conversation", "t_created": datetime.now().isoformat()},
            {"content": "מתקשה במעברים בין פעילויות", "domain": "behavioral", "confidence": 0.9, "source": "conversation", "t_created": datetime.now().isoformat()},
            {"content": "רגיש לרעשים חזקים", "domain": "sensory", "confidence": 0.85, "source": "conversation", "t_created": datetime.now().isoformat()},
            {"content": "אוהב מוזיקה ויכול לשיר שירים שלמים", "domain": "strengths", "confidence": 0.95, "source": "conversation", "t_created": datetime.now().isoformat()},
            {"content": "יצירתי מאוד בציור ובנייה עם קוביות", "domain": "strengths", "confidence": 0.9, "source": "conversation", "t_created": datetime.now().isoformat()},
            {"content": "יש אחות גדולה בת 6", "domain": "family", "confidence": 1.0, "source": "conversation", "t_created": datetime.now().isoformat()},
        ],
        "essence": {
            "narrative": f"{child_name} הוא ילד סקרן ויצירתי שאוהב מוזיקה ובנייה. הוא רגיש לסביבה שלו ומגיב בעוצמה לשינויים.",
            "temperament": ["רגיש", "יצירתי", "עיקש"],
            "core_qualities": ["סקרנות", "התמדה", "דמיון עשיר"]
        },
        "patterns": []
    }

    # Base stories
    base_stories = [
        {
            "summary": f"אתמול {child_name} התפרץ כשצריך היה לצאת מהבית לגן. לקח 20 דקות להרגיע אותו.",
            "reveals": ["קושי במעברים", "קושי בוויסות רגשי"],
            "domains": ["behavioral", "emotional"],
            "significance": 0.8,
            "timestamp": datetime.now().isoformat()
        },
        {
            "summary": f"בשבת {child_name} בנה מגדל מקוביות - הגבוה ביותר שבנה! היה גאה מאוד.",
            "reveals": ["יכולת מוטורית עדינה", "התמדה", "גאווה בהישגים"],
            "domains": ["motor", "emotional", "cognitive"],
            "significance": 0.7,
            "timestamp": datetime.now().isoformat()
        },
        {
            "summary": f"בגן המטפלת אמרה ש-{child_name} לא מצטרף לחוג יחד עם הילדים האחרים. הוא יושב בצד ומשחק לבד.",
            "reveals": ["קושי חברתי", "העדפה למשחק עצמאי"],
            "domains": ["social"],
            "significance": 0.75,
            "timestamp": datetime.now().isoformat()
        }
    ]

    # Base journal - with entry_type for גילויים view
    base_journal = [
        {
            "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
            "summary": f"התחלנו את המסע עם {child_name}",
            "learned": ["מתחילים להכיר"],
            "significance": "notable",
            "entry_type": "session_started"
        },
        {
            "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
            "summary": "קשה לו לעבור מפעילות לפעילות",
            "learned": ["מתקשה עם רעשים חזקים", "צריך זמן להתכונן לשינויים"],
            "significance": "notable",
            "entry_type": "story_captured"
        },
        {
            "timestamp": (datetime.now() - timedelta(hours=12)).isoformat(),
            "summary": "האם השינויים קשים בגלל שהם מפתיעים אותו?",
            "learned": ["תחום: רגשי"],
            "significance": "notable",
            "entry_type": "exploration_started"
        },
        {
            "timestamp": datetime.now().isoformat(),
            "summary": "אוהב מוזיקה ובנייה",
            "learned": ["שר שירים שלמים", "בונה מגדלים גבוהים מקוביות"],
            "significance": "routine",
            "entry_type": "story_captured"
        },
    ]

    # Session history - realistic conversation
    base_session_history = [
        {"role": "assistant", "content": f"שלום! נעים להכיר. ספרי לי קצת על {child_name}."},
        {"role": "user", "content": f"{child_name} בן 3.5. הוא מאוד רגיש לרעשים וקשה לו עם מעברים."},
        {"role": "assistant", "content": "תודה שאת משתפת. מה קורה כשיש מעברים?"},
        {"role": "user", "content": "הוא מתפרץ, בוכה, לפעמים לוקח 20 דקות להרגיע אותו. אתמול בבוקר היה קשה מאוד."},
        {"role": "assistant", "content": "זה נשמע מאתגר. ספרי לי גם על החוזקות שלו - במה הוא נהנה?"},
        {"role": "user", "content": "הוא אוהב מוזיקה! יכול לשיר שירים שלמים. גם בונה מגדלים מדהימים מקוביות."},
        {"role": "assistant", "content": "איזה יופי. האם יש עוד ילדים במשפחה?"},
        {"role": "user", "content": "כן, יש לו אחות גדולה בת 6. הם משחקים יחד לפעמים אבל גם רבים הרבה."},
    ]

    # Scenario-specific exploration cycles
    scenarios_data = {
        "video_suggestion": {
            "exploration_cycles": [{
                "id": "cycle_transitions",
                "curiosity_type": "hypothesis",
                "focus": "קושי במעברים",
                "focus_domain": "behavioral",
                "status": "active",
                "theory": "יכול להיות שמעברים קשים לו כי השינוי מרגיש גדול ומאיים",
                "confidence": 0.5,
                "video_appropriate": True,
                "video_accepted": False,
                "video_declined": False,
                "video_suggested_at": None,
                "video_scenarios": [],
                "evidence": [
                    {"content": "מתפרץ כשצריך לצאת מהבית", "effect": "supports", "source": "conversation", "timestamp": datetime.now().isoformat()},
                    {"content": "רגיש לרעשים חזקים", "effect": "supports", "source": "conversation", "timestamp": datetime.now().isoformat()},
                ],
                "created_at": datetime.now().isoformat(),
            }]
        },
        "video_accepted": {
            "exploration_cycles": [{
                "id": "cycle_transitions",
                "curiosity_type": "hypothesis",
                "focus": "קושי במעברים",
                "focus_domain": "behavioral",
                "status": "active",
                "theory": "נראה שמעברים מרגישים לו גדולים - אולי בגלל איך שהוא קולט את הסביבה",
                "confidence": 0.5,
                "video_appropriate": True,
                "video_accepted": True,
                "video_declined": False,
                "video_suggested_at": datetime.now().isoformat(),
                "video_scenarios": [{
                    "id": "scenario_morning",
                    "title": "מעבר בוקר - יציאה לגן",
                    "what_to_film": f"צלמו את {child_name} בבוקר כשצריך לצאת מהבית. התחילו כמה דקות לפני שאומרים לו שזמן לצאת.",
                    "rationale_for_parent": f"זה יעזור לי לראות איך {child_name} מגיב לשינויים ואיזה סימנים מקדימים יש לפני ההתפרצות.",
                    "duration_suggestion": "5-7 דקות",
                    "example_situations": ["יציאה לגן בבוקר", "חזרה מהפארק", "סיום משחק אהוב"],
                    "target_hypothesis_id": "cycle_transitions",
                    "what_we_hope_to_learn": "לזהות את הטריגרים הספציפיים ואת רצף התגובות",
                    "focus_points": ["מה קורה ברגע שאומרים 'יוצאים'", "האם יש סימנים מקדימים", "מה עוזר להרגיע"],
                    "category": "hypothesis_test",
                    "status": "pending",
                    "created_at": (datetime.now() - timedelta(days=2)).isoformat(),  # Simulate guidelines generated 2 days ago
                    "reminder_dismissed": False,
                }],
                "evidence": [
                    {"content": "מתפרץ כשצריך לצאת מהבית", "effect": "supports", "source": "conversation", "timestamp": datetime.now().isoformat()},
                ],
                "created_at": datetime.now().isoformat(),
            }]
        },
        "video_uploaded": {
            "exploration_cycles": [{
                "id": "cycle_transitions",
                "curiosity_type": "hypothesis",
                "focus": "קושי במעברים",
                "focus_domain": "behavioral",
                "status": "active",
                "theory": "נראה שמעברים מרגישים לו גדולים - אולי בגלל איך שהוא קולט את הסביבה",
                "confidence": 0.5,
                "video_appropriate": True,
                "video_accepted": True,
                "video_declined": False,
                "video_scenarios": [{
                    "id": "scenario_morning",
                    "title": "מעבר בוקר - יציאה לגן",
                    "what_to_film": f"צלמו את {child_name} בבוקר כשצריך לצאת מהבית.",
                    "rationale_for_parent": "זה יעזור לי לראות איך הוא מגיב לשינויים.",
                    "duration_suggestion": "5-7 דקות",
                    "target_hypothesis_id": "cycle_transitions",
                    "what_we_hope_to_learn": "לזהות את הטריגרים",
                    "focus_points": ["טריגרים", "התנהגות", "מה עוזר"],
                    "category": "hypothesis_test",
                    "status": "uploaded",
                    "video_path": "/uploads/mock_video.mp4",
                    "uploaded_at": datetime.now().isoformat(),
                }],
                "evidence": [
                    {"content": "מתפרץ כשצריך לצאת מהבית", "effect": "supports", "source": "conversation", "timestamp": datetime.now().isoformat()},
                ],
                "created_at": datetime.now().isoformat(),
            }]
        },
        "video_analyzed": {
            "exploration_cycles": [{
                "id": "cycle_transitions",
                "curiosity_type": "hypothesis",
                "focus": "קושי במעברים",
                "focus_domain": "behavioral",
                "status": "active",
                "theory": "נראה שמעברים מרגישים לו גדולים - אולי בגלל איך שהוא קולט את הסביבה",
                "confidence": 0.75,  # Increased after analysis
                "video_appropriate": True,
                "video_accepted": True,
                "video_declined": False,
                "video_scenarios": [{
                    "id": "scenario_morning",
                    "title": "מעבר בוקר - יציאה לגן",
                    "what_to_film": f"צלמו את {child_name} בבוקר כשצריך לצאת מהבית.",
                    "rationale_for_parent": "זה יעזור לי לראות איך הוא מגיב לשינויים.",
                    "duration_suggestion": "5-7 דקות",
                    "target_hypothesis_id": "cycle_transitions",
                    "status": "analyzed",
                    "video_path": "/uploads/mock_video.mp4",
                    "uploaded_at": (datetime.now() - timedelta(hours=1)).isoformat(),
                    "analyzed_at": datetime.now().isoformat(),
                    "analysis_result": {
                        "verdict": "supports",
                        "confidence_level": "high",
                        "insights_for_parent": [
                            f"{child_name} מראה סימני מצוקה כבר כשמתחילים לדבר על יציאה",
                            "הוא מחפש את הצעצוע האהוב שלו לפני שמוכן לצאת",
                            "כשנותנים לו זמן - הוא נרגע יותר מהר",
                        ],
                        "strengths_observed": [
                            f"{child_name} מסוגל להירגע בעזרת המוזיקה האהובה",
                            "הוא משתף פעולה כשמבינים את הקצב שלו",
                        ],
                        "hypothesis_evidence": "הסרטון מראה בבירור שהרגישות החושית משחקת תפקיד - הילד מכסה את האוזניים כשהדלת נפתחת",
                    },
                }],
                "evidence": [
                    {"content": "מתפרץ כשצריך לצאת מהבית", "effect": "supports", "source": "conversation", "timestamp": datetime.now().isoformat()},
                    {"content": "בסרטון נראה שמכסה אוזניים כשפותחים דלת", "effect": "supports", "source": "video", "timestamp": datetime.now().isoformat()},
                ],
                "created_at": datetime.now().isoformat(),
            }]
        },
        "multi_hypothesis": {
            "exploration_cycles": [
                {
                    "id": "cycle_transitions",
                    "curiosity_type": "hypothesis",
                    "focus": "קושי במעברים",
                    "focus_domain": "behavioral",
                    "status": "active",
                    "theory": "נראה שמעברים מרגישים לו גדולים - אולי בגלל איך שהוא קולט את הסביבה",
                    "confidence": 0.5,
                    "video_appropriate": True,
                    "video_accepted": False,
                    "video_declined": False,
                    "video_scenarios": [],
                    "evidence": [
                        {"content": "מתפרץ כשצריך לצאת מהבית", "effect": "supports", "source": "conversation", "timestamp": datetime.now().isoformat()},
                    ],
                    "created_at": datetime.now().isoformat(),
                },
                {
                    "id": "cycle_social",
                    "curiosity_type": "question",
                    "focus": "משחק עצמאי",
                    "focus_domain": "social",
                    "status": "active",
                    "question": f"האם {child_name} מעדיף לשחק לבד מבחירה או שיש קושי חברתי?",
                    "answer_fragments": ["לפי המטפלת הוא יושב בצד בחוגים", "בבית משחק עם אחותו לפעמים"],
                    "evidence": [
                        {"content": "בגן יושב בצד במקום להצטרף לחוג", "effect": "supports", "source": "conversation", "timestamp": datetime.now().isoformat()},
                    ],
                    "created_at": datetime.now().isoformat(),
                },
            ]
        },
        "synthesis_ready": {
            "exploration_cycles": [
                {
                    "id": "cycle_transitions",
                    "curiosity_type": "hypothesis",
                    "focus": "קושי במעברים",
                    "focus_domain": "behavioral",
                    "status": "complete",
                    "theory": "נראה שמעברים מרגישים לו גדולים - אולי בגלל איך שהוא קולט את הסביבה",
                    "confidence": 0.85,
                    "video_appropriate": True,
                    "video_accepted": True,
                    "video_scenarios": [{
                        "id": "scenario_morning",
                        "status": "analyzed",
                        "analysis_result": {"verdict": "supports", "confidence_level": "high"},
                    }],
                    "evidence": [
                        {"content": "מתפרץ כשצריך לצאת", "effect": "supports", "source": "conversation", "timestamp": datetime.now().isoformat()},
                        {"content": "מכסה אוזניים בסרטון", "effect": "supports", "source": "video", "timestamp": datetime.now().isoformat()},
                    ],
                    "created_at": (datetime.now() - timedelta(days=2)).isoformat(),
                },
                {
                    "id": "cycle_social",
                    "curiosity_type": "question",
                    "focus": "משחק חברתי",
                    "focus_domain": "social",
                    "status": "complete",
                    "question": "האם יש קושי חברתי?",
                    "answer_fragments": ["מעדיף משחק עצמאי", "יש יכולת לשחק עם אחותו"],
                    "evidence": [
                        {"content": "משחק לבד בגן", "effect": "supports", "source": "conversation", "timestamp": datetime.now().isoformat()},
                    ],
                    "created_at": (datetime.now() - timedelta(days=1)).isoformat(),
                },
            ]
        },
        "rich_conversation": {
            "exploration_cycles": [{
                "id": "cycle_transitions",
                "curiosity_type": "hypothesis",
                "focus": "קושי במעברים",
                "focus_domain": "behavioral",
                "status": "active",
                "theory": "יכול להיות שמעברים קשים לו כי השינוי מרגיש גדול ומאיים",
                "confidence": 0.6,
                "video_appropriate": True,
                "video_accepted": False,
                "video_declined": False,
                "video_scenarios": [],
                "evidence": [
                    {"content": "מתפרץ כשצריך לצאת מהבית", "effect": "supports", "source": "conversation", "timestamp": datetime.now().isoformat()},
                    {"content": "רגיש לרעשים חזקים", "effect": "supports", "source": "conversation", "timestamp": datetime.now().isoformat()},
                    {"content": "לוקח זמן להירגע אחרי שינוי", "effect": "supports", "source": "conversation", "timestamp": datetime.now().isoformat()},
                ],
                "created_at": datetime.now().isoformat(),
            }]
        },
        # dynamic_crystal: Rich data for LLM to generate Crystal dynamically (NO pre-built crystal)
        "dynamic_crystal": {
            "exploration_cycles": [{
                "id": "cycle_transitions",
                "curiosity_type": "hypothesis",
                "focus": "קושי במעברים",
                "focus_domain": "behavioral",
                "status": "active",
                "theory": "יכול להיות שמעברים קשים לו כי השינוי מרגיש גדול ומאיים",
                "confidence": 0.6,
                "video_appropriate": True,
                "video_accepted": False,
                "video_declined": False,
                "video_scenarios": [],
                "evidence": [
                    {"content": "מתפרץ כשצריך לצאת מהבית", "effect": "supports", "source": "conversation", "timestamp": datetime.now().isoformat()},
                    {"content": "רגיש לרעשים חזקים", "effect": "supports", "source": "conversation", "timestamp": datetime.now().isoformat()},
                    {"content": "לוקח זמן להירגע אחרי שינוי", "effect": "supports", "source": "conversation", "timestamp": datetime.now().isoformat()},
                ],
                "created_at": datetime.now().isoformat(),
            }]
        },
        # with_crystal: same exploration cycles as synthesis_ready, crystal added separately below
        "with_crystal": {
            "exploration_cycles": [
                {
                    "id": "cycle_transitions",
                    "curiosity_type": "hypothesis",
                    "focus": "קושי במעברים",
                    "focus_domain": "behavioral",
                    "status": "complete",
                    "theory": "נראה שמעברים מרגישים לו גדולים - אולי בגלל איך שהוא קולט את הסביבה",
                    "confidence": 0.85,
                    "video_appropriate": True,
                    "video_accepted": True,
                    "video_scenarios": [{
                        "id": "scenario_morning",
                        "title": "מעבר בוקר - יציאה לגן",
                        "what_to_film": f"צלמו את {child_name} בבוקר כשצריך לצאת מהבית.",
                        "rationale_for_parent": "זה יעזור לראות איך הוא מגיב לשינויים.",
                        "duration_suggestion": "5-7 דקות",
                        "target_hypothesis_id": "cycle_transitions",
                        "status": "analyzed",
                        "video_path": "/uploads/mock_video.mp4",
                        "uploaded_at": (datetime.now() - timedelta(hours=1)).isoformat(),
                        "analyzed_at": datetime.now().isoformat(),
                        "analysis_result": {"verdict": "supports", "confidence_level": "high"},
                    }],
                    "evidence": [
                        {"content": "מתפרץ כשצריך לצאת", "effect": "supports", "source": "conversation", "timestamp": datetime.now().isoformat()},
                        {"content": "מכסה אוזניים בסרטון", "effect": "supports", "source": "video", "timestamp": datetime.now().isoformat()},
                    ],
                    "created_at": (datetime.now() - timedelta(days=2)).isoformat(),
                },
                {
                    "id": "cycle_social",
                    "curiosity_type": "question",
                    "focus": "משחק חברתי",
                    "focus_domain": "social",
                    "status": "complete",
                    "question": "האם יש קושי חברתי?",
                    "answer_fragments": ["מעדיף משחק עצמאי", "יש יכולת לשחק עם אחותו"],
                    "evidence": [
                        {"content": "משחק לבד בגן", "effect": "supports", "source": "conversation", "timestamp": datetime.now().isoformat()},
                    ],
                    "created_at": (datetime.now() - timedelta(days=1)).isoformat(),
                },
            ]
        },
    }

    # Additional rich facts for rich_conversation and dynamic_crystal
    if scenario in ("rich_conversation", "dynamic_crystal"):
        base_understanding["facts"].extend([
            {"content": "אוהב צעצועים שמסתובבים", "domain": "play", "confidence": 0.9, "source": "conversation", "t_created": datetime.now().isoformat()},
            {"content": "לא אוהב להתלכלך בחול", "domain": "sensory", "confidence": 0.85, "source": "conversation", "t_created": datetime.now().isoformat()},
            {"content": "יודע את כל השירים מסרטון אהוב", "domain": "cognitive", "confidence": 0.95, "source": "conversation", "t_created": datetime.now().isoformat()},
            {"content": "ישן טוב בלילה, 10-12 שעות", "domain": "daily_routines", "confidence": 1.0, "source": "conversation", "t_created": datetime.now().isoformat()},
            {"content": "אוכל מבחר מצומצם של מאכלים", "domain": "sensory", "confidence": 0.8, "source": "conversation", "t_created": datetime.now().isoformat()},
        ])
        base_session_history.extend([
            {"role": "assistant", "content": "מעניין. ספרי לי עוד על המשחק שלו."},
            {"role": "user", "content": "הוא אוהב צעצועים שמסתובבים, יכול לשחק איתם שעות. גם את הגלגלים של המכוניות הוא מסובב."},
            {"role": "assistant", "content": "ומה לגבי משחק בחוץ?"},
            {"role": "user", "content": "הוא לא אוהב ארגז חול, מפריע לו להתלכלך. בפארק הוא משחק בעיקר על הנדנדה."},
            {"role": "assistant", "content": "איך הוא עם אוכל?"},
            {"role": "user", "content": "אוכל רק כמה דברים ספציפיים - פסטה, במבה, בננה. קשה להכניס דברים חדשים."},
        ])

    # Build result with base data
    result = {
        "name": child_name,
        "understanding": base_understanding,
        "stories": base_stories,
        "journal": base_journal,
        "session_history": base_session_history,
        **scenarios_data.get(scenario, {}),
    }

    # Add Crystal for scenarios that should have it
    # NOTE: dynamic_crystal is NOT here - it uses LLM to generate Crystal dynamically
    if scenario in ["with_crystal", "synthesis_ready"]:
        result["crystal"] = {
            "essence_narrative": f"{child_name} הוא ילד בעל עולם פנימי עשיר, שאוהב ליצור ולבנות. הרגישות החושית שלו היא גם חוזקה - היא מאפשרת לו להתרכז לעומק בדברים שמעניינים אותו. הוא זקוק לזמן להתאקלם לשינויים, אבל כשנותנים לו את המרחב הזה, הוא מפתיע ביכולת ההסתגלות שלו.",
            "temperament": ["רגיש", "יצירתי", "עיקש", "מתבונן"],
            "core_qualities": ["סקרנות עמוקה", "התמדה", "דמיון עשיר", "יכולת ריכוז גבוהה"],
            "patterns": [
                {
                    "description": f"המוזיקה היא ערוץ ויסות מרכזי עבור {child_name} - הוא נרגע ומתחבר דרכה",
                    "domains_involved": ["emotional", "sensory", "strengths"],
                    "confidence": 0.85,
                    "detected_at": datetime.now().isoformat(),
                },
                {
                    "description": "כשצריך לעבור לפעילות אחרת, הוא צריך הרבה זמן להתארגן - נראה שהשינוי מרגיש לו גדול",
                    "domains_involved": ["sensory", "behavioral", "emotional"],
                    "confidence": 0.8,
                    "detected_at": datetime.now().isoformat(),
                },
                {
                    "description": "הבנייה והיצירה הם דרך להביע את עצמו ולהרגיש שליטה",
                    "domains_involved": ["cognitive", "emotional", "motor"],
                    "confidence": 0.75,
                    "detected_at": datetime.now().isoformat(),
                },
            ],
            "intervention_pathways": [
                {
                    "hook": "אהבת המוזיקה והיכולת לשיר שירים שלמים",
                    "concern": "קושי במעברים",
                    "suggestion": f"לנגן שיר מוכר לפני מעברים - ליצור 'שיר מעברים' ש{child_name} יידע שמסמן שינוי קרב",
                    "confidence": 0.8,
                },
                {
                    "hook": "הנאה מבנייה עם קוביות",
                    "concern": "קושי בביטוי מילולי",
                    "suggestion": f"לבנות יחד ולדבר על מה שבונים - 'איזה צבע?' 'עוד אחד?' - ליצור הזדמנויות לתקשורת דרך משחק אהוב",
                    "confidence": 0.75,
                },
                {
                    "hook": "יכולת ריכוז גבוהה בפעילויות מעניינות",
                    "concern": "רגישות חושית",
                    "suggestion": f"להשתמש בפעילויות מרוכזות (לגו, ציור) כ'עוגן' לפני ואחרי מצבים מאתגרים חושית",
                    "confidence": 0.7,
                },
            ],
            "open_questions": [
                f"האם {child_name} מגיב אחרת למעברים כשהוא יודע מראש מה יקרה?",
                "האם יש הבדל בין מעברים בבית לבין מעברים בגן?",
                f"איך {child_name} מגיב לילדים אחרים שמנסים להצטרף למשחק שלו?",
            ],
            "expert_recommendations": [
                {
                    "profession": "מרפא בעיסוק",
                    "specialization": f"מרפא שעובד דרך בנייה ויצירה, מכיר עולם הלגו והמשחק הקונסטרוקטיבי",
                    "why_this_match": f"{child_name} בונה לשעות ונרגע כשהידיים עסוקות - מרפא שיעבוד איתו דרך בנייה יגיע אליו דרך מה שהוא אוהב, לא דרך מה שקשה לו",
                    "recommended_approach": "גישה משחקית דרך בנייה ויצירה",
                    "why_this_approach": f"כי {child_name} מתחבר דרך הידיים והעיניים, לא דרך הוראות מילוליות",
                    "what_to_look_for": [
                        "מרפא שיש לו קוביות ולגו בחדר הטיפולים",
                        "מישהו שנותן לילד להוביל את המשחק",
                        "גישה רגועה וסבלנית, בלי לחץ להתקדם מהר",
                    ],
                    "summary_for_professional": f"{child_name} הוא ילד בן 3.5, יצירתי ובעל דמיון עשיר. הוא בונה מגדלים מורכבים ויכול להתרכז בבנייה לזמן ארוך. יש לו רגישות חושית, במיוחד לרעשים, וקושי במעברים. הדרך להגיע אליו היא דרך הידיים - בנייה, יצירה, משחק בחומרים. המוזיקה גם מרגיעה אותו. הוא צריך זמן להתאקלם לסביבה חדשה ולאנשים חדשים.",
                    "confidence": 0.75,
                    "priority": "when_ready",
                },
                {
                    "profession": "קלינאית תקשורת",
                    "specialization": "קלינאית שמשלבת מוזיקה ושירה בטיפול, או עם רקע במוזיקה תרפיה",
                    "why_this_match": f"{child_name} שר שירים שלמים אבל מתקשה בדיבור רגיל - קלינאית שתעבוד דרך השירה תוכל להשתמש בחוזקה הזו כגשר לתקשורת",
                    "recommended_approach": "גישה מבוססת משחק ומוזיקה",
                    "why_this_approach": f"כי {child_name} כבר מצליח להוציא מילים דרך שירה - זה הערוץ הפתוח שלו",
                    "what_to_look_for": [
                        "קלינאית שמשתמשת בשירים ומוזיקה כחלק מהטיפול",
                        "גישה משחקית, לא 'תרגולית'",
                        "מישהי שנותנת לילד להוביל ולא דוחפת",
                    ],
                    "summary_for_professional": f"{child_name} הוא ילד בן 3.5 שמתקשה בביטוי מילולי אבל שר שירים שלמים בצורה מדויקת. הוא מבין הרבה יותר ממה שהוא מביע. הוא רגיש חושית ומתחבר דרך מוזיקה ובנייה. הגישה המשחקית והמוזיקלית היא המפתח להגיע אליו. הוא זקוק לזמן להתחמם לאנשים חדשים.",
                    "confidence": 0.7,
                    "priority": "soon",
                },
            ],
            "portrait_sections": [
                {
                    "title": "העולם הפנימי והיצירה",
                    "icon": "🧩",
                    "content": f"{child_name} הוא ילד עם עולם פנימי עשיר ודמיון מפותח. הוא מבטא את עצמו בעיקר דרך בנייה ויצירה - יכול לבנות מגדלים מרשימים ולהתרכז בזה לזמן ארוך. המוזיקה היא חלק בלתי נפרד ממנו, והוא שר שירים שלמים בהנאה גלויה.",
                    "content_type": "paragraph",
                },
                {
                    "title": "התמודדות עם שינויים",
                    "icon": "⏳",
                    "content": f"מעברים בין פעילויות מהווים אתגר עבור {child_name}. הוא צריך זמן להתכונן לשינויים, ואת הזמן הזה כדאי לתת לו. כשמכינים אותו מראש ונותנים לו להיפרד בקצב שלו, המעברים הרבה יותר קלים.",
                    "content_type": "paragraph",
                },
                {
                    "title": "הסביבה האופטימלית עבורו",
                    "icon": "🌱",
                    "content": f"• סביבה שקטה יחסית, בלי רעשים פתאומיים\n• הכנה מראש לפני שינויים ('עוד 5 דקות נצא')\n• מוזיקה כגשר - שיר מעברים יכול לעזור מאוד\n• זמן לבנות וליצור - זה מרגיע ומעצים אותו",
                    "content_type": "bullets",
                },
            ],
            "created_at": (datetime.now() - timedelta(hours=2)).isoformat(),
            "based_on_observations_through": datetime.now().isoformat(),
            "version": 1,
        }

    return result


@router.get("/seed/gestalt/scenarios")
async def list_gestalt_scenarios():
    """
    🧪 List all available Darshan seeding scenarios

    Each scenario seeds a specific state in the video exploration flow,
    allowing manual testing from any point in the workflow.
    """
    return {
        "scenarios": [
            {
                "id": scenario_id,
                **scenario_info,
                "seed_url": f"/api/dev/seed/gestalt/{scenario_id}",
            }
            for scenario_id, scenario_info in GESTALT_SCENARIOS.items()
        ],
        "usage": {
            "example": "POST /api/dev/seed/gestalt/video_suggestion?child_name=דניאל",
            "then": "Open http://localhost:5173/?family={returned_family_id}",
        }
    }


@router.post("/seed/gestalt/{scenario}")
async def seed_gestalt_scenario(
    scenario: str,
    family_id: str = None,
    child_name: str = "דניאל"
):
    """
    🧪 Seed a Darshan scenario for manual testing

    This creates a family with the specified state in the video exploration flow,
    allowing you to manually test from any point without going through the full conversation.

    Scenarios:
    - video_suggestion: Hypothesis ready for video, awaiting consent
    - video_accepted: Guidelines generated, ready for upload
    - video_uploaded: Video uploaded, ready for analysis
    - video_analyzed: Analysis complete, insights available
    - multi_hypothesis: Multiple active explorations
    - synthesis_ready: Ready for synthesis (includes Crystal)
    - rich_conversation: Rich data for testing responses
    - with_crystal: Full Crystal with patterns, pathways, and expert recommendations

    Returns:
    - family_id: Use this in the URL to open the app
    - expected_cards: What cards should appear
    - next_action: What to do next to continue testing
    - url: Direct link to open the app with this family
    """
    import time

    if scenario not in GESTALT_SCENARIOS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown scenario: {scenario}. Available: {list(GESTALT_SCENARIOS.keys())}"
        )

    # Generate family_id if not provided
    if not family_id:
        family_id = f"seed_{scenario}_{int(time.time())}"

    logger.info(f"🌱 Seeding Living Gestalt scenario '{scenario}' for family '{family_id}'")

    # Build seed data
    seed_data = build_gestalt_seed_data(scenario, child_name)

    # Persist to database via DarshanRepository
    from app.db.repositories import UnitOfWork
    async with UnitOfWork() as uow:
        await uow.darshan.save_darshan_data(family_id, seed_data)
        await uow.commit()
        logger.info(f"✅ Saved gestalt data to database for {family_id}")

    # Get the derived cards to verify the scenario works
    try:
        from app.chitta import get_chitta_service
        chitta_service = get_chitta_service()

        # Clear cache to ensure fresh load
        if family_id in chitta_service._gestalts:
            del chitta_service._gestalts[family_id]

        gestalt = await chitta_service.get_gestalt(family_id)
        derived_cards = chitta_service._cards_service.derive_cards(gestalt) if gestalt else []
    except Exception as e:
        logger.warning(f"Could not derive cards: {e}")
        derived_cards = []

    scenario_info = GESTALT_SCENARIOS[scenario]

    return {
        "status": "seeded",
        "family_id": family_id,
        "scenario": scenario,
        "scenario_info": scenario_info,
        "child_name": child_name,
        "derived_cards": derived_cards,
        "expected_cards": scenario_info["expected_cards"],
        "next_action": scenario_info["next_action"],
        "url": f"http://localhost:5173/?family={family_id}",
        "data_summary": {
            "facts_count": len(seed_data.get("understanding", {}).get("facts", [])),
            "stories_count": len(seed_data.get("stories", [])),
            "curiosities_count": len(seed_data.get("curiosities", {}).get("dynamic", [])),
            "session_history_count": len(seed_data.get("session_history", [])),
        }
    }


@router.delete("/seed/gestalt/{child_id}")
async def delete_gestalt_seed(child_id: str):
    """
    🧪 Delete a seeded gestalt for a child

    Removes from database and clears any cached state.
    """
    # Delete from database
    from app.db.repositories import UnitOfWork
    try:
        async with UnitOfWork() as uow:
            await uow.darshan.delete_darshan_data(child_id)
            await uow.commit()
            logger.info(f"🗑️ Deleted gestalt data from database for {child_id}")
    except Exception as e:
        logger.warning(f"Could not delete from database: {e}")

    # Clear from cache if service is loaded
    try:
        from app.chitta import get_chitta_service
        chitta_service = get_chitta_service()
        if child_id in chitta_service._gestalts:
            del chitta_service._gestalts[child_id]
    except:
        pass

    return {
        "status": "deleted",
        "child_id": child_id,
    }
