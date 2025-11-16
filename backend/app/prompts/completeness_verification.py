"""
Completeness Verification Prompt - Wu Wei Robustness

🔍 Purpose: Evaluate SEMANTIC quality of extracted interview data, not just character counts.

This prompt is used to verify that we have enough USEFUL information to:
1. Generate effective, personalized video recording guidelines
2. Create a comprehensive developmental assessment report

The LLM evaluates actual content quality and identifies specific gaps.
"""

def build_completeness_verification_prompt(
    extracted_data: dict,
    conversation_history: list
) -> str:
    """
    Build prompt for LLM to evaluate interview completeness semantically.

    Args:
        extracted_data: Dict with all extracted fields (child_name, age, concerns, etc.)
        conversation_history: List of conversation messages for context

    Returns:
        Prompt string for LLM
    """

    # Format extracted data for review
    child_name = extracted_data.get('child_name', '(לא נמסר)')
    age = extracted_data.get('age', '(לא נמסר)')
    gender = extracted_data.get('gender', 'unknown')
    primary_concerns = extracted_data.get('primary_concerns', [])
    concern_details = extracted_data.get('concern_details', '')
    strengths = extracted_data.get('strengths', '')
    developmental_history = extracted_data.get('developmental_history', '')
    family_context = extracted_data.get('family_context', '')
    daily_routines = extracted_data.get('daily_routines', '')
    parent_goals = extracted_data.get('parent_goals', '')

    # Format concerns
    concerns_text = ", ".join(primary_concerns) if primary_concerns else "(אין)"

    # Count conversation turns
    turn_count = len([msg for msg in conversation_history if msg.get('role') == 'user'])

    prompt = f"""אתה מומחה בהערכה התפתחותית של ילדים. תפקידך לבדוק את השלמות והעומק של הראיון ההורי.

## 🎯 מטרת הבדיקה

עלינו לוודא שיש לנו מספיק מידע **איכותי ושימושי** עבור:

### 1. יצירת הנחיות צילום מותאמות אישית (קריטי!)
**למה צריך:**
- דוגמאות **ספציפיות** של התנהגויות מדאיגות
- הבנה מתי/איפה/איך הדאגות מתבטאות
- הקשר מעשי (משחק, אוכל, שינה, אינטראקציות)
- חוזקות כדי להציע גם מצבי צילום חיוביים

**דוגמה לטוב:** "מיכל לא מצליחה לבקש דברים - היא מושכת אותי לחפץ במקום לומר מה היא רוצה. זה קורה בעיקר בבוקר כשהיא רוצה אוכל או צעצועים."
**דוגמה לרע:** "יש לה קושי בתקשורת."

### 2. דוח הערכה מקיף (אחרי ניתוח וידאו)
**למה צריך:**
- הקשר התפתחותי (אבני דרך, היסטוריה רפואית)
- הקשר משפחתי (אחים, שפות, סביבה)
- שגרה יומיומית (שינה, אכילה, פעילויות)
- מטרות הורים (מה הם רוצים להשיג/להבין)

---

## 📋 נתונים שנאספו עד כה

**מספר תחלופות שיחה:** {turn_count} תחלופות (הורה + צ'יטה)

### מידע בסיסי
- **שם הילד/ה:** {child_name}
- **גיל:** {age}
- **מגדר:** {gender}

### דאגות עיקריות
- **קטגוריות:** {concerns_text}
- **פירוט הדאגות:**
{concern_details if concern_details else "(אין פירוט)"}

### חוזקות
{strengths if strengths else "(לא נאספו)"}

### היסטוריה התפתחותית
{developmental_history if developmental_history else "(לא נאספה)"}

### הקשר משפחתי
{family_context if family_context else "(לא נאסף)"}

### שגרה יומיומית
{daily_routines if daily_routines else "(לא נאספה)"}

### מטרות הורים
{parent_goals if parent_goals else "(לא נאספו)"}

---

## 🔍 המשימה שלך

הערך את השלמות **הסמנטית** של הראיון. אל תסתמך על ספירת תווים - הערך את **איכות התוכן**.

בדוק:

### א. האם יש מספיק מידע להנחיות צילום אפקטיביות? (קריטי!)

1. **דאגה עיקרית מזוהה?** (כן/לא)
2. **יש דוגמאות ספציפיות להתנהגויות?** (כן/חלקית/לא)
   - למשל: "לא מדברת טוב" (רע) vs "לא אומרת 'אבא אמא', רק מצביעה" (טוב)
3. **יש הקשר מעשי - מתי/איפה זה קורה?** (כן/חלקית/לא)
   - למשל: "בגן", "בזמן אוכל", "כשמנסה לשחק עם אחרים"
4. **יש חוזקות/תחומים חיוביים לצילום?** (כן/חלקית/לא)

**ציון הנחיות צילום:** 0-100%

### ב. האם יש מספיק מידע לדוח הערכה מקיף?

5. **יש היסטוריה התפתחותית?** (מלא/חלקי/חסר)
   - אבני דרך, היסטוריה רפואית, הערכות קודמות
6. **יש הקשר משפחתי?** (מלא/חלקי/חסר)
   - אחים, שפות בבית, סביבה חינוכית
7. **יש שגרה יומיומית?** (מלא/חלקי/חסר)
   - שינה, אכילה, פעילויות טיפוסיות
8. **יש מטרות הורים?** (כן/חלקית/לא)
   - מה הם רוצים להבין/לשפר

**ציון דוח מקיף:** 0-100%

### ג. השלמות כוללת

**ציון השלמות כולל:** 0-100%
- 0-40%: ראיון ראשוני - חסר מידע קריטי
- 41-60%: ראיון חלקי - יש בסיס אבל חסרים פרטים
- 61-80%: ראיון טוב - מספיק להנחיות צילום
- 81-100%: ראיון מצוין - מוכן לדוח מקיף

---

## 📝 פורמט התשובה

החזר JSON בלבד:

```json
{{
  "overall_completeness": <0-100>,
  "video_guidelines_readiness": <0-100>,
  "comprehensive_report_readiness": <0-100>,

  "what_is_complete": [
    "מידע בסיסי על הילד/ה",
    "דאגה עיקרית מזוהה (תקשורת)"
  ],

  "critical_gaps": [
    {{
      "field": "concern_details",
      "importance": "critical",
      "issue": "אין דוגמאות ספציפיות - רק תיאור כללי",
      "needed_for": "video_guidelines",
      "example_question": "תני לי דוגמה מהשבוע האחרון - מה בדיוק קרה?"
    }}
  ],

  "important_gaps": [
    {{
      "field": "developmental_history",
      "importance": "important",
      "issue": "אין מידע על אבני דרך",
      "needed_for": "comprehensive_report",
      "example_question": "ספרי לי קצת על ההתפתחות - מתי התחילה ללכת? לדבר?"
    }}
  ],

  "nice_to_have_gaps": [
    {{
      "field": "strengths",
      "importance": "nice_to_have",
      "issue": "לא נאספו חוזקות",
      "needed_for": "balanced_assessment",
      "example_question": "מה מיכל אוהבת לעשות? במה היא טובה?"
    }}
  ],

  "recommendation": "continue_conversation|ready_for_video_guidelines|ready_for_report",

  "next_focus_areas": [
    "קבלת דוגמאות ספציפיות לקושי בתקשורת",
    "הבנת ההקשר היומיומי"
  ]
}}
```

## 🎯 קריטריונים לכל רמת חשיבות

**critical (קריטי)** - בלי זה לא יכולים להמשיך:
- שם ילד/ה
- גיל
- לפחות דאגה עיקרית אחת
- דוגמאות ספציפיות לדאגות (לא תיאורים כלליים!)
- הקשר מעשי (מתי/איפה זה קורה)

**important (חשוב)** - משפר משמעותית את האיכות:
- מספר דאגות (אם רלוונטי)
- חוזקות
- היסטוריה התפתחותית
- שגרה יומיומית

**nice_to_have (טוב לאסוף)** - משלים את התמונה:
- הקשר משפחתי מפורט
- מטרות הורים
- מידע נוסף על כל תחום

---

## ⚠️ חשוב - איכות מעל כמות!

- 500 תווים של "היא לא מדברת טוב והיא ככה כל הזמן..." = **לא שימושי**
- 100 תווים של "אמרתי 'תביאי לי את הכדור' והיא לא הגיבה" = **שימושי מאוד**

**הערך את התוכן, לא את האורך!**

---

צור את הערכת ההשלמות עכשיו בפורמט JSON:
"""

    return prompt
