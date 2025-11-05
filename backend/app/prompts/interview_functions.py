"""
Interview Function Definitions for LLM Function Calling

These functions enable continuous extraction during natural conversation.
The LLM calls these functions to:
1. Extract structured interview data opportunistically
2. Signal when user wants to perform an action
3. Check if interview is complete
"""

from typing import List, Dict, Any


# === Interview Data Extraction Function ===

EXTRACT_INTERVIEW_DATA = {
    "name": "extract_interview_data",
    "description": """Extract structured child development data from the conversation.

Call this function WHENEVER the parent shares relevant information - don't wait for complete answers or milestones.

Examples of when to call:
- Parent mentions child's name, age, or gender
- Parent describes strengths, interests, or what child likes to do
- Parent shares concerns, challenges, or difficulties
- Parent describes daily routines, behaviors, or typical situations
- Parent mentions developmental history, pregnancy, birth, milestones
- Parent describes family context, siblings, support systems
- Parent states goals or what they hope will improve

Extract whatever information is available - partial data is fine. You'll be called multiple times throughout the conversation.""",
    "parameters": {
        "type": "object",
        "properties": {
            "child_name": {
                "type": "string",
                "description": "Child's name if mentioned (leave empty if not shared)"
            },
            "age": {
                "type": "number",
                "description": "Child's exact age in years (can be decimal like 3.5). Leave empty if not mentioned."
            },
            "gender": {
                "type": "string",
                "enum": ["male", "female", "unknown"],
                "description": "Child's gender. Can often infer from Hebrew grammar (הוא/היא). Use 'unknown' if unclear."
            },
            "primary_concerns": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": [
                        "speech",           # דיבור, שפה, תקשורת
                        "social",           # חברתי, קשר עין, אינטראקציה
                        "attention",        # קשב, ריכוז, היפראקטיביות
                        "motor",            # מוטורי, תנועה, קואורדינציה
                        "sensory",          # חושי, רגישויות
                        "emotional",        # רגשי, חרדות, פחדים
                        "behavioral",       # התנהגות, כעסים, התפרצויות
                        "learning",         # למידה, קוגניטיבי
                        "sleep",            # שינה
                        "eating",           # אכילה
                        "other"             # אחר
                    ]
                },
                "description": "Categories of concerns mentioned by parent. Can select multiple."
            },
            "concern_details": {
                "type": "string",
                "description": "Detailed description of concerns with specific examples from parent. Include: what happens, when, frequency, impact on daily life."
            },
            "strengths": {
                "type": "string",
                "description": "Child's interests, favorite activities, things they're good at, special talents or skills."
            },
            "developmental_history": {
                "type": "string",
                "description": "Information about pregnancy, birth, early developmental milestones (sitting, walking, first words), medical history, previous diagnoses."
            },
            "family_context": {
                "type": "string",
                "description": "Siblings, family developmental history (other family members with similar challenges), educational setting (gan, school), support systems, family structure."
            },
            "daily_routines": {
                "type": "string",
                "description": "Description of typical day, morning/evening routines, behaviors at home vs. school/gan, sleep patterns, eating patterns."
            },
            "parent_goals": {
                "type": "string",
                "description": "What parent hopes to achieve, what they want to improve, their aspirations for the child."
            },
            "urgent_flags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Any safety concerns or red flags requiring immediate attention (self-harm, severe aggression, regression, medical concerns)."
            }
        },
        "required": []  # Nothing is required - extract whatever is available
    }
}


# === User Action Intent Function ===

USER_WANTS_ACTION = {
    "name": "user_wants_action",
    "description": """Call this when the user clearly wants to perform a specific action or move to a different task.

Examples:
- "רוצה לראות את הדוח" → action: "view_report"
- "איך מעלים סרטון?" → action: "upload_video"
- "תראי לי את ההנחיות" → action: "view_video_guidelines"
- "רוצה לדבר עם מישהו" → action: "consultation_mode"
- "איפה היומן שלי?" → action: "view_journal"
- "רוצה למצוא מומחים" → action: "find_experts"

Don't call this for clarifying questions during the interview - only for clear intent to DO something.""",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "view_report",              # רוצה לראות דוח
                    "upload_video",             # רוצה להעלות סרטון
                    "view_video_guidelines",    # רוצה לראות הנחיות צילום
                    "consultation_mode",        # רוצה לדבר/להתייעץ
                    "add_journal_entry",        # רוצה לכתוב ביומן
                    "view_journal",             # רוצה לראות יומן
                    "find_experts",             # רוצה למצוא מומחים
                    "share_report"              # רוצה לשתף דוח
                ],
                "description": "The specific action the user wants to perform"
            },
            "details": {
                "type": "string",
                "description": "Additional context about what the user wants (optional)"
            }
        },
        "required": ["action"]
    }
}


# === Interview Completeness Check Function ===

CHECK_INTERVIEW_COMPLETENESS = {
    "name": "check_interview_completeness",
    "description": """Call this to evaluate if enough information has been gathered to complete the interview and generate personalized video guidelines.

Call this when:
1. You've collected substantial information across multiple areas
2. Parent signals they're done ("זה הכל", "סיימתי", "אין לי יותר מה להוסיף")
3. You've asked about all major areas and got responses

Don't call too early - we need enough context to create meaningful video guidelines.""",
    "parameters": {
        "type": "object",
        "properties": {
            "ready_to_complete": {
                "type": "boolean",
                "description": "True if sufficient information has been collected to generate useful video guidelines. False if more information needed."
            },
            "missing_critical_info": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of critical pieces of information still needed (e.g., 'child age', 'primary concerns', 'specific examples'). Empty if ready to complete."
            },
            "completeness_estimate": {
                "type": "number",
                "description": "Estimated completeness percentage (0-100). Consider: basic info (20%), concerns with details (40%), developmental history (20%), family context (10%), parent goals (10%)."
            }
        },
        "required": ["ready_to_complete"]
    }
}


# === All Interview Functions (for LLM) ===

INTERVIEW_FUNCTIONS: List[Dict[str, Any]] = [
    EXTRACT_INTERVIEW_DATA,
    USER_WANTS_ACTION,
    CHECK_INTERVIEW_COMPLETENESS
]


# === Helper: Get function by name ===

def get_function_by_name(name: str) -> Dict[str, Any]:
    """Get function definition by name"""
    for func in INTERVIEW_FUNCTIONS:
        if func["name"] == name:
            return func
    raise ValueError(f"Function {name} not found")
