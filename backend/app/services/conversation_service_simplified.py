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
from typing import Dict, Any, Optional, List, Set, Tuple
from datetime import datetime
from collections import defaultdict

from .llm.base import Message
from .llm.factory import create_llm_provider
from .session_service import SessionState, get_session_service
from .lifecycle_manager import get_lifecycle_manager
from .prerequisite_service import get_prerequisite_service
from ..prompts.comprehensive_prompt_builder import build_comprehensive_prompt
from ..prompts.conversation_functions import CONVERSATION_FUNCTIONS_COMPREHENSIVE

logger = logging.getLogger(__name__)


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
        Process user message using simplified single-LLM architecture.

        Flow (Wu Wei - natural flow with safety limits):
        1. Get session data
        2. Build comprehensive prompt
        3. Function calling loop (model decides when done)
           - Keep tools available
           - Track function call count
           - Detect loops
        4. Process function calls
        5. Semantic verification (smart intervals)
        6. Return response

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

        # 1. Get session state
        session = self.session_service.get_or_create_session(family_id)
        data = session.extracted_data

        # 2. Build comprehensive system prompt
        available_artifacts = list(session.artifacts.keys())
        message_count = self._count_user_messages(session)

        system_prompt = build_comprehensive_prompt(
            child_name=data.child_name,
            age=data.age,
            gender=data.gender,
            extracted_data={
                'child_name': data.child_name,
                'age': data.age,
                'gender': data.gender,
                'primary_concerns': data.primary_concerns,
                'concern_details': data.concern_details,
                'strengths': data.strengths,
                'developmental_history': data.developmental_history,
                'family_context': data.family_context,
                'daily_routines': data.daily_routines,
                'parent_goals': data.parent_goals
            },
            completeness=session.completeness,
            available_artifacts=available_artifacts,
            message_count=message_count,
            session=session,
            lifecycle_manager=self.lifecycle_manager
        )

        # 3. Get conversation history
        history = self.session_service.get_conversation_history(family_id) or []

        # Build messages array
        messages = [Message(role="system", content=system_prompt)]

        for turn in history:
            messages.append(Message(
                role=turn["role"],
                content=turn["content"]
            ))

        messages.append(Message(role="user", content=user_message))

        # 4. FUNCTION CALLING LOOP (Wu Wei - natural flow with safety limits)
        logger.info("🤖 Starting Wu Wei function calling loop")

        loop_result = await self._function_calling_loop(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            family_id=family_id
        )

        # Unpack loop results
        final_response = loop_result["response"]
        llm_response = loop_result["llm_response"]
        all_extractions = loop_result["extractions"]
        action_requested = loop_result["action_requested"]
        developmental_question = loop_result["developmental_question"]
        analysis_question = loop_result["analysis_question"]
        app_help_request = loop_result["app_help_request"]

        # 5. Handle empty response with smart fallback
        if not final_response:
            final_response = self._generate_smart_fallback(
                family_id=family_id,
                all_extractions=all_extractions,
                user_message=user_message
            )

        # 6. Save conversation turn
        self.session_service.add_conversation_turn(family_id, "user", user_message)
        self.session_service.add_conversation_turn(family_id, "assistant", final_response)

        # 7. Get updated session state
        session = self.session_service.get_or_create_session(family_id)
        completeness_pct = session.completeness * 100

        # 8. Semantic verification (smart intervals)
        should_verify = self._should_run_verification(session)

        if should_verify:
            turn_count = self._count_user_messages(session)
            logger.info(f"🔍 Running semantic completeness verification (turn {turn_count})")
            semantic_result = await self.session_service.verify_semantic_completeness(family_id)

            if semantic_result.get('video_guidelines_readiness', 0) >= 80:
                logger.info(f"✅ Ready for video guidelines! ({semantic_result.get('video_guidelines_readiness')}%)")

        # 9. Generate context cards
        context_cards = self._generate_context_cards(
            family_id,
            session.completeness,
            action_requested,
            None
        )

        # 10. Process lifecycle events
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

        # 11. Wu Wei: Use lifecycle event messages if triggered
        response_text = self._merge_lifecycle_messages(
            final_response=final_response,
            lifecycle_result=lifecycle_result
        )

        # 12. Return response
        merged_extractions = self._merge_extractions(all_extractions)

        return {
            "response": response_text,
            "function_calls": [
                {"name": fc.name, "arguments": fc.arguments}
                for fc in llm_response.function_calls
            ],
            "completeness": completeness_pct,
            "extracted_data": merged_extractions,
            "context_cards": context_cards,
            "stats": self.session_service.get_session_stats(family_id),
            "architecture": "simplified_wu_wei",
            "intents_detected": {
                "developmental_question": developmental_question,
                "analysis_question": analysis_question,
                "app_help_request": app_help_request,
                "action_requested": action_requested
            }
        }

    async def _function_calling_loop(
        self,
        messages: List[Message],
        temperature: float,
        max_tokens: int,
        family_id: str
    ) -> Dict[str, Any]:
        """
        Wu Wei function calling loop - let model decide when done.

        Safety mechanisms:
        - Max iterations (prevent infinite loops)
        - Max function calls (cost control)
        - Loop detection (same function repeatedly)

        Returns:
            Dict with response, llm_response, extractions, and intents
        """
        iteration = 0
        total_function_calls = 0
        llm_response = None

        # Track ALL extractions and intents across iterations
        all_extractions = []
        action_requested = None
        developmental_question = None
        analysis_question = None
        app_help_request = None

        # Loop detection: track function call signatures
        function_call_history: List[Tuple[str, str]] = []  # (name, args_hash)

        while iteration < self.MAX_ITERATIONS:
            iteration += 1
            logger.info(f"🔄 Iteration {iteration}/{self.MAX_ITERATIONS} (total calls: {total_function_calls}/{self.MAX_FUNCTION_CALLS})")

            # Wu Wei: Always provide tools, let model decide when done
            # Only remove tools if we've hit the function call limit
            functions_param = None if total_function_calls >= self.MAX_FUNCTION_CALLS else CONVERSATION_FUNCTIONS_COMPREHENSIVE

            if total_function_calls >= self.MAX_FUNCTION_CALLS:
                logger.warning(f"⚠️ Function call limit reached ({self.MAX_FUNCTION_CALLS}), forcing text response")

            # Call LLM
            llm_response = await self.llm.chat(
                messages=messages,
                functions=functions_param,
                temperature=temperature,
                max_tokens=max_tokens
            )

            response_text = llm_response.content or ""
            has_function_calls = len(llm_response.function_calls) > 0
            finish_reason = getattr(llm_response, 'finish_reason', None)

            logger.info(
                f"✅ LLM response: {len(response_text)} chars, "
                f"{len(llm_response.function_calls)} function calls, "
                f"finish_reason: {finish_reason}"
            )

            # Log function calls with details
            if has_function_calls:
                self._log_function_calls(llm_response.function_calls)
            else:
                if iteration == 1 and functions_param:
                    logger.info("ℹ️ No function calls on first iteration - model provided direct response")

            # Check for malformed function call
            if finish_reason and 'MALFORMED' in str(finish_reason):
                logger.error(
                    f"🔴 MALFORMED_FUNCTION_CALL detected on iteration {iteration}. "
                    f"Model may be too weak. Recommend gemini-2.5-flash or better."
                )
                if iteration > 1:
                    logger.warning("⚠️ Falling back to previous valid state")
                    break

            # If no function calls, we have the final text response
            if not has_function_calls:
                logger.info("✅ Final text response received")
                break

            # Check if we're hitting the function call limit
            if total_function_calls + len(llm_response.function_calls) > self.MAX_FUNCTION_CALLS:
                logger.warning(
                    f"⚠️ Would exceed function call limit. "
                    f"Stopping at {total_function_calls} calls."
                )
                break

            # Loop detection: check if model is stuck
            if self._detect_function_loop(llm_response.function_calls, function_call_history):
                logger.error("🔴 Function call loop detected! Model is stuck. Breaking loop.")
                break

            # Add assistant's response to conversation
            messages.append(Message(
                role="assistant",
                content=response_text or "",
                function_calls=llm_response.function_calls
            ))

            # Process function calls
            function_results = []
            new_extractions, new_intents = self._process_function_calls(
                llm_response.function_calls,
                family_id
            )

            # Track results
            all_extractions.extend(new_extractions)
            if new_intents.get("action_requested"):
                action_requested = new_intents["action_requested"]
            if new_intents.get("developmental_question"):
                developmental_question = new_intents["developmental_question"]
            if new_intents.get("analysis_question"):
                analysis_question = new_intents["analysis_question"]
            if new_intents.get("app_help_request"):
                app_help_request = new_intents["app_help_request"]

            # Build function results for model
            for func_call in llm_response.function_calls:
                if func_call.name == "extract_interview_data":
                    function_results.append({
                        "name": func_call.name,
                        "result": {"status": "success", "data_saved": True}
                    })
                elif func_call.name == "ask_developmental_question":
                    function_results.append({
                        "name": func_call.name,
                        "result": {"status": "noted", "topic": func_call.arguments.get('question_topic')}
                    })
                elif func_call.name == "ask_about_analysis":
                    function_results.append({
                        "name": func_call.name,
                        "result": {"status": "noted", "element": func_call.arguments.get('analysis_element')}
                    })
                elif func_call.name == "ask_about_app":
                    function_results.append({
                        "name": func_call.name,
                        "result": {"status": "noted", "topic": func_call.arguments.get('help_topic')}
                    })
                elif func_call.name == "request_action":
                    function_results.append({
                        "name": func_call.name,
                        "result": {"status": "noted", "action": func_call.arguments.get('action')}
                    })

            # Add function results to conversation
            messages.append(Message(
                role="function",
                content="Function execution results",
                function_response=function_results
            ))

            total_function_calls += len(llm_response.function_calls)
            logger.info(f"📤 Sent {len(function_results)} function results back to LLM")

        # Check for early exit conditions
        if iteration >= self.MAX_ITERATIONS:
            logger.warning(f"⚠️ Reached max iterations ({self.MAX_ITERATIONS})")

        return {
            "response": response_text,
            "llm_response": llm_response,
            "extractions": all_extractions,
            "action_requested": action_requested,
            "developmental_question": developmental_question,
            "analysis_question": analysis_question,
            "app_help_request": app_help_request
        }

    def _process_function_calls(
        self,
        function_calls: List[Any],
        family_id: str
    ) -> Tuple[List[Dict], Dict[str, Any]]:
        """
        Process function calls and return extractions and intents.

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

    def _detect_function_loop(
        self,
        function_calls: List[Any],
        history: List[Tuple[str, str]]
    ) -> bool:
        """
        Detect if model is stuck in a loop calling the same function repeatedly.

        Returns:
            True if loop detected, False otherwise
        """
        import hashlib

        # Build signatures for current calls
        current_signatures = []
        for fc in function_calls:
            # Create hash of function name + arguments
            args_str = str(sorted(fc.arguments.items()))
            signature = (fc.name, hashlib.md5(args_str.encode()).hexdigest()[:8])
            current_signatures.append(signature)

        # Check if any signature appears too many times in recent history
        recent_history = history[-10:]  # Look at last 10 calls
        for sig in current_signatures:
            count = recent_history.count(sig)
            if count >= 3:  # Same call 3 times = stuck
                logger.error(f"🔴 Loop detected: {sig[0]} called {count} times with same args")
                return True

        # Add current signatures to history
        history.extend(current_signatures)
        return False

    def _log_function_calls(self, function_calls: List[Any]) -> None:
        """Log function call details for debugging"""
        logger.info(f"📞 Functions called: {[fc.name for fc in function_calls]}")
        for fc in function_calls:
            arg_keys = list(fc.arguments.keys())
            logger.debug(f"   📋 {fc.name}({arg_keys})")
            # Log first 200 chars of each argument
            for key, value in fc.arguments.items():
                value_str = str(value)[:200]
                logger.debug(f"      {key}: {value_str}")

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

    def _merge_lifecycle_messages(
        self,
        final_response: str,
        lifecycle_result: Dict[str, Any]
    ) -> str:
        """
        Merge lifecycle event messages with final response.

        If lifecycle events triggered, their messages explain what happened
        (e.g., "Video guidelines are ready!"). Use these instead of or
        alongside the conversational response.
        """
        if not lifecycle_result.get("events_triggered"):
            return final_response

        # Extract all event messages
        event_messages = [
            event.get("message", "")
            for event in lifecycle_result["events_triggered"]
            if event.get("message")
        ]

        if not event_messages:
            return final_response

        # Log what we're doing
        event_names = [e["event_name"] for e in lifecycle_result["events_triggered"]]
        logger.info(f"🎉 Lifecycle events triggered: {event_names}")

        # If we have multiple events, combine them
        lifecycle_message = "\n\n".join(event_messages)

        # Use lifecycle message as primary response
        # (it explains what just unlocked/happened)
        logger.info(f"📢 Using lifecycle message: {lifecycle_message[:100]}...")
        return lifecycle_message

    def _count_user_messages(self, session: SessionState) -> int:
        """Count user messages in conversation history"""
        conversation_history = session.conversation_history or []
        return len([m for m in conversation_history if m.get('role') == 'user'])

    def _should_run_verification(self, session: SessionState) -> bool:
        """
        Determine if semantic verification should run this turn.

        Uses exponential backoff: verify at turns 6, 9, 12, 18, 24, 36...
        Stop verifying once video guidelines are generated.
        """
        turn_count = self._count_user_messages(session)
        video_guidelines_generated = session.has_artifact("baseline_video_guidelines")

        # Don't verify if guidelines already generated
        if video_guidelines_generated:
            return False

        # Check if current turn matches a verification turn
        if turn_count not in self.VERIFICATION_TURNS:
            return False

        # Verify if we haven't verified at this turn already
        return turn_count != session.semantic_verification_turn

    def _merge_extractions(self, all_extractions: List[Dict]) -> Dict[str, Any]:
        """Merge all extractions into a single dict"""
        merged = {}
        for extraction in all_extractions:
            merged.update(extraction)
        return merged

    def _build_session_data_dict(self, family_id: str, session: SessionState) -> Dict[str, Any]:
        """Build session data dict for prerequisite service"""
        try:
            extracted_dict = session.extracted_data.model_dump()
        except AttributeError:
            extracted_dict = session.extracted_data.dict()

        return {
            "family_id": family_id,
            "extracted_data": extracted_dict,
            "message_count": self._count_user_messages(session),
            "artifacts": session.artifacts,
            "semantic_verification": session.semantic_verification,
            "video_guidelines": session.has_artifact("baseline_video_guidelines"),
            "video_guidelines_status": (
                session.get_artifact("baseline_video_guidelines").status
                if session.get_artifact("baseline_video_guidelines")
                else "pending"
            ),
            "parent_report_id": (
                session.get_artifact("baseline_parent_report").artifact_id
                if session.has_artifact("baseline_parent_report")
                else None
            ),
            "uploaded_video_count": 0,
            "re_assessment_active": False,
            "viewed_guidelines": False,
            "declined_guidelines_offer": False,
        }

    def _generate_context_cards(
        self,
        family_id: str,
        completeness: float,
        action_requested: Optional[str],
        completeness_check: Optional[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Generate context cards for UI.

        Can be enhanced later with:
        - Progress indicators
        - Next steps suggestions
        - Missing information highlights
        """
        # For now, return empty list
        # Can add card generation logic as needed
        return []


# Singleton instance
_simplified_conversation_service = None


def get_simplified_conversation_service() -> SimplifiedConversationService:
    """Get or create singleton simplified conversation service"""
    global _simplified_conversation_service
    if _simplified_conversation_service is None:
        _simplified_conversation_service = SimplifiedConversationService()
    return _simplified_conversation_service
