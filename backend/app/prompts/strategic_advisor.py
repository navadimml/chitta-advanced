"""
Strategic Interview Advisor - LLM-based analysis of interview coverage

Uses LLM to intelligently analyze what's been covered and what needs attention.
Much smarter than pattern matching!
"""

import logging
from typing import Dict, Any, List, Optional
from ..services.llm.base import Message, BaseLLMProvider

logger = logging.getLogger(__name__)


async def get_strategic_guidance(
    llm_provider: BaseLLMProvider,
    extracted_data: Dict[str, Any],
    completeness: float
) -> str:
    """
    Use LLM to analyze interview coverage and provide strategic guidance

    This is NOT pattern matching - it's intelligent analysis!

    Args:
        llm_provider: The LLM to use for analysis
        extracted_data: Structured data extracted so far
        completeness: Current interview completeness (0.0-1.0)

    Returns:
        Strategic guidance text to inject into interview prompt
    """

    # Build analysis prompt
    completeness_pct = int(completeness * 100)

    # Build content previews - show ACTUAL content, not just lengths
    concern_details = (extracted_data.get('concern_details', '') or '')
    strengths = (extracted_data.get('strengths', '') or '')

    # Check for existing diagnoses in the data
    dev_history = (extracted_data.get('developmental_history', '') or '')
    has_diagnosis_mentioned = any(keyword in concern_details.lower() or keyword in dev_history.lower()
                                   for keyword in ['אובחן', 'אבחנה', 'diagnosed', 'diagnosis', 'autism', 'אוטיזם', 'adhd', 'דיסלקציה'])

    diagnosis_note = ""
    if has_diagnosis_mentioned:
        diagnosis_note = """
**⚠️ EXISTING DIAGNOSIS MENTIONED**:
- DON'T re-investigate areas already diagnosed
- Focus on: diagnosis context, current support, NEW concerns beyond diagnosis, strengths
- Parents are experts on diagnosed areas - respect that
"""

    # Check for missing critical info
    child_name = extracted_data.get('child_name', '')
    age = extracted_data.get('age', '')

    missing_critical_info = []
    if not child_name or child_name == 'unknown':
        missing_critical_info.append("⚠️ MISSING: Child's name - ask naturally: 'רק רוצה לוודא - מה שם הילד/ה?' (casual, like you forgot)")
    if not age or age == 'unknown':
        missing_critical_info.append("⚠️ MISSING: Child's age - ask naturally: 'ואיזה גיל?'")

    missing_info_section = ""
    if missing_critical_info:
        missing_info_section = f"""

**🚨 CRITICAL - MISSING BASIC INFO:**
{chr(10).join(missing_critical_info)}

Ask for this BEFORE exploring more areas! Be natural and casual."""

    # Check if ready to end (high completeness + substantial data)
    ready_to_end = (
        completeness >= 0.75 and
        len(concern_details) > 300 and
        len(strengths) > 100 and
        child_name and
        age
    )

    ending_section = ""
    if ready_to_end:
        ending_section = f"""

**✅ READY TO END:**
Interview is comprehensive ({completeness_pct}%). Time to wrap up!
Say: "תודה רבה! יש לי תמונה מקיפה של [name]. ההנחיות לצילום הווידאו יופיעו כאן למעלה."
DON'T ask more questions - interview is complete!"""

    analysis_prompt = f"""Analyze child development interview data to determine coverage.

**Current data:**
Child: {extracted_data.get('child_name', 'unknown')}, {extracted_data.get('age', '?')} years
Concerns: {extracted_data.get('primary_concerns', [])}

**Concern details ({len(concern_details)} chars):**
"{concern_details[:300] if concern_details else '[EMPTY]'}"

**Strengths ({len(strengths)} chars):**
"{strengths[:200] if strengths else '[EMPTY]'}"

Completeness: {completeness_pct}%
{diagnosis_note}{missing_info_section}{ending_section}

**Task:** Analyze which developmental areas are covered in the DATA (not what parent said).

Areas: motor, communication, social, emotional/behavioral, daily routines, family, history, goals

Write 2-4 concise bullets:
- ✅ COVERED WELL: [area] - substantial data
- ⚠️ NEEDS MORE: [area] - data exists but sparse
- ❌ NOT EXPLORED: [area] - no data
- 🏥 DIAGNOSED: [area] - diagnosis in data

**CRITICAL:**
- This is DATA ANALYSIS, not conversation attribution
- Never say "parent mentioned" - you're analyzing extracted fields
- Be accurate to prevent repetition"""

    messages = [Message(role="user", content=analysis_prompt)]

    try:
        response = await llm_provider.chat(
            messages=messages,
            temperature=0.3,  # Low temperature for consistent analysis
            max_tokens=200    # Keep it concise
        )

        guidance = response.content.strip()

        if not guidance:
            # Fallback to simple completion-based guidance
            if completeness < 0.20:
                guidance = "Just starting - build rapport and learn what brought parent here"
            elif completeness < 0.50:
                guidance = "Have initial information - explore concerns deeply with examples"
            elif completeness < 0.80:
                guidance = "Good depth on main topics - gather broader context (family, routines, goals)"
            else:
                guidance = "Comprehensive information gathered - wrap up and transition to video guidelines"

        logger.info(f"Strategic guidance ({completeness_pct}%): {guidance[:100]}...")
        return guidance

    except Exception as e:
        logger.error(f"Strategic advisor failed: {e}")
        # Fallback to simple guidance
        if completeness < 0.50:
            return "Continue exploring - follow parent's lead while ensuring depth"
        else:
            return "Good progress - ensure all developmental areas covered"


def build_strategic_awareness_section(guidance: str, completeness: float) -> str:
    """
    Format strategic guidance into prompt section

    Args:
        guidance: The strategic guidance from LLM analysis
        completeness: Current completeness percentage

    Returns:
        Formatted section for interview prompt
    """
    completeness_pct = int(completeness * 100)

    return f"""
## 📊 Strategic Awareness (Current: {completeness_pct}%)

**Coverage analysis:**
{guidance}

**Remember:** This is awareness, not a script. You lead the conversation proactively, finding natural moments to explore these areas. The conversation should flow organically while you ensure comprehensive coverage.

Don't mention percentages or "coverage" to the parent - this is your internal awareness only.
"""
