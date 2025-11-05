"""
Domain-Specific Knowledge for Chitta

This file contains domain-specific content that would be different
for other applications (e.g., career counseling, medical diagnosis, etc.)

The STRUCTURE is reusable, the CONTENT is domain-specific.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Feature:
    """A feature available in the app"""
    name: str
    name_hebrew: str
    description: str
    description_hebrew: str
    always_available: bool
    requires: List[str] = None  # Prerequisites
    enhanced_by: List[str] = None  # Works without, better with

    def __post_init__(self):
        if self.requires is None:
            self.requires = []
        if self.enhanced_by is None:
            self.enhanced_by = []


# ============================================================================
# CHITTA DOMAIN KNOWLEDGE
# ============================================================================

DOMAIN_INFO = {
    "app_name": "Chitta",
    "app_name_hebrew": "צ'יטה",
    "domain": "child_development_screening",
    "purpose": "Child development screening and assessment platform",
    "purpose_hebrew": "פלטפורמה להערכת והתפתחות ילדים"
}

PROCESS_OVERVIEW = """
The screening process happens in stages:

1. **Interview** (מה שאנחנו עושים עכשיו)
   - Deep conversation about your child
   - Understanding strengths, concerns, context
   - Takes about 30 minutes

2. **Video Guidelines** (הנחיות צילום)
   - After interview is complete (80%+)
   - I create personalized filming instructions
   - Shows exactly what scenarios to film

3. **Film & Upload Videos** (צילום והעלאת סרטונים)
   - Parent films 3+ short videos based on guidelines
   - Shows child in different situations

4. **AI Analysis** (ניתוח בינה מלאכותית)
   - Takes ~24 hours
   - Analyzes developmental patterns in videos
   - Combined with interview insights

5. **Comprehensive Report** (דוח מקיף)
   - Detailed findings and recommendations
   - Developmental profile
   - Next steps

6. **Expert Matching** (התאמת מומחים)
   - Connect with relevant specialists
   - Based on report findings
"""

PROCESS_OVERVIEW_HEBREW = """
תהליך הבדיקה מתקדם בשלבים:

1. **ראיון** (מה שאנחנו עושים עכשיו)
   - שיחה מעמיקה על הילד/ה שלך
   - הבנת נקודות חוזק, דאגות, הקשר
   - לוקח בערך 30 דקות

2. **הנחיות צילום**
   - אחרי שהראיון מושלם (80%+)
   - אני יוצרת הוראות צילום מותאמות אישית
   - מראה בדיוק אילו סיטואציות לצלם

3. **צילום והעלאת סרטונים**
   - ההורה מצלם 3+ סרטונים קצרים לפי ההנחיות
   - מציגים את הילד/ה במצבים שונים

4. **ניתוח בינה מלאכותית**
   - לוקח בערך 24 שעות
   - מנתח דפוסי התפתחות בסרטונים
   - בשילוב תובנות מהראיון

5. **דוח מקיף**
   - ממצאים והמלצות מפורטים
   - פרופיל התפתחותי
   - צעדים הבאים

6. **התאמת מומחים**
   - חיבור למומחים רלוונטיים
   - מבוסס על ממצאי הדוח
"""

FEATURES = [
    Feature(
        name="Interview Conversation",
        name_hebrew="שיחת ראיון",
        description="In-depth conversation to understand your child's development",
        description_hebrew="שיחה מעמיקה להבנת התפתחות הילד/ה שלך",
        always_available=True
    ),
    Feature(
        name="Development Journal",
        name_hebrew="יומן התפתחות",
        description="Document daily observations, progress, and concerns anytime",
        description_hebrew="תיעוד תצפיות יומיות, התקדמות ודאגות בכל זמן",
        always_available=True
    ),
    Feature(
        name="Ask Questions (Consultation)",
        name_hebrew="שאלת שאלות (ייעוץ)",
        description="Ask me questions about child development, the process, or concerns anytime",
        description_hebrew="שאלי אותי שאלות על התפתחות ילדים, התהליך או דאגות בכל זמן",
        always_available=True
    ),
    Feature(
        name="Video Filming Guidelines",
        name_hebrew="הנחיות צילום",
        description="Personalized instructions for what videos to film",
        description_hebrew="הוראות מותאמות אישית לאילו סרטונים לצלם",
        always_available=False,
        requires=["interview_complete"]
    ),
    Feature(
        name="Upload Videos",
        name_hebrew="העלאת סרטונים",
        description="Upload 3+ short videos of your child in different scenarios",
        description_hebrew="העלאת 3+ סרטונים קצרים של הילד/ה במצבים שונים",
        always_available=False,
        requires=["interview_complete"]
    ),
    Feature(
        name="Video Analysis",
        name_hebrew="ניתוח סרטונים",
        description="AI analyzes videos for developmental patterns (~24 hours)",
        description_hebrew="ניתוח בינה מלאכותית של דפוסי התפתחות בסרטונים (~24 שעות)",
        always_available=False,
        requires=["minimum_videos"]
    ),
    Feature(
        name="Developmental Report",
        name_hebrew="דוח התפתחותי",
        description="Comprehensive report with findings, recommendations, and next steps",
        description_hebrew="דוח מקיף עם ממצאים, המלצות וצעדים הבאים",
        always_available=False,
        requires=["reports_available"]
    ),
    Feature(
        name="Download Report",
        name_hebrew="הורדת דוח",
        description="Download your report as PDF to share with professionals",
        description_hebrew="הורדת הדוח כ-PDF לשיתוף עם אנשי מקצוע",
        always_available=False,
        requires=["reports_available"]
    ),
    Feature(
        name="Find Experts",
        name_hebrew="מציאת מומחים",
        description="Browse and connect with developmental specialists",
        description_hebrew="עיון וחיבור למומחי התפתחות",
        always_available=True,
        enhanced_by=["reports_available"]
    ),
]


# ============================================================================
# COMMON QUESTIONS AND ANSWERS
# ============================================================================

FAQ = {
    "what_can_i_do": {
        "question_patterns": [
            "מה אני יכול לעשות",
            "מה יש פה",
            "איזה אפשרויות",
            "what can i do",
            "what features",
            "what's available"
        ],
        "answer_hebrew": """יש כמה דברים שאפשר לעשות כאן:

**זמין כרגע (תמיד):**
• **שיחה איתי** - מה שאנחנו עושים עכשיו, ראיון מעמיק על {child_name}
• **יומן התפתחות** - תיעוד תצפיות יומיות ודאגות
• **שאלת שאלות** - שאלי אותי כל שאלה על התפתחות ילדים

**אחרי שנסיים את השיחה:**
• **הנחיות צילום** - אני אכין לך הוראות מדויקות לאילו סרטונים לצלם
• **העלאת סרטונים** - תעלי 3 סרטונים קצרים של {child_name}

**אחרי ניתוח הסרטונים (~24 שעות):**
• **דוח התפתחותי מקיף** - ממצאים והמלצות
• **מציאת מומחים** - חיבור למומחים מתאימים

כרגע אנחנו בשלב הראיון, וזה הבסיס לכל מה שיבוא אחר כך. רוצה שנמשיך?"""
    },
    "how_does_it_work": {
        "question_patterns": [
            "איך זה עובד",
            "מה התהליך",
            "how does this work",
            "what's the process"
        ],
        "answer_hebrew": PROCESS_OVERVIEW_HEBREW
    },
    "how_long": {
        "question_patterns": [
            "כמה זמן",
            "how long",
            "duration"
        ],
        "answer_hebrew": """התהליך המלא:
• **הראיון**: בערך 30 דקות (אפשר לקחת הפסקות)
• **צילום**: בזמנך החופשי, בערך 15-20 דקות סה"כ
• **ניתוח**: בערך 24 שעות
• **סה"כ**: יומיים בערך מהתחלה ועד הדוח

כרגע אנחנו בראיון. רוצה שנמשיך?"""
    },
    "why_video_and_privacy": {
        "question_patterns": [
            "למה צריך לצלם",
            "למה ווידאו",
            "למה סרטון",
            "פרטיות",
            "איפה שומרים",
            "בטיחות",
            "מי רואה",
            "why video",
            "privacy",
            "security",
            "where stored"
        ],
        "answer_hebrew": """זו שאלה כל כך חשובה! החשש לגבי פרטיות הוא טבעי ומובן לחלוטין.

**למה סרטונים?**
כשאנחנו מדברות, אני (צ'יטה - AI) שומעת את התיאור שלך, שהוא הכי חשוב. אבל לפעמים יש דברים קטנים שקשה לתאר במילים - שפת גוף, קשר עין, אופן המשחק, האינטראקציות. הסרטונים מאפשרים לבינה המלאכותית שלי לנתח את הדפוסים ההתפתחותיים בדרך מדויקת יותר, ולתת לך תמונה מלאה יותר.

**פרטיות וביטחון:**
• **מוצפן ומאובטח**: הסרטונים נשמרים במערכת מאובטחת ומוצפנת ברמה הכי גבוהה (כמו מערכות רפואיות)
• **ניתוח אוטומטי**: הניתוח נעשה על ידי בינה מלאכותית (AI) שמחפשת דפוסי התפתחות
• **גישה מוגבלת**: רק אתה וצוות המקצועי המורשה שלך יכולים לראות את הסרטונים
• **אין שיתוף**: הסרטונים לעולם לא משותפים עם גורמי חוץ ללא הסכמתך המפורשת
• **מחיקה**: אתה יכול למחוק את הסרטונים בכל עת

הפרטיות והביטחון שלך הם בראש סדר העדיפויות. אם יש לך עוד שאלות על זה, אני כאן.

רוצה שנמשיך בשיחה?"""
    }
}


def get_feature_list_hebrew(current_state: Dict = None) -> str:
    """
    Get formatted feature list in Hebrew, showing what's available now

    Args:
        current_state: Dict with interview_complete, videos_uploaded, etc.

    Returns:
        Formatted Hebrew string listing features
    """
    if current_state is None:
        current_state = {}

    interview_complete = current_state.get("interview_complete", False)
    minimum_videos = current_state.get("minimum_videos", False)
    reports_available = current_state.get("reports_available", False)

    available_now = []
    available_later = []

    for feature in FEATURES:
        if feature.always_available:
            status = "✓"
            available_now.append(f"{status} **{feature.name_hebrew}** - {feature.description_hebrew}")
        else:
            # Check if available based on current state
            is_available = True
            if "interview_complete" in feature.requires and not interview_complete:
                is_available = False
            if "minimum_videos" in feature.requires and not minimum_videos:
                is_available = False
            if "reports_available" in feature.requires and not reports_available:
                is_available = False

            if is_available:
                status = "✓"
                available_now.append(f"{status} **{feature.name_hebrew}** - {feature.description_hebrew}")
            else:
                status = "○"
                available_later.append(f"{status} **{feature.name_hebrew}** - {feature.description_hebrew}")

    result = "**זמין עכשיו:**\n" + "\n".join(available_now)

    if available_later:
        result += "\n\n**יהיה זמין בהמשך:**\n" + "\n".join(available_later)

    return result


def match_faq_question(user_message: str) -> Optional[str]:
    """
    Match user message to FAQ question

    Args:
        user_message: User's message

    Returns:
        FAQ key if matched, None otherwise
    """
    user_message_lower = user_message.lower()

    for faq_key, faq_data in FAQ.items():
        for pattern in faq_data["question_patterns"]:
            if pattern.lower() in user_message_lower:
                return faq_key

    return None
