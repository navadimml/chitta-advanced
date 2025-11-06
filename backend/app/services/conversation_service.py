"""
Conversation Service - Orchestrates LLM conversations with function calling

This service:
1. Manages conversation flow with LLM
2. Processes function calls (data extraction, actions, completeness)
3. Updates interview state based on LLM responses
4. Generates appropriate system prompts
5. Returns responses with updated context
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from .llm.base import Message, BaseLLMProvider
from .llm.factory import create_llm_provider
from .interview_service import get_interview_service, InterviewService
from .prerequisite_service import get_prerequisite_service, PrerequisiteService
from .knowledge_service import get_knowledge_service, KnowledgeService
from ..prompts.interview_prompt import build_interview_prompt
from ..prompts.dynamic_interview_prompt import build_dynamic_interview_prompt
from ..prompts.interview_functions import INTERVIEW_FUNCTIONS
from ..prompts.interview_functions_lite import INTERVIEW_FUNCTIONS_LITE
from ..prompts.prerequisites import Action

logger = logging.getLogger(__name__)


class ConversationService:
    """
    Manages LLM conversations with continuous extraction

    This is the main orchestrator that connects:
    - LLM Provider (Gemini/Claude/etc)
    - Interview Service (state management)
    - Function calling (data extraction)
    """

    def __init__(
        self,
        llm_provider: Optional[BaseLLMProvider] = None,
        interview_service: Optional[InterviewService] = None,
        prerequisite_service: Optional[PrerequisiteService] = None,
        knowledge_service: Optional[KnowledgeService] = None
    ):
        self.llm = llm_provider or create_llm_provider()
        self.interview_service = interview_service or get_interview_service()
        self.prerequisite_service = prerequisite_service or get_prerequisite_service()
        self.knowledge_service = knowledge_service or get_knowledge_service()

        logger.info(f"ConversationService initialized with {self.llm.get_provider_name()}")

    async def process_message(
        self,
        family_id: str,
        user_message: str,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Process a user message and return LLM response with updated state

        Args:
            family_id: Unique family identifier
            user_message: The user's message
            temperature: LLM sampling temperature

        Returns:
            Dict with:
                - response: LLM's text response
                - function_calls: List of function calls made (if any)
                - completeness: Updated interview completeness (0-100)
                - extracted_data: Summary of extracted data
                - context_cards: UI context cards to show
        """
        logger.info(f"Processing message for family {family_id}: {user_message[:50]}...")

        # 1. Get current interview state
        session = self.interview_service.get_or_create_session(family_id)
        data = session.extracted_data

        # 2. QUICK INTENT DETECTION
        # Detect if user wants to: (a) perform action, (b) get info about app, or (c) just conversing
        intent_detected = None
        prerequisite_check = None
        information_request = None
        injected_knowledge = None

        # First check for information requests using knowledge service (LLM-based)
        information_request = await self.knowledge_service.detect_information_request(user_message)

        if information_request:
            logger.info(f"✓ Information request detected: {information_request}")

            # Build context for knowledge retrieval
            context = {
                "child_name": data.child_name,
                "completeness": session.completeness,
                "video_count": 0,  # TODO: Get from actual video count
                "reports_available": False  # TODO: Get from actual report status
            }

            # Inject knowledge for LLM to use in generating response
            # LLM will generate natural response using this knowledge
            injected_knowledge = self.knowledge_service.get_knowledge_for_prompt(
                information_request,
                context
            )
            logger.info(f"Injecting domain knowledge about {information_request} for LLM to use")

        else:
            # If not information request, check for action request
            intent_prompt = f"""Analyze this message and determine if the user wants to perform a specific ACTION.

User message: "{user_message}"

Common action indicators:
- "תן לי דוח" / "רוצה לראות דוח" → wants report
- "איך מעלים סרטון" / "להעלות סרטון" → wants to upload video
- "תראי לי הנחיות" → wants video guidelines
- Just conversing about child → NO action

Respond with ONLY the action name if detected, or "CONVERSATION" if just talking.
Actions: view_report, upload_video, view_video_guidelines, find_experts, add_journal_entry
Or: CONVERSATION"""

            try:
                intent_response = await self.llm.chat(
                    messages=[
                        Message(role="system", content=intent_prompt),
                        Message(role="user", content=user_message)
                    ],
                    functions=None,
                    temperature=0.1,
                    max_tokens=50
                )

                intent_text = intent_response.content.strip().lower()
                logger.info(f"Intent detection: {intent_text}")

                # Check if it's an action (not just conversation)
                if intent_text != "conversation" and intent_text in [a.value for a in Action]:
                    intent_detected = intent_text
                    logger.info(f"✓ Action request detected: {intent_detected}")

                    # 3. PREREQUISITE CHECK - Is this action currently feasible?
                    context = {
                        "completeness": session.completeness,
                        "child_name": data.child_name,
                        "video_count": 0,  # TODO: Get from actual video storage
                        "analysis_complete": False,  # TODO: Get from actual analysis status
                        "reports_available": False  # TODO: Get from actual report status
                    }

                    prerequisite_check = self.prerequisite_service.check_action_feasible(
                        intent_detected,
                        context
                    )

                    logger.info(
                        f"Prerequisite check: feasible={prerequisite_check.feasible}, "
                        f"missing={prerequisite_check.missing_prerequisites}"
                    )

            except Exception as e:
                logger.warning(f"Intent detection failed: {e} - continuing with normal flow")
                intent_detected = None
                prerequisite_check = None

        # 4. Determine which functions to use (for extraction call later)
        model_name = getattr(self.llm, 'model_name', 'unknown')
        use_lite = self.interview_service.should_use_lite_mode(family_id, model_name)

        if use_lite:
            functions = INTERVIEW_FUNCTIONS_LITE
            logger.debug(f"Using LITE functions for {family_id}")
        else:
            functions = INTERVIEW_FUNCTIONS
            logger.debug(f"Using FULL functions for {family_id}")

        # 5. Build CONTEXTUAL conversation prompt using proper interview prompts
        # Use comprehensive prompts that have all the detailed instructions

        # Check if video guidelines already generated (post-interview phase)
        if session.video_guidelines_generated:
            # Post-interview: simpler prompt focused on answering questions
            base_prompt = f"""You are Chitta (צ'יטה) - a warm, empathetic AI assistant.

The interview is complete and video filming guidelines have been generated!

Current status:
- Child: {data.child_name or "unknown"} (age: {data.age or "unknown"})
- Interview: ✅ Complete ({session.completeness:.0%})
- Video guidelines: ✅ Generated and ready

Your role now:
- Answer any questions the parent has about the process, video filming, or next steps
- Be helpful and supportive
- If they ask about uploading videos, explain they can use the video upload section
- Keep responses brief and helpful

Remember: You are an AI assistant. Be transparent about your nature when relevant."""

        else:
            # During interview: use dynamic interview prompt
            # Natural flow with strategic awareness - not rigid stages!

            if use_lite:
                # For flash-lite: use dynamic prompt that analyzes coverage and provides subtle guidance
                # This maintains natural flow while ensuring comprehensive coverage
                base_prompt = build_dynamic_interview_prompt(
                    child_name=data.child_name or "unknown",
                    age=str(data.age) if data.age else "unknown",
                    gender=data.gender or "unknown",
                    concerns=data.primary_concerns,
                    completeness=session.completeness,
                    extracted_data={
                        "child_name": data.child_name,
                        "age": data.age,
                        "primary_concerns": data.primary_concerns,
                        "concern_details": data.concern_details,
                        "strengths": data.strengths,
                        "developmental_history": data.developmental_history,
                        "family_context": data.family_context,
                        "daily_routines": data.daily_routines,
                        "parent_goals": data.parent_goals
                    }
                )
            else:
                # For more capable models: can use comprehensive prompt or dynamic prompt
                # Dynamic prompt works for all models
                base_prompt = build_dynamic_interview_prompt(
                    child_name=data.child_name or "unknown",
                    age=str(data.age) if data.age else "unknown",
                    gender=data.gender or "unknown",
                    concerns=data.primary_concerns,
                    completeness=session.completeness,
                    extracted_data={
                        "child_name": data.child_name,
                        "age": data.age,
                        "primary_concerns": data.primary_concerns,
                        "concern_details": data.concern_details,
                        "strengths": data.strengths,
                        "developmental_history": data.developmental_history,
                        "family_context": data.family_context,
                        "daily_routines": data.daily_routines,
                        "parent_goals": data.parent_goals
                    }
                )

        # Add prerequisite context if action was detected
        if prerequisite_check:
            if prerequisite_check.feasible:
                # Action IS possible - let LLM know they can facilitate it
                base_prompt += f"""

## ⚠️ IMPORTANT: User Action Request

The user wants to: **{prerequisite_check.action.value}**

✅ This action IS currently possible! The prerequisites are met.

Your response should:
1. Acknowledge their request positively
2. Help them with what they want
3. If interview not fully complete and action is view_report: Ask if there's anything else they want to share first

Example: "בהחלט! יש לי מספיק מידע כדי להתחיל. לפני שאסכם - יש עוד משהו חשוב שלא דיברנו עליו?"
"""
            else:
                # Action is NOT possible yet - explain warmly
                base_prompt += f"""

## ⚠️ IMPORTANT: User Action Request (Not Yet Possible)

The user wants to: **{prerequisite_check.action.value}**

❌ This action is NOT yet possible. Missing: {prerequisite_check.missing_prerequisites}

Your response should:
1. Use this explanation (personalized for them):
   "{prerequisite_check.explanation_to_user}"

2. Then guide back to completing what's needed
3. Be warm and encouraging - never make them feel blocked

The explanation above is already in Hebrew and personalized - USE IT or adapt it naturally.
"""

        # Add injected knowledge if information request detected
        if injected_knowledge:
            base_prompt += f"\n\n{injected_knowledge}"

        system_prompt = base_prompt

        # 6. Build conversation messages
        messages = [Message(role="system", content=system_prompt)]

        # Add recent conversation history (last 10 turns)
        history = self.interview_service.get_conversation_history(
            family_id,
            last_n=20  # Last 10 exchanges (user + assistant)
        )

        for turn in history:
            messages.append(Message(
                role=turn["role"],
                content=turn["content"]
            ))

        # Add current user message
        messages.append(Message(role="user", content=user_message))

        # 7. Call LLM - TWO SEPARATE CALLS to ensure we always get text
        #
        # CRITICAL: Gemini returns empty text when functions are provided.
        # Solution: Split into two calls:
        #   Call 1 (Conversation): Get natural Hebrew response WITHOUT functions
        #   Call 2 (Extraction): Extract structured data from the conversation
        #
        # This ensures parents always see a response, and data extraction happens separately.

        try:
            # CALL 1: Get conversational response (NO functions)
            # This ensures we ALWAYS get Hebrew text back
            llm_response = await self.llm.chat(
                messages=messages,
                functions=None,  # ← NO FUNCTIONS = Always get text
                temperature=temperature,
                max_tokens=2000
            )

            logger.info(
                f"Conversation response: {len(llm_response.content)} chars"
            )

            # Ensure we got a response
            if not llm_response.content.strip():
                logger.error("❌ LLM returned empty response even without functions!")
                llm_response.content = "סליחה, יש לי בעיה טכנית. בואי ננסה שוב."

            # CALL 2: Extract structured data from conversation
            # Create dedicated extraction context with current state
            session = self.interview_service.get_or_create_session(family_id)
            current_data = session.extracted_data

            extraction_system = f"""You are a data extraction assistant. Extract structured information from this conversation turn.

**Current data summary (for context):**
- Child: {current_data.child_name or 'unknown'}, {current_data.age or '?'} years, {current_data.gender or 'unknown'}
- Concerns so far: {current_data.primary_concerns or 'none yet'}
- Details collected: {len(current_data.concern_details or '')} characters
- Completeness: {session.completeness:.0%}

**Your job in this turn:**
Extract EVERYTHING the parent shares - even small details add up!

**CRITICAL - Concern Details:**
If parent describes concerns, extract rich details to concern_details field:
- What exactly happens? (specific behaviors/examples)
- When does it occur? (frequency, situations)
- Where? (home, school, everywhere)
- Impact on daily life?
- How long has this been happening?

**Extract:**
- Basic info (name, age, gender) - if mentioned
- Primary concerns (categories like 'speech', 'social', etc.)
- concern_details - ANY descriptions, examples, or elaborations about concerns
- strengths - interests, what child enjoys, good at
- developmental_history - milestones, pregnancy, birth, medical history
- family_context - siblings, family history, educational setting
- daily_routines - typical day, behaviors, patterns
- parent_goals - what they hope to improve

Call extract_interview_data with whatever is relevant from this turn. Every bit of information helps!"""

            extraction_messages = [
                Message(role="system", content=extraction_system),
                Message(role="user", content=f"Parent: {user_message}"),
                Message(role="assistant", content=f"Response: {llm_response.content}"),
                Message(role="user", content="Extract all relevant data from this conversation turn.")
            ]

            extraction_response = await self.llm.chat(
                messages=extraction_messages,
                functions=functions,  # ← NOW with functions for extraction
                temperature=0.1,  # Very low temp for deterministic extraction
                max_tokens=500
            )

            # Use ONLY function calls from extraction response
            # CRITICAL: Do NOT append extraction_response.content to llm_response.content
            # The extraction content is just for the model, not for the user
            llm_response.function_calls = extraction_response.function_calls

            logger.info(
                f"Extraction found: {len(extraction_response.function_calls)} function calls"
            )

            # Debug: Log if extraction returned unexpected text
            if extraction_response.content and extraction_response.content.strip():
                logger.debug(f"Extraction response text (not shown to user): {extraction_response.content[:100]}")

        except Exception as e:
            logger.error(f"LLM call failed: {e}", exc_info=True)
            return {
                "response": "מצטערת, נתקלתי בבעיה טכנית. בואי ננסה שוב.",
                "function_calls": [],
                "completeness": session.completeness * 100,
                "extracted_data": {},
                "context_cards": [],
                "error": str(e)
            }

        # 5. Process function calls
        extraction_summary = {}
        action_requested = None
        completeness_check = None

        for func_call in llm_response.function_calls:
            if func_call.name == "extract_interview_data":
                # Log what's being extracted BEFORE update
                logger.info(f"📝 EXTRACTION ATTEMPT: {list(func_call.arguments.keys())}")
                for key, value in func_call.arguments.items():
                    if value:  # Only log non-empty values
                        value_preview = str(value)[:100] if isinstance(value, str) else value
                        logger.info(f"   - {key}: {value_preview}")

                # Update extracted data
                # Note: If LLM doesn't get the name, it will ask naturally in the conversation
                updated_data = self.interview_service.update_extracted_data(
                    family_id,
                    func_call.arguments
                )
                extraction_summary = func_call.arguments

                # Get current completeness and show what was updated
                session = self.interview_service.get_or_create_session(family_id)
                logger.info(f"✅ DATA UPDATED - Completeness: {session.completeness:.1%}")
                logger.info(f"   - Extraction count: {updated_data.extraction_count}")
                logger.info(f"   - Current data summary:")
                logger.info(f"     * Basic: name={bool(updated_data.child_name)}, age={bool(updated_data.age)}, gender={updated_data.gender}")
                logger.info(f"     * Concerns: {len(updated_data.primary_concerns)} items = {updated_data.primary_concerns}")
                logger.info(f"     * Concern details: {len(updated_data.concern_details or '')} chars")
                logger.info(f"     * Strengths: {len(updated_data.strengths or '')} chars")
                logger.info(f"     * Dev history: {len(updated_data.developmental_history or '')} chars")
                logger.info(f"     * Family context: {len(updated_data.family_context or '')} chars")
                logger.info(f"     * Daily routines: {len(updated_data.daily_routines or '')} chars")
                logger.info(f"     * Parent goals: {len(updated_data.parent_goals or '')} chars")

            elif func_call.name == "user_wants_action":
                action_requested = func_call.arguments.get("action")
                logger.info(f"User wants action: {action_requested}")

            elif func_call.name == "check_interview_completeness":
                completeness_check = func_call.arguments
                logger.info(f"Completeness check: {completeness_check}")

        # 6. Save conversation turn
        self.interview_service.add_conversation_turn(
            family_id,
            role="user",
            content=user_message
        )
        self.interview_service.add_conversation_turn(
            family_id,
            role="assistant",
            content=llm_response.content
        )

        # 7. Get updated session state
        session = self.interview_service.get_or_create_session(family_id)
        completeness_pct = session.completeness * 100

        # 8. Generate context cards based on state
        context_cards = self._generate_context_cards(
            family_id,
            session.completeness,
            action_requested,
            completeness_check
        )

        # 9. Check if video guidelines should be generated
        if (session.completeness >= 0.80 and
            not session.video_guidelines_generated and
            completeness_check and
            completeness_check.get("ready_to_complete")):

            # Mark as generated (actual generation would happen here)
            self.interview_service.mark_video_guidelines_generated(family_id)

            # Add video upload card
            context_cards.append({
                "title": "הנחיות צילום מוכנות",
                "subtitle": "מותאמות במיוחד עבור הצרכים שסיפרת לי",
                "icon": "video",
                "status": "new",
                "action": "view_video_guidelines"
            })

        # 10. Return comprehensive response
        return {
            "response": llm_response.content,
            "function_calls": [
                {"name": fc.name, "arguments": fc.arguments}
                for fc in llm_response.function_calls
            ],
            "completeness": completeness_pct,
            "extracted_data": extraction_summary,
            "context_cards": context_cards,
            "stats": self.interview_service.get_session_stats(family_id)
        }

    def _generate_context_cards(
        self,
        family_id: str,
        completeness: float,
        action_requested: Optional[str],
        completeness_check: Optional[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Generate context cards based on interview state

        Cards show current status and available actions
        """
        cards = []
        session = self.interview_service.get_or_create_session(family_id)
        data = session.extracted_data

        # Interview progress card (always shown)
        progress_status = "pending" if completeness < 0.5 else "processing" if completeness < 0.8 else "completed"
        cards.append({
            "title": "שיחת ההיכרות",
            "subtitle": f"התקדמות: {completeness:.0%}",
            "icon": "message-circle",
            "status": progress_status,
            "progress": completeness * 100
        })

        # Child profile card (if we have basic info)
        if data.child_name and data.age:
            # Build subtitle - don't show "0 תחומי התפתחות"
            if data.primary_concerns:
                concerns_count = len(data.primary_concerns)
                concerns_text = "תחום התפתחות אחד" if concerns_count == 1 else f"{concerns_count} תחומי התפתחות"
                subtitle = f"גיל {data.age}, {concerns_text}"
            else:
                # No concerns yet - just show age
                subtitle = f"גיל {data.age}"

            cards.append({
                "title": f"פרופיל: {data.child_name}",
                "subtitle": subtitle,
                "icon": "user",
                "status": "active"
            })

        # Concerns card (if mentioned)
        if data.primary_concerns:
            concerns_hebrew = self._translate_concerns(data.primary_concerns)
            cards.append({
                "title": "נושאים שעלו",
                "subtitle": ", ".join(concerns_hebrew[:3]),
                "icon": "alert-circle",
                "status": "active"
            })

        # Video guidelines card (if ready)
        if completeness >= 0.80:
            cards.append({
                "title": "העלאת סרטון",
                "subtitle": "מוכן לשלב הבא",
                "icon": "video",
                "status": "action",
                "action": "upload_video"
            })

        # Urgent flags card (if any)
        if data.urgent_flags:
            cards.append({
                "title": "דורש תשומת לב",
                "subtitle": "נושאים שחשוב לטפל בהם",
                "icon": "alert-triangle",
                "status": "urgent"
            })

        return cards

    def _translate_concerns(self, concerns: List[str]) -> List[str]:
        """Translate concern categories to Hebrew"""
        translations = {
            "speech": "דיבור",
            "social": "חברתי",
            "attention": "קשב",
            "motor": "מוטורי",
            "sensory": "חושי",
            "emotional": "רגשי",
            "behavioral": "התנהגות",
            "learning": "למידה",
            "sleep": "שינה",
            "eating": "אכילה",
            "other": "אחר"
        }
        return [translations.get(c, c) for c in concerns]

    def _generate_fallback_response(
        self,
        function_calls: List[Any],
        current_data: Any
    ) -> str:
        """
        Generate an appropriate Hebrew response when LLM returns empty text

        This is a fallback for when the model makes function calls but doesn't
        include conversational text (a known issue with some models).

        Args:
            function_calls: The function calls made by the LLM
            current_data: Current extracted data

        Returns:
            Appropriate Hebrew response based on what was extracted
        """
        for func_call in function_calls:
            if func_call.name == "extract_interview_data":
                args = func_call.arguments

                # Check what was extracted and respond accordingly
                if args.get("child_name") and args.get("age"):
                    name = args.get("child_name")
                    age = args.get("age")
                    return f"נעים להכיר את {name}! ספרי לי עוד על {name} - במה הוא/היא אוהב/ת לעסוק?"

                elif args.get("child_name"):
                    name = args.get("child_name")
                    return f"נעים להכיר, {name}! בן כמה הוא/היא?"

                elif args.get("age"):
                    return "תודה! ספרי לי קצת עוד - מה מעניין אותך בעיקר בהתפתחות של הילד/ה?"

                elif args.get("primary_concerns") or args.get("concern_details"):
                    return "הבנתי. זה חשוב שדיברנו על זה. ספרי לי עוד - איך זה משפיע על היום יום?"

                elif args.get("strengths"):
                    return "נהדר! חשוב לי לדעת גם על החוזקות. מה עוד מתקדם יפה?"

                elif args.get("developmental_history"):
                    return "תודה על השיתוף. זה עוזר לי להבין את התמונה המלאה."

                # Generic response for any other extraction
                return "הבנתי, תודה! ספרי לי עוד קצת."

            elif func_call.name == "user_wants_action":
                action = func_call.arguments.get("action")

                # Get child reference for personalized responses
                child_ref = current_data.child_name if (current_data and current_data.child_name) else "הילד/ה"

                # Handle report request
                if action == "view_report":
                    return f"אני רוצה לעזור לך עם דוח מקיף! אבל כדי לייצר ממצאים משמעותיים אני צריכה להכיר את {child_ref} טוב יותר. בואי נמשיך עוד קצת והדוח יהיה הרבה יותר מותאם."

                # Handle video upload request
                elif action == "upload_video":
                    return "נהדר שאת מוכנה להעלות סרטון! קודם בואי נסיים את השיחה כדי שאוכל ליצור לך הנחיות צילום מותאמות אישית."

                # Handle video guidelines request
                elif action == "view_video_guidelines":
                    return "אני אכין לך הנחיות צילום מותאמות ברגע שנסיים את השיחה. בואי נמשיך עוד קצת."

                # Generic action response
                else:
                    return "הבנתי את הבקשה. בואי קודם נסיים את השיחה ואז נטפל בזה."

        # Default fallback if we can't determine what was extracted
        if current_data and current_data.child_name:
            return "הבנתי. ספרי לי עוד."
        else:
            return "שלום! אני כאן כדי להכיר את המשפחה שלך. ספרי לי על הילד/ה שלך."

    async def get_session_summary(self, family_id: str) -> Dict[str, Any]:
        """Get a summary of the current session state"""
        stats = self.interview_service.get_session_stats(family_id)
        session = self.interview_service.get_or_create_session(family_id)

        return {
            **stats,
            "context_summary": self.interview_service.get_context_summary(family_id),
            "recent_messages": self.interview_service.get_conversation_history(
                family_id,
                last_n=6
            )
        }


# Singleton instance
_conversation_service = None

def get_conversation_service() -> ConversationService:
    """Get singleton ConversationService instance"""
    global _conversation_service
    if _conversation_service is None:
        _conversation_service = ConversationService()
    return _conversation_service
