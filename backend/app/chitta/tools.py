"""
Chitta Tool Definitions - Simplified

5 tools for Darshan to perceive and learn.

DESIGN PRINCIPLES:
- Minimum NECESSARY complexity
- Each tool has a clear, distinct purpose
- Gemini-compatible schemas (at least one required field)

Tools:
1. notice - Record observation about child
2. wonder - Spawn new curiosity (4 types)
3. capture_story - Capture meaningful story
4. add_evidence - Add evidence to active exploration
5. spawn_exploration - Start focused exploration
"""

from typing import List, Dict, Any


# === Tool Definitions ===

TOOL_NOTICE = {
    "name": "notice",
    "description": """Record an observation about the child.

Use this when you learn something about the child from the conversation.
This could be a fact, behavior, preference, or characteristic.

**TEMPORAL DATA IS CRITICAL** - Extract timing information into structured fields:

Examples:
- "אתמול הוא שיחק יפה" → when_type: "days_ago", when_value: 1
- "לפני שבוע התחיל לישון טוב" → when_type: "weeks_ago", when_value: 1
- "בגיל שנה התחיל ללכת" → when_type: "age_months", when_value: 12
- "בגיל שנתיים דיבר" → when_type: "age_months", when_value: 24
- "בדרך כלל הוא רגוע" → when_type: "habitual", when_value: null
- "עכשיו יותר קל לו" → when_type: "now", when_value: null
- "הוא אוהב דינוזאורים" → when_type: null (no timing mentioned)

For CHANGE over time - use TWO notices:
- "פעם היה קשה, עכשיו יותר קל" →
  1. notice: "היה קשה לו", when_type: "past_unspecified"
  2. notice: "יותר קל", when_type: "now"
""",
    "parameters": {
        "type": "object",
        "properties": {
            "observation": {
                "type": "string",
                "description": "What was observed or learned about the child (concise)"
            },
            "domain": {
                "type": "string",
                "description": """Developmental domain. Use specific domains:
- birth_history: pregnancy, labor, delivery, complications at birth
- medical: health issues, hospitalizations, diagnoses, medications
- milestones: "when did X start" timing info (first words, first steps, toilet training)
- motor/language/social/cognitive: current abilities in these areas
- sensory: sensitivities to sound, touch, light, textures
- regulation: self-calming, managing emotions, transitions
- sleep/feeding: daily routines
- context: family situation, living environment, childcare""",
                "enum": ["motor", "social", "emotional", "cognitive", "language", "sensory", "regulation", "essence", "strengths", "context", "concerns", "general", "sleep", "feeding", "play", "birth_history", "milestones", "medical", "regression"]
            },
            "when_type": {
                "type": "string",
                "description": "Type of temporal reference",
                "enum": ["now", "days_ago", "weeks_ago", "months_ago", "age_months", "habitual", "past_unspecified"]
            },
            "when_value": {
                "type": "number",
                "description": "Numeric value for the temporal type: days/weeks/months ago, or age in months. Examples: days_ago+1=yesterday, age_months+12=at 1 year old, age_months+24=at 2 years"
            },
            "confidence": {
                "type": "number",
                "description": "How confident (0-1). Default 0.7"
            }
        },
        "required": ["observation", "domain"]
    }
}


TOOL_WONDER = {
    "name": "wonder",
    "description": """Spawn a new curiosity about the child.

Choose the type based on what kind of exploration this is:

- **discovery**: Open receiving, no specific question
  Example: "Understanding his essence", "What makes her unique"

- **question**: Following a specific thread
  Example: "What triggers meltdowns?", "How does he communicate needs?"

- **hypothesis**: Testing a theory that could be confirmed/refuted
  Example: "Music helps him regulate", "Transitions are harder in mornings"
  Set video_appropriate=true if this could be tested by observing video

  IMPORTANT: Frame the theory as TENTATIVE, not as fact:
  ❌ "הקושי במעברים נובע מרגישות חושית" (stating mechanism as fact)
  ✅ "יכול להיות שמעברים קשים כי השינוי מרגיש גדול עבורו" (tentative)

- **pattern**: Connecting dots across domains
  Example: "Sensory input affects regulation", "Social challenges link to communication"

IMPORTANT: Certainty is INDEPENDENT of type.
- Low certainty (0.2-0.3) = just starting to explore
- High certainty (0.7-0.8) = nearly confirmed/answered

VIDEO VALUE:
When you notice that video observation could add value beyond conversation,
specify WHY in video_value. Only use when video provides something
conversation cannot:

- "calibration": Parent made absolute claim ("never", "always") about
  clinically significant behavior. Video could show the actual picture.
- "chain": Multiple domains seem connected. Video could reveal the sequence.
- "discovery": We've never seen this child. Baseline observation could
  reveal things we don't know to ask about.
- "reframe": Parent describes concern that might actually be a strength
  when seen in context.
- "relational": The parent-child interaction pattern itself is the question.

Leave video_value empty if conversation is sufficient.
""",
    "parameters": {
        "type": "object",
        "properties": {
            "about": {
                "type": "string",
                "description": "What we're curious about"
            },
            "type": {
                "type": "string",
                "enum": ["discovery", "question", "hypothesis", "pattern"],
                "description": "Type of curiosity"
            },
            "certainty": {
                "type": "number",
                "description": "How confident within this type (0-1). Low=just starting, High=nearly answered/confirmed"
            },
            "domain": {
                "type": "string",
                "description": "Primary developmental domain"
            },
            "theory": {
                "type": "string",
                "description": "For hypothesis: the theory to test. Use TENTATIVE language (יכול להיות ש..., נראה ש..., אולי...). NEVER state mechanisms as facts."
            },
            "video_appropriate": {
                "type": "boolean",
                "description": "For hypothesis: can video observation test this?"
            },
            "video_value": {
                "type": "string",
                "enum": ["calibration", "chain", "discovery", "reframe", "relational"],
                "description": "WHY video would add value beyond conversation. Only set if video provides unique insight."
            },
            "video_value_reason": {
                "type": "string",
                "description": "Brief explanation of what video could reveal that conversation cannot."
            },
            "question": {
                "type": "string",
                "description": "For question: the specific question to explore"
            },
            "domains_involved": {
                "type": "array",
                "items": {"type": "string"},
                "description": "For pattern: domains that are connected"
            }
        },
        "required": ["about", "type"]
    }
}


TOOL_CAPTURE_STORY = {
    "name": "capture_story",
    "description": """Capture a meaningful story shared by the parent.

Stories are GOLD - a skilled observer sees MULTIPLE signals in ONE story.

When to use:
- Parent shares a specific incident or moment
- The story reveals something about who the child IS
- There are developmental signals to extract

Example input: "אתמול בגן ראתה ילד אחר בוכה והלכה לטפוח לו על הגב"

Example output:
- summary: "בגן, ניגשה לילד בוכה וטפחה לו על הגב"
- reveals: ["שמה לב כשמישהו עצוב", "ניגשת לעזור מעצמה", "לא מפחדת מילדים לא מוכרים"]
- domains: ["social", "emotional"]
- significance: 0.8 (high - reveals core nature)

IMPORTANT - Use SITUATIONAL language in Hebrew, not clinical terms:
✗ "empathy" → ✓ "שם לב כשמישהו עצוב"
✗ "emotional regulation" → ✓ "יודע להירגע אחרי כעס"
✗ "sensory sensitivity" → ✓ "מתקשה עם רעשים חזקים"
✗ "prosocial behavior" → ✓ "רוצה לעזור לאחרים"
✗ "transition difficulty" → ✓ "קשה לו לעבור מפעילות לפעילות"

Be generous with what a story reveals. Look for:
- What it shows about their nature/essence
- What developmental capacities it demonstrates
- What it suggests about their inner world
""",
    "parameters": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "Brief summary of the story (1-2 sentences)"
            },
            "reveals": {
                "type": "array",
                "items": {"type": "string"},
                "description": "What this story reveals - in SITUATIONAL Hebrew ('שם לב כש...', 'יודע ל...', 'אוהב...'). NOT clinical terms. Be thorough - one story can reveal many things."
            },
            "domains": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Developmental domains touched: social, emotional, motor, cognitive, language, sensory, regulation"
            },
            "significance": {
                "type": "number",
                "description": "How significant is this story (0-1). High = reveals who this child IS at their core."
            }
        },
        "required": ["summary", "reveals", "domains", "significance"]
    }
}


TOOL_ADD_EVIDENCE = {
    "name": "add_evidence",
    "description": """Add evidence to an active exploration.

Use this when:
- Something the parent shared relates to an active exploration
- You have new information that supports/contradicts/transforms a hypothesis
- You're gathering data for an ongoing investigation

Effects:
- "supports": Increases confidence in hypothesis
- "contradicts": Decreases confidence in hypothesis
- "transforms": Changes our understanding - hypothesis may need revision
""",
    "parameters": {
        "type": "object",
        "properties": {
            "cycle_id": {
                "type": "string",
                "description": "ID of the active exploration"
            },
            "evidence": {
                "type": "string",
                "description": "The evidence content"
            },
            "effect": {
                "type": "string",
                "enum": ["supports", "contradicts", "transforms"],
                "description": "How this evidence affects the exploration"
            }
        },
        "required": ["cycle_id", "evidence"]
    }
}


TOOL_RECORD_MILESTONE = {
    "name": "record_milestone",
    "description": """Record a developmental milestone with age.

Use when parent mentions WHEN something happened:
- "He started walking at 14 months"
- "First words around age 1"
- "Toilet trained at 3"
- "Started therapy at 2.5"

Also record regressions:
- "Lost words at 18 months"
- "Stopped playing with other kids around age 2"

And birth/pregnancy history (use domain='birth_history'):
- Birth moment: milestone_type='birth' (e.g., "C-section", "Natural birth")
- Pregnancy events: milestone_type='concern' or 'achievement' (e.g., "Born at 36 weeks", "Difficult pregnancy")

Timeline order: pregnancy events → birth → post-birth milestones by age
""",
    "parameters": {
        "type": "object",
        "properties": {
            "description": {
                "type": "string",
                "description": "What happened"
            },
            "age_months": {
                "type": "number",
                "description": "Age in months when it happened. For post-birth milestones only. Leave empty for pregnancy/birth events."
            },
            "age_description": {
                "type": "string",
                "description": "Age in words if months unknown: 'בגיל שנה', 'בערך בגיל שנתיים'"
            },
            "domain": {
                "type": "string",
                "enum": ["motor", "language", "social", "cognitive", "regulation", "birth_history", "medical"],
                "description": "Developmental domain. Use 'birth_history' for pregnancy and birth events."
            },
            "milestone_type": {
                "type": "string",
                "enum": ["achievement", "concern", "regression", "intervention", "birth"],
                "description": "achievement=positive milestone, concern=worry, regression=lost skill, intervention=therapy started, birth=the actual birth moment"
            }
        },
        "required": ["description", "domain", "milestone_type"]
    }
}


TOOL_SET_CHILD_IDENTITY = {
    "name": "set_child_identity",
    "description": """Set or update basic identity information about the child.

CALL THIS when you learn the child's:
- Name (שם)
- Age (גיל) - in years, can be decimal like 3.5
- Gender (מין) - inferred from Hebrew pronouns (הוא=male, היא=female)

Examples:
- Parent says "יש לי בת בת 4, שמה מיקה" → name: "מיקה", age: 4, gender: "female"
- Parent says "הבן שלי בן 3.5" → age: 3.5, gender: "male"
- "קוראים לה נועה" → name: "נועה", gender: "female"

Only set fields that are explicitly mentioned. Don't guess.
This updates the child's permanent identity record.""",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Child's name. Only set if explicitly mentioned."
            },
            "age": {
                "type": "number",
                "description": "Child's age in years. Can be decimal (3.5 = three and a half)."
            },
            "gender": {
                "type": "string",
                "enum": ["male", "female"],
                "description": "Child's gender. Infer from Hebrew: הוא/בן=male, היא/בת=female"
            }
        },
        "required": []
    }
}


TOOL_SPAWN_EXPLORATION = {
    "name": "spawn_exploration",
    "description": """Start a focused exploration.

Use this when:
- A curiosity is ready for deeper investigation (strong pull, not yet explored)
- You want to systematically explore a hypothesis
- A pattern needs validation across domains

This creates an exploration that can:
- Gather evidence through conversation
- Potentially use video observation (if hypothesis is video_appropriate)
- Track progress toward understanding

One domain per exploration - don't mix domains in a single exploration.
""",
    "parameters": {
        "type": "object",
        "properties": {
            "focus": {
                "type": "string",
                "description": "What we're exploring"
            },
            "type": {
                "type": "string",
                "enum": ["discovery", "question", "hypothesis", "pattern"],
                "description": "Type of exploration"
            },
            "domain": {
                "type": "string",
                "description": "Primary domain for this exploration"
            },
            "theory": {
                "type": "string",
                "description": "For hypothesis: the theory to test"
            },
            "video_appropriate": {
                "type": "boolean",
                "description": "For hypothesis: can video observation test this?"
            },
            "question": {
                "type": "string",
                "description": "For question: the specific question"
            },
            "aspect": {
                "type": "string",
                "description": "For discovery: what aspect (essence, strengths, context)"
            },
            "observation": {
                "type": "string",
                "description": "For pattern: the pattern observed"
            }
        },
        "required": ["focus", "type"]
    }
}


# === Tool Collections ===

PERCEPTION_TOOLS = [
    TOOL_NOTICE,
    TOOL_WONDER,
    TOOL_CAPTURE_STORY,
    TOOL_ADD_EVIDENCE,
    TOOL_SPAWN_EXPLORATION,
    TOOL_RECORD_MILESTONE,
    TOOL_SET_CHILD_IDENTITY,
]


def get_perception_tools() -> List[Dict[str, Any]]:
    """Get tools for Phase 1 perception."""
    return PERCEPTION_TOOLS


def get_tool_by_name(name: str) -> Dict[str, Any]:
    """Get a specific tool definition by name."""
    for tool in PERCEPTION_TOOLS:
        if tool["name"] == name:
            return tool
    return None


# === Tool Schema Conversion for Gemini ===

def to_gemini_schema(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert tool definitions to Gemini-compatible format.

    Gemini requires function declarations in a specific format.
    """
    gemini_tools = []

    for tool in tools:
        gemini_tool = {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": tool["parameters"]
        }
        gemini_tools.append(gemini_tool)

    return gemini_tools


# === Validation ===

def validate_tool_call(name: str, args: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate a tool call has required parameters.

    Returns (is_valid, error_message).
    """
    tool = get_tool_by_name(name)
    if not tool:
        return False, f"Unknown tool: {name}"

    required = tool["parameters"].get("required", [])
    for param in required:
        if param not in args:
            return False, f"Missing required parameter: {param}"

    return True, ""
