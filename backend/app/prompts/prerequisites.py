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
    required_videos: int = 3
) -> str:
    """
    Get Hebrew explanation for why action is not yet available

    Args:
        action: The action user wants to perform
        child_name: Child's name for personalization
        video_count: Number of videos uploaded
        required_videos: Number of videos required

    Returns:
        Hebrew explanation to give to user
    """
    prereq_info = get_action_prerequisites(action)
    explanation = prereq_info.get("explanation_to_user", "")

    # Replace placeholders
    remaining = max(0, required_videos - video_count)
    explanation = explanation.replace("{child_name}", child_name)
    explanation = explanation.replace("{video_count}", str(video_count))
    explanation = explanation.replace("{remaining}", str(remaining))

    return explanation


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
