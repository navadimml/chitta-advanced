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
        Generate personalized video recording guidelines using two-stage LLM approach.

        Wu Wei: This is triggered when knowledge is rich (qualitative check).

        Two-stage approach:
        1. Extract structured JSON from interview transcript
        2. Generate video guidelines from structured data

        Args:
            session_data: Session data including extracted_data, child info, concerns, conversation_history

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
            # Generate using LLM (or fallback to template if no LLM)
            if self.llm_provider:
                logger.info("📝 Using two-stage LLM generation for video guidelines")
                content = await self._generate_guidelines_with_llm(session_data)
            else:
                logger.info("📝 Using template generation (no LLM provider)")
                # Fallback to template
                child_name = session_data.get("child_name", "ילד/ה")
                age = session_data.get("age", "")
                age_str = f"{age} שנים" if age else "גיל לא צוין"
                concerns = session_data.get("primary_concerns", [])
                concern_details = session_data.get("concern_details", "")

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

    async def _generate_guidelines_with_llm(self, session_data: Dict[str, Any]) -> str:
        """
        Two-stage LLM generation for video guidelines.

        Stage 1: Extract structured JSON from interview transcript
        Stage 2: Generate guidelines from structured data

        Args:
            session_data: Session data with conversation_history, extracted_data, etc.

        Returns:
            Markdown formatted video guidelines in Hebrew
        """
        import json

        # Stage 1: Extract structured JSON from conversation
        logger.info("🔍 Stage 1: Extracting structured JSON from interview transcript")
        conversation_history = session_data.get("conversation_history", [])

        # Build transcript from conversation history
        transcript = self._build_transcript(conversation_history)
        stage1_prompt = self._build_stage1_extraction_prompt(transcript)

        # Call LLM for extraction
        extracted_json_str = await self._call_llm(stage1_prompt, temperature=0.1, max_tokens=2000)

        # Parse JSON
        try:
            extracted_data = json.loads(extracted_json_str)
            logger.info(f"✅ Stage 1 complete: Extracted structured data ({len(extracted_json_str)} chars)")
        except json.JSONDecodeError as e:
            logger.error(f"❌ Stage 1 failed: Invalid JSON from LLM: {e}")
            logger.error(f"Raw output: {extracted_json_str[:500]}")
            raise ValueError(f"LLM returned invalid JSON: {e}")

        # Stage 2: Generate guidelines from structured data
        logger.info("📝 Stage 2: Generating video guidelines from structured data")
        stage2_prompt = self._build_stage2_guidelines_prompt(extracted_data)

        # Call LLM for guidelines generation
        guidelines_json_str = await self._call_llm(stage2_prompt, temperature=0.7, max_tokens=3000)

        # Parse guidelines JSON
        try:
            guidelines_data = json.loads(guidelines_json_str)
            logger.info(f"✅ Stage 2 complete: Generated guidelines ({len(guidelines_json_str)} chars)")
        except json.JSONDecodeError as e:
            logger.error(f"❌ Stage 2 failed: Invalid JSON from LLM: {e}")
            logger.error(f"Raw output: {guidelines_json_str[:500]}")
            raise ValueError(f"LLM returned invalid JSON: {e}")

        # Convert JSON to markdown format for parent
        markdown_content = self._convert_guidelines_json_to_markdown(guidelines_data)

        logger.info(f"✅ Two-stage generation complete: {len(markdown_content)} chars markdown")
        return markdown_content

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
    "parent_name": "שם ההורה (if known, else 'הורה יקר')",
    "child_name": "שם הילד/ה (if known)",
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
