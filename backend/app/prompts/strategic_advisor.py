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

    analysis_prompt = f"""You are analyzing a child development interview to determine what's been covered and what needs attention.

**CRITICAL**: Don't just look at what fields are empty. READ THE ACTUAL CONTENT to understand what developmental areas have been discussed!

**Current extracted data:**

Child name: {extracted_data.get('child_name', 'unknown')}
Age: {extracted_data.get('age', 'unknown')}
Gender: {extracted_data.get('gender', 'unknown')}

Primary concerns: {extracted_data.get('primary_concerns', [])}

**Concern details ({len(concern_details)} chars):**
"{concern_details[:400] if concern_details else '[EMPTY - nothing discussed yet]'}"

**Strengths ({len(strengths)} chars):**
"{strengths[:300] if strengths else '[EMPTY - no strengths mentioned]'}"

Overall completeness: {completeness_pct}%

**Your task:**

Analyze what developmental areas have ACTUALLY been discussed (read the content above carefully!):
- Motor skills (writing, drawing, running, coordination)
- Communication (speech, understanding, expressing)
- Social (friends, playing with others)
- Emotional/behavioral (tantrums, regulation, transitions)
- Daily routines and context
- Family background
- Developmental history (milestones)
- Parent's goals and hopes

**Provide guidance in 2-4 bullet points:**
1. What developmental areas have been covered with good depth? (Look in the actual text!)
2. What's been mentioned briefly but needs concrete examples?
3. What developmental areas haven't been touched at all?
4. CRITICAL: If an area has been discussed extensively (50+ chars of detail), DON'T ask about it again!

**Anti-repetition rule**: If we have rich detail on a topic, mark it as DONE and move to unexplored areas.

Be VERY concise. This is strategic awareness, not a script."""

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
