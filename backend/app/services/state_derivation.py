"""
State Derivation - Pure Functions
Cards, greetings, suggestions all derive from state.
Nothing is stored - everything is computed.

🌟 Wu Wei: Now includes time-aware context for intermittent users
🌟 Uses i18n for all user-facing text
"""
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from ..models.family_state import FamilyState
from .i18n_service import t, get_i18n


def derive_active_cards(state: FamilyState) -> List[dict]:
    """
    Cards are COMPUTED from state, not stored.
    This is Wu Wei - system organizes itself.

    Note: Card text comes from i18n, card structure is framework logic.
    """
    cards = []
    i18n = get_i18n()

    # Rule 1: If guidelines exist but videos < 3, show upload + guidelines cards
    if "baseline_video_guidelines" in state.artifacts:
        videos_count = len(state.videos_uploaded)
        videos_remaining = 3 - videos_count

        if videos_count < 3:
            # Upload card
            cards.append({
                "card_type": "action",
                "status": "pending",
                "icon": "Upload",
                "title": t("cards.upload_videos.title",
                          videos_uploaded=videos_count, videos_total=3),
                "subtitle": t("cards.upload_videos.body",
                             videos_remaining=videos_remaining),
                "action": "upload",
                "color": "orange",
                "priority": 9
            })

        # Guidelines card (always show if exists)
        cards.append({
            "card_type": "artifact",
            "status": "ready",
            "icon": "FileText",
            "title": t("cards.guidelines_ready.title"),
            "subtitle": t("ui.buttons.view_guidelines"),
            "action": "view_guidelines",
            "color": "blue",
            "priority": 8
        })

    # Rule 2: If parent report exists, show it
    if "parent_report" in state.artifacts:
        child_name = state.child.get("name", "") if state.child else ""
        cards.append({
            "card_type": "artifact",
            "status": "new",
            "icon": "FileCheck",
            "title": t("cards.report_ready.title"),
            "subtitle": t("cards.report_ready.body", child_name=child_name),
            "action": "parentReport",
            "color": "purple",
            "priority": 10
        })

    # Rule 3: If professional report exists, show it
    if "professional_report" in state.artifacts:
        cards.append({
            "card_type": "artifact",
            "status": "new",
            "icon": "FileText",
            "title": t("cards.report_ready.title"),  # Reuse same key
            "subtitle": t("cards.report_ready.footer"),
            "action": "proReport",
            "color": "green",
            "priority": 9
        })

    # Rule 4: If interview ongoing (no artifacts yet), show progress
    if not state.artifacts and len(state.conversation) > 2:
        cards.append({
            "card_type": "progress",
            "status": "processing",
            "icon": "MessageCircle",
            "title": t("cards.welcome.title"),
            "subtitle": t("moments.first_message"),
            "color": "cyan",
            "priority": 7
        })

    # Rule 5: If videos analyzing, show progress
    if len(state.videos_uploaded) >= 3 and "parent_report" not in state.artifacts:
        cards.append({
            "card_type": "progress",
            "status": "processing",
            "icon": "Loader",
            "title": t("greetings.stage.videos_analyzing"),
            "subtitle": "",
            "color": "yellow",
            "priority": 8
        })

    # Sort by priority and return top 4
    sorted_cards = sorted(cards, key=lambda x: x["priority"], reverse=True)
    return sorted_cards[:4]


def calculate_time_gap(last_active: Optional[datetime]) -> Dict[str, Any]:
    """
    Calculate time gap since last activity.

    This is a pure framework function - no text, just data.

    Returns:
        Dict with hours, days, category, and is_returning flag
    """
    if not last_active:
        return {
            "hours": 0,
            "days": 0,
            "category": "same_session",
            "is_returning": False
        }

    now = datetime.now()

    # Handle timezone-aware datetimes
    if last_active.tzinfo is not None and now.tzinfo is None:
        now = datetime.now(last_active.tzinfo)

    time_diff = now - last_active
    hours = time_diff.total_seconds() / 3600
    days = time_diff.days

    # Categorize
    if hours < 1:
        category = "same_session"
        is_returning = False
    elif hours < 24:
        category = "short_break"
        is_returning = False
    elif hours < 168:  # 7 days
        category = "returning"
        is_returning = True
    else:
        category = "long_absence"
        is_returning = True

    return {
        "hours": round(hours, 1),
        "days": days,
        "category": category,
        "is_returning": is_returning
    }


def derive_contextual_greeting(state: FamilyState) -> str:
    """
    Greeting is COMPUTED from state using i18n translations.
    System knows where family is by looking at DNA.

    🌟 Wu Wei: Time-aware, uses i18n for all text
    """
    i18n = get_i18n()

    # First visit
    if not state.conversation:
        return t("greetings.first_visit")

    child_name = state.child.get("name") if state.child else "הילד/ה"

    # Calculate time gap for returning users
    time_gap = calculate_time_gap(state.last_active)
    days = time_gap["days"]

    # Returning after long absence (7+ days)
    if time_gap["category"] == "long_absence":
        return t("greetings.returning.long_absence", child_name=child_name)

    # Returning after 1-7 days
    if time_gap["category"] == "returning":
        time_ago = i18n.format_time_ago(days)

        # Customize based on journey stage
        if not state.artifacts:
            return t("greetings.returning.after_days",
                    child_name=child_name, time_ago=time_ago)

        if "baseline_video_guidelines" in state.artifacts and len(state.videos_uploaded) == 0:
            return t("greetings.stage.guidelines_ready",
                    child_name=child_name, time_ago=time_ago)

    # Same session or short break - use stage-based greetings
    videos_count = len(state.videos_uploaded)

    # Report ready
    if "parent_report" in state.artifacts:
        return t("greetings.stage.report_ready", child_name=child_name)

    # Videos analyzing
    if videos_count >= 3 and "parent_report" not in state.artifacts:
        return t("greetings.stage.videos_analyzing", child_name=child_name)

    # Partial videos
    if "baseline_video_guidelines" in state.artifacts:
        if videos_count == 0:
            return t("greetings.stage.guidelines_ready",
                    child_name=child_name, time_ago="")
        elif videos_count < 3:
            return t("greetings.stage.videos_partial",
                    child_name=child_name,
                    videos_uploaded=videos_count,
                    videos_remaining=3 - videos_count)

    # Mid-interview (default)
    return t("greetings.returning.short_break", child_name=child_name)


def derive_suggestions(state: FamilyState) -> List[dict]:
    """
    Suggestions derive from state.
    Guide user on what to do next.

    Note: Suggestions are kept simple - could be moved to i18n if needed.
    """
    suggestions = []

    # No conversation yet - basic suggestions
    if not state.conversation:
        return [
            {"text": "שמו יוני והוא בן 3.5", "action": None},
            {"text": "הילדה שלי בת 5", "action": None},
            {"text": "רוצה להתחיל בהערכה", "action": None}
        ]

    # Mid-interview - encourage sharing
    if not state.artifacts:
        if state.child:
            child_name = state.child.get("name", "הילד")
            return [
                {"text": f"ספרי על החוזקות של {child_name}", "action": None},
                {"text": "מה מדאיג אותי", "action": None},
                {"text": "איך הוא מתנהג בגן", "action": None}
            ]

    # Guidelines ready - encourage video upload
    if "baseline_video_guidelines" in state.artifacts:
        videos_count = len(state.videos_uploaded)
        if videos_count < 3:
            return [
                {"text": t("ui.buttons.view_guidelines"), "action": "view_guidelines"},
                {"text": t("ui.buttons.upload_video"), "action": "upload"},
                {"text": "יש לי שאלה על הצילום", "action": None}
            ]

    # Reports ready - encourage viewing
    if "parent_report" in state.artifacts:
        return [
            {"text": t("ui.buttons.view_report"), "action": "parentReport"},
            {"text": "מה המלצות", "action": None},
            {"text": "צריך עזרה להבין", "action": None}
        ]

    return suggestions
