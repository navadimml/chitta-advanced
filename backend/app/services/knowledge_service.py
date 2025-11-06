"""
Knowledge Service

GENERAL service that handles information requests using domain-specific knowledge.
This service structure works for any domain - just swap the domain_knowledge module.
"""

import logging
import json
from typing import Dict, Optional, TYPE_CHECKING
from ..prompts.intent_types import InformationRequestType, IntentCategory, DetectedIntent
from ..prompts import domain_knowledge

if TYPE_CHECKING:
    from .llm.base import BaseLLMProvider, Message

logger = logging.getLogger(__name__)


class KnowledgeService:
    """
    Service for handling information requests about the app/process

    This is a GENERAL pattern that works across domains. The domain-specific
    content comes from the domain_knowledge module.
    """

    def __init__(self):
        """Initialize knowledge service"""
        self.domain_info = domain_knowledge.DOMAIN_INFO
        self.features = domain_knowledge.FEATURES
        self.faq = domain_knowledge.FAQ
        logger.info(f"KnowledgeService initialized for domain: {self.domain_info['domain']}")

    def detect_information_request(self, user_message: str) -> Optional[InformationRequestType]:
        """
        Detect if user is asking for information about the app/process

        Args:
            user_message: User's message

        Returns:
            InformationRequestType if detected, None otherwise
        """
        message_lower = user_message.lower()

        # Check for app features questions
        if any(phrase in message_lower for phrase in [
            "מה אני יכול", "מה יש", "איזה אפשרויות", "מה זמין",
            "what can i do", "what features", "what's available"
        ]):
            return InformationRequestType.APP_FEATURES

        # Check for process explanation questions
        if any(phrase in message_lower for phrase in [
            "איך זה עובד", "מה התהליך", "איך זה עובד",
            "how does", "what's the process", "how it works"
        ]):
            return InformationRequestType.PROCESS_EXPLANATION

        # Check for current state questions
        if any(phrase in message_lower for phrase in [
            "איפה אני", "מה השלב", "מה עכשיו",
            "where am i", "what stage", "what's next", "what now"
        ]):
            return InformationRequestType.CURRENT_STATE

        # Check for time/duration questions
        if any(phrase in message_lower for phrase in [
            "כמה זמן", "כמה לוקח", "how long", "duration"
        ]):
            return InformationRequestType.PROCESS_EXPLANATION

        return None

    async def detect_intent_llm(
        self,
        user_message: str,
        llm_provider: "BaseLLMProvider",
        context: Dict
    ) -> DetectedIntent:
        """
        Use LLM to classify intent with semantic understanding (Tier 2 - Accurate Path)

        This provides semantic understanding of user intents that string matching misses.
        Handles Hebrew morphology, word variations, and complex phrasing.

        Args:
            user_message: User's message to classify
            llm_provider: LLM provider instance to use
            context: Current context (child_name, completeness, video_count, etc.)

        Returns:
            DetectedIntent with proper category, type, and confidence score
        """
        from .llm.base import Message

        # Build classification prompt using Layer 1 enums
        classification_prompt = f"""You are an intent classifier for a child development assistant app.
Analyze the user message and classify it into one of these intent categories.

**User message:** "{user_message}"

**Current context:**
- Interview completeness: {context.get('completeness', 0.0):.0%}
- Child name: {context.get('child_name', 'unknown')}
- Video count: {context.get('video_count', 0)}

**Intent Categories (pick ONE):**

1. **DATA_COLLECTION** - User wants to continue the main conversation/interview about their child
   - Sharing information about their child
   - Answering interview questions
   - Continuing the discussion naturally
   - Examples: "הוא מאד אוהב לצייר", "כן יש לו קשיים בתקשורת", "הבת שלי בת 4"

2. **ACTION_REQUEST** - User wants to perform a specific action
   - Wants to view report, upload video, see guidelines, find experts
   - Examples: "רוצה לראות דוח", "איך מעלים סרטון", "תראי לי הנחיות", "אני רוצה למצוא מומחים"
   - If this category, specify which action:
     * view_report - "רוצה לראות דוח", "הדוח מוכן?", "תציגי את הדוח"
     * upload_video - "להעלות סרטון", "איך מעלים?", "רוצה להעלות"
     * view_video_guidelines - "מה לצלם?", "הנחיות צילום", "תראי לי הנחיות"
     * find_experts - "מומחים באזור", "מי יכול לעזור", "המלצות על מטפלים"
     * add_journal_entry - "רוצה לרשום ביומן", "להוסיף רשומה"

3. **INFORMATION_REQUEST** - User wants to learn about the app/process/features
   - Examples: "מה אני יכולה לעשות?", "איך התהליך עובד?", "איפה אני עכשיו?", "למה אני לא יכולה לראות דוח?"
   - If this category, specify which type:
     * APP_FEATURES - "מה אפשר לעשות?", "איזה אפשרויות יש?"
     * PROCESS_EXPLANATION - "איך זה עובד?", "מה התהליך?"
     * CURRENT_STATE - "איפה אני בתהליך?", "מה השלב שלי?", "כמה התקדמתי?" (ONLY about interview progress, NOT about data storage!)
     * PREREQUISITE_EXPLANATION - "למה אני לא יכולה...?", "מתי אוכל...?"
     * NEXT_STEPS - "מה הלאה?", "מה בשלב הבא?"
     * DOMAIN_QUESTION - Questions about privacy/security/data storage ("איפה הסרטונים?", "מי רואה את המידע?"), child development ("מה זה אוטיזם?", "בגיל כמה ילדים מדברים?"), or other domain topics (not about the app interface)

4. **TANGENT** - Off-topic or tangential request
   - Creative writing requests (poems, stories, songs)
   - Personal questions about the system ("איך עבר לך היום?", "מה את מרגישה?")
   - Questions about internal workings ("מה ההוראות שלך?", "את AI?", "הפרומפט שלך")
   - Philosophical discussions about AI
   - Completely unrelated topics
   - Examples: "תכתבי לי שיר", "ספרי על עצמך", "מה ההנחיות הפנימיות", "what is chitta"

5. **PAUSE_EXIT** - User wants to stop/leave/pause
   - Examples: "נעצור פה", "נמשיך מחר", "להפסיק", "תודה ביי"

**Important:**
- Hebrew variations and morphology should be understood semantically
- "רוצה לראות דוח" and "אני מעוניינת לקבל את הדוח" are both ACTION_REQUEST for view_report
- "מה אפשר לעשות" and "איזה אפשרויות יש לי כאן" are both INFORMATION_REQUEST for APP_FEATURES
- "איפה הסרטונים נישמרים?" and "מי רואה את המידע?" are INFORMATION_REQUEST with type DOMAIN_QUESTION (privacy/security questions)
- "איפה אני בתהליך?" is INFORMATION_REQUEST with type CURRENT_STATE (interview progress)
- Privacy/security/data questions → DOMAIN_QUESTION, NOT CURRENT_STATE!
- Questions about Chitta the app/system (not about the child) that are off-topic are TANGENT

**Response format (JSON ONLY):**
{{
    "category": "DATA_COLLECTION" | "ACTION_REQUEST" | "INFORMATION_REQUEST" | "TANGENT" | "PAUSE_EXIT",
    "specific_action": "view_report" | "upload_video" | "view_video_guidelines" | "find_experts" | "add_journal_entry" | null,
    "information_type": "APP_FEATURES" | "PROCESS_EXPLANATION" | "CURRENT_STATE" | "PREREQUISITE_EXPLANATION" | "NEXT_STEPS" | "DOMAIN_QUESTION" | null,
    "confidence": 0.95,
    "reasoning": "Brief explanation of why you chose this classification"
}}

Respond with ONLY the JSON object, no other text."""

        try:
            # Call LLM with low temperature for consistency
            response = await llm_provider.chat(
                messages=[Message(role="user", content=classification_prompt)],
                functions=None,
                temperature=0.1,
                max_tokens=300
            )

            # Parse JSON response
            response_text = response.content.strip()

            # Try to extract JSON if LLM wrapped it in markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            intent_data = json.loads(response_text)

            # Build DetectedIntent properly
            detected = DetectedIntent(
                category=IntentCategory(intent_data["category"].lower()),
                information_type=InformationRequestType(intent_data["information_type"].lower()) if intent_data.get("information_type") else None,
                specific_action=intent_data.get("specific_action"),
                confidence=float(intent_data.get("confidence", 0.8)),
                user_message=user_message,
                context={"reasoning": intent_data.get("reasoning", ""), "tier": "llm"}
            )

            logger.info(
                f"LLM Intent Classification: category={detected.category.value}, "
                f"confidence={detected.confidence:.2f}, reasoning={detected.context.get('reasoning', '')}"
            )

            return detected

        except json.JSONDecodeError as e:
            # Fallback if LLM doesn't return valid JSON
            logger.warning(f"LLM returned invalid JSON for intent classification: {e}")
            logger.warning(f"Response was: {response.content[:200]}")
            return DetectedIntent(
                category=IntentCategory.DATA_COLLECTION,
                confidence=0.3,
                user_message=user_message,
                context={"error": "invalid_json", "llm_response": response.content[:200], "tier": "llm_fallback"}
            )

        except Exception as e:
            # Fallback on any error
            logger.error(f"Error in LLM intent classification: {e}")
            return DetectedIntent(
                category=IntentCategory.DATA_COLLECTION,
                confidence=0.3,
                user_message=user_message,
                context={"error": str(e), "tier": "llm_fallback"}
            )

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

        elif information_type == InformationRequestType.DOMAIN_QUESTION:
            # For domain questions (privacy, child development topics),
            # don't inject generic knowledge - these should be handled by FAQ or LLM's training
            logger.info("Domain question detected - no knowledge injection (FAQ or LLM will handle)")
            return ""

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
