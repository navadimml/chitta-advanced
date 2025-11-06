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
        child_name = context.get("child_name", "הילד/ה")

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
        child_name = context.get("child_name", "הילד/ה")
        completeness = context.get("completeness", 0.0)
        interview_complete = completeness >= 0.80

        # Get feature list based on current state
        current_state = {
            "interview_complete": interview_complete,
            "minimum_videos": context.get("video_count", 0) >= 3,
            "reports_available": context.get("reports_available", False)
        }

        feature_list = domain_knowledge.get_feature_list_hebrew(current_state)

        # Check if there's a matching FAQ answer
        faq_key = domain_knowledge.match_faq_question("מה אני יכול לעשות")
        if faq_key and faq_key in self.faq:
            faq_answer = self.faq[faq_key]["answer_hebrew"]
            # Replace placeholders
            faq_answer = faq_answer.replace("{child_name}", child_name)
            answer = faq_answer
        else:
            answer = feature_list

        return f"""## ⚠️ INFORMATION REQUEST DETECTED

The parent asked: **"What can I do in this app?"**

This is a legitimate question about app features. You should answer it!

**Here's what you should tell them:**

{answer}

**After answering, ask if they want to continue the interview.**"""

    def _get_process_knowledge(self) -> str:
        """Get knowledge about the process"""
        process = domain_knowledge.PROCESS_OVERVIEW_HEBREW

        return f"""## ⚠️ INFORMATION REQUEST DETECTED

The parent asked about the process/how it works.

**Here's the process overview to share:**

{process}

**After explaining, ask if they want to continue the interview.**"""

    def _get_current_state_knowledge(self, context: Dict) -> str:
        """Get knowledge about current state and next steps"""
        completeness = context.get("completeness", 0.0)
        completeness_pct = int(completeness * 100)
        child_name = context.get("child_name", "הילד/ה")

        if completeness < 0.80:
            return f"""## ⚠️ INFORMATION REQUEST DETECTED

The parent asked where they are in the process.

**Current state:**
- Stage: Interview (in progress)
- Completeness: {completeness_pct}%
- Next: Continue interview until ~80%+, then video guidelines

**Tell them:**
"אנחנו בשלב הראיון, שזה הבסיס לכל התהליך. עברנו בערך {completeness_pct}% - עוד קצת שיחה ואז נעבור להנחיות צילום. רוצה שנמשיך?"
"""
        else:
            return f"""## ⚠️ INFORMATION REQUEST DETECTED

The parent asked where they are in the process.

**Current state:**
- Stage: Interview complete ({completeness_pct}%)
- Next: Video filming guidelines

**Tell them:**
"סיימנו את הראיון! ({completeness_pct}%) השלב הבא הוא שאני אכין לך הנחיות צילום מותאמות אישית ל{child_name}. מוכנ/ה לקבל אותן?"
"""

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

            # Replace placeholders
            child_name = context.get("child_name", "הילד/ה")
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
