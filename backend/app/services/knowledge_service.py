"""
Knowledge Service

GENERAL service that handles information requests using domain-specific knowledge.
This service structure works for any domain - just swap the domain_knowledge module.

Uses LLM-based classification for FAQ matching - intelligent without heavy dependencies.
"""

import logging
from typing import Dict, Optional, Tuple
from ..prompts.intent_types import InformationRequestType, DetectedIntent, IntentCategory
from ..prompts.prerequisites import Action
from ..prompts import domain_knowledge
from .llm.factory import create_llm_provider
from .llm.base import Message


logger = logging.getLogger(__name__)


class KnowledgeService:
    """
    Service for handling information requests about the app/process

    This is a GENERAL pattern that works across domains. The domain-specific
    content comes from the domain_knowledge module.

    Uses LLM-based FAQ matching - intelligent, lightweight, multilingual!
    """

    def __init__(self, llm_provider=None):
        """Initialize knowledge service

        Args:
            llm_provider: Optional LLM provider for intelligent intent detection and FAQ matching
        """
        self.domain_info = domain_knowledge.DOMAIN_INFO
        self.features = domain_knowledge.FEATURES
        self.faq = domain_knowledge.FAQ
        self.llm = llm_provider or create_llm_provider()
        logger.info(f"KnowledgeService initialized for domain: {self.domain_info['domain']}")

    async def detect_unified_intent(
        self,
        user_message: str,
        recent_conversation: list = None,
        available_artifacts: list = None,
        child_context: dict = None
    ) -> DetectedIntent:
        """
        Unified intent detection with rich dialogue context (Wu Wei approach)

        Instead of simplified boolean flags, we pass ACTUAL rich context:
        - Recent conversation exchanges (to understand dialogue flow)
        - Available artifacts (to know what can be consulted about)
        - Child context (to personalize developmental answers)

        This lets the LLM naturally understand the situation without rigid rules.

        Args:
            user_message: User's current message
            recent_conversation: Last 3-4 conversation exchanges [{"role": "...", "content": "..."}]
            available_artifacts: List of artifact names/titles that exist
            child_context: Dict with child_name, age, primary_concerns

        Returns:
            DetectedIntent with category and specific details
        """
        # Build rich context for the prompt
        context_parts = []

        # 1. Recent dialogue flow (crucial for understanding if parent is responding)
        if recent_conversation:
            context_parts.append("**Recent conversation:**")
            for turn in recent_conversation[-4:]:  # Last 2 exchanges
                role_name = "Chitta" if turn.get("role") == "assistant" else "Parent"
                content_preview = turn.get("content", "")[:150]
                context_parts.append(f"  {role_name}: {content_preview}...")

        # 2. Available artifacts (to know what can be consulted about)
        if available_artifacts:
            context_parts.append(f"\n**Available artifacts/reports:** {', '.join(available_artifacts)}")
        else:
            context_parts.append("\n**Available artifacts/reports:** None yet")

        # 3. Child context (for developmental questions)
        if child_context:
            child_name = child_context.get("child_name", "")
            age = child_context.get("age", "")
            concerns = child_context.get("primary_concerns", [])
            if child_name:
                context_parts.append(f"\n**Child:** {child_name}, age {age}, concerns: {', '.join(concerns) if concerns else 'not yet discussed'}")

        rich_context = "\n".join(context_parts) if context_parts else "No prior context (conversation just started)"

        detection_prompt = f"""Analyze this parent's message and understand their intent in the context of the dialogue.

**DIALOGUE CONTEXT:**
{rich_context}

**Current parent message:** "{user_message}"

---

**Your task:** Understand what the parent NEEDS right now. Don't force into rigid categories - understand the natural flow.

**Intent Categories:**

1. **CONVERSATION** - Parent is SHARING/RESPONDING in the natural dialogue flow

   **Key indicators:**
   - Chitta just asked a question and parent is answering it
   - Parent is responding to something Chitta said ("תודה ששאלת", "כן זה נכון")
   - Parent is sharing new observations about their child
   - Parent is elaborating on something already discussed
   - The message flows naturally from the previous exchange

   **Examples:**
   - Chitta asks "ספרי לי על הדיבור של יוני" → Parent: "הוא מדבר רק כמה מילים בודדות"
   - Chitta says "נשמע שהוא מחפש גירוי חושי" → Parent: "כן, זה נכון! תודה ששאלת על זה"
   - Parent shares: "היום הוא עשה משהו מעניין", "הילד שלי בן 5"

   **CRITICAL:** If parent is answering Chitta's question → ALWAYS CONVERSATION!

2. **CONSULTATION** - Parent is asking a NEW question seeking expertise

   This is **the beauty and strength of Chitta**: Parent can ask ANY question about child development,
   and Chitta uses the LLM's huge developmental knowledge + the specific child's context to give
   personalized expert answers.

   **Two types (but both are CONSULTATION):**

   a) **General developmental questions:**
      - "מה זה חיפוש חושי?" (What is sensory seeking?)
      - "איך יודעים שיש ADHD?" (How do you know if there's ADHD?)
      - "מה עושים עם התפרצויות?" (What do you do with meltdowns?)

   b) **Questions about Chitta's specific analysis:**
      - "למה אמרת שיש לו חיפוש חושי?" (Why did you say he has sensory seeking?)
      - "מה הפסיכולוגית כתבה?" (What did the psychologist write?)
      - "האם הדיבור שלו השתפר?" (Has his speech improved?)

   **Key indicators:**
   - Parent asks a NEW question (not answering Chitta)
   - Question is about child development, strategies, or patterns
   - Question may reference artifacts/reports OR general knowledge
   - Parent is seeking EXPLANATION, not just chatting

   **Note:** Only categorize as CONSULTATION if artifacts exist OR it's a general developmental question.
   If no artifacts exist and parent asks "Why did you say X?", it might be CONVERSATION (clarifying dialogue).

3. **ACTION** - Parent wants something specific delivered/executed

   **Examples:**
   - "תן לי דוח" (show me report)
   - "איך מעלים סרטון?" (how to upload video?)
   - "תראי הנחיות" (show guidelines)
   - "עבור לבדיקה" (start test mode)

   **Actions:** view_report, upload_video, view_video_guidelines, find_experts, add_journal_entry, start_test_mode, start_demo

4. **INFORMATION** - Parent asking about the app/process/features (meta questions)

   **Examples:**
   - "מה זה צ'יטה?" (what is this app?)
   - "איך זה עובד?" (how does this work?)
   - "איפה אני בתהליך?" (where am I in the process?)

   **Sub-types:** APP_FEATURES, PROCESS_EXPLANATION, CURRENT_STATE

---

**Response format:**
Line 1: Category (CONVERSATION, CONSULTATION, ACTION, or INFORMATION)
Line 2 (if needed): Sub-type or specific action

**Examples with context:**

Example 1:
Context: Chitta just asked "ספרי לי עוד על הדיבור של יוני"
Parent: "תודה ששאלת. הוא מדבר רק כמה מילים בודדות"
→ CONVERSATION (parent is ANSWERING Chitta's question)

Example 2:
Context: Chitta said "נשמע שיוני מחפש גירוי חושי במערכת הווסטיבולרית"
Parent: "מה זה חיפוש חושי?"
→ CONSULTATION (parent asking NEW developmental question)

Example 3:
Context: Artifacts exist: baseline_parent_report
Parent: "למה כתבת שיש לו חיפוש חושי?"
→ CONSULTATION (parent asking about Chitta's specific analysis)

Example 4:
Context: No artifacts yet, conversation in progress
Parent: "למה אמרת שזה גירוי חושי?"
→ CONVERSATION (clarifying what Chitta just said in dialogue, not consulting a report)

Example 5:
Context: Any
Parent: "תן לי את הדוח"
→ ACTION\nview_report"""

        try:
            response = await self.llm.chat(
                messages=[
                    Message(role="system", content=detection_prompt),
                    Message(role="user", content=user_message)
                ],
                functions=None,
                temperature=0.1,
                max_tokens=50
            )

            lines = [line.strip() for line in response.content.strip().split('\n') if line.strip()]
            category_text = lines[0].upper() if lines else "CONVERSATION"

            logger.info(f"Unified intent detection: {category_text} for message: {user_message[:50]}")

            # Parse category
            if category_text == "INFORMATION":
                info_type_text = lines[1].upper() if len(lines) > 1 else "APP_FEATURES"

                # Map to InformationRequestType
                info_type = None
                if info_type_text == "APP_FEATURES":
                    info_type = InformationRequestType.APP_FEATURES
                elif info_type_text == "PROCESS_EXPLANATION":
                    info_type = InformationRequestType.PROCESS_EXPLANATION
                elif info_type_text == "CURRENT_STATE":
                    info_type = InformationRequestType.CURRENT_STATE
                else:
                    info_type = InformationRequestType.APP_FEATURES  # Default

                return DetectedIntent(
                    category=IntentCategory.INFORMATION_REQUEST,
                    information_type=info_type,
                    user_message=user_message
                )

            elif category_text == "ACTION":
                action_text = lines[1].lower() if len(lines) > 1 else None

                # Validate it's a real action
                valid_actions = [a.value for a in Action]
                if action_text in valid_actions:
                    return DetectedIntent(
                        category=IntentCategory.ACTION_REQUEST,
                        specific_action=action_text,
                        user_message=user_message
                    )
                else:
                    # Invalid action, treat as conversation
                    logger.warning(f"Invalid action detected: {action_text}, treating as conversation")
                    return DetectedIntent(
                        category=IntentCategory.DATA_COLLECTION,
                        user_message=user_message
                    )

            elif category_text == "CONSULTATION":
                # User is asking about previous conversations, reports, or insights
                return DetectedIntent(
                    category=IntentCategory.CONSULTATION,
                    user_message=user_message
                )

            else:
                # CONVERSATION or anything else
                return DetectedIntent(
                    category=IntentCategory.DATA_COLLECTION,
                    user_message=user_message
                )

        except Exception as e:
            logger.warning(f"Unified intent detection failed: {e} - defaulting to CONVERSATION")
            return DetectedIntent(
                category=IntentCategory.DATA_COLLECTION,
                user_message=user_message
            )

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

    async def match_faq_with_llm(self, user_message: str) -> Optional[str]:
        """
        Match FAQ using LLM classification

        Much more intelligent than string matching - handles paraphrasing, synonyms,
        context, and multilingual queries. No heavy dependencies!

        Args:
            user_message: User's question

        Returns:
            FAQ key if matched, None if no good match
        """
        # Build list of FAQ categories for LLM to choose from
        faq_list = "\n".join([f"- {key}: {data.get('question_patterns', [])[0] if data.get('question_patterns') else key}"
                              for key, data in self.faq.items()])

        classification_prompt = f"""Analyze this user question and determine which FAQ category it best matches, if any.

User question: "{user_message}"

Available FAQ categories:
{faq_list}

Instructions:
1. If the question clearly matches one of the FAQ categories, respond with ONLY the FAQ key (e.g., "why_the_name_chitta")
2. If the question doesn't match any FAQ, respond with "NO_MATCH"
3. Consider paraphrasing, synonyms, and context
4. Handle both Hebrew and English
5. Be strict - only match if you're confident it's asking about that FAQ topic

Respond with ONLY the FAQ key or "NO_MATCH"."""

        try:
            response = await self.llm.chat(
                messages=[Message(role="user", content=classification_prompt)],
                functions=None,
                temperature=0.1,
                max_tokens=50
            )

            faq_key = response.content.strip()

            if faq_key == "NO_MATCH" or faq_key not in self.faq:
                logger.info(f"No FAQ match for: {user_message[:50]}...")
                return None

            logger.info(f"✓ FAQ matched via LLM: {faq_key} for question: {user_message[:50]}...")
            return faq_key

        except Exception as e:
            logger.error(f"LLM-based FAQ matching failed: {e}")
            return None

    async def get_direct_answer(
        self,
        user_message: str,
        context: Dict
    ) -> Optional[str]:
        """
        Get direct answer to FAQ question if available

        Uses LLM classification for robust FAQ detection - handles paraphrasing,
        multilingual queries, and context without heavy dependencies.

        Args:
            user_message: User's question
            context: Current context

        Returns:
            Direct Hebrew answer if available, None otherwise
        """
        # Use LLM-based matching
        faq_key = await self.match_faq_with_llm(user_message)

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
