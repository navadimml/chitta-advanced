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
from .interview_service import InterviewState, get_interview_service, InterviewService
from .prerequisite_service import get_prerequisite_service, PrerequisiteService
from .knowledge_service import get_knowledge_service, KnowledgeService
from .consultation_service import get_consultation_service, ConsultationService
from .artifact_generation_service import ArtifactGenerationService
from .lifecycle_manager import get_lifecycle_manager, LifecycleManager  # 🌟 Wu Wei: Core dependency graph processor
from .sage_service import get_sage_service, SageService, SageWisdom  # 🌟 Wu Wei: Interpretive reasoning layer
from .hand_service import get_hand_service, HandService, ActionMode  # 🌟 Wu Wei: Action decision layer
from ..config.artifact_manager import get_artifact_manager
from ..prompts.interview_prompt import build_interview_prompt
from ..prompts.dynamic_interview_prompt import build_dynamic_interview_prompt
from ..prompts.strategic_advisor import get_strategic_guidance
from ..prompts.interview_functions import INTERVIEW_FUNCTIONS
from ..prompts.interview_functions_lite import INTERVIEW_FUNCTIONS_LITE
from ..prompts.prerequisites import Action
from ..prompts.intent_types import IntentCategory
# Wu Wei Architecture: Import phase_manager and card_generator for config-driven phase tracking and UI
from ..config.phase_manager import get_phase_manager, PhaseManager
from ..config.card_generator import get_card_generator, CardGenerator

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
        extraction_llm_provider: Optional[BaseLLMProvider] = None,
        interview_service: Optional[InterviewService] = None,
        prerequisite_service: Optional[PrerequisiteService] = None,
        knowledge_service: Optional[KnowledgeService] = None,
        consultation_service: Optional[ConsultationService] = None,
        sage_service: Optional[SageService] = None,
        hand_service: Optional[HandService] = None,
        phase_manager: Optional[PhaseManager] = None,
        card_generator: Optional[CardGenerator] = None,
        artifact_generation_service: Optional[ArtifactGenerationService] = None,
        lifecycle_manager: Optional[LifecycleManager] = None
    ):
        self.llm = llm_provider or create_llm_provider()

        # 🎯 Dedicated extraction LLM with stronger model for better categorization
        # Conversation uses fast model (e.g., flash-lite) for speed
        # Extraction uses stronger model (e.g., flash-exp or pro) for accuracy
        self.extraction_llm = extraction_llm_provider or self._create_extraction_llm()

        self.interview_service = interview_service or get_interview_service()
        self.prerequisite_service = prerequisite_service or get_prerequisite_service()
        self.knowledge_service = knowledge_service or get_knowledge_service()
        self.consultation_service = consultation_service or get_consultation_service()  # 🌟 Universal consultation handler
        self.sage_service = sage_service or get_sage_service()  # 🌟 Wu Wei: Interpretive reasoning - "What does this mean?"
        self.hand_service = hand_service or get_hand_service()  # 🌟 Wu Wei: Action decision - "What do we do about it?"
        self.phase_manager = phase_manager or get_phase_manager()  # 🌟 Wu Wei: Config-driven phase management
        self.card_generator = card_generator or get_card_generator()  # 🌟 Wu Wei: Config-driven UI cards
        self.artifact_service = artifact_generation_service or ArtifactGenerationService()  # 🌟 Wu Wei: Artifact generation
        self.lifecycle_manager = lifecycle_manager or get_lifecycle_manager()  # 🌟 Wu Wei: CORE - dependency graph processor

        logger.info(f"ConversationService initialized:")
        logger.info(f"  - Conversation LLM: {self.llm.get_provider_name()}")
        logger.info(f"  - Extraction LLM: {self.extraction_llm.get_provider_name()}")
        logger.info(f"  - Sage/Hand architecture: ENABLED (Wu Wei interpretive reasoning)")

    def _create_extraction_llm(self) -> BaseLLMProvider:
        """
        Create a stronger LLM specifically for extraction.

        Extraction is a critical task that requires better reasoning to:
        - Distinguish concerns from strengths
        - Categorize information correctly
        - Handle nuanced language

        IMPORTANT: Model must have stable function calling support!
        gemini-flash-latest caused MALFORMED_FUNCTION_CALL errors (extraction failed).
        Using gemini-2.5-flash which is the current stable model for function calling.
        """
        import os

        # Check if extraction model is explicitly configured
        extraction_model = os.getenv("EXTRACTION_MODEL")

        if extraction_model:
            logger.info(f"Using configured extraction model: {extraction_model}")
            return create_llm_provider(model=extraction_model)

        # Use gemini-2.5-flash: Current stable model with excellent function calling support
        # Best balance of speed, accuracy, and stable function calling for extraction
        logger.info("Using extraction model: gemini-2.5-flash (stable function calling)")
        return create_llm_provider(model="gemini-2.5-flash")

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

        # 2. SAGE → HAND ARCHITECTURE (Wu Wei interpretive reasoning)
        # The Sage interprets what the parent means and needs (natural understanding)
        # The Hand decides what action to take (structured decision)
        # This is separation of concerns: understanding vs action
        intent_detected = None
        prerequisite_check = None
        information_request = None
        injected_knowledge = None

        # Build rich context for Sage interpretation
        # 1. Recent conversation (to understand dialogue flow)
        recent_history = self.interview_service.get_conversation_history(
            family_id,
            last_n=8  # Last 4 exchanges
        )

        # 2. Available artifacts (to know what can be consulted about)
        artifact_names = []
        if session.artifacts:
            for artifact_id, artifact in session.artifacts.items():
                # Get readable name from artifact content or use ID
                if hasattr(artifact, 'content') and isinstance(artifact.content, dict):
                    title = artifact.content.get('title', artifact_id)
                    artifact_names.append(title)
                else:
                    artifact_names.append(artifact_id)

        # 3. Child context (for developmental consultation)
        child_context = {
            "child_name": data.child_name,
            "age": data.age,
            "primary_concerns": data.primary_concerns or []
        }

        # 4. Session state
        session_state = {
            "completeness": session.completeness
        }

        # STEP 1: The Sage interprets (natural understanding)
        logger.info("✨ Invoking Sage to interpret parent's message...")
        sage_wisdom: SageWisdom = await self.sage_service.interpret(
            user_message=user_message,
            recent_conversation=recent_history,
            child_context=child_context,
            available_artifacts=artifact_names,
            session_state=session_state
        )
        logger.info(f"✨ Sage wisdom: {sage_wisdom.interpretation[:120]}...")

        # STEP 2: The Hand decides action (structured decision)
        logger.info("👋 Invoking Hand to decide action based on wisdom...")
        hand_guidance = await self.hand_service.decide_action(
            wisdom=sage_wisdom,
            user_message=user_message,
            available_artifacts=artifact_names,
            available_actions=[a.value for a in Action]
        )
        logger.info(f"👋 Hand guidance: {hand_guidance.mode.value} - {hand_guidance.reasoning[:80]}...")

        # STEP 3: Execute based on Hand's guidance (natural action flow)

        # Handle EXPLAIN_PROCESS mode (app/process questions)
        if hand_guidance.mode == ActionMode.EXPLAIN_PROCESS:
            logger.info(f"✓ Explain process mode: {hand_guidance.information_type}")

            # Build context for knowledge retrieval
            context = {
                "child_name": data.child_name,
                "completeness": session.completeness,
                "video_count": 0,  # TODO: Get from actual video count
                "reports_available": False  # TODO: Get from actual report status
            }

            # Map information_type to InformationRequestType
            from ..prompts.intent_types import InformationRequestType
            info_type_map = {
                "app_features": InformationRequestType.APP_FEATURES,
                "process_explanation": InformationRequestType.PROCESS_EXPLANATION,
                "current_state": InformationRequestType.CURRENT_STATE
            }
            information_request = info_type_map.get(
                hand_guidance.information_type,
                InformationRequestType.APP_FEATURES
            )

            # Inject knowledge for LLM to use in generating response
            injected_knowledge = self.knowledge_service.get_knowledge_for_prompt(
                information_request,
                context
            )
            logger.info(f"Injecting domain knowledge about {information_request} for LLM to use")

        # Handle CONSULTATION mode (developmental questions)
        elif hand_guidance.mode == ActionMode.CONSULTATION:
            logger.info(f"✓ Consultation mode: {hand_guidance.consultation_type}")

            # Use universal consultation service - handles ALL consultation types
            consultation_result = await self.consultation_service.handle_consultation(
                family_id=family_id,
                question=user_message,
                conversation_history=recent_history
            )

            # Return consultation response directly (already saved to history by consultation service)
            return {
                "response": consultation_result["response"],
                "function_calls": [],
                "completeness": session.completeness * 100,
                "extracted_data": {},
                "context_cards": self._generate_context_cards(
                    family_id,
                    session.completeness,
                    None,
                    None
                ),
                "stats": self.interview_service.get_session_stats(family_id),
                "consultation": {
                    "sources_used": consultation_result["sources_used"],
                    "timestamp": consultation_result["timestamp"]
                },
                "sage_wisdom": {
                    "interpretation": sage_wisdom.interpretation,
                    "emotional_state": sage_wisdom.emotional_state
                }
            }

        # Handle DELIVER_ARTIFACT mode (specific artifact requests)
        elif hand_guidance.mode == ActionMode.DELIVER_ARTIFACT:
            intent_detected = hand_guidance.artifact_id or "view_report"
            logger.info(f"✓ Deliver artifact mode: {intent_detected}")

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

        # Handle EXECUTE_ACTION mode (other actions)
        elif hand_guidance.mode == ActionMode.EXECUTE_ACTION:
            intent_detected = hand_guidance.action_name
            logger.info(f"✓ Execute action mode: {intent_detected}")

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

        # Handle CONVERSATION mode (natural dialogue with extraction)
        else:
            logger.info(f"✓ Conversation mode (extraction: {hand_guidance.extraction_needed})")

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

            # 🌟 INJECT ARTIFACT AWARENESS - Even post-interview, Chitta needs to know what exists
            artifact_awareness = self._build_artifact_awareness(session)
            if artifact_awareness:
                base_prompt += f"""

{artifact_awareness}
"""

        else:
            # During interview: use dynamic interview prompt with LLM-based strategic advisor
            # Natural flow + intelligent strategic awareness

            # Get strategic guidance from LLM analysis of extracted data
            # This is MUCH smarter than pattern matching!
            extracted_data_dict = {
                "child_name": data.child_name,
                "age": data.age,
                "gender": data.gender,
                "primary_concerns": data.primary_concerns,
                "concern_details": data.concern_details,
                "strengths": data.strengths,
                "developmental_history": data.developmental_history,
                "family_context": data.family_context,
                "daily_routines": data.daily_routines,
                "parent_goals": data.parent_goals
            }

            # 🌟 Wu Wei: Build prerequisite context for lifecycle awareness
            # This allows strategic advisor to check what moments are coming next
            session_data = self._build_session_data_dict(family_id, session)
            lifecycle_context = self.prerequisite_service.get_context_for_cards(session_data)

            strategic_guidance = await get_strategic_guidance(
                self.llm,
                extracted_data_dict,
                session.completeness,
                lifecycle_manager=self.lifecycle_manager,  # 🌟 Pass lifecycle manager
                context=lifecycle_context  # 🌟 Pass full context for prerequisite evaluation
            )

            # Build dynamic prompt with strategic guidance
            base_prompt = build_dynamic_interview_prompt(
                child_name=data.child_name or "unknown",
                age=str(data.age) if data.age else "unknown",
                gender=data.gender or "unknown",
                concerns=data.primary_concerns,
                completeness=session.completeness,
                extracted_data=extracted_data_dict,
                strategic_guidance=strategic_guidance
            )

        # 🌟 INJECT ARTIFACT AWARENESS - Critical for sync between lifecycle events and conversation
        # This ensures Chitta knows what artifacts have been generated and can reference them properly
        artifact_awareness = self._build_artifact_awareness(session)
        if artifact_awareness:
            base_prompt += f"""

{artifact_awareness}
"""

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
            base_prompt += f"""

## 📚 KNOWLEDGE TO USE IN YOUR RESPONSE

{injected_knowledge}

**CRITICAL - How to Use This Knowledge:**
- Use the information above to answer the parent's question naturally
- **DON'T re-introduce yourself!** You already said "שלום! אני צ'יטה" in your first message
- **DON'T repeat greetings** - just answer their question warmly
- If the knowledge includes "שאלה מצוינת" or similar, that's fine - just don't add "שלום! אני צ'יטה" again
- After answering, invite them to continue: "יש לך עוד שאלות, או שנמשיך בשיחה על הילד/ה?"
"""

        system_prompt = base_prompt

        # 6. Build conversation messages
        messages = [Message(role="system", content=system_prompt)]

        # Add recent conversation history (last 20 turns)
        # Increased from 20 to 40 to reduce context loss glitches
        history = self.interview_service.get_conversation_history(
            family_id,
            last_n=40  # Last 20 exchanges (user + assistant)
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
                f"Conversation response: {len(llm_response.content)} chars, "
                f"finish_reason: {llm_response.finish_reason}"
            )

            # Check if response is empty (blocked, unknown error, or other issue)
            # Retry with simplified prompt for ANY empty response, not just safety blocks
            if not llm_response.content.strip():

                logger.warning(
                    f"⚠️ Empty response (finish_reason: {llm_response.finish_reason}). "
                    f"Retrying with simplified prompt..."
                )

                # Create a much simpler, safer prompt for retry
                simple_system = f"""You are Chitta (צ'יטה), a warm Hebrew-speaking assistant helping parents understand their child's development.

Child: {data.child_name or "unknown"} | Age: {data.age or "unknown"}
Interview progress: {session.completeness:.0%}

Your role:
- Have a natural, empathetic conversation in Hebrew
- Ask thoughtful questions about the child's development
- Be warm and supportive
- Ask ONE question at a time

Current conversation state:
- Basic info: {"collected" if data.child_name and data.age else "still gathering"}
- Concerns discussed: {len(data.primary_concerns)} areas
- Detail level: {session.completeness:.0%}

Continue the conversation naturally."""

                # Build simpler messages (last 10 turns only + simple system)
                simple_messages = [Message(role="system", content=simple_system)]

                # Add last 10 conversation turns
                recent_history = self.interview_service.get_conversation_history(
                    family_id,
                    last_n=10
                )
                for turn in recent_history:
                    simple_messages.append(Message(
                        role=turn["role"],
                        content=turn["content"]
                    ))

                # Add current user message
                simple_messages.append(Message(role="user", content=user_message))

                # Retry with simpler prompt
                llm_response = await self.llm.chat(
                    messages=simple_messages,
                    functions=None,
                    temperature=temperature,
                    max_tokens=2000
                )

                logger.info(
                    f"Retry response: {len(llm_response.content)} chars, "
                    f"finish_reason: {llm_response.finish_reason}"
                )

            # Ensure we got a response
            if not llm_response.content.strip():
                logger.error("❌ LLM returned empty response even after retry!")
                llm_response.content = "סליחה, יש לי בעיה טכנית. בואי ננסה שוב."

            # CALL 2: Extract structured data from conversation
            # Create dedicated extraction context with current state
            session = self.interview_service.get_or_create_session(family_id)
            current_data = session.extracted_data

            extraction_system = f"""Extract structured information from this conversation turn.

**Current data:**
Child: {current_data.child_name or 'unknown'}, {current_data.age or '?'} years
Concerns: {current_data.primary_concerns or 'none yet'}
Completeness: {session.completeness:.0%}

**EXTRACTION RULES:**

1. **Extract EVERYTHING - conversation history is limited!**
   - Parent's words disappear after ~20 exchanges
   - Extract now or lose it forever
   - Better to over-extract than miss something

2. **CRITICAL - Concerns vs Strengths:**
   ⚠️ PRIMARY_CONCERNS = ONLY if parent expresses WORRY/DIFFICULTY/PROBLEM
   ✅ STRENGTHS = Positive behaviors, things child does well

   **Strengths (NOT concerns):**
   - "plays with other children", "gets along well", "has friends" → STRENGTH
   - "talks a lot", "communicates well" → STRENGTH
   - "runs and climbs" → STRENGTH

   **Concerns (extract these):**
   - "struggles to connect", "avoids interaction" → concern
   - "doesn't speak well", "speech delay" → concern

3. **Use parent's EXACT WORDS for strengths:**
   - Parent: "הוא רץ ומטפס כל הזמן" → Extract: "רץ ומטפס כל הזמן" ✅
   - NOT: "יכולות מוטוריות טובות" ❌ (clinical jargon)

4. **Extract everything relevant:**
   - Basic info: name, age, gender
   - Concerns: categories + detailed descriptions
   - Strengths: interests, abilities, positive traits
   - History: milestones, medical, evaluations
   - Family: siblings, dynamics, support
   - Daily life: routines, sleep, eating, activities
   - Goals: what parent hopes to achieve

Call extract_interview_data with ALL relevant information from this turn."""

            extraction_messages = [
                Message(role="system", content=extraction_system),
                Message(role="user", content=f"Parent: {user_message}"),
                Message(role="assistant", content=f"Response: {llm_response.content}"),
                Message(role="user", content="Extract all relevant data from this conversation turn.")
            ]

            # 🎯 Use dedicated extraction LLM (stronger model for better categorization)
            extraction_response = await self.extraction_llm.chat(
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

        # 9. 🌟 Wu Wei: Process lifecycle events (dependency graph magic!)
        # This replaces ALL hardcoded artifact generation logic
        # Everything emerges from lifecycle_events.yaml configuration
        session_data = self._build_session_data_dict(family_id, session)

        # Flatten extracted_data for prerequisite evaluation
        context = self.prerequisite_service.get_context_for_cards(session_data)

        # Let lifecycle manager check dependency graph and auto-generate artifacts
        lifecycle_result = await self.lifecycle_manager.process_lifecycle_events(
            family_id=family_id,
            context=context,
            session=session
        )

        # Log what emerged
        if lifecycle_result["artifacts_generated"]:
            logger.info(
                f"🌟 Wu Wei: Artifacts emerged from dependency graph: "
                f"{lifecycle_result['artifacts_generated']}"
            )

        # 🌟 Wu Wei: If lifecycle events were triggered, use their messages from YAML
        # Events have already-formatted messages from lifecycle_events.yaml
        if lifecycle_result["events_triggered"]:
            # Use the first event's message (usually only one per turn)
            event = lifecycle_result["events_triggered"][0]
            logger.info(
                f"🎉 Wu Wei: Using event message from lifecycle_events.yaml: {event['event_name']}"
            )

            return {
                "response": event["message"],  # Use message from YAML!
                "function_calls": [
                    {"name": fc.name, "arguments": fc.arguments}
                    for fc in llm_response.function_calls
                ],
                "completeness": completeness_pct,
                "extracted_data": extraction_summary,
                "context_cards": context_cards,
                "stats": self.interview_service.get_session_stats(family_id),
                "lifecycle_event": event["event_name"]  # Signal which event occurred
            }

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

    def _build_session_data_dict(
        self,
        family_id: str,
        session: 'InterviewState'
    ) -> Dict[str, Any]:
        """
        🌟 Wu Wei: Build session_data dict for prerequisite_service

        Transforms InterviewState → session_data format expected by
        prerequisite_service.get_context_for_cards()

        Args:
            family_id: Family identifier
            session: InterviewState object

        Returns:
            Session data dict with extracted_data, artifacts, flags, etc.
        """
        # Get extracted data as dict
        try:
            extracted_dict = session.extracted_data.model_dump()
        except AttributeError:
            extracted_dict = session.extracted_data.dict()

        return {
            "family_id": family_id,
            "extracted_data": extracted_dict,
            "message_count": len(session.conversation_history),

            # 🌟 Wu Wei: Include actual artifacts from session
            "artifacts": session.artifacts,  # Dict[str, Artifact]

            # DEPRECATED: Old field names (for backwards compatibility)
            "video_guidelines": session.video_guidelines_generated,
            "video_guidelines_status": "ready" if session.video_guidelines_generated else "pending",
            "parent_report_id": session.get_artifact("baseline_parent_report").artifact_id if session.has_artifact("baseline_parent_report") else None,

            # TODO fields
            "uploaded_video_count": 0,  # TODO: Get from video storage
            "re_assessment_active": False,  # TODO: Track from flags
            "viewed_guidelines": False,  # TODO: Track user actions
            "declined_guidelines_offer": False,  # TODO: Track user actions
        }

    def _build_artifact_awareness(self, session: Any) -> str:
        """
        Build artifact awareness section for injection into conversation prompt.

        This ensures Chitta knows what artifacts have been generated and can
        reference them properly in conversation (critical for sync).

        🌟 GENERIC IMPLEMENTATION - Works with any artifact type from config!

        Args:
            session: Current interview session

        Returns:
            Formatted artifact awareness string, or empty string if no artifacts
        """
        if not session.artifacts:
            return ""

        artifact_manager = get_artifact_manager()
        artifacts_list = []

        for artifact_id, artifact in session.artifacts.items():
            # Get artifact definition from config (config-driven!)
            artifact_def = artifact_manager.get_artifact(artifact_id)

            if artifact_def:
                # Use Hebrew name from config
                friendly_name = artifact_def.get("name", artifact.artifact_type)
                description = artifact_def.get("description", "")
            else:
                # Fallback if not in config
                friendly_name = artifact.artifact_type
                description = ""

            # Format creation date
            created_date = artifact.created_at
            if hasattr(created_date, 'strftime'):
                date_str = created_date.strftime("%d/%m/%Y %H:%M")
            else:
                date_str = str(created_date)

            # Build artifact entry
            artifact_entry = f"  ✅ **{friendly_name}** (נוצר: {date_str})"
            if description:
                artifact_entry += f"\n     {description}"

            artifacts_list.append(artifact_entry)

        if not artifacts_list:
            return ""

        # 🌟 Get UI context from lifecycle manager to tell Chitta WHERE artifacts are
        ui_context = self._get_artifact_ui_context(session)

        return f"""
## 📋 מסמכים ותוצרים שכבר יצרת

{chr(10).join(artifacts_list)}

**חשוב מאוד:** המסמכים האלה כבר קיימים וזמינים להורה!

**איפה להפנות את ההורה:**
{ui_context}

**הנחיות לשימוש:**
- אם ההורה שואל על מסמך - התייחס אליו כמוכן, לא כמשהו שעוד צריך ליצור
- השתמש בלשון עבר: "כבר הכנתי", "יצרתי", "סיכמתי" (לא "אכין", "ייצר")
- הפנה אותם למיקום הנכון (כרטיס ההקשר או מקטע ספציפי)
- אם הם שואלים על תוכן - תן סקירה קצרה והפנה לקריאה מלאה

**דוגמאות לתשובות טובות:**
- "כבר הכנתי לך [שם המסמך]! תראי אותו [היכן למצוא]"
- "בדוח שיצרתי ראית שכתבתי על..."
- "אם תרצי לקרוא את ההנחיות המלאות, [היכן למצוא]"
"""

    def _get_artifact_ui_context(self, session: Any) -> str:
        """
        Get UI context for where artifacts are located.

        Uses lifecycle events configuration to tell Chitta where each artifact
        can be found in the UI.

        Args:
            session: Current interview session

        Returns:
            Formatted string with UI locations for artifacts
        """
        # Get lifecycle manager to access event configurations
        lifecycle_manager = self.lifecycle_manager

        ui_locations = []

        # Check which lifecycle events have been triggered
        # and get their UI context
        for artifact_id in session.artifacts.keys():
            # Find lifecycle event that created this artifact
            event_config = lifecycle_manager._find_event_for_artifact(artifact_id)

            if event_config and "ui" in event_config:
                ui_info = event_config["ui"]
                default_text = ui_info.get("default", "")

                if default_text:
                    artifact_manager = get_artifact_manager()
                    artifact_def = artifact_manager.get_artifact(artifact_id)
                    artifact_name = artifact_def.get("name", artifact_id) if artifact_def else artifact_id

                    ui_locations.append(f"- **{artifact_name}**: {default_text}")

        if ui_locations:
            return "\n".join(ui_locations)
        else:
            return "- כרטיסי ההקשר (Context Cards) בראש הדף\n- או במקטע המתאים בתפריט"

    def _generate_context_cards(
        self,
        family_id: str,
        completeness: float,
        action_requested: Optional[str],
        completeness_check: Optional[Dict]
    ) -> List[Dict[str, Any]]:
        """
        🌟 Wu Wei Architecture: Generate context cards using prerequisite_service

        Now uses prerequisite_service.get_context_for_cards() which builds context
        with artifacts, flags, and prerequisites - all aligned with lifecycle_events.yaml!

        Args:
            family_id: Family identifier
            completeness: DEPRECATED (kept for compatibility)
            action_requested: Action user requested (if any)
            completeness_check: DEPRECATED (kept for compatibility)

        Returns:
            List of card dicts for frontend
        """
        session = self.interview_service.get_or_create_session(family_id)

        # 🌟 Wu Wei: Build session_data and let prerequisite_service build context
        session_data = self._build_session_data_dict(family_id, session)

        # Get Wu Wei context (includes artifacts, flags, knowledge_is_rich, etc.)
        context = self.prerequisite_service.get_context_for_cards(session_data)

        # Add current interaction context (not in prerequisite_service)
        context["action_requested"] = action_requested
        context["completeness_check"] = completeness_check
        context["completeness"] = completeness  # DEPRECATED but may be used by old cards

        # 🌟 Use card_generator to get config-driven cards
        cards = self.card_generator.get_visible_cards(context)

        logger.debug(
            f"Generated {len(cards)} context cards using card_generator "
            f"(phase={session.phase}, completeness={completeness:.1%})"
        )

        return cards

    def _translate_concerns(self, concerns: List[str]) -> List[str]:
        """
        Translate concern categories to Hebrew using observational language.

        Chitta is NOT a diagnostic tool - we use descriptive, observational
        language that focuses on what parents observe, not clinical categories.
        """
        translations = {
            "speech": "שפה ותקשורת",           # Language and communication (not just "speech")
            "social": "קשרים עם אחרים",        # Connections with others (observational)
            "attention": "ריכוז וקשב",         # Focus and attention
            "motor": "תנועה ותיאום",            # Movement and coordination (descriptive)
            "sensory": "חוויות חושיות",        # Sensory experiences (not diagnostic)
            "emotional": "ויסות רגשי",          # Emotional regulation (functional, not diagnostic)
            "behavioral": "תגובות והסתגלות",   # Reactions and adjustment (observational)
            "learning": "למידה והבנה",         # Learning and understanding
            "sleep": "שגרות שינה",             # Sleep routines (observational)
            "eating": "הרגלי אכילה",           # Eating habits (observational)
            "other": "נושאים נוספים"          # Additional topics
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
