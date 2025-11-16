"""
Fallback Extraction Mechanism for Failed Function Calls

When a model fails to call functions properly, we can use:
1. Structured output (JSON mode) to extract data
2. Post-processing extraction from conversation
3. Regex-based extraction for simple fields

This provides a safety net for less capable models.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from ..llm.base import BaseLLMProvider, Message

logger = logging.getLogger(__name__)


# === JSON Schema for Structured Extraction ===

EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "child_name": {
            "type": "string",
            "description": "Child's name if mentioned in the conversation"
        },
        "age": {
            "type": "number",
            "description": "Child's exact age in years (can be decimal)"
        },
        "gender": {
            "type": "string",
            "enum": ["male", "female", "unknown"],
            "description": "Child's gender"
        },
        "concerns": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of concerns mentioned (e.g., speech, social, attention)"
        },
        "concern_details": {
            "type": "string",
            "description": "Detailed description of concerns with examples"
        },
        "strengths": {
            "type": "string",
            "description": "Child's strengths and interests"
        },
        "other_notes": {
            "type": "string",
            "description": "Any other important information"
        },
        "has_new_information": {
            "type": "boolean",
            "description": "True if this turn contains new extractable information"
        }
    },
    "required": ["has_new_information"]
}


# === Structured Output Extraction ===

async def extract_with_structured_output(
    llm: BaseLLMProvider,
    conversation_history: List[Message],
    latest_user_message: str
) -> Optional[Dict[str, Any]]:
    """
    Use structured output (JSON mode) to extract data when function calling fails

    Args:
        llm: LLM provider instance
        conversation_history: Recent conversation context
        latest_user_message: The user's latest message

    Returns:
        Extracted data as dictionary, or None if extraction fails
    """
    extraction_prompt = f"""You are analyzing a conversation about a child's development.

Extract structured information from the latest user message.

Recent conversation context:
{_format_conversation_for_extraction(conversation_history[-3:] if len(conversation_history) > 3 else conversation_history)}

Latest user message:
"{latest_user_message}"

Extract any relevant information about:
- Child's name, age, gender
- Concerns or challenges mentioned
- Strengths or interests
- Family context, history, or other details

If no new information in latest message, set has_new_information to false."""

    try:
        messages = [
            Message(role="system", content="Extract structured child development data from conversation."),
            Message(role="user", content=extraction_prompt)
        ]

        result = await llm.chat_with_structured_output(
            messages=messages,
            response_schema=EXTRACTION_SCHEMA,
            temperature=0.3  # Lower temperature for extraction
        )

        if result.get("has_new_information", False):
            logger.info("✅ Fallback extraction successful via structured output")
            return result
        else:
            logger.debug("No new information to extract in this turn")
            return None

    except Exception as e:
        logger.error(f"Structured output extraction failed: {e}")
        return None


# === Regex-Based Extraction (Last Resort) ===

def extract_with_regex(text: str) -> Dict[str, Any]:
    """
    Basic regex-based extraction for common patterns (last resort)

    Args:
        text: User message text

    Returns:
        Dictionary with extracted fields
    """
    extracted = {}

    # Extract age patterns
    # "בן 3", "בת 4.5", "הוא בן 3 וחצי"
    age_patterns = [
        r'בן\s+(\d+(?:\.\d+)?)',
        r'בת\s+(\d+(?:\.\d+)?)',
        r'age\s+(\d+(?:\.\d+)?)',
        r'(\d+(?:\.\d+)?)\s+(?:years|שנים)',
        r'(\d+)\s+וחצי',  # X and a half
    ]

    for pattern in age_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            age_str = match.group(1)
            try:
                age = float(age_str)
                if 0 < age < 18:  # Sanity check
                    extracted['age'] = age
                    break
            except ValueError:
                pass

    # Handle "וחצי" (and a half)
    if 'age' not in extracted:
        half_match = re.search(r'(\d+)\s+וחצי', text)
        if half_match:
            try:
                extracted['age'] = float(half_match.group(1)) + 0.5
            except ValueError:
                pass

    # Extract gender from Hebrew grammar
    # הוא = male, היא = female
    if 'הוא' in text and 'היא' not in text:
        extracted['gender'] = 'male'
    elif 'היא' in text and 'הוא' not in text:
        extracted['gender'] = 'female'

    # Extract common concern keywords
    concern_keywords = {
        'דיבור': 'speech',
        'שפה': 'speech',
        'תקשורת': 'speech',
        'חברתי': 'social',
        'קשר עין': 'social',
        'קשב': 'attention',
        'ריכוז': 'attention',
        'היפראקטיבי': 'attention',
        'מוטורי': 'motor',
        'תנועה': 'motor',
        'חושי': 'sensory',
        'רגישות': 'sensory',
        'רגשי': 'emotional',
        'חרדה': 'emotional',
        'התנהגות': 'behavioral',
        'כעסים': 'behavioral',
    }

    concerns = []
    for keyword, category in concern_keywords.items():
        if keyword in text:
            if category not in concerns:
                concerns.append(category)

    if concerns:
        extracted['concerns'] = concerns

    return extracted if extracted else None


# === Hybrid Extraction Strategy ===

async def extract_with_fallback(
    llm: BaseLLMProvider,
    conversation_history: List[Message],
    latest_user_message: str,
    function_calls_received: List[Any]
) -> Optional[Dict[str, Any]]:
    """
    Hybrid extraction strategy:
    1. If function calls present and valid → use them
    2. Else try structured output extraction
    3. Else try regex-based extraction
    4. Return best available result

    Args:
        llm: LLM provider instance
        conversation_history: Recent conversation
        latest_user_message: Latest user message
        function_calls_received: Function calls from LLM (may be empty)

    Returns:
        Extracted data or None
    """
    # Strategy 1: Function calls already worked
    if function_calls_received:
        for fc in function_calls_received:
            if fc.name == "extract_interview_data":
                logger.debug("✅ Using function call extraction (primary method)")
                return fc.arguments
        return None

    logger.warning("⚠️  No function calls detected - using fallback extraction")

    # Strategy 2: Structured output (JSON mode)
    if llm.supports_structured_output():
        structured_result = await extract_with_structured_output(
            llm, conversation_history, latest_user_message
        )
        if structured_result:
            return structured_result

    # Strategy 3: Regex-based (last resort)
    logger.warning("⚠️  Structured output failed - trying regex extraction")
    regex_result = extract_with_regex(latest_user_message)
    if regex_result:
        logger.info(f"✅ Regex extraction found: {list(regex_result.keys())}")
        return regex_result

    logger.warning("❌ All extraction methods failed for this turn")
    return None


# === Helper Functions ===

def _format_conversation_for_extraction(messages: List[Message]) -> str:
    """Format conversation history for extraction prompt"""
    lines = []
    for msg in messages:
        role = msg.role.upper()
        lines.append(f"{role}: {msg.content}")
    return "\n".join(lines)


def merge_extracted_data(
    existing_data: Dict[str, Any],
    new_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Merge new extracted data with existing data (additive)

    Rules:
    - Scalars: new value overrides if not empty
    - Arrays: merge and deduplicate
    - Strings: append if different

    Args:
        existing_data: Current extracted data
        new_data: Newly extracted data

    Returns:
        Merged data dictionary
    """
    merged = existing_data.copy()

    for key, value in new_data.items():
        if value is None or value == "" or value == []:
            continue

        if key not in merged or not merged[key]:
            # New field or empty existing
            merged[key] = value

        elif isinstance(value, list):
            # Merge arrays and deduplicate
            existing_list = merged.get(key, [])
            if isinstance(existing_list, list):
                merged[key] = list(set(existing_list + value))
            else:
                merged[key] = value

        elif isinstance(value, str):
            # For strings, append if significantly different
            # Handle None properly - don't convert to string 'None'
            existing = merged.get(key)
            existing_str = str(existing) if existing is not None else ""
            if value.lower() not in existing_str.lower():
                merged[key] = f"{existing_str}. {value}".strip(". ")
            # else: keep existing (no change needed)

        else:
            # For numbers and other types, take new value
            merged[key] = value

    return merged
