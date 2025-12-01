"""
Chitta Tools - Function definitions for the AI

These tools define WHAT Chitta can do. The AI decides WHEN to use them
based on the conversation and the Living Gestalt principles.

Design principles:
1. Tools are PURPOSE-DRIVEN, not threshold-based
2. Descriptions guide when to use (no arbitrary completeness scores)
3. Descriptions are in English - the LLM understands English best
4. Domain-specific text (Hebrew responses) comes from i18n at execution time

Tool categories aligned with Living Gestalt:
1. Understanding tools - Build the Gestalt (essence, strengths, history, family, concerns)
2. Story tools - Capture meaningful moments
3. Living Edge tools - Track patterns, hypotheses, questions
4. Exploration tools - Hypothesis-driven video cycles
5. Synthesis tools - Point-in-time understanding snapshots
6. Query tools - Handle parent questions

IMPORTANT PARADIGM SHIFT (November 2024):
- OLD: Threshold-based → "completeness >= 0.4 → generate guidelines"
- NEW: Purpose-driven → "hypothesis needs observation → start exploration"
- OLD: State-based → "has_video_guidelines: bool"
- NEW: Activity-based → "exploration_cycle: {purpose, scenarios, status}"
"""

from typing import List, Dict, Any
from .gestalt import Gestalt


def get_chitta_tools(gestalt: Gestalt = None) -> List[Dict[str, Any]]:
    """
    Get the tool definitions for Chitta.

    Args:
        gestalt: Optional Gestalt to customize tool availability/descriptions

    Returns:
        List of function definitions for LLM tool use
    """
    tools = [
        # === Understanding Tools (Building the Gestalt) ===
        _tool_update_understanding(),
        _tool_capture_story(),

        # === Living Edge Tools ===
        _tool_note_pattern(),
        _tool_form_hypothesis(),

        # === Exploration Tools (Video - Activity-Based) ===
        _tool_start_exploration(),
        _tool_add_scenario(),
        _tool_analyze_video(),
        _tool_complete_exploration(),

        # === Synthesis Tools ===
        _tool_generate_synthesis(),

        # === Query Tools ===
        _tool_ask_about_child(),
        _tool_ask_about_app(),
    ]

    return tools


# === Understanding Tools ===

def _tool_update_understanding() -> Dict[str, Any]:
    """
    Extract and update developmental data from conversation.

    This is the PRIMARY tool for building the Living Gestalt.
    """
    return {
        "name": "update_child_understanding",
        "description": """Extract information from the parent's message and update the Living Gestalt.

This is the PRIMARY tool for building understanding. Use it LIBERALLY.

ALWAYS call when parent shares:

IDENTITY (essentials first):
- Child's name, age, gender

ESSENCE (who they are):
- Temperament observations ("slow to warm", "intense", "cautious")
- Energy patterns ("high energy but focuses on interests")
- Core qualities ("curious", "loving", "determined")

STRENGTHS (before concerns!):
- Abilities and what they're good at
- Interests and passions
- What lights them up
- What surprises people about them

HISTORY (critical for interpretation):
- Birth/pregnancy information (especially complications, prematurity)
- Developmental milestones
- Previous evaluations or diagnoses
- Past/current interventions

FAMILY:
- Family structure (who at home, siblings)
- Languages spoken at home
- Family developmental history ("dad was late talker")
- Sibling dynamics ("sister speaks for him")

CONCERNS (in context of above):
- Developmental concern areas
- Specific details and examples

OTHER:
- Daily routines
- Parent goals and hopes
- Parent emotional state

Extract ONLY what was actually said - never infer or assume.
""",
        "parameters": {
            "type": "object",
            "properties": {
                # === Identity ===
                "child_name": {
                    "type": "string",
                    "description": "Child's name if mentioned"
                },
                "age": {
                    "type": "number",
                    "description": "Age in years (can be decimal, e.g., 2.5)"
                },
                "gender": {
                    "type": "string",
                    "enum": ["male", "female", "unknown"],
                    "description": "Gender if clearly indicated"
                },

                # === Essence ===
                "temperament_observations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Temperament notes: 'slow to warm', 'intense', 'cautious with new people'"
                },
                "energy_pattern": {
                    "type": "string",
                    "description": "Energy/pace description: 'high energy but can focus deeply'"
                },
                "core_qualities": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Core qualities: 'curious', 'loving', 'determined', 'sensitive'"
                },

                # === Strengths ===
                "abilities": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "What they're good at: 'great memory', 'problem solver', 'creative'"
                },
                "interests": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "What they love: 'dinosaurs', 'music', 'cars', 'water play'"
                },
                "what_lights_them_up": {
                    "type": "string",
                    "description": "Narrative about what makes them come alive"
                },
                "surprises_people": {
                    "type": "string",
                    "description": "What surprises people about them"
                },

                # === History ===
                "birth_complications": {
                    "type": "string",
                    "description": "Birth/pregnancy complications if mentioned"
                },
                "was_premature": {
                    "type": "boolean",
                    "description": "Was the child born premature?"
                },
                "weeks_gestation": {
                    "type": "integer",
                    "description": "Weeks of gestation if premature"
                },
                "milestone_notes": {
                    "type": "string",
                    "description": "Milestone info: 'walked at 14 months, first words at 18 months'"
                },
                "previous_diagnoses": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Any previous diagnoses mentioned"
                },
                "previous_evaluations": {
                    "type": "string",
                    "description": "Previous evaluations: who, when, findings"
                },
                "interventions": {
                    "type": "string",
                    "description": "Current/past therapy or interventions"
                },

                # === Family ===
                "family_structure": {
                    "type": "string",
                    "description": "Family structure: 'two parents, older sister'"
                },
                "siblings": {
                    "type": "string",
                    "description": "Sibling info including any dynamics: 'sister speaks for him'"
                },
                "languages_at_home": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Languages spoken at home"
                },
                "family_developmental_history": {
                    "type": "string",
                    "description": "Family history: 'dad was late talker', 'uncle has ADHD'"
                },

                # === Concerns ===
                "primary_concerns": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["speech", "social", "attention", "motor", "sensory",
                                 "emotional", "behavioral", "learning", "sleep", "eating", "other"]
                    },
                    "description": "Developmental concern areas mentioned"
                },
                "concern_details": {
                    "type": "string",
                    "description": "Specific details about concerns - use parent's own words"
                },
                "concern_context": {
                    "type": "string",
                    "description": "When concerns started, what triggers them"
                },

                # === Other ===
                "daily_routines": {
                    "type": "string",
                    "description": "Typical daily routines and behaviors"
                },
                "parent_goals": {
                    "type": "string",
                    "description": "What the parent hopes to achieve or understand"
                },
                "parent_emotional_state": {
                    "type": "string",
                    "description": "How parent seems to be coping"
                },
                "urgent_flags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Safety concerns: self-harm, harm to others, neglect indicators"
                },
                "filming_preference": {
                    "type": "string",
                    "enum": ["wants_videos", "report_only"],
                    "description": "ONLY set when parent explicitly agrees/declines video observation"
                }
            },
            "required": []
        }
    }


def _tool_capture_story() -> Dict[str, Any]:
    """
    Capture a meaningful story or observation from the parent.

    Stories are gold - they reveal patterns that summaries hide.
    """
    return {
        "name": "capture_story",
        "description": """Capture a story or observation the parent shared about their child.

Stories are the RICHEST source of understanding. They reveal:
- Patterns that summaries hide
- Context that labels miss
- The child as they really are

Use this when parent shares:
- A specific moment or incident
- A recurring situation
- Something that surprised them
- A breakthrough or regression

Examples worth capturing:
- "Yesterday at the park, she saw another child crying and went to pat his back"
- "He gets so frustrated when blocks fall - throws them and cries"
- "She can spend hours with dinosaurs, making up elaborate scenarios"
- "My mom started humming and he actually looked at her - really looked"

Capture in the parent's own words. Note what it reveals.
""",
        "parameters": {
            "type": "object",
            "properties": {
                "story_content": {
                    "type": "string",
                    "description": "The story in the parent's own words"
                },
                "themes": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["speech", "social", "attention", "motor", "sensory",
                                 "emotional", "behavioral", "learning", "play",
                                 "interaction", "strengths", "connection"]
                    },
                    "description": "Developmental themes this story touches"
                },
                "sentiment": {
                    "type": "string",
                    "enum": ["positive", "concern", "neutral", "mixed", "breakthrough"],
                    "description": "The emotional tone of the story"
                },
                "what_it_reveals": {
                    "type": "string",
                    "description": "What this story tells us about the child"
                },
                "context": {
                    "type": "string",
                    "description": "What prompted this story (question asked, topic)"
                }
            },
            "required": ["story_content"]
        }
    }


# === Living Edge Tools ===

def _tool_note_pattern() -> Dict[str, Any]:
    """
    Note a pattern emerging across observations.

    Patterns connect scattered observations into themes.
    """
    return {
        "name": "note_pattern",
        "description": """Note when you detect a pattern emerging across observations.

Patterns are themes that appear repeatedly in different contexts:
- "Mornings are hard" + "car seat battles" + "bedtime struggles" = "Transitions are difficult"
- "Watches before joining" + "hides with new people" + "slow to warm at daycare" = "Approach caution"

Use this when:
- Same theme appears in 2+ different contexts
- Parent mentions something that connects to earlier observation
- You notice a thread running through multiple stories

This helps track understanding and can drive future exploration.
""",
        "parameters": {
            "type": "object",
            "properties": {
                "theme": {
                    "type": "string",
                    "description": "The pattern theme: 'transitions are difficult', 'approach caution'"
                },
                "observations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "The observations that connect: ['mornings hard', 'car seat battles']"
                },
                "domains_involved": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Developmental domains involved: ['emotional', 'sensory']"
                },
                "confidence": {
                    "type": "number",
                    "description": "How confident in this pattern (0.0-1.0)"
                }
            },
            "required": ["theme", "observations"]
        }
    }


def _tool_form_hypothesis() -> Dict[str, Any]:
    """
    Form a working hypothesis about the child.

    Hypotheses are theories held lightly, driving curiosity.
    """
    return {
        "name": "form_hypothesis",
        "description": """Form a working hypothesis about the child.

Hypotheses are NOT diagnoses. They are working theories that:
- Explain patterns we're seeing
- Guide what questions to ask
- Drive video observation requests
- Are held LIGHTLY and revised with new information

Good hypotheses:
- "Speech delay might be primarily temperament-related - capacity is there, safety is the key"
- "The transition difficulty could be sensory-based - each transition involves sensory shift"
- "Slow-to-warm is temperament, not social deficit - he CAN connect, just needs time"

Bad (too diagnostic):
- "Has autism"
- "ADHD confirmed"

Use when:
- Patterns suggest an explanation
- You want to explore a theory
- You're guiding video observation

Always indicate evidence for AND against.
""",
        "parameters": {
            "type": "object",
            "properties": {
                "theory": {
                    "type": "string",
                    "description": "The hypothesis - descriptive, not diagnostic"
                },
                "supporting_evidence": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "What supports this hypothesis"
                },
                "contradicting_evidence": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "What contradicts or complicates this hypothesis"
                },
                "arose_from": {
                    "type": "string",
                    "description": "What triggered this hypothesis"
                },
                "questions_to_explore": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Questions that would test this hypothesis"
                }
            },
            "required": ["theory"]
        }
    }


# === Exploration Tools (Activity-Based) ===

def _tool_start_exploration() -> Dict[str, Any]:
    """
    Start a video exploration cycle - hypothesis-driven, not threshold-based.

    This replaces the old generate_video_guidelines tool.
    """
    return {
        "name": "start_video_exploration",
        "description": """Start a video exploration cycle to test hypotheses or answer questions.

WHEN TO USE:
- When conversation alone can't answer what we're wondering
- When hypotheses need visual observation to test
- When we've hit the limits of what words can convey
- When the parent seems ready and interested in filming

WHEN NOT TO USE:
- Parent chose report_only
- Still in early rapport-building (know the child first)
- No clear purpose for observation (never "just to see")

HOW IT WORKS:
1. This tool starts an exploration CYCLE
2. The cycle has a PURPOSE (hypotheses or questions driving it)
3. We request specific SCENARIOS to observe
4. Parent films and uploads
5. We analyze and learn
6. Cycle completes when we've learned what we needed

Example:
- Hypothesis: "His slow-to-warm is temperament, not social deficit"
- Scenarios: "playing alone (comfort)", "new adult enters room (response)"
- Analysis: Look for capacity vs. caution patterns

The guidelines artifact is created to help the parent know what to film.
But the artifact is just a TOOL for the exploration, not the goal.
""",
        "parameters": {
            "type": "object",
            "properties": {
                "exploration_purpose": {
                    "type": "string",
                    "description": "What question or hypothesis drives this exploration?"
                },
                "hypotheses_to_test": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific hypotheses to test through observation"
                },
                "what_conversation_cant_answer": {
                    "type": "string",
                    "description": "What do we need to SEE that we can't learn from talking?"
                },
                "scenarios": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "scenario": {
                                "type": "string",
                                "description": "What to film: 'playing alone', 'with sibling'"
                            },
                            "why_we_want_to_see": {
                                "type": "string",
                                "description": "What this scenario reveals"
                            },
                            "focus_points": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Specific things to watch for"
                            },
                            "duration": {
                                "type": "string",
                                "enum": ["short", "medium", "long"],
                                "description": "How long to film"
                            }
                        },
                        "required": ["scenario", "why_we_want_to_see"]
                    },
                    "description": "Specific scenarios to capture"
                }
            },
            "required": ["exploration_purpose", "scenarios"]
        }
    }


def _tool_add_scenario() -> Dict[str, Any]:
    """
    Add a scenario to an active exploration cycle.
    """
    return {
        "name": "add_exploration_scenario",
        "description": """Add another video scenario to the active exploration.

Use when:
- New hypothesis emerges during conversation
- Parent mentions something that would be good to observe
- We realize we need another angle on what we're exploring

Only works when an exploration cycle is active.
""",
        "parameters": {
            "type": "object",
            "properties": {
                "scenario": {
                    "type": "string",
                    "description": "What to film"
                },
                "why_we_want_to_see": {
                    "type": "string",
                    "description": "What this scenario reveals"
                },
                "connects_to_hypothesis": {
                    "type": "string",
                    "description": "Which hypothesis this helps test"
                },
                "focus_points": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific things to watch for"
                }
            },
            "required": ["scenario", "why_we_want_to_see"]
        }
    }


def _tool_analyze_video() -> Dict[str, Any]:
    """
    Trigger analysis of an uploaded video.
    """
    return {
        "name": "analyze_video",
        "description": """Analyze an uploaded video within the current exploration cycle.

The analysis uses:
- The Living Gestalt context (who this child is)
- The exploration purpose (what we're looking for)
- Active hypotheses (what we're testing)
- Clinical observation frameworks (DSM-5, DIR/Floortime)

Analysis produces:
- Observations across developmental domains
- Evidence FOR or AGAINST active hypotheses
- New patterns noticed
- New questions that arise
- What we learned vs. what we still wonder

The analysis feeds back into the Gestalt and informs the exploration.
""",
        "parameters": {
            "type": "object",
            "properties": {
                "video_id": {
                    "type": "string",
                    "description": "ID of video to analyze"
                },
                "primary_focus": {
                    "type": "string",
                    "description": "Main thing to look for (ties to exploration purpose)"
                },
                "hypotheses_to_test": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific hypotheses to evaluate"
                }
            },
            "required": []
        }
    }


def _tool_complete_exploration() -> Dict[str, Any]:
    """
    Complete the current exploration cycle with learnings.
    """
    return {
        "name": "complete_exploration_cycle",
        "description": """Complete the current video exploration cycle.

Use when:
- We've learned what we set out to learn
- Hypotheses have been confirmed/revised/rejected
- Parent wants to pause video observation
- Ready to move on to synthesis or new direction

This captures what we learned for the Gestalt.
""",
        "parameters": {
            "type": "object",
            "properties": {
                "what_we_learned": {
                    "type": "string",
                    "description": "Summary of insights from this exploration"
                },
                "hypotheses_supported": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Hypotheses that were supported"
                },
                "hypotheses_contradicted": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Hypotheses that were contradicted"
                },
                "new_hypotheses": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "New hypotheses that emerged"
                },
                "remaining_questions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Questions still unanswered"
                }
            },
            "required": ["what_we_learned"]
        }
    }


# === Synthesis Tools ===

def _tool_generate_synthesis() -> Dict[str, Any]:
    """
    Generate a synthesis (parent report) of current understanding.

    Replaces the old threshold-based generate_parent_report.
    """
    return {
        "name": "generate_synthesis",
        "description": """Generate a synthesis of our current understanding.

WHEN TO USE:
- Parent wants to share understanding with partner, family, professional
- A significant exploration cycle has completed
- Parent explicitly requests a summary or report
- Enough has changed that a new snapshot would be valuable

WHEN NOT TO USE:
- Just to "have a report" (must serve a purpose)
- In early conversation before we know the child
- Without strengths and essence (these come FIRST)

The synthesis captures the Living Gestalt at this moment in time:
- WHO this child is (essence, temperament)
- STRENGTHS and interests (always first)
- History and context
- Concerns in context
- Patterns we've noticed
- Hypotheses we're exploring
- What we're still wondering

Previous syntheses become HISTORICAL - we track changes over time.
This supports the long-term relationship (months/years).
""",
        "parameters": {
            "type": "object",
            "properties": {
                "purpose": {
                    "type": "string",
                    "description": "Why generate this synthesis? Who is it for?"
                },
                "include_recommendations": {
                    "type": "boolean",
                    "description": "Include next-step suggestions"
                },
                "include_hypotheses": {
                    "type": "boolean",
                    "description": "Include working hypotheses (appropriately framed)"
                },
                "emphasis": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Areas to emphasize based on purpose"
                },
                "for_professional": {
                    "type": "boolean",
                    "description": "Is this for a professional? (adjusts detail level)"
                }
            },
            "required": ["purpose"]
        }
    }


# === Query Tools ===

def _tool_ask_about_child() -> Dict[str, Any]:
    """
    Parent asks a developmental question about their child.
    """
    return {
        "name": "ask_developmental_question",
        "description": """Handle when parent asks a developmental question.

Use when parent asks about:
- Developmental milestones ("is this normal for his age?")
- Diagnoses or conditions ("what is ADHD?")
- Therapy options ("what kind of therapy might help?")
- Behavior understanding ("why does she do this?")
- Parenting strategies ("how should I handle tantrums?")

Your response should be:
- Grounded in this child's specific context
- Educational, not diagnostic
- Empowering, not alarming
- Honest about uncertainty
""",
        "parameters": {
            "type": "object",
            "properties": {
                "question_topic": {
                    "type": "string",
                    "enum": [
                        "developmental_milestone",
                        "diagnosis_explanation",
                        "therapy_options",
                        "behavior_understanding",
                        "parenting_strategy",
                        "educational_approach",
                        "general_developmental"
                    ],
                    "description": "The category of question"
                },
                "question_text": {
                    "type": "string",
                    "description": "The actual question"
                },
                "relates_to_child": {
                    "type": "boolean",
                    "description": "Is this about their specific child vs. general?"
                }
            },
            "required": ["question_topic", "question_text"]
        }
    }


def _tool_ask_about_app() -> Dict[str, Any]:
    """
    Parent asks about the app or process.
    """
    return {
        "name": "ask_about_app",
        "description": """Handle when parent asks about the app or process.

Use for questions like:
- "How do I upload a video?"
- "Where is the report?"
- "What happens next?"
- "How does this work?"

Guide them clearly and warmly.
""",
        "parameters": {
            "type": "object",
            "properties": {
                "help_topic": {
                    "type": "string",
                    "enum": [
                        "how_to_upload_video",
                        "where_to_find_report",
                        "where_to_find_guidelines",
                        "process_explanation",
                        "next_steps",
                        "app_features",
                        "technical_issue",
                        "general_help"
                    ],
                    "description": "What they need help with"
                },
                "question_text": {
                    "type": "string",
                    "description": "Their actual question"
                }
            },
            "required": ["help_topic", "question_text"]
        }
    }


# === Export ===

CHITTA_TOOLS = get_chitta_tools()
