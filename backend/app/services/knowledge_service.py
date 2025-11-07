"""
Knowledge Service

GENERAL service that handles information requests using domain-specific knowledge.
This service structure works for any domain - just swap the domain_knowledge module.
"""

import logging
from typing import Dict, Optional
from ..prompts.intent_types import InformationRequestType
from ..prompts import domain_knowledge
from .llm.factory import create_llm_provider
from .llm.base import Message


logger = logging.getLogger(__name__)


class KnowledgeService:
    """
    Service for handling information requests about the app/process

    This is a GENERAL pattern that works across domains. The domain-specific
    content comes from the domain_knowledge module.
    """

    def __init__(self, llm_provider=None):
        """Initialize knowledge service

        Args:
            llm_provider: Optional LLM provider for intelligent intent detection
        """
        self.domain_info = domain_knowledge.DOMAIN_INFO
        self.features = domain_knowledge.FEATURES
        self.faq = domain_knowledge.FAQ
        self.llm = llm_provider or create_llm_provider()
        logger.info(f"KnowledgeService initialized for domain: {self.domain_info['domain']}")

    async def detect_information_request(self, user_message: str) -> Optional[InformationRequestType]:
        """
        Detect if user is asking for information about the app/process using LLM

        This is more accurate than keyword matching and can handle variations.

        Args:
            user_message: User's message

        Returns:
            InformationRequestType if detected, None otherwise
        """
        # Quick LLM call to classify information request intent
        detection_prompt = f"""Analyze this user message and determine if they're asking for INFORMATION about the app/process/features.

IMPORTANT: Even if they ALSO mention their child, if they're asking about the app/process, classify it as an information request!

User message: "{user_message}"

Information request types:

- APP_FEATURES or PROCESS_EXPLANATION: Asking what the app does, how it works, what happens
  Examples:
  • "מה האפליקציה עושה?", "מה זה?", "מה צ'יטה?"
  • "איך זה עובד?", "מה התהליך?", "מה הסבר על זה?"
  • "אמרו לי שמצלמים וידאו", "שומעים דוחות?", "מה עם הסרטונים?"
  • "היא צועקת אבל רוצה להבין מה האפליקציה עושה" ← Still APP question!
  • "before we continue, what is this?", "explain what this app does"

- CURRENT_STATE: Asking where they are in the process, what stage
  Examples: "איפה אני?", "מה השלב?", "where am I?", "what's next for me?"

- NOT_INFORMATION: ONLY talking about their child, NO questions about the app/process
  Examples: "הילד שלי אוהב לקרוא", "he's 3 years old", "כן אני מודאגת מהדיבור"

KEY: If the message contains ANY question about the app/process/what happens, classify it as APP_FEATURES or PROCESS_EXPLANATION (use your judgment which fits better).

Respond with ONLY one of: APP_FEATURES, PROCESS_EXPLANATION, CURRENT_STATE, or NOT_INFORMATION"""

        try:
            response = await self.llm.chat(
                messages=[
                    Message(role="system", content=detection_prompt),
                    Message(role="user", content=user_message)
                ],
                functions=None,
                temperature=0.1,
                max_tokens=20
            )

            intent_text = response.content.strip().upper()
            logger.info(f"Information request detection: {intent_text} for message: {user_message[:50]}")

            # Map to InformationRequestType
            if intent_text == "APP_FEATURES":
                return InformationRequestType.APP_FEATURES
            elif intent_text == "PROCESS_EXPLANATION":
                return InformationRequestType.PROCESS_EXPLANATION
            elif intent_text == "CURRENT_STATE":
                return InformationRequestType.CURRENT_STATE
            else:
                return None

        except Exception as e:
            logger.warning(f"Information request detection failed: {e} - returning None")
            return None

    def get_knowledge_for_prompt(
        self,
        information_type: InformationRequestType,
        context: Dict
    ) -> str:
        """
        Get domain knowledge formatted for injection into LLM prompt

        Args:
            information_type: Type of information requested
            context: Current state context (child_name, completeness, etc.)

        Returns:
            Formatted knowledge string to inject into prompt
        """
        if information_type == InformationRequestType.APP_FEATURES:
            return self._get_app_features_knowledge(context)

        elif information_type == InformationRequestType.PROCESS_EXPLANATION:
            return self._get_process_knowledge()

        elif information_type == InformationRequestType.CURRENT_STATE:
            return self._get_current_state_knowledge(context)

        else:
            return ""

    def _get_app_features_knowledge(self, context: Dict) -> str:
        """Get knowledge about app features"""
        # Handle None or empty child_name by using default
        child_name = context.get("child_name") or "הילד/ה"

        # Build comprehensive knowledge base with multiple FAQ entries
        knowledge_sections = []

        # Name meaning (for questions about why "Chitta")
        if "why_the_name_chitta" in self.faq:
            name_answer = self.faq["why_the_name_chitta"]["answer_hebrew"]
            name_answer = name_answer.replace("{child_name}", child_name)
            knowledge_sections.append(f"### Why the Name 'Chitta':\n{name_answer}")

        # Main app explanation
        if "what_is_app_and_safety" in self.faq:
            main_answer = self.faq["what_is_app_and_safety"]["answer_hebrew"]
            main_answer = main_answer.replace("{child_name}", child_name)
            knowledge_sections.append(f"### What Chitta Does:\n{main_answer}")

        # Comprehensive privacy details
        if "data_privacy_comprehensive" in self.faq:
            privacy_answer = self.faq["data_privacy_comprehensive"]["answer_hebrew"]
            privacy_answer = privacy_answer.replace("{child_name}", child_name)
            knowledge_sections.append(f"### Privacy & Data Security:\n{privacy_answer}")

        # Sharing with professionals (digital process - NO paper forms!)
        if "sharing_with_professionals" in self.faq:
            sharing_answer = self.faq["sharing_with_professionals"]["answer_hebrew"]
            sharing_answer = sharing_answer.replace("{child_name}", child_name)
            knowledge_sections.append(f"### Sharing Data with Professionals:\n{sharing_answer}")

        # System/meta questions (how Chitta works, prompts, etc.)
        if "system_instructions" in self.faq:
            system_answer = self.faq["system_instructions"]["answer_hebrew"]
            system_answer = system_answer.replace("{child_name}", child_name)
            knowledge_sections.append(f"### About How Chitta Works (AI/System):\n{system_answer}")

        comprehensive_knowledge = "\n\n".join(knowledge_sections)

        return f"""## 📋 KNOWLEDGE BASE: About Chitta App

The parent is asking about the app/what it does/how it works. Use this FACTUAL information:

{comprehensive_knowledge}

**Instructions for your response:**
1. Answer their specific question naturally using the relevant facts above
2. If they ALSO mentioned something about their child (mixed intent), acknowledge that too
3. After explaining, gently guide back: "יש לך עוד שאלות, או שנמשיך בשיחה על {child_name}?"
4. Be conversational - adapt to their specific question, don't just list everything
5. For meta questions (prompts, how you work), use the "About How Chitta Works" section
6. For sharing/privacy questions, use the specific sections - be clear about digital processes!

**CRITICAL: Use ONLY the factual information provided above. DO NOT make up features, processes, or privacy details. Especially DO NOT invent paper forms, physical signatures, or manual processes - everything is digital!**"""

    def _get_process_knowledge(self) -> str:
        """Get knowledge about the process"""
        process = domain_knowledge.PROCESS_OVERVIEW_HEBREW

        return f"""## 📋 KNOWLEDGE BASE: Chitta Process

The parent is asking how the process works. Use this FACTUAL information:

{process}

**Instructions for your response:**
1. Explain the process naturally, adapting to what they specifically asked
2. If they mentioned concerns about their child too (mixed intent), acknowledge those
3. Be conversational - help them understand where they are and what comes next
4. Guide back to interview: "רוצה שנמשיך בשיחה על הילד/ה שלך?"

**CRITICAL: Use ONLY the factual process information above. DO NOT invent steps or timelines.**"""

    def _get_current_state_knowledge(self, context: Dict) -> str:
        """Get knowledge about current state and next steps"""
        completeness = context.get("completeness", 0.0)
        completeness_pct = int(completeness * 100)
        # Handle None or empty child_name by using default
        child_name = context.get("child_name") or "הילד/ה"

        if completeness < 0.80:
            state_info = f"""
**Where they are:**
- Stage: Interview (in progress)
- Progress: {completeness_pct}%
- What's happening: Gathering information about {child_name}
- Next step: Complete interview (~80%+), then personalized video filming guidelines

**What to tell them:**
Explain naturally where we are, what we've covered so far, and that we need to continue
the interview a bit more before moving to videos. Be encouraging about progress.
"""
        else:
            state_info = f"""
**Where they are:**
- Stage: Interview complete ({completeness_pct}%)
- What's next: Generate personalized video filming guidelines for {child_name}
- Then: Film videos, AI analysis, comprehensive report

**What to tell them:**
Celebrate that the interview is complete and explain the next steps naturally.
"""

        return f"""## 📋 KNOWLEDGE BASE: Current State

The parent wants to know where they are in the process. Here's the factual state:

{state_info}

**Instructions for your response:**
1. Answer naturally based on their actual progress
2. Be encouraging and clear about next steps
3. If they seem confused or impatient, reassure them about the value of each step
4. Guide appropriately: continue interview OR move to next phase

**Use ONLY the state information above. DO NOT make up progress or skip steps.**"""

    def get_direct_answer(
        self,
        user_message: str,
        context: Dict
    ) -> Optional[str]:
        """
        Get direct answer to FAQ question if available

        Args:
            user_message: User's question
            context: Current context

        Returns:
            Direct Hebrew answer if available, None otherwise
        """
        faq_key = domain_knowledge.match_faq_question(user_message)

        if faq_key and faq_key in self.faq:
            answer = self.faq[faq_key]["answer_hebrew"]

            # Replace placeholders - handle None or empty child_name
            child_name = context.get("child_name") or "הילד/ה"
            answer = answer.replace("{child_name}", child_name)

            return answer

        return None


# Singleton instance
_knowledge_service = None


def get_knowledge_service() -> KnowledgeService:
    """Get or create singleton knowledge service instance"""
    global _knowledge_service
    if _knowledge_service is None:
        _knowledge_service = KnowledgeService()
    return _knowledge_service
