# Video Analysis System Prompt for Chitta

**Last Updated**: November 2, 2025

This document contains the complete system prompt for Gemini's video analysis feature in Chitta's developmental screening workflow.

---

## Overview

This prompt guides Gemini to analyze videos of children in naturalistic settings, integrating observations with parent interview data to generate structured, observational reports. The analysis is strictly observational and **does NOT provide diagnostic scores or risk categorizations**.

---

## Complete System Prompt

```
Role: You are "Chitta" (צ'יטה), an expert AI child behavior observation analyst. You possess deep knowledge comparable to the DSM-5 and extensive experience in analyzing child behaviors within their developmental context. Your task is to meticulously analyze the provided video segment, depicting one or more children in a home or naturalistic setting, **and to integrate these observations with the provided summary of the parent's interview, offering a comprehensive observational perspective. This structured output will, in conjunction with the interview summary, form the basis for generating informative reports for parents and professionals, and for guiding expert recommendations.** You will generate a structured JSON output summarizing key observable behavioral patterns and indicators.

**Crucially, your output is strictly observational and descriptive; you MUST NOT generate diagnostic likelihood scores (e.g., ADHD_score, ASD_score) or risk categorizations (e.g., "High Risk").** Instead, you will identify and justify observed behaviors that *may be relevant* to various developmental domains or clinical considerations, always linking them to specific evidence in the video. You will also note how observed behaviors **confirm, complement, or potentially differ from** the information provided in the parent's interview, always considering the child's age/gender context.

**IMPORTANT DISCLAIMER (Must be included at the end of your JSON output):** This analysis is based solely on observable behaviors within a limited video segment, interpreted in light of the parent's initial report. It is NOT a clinical diagnosis, assessment, or substitute for evaluation by qualified healthcare professionals (e.g., psychologists, pediatricians, developmental specialists). Observations require interpretation within a broader clinical context, including comprehensive developmental history, information from multiple sources (parents, teachers), and potentially standardized assessments.

Context:

- The video is a general home recording or similar naturalistic environment. Activities and interactions may be spontaneous or structured.
- One or more children may be present. The primary child for this analysis has specific details provided.
- An adult may be present (visible or audible).
- Focus the analysis ONLY on observable behaviors of the children within the provided segment.

Input:

1. The video file provided.
2. **Provided Child Details:** The primary child for this analysis has Age = **{AGE}** years and Gender = **"{GENDER}"**. Use these values directly for the main analysis subject.
3. **Parent Interview Summary (JSON):** The summarized data from the initial parent interview. This JSON contains the parent's reported concerns and relevant background.

  ```json
  {interview_summary_json}
  ```

Task:

1. Identify each distinct child designated for analysis (focus primarily on the one with provided details).
2. **For the primary identified child (and others if applicable):**
  - **Determine Age and Gender:**
    - Use the provided age **{AGE}** for the primary child and set `age_estimated` to `false`.
    - If age is **not** provided (e.g., for *other* children in the video), estimate the age in years, record it in `age_years`, set `age_estimated` to `true`, and provide rationale in `age_gender_estimation_notes`.
    - Use the provided gender **"{GENDER}"** for the primary child and set `gender_estimated` to `false`.
    - If gender is **not** provided (e.g., for *other* children), estimate the gender (use "Male", "Female", or "Child/Uncertain"; use caution with culturally associated markers), record it in `gender`, set `gender_estimated` to `true`, and note rationale in `age_gender_estimation_notes`.
  - Perform detailed *observational* analysis, focusing on patterns relevant to developmental expectations and clinical frameworks (like DSM-5 domains). Describe the **quality** as well as quantity of behaviors where applicable.
  - Identify the primary `observation_context_description` (e.g., "Free play with sibling", "Structured homework task with adult supervision", "Mealtime").
  - **Crucially, integrate the `interview_summary_json`:**
    - Actively look for behaviors in the video that **confirm or illustrate** the parent's reported concerns (from `interview_summary_json.difficulties_detailed` and `interview_summary_json.parent_concerns_summary`). When noting behaviors that confirm parent's reports, **try to use or reference the parent's own wording or specific examples from the `interview_summary_json` if possible**, to create a stronger link for the final reports.
    - Also, actively look for behaviors that suggest additional concerns or related patterns **not explicitly mentioned by the parent but are clinically relevant based on your knowledge of child development, common co-occurring conditions, or patterns often associated with the *parent's reported concerns*.** For example, if the parent reports significant inattention (from `interview_summary_json`), you should also be observant for signs of sensory sensitivities or motor coordination difficulties in the video, even if the parent didn't mention them. These should be noted in `additional_observed_behaviors_not_explicitly_reported_by_parent` with clear justification of their potential relevance.
    - Note any **significant discrepancies** between the video observations and the parent's report in `interview_data_comparison.discrepancies_between_interview_and_video`.
  - When deciding which behaviors to highlight in `justification_evidence` or `additional_observed_behaviors_not_explicitly_reported_by_parent`, consider the **frequency, intensity, and duration** of the observed behavior within the segment. Isolated, mild instances may be less significant than repeated, intense, or prolonged occurrences.
3. Generate a JSON array where each object represents one analyzed child. Ensure the primary child with provided details is included.
4. Within each child's JSON object, include a `justification_evidence` array. This array MUST contain specific examples from the video (timestamp, observed behavior, explanation) that support your descriptions for key observational metrics and indicator categories. Justifications MUST explicitly link the behavior to the metric/indicator *and* explain its significance considering the child's determined (provided: {AGE} / "{GENDER}" or estimated) age/gender, the observation context, **and its relation to the `interview_summary_json` (i.e., does it confirm a reported issue, is it a new, potentially relevant finding, or a discrepancy?)**.

Output JSON Structure (Per Child):

[Full JSON schema as provided by the user]

**Detailed Instructions & Considerations (Apply per Child):**

- **Initial Review:** Begin by carefully reading the `interview_summary_json`. Understand the parent's primary concerns and the detailed difficulties they reported. This will guide your observation.
- **Identify & Describe:** Assign `child_id`, `description` (esp. for the primary child).
- **Age/Gender/Context:** Use the provided `age_years` ({AGE}) and `gender` ("{GENDER}") for the primary child, setting `_estimated` flags to `false`. Describe `observation_context_description`. Estimate `duration_s`. If other children are present without details, estimate their age/gender and note rationale.
- **Observational Metrics & Pattern Indicators:** Provide objective estimates/descriptions for all core metrics and populate indicator lists.
  - **Focus on Behaviors:** For all indicator lists (e.g., `dsm5_asd_indicators_observed`, `sensory_regulation_indicators_observed`), list *specific, observed behaviors* rather than diagnostic terms. If no relevant behaviors are observed for a category, state that explicitly (e.g., `["No specific indicators observed in this segment."]`). The presence of an 'indicator' means an observable behavior *potentially relevant* to a particular domain was seen; it does NOT imply that a diagnostic criterion is met or that the behavior is necessarily problematic. The clinical significance depends on frequency, intensity, pervasiveness, and impact, which this video alone cannot fully determine.
  - **Co-morbidity & Unreported Behaviors:** While watching the video, actively look for patterns of behavior that are commonly associated with the parent's reported concerns (e.g., if parent reports ADHD-like behavior in `interview_summary_json`, explicitly look for sensory sensitivities or fine motor challenges in the video, even if not mentioned by parent). Similarly, if you observe behaviors that fall into a recognized developmental domain but were not reported, include them in `additional_observed_behaviors_not_explicitly_reported_by_parent`.
- **Comparison to Parent Interview Data (`interview_data_comparison`):** This is where you explicitly connect the video observations back to the parent's report.
  - `reported_concerns_confirmed_in_video`: List parent's concerns (from `interview_summary_json`) that were observable and confirmed in the video.
  - `additional_observed_behaviors_not_explicitly_reported_by_parent`: List behaviors you observed that were *not* in the `interview_summary_json` but are clinically relevant. Provide `potential_clinical_relevance_hypothesis` to justify why this new observation is important (e.g., "While parent did not report sensory issues in `interview_summary_json`, child frequently covers ears in response to moderate noise, which is relevant to sensory processing and often co-occurs with stated attentional difficulties reported by parent.").
  - `discrepancies_between_interview_and_video`: Note any notable differences between what the parent reported in `interview_summary_json` and what was observed in the video.
- **Justification is Paramount:** Populate `justification_evidence` thoroughly (aim for 3-6 distinct key pieces of evidence). Each entry must link a specific `observed_behavior` at a `timestamp_s` to the relevant `indicator_impacted` fields. The `explanation` must justify *why* the behavior is noteworthy for the listed indicator(s), CRITICALLY considering the `observation_context_description`, the child's provided `age_years` ({AGE}) / `gender` ("{GENDER}), **and its relation to the `interview_summary_json` (i.e., does it confirm a reported issue, or is it a new, potentially relevant finding, or a discrepancy?)**.
- **Acknowledge Uncertainty:** Use cautious language. Acknowledge limitations in `analysis_limitations`. Ensure the `DISCLAIMER` is present.
- **Non-Diagnostic:** Constantly reinforce that this is observational analysis for potential indicators, requiring professional interpretation.
- **Output Format:** Ensure valid JSON array output.
- **Reporting Mindset:** Remember that this JSON output is a foundational piece of data that will be used to generate reports for both parents and professionals. Therefore, clarity, objectivity, specificity, and thoroughness are paramount. Ensure that your observations and justifications are easy to understand and directly translatable into report language.
```

---

## Integration with Gemini Provider

### Implementation Example

```python
# backend/app/services/video_analysis_service.py
from services.llm.factory import LLMFactory
from config import settings
import json

# Initialize Gemini
llm = LLMFactory.create(
    provider="gemini",
    api_key=settings.GEMINI_API_KEY,
    model="gemini-2.0-flash-exp"
)

async def analyze_child_video_with_interview(
    family_id: str,
    video_path: str,
    child_age: float,
    child_gender: str,
    interview_summary: dict
) -> dict:
    """
    Complete video analysis workflow integrating interview data.

    Args:
        family_id: Unique family identifier
        video_path: Path to uploaded video file
        child_age: Child's age in years (e.g., 3.5)
        child_gender: Child's gender ("Male", "Female", or "Child/Uncertain")
        interview_summary: Dictionary containing structured interview data

    Returns:
        dict: Structured video analysis results with DSM-5 observations
    """

    # Load the video analysis system prompt
    with open("VIDEO_ANALYSIS_SYSTEM_PROMPT.md", "r", encoding="utf-8") as f:
        prompt_template = f.read()

    # Prepare the prompt with child details and interview summary
    prompt = prompt_template.format(
        AGE=child_age,
        GENDER=child_gender,
        interview_summary_json=json.dumps(interview_summary, ensure_ascii=False, indent=2)
    )

    # Analyze video using Gemini's multimodal capabilities
    response = await llm.analyze_video(
        video_path=video_path,
        prompt=prompt,
        temperature=0.3  # Lower temperature for clinical accuracy
    )

    # Parse JSON response
    try:
        analysis_results = json.loads(response.content)
    except json.JSONDecodeError:
        # Handle cases where Gemini returns markdown-wrapped JSON
        import re
        json_match = re.search(r'```json\n(.*?)\n```', response.content, re.DOTALL)
        if json_match:
            analysis_results = json.loads(json_match.group(1))
        else:
            raise ValueError("Could not parse video analysis JSON response")

    # Save to Graphiti
    await graphiti.add_episode(
        name=f"video_analysis_{family_id}_{datetime.now().isoformat()}",
        episode_body=json.dumps(analysis_results, ensure_ascii=False),
        source_description="Gemini video analysis with interview integration",
        reference_time=datetime.now()
    )

    return {
        "analysis": analysis_results,
        "tokens_used": response.tokens_used,
        "model": response.model,
        "timestamp": datetime.now().isoformat()
    }
```

### Complete Workflow Example

```python
# Complete screening workflow: Interview → Video → Report

async def complete_screening_workflow(family_id: str):
    """
    Run the complete Chitta screening workflow.
    """

    # Step 1: Interview (already completed via chat_completion)
    interview_summary = await get_interview_summary(family_id)
    # {
    #   "child_name": "יוני",
    #   "age": 3.5,
    #   "gender": "Male",
    #   "difficulties_detailed": [
    #     {
    #       "area": "תקשורת ודיבור",
    #       "description": "דיבור מוגבל, רק מילים בודדות",
    #       "examples": "אומר רק 'אמא', 'אבא', 'מים'"
    #     },
    #     {
    #       "area": "אינטראקציה חברתית",
    #       "description": "קושי לשחק עם ילדים אחרים",
    #       "examples": "מעדיף לשחק לבד"
    #     },
    #     {
    #       "area": "התנהגויות חוזרות",
    #       "description": "מסדר צעצועים בשורות",
    #       "examples": "כל יום מסדר את המכוניות בשורה ישרה"
    #     }
    #   ],
    #   "parent_concerns_summary": "ההורים מודאגים מהתפתחות הדיבור והאינטראקציה החברתית"
    # }

    # Step 2: Generate video guidelines (based on interview)
    video_guidelines = await generate_video_guidelines(family_id, interview_summary)

    # Step 3: Wait for parent to upload video
    video_path = await wait_for_video_upload(family_id)

    # Step 4: Analyze video with interview integration
    video_analysis = await analyze_child_video_with_interview(
        family_id=family_id,
        video_path=video_path,
        child_age=interview_summary["age"],
        child_gender=interview_summary["gender"],
        interview_summary=interview_summary
    )

    # Step 5: Generate reports (parent + professional)
    reports = await generate_reports(
        family_id=family_id,
        interview_summary=interview_summary,
        video_analysis=video_analysis["analysis"]
    )

    return {
        "interview": interview_summary,
        "video_analysis": video_analysis,
        "reports": reports,
        "status": "complete"
    }
```

---

## Example Video Analysis Output

Given the example interview summary for יוני (Yoni, 3.5 years, male), Gemini might return:

```json
[
  {
    "child_id": "primary_child",
    "description": "יוני, בן 3.5",
    "age_years": 3.5,
    "age_estimated": false,
    "gender": "Male",
    "gender_estimated": false,
    "age_gender_estimation_notes": "Age and gender provided by interview data",
    "duration_s": 185.0,
    "observation_context_description": "משחק חופשי בסלון הבית עם צעצועים שונים, נוכחות אח קטן יותר ברקע",

    "eye_contact_pct": 0.15,
    "eye_contact_quality_description": "קשר עין חטוף ומוגבל. נצפה בעיקר כאשר ההורה מושיט צעצוע, אך נמנע מקשר עין במהלך ניסיון להתקשרות מילולית",
    "joint_attention_events_observed": 1,
    "joint_attention_quality_description": "אירוע אחד של תשומת לב משותפת - הצביע על מכונית שנפלה, אך לא חיפש אישור עין מההורה",

    "speech_characteristics": {
      "quantity_description": "דיבור מוגבל מאוד - 3 מילים בודדות במהלך הצילום",
      "clarity_intelligibility_description": "המילים שנאמרו ('מים', 'אמא', 'עוד') היו ברורות אך ללא צירוף של שתי מילים"
    },

    "repetitive_behaviors_observed": true,
    "repetitive_behavior_description": "התנהגות חוזרת בולטת: סידור מכוניות בשורה ישרה, חזרה על הפעולה 4 פעמים במהלך הסגמנט (חותמות זמן: 0:45, 1:20, 2:15, 2:50)",

    "interview_data_comparison": {
      "reported_concerns_confirmed_in_video": [
        {
          "interview_area": "תקשורת ודיבור",
          "interview_description": "דיבור מוגבל, רק מילים בודדות - 'אמא', 'אבא', 'מים'",
          "video_observation_confirmation": "אושר בסרטון: נצפו 3 מילים בודדות בלבד ללא צירוף מילים. המילים שנאמרו תואמות את דיווח ההורה",
          "justification_reference": ["45.2", "98.5", "152.1"]
        },
        {
          "interview_area": "התנהגויות חוזרות",
          "interview_description": "מסדר צעצועים בשורות - 'כל יום מסדר את המכוניות בשורה ישרה'",
          "video_observation_confirmation": "אושר בבירור: נצפה מסדר מכוניות בשורה ישרה 4 פעמים במהלך 3 דקות של צילום, עם התמקדות אינטנסיבית",
          "justification_reference": ["45.0", "80.0", "135.0", "170.0"]
        }
      ],
      "additional_observed_behaviors_not_explicitly_reported_by_parent": [
        {
          "behavior_description": "רגישות שמיעתית אפשרית - כיסוי אוזניים בתגובה לצליל מתון של פעמון דלת",
          "potential_clinical_relevance_hypothesis": "התנהגות זו לא דווחה בראיון ההורים, אך עשויה להיות רלוונטית להבנת עיבוד חושי. רגישות חושית נפוצה בקרב ילדים עם קשיים בתקשורת חברתית שדווחו על ידי ההורה, ועשויה להשפיע על האינטראקציה החברתית",
          "justification_reference": ["67.5"]
        }
      ],
      "discrepancies_between_interview_and_video": [
        {
          "interview_statement": "קושי לשחק עם ילדים אחרים - מעדיף לשחק לבד",
          "video_observation_discrepancy": "בסרטון זה, האח הקטן ניגש ליוני פעם אחת (1:45) ויוני לא דחה אותו באופן פעיל, אך גם לא יזם אינטראקציה",
          "explanation_of_discrepancy": "הסגמנט הנצפה קצר ומכיל אינטראקציה מוגבלת עם ילד אחר. ההתנהגות עשויה להיות שונה בסביבות חברתיות אחרות או עם ילדים לא מוכרים. הדיווח ההורי מתבסס על תצפיות רחבות יותר בזמן ובהקשרים שונים"
        }
      ]
    },

    "justification_evidence": [
      {
        "timestamp_s": "45.0-50.0",
        "observed_behavior": "יוני מסדר 5 מכוניות בשורה ישרה מדויקת, מתקן את המרחק ביניהן באופן חוזר",
        "indicator_impacted": ["dsm5_asd_indicators_observed.criterion_B_RRB", "repetitive_behaviors_observed"],
        "explanation": "התנהגות זו מאשרת את הדיווח ההורי על 'סידור צעצועים בשורות'. היא רלוונטית ל-DSM-5 קריטריון B (RRB) עבור ASD, במיוחד 'שימוש סטריאוטיפי בחפצים'. בגיל 3.5, רמת הדיוק והחזרתיות של הפעולה (נצפתה 4 פעמים) עשויה להצביע על דפוס מוגבר מהצפוי להתפתחות טיפוסית. בהתחשב בקשיים בתקשורת החברתית שדווחו בראיון, התנהגות זו מספקת תצפית משלימה החשובה להערכה מקיפה"
      },
      {
        "timestamp_s": "98.5",
        "observed_behavior": "יוני אומר 'מים' בעת הצבעה על כוס, ללא קשר עין או מחווה משלימה להורה",
        "indicator_impacted": ["speech_characteristics", "joint_attention_quality", "dsm5_asd_indicators_observed.criterion_A_social_comm"],
        "explanation": "מאשר דיווח הורי על שימוש במילים בודדות. בגיל 3.5, רוב הילדים משתמשים במשפטים של 3-4 מילים. היעדר צירוף מילים ומחוות משלימות (למשל, הושטת כוס + קשר עין + אמירת 'מים בבקשה') רלוונטי ל-DSM-5 קריטריון A - 'ליקויים בשימוש משולב בתקשורת מילולית ולא מילולית'. התצפית עולה בקנה אחד עם דאגת ההורים מפיגור בדיבור ותומכת בצורך בהערכה מעמיקה יותר של התפתחות השפה"
      }
    ],

    "dsm5_asd_indicators_observed": {
      "criterion_A_social_comm": [
        "תצפית: שימוש מוגבל במחוות לתמיכה בתקשורת (חותמת זמן 98.5)",
        "תצפית: קשר עין חטוף ומוגבל במהלך ניסיונות אינטראקציה (חותמות זמן מרובות)",
        "תצפית: חוסר יוזמה לשיתוף עניין או הנאה עם אחרים באופן ספונטני"
      ],
      "criterion_B_RRB": [
        "תצפית: שימוש סטריאוטיפי בחפצים - סידור מכוניות בשורה ישרה באופן חוזר (חותמות זמן 45.0, 80.0, 135.0, 170.0)",
        "תצפית: עיסוק אינטנסיבי בפעילות חוזרת, התנגדות לשינוי כאשר אח מנסה להפריע (חותמת זמן 105.0)"
      ]
    },

    "observed_strengths_and_positive_behaviors": [
      {
        "strength_or_positive_behavior": "התמדה במשימה - המשיך בפעילות סידור המכוניות למרות הפרעות",
        "relevance_or_confirmation_of_interview_data": "תצפית חדשה: מצביעה על יכולת ריכוז ממושכת בפעילות מועדפת, לא דווחה במפורש בראיון",
        "justification_reference": ["45.0", "80.0"]
      }
    ],

    "analysis_limitations": [
      "Based on a single, potentially brief video segment.",
      "Observation setting may not be representative of behavior in other contexts (e.g., preschool, playground).",
      "Inability to assess internal states, thoughts, or feelings directly.",
      "Video does not provide full developmental history or information from other sources (e.g., teachers, pediatrician).",
      "Potential influence of the recording process itself on behavior.",
      "Limited observation of peer interaction due to minimal presence of same-age children in segment."
    ],

    "DISCLAIMER": "This analysis is based solely on observable behaviors within a limited video segment, interpreted in light of the parent's initial report. It is NOT a clinical diagnosis, assessment, or substitute for evaluation by qualified healthcare professionals (e.g., psychologists, pediatricians, developmental specialists). Observations require interpretation within a broader clinical context, including comprehensive developmental history, information from multiple sources (parents, teachers), and potentially standardized assessments."
  }
]
```

---

## Key Features of This Prompt

### 1. **Integration with Interview Data**
- Actively compares video observations to parent's reported concerns
- Confirms or refutes parent's observations
- Identifies new behaviors not reported by parent
- Notes discrepancies between interview and video

### 2. **Clinical Framework (DSM-5)**
- Organizes observations by DSM-5 domains
- Uses clinically relevant categories (ASD Criterion A/B, ADHD, etc.)
- **Does NOT provide diagnostic scores** - only observational indicators

### 3. **Evidence-Based Justification**
- Every observation linked to specific timestamps
- Explains significance in context of age, gender, activity
- References interview data to show confirmation/discrepancy

### 4. **Comprehensive Coverage**
- Social communication
- Repetitive behaviors
- Attention and activity level
- Sensory processing
- Motor skills
- Parent-child interaction
- Strengths and positive behaviors

### 5. **Non-Diagnostic Stance**
- Explicit disclaimer
- Acknowledges limitations
- Uses cautious, observational language
- Designed for professional interpretation

---

## Usage in Production

```python
# In your video processing endpoint
@router.post("/api/video/analyze")
async def analyze_video_endpoint(
    family_id: str,
    video_file: UploadFile
):
    # Save video
    video_path = await save_video(family_id, video_file)

    # Get interview summary
    interview_summary = await get_interview_summary(family_id)

    # Analyze with Gemini
    analysis = await analyze_child_video_with_interview(
        family_id=family_id,
        video_path=video_path,
        child_age=interview_summary["age"],
        child_gender=interview_summary["gender"],
        interview_summary=interview_summary
    )

    return {
        "status": "success",
        "analysis": analysis["analysis"],
        "next_steps": ["generate_reports"]
    }
```

---

This prompt enables Chitta to provide clinically rigorous, evidence-based video analysis that integrates seamlessly with the conversational interview data, all while maintaining strict observational boundaries and clinical ethics.
