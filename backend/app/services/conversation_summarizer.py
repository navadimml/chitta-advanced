"""
Conversation Summarizer - Compresses long conversation histories

🌟 Wu Wei: Creates concise summaries for context compression
- Prevents token overflow in long conversations
- Maintains essential information for continuity
- Supports intermittent users returning after gaps

This service:
1. Summarizes conversation history when it exceeds threshold
2. Extracts key topics and decisions made
3. Tracks conversation milestones
4. Provides compressed context for LLM prompts

🌟 Uses i18n for user-facing text, English for LLM prompts
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from app.services.llm.factory import create_llm_provider
from app.services.llm.base import Message
from app.services.i18n_service import t, t_section

logger = logging.getLogger(__name__)

# Thresholds for summarization
SUMMARY_THRESHOLD_MESSAGES = 20  # Summarize after this many messages
SUMMARY_KEEP_RECENT = 6  # Keep this many recent messages in full
MAX_SUMMARY_LENGTH = 500  # Max characters for summary


class ConversationSummarizer:
    """
    Summarizes long conversations for context compression
    """

    def __init__(self, llm_provider=None):
        """Initialize with optional LLM provider"""
        if llm_provider is None:
            import os
            provider_type = os.getenv("LLM_PROVIDER", "gemini")
            model = os.getenv("FAST_LLM_MODEL", "gemini-2.0-flash-exp")
            self.llm = create_llm_provider(
                provider_type=provider_type,
                model=model,
                use_enhanced=False
            )
            logger.info(f"ConversationSummarizer initialized with {model}")
        else:
            self.llm = llm_provider

    def should_summarize(self, conversation_history: List[Dict]) -> bool:
        """
        Check if conversation needs summarization

        Args:
            conversation_history: List of message dicts

        Returns:
            True if summarization is recommended
        """
        return len(conversation_history) > SUMMARY_THRESHOLD_MESSAGES

    async def summarize_conversation(
        self,
        conversation_history: List[Dict],
        extracted_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a summary of the conversation

        Args:
            conversation_history: Full conversation history
            extracted_data: Current extracted data about the child

        Returns:
            Dict with summary and metadata
        """
        if not conversation_history:
            return {
                "summary": "",
                "key_topics": [],
                "decisions_made": [],
                "message_count": 0
            }

        # Build prompt for summarization
        prompt = self._build_summarization_prompt(conversation_history, extracted_data)

        try:
            response = await self.llm.chat(
                messages=[Message(role="user", content=prompt)],
                temperature=0.3,
                max_tokens=1000,
                response_format="json"
            )

            result = json.loads(response.content)
            logger.info(f"📝 Conversation summarized: {len(result.get('summary', ''))} chars")
            return result

        except Exception as e:
            logger.error(f"Error summarizing conversation: {e}")
            # Fallback to simple summary
            return self._create_fallback_summary(conversation_history, extracted_data)

    def _build_summarization_prompt(
        self,
        conversation_history: List[Dict],
        extracted_data: Dict[str, Any]
    ) -> str:
        """Build the prompt for conversation summarization (English for LLM)"""

        # Format conversation for the prompt
        conversation_text = self._format_conversation(conversation_history)

        # Get values with fallbacks
        child_name = extracted_data.get('child_name', 'not specified')
        age = extracted_data.get('age', 'not specified')
        concerns = extracted_data.get('primary_concerns', []) or ['not specified']
        strengths = extracted_data.get('strengths', 'not specified')
        if strengths and len(strengths) > 100:
            strengths = strengths[:100]

        prompt = f"""Summarize the following conversation between a parent and Chitta (a child development support system).

**Extracted information about the child:**
- Name: {child_name}
- Age: {age}
- Areas of concern: {', '.join(concerns)}
- Strengths: {strengths}

**Conversation:**
{conversation_text}

**Instructions:**
Return JSON with this structure:
{{
    "summary": "Brief summary of the conversation (up to 300 words, in the same language as the conversation)",
    "key_topics": ["topic 1", "topic 2", ...],
    "decisions_made": ["decision 1", "decision 2", ...],
    "open_questions": ["open question 1", ...],
    "emotional_tone": "Brief description of the parent's emotional tone",
    "next_suggested_topic": "The next topic worth discussing"
}}

Focus on:
1. What the parent shared about the child
2. What concerns the parent
3. What's important to the parent
4. Any decisions or agreements made"""

        return prompt

    def _format_conversation(self, conversation_history: List[Dict]) -> str:
        """Format conversation history for the prompt (English labels for LLM)"""
        lines = []
        for msg in conversation_history[-30:]:  # Limit to last 30 messages for summary
            role = "Parent" if msg.get("role") == "user" else "Chitta"
            content = msg.get("content", "")[:500]  # Truncate long messages
            lines.append(f"{role}: {content}")

        return "\n\n".join(lines)

    def _create_fallback_summary(
        self,
        conversation_history: List[Dict],
        extracted_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a simple fallback summary without LLM, using i18n"""
        child_name = extracted_data.get("child_name")
        concerns = extracted_data.get("primary_concerns", [])

        summary_parts = []
        if child_name:
            summary_parts.append(t("milestones.met_child", child_name=child_name))
        if concerns:
            # Translate concern labels
            concern_translations = t_section("domain.concerns")
            translated = [concern_translations.get(c, c) for c in concerns[:3]]
            summary_parts.append(t("domain.summary_templates.concerns_discussed",
                                   concerns=", ".join(translated)))

        # Message count (framework info, not translated)
        msg_count = len(conversation_history)
        summary_parts.append(f"({msg_count} messages)")

        return {
            "summary": ". ".join(summary_parts),
            "key_topics": concerns[:3] if concerns else [],
            "decisions_made": [],
            "message_count": msg_count
        }

    def get_compressed_context(
        self,
        conversation_history: List[Dict],
        summary: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """
        Get compressed conversation context for LLM

        Returns recent messages plus summary of older ones

        Args:
            conversation_history: Full conversation history
            summary: Pre-computed summary (optional)

        Returns:
            Compressed list suitable for LLM context
        """
        if len(conversation_history) <= SUMMARY_KEEP_RECENT:
            return conversation_history

        # Keep recent messages
        recent = conversation_history[-SUMMARY_KEEP_RECENT:]

        # Create summary message for older content
        older_count = len(conversation_history) - SUMMARY_KEEP_RECENT

        if summary and summary.get("summary"):
            summary_text = summary["summary"]
        else:
            summary_text = f"[סיכום של {older_count} הודעות קודמות]"

        summary_message = {
            "role": "system",
            "content": f"<conversation_summary>\n{summary_text}\n</conversation_summary>",
            "is_summary": True
        }

        return [summary_message] + recent

    def extract_conversation_milestones(
        self,
        conversation_history: List[Dict],
        extracted_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract key milestones from the conversation

        Useful for showing progress to returning users.
        Uses i18n for milestone descriptions.

        Args:
            conversation_history: Full conversation history
            extracted_data: Current extracted data

        Returns:
            List of milestone dicts
        """
        milestones = []

        # Check for key data points being established
        if extracted_data.get("child_name"):
            milestones.append({
                "type": "info_gathered",
                "description": t("milestones.met_child",
                                child_name=extracted_data['child_name']),
                "icon": "👋"
            })

        if extracted_data.get("primary_concerns"):
            concerns = extracted_data["primary_concerns"]
            milestones.append({
                "type": "concerns_identified",
                "description": t("milestones.concerns_identified",
                                count=len(concerns)),
                "icon": "🎯"
            })

        if extracted_data.get("strengths"):
            milestones.append({
                "type": "strengths_identified",
                "description": t("milestones.strengths_identified"),
                "icon": "💪"
            })

        # Check message count milestones
        msg_count = len(conversation_history)
        if msg_count >= 10:
            milestones.append({
                "type": "conversation_depth",
                "description": t("milestones.deep_conversation"),
                "icon": "💬"
            })

        return milestones


# Singleton
_conversation_summarizer: Optional[ConversationSummarizer] = None


def get_conversation_summarizer() -> ConversationSummarizer:
    """Get singleton ConversationSummarizer instance"""
    global _conversation_summarizer
    if _conversation_summarizer is None:
        _conversation_summarizer = ConversationSummarizer()
    return _conversation_summarizer
