"""
Development-only routes for testing and debugging

Key endpoints:
- /dev/xray/personas - List available parent personas for testing
- /dev/xray/run/{persona} - Run dynamic X-Ray test with simulated parent
- /dev/xray/reports - List all X-Ray reports
- /dev/xray/html/{filename} - View HTML dashboard for a report
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse
from typing import Literal, Optional
import logging
import os
import json
import subprocess
import asyncio
import sys
from pathlib import Path
from datetime import datetime

from app.services.session_service import get_session_service
from app.services.lifecycle_manager import get_lifecycle_manager
from app.services.prerequisite_service import get_prerequisite_service

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
    "video_with_hypothesis": {
        "description": "📹 Video observation test - parent struggling to describe, ACTIVE hypothesis exists",
        "data": {
            "child_name": "נועם",
            "age": 3.5,
            "gender": "male",
            "primary_concerns": ["speech", "sensory"],
            "concern_details": "נועם מתקשה עם מעברים ושינויים בשגרה. קשה לתאר מה בדיוק קורה, אבל משהו לא מסתדר.",
            "strengths": "נועם אוהב מאוד מוזיקה ויכול לשיר שירים שלמים. הוא גם מאוד יצירתי בציור.",
            "developmental_history": "התפתחות תקינה עד גיל שנתיים, אז התחיל להיות מאוד רגיש לרעשים.",
            "family_context": "משפחה דוברת עברית, יש אחות גדולה בת 6.",
            "daily_routines": "גן בבוקר עד 14:00, אחר כצהריים בבית.",
        },
        "completeness": 0.75,
        "message_count": 10,
        "seed_hypotheses": True,  # Special flag to seed hypotheses
        "hypotheses": [
            {
                "id": "hyp_sensory_transitions",
                "theory": "נועם רגיש במיוחד לשינויים סנסוריים, ולכן מעברים קשים לו",
                "domain": "sensory",
                "confidence": 0.7,
                "status": "active",  # CRITICAL - must be active for video tool
                "questions_to_explore": [
                    "האם הרגישות מופיעה גם במעברים שקטים?",
                    "האם הכנה מראש עוזרת?",
                    "אילו מעברים קשים יותר?"
                ],
                "evidence": [
                    {
                        "source": "conversation",
                        "content": "ההורה ציין שהילד מאוד רגיש לרעשים",
                        "domain": "sensory"
                    },
                    {
                        "source": "conversation",
                        "content": "מעברים בין פעילויות מאוד קשים",
                        "domain": "regulation"
                    }
                ]
            },
            {
                "id": "hyp_verbal_expression",
                "theory": "לנועם יש מה לומר אבל הוא מתקשה להוציא את המילים",
                "domain": "communication",
                "confidence": 0.5,
                "status": "forming",
                "questions_to_explore": [
                    "האם הוא מתקשר טוב יותר בשירה?",
                    "האם יש פער בין הבנה לביטוי?"
                ],
                "evidence": [
                    {
                        "source": "conversation",
                        "content": "יכול לשיר שירים שלמים אבל מתקשה בדיבור רגיל",
                        "domain": "communication"
                    }
                ]
            }
        ],
        "conversation_context": [
            ("user", "שלום, אני דואג לנועם בן 3.5"),
            ("assistant", "שלום, ספר/י לי על נועם"),
            ("user", "הוא מאוד רגיש לרעשים וקשה לו עם שינויים"),
            ("assistant", "מה קורה כשיש מעברים?"),
            ("user", "קשה לי להסביר... זה משהו שצריך לראות"),
        ]
    },
}


@router.post("/seed/{scenario}")
async def seed_test_scenario(
    scenario: Literal["early_conversation", "guidelines_ready", "videos_uploaded", "living_dashboard", "video_with_hypothesis"],
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

    # 📹 Video with Hypothesis: Seed hypotheses into Child.understanding
    if scenario_config.get("seed_hypotheses"):
        from app.models.understanding import Hypothesis, Evidence, DevelopmentalUnderstanding
        from app.services.unified_state_service import get_unified_state_service

        logger.info("📹 Seeding hypotheses for video observation test...")

        unified = get_unified_state_service()
        child = unified.get_child(family_id)

        # Seed hypotheses from scenario config
        for hyp_data in scenario_config.get("hypotheses", []):
            # Create evidence objects
            evidence_list = []
            for ev_data in hyp_data.get("evidence", []):
                evidence = Evidence(
                    source=ev_data.get("source", "conversation"),
                    content=ev_data.get("content", ""),
                    domain=ev_data.get("domain"),
                    observed_at=datetime.now()
                )
                evidence_list.append(evidence)

            # Create hypothesis with ACTIVE status
            hypothesis = Hypothesis(
                id=hyp_data.get("id", f"hyp_{len(child.understanding.hypotheses)}"),
                theory=hyp_data.get("theory", ""),
                domain=hyp_data.get("domain", "general"),
                confidence=hyp_data.get("confidence", 0.5),
                status=hyp_data.get("status", "active"),  # CRITICAL for video tool
                evidence=evidence_list,
                questions_to_explore=hyp_data.get("questions_to_explore", []),
                formed_at=datetime.now(),
                last_evidence_at=datetime.now()
            )
            child.understanding.add_hypothesis(hypothesis)
            logger.info(f"  ✅ Added hypothesis: {hypothesis.id} ({hypothesis.status})")

        # Use custom conversation context if provided
        if scenario_config.get("conversation_context"):
            for role, content in scenario_config["conversation_context"]:
                session.conversation_history.append({
                    "role": role,
                    "content": content,
                    "timestamp": datetime.now().isoformat()
                })
            logger.info(f"  ✅ Added {len(scenario_config['conversation_context'])} conversation turns")

        logger.info(f"✅ Seeded {len(child.understanding.hypotheses)} hypotheses for video observation test")

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


@router.get("/session/{family_id}/memory")
async def get_session_memory(family_id: str):
    """
    🔧 DEV ONLY: Get session conversation memory (for X-Ray debugging)

    Returns the distilled relationship memory from reflection service.
    This shows what Chitta has learned about the parent's communication style
    and the conversation patterns - the "slow brain" processing.
    """
    from app.services.unified_state_service import get_unified_state_service

    unified = get_unified_state_service()
    session = unified.get_or_create_session(family_id)

    return {
        "family_id": family_id,
        "memory": session.memory.model_dump(),
        "turn_count": session.turn_count,
        "last_reflection_turn": session.last_reflection_turn,
        "pending_reflection": session.pending_reflection,
        "needs_reflection": session.needs_reflection()
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


# ========================================
# 🧪 LIVING GESTALT SEEDING SYSTEM
# ========================================
# These endpoints seed data for the new Living Gestalt architecture
# allowing manual testing of video flow and exploration cycles

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
        "description": "ניתוח הושלם עם תובנות.",
        "expected_cards": ["video_insights"],
        "next_action": "צפו בתובנות, המשיכו בשיחה",
    },
    "multi_hypothesis": {
        "name": "Multiple Hypotheses",
        "description": "מספר השערות פעילות בשלבים שונים.",
        "expected_cards": ["video_suggestion", "synthesis_available"],
        "next_action": "בדקו טיפול במספר כרטיסים",
    },
    "synthesis_ready": {
        "name": "Synthesis Ready",
        "description": "מספיק מידע נאסף לדוח סינתזה.",
        "expected_cards": ["synthesis_available"],
        "next_action": "בקשו סינתזה",
    },
    "rich_conversation": {
        "name": "Rich Conversation History",
        "description": "שיחה עשירה עם הרבה עובדות, סיפורים והשערות - אידיאלי לבדיקת זיכרון ותגובות.",
        "expected_cards": ["video_suggestion"],
        "next_action": "שלחו הודעה וראו שהמערכת מכירה את הילד",
    },
}


def build_gestalt_seed_data(scenario: str, child_name: str = "דניאל") -> dict:
    """
    Build realistic gestalt data for a scenario.

    Returns data in the format expected by LivingGestalt.from_child_data()
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

    # Base journal
    base_journal = [
        {"timestamp": datetime.now().isoformat(), "summary": "התחלנו להכיר את המשפחה", "learned": ["קושי במעברים", "רגישות חושית"], "significance": "notable"},
        {"timestamp": datetime.now().isoformat(), "summary": "שמענו על החוזקות", "learned": ["מוזיקה", "בנייה", "יצירתיות"], "significance": "routine"},
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
                "theory": "הקושי במעברים נובע מרגישות חושית - שינוי הסביבה מציף את המערכת החושית",
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
                "theory": "הקושי במעברים נובע מרגישות חושית",
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
                "theory": "הקושי במעברים נובע מרגישות חושית",
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
                "theory": "הקושי במעברים נובע מרגישות חושית",
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
                    "theory": "הקושי במעברים נובע מרגישות חושית",
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
                    "theory": "הקושי במעברים נובע מרגישות חושית",
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
                "theory": "הקושי במעברים נובע מרגישות חושית ומקושי בוויסות עצמי",
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
    }

    # Additional rich facts for rich_conversation
    if scenario == "rich_conversation":
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

    return {
        "name": child_name,
        "understanding": base_understanding,
        "stories": base_stories,
        "journal": base_journal,
        "session_history": base_session_history,
        **scenarios_data.get(scenario, {}),
    }


@router.get("/seed/gestalt/scenarios")
async def list_gestalt_scenarios():
    """
    🧪 List all available Living Gestalt seeding scenarios

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
    🧪 Seed a Living Gestalt scenario for manual testing

    This creates a family with the specified state in the video exploration flow,
    allowing you to manually test from any point without going through the full conversation.

    Scenarios:
    - video_suggestion: Hypothesis ready for video, awaiting consent
    - video_accepted: Guidelines generated, ready for upload
    - video_uploaded: Video uploaded, ready for analysis
    - video_analyzed: Analysis complete, insights available
    - multi_hypothesis: Multiple active explorations
    - synthesis_ready: Ready for synthesis
    - rich_conversation: Rich data for testing responses

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

    # Persist to gestalt file
    gestalt_file = Path("data/children") / f"{family_id}.json"
    gestalt_file.parent.mkdir(parents=True, exist_ok=True)

    with open(gestalt_file, "w", encoding="utf-8") as f:
        json.dump(seed_data, f, ensure_ascii=False, indent=2, default=str)

    logger.info(f"✅ Saved gestalt data to {gestalt_file}")

    # Get the derived cards to verify the scenario works
    try:
        from app.chitta import get_chitta_service
        chitta_service = get_chitta_service()

        # Clear cache to ensure fresh load
        if family_id in chitta_service._gestalts:
            del chitta_service._gestalts[family_id]

        gestalt = await chitta_service._get_gestalt(family_id)
        derived_cards = chitta_service._derive_cards(gestalt) if gestalt else []
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
            "cycles_count": len(seed_data.get("exploration_cycles", [])),
            "session_history_count": len(seed_data.get("session_history", [])),
        }
    }


@router.delete("/seed/gestalt/{family_id}")
async def delete_gestalt_seed(family_id: str):
    """
    🧪 Delete a seeded gestalt family

    Removes both the gestalt file and clears any cached state.
    """
    gestalt_file = Path("data/children") / f"{family_id}.json"

    if gestalt_file.exists():
        gestalt_file.unlink()
        logger.info(f"🗑️ Deleted gestalt file: {gestalt_file}")

    # Clear from cache if service is loaded
    try:
        from app.chitta import get_chitta_service
        chitta_service = get_chitta_service()
        if family_id in chitta_service._gestalts:
            del chitta_service._gestalts[family_id]
    except:
        pass

    return {
        "status": "deleted",
        "family_id": family_id,
    }
