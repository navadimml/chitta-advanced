"""
Prerequisite Definitions

Defines what actions require what prerequisites (the "dependency graph").
This is NOT exposed to the user - it's backend logic that helps LLM
understand when actions are possible and guide users appropriately.
"""

from enum import Enum
from typing import Dict, List, Any


class Action(str, Enum):
    """Available actions in the system"""
    # Interview
    CONTINUE_INTERVIEW = "continue_interview"
    COMPLETE_INTERVIEW = "complete_interview"

    # Video
    VIEW_VIDEO_GUIDELINES = "view_video_guidelines"
    UPLOAD_VIDEO = "upload_video"
    ANALYZE_VIDEOS = "analyze_videos"

    # Reports
    VIEW_REPORT = "view_report"
    DOWNLOAD_REPORT = "download_report"

    # Experts
    FIND_EXPERTS = "find_experts"
    CONTACT_EXPERT = "contact_expert"

    # Sharing
    SHARE_REPORT = "share_report"

    # Always available
    CONSULTATION = "consultation"
    ADD_JOURNAL_ENTRY = "add_journal_entry"
    VIEW_JOURNAL = "view_journal"

    # System/Developer actions
    START_TEST_MODE = "start_test_mode"
    START_DEMO = "start_demo"


class PrerequisiteType(str, Enum):
    """Types of prerequisites"""
    INTERVIEW_COMPLETE = "interview_complete"
    VIDEOS_UPLOADED = "videos_uploaded"
    MINIMUM_VIDEOS = "minimum_videos"
    ANALYSIS_COMPLETE = "analysis_complete"
    REPORTS_AVAILABLE = "reports_available"


# === Prerequisite Graph ===
# This defines what each action requires

PREREQUISITES: Dict[Action, Dict[str, Any]] = {
    # Interview actions
    Action.CONTINUE_INTERVIEW: {
        "requires": [],
        "description": "Continue the interview - always available"
    },
    Action.COMPLETE_INTERVIEW: {
        "requires": [],  # LLM decides when enough data collected
        "description": "Complete interview when sufficient information gathered"
    },

    # Video guidelines and upload
    Action.VIEW_VIDEO_GUIDELINES: {
        "requires": [PrerequisiteType.INTERVIEW_COMPLETE],
        "description": "Interview must be completed to generate personalized video guidelines",
        "explanation_to_user": "כדי ליצור הנחיות צילום מותאמות אישית, אני צריכה קודם לסיים את הראיון. בואי נמשיך בשיחה - נשארו עוד כמה דברים שחשוב לי לדעת."
    },
    Action.UPLOAD_VIDEO: {
        "requires": [PrerequisiteType.INTERVIEW_COMPLETE],
        "description": "Interview must be completed before uploading videos",
        "explanation_to_user": "נהדר שאת מוכנה להעלות סרטונים! בואי נסיים קודם את הראיון, ואז אוכל ליצור עבורך הנחיות צילום מדויקות שמתאימות ל{child_name}."
    },

    # Video analysis
    Action.ANALYZE_VIDEOS: {
        "requires": [
            PrerequisiteType.INTERVIEW_COMPLETE,
            PrerequisiteType.VIDEOS_UPLOADED,
            PrerequisiteType.MINIMUM_VIDEOS
        ],
        "minimum_videos": 3,
        "description": "Need interview complete and at least 3 videos to analyze",
        "explanation_to_user": "כדי לנתח את הסרטונים, אני צריכה לפחות 3 סרטונים שמציגים את {child_name} במצבים שונים. עד כה יש {video_count} סרטונים. בואי נעלה עוד {remaining} סרטונים."
    },

    # Reports
    Action.VIEW_REPORT: {
        "requires": [PrerequisiteType.REPORTS_AVAILABLE],
        "description": "Reports must be generated (after video analysis)",
        "explanation_to_user": "הדוח עדיין בהכנה. אני מנתחת את הסרטונים של {child_name} ומכינה עבורך סיכום מקיף. זה לוקח קצת זמן - אני רוצה לתת לך מידע מדויק ושימושי. 💙"
    },
    Action.DOWNLOAD_REPORT: {
        "requires": [PrerequisiteType.REPORTS_AVAILABLE],
        "description": "Reports must be available to download"
    },

    # Experts
    Action.FIND_EXPERTS: {
        "requires": [],  # Can browse experts anytime
        "enhanced_by": [PrerequisiteType.REPORTS_AVAILABLE],
        "description": "Can browse experts anytime, but matching is better with completed reports",
        "explanation_to_user": "את יכולה לעיין במומחים כבר עכשיו. אבל אם נחכה עד שהדוח יהיה מוכן, אוכל להמליץ לך על מומחים שמתאימים בדיוק לצרכים של {child_name}."
    },
    Action.CONTACT_EXPERT: {
        "requires": [PrerequisiteType.REPORTS_AVAILABLE],
        "description": "Should have reports before contacting experts",
        "explanation_to_user": "מומלץ לחכות עד שהדוח יהיה מוכן לפני פניה למומחים. ככה יהיה להם כבר מידע מקדים ויוכלו לעזור לך טוב יותר."
    },

    # Sharing
    Action.SHARE_REPORT: {
        "requires": [PrerequisiteType.REPORTS_AVAILABLE],
        "description": "Must have reports to share",
        "explanation_to_user": "ברגע שהדוח יהיה מוכן, תוכלי לשתף אותו בצורה מאובטחת עם מומחים או בני משפחה."
    },

    # Always available
    Action.CONSULTATION: {
        "requires": [],
        "description": "Consultation mode available anytime - ask questions about child development, the process, etc."
    },
    Action.ADD_JOURNAL_ENTRY: {
        "requires": [],
        "description": "Journaling available anytime - document observations, progress, concerns"
    },
    Action.VIEW_JOURNAL: {
        "requires": [],
        "description": "View journal entries anytime"
    }
}


def get_action_prerequisites(action: Action) -> Dict[str, Any]:
    """
    Get prerequisite information for an action

    Returns:
        Dict with:
        - requires: List of PrerequisiteType
        - minimum_videos: Int (if applicable)
        - description: English description
        - explanation_to_user: Hebrew explanation to give user if blocked
        - enhanced_by: Optional list of prerequisites that enhance (but don't block) the action
    """
    return PREREQUISITES.get(action, {
        "requires": [],
        "description": "Unknown action"
    })


def get_prerequisite_explanation(
    action: Action,
    child_name: str = "הילד/ה",
    video_count: int = 0,
    required_videos: int = 3,
    interview_complete: bool = False,
    analysis_complete: bool = False,
    completeness: float = 0.0
) -> str:
    """
    Get context-aware Hebrew explanation for why action is not yet available

    Args:
        action: The action user wants to perform
        child_name: Child's name for personalization
        video_count: Number of videos uploaded
        required_videos: Number of videos required
        interview_complete: Whether interview is 80%+ complete
        analysis_complete: Whether video analysis is complete
        completeness: Interview completeness percentage (0.0 to 1.0)

    Returns:
        Hebrew explanation to give to user
    """
    # For VIEW_REPORT, provide context-aware explanation based on actual state
    if action == Action.VIEW_REPORT:
        return _get_view_report_explanation(
            child_name=child_name,
            video_count=video_count,
            required_videos=required_videos,
            interview_complete=interview_complete,
            analysis_complete=analysis_complete,
            completeness=completeness
        )

    # For UPLOAD_VIDEO and VIEW_VIDEO_GUIDELINES, check knowledge richness
    if action in [Action.UPLOAD_VIDEO, Action.VIEW_VIDEO_GUIDELINES]:
        if not interview_complete:
            return f"נהדר שאת מוכנה להמשיך! אני רוצה להכיר את {child_name} עוד קצת לפני שאכין הנחיות צילום מותאמות. בואי נמשיך בשיחה שלנו - יש עוד כמה דברים שיעזרו לי להבין טוב יותר."

    # For ANALYZE_VIDEOS, check what's missing
    if action == Action.ANALYZE_VIDEOS:
        if not interview_complete:
            return f"כדי לנתח סרטונים, אני קודם צריכה להכיר את {child_name} דרך השיחה שלנו. בואי נמשיך."
        elif video_count == 0:
            return f"כדי לנתח, אני צריכה שתעלי סרטונים של {child_name}. אני אכין לך הנחיות צילום כשתהיי מוכנה."
        elif video_count < required_videos:
            remaining = required_videos - video_count
            remaining_text = "סרטון אחד" if remaining == 1 else f"{remaining} סרטונים"
            video_count_text = "סרטון אחד" if video_count == 1 else f"{video_count} סרטונים"
            return f"כדי לנתח את הסרטונים, אני צריכה לפחות {required_videos} סרטונים שמציגים את {child_name} במצבים שונים. עד כה יש {video_count_text}. בואי נעלה עוד {remaining_text}."

    # For other actions, use static explanation with placeholder replacement
    prereq_info = get_action_prerequisites(action)
    explanation = prereq_info.get("explanation_to_user", "")

    # Replace placeholders
    remaining = max(0, required_videos - video_count)
    explanation = explanation.replace("{child_name}", child_name)
    explanation = explanation.replace("{video_count}", str(video_count))
    explanation = explanation.replace("{remaining}", str(remaining))

    return explanation


def _get_view_report_explanation(
    child_name: str,
    video_count: int,
    required_videos: int,
    interview_complete: bool,
    analysis_complete: bool,
    completeness: float
) -> str:
    """
    Get context-aware explanation for why VIEW_REPORT is not available

    This checks the actual state and provides appropriate guidance:
    - Interview not done → finish interview first
    - Interview done, no videos → need to film videos based on guidelines
    - Videos uploaded but not enough → need more videos
    - Videos being analyzed → analysis in progress
    """
    # Check what stage we're actually at
    if not interview_complete:
        completeness_pct = int(completeness * 100)
        return f"אני רוצה ליצור לך דוח מקיף! אבל קודם אני צריכה להכיר את {child_name} טוב יותר דרך השיחה שלנו. כבר עברנו {completeness_pct}% מהראיון - בואי נמשיך."

    # Interview is complete, but no videos yet
    if video_count == 0:
        return f"כדי ליצור דוח, אני צריכה לראות את {child_name} בפעולה! קודם אני אכין לך הנחיות צילום מותאמות אישית, ואז תעלי 3 סרטונים קצרים. אחרי שאנתח אותם - הדוח יהיה מוכן."

    # Have some videos but not enough
    if video_count < required_videos:
        remaining = required_videos - video_count
        remaining_text = "סרטון אחד נוסף" if remaining == 1 else f"{remaining} סרטונים נוספים"
        video_count_text = "סרטון אחד" if video_count == 1 else f"{video_count} סרטונים"
        return f"כמעט שם! יש {video_count_text}, אני צריכה עוד {remaining_text} כדי לקבל תמונה מלאה של {child_name}. ברגע שיהיו 3 סרטונים, אני אתחיל בניתוח ואכין את הדוח."

    # Have enough videos, currently analyzing
    if analysis_complete:
        # Analysis done but reports not generated yet (edge case)
        return f"הניתוח הושלם! אני עובדת כרגע על הכנת הדוח המפורט עבור {child_name}. עוד רגע זה יהיה מוכן. 💙"
    else:
        # Analysis in progress
        return f"מצוין! יש לי 3 סרטונים של {child_name} ואני מנתחת אותם כרגע. זה לוקח בדרך כלל כ-24 שעות. אני רוצה לתת לך ממצאים מדויקים ושימושיים, אז שווה להמתין. בינתיים, את יכולה להוסיף תצפיות ליומן. 💙"


def is_always_available(action: Action) -> bool:
    """Check if action is always available (no prerequisites)"""
    prereq_info = get_action_prerequisites(action)
    return len(prereq_info.get("requires", [])) == 0


def get_always_available_actions() -> List[Action]:
    """Get list of actions that are always available"""
    return [
        action for action in Action
        if is_always_available(action)
    ]


# === Helper for LLM Prompt ===

def get_prerequisite_summary_for_prompt() -> str:
    """
    Get a summary of prerequisites formatted for LLM system prompt

    This tells the LLM what actions require what prerequisites so it can
    understand when to guide users toward completing prerequisites.
    """
    summary = """## Action Prerequisites

When user wants to perform an action, these are the requirements:

**Always Available:**
- Consultation (ask questions anytime)
- Add journal entry (document observations anytime)
- View journal (read past entries anytime)

**Requires Interview Complete:**
- View video guidelines (need context to create personalized guidelines)
- Upload videos (need interview to know what scenarios to film)

**Requires Interview + Videos (3+):**
- Analyze videos (need sufficient video data)

**Requires Analysis Complete (Reports Available):**
- View report (must complete analysis first)
- Download report
- Share report with experts

**Can Do Anytime, Better with Reports:**
- Find experts (can browse anytime, but matching is better with reports)

When user requests something not yet available, gently explain what's needed first and guide them forward."""

    return summary
