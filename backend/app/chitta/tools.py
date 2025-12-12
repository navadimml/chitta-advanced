"""
Chitta Tool Definitions - Simplified

5 tools for the Living Gestalt to learn and explore.

DESIGN PRINCIPLES:
- Minimum NECESSARY complexity
- Each tool has a clear, distinct purpose
- Gemini-compatible schemas (at least one required field)

Tools:
1. notice - Record observation about child
2. wonder - Spawn new curiosity (4 types)
3. capture_story - Capture meaningful story
4. add_evidence - Add evidence to active cycle
5. spawn_exploration - Start focused exploration
"""

from typing import List, Dict, Any


# === Tool Definitions ===

TOOL_NOTICE = {
    "name": "notice",
    "description": """Record an observation about the child.

Use this when you learn something about the child from the conversation.
This could be a fact, behavior, preference, or characteristic.

Examples:
- "He loves dinosaurs" → notice about interests
- "She has an older brother" → notice about family
- "Transitions are difficult" → notice about regulation
""",
    "parameters": {
        "type": "object",
        "properties": {
            "observation": {
                "type": "string",
                "description": "What was observed or learned about the child"
            },
            "domain": {
                "type": "string",
                "description": "Developmental domain: motor, social, emotional, cognitive, language, sensory, regulation, essence, strengths, context, concerns, general",
                "enum": ["motor", "social", "emotional", "cognitive", "language", "sensory", "regulation", "essence", "strengths", "context", "concerns", "general"]
            },
            "when": {
                "type": "string",
                "description": "When this was true (e.g., 'yesterday', 'usually', 'at age 2', 'now')"
            },
            "confidence": {
                "type": "number",
                "description": "How confident you are (0-1). Default 0.7"
            }
        },
        "required": ["observation"]
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

Example input: "Yesterday at the park, she saw another child crying and went over to pat his back"

Example output:
- summary: "At the park, comforted crying child by patting his back"
- reveals: ["empathy", "emotional recognition", "prosocial initiation", "comfort with unfamiliar children"]
- domains: ["social", "emotional"]
- significance: 0.8 (high - reveals core nature)

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
                "description": "What developmental signals this story reveals. Be thorough - one story can reveal many things."
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
    "description": """Add evidence to an active exploration cycle.

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
                "description": "ID of the active exploration cycle"
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


TOOL_SPAWN_EXPLORATION = {
    "name": "spawn_exploration",
    "description": """Start a focused exploration cycle.

Use this when:
- A curiosity is ready for deeper investigation (high activation, not yet explored)
- You want to systematically explore a hypothesis
- A pattern needs validation across domains

This creates an exploration cycle that can:
- Gather evidence through conversation
- Potentially use video observation (if hypothesis is video_appropriate)
- Track progress toward understanding

One domain per cycle - don't mix domains in a single exploration.
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

EXTRACTION_TOOLS = [
    TOOL_NOTICE,
    TOOL_WONDER,
    TOOL_CAPTURE_STORY,
    TOOL_ADD_EVIDENCE,
    TOOL_SPAWN_EXPLORATION,
]


def get_extraction_tools() -> List[Dict[str, Any]]:
    """Get tools for Phase 1 extraction."""
    return EXTRACTION_TOOLS


def get_tool_by_name(name: str) -> Dict[str, Any]:
    """Get a specific tool definition by name."""
    for tool in EXTRACTION_TOOLS:
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
