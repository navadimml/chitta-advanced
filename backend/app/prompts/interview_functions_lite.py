"""
Interview Function Definitions - LITE VERSION for Less Capable Models

These are simplified versions of the interview functions optimized for
models with weaker function calling capabilities (e.g., Gemini Flash).

Key changes:
1. Fewer optional parameters (only most important fields)
2. Simpler descriptions
3. Clearer examples
4. More explicit required fields
"""

from typing import List, Dict, Any


# === Simplified Interview Data Extraction ===

EXTRACT_INTERVIEW_DATA_LITE = {
    "name": "extract_interview_data",
    "description": """Extract child development data from conversation.

CALL THIS FUNCTION IMMEDIATELY whenever parent mentions:
- Child's name, age, or gender
- Concerns or challenges
- Strengths or interests
- Any other relevant information

Don't wait - extract whatever information is available right now!""",
    "parameters": {
        "type": "object",
        "properties": {
            "child_name": {
                "type": "string",
                "description": "Child's name (leave empty if not mentioned)"
            },
            "age": {
                "type": "number",
                "description": "Child's age in years (can be decimal like 3.5)"
            },
            "gender": {
                "type": "string",
                "enum": ["male", "female", "unknown"],
                "description": "Child's gender. Infer from Hebrew (הוא=male, היא=female)"
            },
            "concerns": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["speech", "social", "attention", "motor", "sensory", "emotional", "behavioral", "learning", "sleep", "eating", "other"]
                },
                "description": "ONLY if parent expresses WORRY/DIFFICULTY/PROBLEM! Categories of concerns. DO NOT extract positive behaviors (like 'plays well with kids') as concerns - those are strengths!"
            },
            "concern_description": {
                "type": "string",
                "description": "Everything about concerns (including developmental history like 'started talking late'). Copy parent's words with examples and context."
            },
            "strengths": {
                "type": "string",
                "description": "COPY PARENT'S EXACT WORDS about positive things! Parent says 'רץ ומטפס' → write 'רץ ומטפס'. DO NOT categorize (like 'יכולות מוטוריות') - use their actual words!"
            },
            "other_info": {
                "type": "string",
                "description": "ONLY neutral/positive context: siblings, daycare, typical routines, parent hopes. DO NOT duplicate information already in concerns/strengths/concern_description! If milestone relates to a concern (late speech) → use concern_description, NOT here!"
            }
        },
        "required": []  # Nothing required - extract what's available
    }
}


# === User Action Intent ===

USER_WANTS_ACTION_LITE = {
    "name": "user_wants_action",
    "description": """Call when user wants to DO something specific.

Examples:
- "רוצה לראות דוח" → action: "view_report"
- "איך מעלים סרטון" → action: "upload_video"
- "תראי לי הנחיות" → action: "view_video_guidelines"

Only call for ACTIONS, not for questions during interview.""",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "view_report",
                    "upload_video",
                    "view_video_guidelines",
                    "consultation_mode",
                    "add_journal_entry",
                    "view_journal",
                    "find_experts",
                    "share_report"
                ],
                "description": "The action user wants to perform"
            }
        },
        "required": ["action"]
    }
}


# === Interview Completion Check ===

CHECK_INTERVIEW_COMPLETENESS_LITE = {
    "name": "check_interview_completeness",
    "description": """Call when user signals they are done talking.

Signals that user is done:
- "זה הכל"
- "סיימתי"
- "אין לי יותר מה להוסיף"

Only call this when user clearly wants to finish.""",
    "parameters": {
        "type": "object",
        "properties": {
            "ready_to_complete": {
                "type": "boolean",
                "description": "True if enough information collected to create video guidelines"
            },
            "completeness_percentage": {
                "type": "number",
                "description": "Estimate 0-100. Need: basic info (20%), concerns (35%), strengths (15%), context (30%)"
            },
            "what_is_missing": {
                "type": "string",
                "description": "What critical information is still missing (if any)"
            }
        },
        "required": ["ready_to_complete"]
    }
}


# === All Functions (Lite Version) ===

INTERVIEW_FUNCTIONS_LITE: List[Dict[str, Any]] = [
    EXTRACT_INTERVIEW_DATA_LITE,
    USER_WANTS_ACTION_LITE,
    CHECK_INTERVIEW_COMPLETENESS_LITE
]


# === Helper Functions ===

def get_function_by_name_lite(name: str) -> Dict[str, Any]:
    """Get lite function definition by name"""
    for func in INTERVIEW_FUNCTIONS_LITE:
        if func["name"] == name:
            return func
    raise ValueError(f"Function {name} not found in lite functions")


def should_use_lite_functions(model_name: str) -> bool:
    """
    Determine if we should use lite functions based on model

    Use lite functions for:
    - Gemini Flash models (ONLY if LLM_USE_ENHANCED is true)
    - Smaller/faster models (ONLY if LLM_USE_ENHANCED is true)
    - Models known to have weaker function calling (ONLY if LLM_USE_ENHANCED is true)

    If LLM_USE_ENHANCED=false, ALWAYS use full functions regardless of model.

    Use full functions for:
    - Gemini Pro 2.0
    - GPT-4
    - Claude Opus/Sonnet
    - Other high-capability models
    - ANY model when LLM_USE_ENHANCED=false
    """
    import os

    # Check if enhanced mode is enabled
    use_enhanced_env = os.getenv("LLM_USE_ENHANCED", "true").lower()
    use_enhanced = use_enhanced_env in ["true", "1", "yes"]

    # If enhanced mode is disabled, NEVER use lite functions
    if not use_enhanced:
        return False

    # Only check model indicators if enhanced mode is on
    model_lower = model_name.lower()

    # Models that should use lite functions
    lite_models = [
        "flash",           # Gemini Flash
        "gemini-1.5-flash",
        "gemini-2.0-flash",
        "gpt-3.5",         # GPT-3.5
        "small",           # Any "small" model
        "mini",            # Any "mini" model
        "lite",            # Any "lite" model
    ]

    for lite_indicator in lite_models:
        if lite_indicator in model_lower:
            return True

    return False


def get_appropriate_functions(model_name: str) -> List[Dict[str, Any]]:
    """
    Get the appropriate function set for the model

    Returns:
        INTERVIEW_FUNCTIONS_LITE for less capable models
        INTERVIEW_FUNCTIONS for high-capability models
    """
    if should_use_lite_functions(model_name):
        return INTERVIEW_FUNCTIONS_LITE

    # Import full functions
    from .interview_functions import INTERVIEW_FUNCTIONS
    return INTERVIEW_FUNCTIONS
