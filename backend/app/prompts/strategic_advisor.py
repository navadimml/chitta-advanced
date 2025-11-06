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

    analysis_prompt = f"""You are analyzing an in-depth child development interview to determine what's been covered and what needs attention.

**Current extracted data:**

Child name: {extracted_data.get('child_name', 'unknown')}
Age: {extracted_data.get('age', 'unknown')}
Gender: {extracted_data.get('gender', 'unknown')}

Primary concerns: {extracted_data.get('primary_concerns', [])}
Concern details: {len(extracted_data.get('concern_details', '') or '')} characters
  Text: "{(extracted_data.get('concern_details', '') or '')[:200]}..."

Strengths: {len(extracted_data.get('strengths', '') or '')} characters
  Text: "{(extracted_data.get('strengths', '') or '')[:100]}..."

Developmental history: {len(extracted_data.get('developmental_history', '') or '')} characters
Family context: {len(extracted_data.get('family_context', '') or '')} characters
Daily routines: {len(extracted_data.get('daily_routines', '') or '')} characters
Parent goals: {len(extracted_data.get('parent_goals', '') or '')} characters

Overall completeness: {completeness_pct}%

**Your task:**

Analyze this data and provide brief, strategic guidance for the interviewer (Chitta).

Focus on:
1. What's been explored deeply with rich detail?
2. What's been mentioned but needs more depth (examples, situations, frequency)?
3. What hasn't been explored at all?
4. What should Chitta focus on next?

Provide your analysis in 2-4 bullet points. Be specific and actionable.
Make it guidance, not commands - Chitta will find natural moments.

Keep it VERY concise - this is strategic awareness, not a script.
"""

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
