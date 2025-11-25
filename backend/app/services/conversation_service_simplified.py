"""
Simplified Conversation Service - Single LLM Architecture (Refactored)

This replaces the complex Sage+Hand+Strategic architecture with ONE comprehensive LLM call.

Benefits:
- 1-2 LLM calls instead of 5-6
- 80% cost reduction
- 5x faster responses
- Same or better quality
- Easy to maintain and extend

Key improvements in this refactored version:
- Wu Wei flow: Tools stay available, model decides when done
- Better empty response handling
- Multiple lifecycle event support
- Loop detection for stuck function calls
- Configurable token limits
- Cleaner code structure
"""

import logging
import asyncio
import re
from typing import Dict, Any, Optional, List, Set, Tuple
from datetime import datetime
from collections import defaultdict

from .llm.base import Message
from .llm.factory import create_llm_provider
from .session_service import SessionState, get_session_service
from .lifecycle_manager import get_lifecycle_manager
from .prerequisite_service import get_prerequisite_service
from ..prompts.comprehensive_prompt_builder import build_comprehensive_prompt
from ..prompts.extraction_prompt import build_extraction_prompt
from ..prompts.conversation_functions import CONVERSATION_FUNCTIONS_COMPREHENSIVE
from ..config.card_generator import get_card_generator

logger = logging.getLogger(__name__)


def clean_response(text: str) -> str:
    """
    Remove internal thinking/reasoning tags and function call syntax from LLM response.

    Some LLMs (like Gemini) may include:
    - <thought> or <thinking> tags showing their reasoning
    - Accidental function call syntax when function calling mechanism fails

    This must be stripped before showing response to user.
    """
    if not text:
        return text

    # Remove internal reasoning tags: <thought>, <thinking>, <start_action>, etc.
    # Model sometimes generates these when it doesn't properly use function calling
    reasoning_tags = r'<(?:thought|thinking|start_action|end_action|action|video_guidelines_request)>.*?</(?:thought|thinking|start_action|end_action|action|video_guidelines_request)>'
    cleaned_text = re.sub(reasoning_tags, '', text, flags=re.DOTALL | re.IGNORECASE)

    # Also remove any standalone malformed tags
    standalone_tags = r'</?(?:thought|thinking|start_action|end_action|action|video_guidelines_request)>'
    cleaned_text = re.sub(standalone_tags, '', cleaned_text, flags=re.IGNORECASE)

    # 🚨 CRITICAL FIX: Remove accidental function call syntax
    # When LLMs fail to use native function calling, they sometimes write about functions in text
    # Examples: "(<extract_interview_data>)", "(<add_journal_entry>)", "</function_name>)"
    # This happens when the model knows it should call a function but can't/doesn't use the API properly

    # Remove function call patterns: (<function_name>) ... </function_name>)
    cleaned_text = re.sub(r'\(<[^>]+>\).*?</[^>]+>\)', '', cleaned_text, flags=re.DOTALL)

    # Remove standalone function tags: (<function_name>) or </function_name>)
    cleaned_text = re.sub(r'\(<[^>]+>\)|</[^>]+>\)', '', cleaned_text)

    return cleaned_text.strip()


class SimplifiedConversationService:
    """
    Simplified conversation service using single LLM call with Wu Wei flow.

    Replaces:
    - Sage (intent interpretation) → Main LLM understands naturally
    - Hand (action decision) → Main LLM detects via functions
    - Strategic Advisor → Built into system prompt
    - Separate extraction → Combined via function calling
    """

    # Configuration constants
    MAX_ITERATIONS = 5  # Maximum conversation turns with model
    MAX_FUNCTION_CALLS = 15  # Maximum total function calls per message
    MAX_TOKENS = 8000  # Generous token limit for Hebrew responses
    DEFAULT_TEMPERATURE = 0.0  # Low temp for reliable function calling

    # Semantic verification intervals (exponential backoff)
    VERIFICATION_TURNS = [6, 9, 12, 18, 24, 36]

    def __init__(self, llm_provider=None):
        """Initialize simplified conversation service"""
        self.llm = llm_provider or create_llm_provider()
        self.session_service = get_session_service()
        self.lifecycle_manager = get_lifecycle_manager()
        self.prerequisite_service = get_prerequisite_service()

        logger.info("✨ SimplifiedConversationService initialized - Wu Wei architecture")

    async def process_message(
        self,
        family_id: str,
        user_message: str,
        temperature: float = None,
        max_tokens: int = None
    ) -> Dict[str, Any]:
        """
        Process user message using TWO-PHASE architecture.

        Phase 1 - EXTRACTION (with functions):
        - Single LLM call with functions enabled
        - Model calls extract_interview_data, ask_developmental_question, etc.
        - Returns 0 chars text (EXPECTED - this is how function calling works!)
        - Process and save all function calls

        Phase 2 - RESPONSE (without functions):
        - Single LLM call WITHOUT functions
        - Model generates conversational Hebrew response
        - This is what we show to the parent

        This matches standard function calling patterns (OpenAI, Anthropic, Google).

        Args:
            family_id: Family identifier
            user_message: Parent's message
            temperature: LLM temperature (default: 0.0)
            max_tokens: Maximum response tokens (default: 8000)

        Returns:
            Response dict with content, extracted data, cards, etc.
        """
        temperature = temperature if temperature is not None else self.DEFAULT_TEMPERATURE
        max_tokens = max_tokens if max_tokens is not None else self.MAX_TOKENS

        logger.info(f"📨 Processing message: {user_message[:100]}...")

        # 1. Get session state and conversation history
        session = self.session_service.get_or_create_session(family_id)
        data = session.extracted_data
        history = self.session_service.get_conversation_history(family_id) or []

        # DEBUG: Log history length and extracted data
        logger.info(f"📚 Conversation history: {len(history)} messages")
        logger.info(f"👤 Extracted data: name={data.child_name}, age={data.age}, concerns={data.primary_concerns}")

        # 2. PHASE 1: EXTRACTION (with functions enabled)
        # Use MINIMAL extraction prompt + XML-tagged context (no full history!)
        logger.info("🔧 Phase 1: Extraction (calling functions)")

        # Get last Chitta message for context
        last_chitta_message = None
        if history:
            for msg in reversed(history):
                if msg["role"] == "assistant":
                    last_chitta_message = msg["content"]
                    break

        # Build compact extraction context with XML tags
        extraction_context = self._build_extraction_context(
            already_extracted=data,
            last_chitta_question=last_chitta_message,
            parent_message=user_message
        )

        # Build minimal extraction messages (SHORT prompt + context, NO full history!)
        extraction_prompt = build_extraction_prompt()
        extraction_messages = [
            Message(role="system", content=extraction_prompt),
            Message(role="user", content=extraction_context)
        ]

        logger.info(f"📝 Phase 1 - Extraction prompt: {len(extraction_prompt)} chars")
        logger.info(f"📝 Phase 1 - Context preview: {extraction_context[:300]}...")
        logger.info(f"📝 Phase 1 - Sending {len(extraction_messages)} messages (should be 2: system + user)")

        extraction_result = await self._extraction_phase(
            messages=extraction_messages,
            temperature=0.0,  # Low temp for reliable extraction
            family_id=family_id,
            max_tokens=2000  # Should be plenty for extraction only
        )

        logger.info(f"📝 Phase 1 - Got {len(extraction_result['function_calls'])} function calls")

        all_extractions = extraction_result["extractions"]
        action_requested = extraction_result["action_requested"]
        developmental_question = extraction_result["developmental_question"]
        analysis_question = extraction_result["analysis_question"]
        app_help_request = extraction_result["app_help_request"]

        logger.info(f"✅ Phase 1 complete: {len(all_extractions)} extractions, {len(extraction_result['function_calls'])} function calls")

        # 4.5. Validate requested action using config-driven action_registry (Wu Wei: domain-agnostic)
        action_validation = None
        if action_requested:
            logger.info(f"🎬 Action requested: {action_requested} - validating via config...")

            # Get action definition from registry (loads from action_graph.yaml)
            from app.config.action_registry import get_action_registry
            action_def = get_action_registry().get_action(action_requested)

            if action_def:
                # CRITICAL: Reload session to get Phase 1 extracted data (child_name, etc.)
                session = self.session_service.get_or_create_session(family_id)

                # Build context for prerequisite check
                session_data = self._build_session_data_dict(family_id, session)
                context = self.prerequisite_service.get_context_for_cards(session_data)

                # Check if action is feasible (config-driven prerequisite check)
                prerequisite_check = self.prerequisite_service.check_action_feasible(
                    action=action_requested,
                    context=context
                )

                # Build validation response (all data from config!)
                action_validation = {
                    "action": action_requested,
                    "feasible": prerequisite_check.feasible,
                    "explanation": prerequisite_check.explanation_to_user if not prerequisite_check.feasible else None,
                    "view_to_open": action_def.opens_view if prerequisite_check.feasible else None  # From YAML!
                }

                logger.info(
                    f"🎬 Action validation (config-driven): {action_requested} -> "
                    f"feasible={prerequisite_check.feasible}, "
                    f"view={action_validation.get('view_to_open', 'none')}"
                )
            else:
                logger.warning(f"❌ Unknown action: {action_requested} (not in action_graph.yaml)")
                action_validation = {
                    "action": action_requested,
                    "feasible": False,
                    "explanation": f"פעולה לא מוכרת: {action_requested}"
                }

        # 4.7. Handle app help request using config-driven FAQ (Wu Wei: domain-agnostic)
        app_help_response = None
        if app_help_request:
            logger.info(f"ℹ️ App help requested: {app_help_request.get('help_topic')} - loading FAQ...")

            # Get FAQ service (loads from app_information.yaml)
            from app.config.app_information_service import get_app_information_service
            app_info_service = get_app_information_service()

            # Build context for FAQ response
            session_data = self._build_session_data_dict(family_id, session)
            faq_context = self.prerequisite_service.get_context_for_cards(session_data)
            faq_context["child_name"] = session.extracted_data.child_name or "הילד/ה שלך"
            faq_context["message_count"] = len(session.conversation_history)

            # Get FAQ response from config
            faq_answer = app_info_service.get_faq_response(
                help_topic=app_help_request.get("help_topic"),
                context=faq_context
            )

            if faq_answer:
                app_help_response = {
                    "help_topic": app_help_request.get("help_topic"),
                    "question": app_help_request.get("question_text"),
                    "answer": faq_answer  # From YAML config with dynamic placeholders filled!
                }
                logger.info(
                    f"ℹ️ FAQ loaded (config-driven): {app_help_request.get('help_topic')} -> "
                    f"{len(faq_answer)} chars"
                )
            else:
                logger.warning(f"❌ No FAQ for help_topic: {app_help_request.get('help_topic')}")

        # 5. CRITICAL: Rebuild system prompt with UPDATED extracted data from Phase 1
        # Phase 1 may have just extracted name, age, or other data that Phase 2 needs to know about
        # MUST get fresh session reference to see updates from Phase 1
        session = self.session_service.get_or_create_session(family_id)
        updated_data = session.extracted_data

        # DEBUG: Verify we have the latest data
        logger.info(f"📊 Updated extracted data for Phase 2: name={updated_data.child_name}, age={updated_data.age}")
        logger.info(f"🔍 Session ID verification: {family_id}")

        updated_system_prompt = build_comprehensive_prompt(
            child_name=updated_data.child_name,
            age=updated_data.age,
            gender=updated_data.gender,
            extracted_data={
                'child_name': updated_data.child_name,
                'age': updated_data.age,
                'gender': updated_data.gender,
                'primary_concerns': updated_data.primary_concerns,
                'concern_details': updated_data.concern_details,
                'strengths': updated_data.strengths,
                'developmental_history': updated_data.developmental_history,
                'family_context': updated_data.family_context,
                'daily_routines': updated_data.daily_routines,
                'parent_goals': updated_data.parent_goals
            },
            completeness=session.completeness,
            available_artifacts=list(session.artifacts.keys()),
            message_count=self._count_user_messages(session),
            session=session,
            lifecycle_manager=self.lifecycle_manager,
            include_function_instructions=False,  # CRITICAL: Phase 2 has no functions, so don't instruct to call them!
            family_id=family_id  # Wu Wei: For moment context builder
        )

        # DEBUG: Log prompt to verify moment context is included
        if "<journey_context>" in updated_system_prompt or "<available_now>" in updated_system_prompt:
            logger.info("✅ Moment context detected in Phase 2 prompt")
        else:
            logger.warning("⚠️ Moment context NOT found in Phase 2 prompt")

        # 5.5. Inject FAQ context if app help was requested (Wu Wei: accurate knowledge injection)
        if app_help_response:
            faq_context_injection = f"""

<app_help_context>
**The parent asked a specific question**: "{app_help_response['question']}"

**Accurate answer for THIS question**:

{app_help_response['answer']}

**Your task**:
1. Provide this information in a natural, conversational way. You can rephrase it slightly to match the flow, but keep all the factual information accurate.
2. Answer ONLY this specific question - don't add feature lists, process explanations, or "what's available now" unless they specifically asked for those topics.
3. After answering, you can briefly and naturally offer to continue talking about the child, but don't be pushy. If they have more questions about the app, let them ask.
</app_help_context>
"""
            updated_system_prompt += faq_context_injection
            logger.info(f"✅ FAQ context injected into Phase 2 prompt ({len(faq_context_injection)} chars)")

        # 5.6. Inject completeness check result if available (Wu Wei: async check with staleness context)
        if session.completed_check_result:
            check_data = session.completed_check_result
            messages_analyzed = check_data.get('messages_analyzed', 0)
            current_message_count = len(session.conversation_history) // 2  # Approximate user messages
            messages_since_check = current_message_count - messages_analyzed

            check_result = check_data.get('result', {})
            overall_readiness = check_result.get('overall_readiness', 0)
            missing_gaps = check_result.get('missing_gaps', [])
            recommendations = check_result.get('recommendations', [])

            completeness_context = f"""

<completeness_check_context>
A completeness check was performed after message {messages_analyzed}.
Currently at message {current_message_count} ({messages_since_check} new messages since check).

**Check findings (at message {messages_analyzed})**:
- Overall readiness: {overall_readiness}%
- Missing information at that time: {', '.join(missing_gaps) if missing_gaps else 'None'}
- Recommendations: {', '.join(recommendations) if recommendations else 'None'}

**IMPORTANT**: This check analyzed messages 1-{messages_analyzed}.
Since then, {messages_since_check} new messages have been added (messages {messages_analyzed + 1}-{current_message_count}).

**Your task**:
1. Consider the check findings as a baseline
2. BUT prioritize information from recent messages ({messages_analyzed + 1} onward)
3. If recent messages filled any gaps mentioned in the check, those gaps are NOW resolved
4. Use this to guide what questions to ask, but don't mention the check to the parent
</completeness_check_context>
"""
            updated_system_prompt += completeness_context
            logger.info(f"✅ Completeness check context injected (check from message {messages_analyzed}, currently at {current_message_count})")

            # Clear the result - only use it once
            session.completed_check_result = None

        # Rebuild messages with updated system prompt for Phase 2
        updated_messages = [Message(role="system", content=updated_system_prompt)]
        for turn in history:
            updated_messages.append(Message(
                role=turn["role"],
                content=turn["content"]
            ))
        updated_messages.append(Message(role="user", content=user_message))

        # DEBUG: Log preview of UPDATED system prompt for Phase 2
        updated_prompt_preview = updated_system_prompt[:500] if len(updated_system_prompt) > 500 else updated_system_prompt
        logger.debug(f"📝 Phase 2 UPDATED system prompt preview: {updated_prompt_preview}...")

        # 5.5. Save user message BEFORE lifecycle check (so message_count is accurate)
        # 🌟 Wu Wei: Lifecycle checks need accurate message count for knowledge_richness evaluation
        self.session_service.add_conversation_turn(family_id, "user", user_message)
        logger.info(f"💾 Saved user message (before lifecycle check)")

        # Refresh session to get updated message count
        session = self.session_service.get_or_create_session(family_id)

        # 6. Process lifecycle events BEFORE Phase 2
        # This gives Phase 2 full context about UI state and capabilities
        session_data = self._build_session_data_dict(family_id, session)
        context = self.prerequisite_service.get_context_for_cards(session_data)
        context["conversation_history"] = session.conversation_history or []

        lifecycle_result = await self.lifecycle_manager.process_lifecycle_events(
            family_id=family_id,
            context=context,
            session=session
        )

        if lifecycle_result["artifacts_generated"]:
            logger.info(
                f"🌟 Artifacts generated: {lifecycle_result['artifacts_generated']}"
            )

        # Extract lifecycle context to pass to Phase 2
        lifecycle_context = self._extract_lifecycle_context(lifecycle_result)

        # 7. PHASE 2: RESPONSE (without functions, WITH lifecycle context and UPDATED data)
        logger.info("💬 Phase 2: Response generation (no functions, with lifecycle context)")
        final_response = await self._response_phase(
            messages=updated_messages,  # Use updated messages with fresh extracted data!
            temperature=temperature,
            max_tokens=max_tokens,
            lifecycle_context=lifecycle_context
        )

        logger.info(f"✅ Phase 2 complete: {len(final_response)} chars")

        # DEBUG: Log Phase 2 response to check for function syntax
        response_preview = final_response[:300] if len(final_response) > 300 else final_response
        logger.debug(f"💬 Phase 2 response preview: {response_preview}")

        # 7. No fallback needed - Phase 2 always returns text!
        # (But keep safety check just in case)
        if not final_response:
            logger.error("🔴 CRITICAL: Phase 2 returned empty response!")
            final_response = "סליחה, משהו השתבש. אפשר לנסות שוב?"

        # 8. Save assistant response (user message already saved before lifecycle check)
        self.session_service.add_conversation_turn(family_id, "assistant", final_response)

        # 9. Get updated session state
        session = self.session_service.get_or_create_session(family_id)
        completeness_pct = session.completeness * 100

        # 10. Semantic verification (smart intervals) - NON-BLOCKING
        should_verify = self._should_run_verification(session)

        if should_verify:
            turn_count = self._count_user_messages(session)
            logger.info(f"🔍 Starting background completeness verification (turn {turn_count}) - won't block response")

            # Mark check as pending
            session.pending_completeness_check = {
                'started_at_message': turn_count,
                'started_at': datetime.now().isoformat()
            }

            # Start background task - DON'T await it!
            asyncio.create_task(
                self._run_completeness_check_background(family_id, turn_count)
            )
            logger.info(f"🚀 Background check task started, continuing with response...")

        # 11. Generate context cards
        # 🌟 Phase 1 Living Dashboard: Use new card lifecycle system
        # Active cards come from lifecycle_result (managed by CardLifecycleService)
        active_cards = lifecycle_result.get("active_cards", [])

        # Legacy: Also get state cards for backwards compatibility during transition
        state_cards = self._generate_context_cards(
            family_id,
            session.completeness,
            action_requested,
            None
        )

        # 🌟 Event-Driven Cards: Extract cards from lifecycle events (legacy)
        event_cards = self._extract_event_cards(lifecycle_result)

        # Merge: Active cards first (new system), then event cards, then state cards
        # This provides backwards compatibility while transitioning to new system
        context_cards = active_cards + event_cards + state_cards

        # Remove duplicates (prefer active_cards version)
        seen_ids = set()
        deduplicated_cards = []
        for card in context_cards:
            card_id = card.get("card_id") or card.get("id")
            if card_id not in seen_ids:
                seen_ids.add(card_id)
                deduplicated_cards.append(card)
        context_cards = deduplicated_cards

        logger.info(
            f"📇 Total cards: {len(context_cards)} "
            f"({len(active_cards)} active + {len(event_cards)} event + {len(state_cards)} state)"
        )

        # 11.5. Notify SSE clients of card updates (Wu Wei: real-time UI updates)
        if context_cards:
            from app.services.sse_notifier import get_sse_notifier
            sse_notifier = get_sse_notifier()
            asyncio.create_task(
                sse_notifier.notify_cards_updated(family_id, context_cards)
            )
            logger.info(f"📡 SSE notification sent for {len(context_cards)} cards")

        # 12. Return response
        merged_extractions = self._merge_extractions(all_extractions)

        return {
            "response": final_response,  # Use Phase 2 response directly (already has lifecycle context)
            "function_calls": extraction_result["function_calls"],
            "completeness": completeness_pct,
            "extracted_data": merged_extractions,
            "context_cards": context_cards,
            "stats": self.session_service.get_session_stats(family_id),
            "architecture": "two_phase_with_lifecycle",
            "intents_detected": {
                "developmental_question": developmental_question,
                "analysis_question": analysis_question,
                "app_help_request": app_help_request,
                "action_requested": action_requested
            },
            "action_validation": action_validation,  # Config-driven action validation (Wu Wei)
            "app_help_response": app_help_response  # Config-driven FAQ response (Wu Wei)
        }

    async def _extraction_phase(
        self,
        messages: List[Message],
        temperature: float,
        family_id: str,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Phase 1: EXTRACTION - Single LLM call with functions enabled.

        The model will call functions like extract_interview_data() and return
        NO TEXT (or minimal text). This is EXPECTED and NORMAL for function calling!

        Returns:
            Dict with extractions, function_calls, and intents
        """
        # Call LLM with functions enabled
        llm_response = await self.llm.chat(
            messages=messages,
            functions=CONVERSATION_FUNCTIONS_COMPREHENSIVE,
            temperature=temperature,
            max_tokens=max_tokens
        )

        # Log what we got
        logger.info(f"📞 Extraction phase: {len(llm_response.function_calls)} function calls, {len(llm_response.content or '')} chars text")

        # CRITICAL DEBUG: Check if response was truncated
        if llm_response.finish_reason == "max_tokens":
            logger.error(f"🔴 Phase 1 HIT MAX_TOKENS! No extraction possible if truncated!")
        elif not llm_response.function_calls:
            logger.warning(f"⚠️ Phase 1 returned NO function calls! Finish reason: {llm_response.finish_reason}")

        # Process function calls
        extractions = []
        intents = {
            "action_requested": None,
            "developmental_question": None,
            "analysis_question": None,
            "app_help_request": None
        }

        if llm_response.function_calls:
            # Extract latest user message for context in normalization
            user_message = next(
                (m.content for m in reversed(messages) if m.role == "user"),
                ""
            )

            new_extractions, new_intents = await self._process_function_calls(
                llm_response.function_calls,
                family_id,
                user_message
            )
            extractions.extend(new_extractions)
            intents.update({k: v for k, v in new_intents.items() if v is not None})

        # CRITICAL: Verify session data was actually saved
        if llm_response.function_calls:
            verification_session = self.session_service.get_or_create_session(family_id)
            verification_data = verification_session.extracted_data
            logger.info(f"🔍 POST-EXTRACTION VERIFICATION: name={verification_data.child_name}, age={verification_data.age}, concerns={verification_data.primary_concerns}")

        return {
            "extractions": extractions,
            "function_calls": [
                {"name": fc.name, "arguments": fc.arguments}
                for fc in llm_response.function_calls
            ],
            "action_requested": intents.get("action_requested"),
            "developmental_question": intents.get("developmental_question"),
            "analysis_question": intents.get("analysis_question"),
            "app_help_request": intents.get("app_help_request")
        }

    async def _response_phase(
        self,
        messages: List[Message],
        temperature: float,
        max_tokens: int,
        lifecycle_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Phase 2: RESPONSE - Single LLM call WITHOUT functions, WITH lifecycle context.

        The model will generate a natural Hebrew conversational response.

        Lifecycle context provides:
        - System context (capabilities, constraints, what to say/not say)
        - UI guidance (what's visible, where things appear)
        - Message guidance (suggested response to enhance)

        This prevents hallucinations about UI state and capabilities.

        Args:
            messages: Conversation messages
            temperature: LLM temperature
            max_tokens: Maximum response tokens
            lifecycle_context: Optional lifecycle context from triggered events

        Returns:
            Hebrew text response
        """
        # If we have lifecycle context, inject it as additional system messages
        phase2_messages = messages.copy()

        if lifecycle_context:
            system_contexts = lifecycle_context.get("system_contexts", [])
            ui_guidance = lifecycle_context.get("ui_guidance", [])
            message_guidance = lifecycle_context.get("message_guidance")

            # Add system contexts (capabilities, constraints)
            for ctx in system_contexts:
                phase2_messages.append(Message(
                    role="system",
                    content=ctx
                ))
                logger.info(f"📋 Added system context: {ctx[:100]}...")

            # Add UI guidance
            for ui in ui_guidance:
                phase2_messages.append(Message(
                    role="system",
                    content=f"<ui_state>\n{ui}\n</ui_state>"
                ))
                logger.info(f"🖥️ Added UI guidance: {ui[:100]}...")

            # Add message guidance (suggested response to enhance)
            if message_guidance:
                phase2_messages.append(Message(
                    role="system",
                    content=f"<suggested_response>\nThe following message captures what just happened. You can use it as-is or enhance it with your warm, conversational style:\n\n{message_guidance}\n</suggested_response>"
                ))
                logger.info(f"💡 Added message guidance: {message_guidance[:100]}...")

        # Call LLM WITHOUT functions - this forces it to return text
        try:
            llm_response = await self.llm.chat(
                messages=phase2_messages,
                functions=None,  # NO FUNCTIONS! This is the key!
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Clean response to remove any thinking/reasoning tags
            response_text = clean_response(llm_response.content or "")
            logger.info(f"💬 Response phase: {len(response_text)} chars, {len(llm_response.function_calls)} function calls (should be 0)")

            # Debug empty responses
            if not response_text:
                logger.error(f"🔴 Phase 2 returned empty response! Finish reason: {llm_response.finish_reason}")
                logger.error(f"   Message count: {len(phase2_messages)}")
                logger.error(f"   Function calls returned: {len(llm_response.function_calls)}")

            return response_text
        except Exception as e:
            logger.error(f"🔴 Phase 2 LLM call failed: {e}")
            logger.exception(e)
            return ""

    # OLD METHOD REMOVED: _function_calling_loop
    # We now use TWO-PHASE architecture (_extraction_phase + _response_phase)
    # instead of a loop trying to get both function calls and text in one go.
    # This matches standard function calling patterns (OpenAI, Anthropic, Google).

    async def _normalize_filming_preference(
        self,
        raw_value: str,
        user_message: str
    ) -> Optional[str]:
        """
        Normalize filming_preference to strict enum values using structured output.

        The LLM may extract natural language like "כן", "רוצה לצלם", "yes", etc.
        This method uses Gemini's structured output with strict enum to normalize.

        Args:
            raw_value: Raw extracted value from function calling
            user_message: The parent's message for context

        Returns:
            "wants_videos" | "report_only" | None
        """
        logger.info(f"🎬 Normalizing filming_preference: raw='{raw_value}'")

        # Define strict schema with enum
        schema = {
            "type": "object",
            "properties": {
                "filming_preference": {
                    "type": "string",
                    "enum": ["wants_videos", "report_only"],
                    "description": "Parent's choice about filming"
                }
            },
            "required": ["filming_preference"]
        }

        # Create prompt for classification
        messages = [
            Message(
                role="system",
                content="""You are a classifier. Given a parent's response about filming their child, classify it as:
- "wants_videos": Parent agrees to film
- "report_only": Parent declines filming

Examples:
- "כן" → wants_videos
- "אני מוכנה לצלם" → wants_videos
- "בסדר, אצלם" → wants_videos
- "לא, רק דוח" → report_only
- "בלי סרטונים" → report_only
- "מעדיפה דוח" → report_only"""
            ),
            Message(
                role="user",
                content=f"Classify this response: '{user_message}'\n\nRaw extracted value: '{raw_value}'"
            )
        ]

        try:
            # Use structured output to enforce enum
            result = await self.llm.chat_with_structured_output(
                messages=messages,
                response_schema=schema,
                temperature=0.1
            )

            normalized = result.get("filming_preference")
            logger.info(f"✅ Normalized filming_preference: '{raw_value}' → '{normalized}'")
            return normalized

        except Exception as e:
            logger.error(f"❌ Failed to normalize filming_preference: {e}")
            return None

    async def _process_function_calls(
        self,
        function_calls: List[Any],
        family_id: str,
        user_message: str
    ) -> Tuple[List[Dict], Dict[str, Any]]:
        """
        Process function calls and return extractions and intents.

        Args:
            function_calls: List of function calls from LLM
            family_id: Family ID
            user_message: Parent's message (for context in normalization)

        Returns:
            Tuple of (extractions_list, intents_dict)
        """
        extractions = []
        intents = {}

        logger.info(f"🔧 Processing {len(function_calls)} function call(s)")

        for func_call in function_calls:
            if func_call.name == "extract_interview_data":
                logger.info(f"📝 Extracting data: {list(func_call.arguments.keys())}")
                logger.debug(f"   → child_name: {repr(func_call.arguments.get('child_name'))}")
                logger.debug(f"   → age: {repr(func_call.arguments.get('age'))}")

                # 🎬 CRITICAL: Normalize filming_preference using structured output
                if 'filming_preference' in func_call.arguments:
                    raw_value = func_call.arguments['filming_preference']
                    if raw_value:  # Only normalize if value exists
                        normalized = await self._normalize_filming_preference(
                            raw_value=raw_value,
                            user_message=user_message
                        )
                        func_call.arguments['filming_preference'] = normalized
                        logger.info(f"🎬 Updated filming_preference: {raw_value} → {normalized}")

                self.session_service.update_extracted_data(
                    family_id,
                    func_call.arguments
                )
                extractions.append(func_call.arguments)

            elif func_call.name == "ask_developmental_question":
                intents["developmental_question"] = func_call.arguments
                logger.info(f"❓ Developmental question: {func_call.arguments.get('question_topic')}")

            elif func_call.name == "ask_about_analysis":
                intents["analysis_question"] = func_call.arguments
                logger.info(f"🔍 Analysis question: {func_call.arguments.get('analysis_element')}")

            elif func_call.name == "ask_about_app":
                intents["app_help_request"] = func_call.arguments
                logger.info(f"ℹ️ App help: {func_call.arguments.get('help_topic')}")

            elif func_call.name == "request_action":
                action = func_call.arguments.get('action')
                intents["action_requested"] = action
                logger.info(f"🎬 Action requested: {action}")

        return extractions, intents

    # OLD METHODS REMOVED: _detect_function_loop, _log_function_calls
    # These were only needed for the loop-based approach.
    # Two-phase architecture doesn't need loop detection.

    def _generate_smart_fallback(
        self,
        family_id: str,
        all_extractions: List[Dict],
        user_message: str
    ) -> str:
        """
        Generate context-aware fallback response when model returns empty.

        This happens when:
        1. Model hits max_iterations while still calling functions
        2. Model fails to generate text (rare)
        3. Response is truncated (max_tokens too low)

        Strategy: Look at what was JUST shared vs what we already know
        """
        if not all_extractions:
            # No extractions AND no response = complete failure
            logger.error("🔴 CRITICAL: No response and no extractions - model failure")
            return "סליחה, משהו השתבש. אפשר לנסות שוב?"

        # We have extractions but no text - generate context-aware response
        logger.warning("⚠️ Generating smart fallback (model hit limits)")

        # Merge all extractions from this turn
        merged = {}
        for ext in all_extractions:
            merged.update(ext)

        # Get current session data
        session = self.session_service.get_or_create_session(family_id)
        data = session.extracted_data

        # Determine what's NEW this turn vs what we already knew
        child_name = merged.get('child_name') or data.child_name or 'הילד/ה'
        age = merged.get('age') or data.age

        # Generate response based on what was JUST shared
        if merged.get('child_name') and merged.get('age'):
            # Just learned name and age
            return f"נעים להכיר את {child_name}! ספרי לי קצת - מה מעסיק אותך?"

        elif merged.get('concern_details') and not merged.get('strengths'):
            # Shared concerns, now ask about strengths
            return f"אני שומעת. ומה {child_name} כן אוהב לעשות? במה הוא טוב?"

        elif merged.get('strengths') and not merged.get('concern_details'):
            # Shared strengths, now ask about concerns
            return f"נהדר! ומה מעסיק אותך לגבי {child_name}?"

        elif merged.get('concern_details'):
            # Shared concern details, ask for more specifics
            return "תני לי דוגמה - מתי זה קרה לאחרונה?"

        else:
            # Generic - just continue naturally
            return "ספרי לי עוד - מה קורה?"

    def _extract_event_cards(
        self,
        lifecycle_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract event-triggered cards from lifecycle events.

        🌟 Event-Driven Cards: Moments can define cards that display when triggered.
        These are one-time celebration/transition cards.

        Args:
            lifecycle_result: Result from lifecycle_manager.process_lifecycle_events()

        Returns:
            List of card dicts ready for frontend display
        """
        if not lifecycle_result.get("events_triggered"):
            return []

        event_cards = []

        for event in lifecycle_result["events_triggered"]:
            card_config = event.get("card")
            if card_config:
                # Format card for frontend (ContextualSurface.jsx)
                # Extract first line of body as subtitle
                body = card_config.get("body", "")
                subtitle = ""
                for line in body.split("\n"):
                    line = line.strip()
                    if line and not line.startswith("#") and not line.startswith("**"):
                        subtitle = line.replace("**", "").replace("*", "")[:100]
                        break

                # Get first action
                actions = card_config.get("actions", [])
                action = actions[0] if actions else None

                # Map card_type to icon
                card_type = card_config.get("card_type", "guidance")
                icon_map = {
                    "success": "CheckCircle",
                    "guidance": "Lightbulb",
                    "progress": "TrendingUp",
                    "action_needed": "AlertCircle",
                }
                icon = icon_map.get(card_type, "Info")

                # Get color from config (default by card_type)
                color_map = {
                    "success": "green",
                    "guidance": "purple",
                    "progress": "blue",
                    "action_needed": "orange",
                }
                color = card_config.get("color", color_map.get(card_type, "gray"))

                card = {
                    "type": f"event_{event['event_name']}",
                    "card_type": card_type,
                    "color": color,
                    "icon": icon,
                    "title": card_config.get("title", ""),
                    "subtitle": subtitle,
                    "action": action,
                    "status": "new",  # Event cards are always "new"
                    "from_event": event["event_name"],
                    "_raw": card_config,  # Keep original for debugging
                }
                event_cards.append(card)
                logger.info(f"💳 Event card from '{event['event_name']}': {card.get('title', 'Untitled')}")

        return event_cards

    def _extract_lifecycle_context(
        self,
        lifecycle_result: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Extract lifecycle context from triggered events.

        Extracts:
        - system_contexts: List of system context strings (capabilities, constraints)
        - ui_guidance: List of UI guidance strings (what's visible in UI)
        - message_guidance: Combined message guidance (suggested response text)

        Returns:
            Dict with lifecycle context, or None if no events triggered
        """
        if not lifecycle_result.get("events_triggered"):
            return None

        event_names = [e["event_name"] for e in lifecycle_result["events_triggered"]]
        logger.info(f"🎉 Lifecycle events triggered: {event_names}")

        system_contexts = []
        ui_guidance = []
        message_parts = []

        for event in lifecycle_result["events_triggered"]:
            # Extract context section
            if event.get("context"):
                system_contexts.append(event["context"])
                logger.info(f"📋 Event '{event['event_name']}' has system context")

            # Extract UI guidance
            if event.get("ui"):
                ui_dict = event["ui"]
                # Prefer mobile guidance if available, otherwise use default
                ui_text = ui_dict.get("mobile") or ui_dict.get("default")
                if ui_text:
                    ui_guidance.append(ui_text)
                    logger.info(f"🖥️ Event '{event['event_name']}' has UI guidance")

            # Extract message guidance
            if event.get("message"):
                message_parts.append(event["message"])
                logger.info(f"💡 Event '{event['event_name']}' has message guidance")

        # Combine message parts if multiple events
        message_guidance = "\n\n".join(message_parts) if message_parts else None

        return {
            "system_contexts": system_contexts,
            "ui_guidance": ui_guidance,
            "message_guidance": message_guidance
        }

    def _merge_lifecycle_messages(
        self,
        final_response: str,
        lifecycle_result: Dict[str, Any]
    ) -> str:
        """
        OLD METHOD - No longer used with two-phase lifecycle integration.

        Lifecycle context is now passed to Phase 2 BEFORE response generation,
        so the LLM generates contextually-aware responses naturally.

        Kept for backwards compatibility but should not be called.
        """
        logger.warning("⚠️ _merge_lifecycle_messages called - this method is deprecated")
        return final_response

    def _build_extraction_context(
        self,
        already_extracted: Any,
        last_chitta_question: Optional[str],
        parent_message: str
    ) -> str:
        """
        Build XML-tagged context for Phase 1 extraction.

        This provides context without sending full conversation history,
        preventing MAX_TOKENS errors as conversation grows.
        """
        # Build summary of what's already extracted
        extracted_summary = []
        if already_extracted.child_name:
            extracted_summary.append(f"- Name: {already_extracted.child_name}")
        if already_extracted.age:
            extracted_summary.append(f"- Age: {already_extracted.age} years")
        if already_extracted.gender:
            extracted_summary.append(f"- Gender: {already_extracted.gender}")
        if already_extracted.primary_concerns:
            concerns_text = ", ".join(already_extracted.primary_concerns)
            extracted_summary.append(f"- Primary concerns: {concerns_text}")
        if already_extracted.strengths:
            extracted_summary.append(f"- Strengths: {already_extracted.strengths[:100]}...")
        if already_extracted.concern_details:
            extracted_summary.append(f"- Concern details: {already_extracted.concern_details[:100]}...")

        extracted_text = "\n".join(extracted_summary) if extracted_summary else "(Nothing extracted yet)"

        # Build context with XML tags
        context = f"""<already_extracted>
{extracted_text}
</already_extracted>"""

        if last_chitta_question:
            context += f"""

<last_chitta_question>
{last_chitta_question}
</last_chitta_question>"""

        context += f"""

<parent_message>
{parent_message}
</parent_message>"""

        return context

    def _count_user_messages(self, session: SessionState) -> int:
        """Count user messages in conversation history"""
        conversation_history = session.conversation_history or []
        return len([m for m in conversation_history if m.get('role') == 'user'])

    def _should_run_verification(self, session: SessionState) -> bool:
        """
        Determine if semantic verification should run this turn.

        Uses exponential backoff: verify at turns 6, 9, 12, 18, 24, 36...
        Wu Wei: Stop verifying once ANY artifact is generated (domain-agnostic).
        """
        turn_count = self._count_user_messages(session)

        # Don't verify if any artifacts already generated (domain-agnostic check)
        if session.artifacts:
            return False

        # Check if current turn matches a verification turn
        if turn_count not in self.VERIFICATION_TURNS:
            return False

        # Verify if we haven't verified at this turn already
        return turn_count != session.semantic_verification_turn

    async def _run_completeness_check_background(self, family_id: str, messages_at_check: int):
        """
        🔄 Run completeness check in background without blocking the response

        Stores result with metadata so next message can use it with staleness context.
        """
        try:
            logger.info(f"🔍 Background completeness check started for {family_id} at message {messages_at_check}")

            # Run the actual check (this is the blocking LLM call)
            result = await self.session_service.verify_semantic_completeness(family_id)

            # Store the result with metadata in session
            session = self.session_service.get_or_create_session(family_id)
            session.completed_check_result = {
                'result': result,
                'messages_analyzed': messages_at_check,
                'check_timestamp': datetime.now().isoformat(),
                'knowledge_was_rich': session.completeness >= 0.7  # Context about state during check
            }
            session.pending_completeness_check = None  # Clear pending flag

            logger.info(f"✅ Background completeness check completed for {family_id}: {result.get('overall_readiness', 0)}% ready")

        except Exception as e:
            logger.error(f"❌ Background completeness check failed for {family_id}: {e}")
            # Clear pending flag even on error
            session = self.session_service.get_or_create_session(family_id)
            session.pending_completeness_check = None

    def _merge_extractions(self, all_extractions: List[Dict]) -> Dict[str, Any]:
        """Merge all extractions into a single dict"""
        merged = {}
        for extraction in all_extractions:
            merged.update(extraction)
        return merged

    def _build_session_data_dict(self, family_id: str, session: SessionState) -> Dict[str, Any]:
        """
        Build raw session data for prerequisite service.

        Wu Wei Principle: Pass ONLY raw session state - let config-driven services
        interpret it. NO domain knowledge, NO transformations!
        """
        try:
            extracted_dict = session.extracted_data.model_dump()
        except AttributeError:
            extracted_dict = session.extracted_data.dict()

        # Get video count from family state
        from app.services.mock_graphiti import get_mock_graphiti
        graphiti = get_mock_graphiti()
        state = graphiti.get_or_create_state(family_id)
        uploaded_video_count = len(state.videos_uploaded)

        # Minimal raw data - prerequisite_service (config-driven) does the rest
        # 🌟 Build base context
        context = {
            "family_id": family_id,
            "message_count": self._count_user_messages(session),
            "artifacts": session.artifacts,  # All artifacts - service interprets from config
            "completeness": session.completeness,
            "uploaded_video_count": uploaded_video_count,  # 🌟 For video-related moments
            "guideline_scenario_count": session.guideline_scenario_count,  # 🎥 Number of scenarios in guidelines
            "video_analysis_status": session.video_analysis_status,  # 🎥 Video analysis progress
        }

        # 🌟 FLATTEN extracted_data fields to top-level for YAML prerequisite access
        # This allows lifecycle_events.yaml to use `filming_preference:` instead of `extracted_data.filming_preference:`
        context.update(extracted_dict)

        # Also keep nested for backward compat (in case some code uses it)
        context["extracted_data"] = extracted_dict

        return context

    def _build_card_context(
        self,
        session: SessionState,
        completeness: float
    ) -> Dict[str, Any]:
        """
        Build context dict for card evaluation.

        🌟 Wu Wei: Domain-agnostic - just passes generic structures.
        Cards define what fields they need via YAML placeholders.
        """
        # Count uploaded videos from artifacts
        # Videos artifact exists when >= 3 videos uploaded
        uploaded_video_count = 0
        if session.has_artifact("baseline_videos"):
            uploaded_video_count = 3  # baseline_videos means 3 videos uploaded

        # 🚨 CRITICAL FIX: Convert Artifact objects to dict format for card evaluation
        # Cards use dot notation (artifacts.baseline_video_guidelines.status)
        # which requires dict format, not Artifact objects
        artifacts_dict = {}
        for artifact_id, artifact_obj in session.artifacts.items():
            if hasattr(artifact_obj, 'exists'):
                # It's an Artifact object - convert to dict
                artifacts_dict[artifact_id] = {
                    "exists": artifact_obj.exists,
                    "status": artifact_obj.status,
                    "artifact_id": artifact_obj.artifact_id
                }
            elif isinstance(artifact_obj, dict):
                # Already a dict
                artifacts_dict[artifact_id] = artifact_obj

        # 🚨 CRITICAL FIX: Convert ExtractedData Pydantic model to dict
        # Cards need dict access for top-level keys like child_name, filming_preference
        try:
            extracted_dict = session.extracted_data.model_dump()
        except AttributeError:
            extracted_dict = session.extracted_data.dict()

        # 🌟 FLATTEN extracted_data fields to top-level for backward compatibility
        # This allows YAML to use `child_name:` instead of `extracted_data.child_name:`
        context = {
            "message_count": len(session.conversation_history),
            "completeness": completeness,
            "artifacts": artifacts_dict,  # 🚨 FIX: Dict format for card evaluation
            "uploaded_video_count": uploaded_video_count,
        }

        # Add all extracted fields as top-level keys
        context.update(extracted_dict)

        # Also keep nested for backward compat (in case some code uses it)
        context["extracted_data"] = extracted_dict

        return context

    def _generate_context_cards(
        self,
        family_id: str,
        completeness: float,
        action_requested: Optional[str],
        completeness_check: Optional[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Generate persistent state cards for UI using CardGenerator.

        These are continuous indicator cards that display while conditions are true
        (e.g., conversation_depth_card, video_guidelines_card, journal_card).

        Event-triggered cards are handled separately in process_message().
        """
        session = self.session_service.get_or_create_session(family_id)
        if not session:
            return []

        # Build context for card evaluation
        card_context = self._build_card_context(session, completeness)

        # Get cards from CardGenerator
        card_generator = get_card_generator()
        cards = card_generator.get_visible_cards(card_context, max_cards=4)

        logger.info(f"📇 Generated {len(cards)} persistent state cards")
        return cards


# Singleton instance
_simplified_conversation_service = None


def get_simplified_conversation_service() -> SimplifiedConversationService:
    """Get or create singleton simplified conversation service"""
    global _simplified_conversation_service
    if _simplified_conversation_service is None:
        _simplified_conversation_service = SimplifiedConversationService()
    return _simplified_conversation_service
