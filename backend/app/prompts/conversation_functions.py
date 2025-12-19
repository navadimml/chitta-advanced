"""
Comprehensive Conversation Function Definitions - Simplified Architecture

🌟 Wu Wei: Function definitions are now built dynamically from config + i18n.
Use get_conversation_functions() from function_builder for dynamic definitions.

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

# Import the dynamic function builder
from app.services.function_builder import get_conversation_functions as _get_dynamic_functions


def get_conversation_functions(language: str = None) -> List[Dict[str, Any]]:
    """
    Get conversation function definitions dynamically from config + i18n.

    Wu Wei: Structure from domain config, text from i18n.

    Args:
        language: Language code (e.g., "he", "en"). Defaults to system default.

    Returns:
        List of function definitions for LLM tool use.
    """
    return _get_dynamic_functions(language)


# Legacy export for backwards compatibility
# These are static definitions - prefer using get_conversation_functions() instead
CONVERSATION_FUNCTIONS_COMPREHENSIVE: List[Dict[str, Any]] = get_conversation_functions()


def get_function_by_name(name: str, language: str = None) -> Dict[str, Any]:
    """Get function definition by name"""
    functions = get_conversation_functions(language)
    for func in functions:
        if func["name"] == name:
            return func
    raise ValueError(f"Function {name} not found")


def get_function_names(language: str = None) -> List[str]:
    """Get list of all function names"""
    return [func["name"] for func in get_conversation_functions(language)]
