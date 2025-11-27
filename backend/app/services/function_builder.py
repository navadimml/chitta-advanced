"""
Function Builder - Builds LLM function definitions from config and i18n

🌟 Wu Wei: Structure from domain config, text from i18n
This service dynamically constructs the function definitions used
for intent detection, loading descriptions and examples from i18n.

The framework layer (this file) knows HOW to build functions.
The domain layer (extraction_schema.yaml) defines WHAT fields exist.
The language layer (i18n) provides the actual text.
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import yaml

from .i18n_service import get_i18n, t_section

logger = logging.getLogger(__name__)

# Path to domain config
DOMAIN_CONFIG_DIR = Path(__file__).parent.parent.parent / "config" / "domain"


class FunctionBuilder:
    """
    Builds LLM function definitions from config and i18n.

    Usage:
        builder = FunctionBuilder()
        functions = builder.get_conversation_functions()
    """

    def __init__(self, language: str = None):
        self.i18n = get_i18n(language)
        self._extraction_schema = None
        self._load_domain_config()

    def _load_domain_config(self):
        """Load domain configuration"""
        schema_path = DOMAIN_CONFIG_DIR / "extraction_schema.yaml"
        if schema_path.exists():
            with open(schema_path, "r", encoding="utf-8") as f:
                self._extraction_schema = yaml.safe_load(f)
            logger.info("Loaded extraction schema")
        else:
            logger.warning(f"Extraction schema not found: {schema_path}")
            self._extraction_schema = {}

    def get_conversation_functions(self, include_get_context: bool = False) -> List[Dict[str, Any]]:
        """
        Build all conversation function definitions.

        Args:
            include_get_context: If True, include get_context function for
                                 selective context querying (Phase 1 optimization)

        Returns list of function defs ready for LLM tool use.
        """
        functions = [
            self._build_extract_interview_data(),
            self._build_ask_developmental_question(),
            self._build_ask_about_analysis(),
            self._build_ask_about_app(),
            self._build_request_action()
        ]

        if include_get_context:
            functions.append(self._build_get_context())

        return functions

    def _build_extract_interview_data(self) -> Dict[str, Any]:
        """Build the extract_interview_data function from config + i18n"""

        # Get i18n content
        intent_config = t_section("intents.extract_interview_data")
        extraction_fields = t_section("extraction.fields")
        extraction_concerns = t_section("extraction.concerns")
        extraction_decisions = t_section("extraction.decisions")

        # Get schema for structure
        schema = self._extraction_schema or {}
        concern_categories = schema.get("concerns", {}).get("categories", [])
        decision_values = schema.get("decisions", {}).get("filming_preference", {}).get("values", [])

        # Build description from i18n
        description = intent_config.get("description", "Extract interview data")
        examples = intent_config.get("examples", "")
        full_description = f"{description}\n\nExamples:\n{examples}" if examples else description

        # Build properties from schema + i18n descriptions
        properties = {}

        # Basic fields
        if extraction_fields.get("child_name"):
            properties["child_name"] = {
                "type": "string",
                "description": extraction_fields["child_name"].get("description", "Child's name")
            }

        if extraction_fields.get("age"):
            properties["age"] = {
                "type": "number",
                "description": extraction_fields["age"].get("description", "Age in years")
            }

        if extraction_fields.get("gender"):
            properties["gender"] = {
                "type": "string",
                "enum": ["male", "female", "unknown"],
                "description": extraction_fields["gender"].get("description", "Gender")
            }

        # Concerns array
        if concern_categories and extraction_concerns:
            properties["primary_concerns"] = {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": concern_categories
                },
                "description": extraction_concerns.get("description", "Primary concerns")
            }

        # Text fields
        for field in ["concern_details", "strengths", "developmental_history",
                      "family_context", "daily_routines", "parent_goals"]:
            if extraction_fields.get(field):
                desc = extraction_fields[field].get("description", field)
                guidance = extraction_fields[field].get("guidance", "")
                full_desc = f"{desc}. {guidance}" if guidance else desc
                properties[field] = {
                    "type": "string",
                    "description": full_desc
                }

        # Urgent flags
        properties["urgent_flags"] = {
            "type": "array",
            "items": {"type": "string"},
            "description": t_section("extraction.safety").get("urgent_flags", {}).get(
                "description", "Safety concerns requiring immediate attention")
        }

        # Filming preference decision
        if decision_values and extraction_decisions.get("filming_preference"):
            fp_config = extraction_decisions["filming_preference"]
            fp_desc = fp_config.get("description", "Filming preference")
            positive = fp_config.get("positive_indicators", "")
            negative = fp_config.get("negative_indicators", "")
            guard = fp_config.get("guard", "")

            full_fp_desc = f"""{fp_desc}

Set to "wants_videos" if parent AGREES: {positive}

Set to "report_only" if parent DECLINES: {negative}

{guard}"""
            properties["filming_preference"] = {
                "type": "string",
                "enum": decision_values,
                "description": full_fp_desc
            }

        return {
            "name": "extract_interview_data",
            "description": full_description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": []
            }
        }

    def _build_ask_developmental_question(self) -> Dict[str, Any]:
        """Build ask_developmental_question function from i18n"""

        intent_config = t_section("intents.ask_developmental_question")
        topics = intent_config.get("topics", {})

        description = intent_config.get("description", "Developmental question")
        examples = intent_config.get("examples", "")
        full_description = f"{description}\n\nExamples:\n{examples}" if examples else description

        return {
            "name": "ask_developmental_question",
            "description": full_description,
            "parameters": {
                "type": "object",
                "properties": {
                    "question_topic": {
                        "type": "string",
                        "enum": list(topics.keys()) if topics else [
                            "developmental_milestone", "diagnosis_explanation",
                            "therapy_options", "behavior_understanding",
                            "parenting_strategy", "educational_approach",
                            "general_developmental"
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

    def _build_ask_about_analysis(self) -> Dict[str, Any]:
        """Build ask_about_analysis function from i18n"""

        intent_config = t_section("intents.ask_about_analysis")
        elements = intent_config.get("elements", {})

        description = intent_config.get("description", "Question about analysis")
        examples = intent_config.get("examples", "")
        full_description = f"{description}\n\nExamples:\n{examples}" if examples else description

        return {
            "name": "ask_about_analysis",
            "description": full_description,
            "parameters": {
                "type": "object",
                "properties": {
                    "analysis_element": {
                        "type": "string",
                        "enum": list(elements.keys()) if elements else [
                            "video_observation", "concern_identification",
                            "strength_identification", "recommendation",
                            "general_conclusion"
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

    def _build_ask_about_app(self) -> Dict[str, Any]:
        """Build ask_about_app function from i18n"""

        intent_config = t_section("intents.ask_about_app")
        topics = intent_config.get("topics", {})

        description = intent_config.get("description", "Question about app")
        examples = intent_config.get("examples", "")
        full_description = f"{description}\n\nExamples:\n{examples}" if examples else description

        return {
            "name": "ask_about_app",
            "description": full_description,
            "parameters": {
                "type": "object",
                "properties": {
                    "help_topic": {
                        "type": "string",
                        "enum": list(topics.keys()) if topics else [
                            "how_to_upload_video", "where_to_find_report",
                            "process_explanation", "next_steps",
                            "app_features", "technical_issue", "general_help"
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

    def _build_request_action(self) -> Dict[str, Any]:
        """Build request_action function from i18n"""

        intent_config = t_section("intents.request_action")
        actions = intent_config.get("actions", {})

        description = intent_config.get("description", "Action request")
        examples = intent_config.get("examples", "")
        full_description = f"{description}\n\nExamples:\n{examples}" if examples else description

        return {
            "name": "request_action",
            "description": full_description,
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": list(actions.keys()) if actions else [
                            "generate_guidelines", "view_guidelines",
                            "upload_video", "view_report",
                            "schedule_consultation", "find_experts", "share_report"
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

    def _build_get_context(self) -> Dict[str, Any]:
        """
        Build get_context function for selective context querying.

        🌟 Wu Wei: Instead of sending all context every turn, the LLM
        requests only the context keys it needs to answer the parent.

        Available context categories:
        - child.*: Child info (name, age, concerns, strengths)
        - artifacts.*: Artifact existence and status
        - ui.*: UI locations and guidance
        - ui_state.*: Current UI state (view, progress, interactions)
        - actions.*: Available/blocked actions
        - moment.*: Active moment context
        - session.*: Session state (returning user, completeness)
        """
        return {
            "name": "get_context",
            "description": """Query specific context needed to respond to the parent.

Call this function to get ONLY the context you need - don't request everything.

**Available context keys:**

child.*
  - child.name, child.age, child.gender
  - child.concerns, child.concerns_text
  - child.strengths, child.concern_details
  - child.filming_preference

artifacts.*
  - artifacts.{id}.exists, artifacts.{id}.status
  - artifacts.has_guidelines, artifacts.has_report

ui.*
  - ui.guidelines.location, ui.report.location
  - ui.{moment_id}.location (UI guidance from moments)

ui_state.* (current UI state - what user sees/does NOW)
  - ui_state.current_view, ui_state.previous_view
  - ui_state.videos_uploaded, ui_state.videos_required, ui_state.videos_remaining
  - ui_state.videos_analyzing, ui_state.video_analysis_progress
  - ui_state.report_generating, ui_state.report_generation_progress
  - ui_state.has_viewed_guidelines, ui_state.has_viewed_report
  - ui_state.recent_interactions (last 5 user actions)
  - ui_state.current_deep_view

actions.*
  - actions.available_list, actions.blocked_list
  - actions.{action_id}.available, actions.{action_id}.blocked_reason

session.*
  - session.is_returning_user, session.returning_user_summary
  - session.message_count, session.completeness, session.days_since_active

moment.*
  - moment.active, moment.active_context
  - moment.{id}.context

**Example queries:**

Location question → get_context(keys=["artifacts.has_guidelines", "ui.guidelines.location"])
Progress question → get_context(keys=["ui_state.videos_uploaded", "ui_state.videos_remaining"])
Available actions → get_context(keys=["actions.available_list"])
Returning user → get_context(keys=["session.is_returning_user", "session.returning_user_summary"])
""",
            "parameters": {
                "type": "object",
                "properties": {
                    "keys": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of context keys to query. Use category.* for all keys in a category."
                    }
                },
                "required": ["keys"]
            }
        }


# Singleton
_function_builder: Optional[FunctionBuilder] = None


def get_function_builder(language: str = None) -> FunctionBuilder:
    """Get function builder instance"""
    global _function_builder
    if _function_builder is None or (language and _function_builder.i18n.language != language):
        _function_builder = FunctionBuilder(language)
    return _function_builder


def get_conversation_functions(language: str = None, include_get_context: bool = False) -> List[Dict[str, Any]]:
    """
    Convenience function to get conversation functions.

    Args:
        language: Language code for i18n
        include_get_context: If True, include get_context function for Phase 1

    Returns:
        List of function definitions for LLM
    """
    return get_function_builder(language).get_conversation_functions(include_get_context=include_get_context)
