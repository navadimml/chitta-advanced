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
import os
from typing import Dict, Any, Optional
from datetime import datetime
import time

from app.models.artifact import Artifact
from app.config.artifact_manager import get_artifact_manager
from app.services.llm.factory import create_llm_provider

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
            llm_provider: LLM provider for generation (optional, will create strong LLM if None)
        """
        if llm_provider is None:
            # 🌟 Create strong LLM specifically for artifact generation
            # This ensures high-quality output for guidelines, reports, etc.
            strong_model = os.getenv("STRONG_LLM_MODEL", "gemini-3-pro-preview")
            provider_type = os.getenv("LLM_PROVIDER", "gemini")

            logger.info(f"🧠 Creating strong LLM for artifact generation: {strong_model}")
            self.llm_provider = create_llm_provider(
                provider_type=provider_type,
                model=strong_model,
                use_enhanced=False  # Strong models don't need enhanced mode
            )
        else:
            self.llm_provider = llm_provider

        self.artifact_manager = get_artifact_manager()
        logger.info(f"ArtifactGenerationService initialized with model: {getattr(self.llm_provider, 'model_name', 'unknown')}")

    async def generate_interview_summary(
        self,
        artifact_id: str,
        session_data: Dict[str, Any],
        **kwargs
    ) -> Artifact:
        """
        🌟 Wu Wei: Generate comprehensive interview summary (formerly Stage 1).

        Extracts structured clinical data + parent persona from conversation transcript.
        This holistic summary captures:
        1. Clinical Data: difficulties, strengths, development
        2. Parent Persona: emotional vibe, vocabulary, communication style
        3. Contextual Assets: specific names, toys, places mentioned

        Used by: video_guidelines, video_analysis, professional_report

        Args:
            artifact_id: Artifact identifier (baseline_interview_summary, etc.)
            session_data: Session data with conversation_history, extracted_data
            **kwargs: Additional parameters from config

        Returns:
            Artifact with status 'ready' or 'error'
        """
        from app.services.llm.base import Message
        import json

        start_time = time.time()
        logger.info(f"📝 Generating interview summary: {artifact_id}")

        conversation_history = session_data.get("conversation_history", [])
        child_name = session_data.get("child_name", "ילד/ה")

        artifact = Artifact(
            artifact_id=artifact_id,
            artifact_type="analysis",
            status="generating",
            content_format="json",
            generation_inputs={
                "child_name": child_name,
                "conversation_turns": len(conversation_history)
            }
        )

        try:
            # Build transcript from conversation history
            transcript = self._build_transcript(conversation_history)

            # Build extraction prompt with holistic parent persona layer
            stage1_prompt_text = f"""# Stage 1: Extract Clinical Data & Parent Persona

## Role
You are a clinical psychologist specializing in child development interviews. You listen not just for symptoms, but for the "Voice of the Parent."

## Task
Extract and structure all information from the transcript. **Preserve parent quotes in Hebrew exactly as spoken.**

This has THREE layers:
1. **Clinical Data:** Specific difficulties, strengths, development (standard extraction)
2. **Parent Persona:** Emotional state, vocabulary, communication style
3. **Contextual Assets:** Specific names, toys, places mentioned

## Critical Instructions

### Clinical Data (Standard Extraction)
✅ Copy exact parent quotes in Hebrew
✅ Include at least 2-3 specific examples per difficulty
✅ Extract strengths, development history, school info
✅ Preserve Hebrew text exactly - spelling, grammar, colloquialisms

### Parent Persona (Holistic Layer)
✅ **Emotional Vibe:** Diagnose parent's state (e.g., "חרדה ומחפשת אישור", "מתוסכלת אך מעשית", "בהכחשה")
✅ **Vocabulary Mirroring:** Identify specific HEBREW words parent uses for behaviors
   - If they say "הוא מתפוצץ" (He explodes), map "Tantrum" -> "מתפוצץ"
   - If they say "הוא מרחף" (He hovers/zones out), map "Inattention" -> "מרחף"
   - This map will be used to personalize guidelines
✅ **Contextual Assets:** List specific items/people mentioned (e.g., "סבתא רחל", "לגו נינג'ה גו", "השטיח האדום בסלון")

### Rules
❌ Don't invent information not in transcript
❌ Don't interpret or analyze - just summarize
❌ Don't translate Hebrew to English
❌ Don't modify parent's words

## Interview Transcript

{transcript}
"""

            # Get structured output using Gemini's native JSON mode
            logger.info("🔍 Extracting clinical data + parent persona from transcript...")
            extracted_data = await self.llm_provider.chat_with_structured_output(
                messages=[Message(role="user", content=stage1_prompt_text)],
                response_schema=self._get_stage1_extraction_schema(),
                temperature=0.1
            )

            logger.info(f"✅ Interview summary extracted: Parent Vibe = {extracted_data.get('parent_emotional_vibe', 'N/A')}")
            logger.info("=" * 80)
            logger.info("📊 INTERVIEW SUMMARY OUTPUT (Clinical Data + Parent Persona):")
            logger.info(json.dumps(extracted_data, ensure_ascii=False, indent=2))
            logger.info("=" * 80)

            # Convert to JSON string
            content = json.dumps(extracted_data, ensure_ascii=False, indent=2)

            artifact.mark_ready(content)
            artifact.generation_duration_seconds = time.time() - start_time
            artifact.generation_model = getattr(self.llm_provider, "model_name", "unknown")

            logger.info(f"✅ Interview summary generated in {artifact.generation_duration_seconds:.2f}s")

        except Exception as e:
            logger.error(f"❌ Error generating interview summary: {e}", exc_info=True)
            artifact.mark_error(str(e))

        return artifact

    async def generate_video_guidelines(
        self,
        artifact_id: str,
        session_data: Dict[str, Any],
        **kwargs
    ) -> Artifact:
        """
        🌟 Wu Wei: Generate personalized video recording guidelines from interview_summary artifact.

        Requires: baseline_interview_summary artifact (contains clinical data + parent persona)
        Generates: Video filming instructions with analyst_context for video analysis

        This method now ONLY does Stage 2 (guideline generation).
        Stage 1 (interview summary extraction) is a separate artifact.

        Args:
            artifact_id: Artifact identifier (baseline_video_guidelines, re_assessment_video_guidelines, etc.)
            session_data: Session data including artifacts dictionary
            **kwargs: Additional parameters from config (interview_summary_source)

        Returns:
            Artifact with status 'ready' or 'error'
        """
        start_time = time.time()

        logger.info(f"🎬 Generating video guidelines: {artifact_id} for child: {session_data.get('child_name', 'Unknown')}")

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
            # 🌟 Wu Wei: Load interview_summary artifact (required dependency)
            interview_summary_source = kwargs.get("interview_summary_source", "baseline_interview_summary")
            interview_summary_artifact = session_data.get("artifacts", {}).get(interview_summary_source)

            if not interview_summary_artifact or not interview_summary_artifact.get("exists"):
                error_msg = f"Cannot generate video guidelines: {interview_summary_source} not available"
                logger.error(f"❌ {error_msg}")
                artifact.mark_error(error_msg)
                return artifact

            # Parse interview summary content
            import json
            if isinstance(interview_summary_artifact.get("content"), str):
                interview_summary = json.loads(interview_summary_artifact.get("content"))
            else:
                interview_summary = interview_summary_artifact.get("content")

            logger.info(f"✅ Loaded interview summary from {interview_summary_source}")

            # Generate using LLM with interview summary
            if self.llm_provider:
                logger.info("📝 Generating video guidelines from interview summary")
                content = await self._generate_guidelines_with_llm(interview_summary)
            else:
                logger.info("📝 Using template generation (no LLM provider)")
                # Fallback to template only if no LLM provider
                child_name = session_data.get("child_name", "ילד/ה")
                age = session_data.get("age", "")
                age_str = f"{age} שנים" if age else "גיל לא צוין"
                concerns = session_data.get("primary_concerns", [])
                concern_details = session_data.get("concern_details", "")

                template_content = self._generate_guidelines_template(
                    child_name=child_name,
                    age_str=age_str,
                    concerns=concerns,
                    concern_details=concern_details
                )

                # Convert to JSON format
                content = self._convert_template_to_json_format(
                    template_content,
                    child_name,
                    age_str
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

    async def _generate_guidelines_with_llm(
        self,
        interview_summary: Dict[str, Any]
    ) -> str:
        """
        🌟 Wu Wei: Generate video guidelines from interview_summary artifact (Stage 2 only).

        Previously this method did Stage 1 (extraction) + Stage 2 (generation).
        Now Stage 1 is a separate artifact (baseline_interview_summary), and this method
        only does Stage 2 using the summary.

        This holistic approach uses parent persona data to create anxiety-reducing,
        personalized guidelines that mirror the parent's language.

        Args:
            interview_summary: Interview summary artifact content (clinical data + parent persona)

        Returns:
            JSON structured video guidelines in Hebrew with embedded analyst_context for video analysis
        """
        from app.services.llm.base import Message
        import json

        logger.info("📝 Generating empathetic video guidelines from interview summary")
        logger.info(f"✅ Using existing interview summary: Parent Vibe = {interview_summary.get('parent_emotional_vibe', 'N/A')}")

        # Extract persona data for personalization from interview_summary
        parent_vibe = interview_summary.get('parent_emotional_vibe', 'לא זוהה')

        # Convert vocab_map from array format to dict for easier use
        vocab_map_array = interview_summary.get('specific_vocabulary_map', [])
        vocab_map = {item['clinical_term']: item['parent_word'] for item in vocab_map_array} if vocab_map_array else {}

        context_assets = interview_summary.get('family_context_assets', [])
        child_name = interview_summary.get('child', {}).get('name', 'הילד/ה')

        json_input = json.dumps(interview_summary, ensure_ascii=False, indent=2)
        stage2_prompt_text = f"""# Stage 2: Generate Empathetic Video Guidelines (Hebrew)

## Role
You are "Chitta," a supportive child development expert writing directly to the Israeli parent in Hebrew.
**Your Goal:** Lower their anxiety while getting high-quality video data for analysis.

## Parent Context (Use This!)
**Parent Vibe:** {parent_vibe}
**Child Name:** {child_name}
**Parent's Vocabulary:** {json.dumps(vocab_map, ensure_ascii=False)}
**Context Assets:** {json.dumps(context_assets, ensure_ascii=False)}

## Critical Instructions for Writing Guidelines

### 1. CONCRETE & SIMPLE (Lower Cognitive Load)
❌ BAD: "שחקו משחק עם חוקים ותורות"
✅ GOOD: "שבו ליד השולחן במטבח, בחרו משחק סולמות וחבלים או זיכרון (קלפים). שחקו יחד 5 דקות."

❌ BAD: "צלמו פעילות יצירתית"
✅ GOOD: "הניחו דף A4 ועפרונות צבעוניים על השולחן. בקשו ממנה לצייר משפחה או בית. צלמו אותה בזמן הציור."

### 2. The "Sandwich" Rationale (Emotional Regulation for Parents)
The `rationale_for_parent` must follow this structure in Hebrew:
1. **Validate:** "שמעתי כמה הבקרים שלכם עמוסים..." (I heard how exhausting mornings are...)
2. **Explain:** "צילום של רגע כזה יעזור לנו להבין בדיוק מה הטריגר..." (Filming this helps us see the trigger...)
3. **Reassure:** "אל תדאגו מ'לסדר' את המצב למצלמה. אנחנו רוצים לראות את החיים האמיתיים." (Don't worry about fixing it...)

For strength_baseline scenarios, emphasize validation and completeness:
- "ראיתי שהוא מצטיין ב... (I saw he excels at...)
- "סרטון של הרגעים הטובים יעזור לנו לראות מה עובד ולבנות על זה..."
- "זה חלק חשוב מהתמונה השלמה"

### 3. Vocabulary Mirroring (CRITICAL)
Use the **Vocabulary Map** above.
- If parent uses "התקף" (Attack), YOU use "התקף" in instructions
- If parent uses "מרחף" (Zones out), YOU use "מרחף"
- Don't use clinical jargon unless parent used it

### 4. Use Contextual Assets
- Do NOT say: "שחקו עם צעצוע" (Play with a toy)
- DO say: "שבו על {context_assets[0] if context_assets else 'השטיח'} עם ה{context_assets[1] if len(context_assets) > 1 else 'צעצוע האהוב'}..."
- Make `example_situations` specific to their mentioned environment

### 5. Focus Points (focus_points) are INTERNAL ONLY
These are for YOU to analyze the video later. NOT for parents to worry about while filming.
Write them as clinical observation notes: "האם נראית תנועת יתר?", "כמה זמן מחזיקה קשב?"

### 6. Example Situations Must Be Concrete
❌ "זמן משחק חופשי"
✅ "בסלון אחרי הצהריים, עם הצעצועים שיש לה בארון"

## Task
1. Identify 1-2 main reported difficulties from the parent's descriptions
2. Infer 1-2 additional areas to check (comorbidities) based on clinical framework below
3. **INCLUDE 1 strength/baseline scenario** - Show the child when regulated and thriving
4. Create **EXACTLY 3-4 video filming guidelines** in Hebrew (minimum 3, maximum 5)

**CRITICAL REQUIREMENT:** You MUST generate at least 3 complete video_guidelines entries:
- At least 1 must be category: "reported_difficulty"
- At least 1 must be category: "strength_baseline" (REQUIRED - strengths-based approach)
- Optionally 1-2 can be category: "comorbidity_check"

## Field Usage by Category

### For "reported_difficulty" and "comorbidity_check":
- difficulty_area: Problem area in Hebrew (e.g., "קשב במשחקים", "ויסות רגשי")

### For "strength_baseline":
- difficulty_area: Strength domain in Hebrew (e.g., "משחק עצמאי", "יצירתיות", "אינטראקציה חברתית")

Each guideline must have:
- Unique id (1, 2, 3, etc.)
- Category (reported_difficulty, comorbidity_check, or strength_baseline)
- difficulty_area: Context-sensitive (problem area OR strength domain)
- title: Short title in Hebrew (3-5 words)
- instruction: CONCRETE, SIMPLE filming instruction using parent's vocabulary
- example_situations: 2-3 CONCRETE situations using their mentioned context
- duration_suggestion: Clear time estimate ("5-7 דקות", "עד שהיא מאבדת עניין")
- focus_points: 2-4 INTERNAL analysis points (clinical observation notes)
- rationale_for_parent: "Sandwich" structure (Validate-Explain-Reassure) in Hebrew

## Clinical Comorbidity Framework

**ADHD/Attention** → Check: Sensory regulation, fine motor, emotional regulation
**Learning difficulties** → Check: Visual perception, auditory processing, working memory
**Social/communication** → Check: Symbolic play, restricted interests, repetitive behaviors
**Emotional outbursts** → Check: Sensory triggers, language comprehension, frustration tolerance
**Language delays** → Check: Social interactions, imaginative play, non-verbal communication

## Structured Data from Interview

{json_input}

## Example of GOOD Difficulty Guideline

{{
  "id": 1,
  "category": "reported_difficulty",
  "difficulty_area": "קשב במשחקים",
  "title": "משחק קופסה במטבח",
  "instruction": "שבו יחד ליד שולחן המטבח. בחרו משחק קופסה פשוט שהילדה מכירה - סולמות וחבלים, דמקה, או זיכרון. שחקו יחד 5-7 דקות, או עד שהיא מאבדת עניין. אם היא קמה או מפסיקה - זה בסדר, המשיכו לצלם עוד דקה כדי לראות לאן היא הולכת.",
  "example_situations": [
    "אחרי ארוחת צהריים, ליד שולחן המטבח",
    "בערב לפני האמבטיה, בסלון על השטיח"
  ],
  "duration_suggestion": "5-7 דקות",
  "focus_points": [
    "כמה זמן היא מחזיקה קשב לפני התנועה הראשונה מהכיסא?",
    "מה היא עושה בזמן ההמתנה לתור - מסתכלת, זזה, מדברת?",
    "איך היא מגיבה כשמזכירים לה לחזור למשחק?"
  ],
  "rationale_for_parent": "שמעתי שהיא מתקשה לחכות לתורה במשחקים וש'המחשבות שלה בורחות' - זה בטח מאתגר בשבילכם. סרטון זה יעזור לנו לראות בדיוק איך זה נראה - האם זה קושי בבלימה, קושי בהמתנה, או משהו אחר. אל תדאגו לגרום למשחק להיראות 'מושלם' - אנחנו רוצים לראות את המציאות. זה יכוון אותנו איך לעזור לה בכיתה א'."
}}

## Example of GOOD Strength Guideline

{{
  "id": 3,
  "category": "strength_baseline",
  "difficulty_area": "משחק יצירתי",
  "title": "זמן יצירה חופשית",
  "instruction": "תנו לה דף ריק וצבעים, ותנו לה לצייר או ליצור מה שהיא רוצה. צלמו 5 דקות של יצירה חופשית.",
  "example_situations": [
    "אחר הצהריים בפינת היצירה",
    "בשולחן המטבח עם עפרונות צבעוניים"
  ],
  "duration_suggestion": "5 דקות",
  "focus_points": [
    "כמה זמן היא נשארת ממוקדת בפעילות?",
    "איך היא מתמודדת עם החומרים?",
    "האם יש יצירתיות ודמיון?"
  ],
  "rationale_for_parent": "שמעתי שהיא אוהבת לצייר וליצור - זה חוזקה אמיתית! סרטון של הרגעים שבהם היא שקועה ביצירה יעזור לנו להבין מה עובד טוב ולבנות על זה. התמונה השלמה כוללת גם את מה שהיא עושה נהדר."
}}
"""

        # Get structured output using Gemini's native JSON mode
        try:
            guidelines_data = await self.llm_provider.chat_with_structured_output(
                messages=[Message(role="user", content=stage2_prompt_text)],
                response_schema=self._get_stage2_guidelines_schema(),
                temperature=0.7
            )
            logger.info(f"✅ Stage 2 complete: Generated guidelines using native JSON mode")
            logger.info("=" * 80)
            logger.info("📊 STAGE 2 OUTPUT (Generated Guidelines):")
            logger.info(json.dumps(guidelines_data, ensure_ascii=False, indent=2))
            logger.info("=" * 80)

            # CRITICAL VALIDATION: Gemini schema constraints are HINTS, not enforced!
            # We must validate the output ourselves to ensure it meets requirements
            video_guidelines = guidelines_data.get("video_guidelines", [])
            if len(video_guidelines) < 3:
                error_msg = f"Validation failed: Generated only {len(video_guidelines)} guidelines, minimum 3 required"
                logger.error(f"❌ {error_msg}")
                logger.error(f"Guidelines data: {json.dumps(guidelines_data, ensure_ascii=False)[:500]}")
                raise ValueError(error_msg)

            logger.info(f"✅ Validation passed: {len(video_guidelines)} guidelines generated")

        except Exception as e:
            logger.error(f"❌ Stage 2 failed: {e}")
            raise ValueError(f"Failed to generate guidelines: {e}")

        # Convert JSON to markdown format for parent
        markdown_content = self._convert_guidelines_json_to_markdown(guidelines_data)

        # Also transform to component-compatible format for frontend
        component_format = self._transform_to_component_format(guidelines_data)

        # Enrich with analyst context for video analysis (Bridge to Observation Agent)
        guidelines_list = guidelines_data.get("video_guidelines", [])
        for idx, scenario in enumerate(component_format.get("scenarios", [])):
            if idx < len(guidelines_list):
                guideline = guidelines_list[idx]
                scenario["analyst_context"] = {
                    "instruction_given_to_parent": scenario.get("what_to_film", ""),
                    "internal_focus_points": guideline.get("focus_points", []),
                    "parent_persona_data": {
                        "emotional_vibe": extracted_data.get("parent_emotional_vibe", ""),
                        "vocabulary_map": extracted_data.get("specific_vocabulary_map", []),  # Array format
                        "context_assets": extracted_data.get("family_context_assets", [])
                    },
                    "clinical_goal": guideline.get("category", "")
                }

        logger.info(f"✅ Holistic generation complete: {len(markdown_content)} chars markdown")
        logger.info(f"📊 Component format: {len(component_format.get('scenarios', []))} scenarios generated")
        logger.info(f"🎯 Analyst context embedded in all scenarios for video analysis")
        logger.debug(f"Guidelines data keys: {guidelines_data.keys()}")
        logger.debug(f"Video guidelines count: {len(guidelines_data.get('video_guidelines', []))}")

        # Return structured format (not markdown) for the component
        return json.dumps(component_format, ensure_ascii=False)

    def _build_transcript(self, conversation_history: list) -> str:
        """Build interview transcript from conversation history."""
        transcript_lines = []

        for turn in conversation_history:
            role = turn.get("role", "unknown")
            content = turn.get("content", "")

            if role == "user":
                transcript_lines.append(f"הורה: {content}")
            elif role == "assistant":
                transcript_lines.append(f"Chitta: {content}")

        return "\n\n".join(transcript_lines)

    def _build_stage1_extraction_prompt(self, transcript: str) -> str:
        """Build Stage 1 prompt for extracting structured data from transcript."""
        return f"""# Chitta Stage 1: JSON Extraction (English Prompt)

## Role
You are a clinical data analyst specializing in child development interviews. Your task is to extract and structure information from parent interviews into JSON format.

## Task
Read the interview transcript and produce a structured JSON with all relevant information. **Preserve all parent quotes in Hebrew exactly as spoken.**

## JSON Schema

```json
{{
  "child": {{
    "name": "",
    "age_years": 0,
    "age_months": 0,
    "gender": ""
  }},

  "main_concern": "Main presenting problem in parent's own words (Hebrew)",

  "difficulties": [
    {{
      "area": "attention|behavior|communication|sensory|emotional|social|learning|motor|sleep|eating|visual|auditory",
      "description": "Detailed description in parent's words (Hebrew)",
      "specific_examples": [
        {{
          "when_where": "When and where it occurs (Hebrew)",
          "behavior": "Exact behavior observed - what child does/says (Hebrew)",
          "trigger": "What triggers it, if known (Hebrew)",
          "frequency": "How often and intensity (Hebrew)",
          "duration": "How long each episode lasts (Hebrew)"
        }}
      ],
      "duration_since_onset": "How long the difficulty has existed (Hebrew)",
      "impact_child": "Impact on child's functioning (Hebrew)",
      "impact_family": "Impact on parent/family (Hebrew)"
    }}
  ],

  "strengths": {{
    "likes": ["What child likes doing (Hebrew)"],
    "good_at": ["What child is good at (Hebrew)"],
    "positives": "Positive observations (Hebrew)"
  }},

  "development": {{
    "pregnancy_birth": "Pregnancy/birth complications if any (Hebrew)",
    "milestones": "Developmental delays if any (Hebrew)",
    "medical": "Chronic conditions/medications/medical events (Hebrew)"
  }},

  "school": {{
    "type": "Preschool/school/special ed (Hebrew)",
    "adjustment": "How child is doing (Hebrew)",
    "support": "Support services received (Hebrew)"
  }},

  "history": {{
    "previous_diagnosis": "Previous diagnoses (Hebrew)",
    "previous_treatment": "Previous treatments and their effectiveness (Hebrew)",
    "family_history": "Similar difficulties in family (Hebrew)"
  }},

  "parent_perspective": {{
    "childs_experience": "What parent thinks child is experiencing (Hebrew)",
    "what_tried": "What parent tried and what worked/didn't (Hebrew)",
    "hopes": "Parent's hopes and expectations (Hebrew)"
  }}
}}
```

## Working Rules

### DO:
✅ Copy exact parent quotes in Hebrew (use quotation marks for direct quotes)
✅ Include **at least 2-3 specific examples** per difficulty
✅ If information is missing → leave `null` or empty string
✅ Maintain valid JSON syntax (critical!)
✅ Be concise but comprehensive
✅ Preserve Hebrew text exactly - including spelling, grammar, colloquialisms

### DON'T:
❌ Don't invent information not in transcript
❌ Don't interpret or analyze - just summarize
❌ Don't add clinical comments
❌ Don't translate Hebrew to English
❌ Don't modify parent's words
❌ Don't add fields not in schema

## Output Format
Return **ONLY** the JSON, no additional text.

Make sure:
- JSON is valid (check syntax carefully)
- All strings are properly escaped
- Hebrew text is preserved
- No trailing commas

---

## Input

The interview transcript will appear after `[TRANSCRIPT]`:

[TRANSCRIPT]
{transcript}
"""

    def _build_stage2_guidelines_prompt(self, extracted_data: dict) -> str:
        """Build Stage 2 prompt for generating guidelines from structured data."""
        import json
        json_input = json.dumps(extracted_data, ensure_ascii=False, indent=2)

        return f"""# Chitta Stage 2: Video Guidelines Generation (English Prompt)

## Role
You are a clinical expert in child development. You receive structured JSON from a parent interview and generate smart video filming guidelines.

## Task
1. Identify 1-2 main reported difficulties
2. Infer 1-2 additional areas to check (comorbidities)
3. Create 3-4 clear, sensitive filming guidelines
4. Output as JSON with Hebrew text for parents

---

## Clinical Framework

### Common Comorbidities:

**ADHD (attention/hyperactivity)** → Check:
- Sensory regulation (noise, touch, light sensitivity)
- Fine motor coordination (writing, cutting)
- Emotional regulation (frustration, transitions)

**Learning difficulties (reading/writing/math)** → Check:
- Eye tracking and visual perception
- Auditory processing and comprehension
- Working memory

**Social/communication difficulties** → Check:
- Symbolic play and imagination
- Restricted interests
- Repetitive behaviors/movements
- Unusual sensory responses

**Emotional outbursts/regulation** → Check:
- Sensory triggers
- Language comprehension (complex instructions)
- Parent-child dynamics

**Language delays** → Check:
- Social interactions
- Imaginative play
- Non-verbal communication

---

## Output JSON Schema

```json
{{
  "parent_greeting": {{
    "parent_name": "שם ההורה (if available from extracted data, else 'הורה יקר')",
    "child_name": "USE CHILD_NAME FROM EXTRACTED DATA ABOVE - שם הילד/ה מהנתונים שמעל",
    "opening_message": "פסקת פתיחה מלאה בעברית - תודה על השיחה, הסבר קצר על מטרת הסרטונים"
  }},

  "general_filming_tips": [
    "צילום טבעי - אל תבקשו מהילד לעשות משהו מיוחד",
    "1-2 דקות לכל סרטון",
    "מיקוד על פני וגוף הילד",
    "סודיות מלאה - הכל נשמר באפליקציה בלבד"
  ],

  "video_guidelines": [
    {{
      "id": 1,
      "category": "reported_difficulty",
      "difficulty_area": "attention|behavior|communication|sensory|emotional|social|learning|motor",
      "title": "כותרת קצרה ותיאורית בעברית",
      "instruction": "הנחיית צילום מפורטת וספציפית בעברית - מה לצלם, איך, באיזה מצב",
      "example_situations": [
        "דוגמה קונקרטית 1 למצב טבעי לצלם",
        "דוגמה קונקרטית 2"
      ],
      "duration_suggestion": "1-2 דקות",
      "focus_points": [
        "על מה להתמקד בצילום - נקודה 1",
        "נקודה 2"
      ]
    }},
    {{
      "id": 2,
      "category": "reported_difficulty",
      "difficulty_area": "...",
      "title": "...",
      "instruction": "...",
      "example_situations": ["..."],
      "duration_suggestion": "1-2 דקות",
      "focus_points": ["..."]
    }},
    {{
      "id": 3,
      "category": "comorbidity_check",
      "related_to": "attention|behavior|...",
      "suspected_area": "sensory|motor|social|...",
      "title": "כותרת רגישה בעברית",
      "instruction": "הנחיית צילום עם ניסוח רך ומזמין בעברית. השתמש בביטויים כמו: 'כדי להשלים את התמונה', 'לפעמים X קשור גם ל-Y', 'אם תשימו לב ל...'",
      "rationale_for_parent": "הסבר קצר ולא-טכני למה זה רלוונטי (אופציונלי)",
      "example_situations": ["דוגמה קונקרטית"],
      "duration_suggestion": "1-2 דקות",
      "focus_points": ["..."]
    }},
    {{
      "id": 4,
      "category": "comorbidity_check",
      "related_to": "...",
      "suspected_area": "...",
      "title": "...",
      "instruction": "...",
      "rationale_for_parent": "...",
      "example_situations": ["..."],
      "duration_suggestion": "1-2 דקות",
      "focus_points": ["..."]
    }}
  ],

  "closing_message": "תודה רבה על שיתוף הפעולה, זה יעזור לנו להבין את [child_name] לעומק!"
}}
```

---

## Guidelines Creation Process

### Step 1: Analyze the JSON
```
What are the 2 most prominent, clearly described difficulties?
→ These become guidelines #1-2 (category: "reported_difficulty")

What comorbidities are likely based on the reported difficulties?
→ Select 1-2 additional areas that are clinically suspicious
→ These become guidelines #3-4 (category: "comorbidity_check")
```

### Step 2: Build Each Guideline

**For each guideline:**
1. **Clear title** - what to film (Hebrew)
2. **Specific instruction** - how to film, in what context (Hebrew)
3. **Concrete examples** - natural situations to capture (Hebrew)
4. **Focus points** - what behaviors/aspects to capture (Hebrew)

**Phrasing rules:**
- 🎯 Action-oriented, specific instructions, not general descriptions
- 🤝 Containing, non-judgmental tone
- 🔍 For comorbidity checks: gentle, inviting language
- 📏 Maximum 4 guidelines total (3 is often ideal)

---

## Critical Rules

### ✅ DO:
- Use child's name throughout the Hebrew text
- Provide specific instructions ("film during homework" not "film learning")
- Give concrete examples ("when doing puzzles, building blocks")
- Keep tone warm and collaborative
- Limit to 3-4 guidelines (don't overwhelm parent)
- Return valid JSON (check syntax!)

### ❌ DON'T:
- Never suggest diagnoses ("check for autism")
- Don't use professional jargon
- Don't overwhelm parent (max 4 guidelines)
- Don't be judgmental or alarming
- Don't create vague instructions
- Don't output anything except the JSON

---

## Sensitive Phrasing Examples (for comorbidity checks)

**Good examples (use these patterns):**
- "כדי להשלים את התמונה הרחבה ביותר, נשמח לראות..."
- "לפעמים קשיים ב-X קשורים גם ל-Y. אם תשימו לב ל-Z, יהיה מועיל לראות..."
- "אפילו אם זה לא נראה כבעיה מרכזית, זה יעזור לנו להבין..."
- "כדי שנוכל לתת את המענה המדויק ביותר, נשמח גם לראות..."

**Bad examples (avoid these):**
- "בדקו אם הילד מראה סימני אוטיזם"
- "אנחנו חושבים שיש בעיה גם ב-X"
- "זה יכול להיות חמור"

---

## Output Format
Return **ONLY** the JSON, no additional text.

Ensure:
- Valid JSON syntax
- All Hebrew strings properly escaped
- Exactly 3-4 video_guidelines (not more, not less)
- At least 1 reported_difficulty category
- At least 1 comorbidity_check category (unless only 1 difficulty was reported)
- Professional yet warm Hebrew text

---

## Input

The extracted JSON will appear here:

```json
{json_input}
```
"""

    def _convert_guidelines_json_to_markdown(self, guidelines_data: dict) -> str:
        """Convert guidelines JSON to markdown format for parents."""
        md = []

        # Parent greeting
        greeting = guidelines_data.get("parent_greeting", {})
        child_name = greeting.get("child_name", "")
        opening = greeting.get("opening_message", "")

        md.append(f"# הנחיות צילום מותאמות אישית עבור {child_name}\n")
        md.append(f"{opening}\n")

        # General tips
        md.append("## טיפים כלליים לצילום\n")
        for tip in guidelines_data.get("general_filming_tips", []):
            md.append(f"- {tip}")
        md.append("")

        # Video guidelines
        md.append("## מה לצלם?\n")
        for guideline in guidelines_data.get("video_guidelines", []):
            gid = guideline.get("id", "")
            title = guideline.get("title", "")
            instruction = guideline.get("instruction", "")
            examples = guideline.get("example_situations", [])
            focus = guideline.get("focus_points", [])
            duration = guideline.get("duration_suggestion", "1-2 דקות")

            md.append(f"### סרטון {gid}: {title}\n")
            md.append(f"**הנחיה:** {instruction}\n")

            if examples:
                md.append("**דוגמאות למצבים:**")
                for ex in examples:
                    md.append(f"- {ex}")
                md.append("")

            if focus:
                md.append("**על מה להתמקד:**")
                for f in focus:
                    md.append(f"- {f}")
                md.append("")

            md.append(f"**משך:** {duration}\n")

        # Closing
        closing = guidelines_data.get("closing_message", "")
        md.append(f"---\n\n{closing}")

        return "\n".join(md)

    def _transform_to_component_format(self, guidelines_data: dict) -> dict:
        """
        Transform LLM-generated JSON to VideoGuidelinesView component format.

        LLM Format:
        - video_guidelines: [{ id, title, instruction, example_situations, focus_points, rationale_for_parent }]
        - general_filming_tips: [...]
        - parent_greeting.opening_message

        Component Format:
        - scenarios: [{ title, context, what_to_film, what_to_look_for, duration, why_matters }]
        - general_tips: [...]
        - introduction: string

        IMPORTANT: Field usage for frontend display:
        - why_matters (rationale_for_parent): MUST be displayed to parents in ALL scenarios as "למה זה חשוב:"
        - what_to_look_for (focus_points): INTERNAL USE ONLY - for team analysis, NOT for parent display
        """
        video_guidelines = guidelines_data.get("video_guidelines", [])
        parent_greeting = guidelines_data.get("parent_greeting", {})

        # Transform video_guidelines to scenarios
        scenarios = []
        for guideline in video_guidelines:
            # Build context from difficulty area (short label, not the full rationale)
            # The full rationale goes in why_matters to avoid duplication
            context = guideline.get("difficulty_area", f"תרחיש {guideline.get('id')}")

            # Build scenario object
            scenario = {
                "title": guideline.get("title", ""),
                "context": context,
                "what_to_film": guideline.get("instruction", ""),
                "what_to_look_for": guideline.get("focus_points", []),  # Internal use - not for display
                "duration": guideline.get("duration_suggestion", "1-2 דקות"),
                "why_matters": guideline.get("rationale_for_parent", "")  # Always include for ALL scenarios
            }

            # Add example situations as additional context
            examples = guideline.get("example_situations", [])
            if examples:
                scenario["examples"] = examples

            scenarios.append(scenario)

        return {
            "introduction": parent_greeting.get("opening_message", ""),
            "scenarios": scenarios,
            "general_tips": guidelines_data.get("general_filming_tips", []),
            "estimated_duration": "1-2 דקות לסרטון",
            "child_name": parent_greeting.get("child_name", "")
        }

    def _strip_markdown_code_blocks(self, text: str) -> str:
        """
        Strip markdown code blocks from LLM output.
        LLMs often wrap JSON in ```json ... ``` or ``` ... ``` blocks.

        Args:
            text: Raw text from LLM that may contain markdown code blocks

        Returns:
            Cleaned text with markdown wrappers removed
        """
        import re

        if not text:
            return text

        text = text.strip()

        # Try multiple patterns to handle different markdown formats
        patterns = [
            # Pattern 1: ```json\n...\n```
            r'^```json\s*\n(.*?)\n```$',
            # Pattern 2: ```\n...\n```
            r'^```\s*\n(.*?)\n```$',
            # Pattern 3: ``` json\n...\n``` (space after backticks)
            r'^```\s+json\s*\n(.*?)\n```$',
            # Pattern 4: More permissive - any backticks with optional json
            r'```(?:json)?\s*(.*?)\s*```',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                extracted = match.group(1).strip()
                if extracted:  # Only return if we got non-empty content
                    return extracted

        # No markdown blocks found, return original text
        return text

    def _convert_template_to_json_format(
        self,
        markdown_content: str,
        child_name: str,
        age_str: str
    ) -> str:
        """
        Convert template markdown to JSON format expected by frontend.

        This ensures template fallback provides the same structure as LLM generation.
        Frontend expects: { introduction, scenarios, general_tips, child_name }
        """
        import json

        # Create 3 standard scenarios for template-based guidelines
        scenarios = [
            {
                "title": "משחק חופשי",
                "context": "תרחיש 1",
                "what_to_film": f"צלמו את {child_name} במשחק חופשי - בבית, בגן, או בכל מקום שנוח. המטרה היא לראות איך {child_name} מתנהל/ת במצב זה.",
                "what_to_look_for": [
                    "איך הילד/ה בוחר/ת פעילות",
                    "משך זמן הקשב לפעילות",
                    "תגובות לסביבה"
                ],
                "duration": "2-5 דקות",
                "examples": [
                    "משחק עם צעצועים בסלון",
                    "פעילות יצירתית בשולחן"
                ]
            },
            {
                "title": "אינטראקציה חברתית",
                "context": "תרחיש 2",
                "what_to_film": f"צלמו אינטראקציה של {child_name} עם אדם אחר - זה יכול להיות אח/ות, הורה, או חבר/ה.",
                "what_to_look_for": [
                    "איכות התקשורת",
                    "יוזמה חברתית",
                    "תגובתיות לאחר"
                ],
                "duration": "2-5 דקות",
                "examples": [
                    "משחק משותף עם ילד אחר",
                    "שיחה עם מבוגר"
                ]
            },
            {
                "title": "פעילות יומיומית",
                "context": "תרחיש 3",
                "what_to_film": f"כל פעילות יומיומית שבה {child_name} עוסק/ת באופן טבעי - אוכל, משחק, הכנה לשינה וכד'.",
                "what_to_look_for": [
                    "עצמאות בביצוע",
                    "התארגנות",
                    "ויסות עצמי"
                ],
                "duration": "2-5 דקות",
                "examples": [
                    "ארוחה משפחתית",
                    "משחק בחצר",
                    "זמן קריאה"
                ]
            }
        ]

        return json.dumps({
            "introduction": f"הנחיות צילום מותאמות עבור {child_name}",
            "scenarios": scenarios,
            "general_tips": [
                "צילום טבעי - אל תבקשו מהילד/ה לעשות משהו מיוחד",
                "2-5 דקות לכל סרטון",
                "מיקוד על פני וגוף הילד/ה",
                "תאורה טבעית היא הכי טובה"
            ],
            "estimated_duration": "2-5 דקות לסרטון",
            "child_name": child_name
        }, ensure_ascii=False)

    def _get_stage1_extraction_schema(self) -> dict:
        """
        Get JSON schema for Stage 1 extraction.
        Defines the structure for extracting interview data + parent persona (holistic diagnosis).
        """
        return {
            "type": "object",
            "properties": {
                "child": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age_years": {"type": "number"},
                        "age_months": {"type": "number"},
                        "gender": {"type": "string"}
                    }
                },
                "main_concern": {"type": "string"},
                "difficulties": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "area": {"type": "string"},
                            "description": {"type": "string"},
                            "specific_examples": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "when_where": {"type": "string"},
                                        "behavior": {"type": "string"},
                                        "trigger": {"type": "string"},
                                        "frequency": {"type": "string"},
                                        "duration": {"type": "string"}
                                    }
                                }
                            },
                            "duration_since_onset": {"type": "string"},
                            "impact_child": {"type": "string"},
                            "impact_family": {"type": "string"}
                        }
                    }
                },
                "strengths": {
                    "type": "object",
                    "properties": {
                        "likes": {"type": "array", "items": {"type": "string"}},
                        "good_at": {"type": "array", "items": {"type": "string"}},
                        "positives": {"type": "string"}
                    }
                },
                "development": {
                    "type": "object",
                    "properties": {
                        "pregnancy_birth": {"type": "string"},
                        "milestones": {"type": "string"},
                        "medical": {"type": "string"}
                    }
                },
                "school": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string"},
                        "adjustment": {"type": "string"},
                        "support": {"type": "string"}
                    }
                },
                "history": {
                    "type": "object",
                    "properties": {
                        "previous_diagnosis": {"type": "string"},
                        "previous_treatment": {"type": "string"},
                        "family_history": {"type": "string"}
                    }
                },
                "parent_perspective": {
                    "type": "object",
                    "properties": {
                        "childs_experience": {"type": "string"},
                        "what_tried": {"type": "string"},
                        "hopes": {"type": "string"}
                    }
                },

                # Holistic Diagnosis Fields (Parent Persona)
                "parent_emotional_vibe": {
                    "type": "string",
                    "description": "Parent's emotional state in Hebrew (e.g., 'חרדה ומחפשת אישור', 'מתוסכלת אך מעשית')"
                },
                "specific_vocabulary_map": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "clinical_term": {"type": "string", "description": "Clinical term (e.g., 'Tantrum', 'Inattention')"},
                            "parent_word": {"type": "string", "description": "Parent's specific Hebrew word (e.g., 'מתפוצץ', 'מרחף')"}
                        },
                        "required": ["clinical_term", "parent_word"]
                    },
                    "description": "Array of vocabulary mappings from clinical terms to parent's specific Hebrew words"
                },
                "family_context_assets": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific toys, people, places mentioned in transcript (e.g., 'סבתא רחל', 'לגו נינג'ה גו', 'השטיח האדום בסלון')"
                }
            }
        }

    def _get_stage2_guidelines_schema(self) -> dict:
        """
        Get JSON schema for Stage 2 guidelines generation.
        Defines the structure for video filming guidelines.
        """
        return {
            "type": "object",
            "required": ["parent_greeting", "general_filming_tips", "video_guidelines"],
            "properties": {
                "parent_greeting": {
                    "type": "object",
                    "required": ["child_name", "opening_message"],
                    "properties": {
                        "parent_name": {"type": "string"},
                        "child_name": {"type": "string"},
                        "opening_message": {"type": "string"}
                    }
                },
                "general_filming_tips": {
                    "type": "array",
                    "minItems": 3,
                    "items": {"type": "string"}
                },
                "video_guidelines": {
                    "type": "array",
                    "minItems": 3,
                    "maxItems": 5,
                    "items": {
                        "type": "object",
                        "required": ["id", "category", "title", "instruction", "example_situations", "focus_points", "rationale_for_parent"],
                        "properties": {
                            "id": {"type": "integer"},
                            "category": {"type": "string", "enum": ["reported_difficulty", "comorbidity_check", "strength_baseline"]},
                            "difficulty_area": {"type": "string", "description": "For difficulties: problem area. For strength_baseline: strength domain (e.g., 'יצירתיות', 'משחק חברתי')"},
                            "title": {"type": "string"},
                            "instruction": {"type": "string"},
                            "example_situations": {
                                "type": "array",
                                "minItems": 2,
                                "items": {"type": "string"}
                            },
                            "duration_suggestion": {"type": "string"},
                            "focus_points": {
                                "type": "array",
                                "minItems": 2,
                                "items": {"type": "string"}
                            },
                            "rationale_for_parent": {"type": "string"}
                        }
                    }
                }
            }
        }

    async def _call_llm(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """
        Call LLM provider with prompt.

        Args:
            prompt: The prompt to send
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text from LLM
        """
        if not self.llm_provider:
            raise ValueError("No LLM provider configured")

        # Use provider's chat method
        from app.services.llm.base import Message

        response = await self.llm_provider.chat(
            messages=[Message(role="user", content=prompt)],
            temperature=temperature,
            max_tokens=max_tokens
        )

        return response.content

    async def generate_artifact(
        self,
        artifact_id: str,
        session_data: Dict[str, Any],
        **kwargs
    ) -> Artifact:
        """
        🌟 Wu Wei: Generic artifact generator - config-driven dispatch.

        This method reads artifacts.yaml to determine how to generate each artifact.
        No hardcoded artifact IDs in the dispatcher!

        Args:
            artifact_id: Artifact identifier (e.g., "baseline_video_guidelines")
            session_data: Session context
            **kwargs: Additional parameters (e.g., required artifacts)

        Returns:
            Generated Artifact with status 'ready' or 'error'
        """
        logger.info(f"🎬 Generic generator dispatching for: {artifact_id}")

        # Get generator config from artifact_manager
        generator_config = self.artifact_manager.get_generator_config(artifact_id)

        if not generator_config:
            logger.error(f"❌ No generator config found for artifact: {artifact_id}")
            error_artifact = Artifact(
                artifact_id=artifact_id,
                artifact_type="unknown",
                status="error"
            )
            error_artifact.mark_error(f"No generator configuration for {artifact_id}")
            return error_artifact

        # Get the generator method name from config
        method_name = generator_config.get("method")

        if not method_name:
            logger.error(f"❌ No method specified in generator config for: {artifact_id}")
            error_artifact = Artifact(
                artifact_id=artifact_id,
                artifact_type="unknown",
                status="error"
            )
            error_artifact.mark_error(f"No method specified for {artifact_id}")
            return error_artifact

        # Get the method from this service
        generator_method = getattr(self, method_name, None)

        if not generator_method:
            logger.error(f"❌ Generator method '{method_name}' not found for: {artifact_id}")
            error_artifact = Artifact(
                artifact_id=artifact_id,
                artifact_type="unknown",
                status="error"
            )
            error_artifact.mark_error(f"Generator method '{method_name}' not implemented")
            return error_artifact

        # Merge config params with kwargs
        params = generator_config.get("params", {})
        call_kwargs = {**params, **kwargs}

        # Call the generator method
        logger.info(f"✅ Calling {method_name} for {artifact_id}")
        return await generator_method(artifact_id, session_data, **call_kwargs)

    async def generate_professional_report(
        self,
        artifact_id: str,
        session_data: Dict[str, Any],
        video_analysis_source: str = "baseline_video_analysis",
        **kwargs
    ) -> Artifact:
        """
        Generate professional clinical report from video analysis.

        Wu Wei: This is triggered when video analysis is complete.

        Args:
            artifact_id: Artifact identifier (baseline_professional_report, etc.)
            session_data: Session data including extracted_data and artifacts
            video_analysis_source: Artifact ID of video analysis to use

        Returns:
            Artifact with status 'ready' or 'error'
        """
        start_time = time.time()

        logger.info(f"📋 Generating professional report: {artifact_id}")

        # Get video analysis from session artifacts
        video_analysis_artifact = session_data.get("artifacts", {}).get(video_analysis_source)

        if not video_analysis_artifact or not video_analysis_artifact.get("exists"):
            logger.error(f"❌ Cannot generate professional report: {video_analysis_source} not found")
            error_artifact = Artifact(
                artifact_id=artifact_id,
                artifact_type="report",
                status="error"
            )
            error_artifact.mark_error(f"Required artifact {video_analysis_source} not available")
            return error_artifact

        # Parse video analysis content
        import json
        video_analysis = json.loads(video_analysis_artifact.get("content", "{}"))

        artifact = Artifact(
            artifact_id=artifact_id,
            artifact_type="report",
            status="generating",
            content_format="markdown",
            generation_inputs={
                "child_name": session_data.get("child_name"),
                "video_analysis_source": video_analysis_source,
                "extracted_data": session_data.get("extracted_data", {})
            }
        )

        try:
            # TODO: Implement professional report generation with LLM
            # For now, create placeholder
            content = self._generate_professional_report_placeholder(
                child_name=session_data.get("child_name", "ילד/ה"),
                session_data=session_data,
                video_analysis=video_analysis
            )

            artifact.mark_ready(content)
            artifact.generation_duration_seconds = time.time() - start_time

            logger.info(f"✅ Professional report generated in {artifact.generation_duration_seconds:.2f}s")

        except Exception as e:
            logger.error(f"❌ Error generating professional report: {e}", exc_info=True)
            artifact.mark_error(str(e))

        return artifact

    async def generate_parent_report(
        self,
        artifact_id: str,
        session_data: Dict[str, Any],
        professional_report_source: str = "baseline_professional_report",
        **kwargs
    ) -> Artifact:
        """
        Generate parent-friendly report derived from professional report.

        Wu Wei: Parent report is a simplified, accessible version of the professional report.

        Args:
            artifact_id: Artifact identifier (baseline_parent_report, etc.)
            session_data: Session data including extracted_data and artifacts
            professional_report_source: Artifact ID of professional report to derive from

        Returns:
            Artifact with status 'ready' or 'error'
        """
        start_time = time.time()

        logger.info(f"📋 Generating parent report from: {professional_report_source}")

        # Get professional report from session artifacts
        professional_report_artifact = session_data.get("artifacts", {}).get(professional_report_source)

        if not professional_report_artifact or not professional_report_artifact.get("exists"):
            logger.error(f"❌ Cannot generate parent report: {professional_report_source} not found")
            error_artifact = Artifact(
                artifact_id=artifact_id,
                artifact_type="report",
                status="error"
            )
            error_artifact.mark_error(f"Required artifact {professional_report_source} not available")
            return error_artifact

        professional_report_content = professional_report_artifact.get("content", "")

        artifact = Artifact(
            artifact_id=artifact_id,
            artifact_type="report",
            status="generating",
            content_format="markdown",
            generation_inputs={
                "child_name": session_data.get("child_name"),
                "professional_report_source": professional_report_source,
                "extracted_data": session_data.get("extracted_data", {})
            }
        )

        try:
            # TODO: Implement parent report derivation from professional report using LLM
            # For now, create placeholder
            content = self._generate_parent_report_placeholder(
                child_name=session_data.get("child_name", "ילד/ה"),
                session_data=session_data
            )

            artifact.mark_ready(content)
            artifact.generation_duration_seconds = time.time() - start_time

            logger.info(f"✅ Parent report generated in {artifact.generation_duration_seconds:.2f}s")

        except Exception as e:
            logger.error(f"❌ Error generating parent report: {e}", exc_info=True)
            artifact.mark_error(str(e))

        return artifact

    def _generate_professional_report_placeholder(
        self,
        child_name: str,
        session_data: Dict[str, Any],
        video_analysis: Dict[str, Any]
    ) -> str:
        """Generate placeholder professional report."""
        return f"""# דוח מקצועי - הערכה התפתחותית

## פרטי המקרה

**שם הילד/ה:** {child_name}
**גיל:** {session_data.get('age', 'לא צוין')}
**תאריך הערכה:** {datetime.now().strftime('%d/%m/%Y')}

## מידע רקע

[מידע מהראיון עם ההורה]

## תצפיות התנהגותיות

### ניתוח וידאו

[ממצאים מניתוח הסרטונים - מבוסס על video_analysis]

### דפוסים זוהו

[דפוסים קליניים שזוהו]

## רושם קליני

### שיקולים אבחנתיים

[שיקולים מבוססי DSM-5/ICD-11]

### רמות ביטחון

[רמות ביטחון בממצאים]

## השלכות תפקודיות

[השפעה על תפקוד יומיומי]

## המלצות

### הערכות נוספות נדרשות

[המלצות להערכות נוספות]

### התערבויות טיפוליות

[המלצות טיפוליות]

### הפניות למומחים

[המלצות להפניה]

## מגבלות ההערכה

[הגבלות והערות חשובות לגבי תחום ההערכה]

---

*דוח מקצועי זה נוצר בתאריך: {datetime.now().strftime('%d/%m/%Y')}*
*למטרות אבחון וטיפול בלבד*
"""

    def _generate_parent_report_placeholder(
        self,
        child_name: str,
        session_data: Dict[str, Any]
    ) -> str:
        """Generate placeholder parent report (derived from professional report)."""
        return f"""# דוח הערכה התפתחותית - {child_name}

## סיכום מנהלים

[דוח זה נגזר מהדוח המקצועי ומותאם להורים]

## פרופיל הילד/ה

**שם:** {child_name}
**גיל:** {session_data.get('age', 'לא צוין')}

## תצפיות התפתחותיות

[תצפיות בשפה נגישה ומכילה]

## תחומי חוזקה

[מה {child_name} עושה נהדר]

## תחומים לתמיכה

[איפה {child_name} יכול/ה להשתפר עם תמיכה]

## המלצות מעשיות

### צעדים מיידיים
[פעולות קונקרטיות]

### יעדים לטווח ארוך
[מה לשאוף אליו]

### משאבים
[קישורים ומשאבים מועילים]

## השלבים הבאים

[תוכנית פעולה ברורה]

---

*דוח זה נוצר בתאריך: {datetime.now().strftime('%d/%m/%Y')}*
*נכתב בשפה פשוטה ומכילה להורים*
"""
