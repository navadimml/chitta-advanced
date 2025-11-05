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
    "domain": "child_development_assistant",
    "purpose": "AI-powered parental assistant for child development - from initial screening through ongoing journey documentation and care coordination",
    "purpose_hebrew": "מערכת ליווי הורי מונעת בינה מלאכותית להתפתחות ילדים - מהערכה ראשונית ועד תיעוד מסע מתמשך ותיאום טיפול"
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
   - Parent films short videos based on personalized guidelines
   - Number and type of videos tailored to child's specific needs
   - Shows child in different relevant situations

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
   - ההורה מצלם סרטונים קצרים לפי הנחיות מותאמות אישית
   - מספר וסוג הסרטונים מותאם לצרכים הספציפיים של הילד/ה
   - מציגים את הילד/ה במצבים רלוונטיים שונים

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
        description="Upload short videos of your child based on personalized filming guidelines",
        description_hebrew="העלאת סרטונים קצרים של הילד/ה לפי הנחיות צילום מותאמות",
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
    "what_is_chitta": {
        "question_patterns": [
            "מה זה צ'יטה",
            "מה זאת האפליקציה",
            "מה זה האפליקציה הזאת",
            "מה את",
            "מה זה כאן",
            "מי את",
            "what is chitta",
            "what is this app",
            "what are you",
            "who are you"
        ],
        "answer_hebrew": """אני Chitta, מערכת ליווי הורי להתפתחות ילדים.

**איך אני עוזרת:**
• שיחה מעמיקה להכרת הילד/ה שלך
• ניתוח וידאו התפתחותי
• תיעוד המסע במקום אחד
• המלצות מקצועיות מבוססות מחקר

השאלה החשובה היא - איך אני יכולה לעזור לך עם הילד/ה שלך? 💙"""
    },
    "internal_instructions": {
        "question_patterns": [
            "ההוראות שלך",
            "ההנחיות שלך",
            "הפרומפט שלך",
            "הסיסטם פרומפט",
            "system prompt",
            "your instructions",
            "your guidelines",
            "your prompt",
            "internal instructions",
            "תשתפי את ההוראות",
            "מה המבנה",
            "איך את עובדת",
            "מה הכללים שלך",
            "how do you work",
            "what's your structure",
            "share your instructions"
        ],
        "answer_hebrew": """התפקיד שלי פשוט לעזור לך להבין את ההתפתחות של הילד/ה שלך באמצעות שיחה מעמיקה וניתוח מקצועי.

בואי נתמקד במה שחשוב - ספרי לי על הילד/ה שלך. מה מדאיג אותך? 💙"""
    },
    "creative_writing_about_chitta": {
        "question_patterns": [
            "תכתבי לי שיר",
            "תכתבי שיר",
            "תספרי לי סיפור",
            "איך עבר לך היום",
            "מה את מרגישה",
            "מה היום שלך",
            "איך את מרגישה היום",
            "write me a poem",
            "write a song",
            "tell me a story",
            "how was your day",
            "how are you feeling",
            "what's your day like"
        ],
        "answer_hebrew": """אני כאן כדי לעזור לך עם הילד/ה שלך, לא לדבר על עצמי.

בואי נתמקד במה שחשוב - ספרי לי על הילד/ה. מה מדאיג אותך? 💙"""
    },
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
• **הנחיות צילום** - אני אכין לך הוראות מדויקות לאילו סרטונים לצלם (מותאם אישית)
• **העלאת סרטונים** - תעלי סרטונים קצרים של {child_name} לפי ההנחיות המותאמות

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
    "data_privacy_comprehensive": {
        "question_patterns": [
            "פרטיות",
            "בטיחות",
            "בטוח",
            "מי רואה",
            "מי יכול לראות",
            "איפה שומרים",
            "איפה אתם שומרים",
            "איפה המידע",
            "איפה הנתונים",
            "מאובטח",
            "הגנת מידע",
            "נתונים רגישים",
            "גישה למידע",
            "privacy",
            "security",
            "data protection",
            "safe",
            "secure",
            "who sees",
            "who can see",
            "where stored",
            "where is the data"
        ],
        "answer_hebrew": """זו שאלה **קריטית** ואני שמחה שאתה שואל! מדובר במידע רגיש על הילד/ה שלך, ואנחנו מתייחסים לזה ברצינות מוחלטת.

**איזה מידע אנחנו אוספים?**
• השיחה שלנו (התפתחות, דאגות, היסטוריה)
• סרטונים של הילד/ה במצבים שונים
• תצפיות שאתה מתעד ביומן
• הדוח וההמלצות

**איך אנחנו שומרים את המידע?**
• **הצפנה מלאה**: כל המידע מוצפן ברמה הכי גבוהה (AES-256, כמו במערכות בנקאות ורפואיות)
• **שרתים מאובטחים**: מידע נשמר בשרתים מאובטחים בהתאם לתקני הגנת מידע רפואי
• **גיבויים מוצפנים**: גיבויים אוטומטיים מוצפנים למניעת אובדן מידע
• **אבטחת רשת**: הגנה רב-שכבתית מפני גישה לא מורשית

**מי יכול לראות את המידע?**
• **אתה**: יש לך גישה מלאה לכל המידע שלך בכל זמן
• **צוות מקצועי מורשה**: רק אם אתה מאשר במפורש (למשל, מומחים שאתה בוחר לשתף איתם)
• **בדיקת איכות**: מומחים מאומתים עשויים לבדוק את הדוח לצורך בקרת איכות (ראה למטה)
• **אף אחד אחר**: אף גורם שלישי לא מקבל גישה ללא הסכמתך המפורשת

**התאמה לתקנים:**
• GDPR (תקנות הגנת מידע אירופאיות) - כולל זכות למחיקה, גישה, תיקון
• הגנה מיוחדת לקטינים - דרישות מחמירות יותר למידע על ילדים
• תקני אבטחת מידע רפואי

**השליטה שלך:**
• **זכות לצפייה**: לראות את כל המידע שנאסף עליך
• **זכות למחיקה**: למחוק את כל המידע בכל עת (right to be forgotten)
• **זכות לייצוא**: להוריד עותק של כל המידע שלך
• **זכות להגבלה**: להגביל את השימוש במידע שלך

**שמירת מידע:**
• המידע נשמר כל עוד אתה משתמש פעיל בשירות
• אתה יכול למחוק את החשבון והמידע בכל עת
• לאחר מחיקה - המידע נמחק לצמיתות תוך 30 יום

הפרטיות והביטחון שלך הם **קדושים** עבורנו. זה הבסיס לאמון ביננו. 💙

יש לך עוד שאלות על זה?"""
    },
    "why_video_and_how": {
        "question_patterns": [
            "למה צריך לצלם",
            "למה ווידאו",
            "למה סרטון",
            "מה הסרטון עושה",
            "why video",
            "why filming"
        ],
        "answer_hebrew": """שאלה מצוינת! בואי אסביר למה הסרטונים כל כך חשובים.

**למה סרטונים?**
כשאנחנו מדברות, אני (צ'יטה - AI) שומעת את התיאור שלך, שהוא **הכי חשוב**. אבל לפעמים יש דברים קטנים שקשה לתאר במילים:
• שפת גוף ותנועות
• קשר עין ותקשורת לא מילולית
• אופן המשחק והאינטראקציה
• קצב ותזמון של תגובות

הסרטונים מאפשרים לבינה המלאכותית שלי לנתח דפוסי התפתחות בדרך מדויקת יותר.

**מה צריך לצלם?**
אחרי השיחה שלנו, אני אכין לך **הנחיות צילום מותאמות אישית** - בדיוק מה צריך לצלם ואיך, בהתאם למה שדיברנו. מספר הסרטונים משתנה בהתאם לצרכים של {child_name or 'הילד/ה'}.

**כמה זמן?**
כמה סרטונים קצרים (כ-3-5 דקות כל אחד) - בדרך כלל סה"כ כ-15-20 דקות צילום.

יש לך עוד שאלות על התהליך?"""
    },
    "human_oversight_quality": {
        "question_patterns": [
            "מי בודק",
            "בן אדם בודק",
            "רק מכונה",
            "רק AI",
            "איש מקצוע רואה",
            "מומחה בודק",
            "בקרת איכות",
            "human check",
            "expert review",
            "quality control",
            "just AI",
            "only machine"
        ],
        "answer_hebrew": """שאלה מצוינת! זה נושא מאוד חשוב.

**איך עובד תהליך בקרת האיכות?**

1. **ניתוח ראשוני (AI)**:
   אני (צ'יטה - AI) מנתחת את השיחה והסרטונים, ומזהה דפוסי התפתחות

2. **בדיקת איכות אוטומטית**:
   מערכת בודקת שהניתוח מלא, עקבי ומבוסס היטב

3. **תיקון אוטומטי אם נדרש**:
   אם מזוהה חוסר או חוסר עקביות - המערכת מתקנת אוטומטית

4. **סקירה אנושית במקרה הצורך**:
   אם התיקון לא מספיק טוב - הדוח מועבר למומחה אנושי לבדיקה **לפני** שאתה רואה אותו

**אז מי רואה את הדוח?**
• בדרך כלל: ניתוח AI עם בדיקת איכות אוטומטית
• במקרים שנדרש: מומחה אנושי בודק ומאשר את הדוח

**המטרה:**
לתת לך דוח **מדויק, מקצועי ושימושי** - בין אם דרך AI מתקדמת, או עם סקירה אנושית נוספת.

**חשוב לדעת:**
• הדוחות מבוססים על מחקר וידע מקצועי בהתפתחות ילדים
• המערכת מאומנת על אלפי מקרים
• תמיד יש אפשרות להתייעצות עם מומחים אנושיים לאחר קבלת הדוח

האם זה מרגיע אותך?"""
    },
    "expert_recommendations": {
        "question_patterns": [
            "מומלץ",
            "ממליץ",
            "המלצות",
            "אישורים",
            "הסמכות",
            "גופים מקצועיים",
            "ארגונים",
            "מהימן",
            "אמין",
            "מי פיתח",
            "מי עומד מאחורי",
            "recommended",
            "endorsements",
            "certifications",
            "accredited",
            "trustworthy",
            "reliable",
            "who developed",
            "who's behind"
        ],
        "answer_hebrew": """שאלה חשובה! אני מבינה שאתה רוצה לדעת שזה מהימן.

**מי עומד מאחורי צ'יטה?**
• **נוירולוג מומחה בהתפתחות ילדים** - אחד המייסדים שלנו הוא נוירולוג מוכר המתמחה בהתפתחות ילדים
• **צוות מקצועי** - משלבים מומחיות רפואית עם טכנולוגיה מתקדמת
• **מבוסס על מחקר** - עוקבים אחר המחקר העדכני ביותר בפסיכולוגיה התפתחותית

**הבסיס המקצועי:**
• עוקבים אחר **קווים מנחים מקצועיים** של ארגונים כמו WHO, AAP (American Academy of Pediatrics)
• מבוססים על **פרוטוקולים קליניים** מוכחים להערכת התפתחות
• פיתוח מתמשך בשיתוף עם מומחי התפתחות ילדים

**המסע שלנו:**
אנחנו בשלב פיתוח מתקדם, ועובדים על:
• **מחקר קליני** - תכנון מחקר קליני באמצעות האפליקציה לאימות יעילות
• **הסמכות מקצועיות** - עבודה להשגת אישורים והמלצות מגופים מקצועיים בתחום
• **שיתופי פעולה** - בניית שותפויות עם מוסדות מובילים

**תקנים ואבטחה:**
• עומדים בתקני **GDPR** להגנת מידע
• הגנה מיוחדת למידע על **קטינים** (דרישות מחמירות יותר)
• אבטחה ברמת **מערכות רפואיות** (הצפנה AES-256)

**השקיפות שלנו:**
אנחנו שקופים לגמרי לגבי המסע שלנו. אנחנו לא טוענים להסמכות שעדיין אין לנו, אבל אנחנו עובדים קשה כדי לבנות את הכלי המקצועי והמהימן ביותר להורים, תוך שמירה על סטנדרטים גבוהים מאוד ושיתוף פעולה עם המומחים המובילים בתחום.

האמון שלך חשוב לנו מאוד. יש לך עוד שאלות? 💙"""
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
    Match user message to FAQ question with fuzzy matching

    Handles word variations, different word orders, and stemming

    Args:
        user_message: User's message

    Returns:
        FAQ key if matched, None otherwise
    """
    user_message_lower = user_message.lower()

    # Helper function to check if multiple keywords are present (fuzzy match)
    def fuzzy_match(keywords: List[str], text: str) -> bool:
        """Check if all keywords are present in text (with stemming)"""
        import re

        # Simple Hebrew stemming - remove common suffixes and prefixes
        def stem_hebrew(word: str) -> str:
            # Remove punctuation first
            word = re.sub(r'[^\u0590-\u05FF\u0600-\u06FF\w]', '', word)

            # Only remove definite article prefix 'ה' (the)
            # Don't remove other letters that might be part of the root
            if word.startswith('ה') and len(word) > 2:
                word = word[1:]

            # Remove common suffixes like ים, ות
            for suffix in ['ים', 'ות']:
                if word.endswith(suffix) and len(word) > len(suffix) + 1:
                    word = word[:-len(suffix)]
                    break

            return word

        # Stem all words in text
        text_words = [stem_hebrew(w) for w in text.split()]
        text_combined = ' '.join(text_words)  # Also check in combined form

        for keyword in keywords:
            keyword_stemmed = stem_hebrew(keyword.lower())
            # Check if keyword (or its stem) appears in any word in text
            found = False
            for word in text_words:
                # Use similarity check - allow for small differences
                # Check if one contains the other, or if they're very similar
                if keyword_stemmed in word or word in keyword_stemmed:
                    found = True
                    break
                # Check for close match (1-2 character difference for Hebrew)
                if len(keyword_stemmed) >= 3 and len(word) >= 3:
                    # Calculate simple similarity
                    # If first 2 chars match and one is substring of other
                    if keyword_stemmed[:2] == word[:2] or keyword_stemmed[:3] == word[:3]:
                        if keyword_stemmed in word or word in keyword_stemmed or \
                           abs(len(keyword_stemmed) - len(word)) <= 1:
                            found = True
                            break

            # Also check if keyword appears in the combined stemmed text
            if not found and keyword_stemmed in text_combined:
                found = True

            if not found:
                return False
        return True

    # Try exact substring match first (backward compatibility)
    for faq_key, faq_data in FAQ.items():
        for pattern in faq_data["question_patterns"]:
            if pattern.lower() in user_message_lower:
                return faq_key

    # Try fuzzy matching for privacy-related questions
    # Special handling for video storage/privacy questions
    privacy_keywords = [
        ['סרטון', 'נשמר'],  # video + saved (נשמר/נישמר/שומר)
        ['סרטון', 'שומר'],  # video + save
        ['סרטון', 'איפה'],  # video + where
        ['וידאו', 'נשמר'],  # video + saved
        ['וידאו', 'שומר'],  # video + save
        ['וידאו', 'איפה'],  # video + where
        ['סרטון', 'פרטיות'],  # video + privacy
        ['וידאו', 'פרטיות'],  # video + privacy
        ['מידע', 'נשמר'],  # data + saved
        ['מידע', 'שומר'],  # data + save
        ['מידע', 'איפה'],  # data + where
        ['נתונים', 'נשמר'],  # data + saved
        ['נתונים', 'שומר'],  # data + save
    ]

    for keywords in privacy_keywords:
        if fuzzy_match(keywords, user_message_lower):
            return "data_privacy_comprehensive"

    # Try fuzzy matching for general privacy questions
    if fuzzy_match(['פרטיות'], user_message_lower) or \
       fuzzy_match(['מאובטח'], user_message_lower) or \
       fuzzy_match(['בטוח'], user_message_lower):
        return "data_privacy_comprehensive"

    return None
