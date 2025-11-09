"""
Artifact Generation Service - Wu Wei Architecture

Generates artifacts (guidelines, reports) when prerequisites are met.
Uses LLM to create personalized, context-aware content.

Key artifacts:
- video_guidelines: Personalized video recording instructions
- parent_report: Comprehensive assessment report (requires video analysis)
- professional_report: Clinical assessment for healthcare providers
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import time

from app.models.artifact import Artifact
from app.config.artifact_manager import get_artifact_manager

logger = logging.getLogger(__name__)


class ArtifactGenerationService:
    """
    Service for generating artifacts using LLM.

    Each artifact has:
    1. Input requirements (what data is needed)
    2. Generation logic (how to create it)
    3. Output format (markdown, JSON, etc.)
    """

    def __init__(self, llm_provider=None):
        """
        Initialize artifact generation service.

        Args:
            llm_provider: LLM provider for generation (optional, will use default if None)
        """
        self.llm_provider = llm_provider
        self.artifact_manager = get_artifact_manager()
        logger.info("ArtifactGenerationService initialized")

    async def generate_video_guidelines(
        self,
        session_data: Dict[str, Any]
    ) -> Artifact:
        """
        Generate personalized video recording guidelines.

        Wu Wei: This is triggered when knowledge is rich (qualitative check).

        Args:
            session_data: Session data including extracted_data, child info, concerns

        Returns:
            Artifact with status 'ready' or 'error'
        """
        artifact_id = "baseline_video_guidelines"
        start_time = time.time()

        logger.info(f"🎬 Generating video guidelines for child: {session_data.get('child_name', 'Unknown')}")

        # Create artifact in 'generating' state
        artifact = Artifact(
            artifact_id=artifact_id,
            artifact_type="guidelines",
            status="generating",
            content_format="markdown",
            generation_inputs={
                "child_name": session_data.get("child_name"),
                "age": session_data.get("age"),
                "primary_concerns": session_data.get("primary_concerns", []),
                "concern_details": session_data.get("concern_details"),
                "strengths": session_data.get("strengths"),
            }
        )

        try:
            # Extract key information
            child_name = session_data.get("child_name", "ילד/ה")
            age = session_data.get("age", "")
            age_str = f"{age} שנים" if age else "גיל לא צוין"

            concerns = session_data.get("primary_concerns", [])
            concern_details = session_data.get("concern_details", "")
            strengths = session_data.get("strengths", "")

            # Build generation prompt
            prompt = self._build_guidelines_prompt(
                child_name=child_name,
                age_str=age_str,
                concerns=concerns,
                concern_details=concern_details,
                strengths=strengths
            )

            # Generate using LLM (or fallback to template if no LLM)
            if self.llm_provider:
                content = await self._generate_with_llm(prompt)
            else:
                content = self._generate_guidelines_template(
                    child_name=child_name,
                    age_str=age_str,
                    concerns=concerns,
                    concern_details=concern_details
                )

            # Mark artifact as ready
            artifact.mark_ready(content)
            artifact.generation_duration_seconds = time.time() - start_time
            artifact.generation_model = getattr(self.llm_provider, "model_name", "template") if self.llm_provider else "template"

            logger.info(
                f"✅ Video guidelines generated successfully in {artifact.generation_duration_seconds:.2f}s "
                f"({len(content)} chars)"
            )

        except Exception as e:
            logger.error(f"❌ Error generating video guidelines: {e}", exc_info=True)
            artifact.mark_error(str(e))

        return artifact

    def _build_guidelines_prompt(
        self,
        child_name: str,
        age_str: str,
        concerns: list,
        concern_details: str,
        strengths: str
    ) -> str:
        """Build LLM prompt for generating video guidelines."""

        concerns_text = "\n".join(f"- {c}" for c in concerns) if concerns else "לא צוינו דאגות ספציפיות"

        return f"""
אתה מומחה בהערכה התפתחותית של ילדים. תפקידך ליצור הנחיות צילום מותאמות אישית להורה.

**מידע על הילד/ה:**
- שם: {child_name}
- גיל: {age_str}

**דאגות עיקריות:**
{concerns_text}

**פרטים נוספים על הדאגות:**
{concern_details if concern_details else "לא צוינו"}

**חוזקות:**
{strengths if strengths else "לא צוינו"}

**המשימה:**
צור הנחיות צילום מותאמות אישית בעברית שיעזרו להורה לצלם סרטונים שיסייעו בהערכה התפתחותית.

**מבנה ההנחיות:**

# הנחיות צילום מותאמות אישית עבור {child_name}

## למה חשוב לצלם?
[הסבר קצר ואישי למה הסרטונים יעזרו - בהקשר לדאגות שהועלו]

## מה לצלם? 3 מצבים מומלצים

### מצב 1: [שם המצב - רלוונטי לדאגה העיקרית]
- **מה לצלם:** [תיאור ספציפי]
- **למה חשוב:** [קשר להערכה]
- **דוגמה:** [דוגמה קונקרטית]

### מצב 2: [מצב נוסף - רלוונטי לדאגה משנית או תחום אחר]
- **מה לצלם:** [תיאור ספציפי]
- **למה חשוב:** [קשר להערכה]
- **דוגמה:** [דוגמה קונקרטית]

### מצב 3: [מצב המראה חוזקות או הקשר כללי]
- **מה לצלם:** [תיאור ספציפי]
- **למה חשוב:** [קשר להערכה]
- **דוגמה:** [דוגמה קונקרטית]

## טיפים טכניים לצילום
- [3-4 טיפים מעשיים: תאורה, זווית, אורך, רעש רקע]

## מה לא צריך לצלם
- [2-3 דברים שלא רלוונטיים או עלולים להפריע]

## הערות חשובות
- סה"כ 3 סרטונים, כל אחד 2-5 דקות
- צילום בסביבה טבעית לילד/ה
- אין צורך בהכנה מיוחדת או "הפקה"

**סגנון כתיבה:**
- חם, מעודד, אופטימי
- ברור ומעשי
- מותאם אישית לדאגות שהועלו
- ממוקד בחוזקות, לא רק בדאגות
- בעברית פשוטה וזורמת

צור את ההנחיות עכשיו:
"""

    def _generate_guidelines_template(
        self,
        child_name: str,
        age_str: str,
        concerns: list,
        concern_details: str
    ) -> str:
        """
        Generate guidelines using template (fallback when no LLM available).

        This is a reasonable default that gets personalized with child info.
        """

        # Determine primary concern area for customization
        primary_area = "התפתחות כללית"
        situation_1 = "משחק חופשי"
        situation_2 = "אינטראקציה חברתית"
        situation_3 = "פעילות יומיומית"

        if concerns:
            concern_lower = concerns[0].lower() if concerns else ""
            if "שפה" in concern_lower or "תקשורת" in concern_lower:
                primary_area = "שפה ותקשורת"
                situation_1 = "שיחה או תקשורת"
                situation_2 = "משחק עם צעצועים"
            elif "חברתי" in concern_lower or "חברה" in concern_lower:
                primary_area = "אינטראקציה חברתית"
                situation_1 = "משחק עם ילדים אחרים"
                situation_2 = "אינטראקציה עם מבוגרים"
            elif "מוטורי" in concern_lower or "תנועה" in concern_lower:
                primary_area = "מיומנויות מוטוריות"
                situation_1 = "פעילות גופנית"
                situation_2 = "משחק הדורש תנועה"

        return f"""# הנחיות צילום מותאמות אישית עבור {child_name}

## למה חשוב לצלם?

הסרטונים שתצלמ/י יעזרו לנו לקבל תמונה עשירה ומלאה על {child_name}. בגיל {age_str}, התבוננות בהתנהגויות טבעיות במצבים שונים יכולה לספק תובנות חשובות, במיוחד בהקשר ל{primary_area}.

אין צורך ב"הפקה" - אנחנו רוצים לראות את {child_name} בסביבה הטבעית, להבין את החוזקות ואת התחומים שאולי צריכים תמיכה.

## מה לצלם? 3 מצבים מומלצים

### מצב 1: {situation_1}

**מה לצלם:**
צלמ/י את {child_name} ב{situation_1} - זה יכול להיות בבית, בגן, או בכל מקום שנוח. המטרה היא לראות איך {child_name} מתנהל/ת במצב הזה.

**למה חשוב:**
מצבים כאלה מאפשרים לנו להבין את הדרך שבה {child_name} {f"מתקשר/ת ומבטא/ה צרכים" if "שפה" in primary_area else "מתקשר/ת עם הסביבה"}.

**דוגמה:**
{f"שיחה רגילה בזמן ארוחה, משחק עם צעצועים תוך כדי תקשורת, או כל מצב שבו {child_name} צריך/ה להביע משהו." if "שפה" in primary_area else f"משחק עם קוביות, פאזל, או משחק חופשי שבו {child_name} בוחר/ת את הפעילות."}

### מצב 2: {situation_2}

**מה לצלם:**
{f"אינטראקציה של {child_name} עם אחר - זה יכול להיות אח/ות, הורה, חבר/ה, או כל אדם אחר." if "חברתי" in primary_area else f"צלמ/י את {child_name} במצב שונה מהראשון - למשל, פעילות מובנית יותר או משחק מסוג אחר."}

**למה חשוב:**
זה עוזר לנו להבין את {f"המיומנויות החברתיות והאינטראקטיביות" if "חברתי" in primary_area else "הגמישות וההסתגלות של " + child_name} במצבים שונים.

**דוגמה:**
{f"משחק משותף עם ילד אחר, שיחה עם מבוגר, או כל מצב שבו {child_name} צריך/ה להגיב לאחר." if "חברתי" in primary_area else f"פעילות יצירתית, משחק עם כלי משחק מסוים, או פעילות שמעניינת את {child_name}."}

### מצב 3: פעילות יומיומית טבעית

**מה לצלם:**
כל פעילות יומיומית שבה {child_name} עוסק/ת באופן טבעי - אוכל, משחק חופשי, הכנה לשינה, וכד'.

**למה חשוב:**
מצבים טבעיים מראים את {child_name} כפי שהוא/היא באמת, ללא "הופעה" או מצב מלאכותי.

**דוגמה:**
ארוחה משפחתית, משחק בחצר, זמן קריאה, או כל רגע יומיומי שנראה אופייני.

## טיפים טכניים לצילום

📱 **זווית צילום:** צלמ/י מגובה עיניים של {child_name} כשאפשר - זה נותן תמונה טובה יותר של ההתנהגות.

💡 **תאורה:** תאורה טבעית היא הכי טובה. נסה/י לצלם באור יום או בחדר מואר.

⏱️ **אורך:** כל סרטון 2-5 דקות. אין צורך יותר - אנחנו צריכים "חלון" לעולם של {child_name}, לא סרט תיעודי שלם.

🔇 **רעש רקע:** כמה שפחות - זה עוזר לנו לשמוע ולהבין את {child_name} טוב יותר.

## מה לא צריך לצלם

❌ אין צורך במצבים "מבוימים" - אנחנו רוצים לראות את {child_name} בטבעיות.

❌ אין צורך לבקש מ{child_name} "לבצע" משימות מסוימות - זה לא מבחן.

❌ אין צורך בסרטונים ארוכים - 2-5 דקות מספיק.

## הערות חשובות

✅ **סה"כ 3 סרטונים** - כל אחד מצב שונה

✅ **סביבה טבעית** - בית, גן, פארק - כל מקום שבו {child_name} מרגיש/ה בנוח

✅ **אין הכנה מיוחדת** - {child_name} לא צריך/ה להתכונן או להתאמן

✅ **פרטיות מובטחת** - הסרטונים נשמרים בצורה מאובטחת ולא משותפים ללא הסכמה מפורשת

---

אנחנו כאן כדי לעזור! הסרטונים האלה יתנו לנו כלים להבין את {child_name} טוב יותר ולהציע המלצות מותאמות אישית.
"""

    async def _generate_with_llm(self, prompt: str) -> str:
        """
        Generate content using LLM provider.

        Args:
            prompt: Generation prompt

        Returns:
            Generated content string
        """
        # TODO: Implement LLM integration
        # For now, this would use self.llm_provider to generate
        # We'll implement this when we have LLM provider setup
        raise NotImplementedError("LLM generation not yet implemented")

    async def generate_parent_report(
        self,
        session_data: Dict[str, Any],
        video_analysis: Dict[str, Any]
    ) -> Artifact:
        """
        Generate comprehensive parent report.

        Wu Wei: This is triggered when video analysis is complete.

        Args:
            session_data: Session data including extracted_data
            video_analysis: Structured observations from video analysis

        Returns:
            Artifact with status 'ready' or 'error'
        """
        artifact_id = "baseline_parent_report"
        start_time = time.time()

        logger.info(f"📋 Generating parent report for: {session_data.get('child_name', 'Unknown')}")

        artifact = Artifact(
            artifact_id=artifact_id,
            artifact_type="report",
            status="generating",
            content_format="markdown",
            generation_inputs={
                "child_name": session_data.get("child_name"),
                "video_analysis": video_analysis,
                "extracted_data": session_data.get("extracted_data", {})
            }
        )

        try:
            # TODO: Implement parent report generation
            # For now, create placeholder
            content = self._generate_parent_report_placeholder(
                child_name=session_data.get("child_name", "ילד/ה"),
                session_data=session_data
            )

            artifact.mark_ready(content)
            artifact.generation_duration_seconds = time.time() - start_time

            logger.info(f"✅ Parent report generated successfully in {artifact.generation_duration_seconds:.2f}s")

        except Exception as e:
            logger.error(f"❌ Error generating parent report: {e}", exc_info=True)
            artifact.mark_error(str(e))

        return artifact

    def _generate_parent_report_placeholder(
        self,
        child_name: str,
        session_data: Dict[str, Any]
    ) -> str:
        """Generate placeholder parent report."""
        return f"""# דוח הערכה התפתחותית - {child_name}

## סיכום מנהלים

[דוח זה ייווצר לאחר ניתוח הסרטונים]

## פרופיל הילד/ה

**שם:** {child_name}
**גיל:** {session_data.get('age', 'לא צוין')}

## תצפיות התפתחותיות

[תצפיות יווצרו מניתוח הסרטונים]

## תחומי חוזקה

[יזוהו מהסרטונים והשיחה]

## תחומים לתמיכה

[יזוהו מהסרטונים והשיחה]

## המלצות

[המלצות מותאמות אישית]

---

*דוח זה נוצר בתאריך: {datetime.now().strftime('%d/%m/%Y')}*
"""
