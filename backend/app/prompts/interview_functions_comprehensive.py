"""
Comprehensive Interview Function Definitions - Simplified Architecture

These 5 functions replace the Sage+Hand architecture.
ALL intent detection is handled via function calling - no separate LLM calls!

Functions:
1. extract_interview_data - Extract structured data during conversation
2. ask_developmental_question - Parent asks general developmental question
3. ask_about_analysis - Parent asks about Chitta's specific analysis
4. ask_about_app - Parent asks about the app/process
5. request_action - Parent wants to do something specific
"""

from typing import List, Dict, Any


# === Function 1: Interview Data Extraction ===

EXTRACT_INTERVIEW_DATA = {
    "name": "extract_interview_data",
    "description": """Extract structured child development data from the conversation.

Call this WHENEVER the parent shares relevant information in THIS turn.

Examples:
- Parent mentions child's name, age, gender
- Parent describes concerns, challenges, difficulties
- Parent shares strengths, interests, what child likes
- Parent describes daily routines, behaviors, situations
- Parent mentions developmental history, milestones
- Parent describes family context, siblings, support
- Parent states goals or hopes

Extract whatever NEW information is available from THIS turn.""",
    "parameters": {
        "type": "object",
        "properties": {
            "child_name": {
                "type": "string",
                "description": "Child's name if mentioned"
            },
            "age": {
                "type": "number",
                "description": "Age in years (can be decimal like 3.5)"
            },
            "gender": {
                "type": "string",
                "enum": ["male", "female", "unknown"],
                "description": "Can often infer from Hebrew grammar (הוא/היא)"
            },
            "primary_concerns": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": [
                        "speech", "social", "attention", "motor", "sensory",
                        "emotional", "behavioral", "learning", "sleep", "eating", "other"
                    ]
                },
                "description": "Only if parent EXPLICITLY mentioned - don't infer!"
            },
            "concern_details": {
                "type": "string",
                "description": "Specific examples with context: what happens, when, frequency, impact"
            },
            "strengths": {
                "type": "string",
                "description": "Interests, favorite activities, things they're good at"
            },
            "developmental_history": {
                "type": "string",
                "description": "Pregnancy, birth, milestones, medical history, diagnoses"
            },
            "family_context": {
                "type": "string",
                "description": "Siblings, family history, educational setting, support"
            },
            "daily_routines": {
                "type": "string",
                "description": "Typical day, sleep patterns, eating, behaviors at home vs school"
            },
            "parent_goals": {
                "type": "string",
                "description": "What parent hopes to achieve, improve, understand"
            },
            "urgent_flags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Safety concerns requiring immediate attention"
            }
        },
        "required": []
    }
}


# === Function 2: Developmental Question (General Consultation) ===

ASK_DEVELOPMENTAL_QUESTION = {
    "name": "ask_developmental_question",
    "description": """Call when parent asks a general developmental or professional question.

Examples:
- "מה זה ADHD?" (What is ADHD?)
- "האם זה נורמלי שהוא לא מדבר בגיל 3?" (Is it normal not to talk at age 3?)
- "למה ילדים עם אוטיזם לא אוהבים קשר עין?" (Why don't autistic kids like eye contact?)
- "איזה טיפול יעזור לו?" (What therapy would help?)
- "איך אני אמורה להגיב כשהוא כועס?" (How should I respond when angry?)

Don't call for:
- Questions about YOUR specific analysis (use ask_about_analysis)
- Questions about the app (use ask_about_app)""",
    "parameters": {
        "type": "object",
        "properties": {
            "question_topic": {
                "type": "string",
                "enum": [
                    "developmental_milestone",    # אבני דרך התפתחותיות
                    "diagnosis_explanation",      # הסבר על אבחון/מצב
                    "therapy_options",            # אפשרויות טיפול
                    "behavior_understanding",     # הבנת התנהגות
                    "parenting_strategy",         # איך להגיב/לנהוג
                    "educational_approach",       # גישה חינוכית
                    "general_developmental"       # כללי התפתחותי
                ],
                "description": "The category of the developmental question"
            },
            "question_text": {
                "type": "string",
                "description": "The actual question for context"
            },
            "relates_to_child": {
                "type": "boolean",
                "description": "True if asking specifically about their child's situation"
            }
        },
        "required": ["question_topic", "question_text"]
    }
}


# === Function 3: Ask About Analysis (Specific Consultation) ===

ASK_ABOUT_ANALYSIS = {
    "name": "ask_about_analysis",
    "description": """Call when parent asks about YOUR specific analysis or conclusions.

Examples:
- "למה אמרת שיש לו חיפוש חושי?" (Why did you say he has sensory seeking?)
- "איך הגעת למסקנה הזאת?" (How did you reach this conclusion?)
- "מה ראית בסרטונים שגרם לך לחשוב ככה?" (What did you see in videos?)
- "למה המלצת על הדבר הזה?" (Why did you recommend this?)
- "איפה ראית את זה שכתבת בדוח?" (Where did you see what you wrote?)""",
    "parameters": {
        "type": "object",
        "properties": {
            "analysis_element": {
                "type": "string",
                "enum": [
                    "video_observation",         # מה ראית בסרטון
                    "concern_identification",    # למה זיהית דאגה זו
                    "strength_identification",   # למה אמרת שזו חוזקה
                    "recommendation",            # למה המלצת על זה
                    "general_conclusion"         # שאלה כללית על המסקנה
                ],
                "description": "What aspect of the analysis they're asking about"
            },
            "question_text": {
                "type": "string",
                "description": "What they're asking"
            },
            "artifact_reference": {
                "type": "string",
                "description": "Which artifact they're referring to (report, guidelines, etc.)"
            }
        },
        "required": ["analysis_element", "question_text"]
    }
}


# === Function 4: Ask About App (Process/Help) ===

ASK_ABOUT_APP = {
    "name": "ask_about_app",
    "description": """Call when parent asks about the app itself, features, or process.

Examples:
- "איך מעלים סרטון?" (How do I upload a video?)
- "מה קורה אחרי שאעלה את הסרטונים?" (What happens after upload?)
- "איפה אני רואה את הדוח?" (Where do I see the report?)
- "איך זה עובד?" (How does this work?)
- "מה הצעד הבא?" (What's the next step?)
- "למה אני לא רואה את הכפתור?" (Why don't I see the button?)""",
    "parameters": {
        "type": "object",
        "properties": {
            "help_topic": {
                "type": "string",
                "enum": [
                    "how_to_upload_video",       # איך מעלים סרטון
                    "where_to_find_report",      # איפה הדוח
                    "process_explanation",       # איך זה עובד
                    "next_steps",                # מה הצעד הבא
                    "app_features",              # מה האפליקציה יכולה
                    "technical_issue",           # בעיה טכנית
                    "general_help"               # עזרה כללית
                ],
                "description": "What aspect of the app they need help with"
            },
            "question_text": {
                "type": "string",
                "description": "What they're asking"
            }
        },
        "required": ["help_topic", "question_text"]
    }
}


# === Function 5: Request Action ===

REQUEST_ACTION = {
    "name": "request_action",
    "description": """Call when parent explicitly requests to DO something specific.

Examples:
- "תכיני לי הנחיות צילום" (Generate guidelines for me)
- "תראי לי את הדוח" (Show me the report)
- "אני רוצה להעלות סרטון" (I want to upload a video)
- "רוצה לדבר עם מומחה" (Want to talk to an expert)
- "תשתפי את הדוח עם הגננת" (Share report with teacher)

Don't call for:
- Questions (use other ask_* functions)
- Just continuing conversation (no function needed)""",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "generate_guidelines",        # תכיני הנחיות צילום
                    "view_guidelines",            # תראי לי את ההנחיות
                    "upload_video",               # רוצה להעלות סרטון
                    "view_report",                # רוצה לראות דוח
                    "schedule_consultation",      # קביעת פגישה עם מומחה
                    "find_experts",               # מציאת מומחים
                    "share_report",               # שיתוף דוח
                    "add_journal_entry",          # כתיבת יומן
                    "view_journal"                # צפייה ביומן
                ],
                "description": "The specific action requested"
            },
            "details": {
                "type": "string",
                "description": "Additional context about the request"
            }
        },
        "required": ["action"]
    }
}


# === All Comprehensive Functions ===

INTERVIEW_FUNCTIONS_COMPREHENSIVE: List[Dict[str, Any]] = [
    EXTRACT_INTERVIEW_DATA,
    ASK_DEVELOPMENTAL_QUESTION,
    ASK_ABOUT_ANALYSIS,
    ASK_ABOUT_APP,
    REQUEST_ACTION
]


# === Helper Functions ===

def get_function_by_name(name: str) -> Dict[str, Any]:
    """Get function definition by name"""
    for func in INTERVIEW_FUNCTIONS_COMPREHENSIVE:
        if func["name"] == name:
            return func
    raise ValueError(f"Function {name} not found")


def get_function_names() -> List[str]:
    """Get list of all function names"""
    return [func["name"] for func in INTERVIEW_FUNCTIONS_COMPREHENSIVE]
