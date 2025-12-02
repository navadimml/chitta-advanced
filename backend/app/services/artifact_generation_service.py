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

            # Build extraction prompt aligned with Living Gestalt model
            stage1_prompt_text = f"""# Stage 1: Extract Living Gestalt from Interview

## Role
You are a clinical psychologist specializing in child development interviews.
You extract a "Living Gestalt" - seeing the WHOLE child, not just problems.

**Living Gestalt Philosophy:**
1. IDENTITY first (name, age)
2. ESSENCE - who is this child as a person?
3. STRENGTHS before concerns (what they do well)
4. CONCERNS in context of everything above
5. HISTORY and FAMILY context
6. PATTERNS and emerging HYPOTHESES

## Task
Extract and structure all information from the transcript following the Living Gestalt structure.
**Preserve parent quotes in Hebrew exactly as spoken.**

## Extraction Layers

### 1. Identity (Essentials)
- Name, age, gender
- Must have these before anything else can be interpreted

### 2. Essence (Who They Are)
Extract observations about:
- **Temperament:** How do they approach the world? (cautious, eager, intense, easy-going)
- **Energy Pattern:** What's their typical energy like?
- **Core Qualities:** What adjectives describe them at their core?

### 3. Strengths (First Class - NOT Afterthoughts!)
**This comes BEFORE concerns.** Extract:
- **Abilities:** What is this child good at?
- **Interests:** What captivates them? What do they love?
- **What Lights Them Up:** Those moments when they truly shine
- **What Surprises People:** Hidden capabilities others don't expect

### 4. Concerns (In Context)
Now the concerns, but in context of the child we've described:
- **Primary Areas:** The main concerns
- **Details:** Specific examples with context (when, where, triggers)
- **Impact:** How it affects child and family

### 5. History & Family Context
- Birth history (complications, prematurity)
- Milestone notes
- Previous evaluations/diagnoses
- Family structure, siblings, languages
- Family developmental history ("dad was a late talker")

### 6. Patterns & Emerging Hypotheses
Based on the conversation, identify:
- **Patterns:** Themes appearing across multiple observations
  Example: "mornings are hard" + "car seat battles" + "bedtime struggles" = "transitions are difficult"
- **Contradictions:** Things that don't fit
  Example: "usually withdrawn but spontaneous with grandma"
- **Potential Hypotheses:** Working theories that could explain what you're seeing
  These come from THREE sources:
  1. Domain Knowledge - clinical patterns (e.g., speech delay often co-occurs with motor planning issues)
  2. Pattern Detection - themes across observations
  3. Contradictions - exceptions that might reveal capacity

### 7. Parent Persona (Holistic Layer)
✅ **Emotional Vibe:** Parent's state (e.g., "חרדה ומחפשת אישור", "מתוסכלת אך מעשית")
✅ **Vocabulary Map:** Specific Hebrew words parent uses for behaviors
   - Map clinical terms to parent's words: "Tantrum" -> "מתפוצץ"
✅ **Context Assets:** Specific items/people mentioned ("סבתא רחל", "לגו נינג'ה גו")

### Rules
❌ Don't invent information not in transcript
❌ Don't diagnose - observe patterns, hold hypotheses lightly
❌ Don't translate Hebrew to English
❌ Don't skip strengths - they're as important as concerns

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

        # Extract hypotheses and patterns from interview summary (new Gestalt structure)
        emerging_hypotheses = interview_summary.get('emerging_hypotheses', [])
        patterns = interview_summary.get('patterns', [])
        contradictions = interview_summary.get('contradictions', [])
        strengths = interview_summary.get('strengths', {})
        concerns = interview_summary.get('concerns', {})

        json_input = json.dumps(interview_summary, ensure_ascii=False, indent=2)
        stage2_prompt_text = f"""# Stage 2: Generate Hypothesis-Driven Video Guidelines (Hebrew)

## Role
You are "Chitta," a supportive child development expert writing directly to the Israeli parent in Hebrew.
**Your Goal:** Create video scenarios that TEST SPECIFIC HYPOTHESES while lowering parent anxiety.

## The Exploration Cycle Philosophy

Video is ONE METHOD of exploration (conversation is another). Each video scenario should:
1. **Test a specific hypothesis** - What are we trying to understand?
2. **Reveal capacity** - Show what the child CAN do, not just problems
3. **Provide evidence** - Help us confirm or refute our working theories

## Parent Context (Use This!)
**Parent Vibe:** {parent_vibe}
**Child Name:** {child_name}
**Parent's Vocabulary:** {json.dumps(vocab_map, ensure_ascii=False)}
**Context Assets:** {json.dumps(context_assets, ensure_ascii=False)}

## Current Hypotheses & Patterns from Interview

**Emerging Hypotheses to Test:**
{json.dumps(emerging_hypotheses, ensure_ascii=False, indent=2) if emerging_hypotheses else "None identified yet"}

**Patterns Detected:**
{json.dumps(patterns, ensure_ascii=False, indent=2) if patterns else "None identified yet"}

**Contradictions to Explore:**
{json.dumps(contradictions, ensure_ascii=False, indent=2) if contradictions else "None identified yet"}

**Child's Strengths:**
{json.dumps(strengths, ensure_ascii=False, indent=2) if strengths else "Not yet identified"}

## Hypothesis-Driven Scenario Design

Each video scenario should be designed to:
1. **Test a hypothesis** - Which theory are we testing?
2. **Provide differential evidence** - What would we see if hypothesis is TRUE vs FALSE?
3. **Capture natural behavior** - Not artificial test conditions

### Scenario Categories:

**1. hypothesis_test** - Directly tests an emerging hypothesis
   - Links to a specific hypothesis from the interview
   - What would confirm it? What would disconfirm it?

**2. pattern_exploration** - Investigates a detected pattern
   - Will we see the pattern in this context too?
   - Does the pattern hold or break here?

**3. contradiction_probe** - Explores a contradiction
   - What's different about when the child succeeds vs struggles?
   - Can we see the capacity in the right conditions?

**4. strength_baseline** - Documents optimal functioning
   - When is this child at their best?
   - What conditions enable thriving?

## Critical Instructions for Writing Guidelines

### 1. CONCRETE & SIMPLE (Lower Cognitive Load)
❌ BAD: "שחקו משחק עם חוקים ותורות"
✅ GOOD: "שבו ליד השולחן במטבח, בחרו משחק סולמות וחבלים או זיכרון (קלפים). שחקו יחד 5 דקות."

### 2. The "Sandwich" Rationale (Emotional Regulation for Parents)
The `rationale_for_parent` must follow this structure in Hebrew:
1. **Validate:** "שמעתי כמה הבקרים שלכם עמוסים..."
2. **Explain:** "צילום של רגע כזה יעזור לנו להבין בדיוק..."
3. **Reassure:** "אל תדאגו מ'לסדר' את המצב למצלמה..."

### 3. Vocabulary Mirroring (CRITICAL)
Use the **Vocabulary Map** - parent's words, not clinical jargon.

### 4. Use Contextual Assets
Make `example_situations` specific to their mentioned environment.

### 5. Focus Points (focus_points) are INTERNAL ONLY
These are for analysis. NOT for parents.
Write them as clinical observation notes linked to hypotheses:
- "האם ההיפותזה שהקושי הוא בויסות מאוששת או לא?"
- "האם נראה את היכולת שמופיעה עם סבתא?"

## Task
Based on the hypotheses, patterns, and contradictions from the interview:

1. **Create 3-4 video scenarios** that test specific hypotheses
2. **At least 1 must be strength_baseline** - showing the child thriving
3. **Each must link to a hypothesis, pattern, or contradiction**

**Required fields for each scenario:**
- id: Unique number
- category: "hypothesis_test" | "pattern_exploration" | "contradiction_probe" | "strength_baseline"
- target_hypothesis: What theory this tests (or "baseline" for strength scenarios)
- what_we_hope_to_learn: The question this video answers
- difficulty_area: Domain being explored
- title: Short Hebrew title
- instruction: CONCRETE filming instruction
- example_situations: 2-3 concrete situations
- duration_suggestion: Time estimate
- focus_points: Internal analysis points (linked to hypothesis)
- rationale_for_parent: Sandwich structure in Hebrew

## Clinical Comorbidity Framework (for domain_knowledge hypotheses)

**ADHD/Attention** → Check: Sensory regulation, fine motor, emotional regulation
**Social/communication** → Check: Symbolic play, restricted interests, repetitive behaviors
**Language delays** → Check: Social interactions, imaginative play, non-verbal communication
**Emotional outbursts** → Check: Sensory triggers, language comprehension

## Structured Data from Interview

{json_input}

## Example of Hypothesis-Test Scenario

{{
  "id": 1,
  "category": "hypothesis_test",
  "target_hypothesis": "הקושי בקשב קשור לויסות רגשי ולא לבעיית קשב ראשונית",
  "what_we_hope_to_learn": "האם היא יכולה להחזיק קשב כשהמצב רגוע ומבוקר? אם כן - ההיפותזה מתחזקת",
  "difficulty_area": "קשב וויסות",
  "title": "משחק קופסה במטבח",
  "instruction": "שבו יחד ליד שולחן המטבח. בחרו משחק קופסה פשוט שהילדה מכירה - סולמות וחבלים או זיכרון. שחקו יחד 5-7 דקות. אם היא קמה או מפסיקה - זה בסדר, המשיכו לצלם.",
  "example_situations": [
    "אחרי ארוחת צהריים, ליד שולחן המטבח",
    "בערב לפני האמבטיה, בסלון על השטיח"
  ],
  "duration_suggestion": "5-7 דקות",
  "focus_points": [
    "האם יש הבדל בקשב בין רגעים רגועים לרגעים עמוסים?",
    "כמה זמן היא מחזיקה לפני התנועה הראשונה?",
    "מה קורה כשמזכירים לה - האם זה עוזר או מגביר?"
  ],
  "rationale_for_parent": "שמעתי שהיא מתקשה לחכות לתורה וש'המחשבות שלה בורחות'. סרטון של משחק רגוע יעזור לנו לראות את היכולת שלה כשאין עומס - זה מידע חשוב מאוד. אל תדאגו מ'לסדר' את המצב - אנחנו רוצים לראות את המציאות."
}}

## Example of Contradiction-Probe Scenario

{{
  "id": 2,
  "category": "contradiction_probe",
  "target_hypothesis": "היכולת לתקשר קיימת - מתגלה בתנאים מסוימים",
  "what_we_hope_to_learn": "מה שונה כשהוא עם סבתא? האם נוכל לראות את היכולת גם בבית?",
  "difficulty_area": "תקשורת חברתית",
  "title": "משחק עם דמות מוכרת",
  "instruction": "אם סבתא או דוד אוהב מגיעים - צלמו כמה דקות של אינטראקציה. אם לא, נסו משחק שבו אתם מחקים משהו שהוא אוהב.",
  "example_situations": [
    "כשסבתא מגיעה לביקור",
    "משחק עם הצעצוע האהוב עם אח גדול"
  ],
  "duration_suggestion": "5 דקות",
  "focus_points": [
    "מה שונה באינטראקציה עם דמות 'בטוחה'?",
    "האם יש יותר יוזמה? יותר מילים? יותר מגע עין?",
    "מה בתנאים האלה מאפשר את ההתנהגות?"
  ],
  "rationale_for_parent": "שמעתי שעם סבתא הוא 'אחר לגמרי' - וזה מאוד משמעותי! לראות מה קורה ברגעים האלה יעזור לנו להבין איפה היכולת קיימת ואיך לבנות עליה."
}}

## Example of Strength-Baseline Scenario

{{
  "id": 3,
  "category": "strength_baseline",
  "target_hypothesis": "baseline",
  "what_we_hope_to_learn": "איך נראית הילדה כשהיא בזרימה ומרוכזת - הבסיס ליכולותיה",
  "difficulty_area": "משחק יצירתי",
  "title": "זמן יצירה חופשית",
  "instruction": "תנו לה דף ריק וצבעים, ותנו לה לצייר מה שהיא רוצה. צלמו 5 דקות של יצירה חופשית.",
  "example_situations": [
    "אחר הצהריים בפינת היצירה",
    "בשולחן המטבח עם עפרונות צבעוניים"
  ],
  "duration_suggestion": "5 דקות",
  "focus_points": [
    "כמה זמן היא נשארת ממוקדת כשהיא עושה מה שהיא אוהבת?",
    "איך נראה הגוף שלה - רגוע? מותח?",
    "מה התנאים שמאפשרים את ההתמקדות הזו?"
  ],
  "rationale_for_parent": "שמעתי שהיא אוהבת לצייר - זה חוזקה אמיתית! לראות אותה ברגעים שבהם היא שקועה יעזור לנו להבין מה עובד ולבנות על זה. התמונה השלמה כוללת גם את מה שהיא עושה נהדר."
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
        # This context is passed to video_analysis_prompt to guide hypothesis testing
        guidelines_list = guidelines_data.get("video_guidelines", [])
        exploration_summary = guidelines_data.get("exploration_summary", {})

        for idx, scenario in enumerate(component_format.get("scenarios", [])):
            if idx < len(guidelines_list):
                guideline = guidelines_list[idx]
                scenario["analyst_context"] = {
                    # What parent was asked to film
                    "instruction_given_to_parent": scenario.get("what_to_film", ""),
                    # Clinical focus points (internal use)
                    "internal_focus_points": guideline.get("focus_points", []),
                    # Parent persona for vocabulary mirroring
                    "parent_persona_data": {
                        "emotional_vibe": interview_summary.get("parent_emotional_vibe", ""),
                        "vocabulary_map": interview_summary.get("specific_vocabulary_map", []),
                        "context_assets": interview_summary.get("family_context_assets", [])
                    },
                    # Hypothesis-driven context (NEW)
                    "clinical_goal": guideline.get("category", ""),
                    "target_hypothesis": guideline.get("target_hypothesis", ""),
                    "what_we_hope_to_learn": guideline.get("what_we_hope_to_learn", ""),
                }

        # Add exploration summary to component format for downstream use
        component_format["exploration_context"] = {
            "hypotheses_being_tested": exploration_summary.get("hypotheses_being_tested", []),
            "patterns_being_explored": exploration_summary.get("patterns_being_explored", []),
            "emerging_hypotheses": emerging_hypotheses,
            "patterns": patterns,
            "contradictions": contradictions,
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
        Get JSON schema for Stage 1 extraction - Living Gestalt structure.

        Aligned with the new Child model and Living Gestalt philosophy:
        1. Identity first
        2. Essence (who they are)
        3. Strengths before concerns
        4. Concerns in context
        5. History and family
        6. Patterns and hypotheses
        7. Parent persona
        """
        return {
            "type": "object",
            "properties": {
                # === 1. IDENTITY (Essentials) ===
                "child": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age_years": {"type": "number"},
                        "age_months": {"type": "number"},
                        "gender": {"type": "string"}
                    }
                },

                # === 2. ESSENCE (Who They Are) ===
                "essence": {
                    "type": "object",
                    "properties": {
                        "temperament_observations": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "How they approach the world: cautious, eager, intense, easy-going, etc."
                        },
                        "energy_pattern": {
                            "type": "string",
                            "description": "Their typical energy pattern (e.g., 'high energy but can focus deeply on interests')"
                        },
                        "core_qualities": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Adjectives describing their core: curious, loving, determined, sensitive"
                        }
                    }
                },

                # === 3. STRENGTHS (First Class!) ===
                "strengths": {
                    "type": "object",
                    "properties": {
                        "abilities": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "What is this child good at?"
                        },
                        "interests": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "What captivates them? What do they love?"
                        },
                        "what_lights_them_up": {
                            "type": "string",
                            "description": "Those moments when they truly shine - narrative"
                        },
                        "surprises_people": {
                            "type": "string",
                            "description": "Hidden capabilities others don't expect"
                        }
                    }
                },

                # === 4. CONCERNS (In Context) ===
                "concerns": {
                    "type": "object",
                    "properties": {
                        "primary_areas": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Main concern areas: attention, communication, motor, etc."
                        },
                        "main_concern_narrative": {
                            "type": "string",
                            "description": "Parent's main concern in their own words"
                        },
                        "details": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "area": {"type": "string"},
                                    "description": {"type": "string"},
                                    "when_where": {"type": "string"},
                                    "triggers": {"type": "string"},
                                    "specific_example": {"type": "string"}
                                }
                            }
                        },
                        "impact_on_child": {"type": "string"},
                        "impact_on_family": {"type": "string"}
                    }
                },

                # === 5. HISTORY ===
                "history": {
                    "type": "object",
                    "properties": {
                        "birth": {
                            "type": "object",
                            "properties": {
                                "complications": {"type": "string"},
                                "premature": {"type": "boolean"},
                                "weeks_gestation": {"type": "number"}
                            }
                        },
                        "milestone_notes": {"type": "string"},
                        "early_development": {"type": "string"},
                        "medical_history": {"type": "string"},
                        "previous_evaluations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "evaluator_type": {"type": "string"},
                                    "findings": {"type": "string"},
                                    "diagnosis_given": {"type": "string"}
                                }
                            }
                        },
                        "previous_diagnoses": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "interventions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {"type": "string"},
                                    "status": {"type": "string"},
                                    "outcome": {"type": "string"}
                                }
                            }
                        }
                    }
                },

                # === 6. FAMILY CONTEXT ===
                "family": {
                    "type": "object",
                    "properties": {
                        "structure": {"type": "string", "description": "e.g., 'two parents, older sister'"},
                        "siblings": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "position": {"type": "string"},
                                    "notes": {"type": "string", "description": "Relevant dynamics: 'speaks for him', 'very close'"}
                                }
                            }
                        },
                        "languages_at_home": {"type": "array", "items": {"type": "string"}},
                        "family_developmental_history": {
                            "type": "string",
                            "description": "Similar difficulties in family: 'dad was a late talker'"
                        },
                        "support_system": {"type": "string"}
                    }
                },

                # === 7. PATTERNS & EMERGING HYPOTHESES ===
                "patterns": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "theme": {"type": "string", "description": "The pattern: 'transitions are difficult'"},
                            "observations": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Evidence for this pattern"
                            },
                            "domains_involved": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Which developmental domains"
                            }
                        }
                    }
                },
                "contradictions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Things that don't fit: 'usually withdrawn but spontaneous with grandma'"
                },
                "emerging_hypotheses": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "theory": {"type": "string", "description": "Working theory to explore"},
                            "source": {
                                "type": "string",
                                "enum": ["pattern", "domain_knowledge", "contradiction"],
                                "description": "Where this hypothesis came from"
                            },
                            "source_details": {"type": "string", "description": "Specific trigger"},
                            "related_domains": {"type": "array", "items": {"type": "string"}},
                            "questions_to_explore": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                },

                # === PARENT PERSONA (for personalization) ===
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
                },

                # === PARENT PERSPECTIVE ===
                "parent_perspective": {
                    "type": "object",
                    "properties": {
                        "what_tried": {"type": "string"},
                        "hopes": {"type": "string"},
                        "childs_experience": {"type": "string", "description": "What parent thinks child is experiencing"}
                    }
                },

                # === SCHOOL CONTEXT ===
                "school": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string"},
                        "adjustment": {"type": "string"},
                        "support": {"type": "string"}
                    }
                }
            }
        }

    def _get_stage2_guidelines_schema(self) -> dict:
        """
        Get JSON schema for Stage 2 guidelines generation - Hypothesis-Driven.

        Each video scenario is designed to test specific hypotheses from the interview.
        This aligns with the unified ExplorationCycle model where video is one method
        of exploration among others (conversation, etc.).
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
                            "category": {
                                "type": "string",
                                "enum": ["hypothesis_test", "pattern_exploration", "contradiction_probe", "strength_baseline"],
                                "description": "What kind of exploration this scenario supports"
                            },
                            "target_hypothesis": {
                                "type": "string",
                                "description": "The hypothesis/pattern/contradiction this scenario tests (or 'baseline' for strength scenarios)"
                            },
                            "what_we_hope_to_learn": {
                                "type": "string",
                                "description": "The specific question this video will answer"
                            },
                            "difficulty_area": {
                                "type": "string",
                                "description": "Domain being explored (e.g., 'קשב', 'ויסות רגשי', 'משחק חברתי')"
                            },
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
                                "items": {"type": "string"},
                                "description": "Internal analysis points - what to look for that would confirm/refute hypothesis"
                            },
                            "rationale_for_parent": {"type": "string"}
                        }
                    }
                },
                # Summary of what hypotheses these guidelines are designed to test
                "exploration_summary": {
                    "type": "object",
                    "properties": {
                        "hypotheses_being_tested": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of hypotheses these videos will help test"
                        },
                        "patterns_being_explored": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Patterns we're investigating"
                        },
                        "what_videos_cant_answer": {
                            "type": "string",
                            "description": "Limitations - what questions still need conversation"
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
