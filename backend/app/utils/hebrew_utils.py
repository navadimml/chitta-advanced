"""
Hebrew Text Processing Utilities

Helper functions for processing Hebrew text,
including name extraction for better interview data quality
"""

import re
from typing import Optional, List


def extract_hebrew_names_from_text(text: str) -> List[str]:
    """
    Extract potential Hebrew names from text using pattern matching

    Hebrew names typically:
    - Start with a capital letter (in transliterated or mixed text)
    - Are 2-6 characters long
    - May contain Hebrew characters only
    - Often appear after common question patterns

    Examples:
    - "מתי והוא בן 9" → ["מתי"]
    - "השם שלו דני" → ["דני"]
    - "הילדה שלי נועה" → ["נועה"]
    """
    names = []

    # Pattern 1: Name after "שם" (name)
    # "השם שלו X", "מה שם הילד? X", etc.
    name_after_shem = re.findall(r'שם\s+(?:שלו|שלה|הילד|הילדה)?\s*([א-ת]{2,8})', text)
    names.extend(name_after_shem)

    # Pattern 2: Name after "קוראים" (called)
    # "קוראים לו X", "איך קוראים לה? X"
    name_after_korim = re.findall(r'קוראים\s+(?:לו|לה|ל)?\s*([א-ת]{2,8})', text)
    names.extend(name_after_korim)

    # Pattern 3: Hebrew word at start (if short message with age)
    # "מתי והוא בן 9" → "מתי"
    if 'בן' in text or 'בת' in text:
        first_words = re.findall(r'^([א-ת]{2,8})\s', text)
        if first_words:
            names.extend(first_words)

    # Pattern 4: Hebrew name in format "X והוא/והיא"
    # "דני והוא בן 5"
    name_before_vehu = re.findall(r'([א-ת]{2,8})\s+וה(?:וא|יא)', text)
    names.extend(name_before_vehu)

    # Deduplicate while preserving order
    seen = set()
    unique_names = []
    for name in names:
        if name not in seen and len(name) >= 2:
            seen.add(name)
            unique_names.append(name)

    return unique_names


def smart_extract_child_name(
    parent_message: str,
    llm_extracted_name: Optional[str]
) -> Optional[str]:
    """
    Intelligently extract child's name using both LLM and pattern matching

    If LLM found a name, trust it.
    If LLM returned "unknown", try pattern matching.

    Args:
        parent_message: The parent's message text
        llm_extracted_name: Name extracted by LLM (or "unknown")

    Returns:
        Best guess at child's name, or None if truly unknown
    """
    # If LLM found a name, trust it
    if llm_extracted_name and llm_extracted_name != "unknown":
        return llm_extracted_name

    # LLM didn't find it - try pattern matching
    potential_names = extract_hebrew_names_from_text(parent_message)

    if potential_names:
        # Return the first (most likely) name
        return potential_names[0]

    # Truly couldn't find a name
    return None


# Common Hebrew names for validation (optional - could help filter false positives)
COMMON_HEBREW_NAMES = {
    # Boys
    "יוסי", "דני", "רועי", "נועם", "אורי", "אבי", "יוני", "עידו", "גיא", "תומר",
    "איתי", "אלון", "יובל", "עמית", "רון", "עומר", "ליאור", "מתי", "ניר", "טל",

    # Girls
    "נועה", "מיכל", "תמר", "שירה", "יעל", "מיה", "עדן", "אורי", "רונית", "דנה",
    "ליה", "אלה", "עדי", "רוני", "תהל", "נטע", "ענבל", "רותם", "ליאת", "מעיין",

    # Unisex
    "עדי", "ליאור", "טל", "נועם", "ניר", "שי", "ים", "חן", "גל"
}


def is_likely_hebrew_name(text: str) -> bool:
    """
    Check if text is likely a Hebrew name

    Criteria:
    - 2-8 Hebrew characters
    - In common names list OR passes heuristic checks
    """
    if not text or len(text) < 2 or len(text) > 8:
        return False

    # Check if all Hebrew letters
    if not re.match(r'^[א-ת]+$', text):
        return False

    # Check against known names
    if text in COMMON_HEBREW_NAMES:
        return True

    # Heuristic: if 2-6 chars and all Hebrew, probably a name
    if 2 <= len(text) <= 6:
        return True

    return False
