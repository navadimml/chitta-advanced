"""
State Derivation - Pure Functions
Cards, greetings, suggestions all derive from state.
Nothing is stored - everything is computed.
"""
from typing import List, Dict
from ..models.family_state import FamilyState


def derive_active_cards(state: FamilyState) -> List[dict]:
    """
    Cards are COMPUTED from state, not stored.
    This is Wu Wei - system organizes itself.
    """
    cards = []

    # Rule 1: If guidelines exist but videos < 3, show upload + guidelines cards
    if "baseline_video_guidelines" in state.artifacts:
        videos_count = len(state.videos_uploaded)

        if videos_count < 3:
            # Upload card
            cards.append({
                "card_type": "action",
                "status": "pending",
                "icon": "Upload",
                "title": f"העלה סרטונים ({videos_count}/3)",
                "subtitle": f"עוד {3 - videos_count} סרטונים נדרשים",
                "action": "upload",
                "color": "orange",
                "priority": 9
            })

        # Guidelines card (always show if exists)
        cards.append({
            "card_type": "artifact",
            "status": "ready",
            "icon": "FileText",
            "title": "הנחיות צילום מוכנות",
            "subtitle": "לחץ לצפייה בהנחיות",
            "action": "view_guidelines",
            "color": "blue",
            "priority": 8
        })

    # Rule 2: If parent report exists, show it
    if "parent_report" in state.artifacts:
        cards.append({
            "card_type": "artifact",
            "status": "new",
            "icon": "FileCheck",
            "title": "דוח הורים מוכן",
            "subtitle": "תובנות מפורטות על הילד",
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
            "title": "דוח מקצועי מוכן",
            "subtitle": "המלצות מקצועיות",
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
            "title": "השיחה מתקדמת יפה",
            "subtitle": "ספרי עוד על הילד",
            "color": "cyan",
            "priority": 7
        })

    # Rule 5: If videos analyzing, show progress
    if len(state.videos_uploaded) >= 3 and "parent_report" not in state.artifacts:
        cards.append({
            "card_type": "progress",
            "status": "processing",
            "icon": "Loader",
            "title": "מנתח סרטונים",
            "subtitle": "זה יכול לקחת יום עבודה",
            "color": "yellow",
            "priority": 8
        })

    # Sort by priority and return top 4
    sorted_cards = sorted(cards, key=lambda x: x["priority"], reverse=True)
    return sorted_cards[:4]


def derive_contextual_greeting(state: FamilyState) -> str:
    """
    Greeting is COMPUTED from state.
    System knows where family is by looking at DNA.
    """

    # First visit
    if not state.conversation:
        return (
            "שלום! אני צ'יטה 💙\n\n"
            "נעים להכיר אותך! אני כאן כדי להכיר את הילד/ה שלך ולהבין איך אפשר לעזור. "
            "נשוחח קצת יחד, ואז נמשיך לשלבים הבאים.\n\n"
            "בואי נתחיל - מה שם הילד/ה שלך ובן/בת כמה?"
        )

    child_name = state.child.get("name") if state.child else "הילד"

    # Returning mid-interview
    if not state.artifacts:
        return (
            f"שלום שוב! 💙 נחמד לראות אותך.\n\n"
            f"המשכנו לדבר על {child_name}. איפה עצרנו?"
        )

    # Guidelines ready, waiting for videos
    if "baseline_video_guidelines" in state.artifacts:
        videos_count = len(state.videos_uploaded)

        if videos_count == 0:
            return (
                f"שלום! 💙 ההנחיות לצילום מוכנות.\n\n"
                f"כשתעלי את הסרטונים של {child_name}, אוכל להתחיל לנתח."
            )
        elif videos_count < 3:
            return (
                f"היי! 💙 ראיתי שהעלית {videos_count} סרטונים.\n\n"
                f"עוד {3 - videos_count} יעזרו לי להבין את {child_name} טוב יותר."
            )
        elif "parent_report" not in state.artifacts:
            return (
                f"מעולה! 💙 קיבלתי את כל הסרטונים.\n\n"
                f"אני מנתח אותם עכשיו. זה יכול לקחת יום עבודה."
            )

    # Reports ready
    if "parent_report" in state.artifacts:
        return (
            f"היי! 💙 הדוח על {child_name} מוכן!\n\n"
            f"גיליתי כמה דברים מעניינים. בואי נראה ביחד?"
        )

    # Default
    return f"שלום! 💙 איך {child_name} היום?"


def derive_suggestions(state: FamilyState) -> List[dict]:
    """
    Suggestions derive from state.
    Guide user on what to do next.
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
                {"text": "הראה לי את ההנחיות", "action": "view_guidelines"},
                {"text": "אעלה סרטון", "action": "upload"},
                {"text": "יש לי שאלה על הצילום", "action": None}
            ]

    # Reports ready - encourage viewing
    if "parent_report" in state.artifacts:
        return [
            {"text": "הראה לי את הדוח", "action": "parentReport"},
            {"text": "מה המלצות", "action": None},
            {"text": "צריך עזרה להבין", "action": None}
        ]

    return suggestions
