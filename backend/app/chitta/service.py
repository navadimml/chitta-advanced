"""
Chitta Service - Main orchestration for Chitta conversations

This service coordinates:
1. Building the Gestalt from Child + UserSession
2. Constructing the system prompt
3. Calling the LLM with tools
4. Processing tool calls
5. Updating state based on responses

Design principles:
- Chitta leads the conversation
- Tools trigger REAL actions (no hallucinated content)
- State is always persisted
- Errors are handled gracefully

Handles:
- Returning users (time gaps, session continuity)
- Async operations (background completeness checks)
- Intermittent use (proper state persistence)
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

from app.models.child import Child, JournalEntry
from app.models.user_session import UserSession
from app.services.unified_state_service import get_unified_state_service

from .gestalt import build_gestalt, Gestalt, get_what_we_know
from .prompt import build_system_prompt
from .tools import get_chitta_tools, get_core_extraction_tools
from .cards import derive_cards_from_child

logger = logging.getLogger(__name__)


class ChittaService:
    """
    Main service for Chitta conversations.

    Usage:
        service = ChittaService()
        response = await service.process_message(family_id, user_message)
    """

    # Configuration
    VERIFICATION_TURNS = [6, 9, 12, 18, 24, 36]  # Semantic verification intervals
    MAX_TOKENS = 4000  # For Hebrew responses

    # Time gap thresholds (hours)
    TIME_GAP_SAME_SESSION = 1
    TIME_GAP_SHORT_BREAK = 24
    TIME_GAP_RETURNING = 168  # 7 days

    def __init__(self, language: str = "he"):
        self.language = language
        self._unified = get_unified_state_service()
        self._llm = None  # Lazy initialization

    def _get_llm(self):
        """Lazy load LLM provider"""
        if self._llm is None:
            import os
            from app.services.llm.factory import create_llm_provider

            model = os.getenv("STRONG_LLM_MODEL", "gemini-2.0-flash-exp")
            provider = os.getenv("LLM_PROVIDER", "gemini")

            self._llm = create_llm_provider(
                provider_type=provider,
                model=model,
                use_enhanced=True  # Use enhanced provider for function calling
            )
        return self._llm

    async def process_message(
        self,
        family_id: str,
        user_message: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user message using TWO-PHASE architecture.

        Phase 1 - EXTRACTION (with functions):
        - LLM call with functions enabled
        - Model calls tools (update_child_understanding, capture_story, etc.)
        - Returns function calls, 0 chars text (EXPECTED!)
        - Process and save all function results

        Phase 2 - RESPONSE (without functions):
        - LLM call WITHOUT functions
        - Model generates conversational Hebrew response
        - This is what we show to the parent

        This matches standard function calling patterns and ensures reliable extraction.

        Args:
            family_id: Child/family identifier
            user_message: The parent's message
            user_id: Optional user identifier (defaults to family_id)

        Returns:
            Dict containing response, tool_calls, gestalt, artifacts_created, etc.
        """
        try:
            # 1. Get current state
            child = self._unified.get_child(family_id)
            session = await self._unified.get_or_create_session_async(family_id, user_id)

            # 2. Check for returning user BEFORE processing (time gap is accurate)
            returning_user_context = self._check_returning_user(session, child)
            if returning_user_context:
                logger.info(
                    f"⏰ Returning user: {returning_user_context['category']} "
                    f"({returning_user_context['days_since']:.1f} days)"
                )

            # 3. Build initial Gestalt (before user message added)
            gestalt = build_gestalt(child, session)

            # 4. Build extraction context for Phase 1 (compact, not full history)
            extraction_context = self._build_extraction_context(
                gestalt=gestalt,
                user_message=user_message,
                session=session
            )

            # =====================================================
            # PHASE 1: EXTRACTION (with functions)
            # =====================================================
            logger.info("🔧 Phase 1: Extraction (calling functions)")

            # Use reduced tool set to avoid Gemini schema complexity errors
            # Full toolset causes "too much branching" - core tools only for extraction
            tools = get_core_extraction_tools(gestalt)
            extraction_result = await self._extraction_phase(
                extraction_context=extraction_context,
                tools=tools,
                family_id=family_id,
                child=child,
                gestalt=gestalt,
            )

            tool_results = extraction_result["tool_results"]
            artifacts_created = extraction_result["artifacts_created"]

            logger.info(f"✅ Phase 1 complete: {len(tool_results)} tool calls processed")

            # =====================================================
            # PHASE 2: RESPONSE (without functions)
            # =====================================================
            logger.info("💬 Phase 2: Response generation (no functions)")

            # Rebuild gestalt with Phase 1 updates
            child = self._unified.get_child(family_id)
            session = await self._unified.get_or_create_session_async(family_id, user_id)

            # Add user message NOW (after Phase 1, before Phase 2)
            session.add_message("user", user_message)

            updated_gestalt = build_gestalt(child, session)

            # Build full system prompt for Phase 2
            # CRITICAL: Don't include tool descriptions since we're calling WITHOUT functions
            # Including tools in prompt but not in API causes MALFORMED_FUNCTION_CALL errors
            system_prompt = build_system_prompt(
                updated_gestalt,
                self.language,
                include_tools_description=False
            )

            # Inject returning user context if applicable
            if returning_user_context:
                system_prompt = self._inject_returning_user_context(
                    system_prompt, returning_user_context
                )

            # Inject tool results context (especially blocked actions)
            if tool_results:
                system_prompt = self._inject_tool_results_context(
                    system_prompt, tool_results, self.language
                )

            # Build full conversation history for Phase 2
            messages = self._build_messages(session, system_prompt)

            # Generate response WITHOUT functions (forces text response)
            response_text = await self._response_phase(
                messages=messages,
                temperature=0.7,
                max_tokens=self.MAX_TOKENS,
            )

            logger.info(f"✅ Phase 2 complete: {len(response_text)} chars")

            # Handle empty response
            if not response_text:
                logger.error("🔴 Phase 2 returned empty response!")
                response_text = self._get_error_response()

            # =====================================================
            # FINALIZE
            # =====================================================

            # Add assistant response to session
            session.add_message("assistant", response_text)

            # Persist state
            await self._unified._persist_session(session)

            # Check if reflection should run (background - deep processing)
            if session.needs_reflection():
                from .reflection import get_reflection_service
                reflection = get_reflection_service()
                await reflection.queue_conversation_reflection(family_id, session)
                session.mark_reflection_queued()
                await self._unified._persist_session(session)
                # Process in background
                asyncio.create_task(reflection.process_pending(family_id))
                logger.info(f"🧠 Queued background reflection (turn {session.turn_count})")

            # Check if semantic verification should run (background)
            should_verify = self._should_run_verification(session, updated_gestalt)
            if should_verify:
                asyncio.create_task(
                    self._run_verification_background(family_id, session.turn_count)
                )
                logger.info(f"🔍 Started background verification (turn {session.turn_count})")

            # Final gestalt
            final_gestalt = build_gestalt(
                self._unified.get_child(family_id),
                session
            )

            return {
                "response": response_text,
                "tool_calls": tool_results,
                "gestalt": final_gestalt.to_dict(),
                "artifacts_created": artifacts_created,
                "completeness": final_gestalt.completeness.score,
                "returning_user": returning_user_context,
                "architecture": "two_phase",
            }

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return {
                "response": self._get_error_response(),
                "tool_calls": [],
                "gestalt": None,
                "artifacts_created": [],
                "error": str(e),
            }

    def _build_messages(
        self,
        session: UserSession,
        system_prompt: str
    ) -> List[Dict[str, Any]]:
        """Build message list for LLM (Phase 2 - active window + memory)"""
        from app.services.llm.base import Message

        # Include memory context in system prompt if available
        enhanced_prompt = system_prompt
        if session.memory and self._has_useful_memory(session.memory):
            memory_context = self._build_memory_context(session.memory)
            enhanced_prompt = f"{system_prompt}\n\n{memory_context}"

        messages = [Message(role="system", content=enhanced_prompt)]

        # Use active window messages (sliding window architecture)
        context = session.get_context_for_llm()
        for msg in context:
            messages.append(Message(
                role=msg["role"],
                content=msg["content"]
            ))

        return messages

    def _has_useful_memory(self, memory) -> bool:
        """Check if memory has useful information to include."""
        if not memory:
            return False
        return bool(
            memory.parent_style or
            memory.vocabulary_preferences or
            memory.context_assets or
            memory.topics_discussed
        )

    def _build_memory_context(self, memory) -> str:
        """Build memory context block for system prompt."""
        parts = ["# Conversation Memory (distilled from previous conversations)"]

        if memory.parent_style:
            parts.append(f"**Parent's communication style**: {memory.parent_style}")

        if memory.emotional_patterns:
            parts.append(f"**Emotional patterns**: {memory.emotional_patterns}")

        if memory.vocabulary_preferences:
            parts.append(f"**Words they use**: {', '.join(memory.vocabulary_preferences[:10])}")

        if memory.context_assets:
            parts.append(f"**People/places mentioned**: {', '.join(memory.context_assets[:10])}")

        if memory.topics_discussed:
            deep_topics = [
                t.topic for t in memory.topics_discussed
                if t.depth in ["explored", "deep_dive"]
            ]
            if deep_topics:
                parts.append(f"**Topics we've covered deeply**: {', '.join(deep_topics[:5])}")

        if memory.rapport_notes:
            parts.append(f"**Relationship notes**: {memory.rapport_notes}")

        return "\n".join(parts)

    def _build_extraction_context(
        self,
        gestalt: Gestalt,
        user_message: str,
        session: UserSession
    ) -> str:
        """
        Build compact extraction context for Phase 1.

        Uses XML tags for structured context without full conversation history.
        This prevents MAX_TOKENS errors as conversation grows.
        """
        # What we already know
        known = get_what_we_know(gestalt)
        known_lines = []
        for key, value in known.items():
            if value:
                if isinstance(value, list):
                    known_lines.append(f"- {key}: {', '.join(str(v) for v in value)}")
                elif isinstance(value, dict):
                    known_lines.append(f"- {key}: {value}")
                else:
                    known_lines.append(f"- {key}: {str(value)[:100]}")

        known_text = "\n".join(known_lines) if known_lines else "(Nothing extracted yet)"

        # Get last assistant message for context
        last_chitta_message = None
        history = session.get_conversation_history(last_n=5)
        for msg in reversed(history):
            if msg["role"] == "assistant":
                last_chitta_message = msg["content"]
                break

        # Build context with XML tags
        context = f"""<already_extracted>
{known_text}
</already_extracted>"""

        # Add active hypotheses for hypothesis evolution
        active_hypotheses = gestalt.hypotheses.active_hypotheses
        if active_hypotheses:
            hypo_lines = []
            for h in active_hypotheses:
                hypo_id = h.get("id", "unknown")
                theory = h.get("theory", "")
                confidence = h.get("confidence", 0.5)
                evidence_count = h.get("evidence_count", 0)
                questions = h.get("questions_to_explore", [])

                hypo_text = f"- ID: {hypo_id} | Confidence: {confidence:.0%} | Evidence: {evidence_count}"
                hypo_text += f"\n  Theory: {theory[:100]}"
                if questions:
                    hypo_text += f"\n  Questions to explore: {'; '.join(questions[:3])}"
                hypo_lines.append(hypo_text)

            context += f"""

<active_hypotheses>
{chr(10).join(hypo_lines)}
</active_hypotheses>"""

        if last_chitta_message:
            context += f"""

<last_chitta_message>
{last_chitta_message[:500]}
</last_chitta_message>"""

        context += f"""

<parent_message>
{user_message}
</parent_message>"""

        return context

    async def _extraction_phase(
        self,
        extraction_context: str,
        tools: List[Dict[str, Any]],
        family_id: str,
        child: Child,
        gestalt: Gestalt,
    ) -> Dict[str, Any]:
        """
        Phase 1: EXTRACTION - LLM call with functions enabled.

        The model calls functions (update_child_understanding, etc.) and returns
        NO TEXT (0 chars). This is EXPECTED and NORMAL for function calling!

        Returns:
            Dict with tool_results and artifacts_created
        """
        from app.services.llm.base import Message
        from app.prompts.extraction_prompt import build_extraction_prompt

        # Build minimal extraction messages
        extraction_prompt = build_extraction_prompt()
        messages = [
            Message(role="system", content=extraction_prompt),
            Message(role="user", content=extraction_context)
        ]

        logger.info(f"📝 Phase 1 - Context: {len(extraction_context)} chars")

        # Call LLM with functions enabled
        llm = self._get_llm()
        llm_response = await llm.chat(
            messages=messages,
            functions=tools,
            temperature=0.0,  # Low temp for reliable extraction
            max_tokens=2000,  # Should be plenty for extraction
        )

        logger.info(
            f"📞 Phase 1 result: {len(llm_response.function_calls)} function calls, "
            f"{len(llm_response.content or '')} chars text"
        )

        # Process function calls
        tool_results = []
        artifacts_created = []

        for func_call in llm_response.function_calls:
            result = await self._process_tool_call(
                family_id=family_id,
                tool_name=func_call.name,
                tool_args=func_call.arguments,
                child=child,
                gestalt=gestalt,
            )
            tool_results.append({
                "tool": func_call.name,
                "arguments": func_call.arguments,
                "result": result,
            })

            if result.get("artifact_created"):
                artifacts_created.append(result["artifact_created"])

        return {
            "tool_results": tool_results,
            "artifacts_created": artifacts_created,
            "function_calls": llm_response.function_calls,
        }

    async def _response_phase(
        self,
        messages: List[Any],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """
        Phase 2: RESPONSE - LLM call WITHOUT functions.

        The model generates a natural Hebrew conversational response.
        NO functions = forces text response.

        CRITICAL: Disable thinking mode to prevent chain-of-thought
        leaking into user-facing responses.

        Returns:
            Hebrew text response
        """
        import re

        llm = self._get_llm()

        # Call LLM WITHOUT functions - forces text response
        llm_response = await llm.chat(
            messages=messages,
            functions=None,  # NO FUNCTIONS! This is the key!
            temperature=temperature,
            max_tokens=max_tokens,
            enable_thinking=False,  # Disable thinking for user-facing response
        )

        response_text = llm_response.content or ""

        # Clean response - remove any thinking/reasoning tags that leaked
        response_text = self._clean_response(response_text)

        logger.info(
            f"💬 Phase 2 result: {len(response_text)} chars, "
            f"{len(llm_response.function_calls)} function calls (should be 0)"
        )

        return response_text

    def _clean_response(self, text: str) -> str:
        """
        Remove internal thinking/reasoning tags from LLM response.

        Some LLMs (like Gemini) may include:
        - <thought> or <thinking> tags showing their reasoning
        - Accidental function call syntax when function calling mechanism fails
        """
        import re

        if not text:
            return text

        # Remove internal reasoning tags
        reasoning_tags = r'<(?:thought|thinking|start_action|end_action|action)>.*?</(?:thought|thinking|start_action|end_action|action)>'
        cleaned = re.sub(reasoning_tags, '', text, flags=re.DOTALL | re.IGNORECASE)

        # Remove standalone malformed tags
        standalone_tags = r'</?(?:thought|thinking|start_action|end_action|action)>'
        cleaned = re.sub(standalone_tags, '', cleaned, flags=re.IGNORECASE)

        # Remove accidental function call syntax
        cleaned = re.sub(r'\(<[^>]+>\).*?</[^>]+>\)', '', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'\(<[^>]+>\)|</[^>]+>\)', '', cleaned)

        return cleaned.strip()

    async def _process_tool_call(
        self,
        family_id: str,
        tool_name: str,
        tool_args: Dict[str, Any],
        child: Child,
        gestalt: Gestalt,
    ) -> Dict[str, Any]:
        """
        Process a single tool call.

        This is where tools become REAL actions.
        """
        logger.info(f"Processing tool: {tool_name} with args: {tool_args}")

        if tool_name in ("update_child_understanding", "extract_interview_data"):
            return await self._handle_update_understanding(family_id, tool_args)

        elif tool_name == "capture_story":
            return await self._handle_capture_story(family_id, tool_args)

        elif tool_name == "detect_milestone":
            return await self._handle_detect_milestone(family_id, tool_args, gestalt)

        elif tool_name == "generate_video_guidelines":
            # DEPRECATED: No tool exposes this name. Use request_video_observation instead.
            logger.warning("DEPRECATED: generate_video_guidelines called - use request_video_observation instead")
            return await self._handle_generate_guidelines(family_id, tool_args, gestalt)

        elif tool_name == "generate_parent_report":
            # DEPRECATED: No tool exposes this name. Handler uses old baseline_interview_summary flow.
            logger.warning("DEPRECATED: generate_parent_report called - this uses the old artifact flow")
            return await self._handle_generate_report(family_id, tool_args, gestalt)

        elif tool_name == "request_video_observation":
            return await self._handle_request_video(family_id, tool_args, gestalt)

        elif tool_name == "analyze_video":
            return await self._handle_analyze_video(family_id, tool_args, gestalt)

        elif tool_name == "ask_developmental_question":
            return self._handle_developmental_question(tool_args, gestalt)

        elif tool_name == "ask_about_app":
            return self._handle_app_question(tool_args, gestalt)

        elif tool_name == "form_hypothesis":
            return await self._handle_form_hypothesis(family_id, tool_args, child)

        elif tool_name == "note_pattern":
            return await self._handle_note_pattern(family_id, tool_args, child)

        elif tool_name == "update_hypothesis_evidence":
            return await self._handle_update_hypothesis_evidence(family_id, tool_args, child)

        # === Exploration Cycle Tools ===
        elif tool_name == "start_exploration":
            return await self._handle_start_exploration(family_id, tool_args, child)

        elif tool_name == "escalate_to_video":
            return await self._handle_escalate_to_video(family_id, tool_args, child)

        elif tool_name == "complete_exploration_cycle":
            return await self._handle_complete_exploration(family_id, tool_args, child)

        elif tool_name == "add_exploration_question":
            return await self._handle_add_exploration_question(family_id, tool_args, child)

        elif tool_name == "record_question_response":
            return await self._handle_record_question_response(family_id, tool_args, child)

        elif tool_name == "add_video_scenario":
            return await self._handle_add_video_scenario(family_id, tool_args, child)

        elif tool_name == "generate_synthesis":
            return await self._handle_generate_synthesis(family_id, tool_args, gestalt)

        else:
            logger.warning(f"Unknown tool: {tool_name}")
            return {"status": "unknown_tool", "tool": tool_name}

    async def _handle_update_understanding(
        self,
        family_id: str,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update child's developmental data and create evidence for hypotheses"""
        # Filter out empty values
        update_data = {k: v for k, v in args.items() if v is not None and v != ""}

        if not update_data:
            return {"status": "no_updates"}

        # Update via unified service
        self._unified.update_extracted_data(family_id, update_data)

        # Create evidence from significant extracted data
        # Evidence feeds into hypotheses during reflection
        evidence_created = await self._create_evidence_from_extraction(family_id, update_data)

        # Recalculate completeness
        new_completeness = self._unified.calculate_completeness(family_id)

        logger.info(f"Updated understanding: {list(update_data.keys())}, completeness: {new_completeness:.0%}")

        return {
            "status": "updated",
            "fields_updated": list(update_data.keys()),
            "new_completeness": new_completeness,
            "evidence_created": evidence_created,
        }

    async def _create_evidence_from_extraction(
        self,
        family_id: str,
        update_data: Dict[str, Any]
    ) -> int:
        """
        Create Evidence objects from extracted conversation data.

        Evidence is created for significant observations that can feed
        into hypothesis testing during reflection.
        """
        from app.models.understanding import Evidence

        child = self._unified.get_child(family_id)
        evidence_count = 0

        # Map extraction fields to evidence domains
        domain_mapping = {
            "concerns": "concerns",
            "primary_concerns": "concerns",
            "concern_details": "concerns",
            "strengths": "strengths",
            "developmental_history": "history",
            "family_context": "family",
            "daily_routines": "daily_life",
        }

        for field, domain in domain_mapping.items():
            if field not in update_data:
                continue

            value = update_data[field]
            if not value:
                continue

            # Create evidence from this field
            if isinstance(value, list):
                for item in value:
                    evidence = Evidence(
                        source="conversation",
                        content=f"[{field}] {item}",
                        domain=domain,
                    )
                    # Add evidence to any matching active hypotheses
                    for hypothesis in child.active_hypotheses():
                        if hypothesis.domain == domain or domain in hypothesis.theory.lower():
                            hypothesis.add_evidence(evidence, "neutral")
                            evidence_count += 1
            else:
                evidence = Evidence(
                    source="conversation",
                    content=f"[{field}] {value}",
                    domain=domain,
                )
                # Add evidence to any matching active hypotheses
                for hypothesis in child.active_hypotheses():
                    if hypothesis.domain == domain or domain in hypothesis.theory.lower():
                        hypothesis.add_evidence(evidence, "neutral")
                        evidence_count += 1

        if evidence_count > 0:
            # Persist child with updated hypotheses
            from app.services.child_service import get_child_service
            await get_child_service().save_child(family_id)
            logger.debug(f"Created {evidence_count} evidence items from extraction")

        return evidence_count

    async def _handle_capture_story(
        self,
        family_id: str,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Capture a story/observation as journal entry"""
        story_content = args.get("story_content")
        if not story_content:
            return {"status": "no_content"}

        # Create journal entry
        from uuid import uuid4
        entry = JournalEntry(
            id=str(uuid4()),
            content=story_content,
            context=args.get("context"),
            themes=args.get("themes", []),
            sentiment=args.get("sentiment"),
            timestamp=datetime.now(),
        )

        # Add to child via unified service
        child = self._unified.get_child(family_id)
        child.add_journal_entry(entry)

        # Persist child
        from app.services.child_service import get_child_service
        get_child_service().save_child(child)

        logger.info(f"Captured story: {story_content[:50]}...")

        return {
            "status": "captured",
            "entry_id": entry.id,
            "themes": entry.themes,
        }

    async def _handle_detect_milestone(
        self,
        family_id: str,
        args: Dict[str, Any],
        gestalt: Gestalt
    ) -> Dict[str, Any]:
        """Handle milestone detection"""
        milestone_type = args.get("milestone_type")
        notes = args.get("notes", "")

        logger.info(f"Milestone detected: {milestone_type} - {notes}")

        # Could trigger UI updates or analytics here
        # For now, just log it

        return {
            "status": "recorded",
            "milestone": milestone_type,
            "notes": notes,
        }

    async def _handle_form_hypothesis(
        self,
        family_id: str,
        args: Dict[str, Any],
        child: Child
    ) -> Dict[str, Any]:
        """
        Form a working hypothesis about the child.

        Hypotheses are theories held lightly that guide exploration.
        Auto-creates or links to an exploration cycle for hypothesis testing.
        """
        from app.models.understanding import Hypothesis, Evidence
        from app.models.exploration import ExplorationCycle, ConversationMethod

        theory = args.get("theory")
        if not theory:
            return {"status": "no_theory"}

        source = args.get("source", "observation")
        source_details = args.get("source_details")

        # Determine domain from related_domains if provided
        related_domains = args.get("related_domains", [])
        domain = related_domains[0] if related_domains else "general"

        # Get questions to explore
        questions_to_explore = args.get("questions_to_explore", [])

        # Create hypothesis
        hypothesis = Hypothesis(
            theory=theory,
            domain=domain,
            source=source,
            source_details=source_details,
            questions_to_explore=questions_to_explore,
            status="forming",
            confidence=0.5,
        )

        # Add supporting evidence as initial evidence
        supporting = args.get("supporting_evidence", [])
        for evidence_text in supporting:
            evidence = Evidence(
                source="conversation",
                content=evidence_text,
                domain=domain,
            )
            hypothesis.add_evidence(evidence, "supports")

        # Note contradicting evidence (doesn't add as evidence yet, just lowers confidence)
        contradicting = args.get("contradicting_evidence", [])
        if contradicting:
            # Lower initial confidence if there's contradicting evidence
            hypothesis.confidence = max(0.3, hypothesis.confidence - 0.1 * len(contradicting))

        # Add to child's understanding
        child.add_hypothesis(hypothesis)

        # Auto-create or link to exploration cycle
        cycle_id = None
        current_cycle = child.current_cycle()

        if current_cycle and current_cycle.status == "active":
            # Add this hypothesis to the current active cycle
            if hypothesis.id not in current_cycle.hypothesis_ids:
                current_cycle.hypothesis_ids.append(hypothesis.id)
            cycle_id = current_cycle.id
            logger.debug(f"Added hypothesis {hypothesis.id} to existing cycle {cycle_id}")
        else:
            # Create a new exploration cycle for this hypothesis
            cycle = ExplorationCycle(
                hypothesis_ids=[hypothesis.id],
                focus_description=f"Exploring: {theory[:100]}",
                status="active",
            )
            # Initialize conversation method with questions if provided
            if questions_to_explore:
                cycle.conversation_method = ConversationMethod()
                for q in questions_to_explore:
                    cycle.conversation_method.add_question(q)
            child.add_cycle(cycle)
            cycle_id = cycle.id
            logger.debug(f"Created new exploration cycle {cycle_id} for hypothesis {hypothesis.id}")

        # Persist child
        from app.services.child_service import get_child_service
        await get_child_service().save_child(family_id)

        logger.info(
            f"💡 Hypothesis formed: {theory[:50]}... "
            f"(source={source}, domain={domain}, confidence={hypothesis.confidence:.0%}, cycle={cycle_id})"
        )

        return {
            "status": "formed",
            "hypothesis_id": hypothesis.id,
            "theory": theory,
            "domain": domain,
            "source": source,
            "confidence": hypothesis.confidence,
            "evidence_count": len(hypothesis.evidence),
            "questions_to_explore": args.get("questions_to_explore", []),
            "exploration_cycle_id": cycle_id,
        }

    async def _handle_note_pattern(
        self,
        family_id: str,
        args: Dict[str, Any],
        child: Child
    ) -> Dict[str, Any]:
        """
        Note a pattern emerging across observations.

        Patterns connect scattered observations into themes.
        """
        from app.models.understanding import Pattern

        theme = args.get("theme")
        if not theme:
            return {"status": "no_theme"}

        observations = args.get("observations", [])
        domains_involved = args.get("domains_involved", [])
        confidence = args.get("confidence", 0.5)

        # Create pattern
        pattern = Pattern(
            theme=theme,
            description=f"Observations: {'; '.join(observations)}",
            related_hypotheses=[],  # Can be linked to hypotheses later
            confidence=confidence,
            source="conversation",
        )

        # Add to child's understanding
        child.add_pattern(pattern)

        # Persist child
        from app.services.child_service import get_child_service
        await get_child_service().save_child(family_id)

        logger.info(
            f"🔗 Pattern noted: {theme} "
            f"(observations={len(observations)}, domains={domains_involved})"
        )

        return {
            "status": "noted",
            "pattern_id": pattern.id,
            "theme": theme,
            "observations_count": len(observations),
            "domains": domains_involved,
            "confidence": confidence,
        }

    async def _handle_update_hypothesis_evidence(
        self,
        family_id: str,
        args: Dict[str, Any],
        child: Child
    ) -> Dict[str, Any]:
        """
        Update hypotheses with evidence from conversation.

        This is the KEY mechanism for hypothesis evolution:
        1. LLM explicitly links parent's response to hypotheses
        2. Direction (supports/contradicts) determines confidence change
        3. Auto-resolution when thresholds are crossed
        """
        from app.models.understanding import Evidence

        evidence_summary = args.get("evidence_summary")
        hypothesis_effects = args.get("hypothesis_effects", [])
        source_question = args.get("source_question")

        if not evidence_summary or not hypothesis_effects:
            return {"status": "no_evidence"}

        results = []
        resolved_hypotheses = []

        for effect in hypothesis_effects:
            hypothesis_id = effect.get("hypothesis_id")
            direction = effect.get("direction", "neutral")
            reasoning = effect.get("reasoning", "")

            if not hypothesis_id:
                continue

            # Find the hypothesis
            hypothesis = child.understanding.get_hypothesis(hypothesis_id)
            if not hypothesis:
                logger.warning(f"Hypothesis not found: {hypothesis_id}")
                results.append({
                    "hypothesis_id": hypothesis_id,
                    "status": "not_found"
                })
                continue

            # Create evidence
            evidence = Evidence(
                source="conversation",
                content=f"{evidence_summary}" + (f" ({reasoning})" if reasoning else ""),
                domain=hypothesis.domain,
            )

            # Add to hypothesis with direction
            old_confidence = hypothesis.confidence
            old_status = hypothesis.status
            hypothesis.add_evidence(evidence, direction)

            # Auto-resolution based on confidence thresholds
            resolution_result = None
            if hypothesis.confidence >= 0.85 and hypothesis.status != "resolved":
                hypothesis.resolve("confirmed", f"High confidence ({hypothesis.confidence:.0%}) based on evidence")
                resolution_result = "confirmed"
                resolved_hypotheses.append({
                    "id": hypothesis_id,
                    "theory": hypothesis.theory,
                    "resolution": "confirmed",
                    "final_confidence": hypothesis.confidence
                })
            elif hypothesis.confidence <= 0.25 and hypothesis.status != "resolved":
                hypothesis.resolve("rejected", f"Low confidence ({hypothesis.confidence:.0%}) based on contradicting evidence")
                resolution_result = "rejected"
                resolved_hypotheses.append({
                    "id": hypothesis_id,
                    "theory": hypothesis.theory,
                    "resolution": "rejected",
                    "final_confidence": hypothesis.confidence
                })

            results.append({
                "hypothesis_id": hypothesis_id,
                "direction": direction,
                "old_confidence": old_confidence,
                "new_confidence": hypothesis.confidence,
                "old_status": old_status,
                "new_status": hypothesis.status,
                "resolution": resolution_result,
            })

            logger.info(
                f"📊 Hypothesis {hypothesis_id[:8]}: {direction} → "
                f"{old_confidence:.0%} → {hypothesis.confidence:.0%} "
                f"(status: {old_status} → {hypothesis.status})"
            )

        # Persist child with updated hypotheses
        from app.services.child_service import get_child_service
        await get_child_service().save_child(family_id)

        return {
            "status": "updated",
            "evidence_summary": evidence_summary,
            "source_question": source_question,
            "hypotheses_updated": len(results),
            "results": results,
            "resolved_hypotheses": resolved_hypotheses,
        }

    async def _handle_generate_guidelines(
        self,
        family_id: str,
        args: Dict[str, Any],
        gestalt: Gestalt
    ) -> Dict[str, Any]:
        """
        DEPRECATED: This handler is dead code - no tool exposes 'generate_video_guidelines'.

        The active flow uses `request_video_observation` tool which calls `_handle_request_video`
        and uses `generate_video_guidelines_from_gestalt` (hypotheses-based approach).

        This old handler uses the baseline_interview_summary → baseline_video_guidelines chain
        which is no longer the active flow.

        Original docstring:
        Trigger video guidelines generation.
        Wu Wei: Guidelines require interview_summary artifact first.
        The artifact chain is:
        1. interview_summary (extracted from conversation)
        2. video_guidelines (personalized from interview_summary)
        """

        # Check prerequisites
        if gestalt.completeness.score < 0.4:
            return {
                "status": "blocked",
                "reason": "insufficient_understanding",
                "completeness": gestalt.completeness.score,
            }

        if gestalt.filming_preference == "report_only":
            return {
                "status": "blocked",
                "reason": "parent_chose_report_only",
            }

        if gestalt.artifacts.has_video_guidelines:
            return {
                "status": "already_exists",
                "artifact_id": "baseline_video_guidelines",
            }

        # Trigger actual generation via artifact service
        try:
            from app.services.artifact_generation_service import get_artifact_generation_service
            from app.services.child_service import get_child_service

            artifact_service = get_artifact_generation_service()
            child_service = get_child_service()
            child = child_service.get_child(family_id)

            # Build session_data in the format artifact_service expects
            session = await self._unified.get_or_create_session_async(family_id)
            session_data = self._build_session_data_for_artifacts(child, session, gestalt)

            # First, ensure interview_summary exists (prerequisite for guidelines)
            interview_summary_id = "baseline_interview_summary"
            if not child.has_artifact(interview_summary_id):
                logger.info("📝 Generating interview summary first (prerequisite for guidelines)")
                interview_artifact = await artifact_service.generate_artifact(
                    artifact_id=interview_summary_id,
                    session_data=session_data,
                )
                if interview_artifact.status == "ready":
                    child.add_artifact(interview_artifact)
                    child_service.save_child(child)
                    # Update session_data with new artifact
                    session_data = self._build_session_data_for_artifacts(child, session, gestalt)
                else:
                    logger.error(f"Failed to generate interview summary: {interview_artifact.error}")
                    return {
                        "status": "error",
                        "error": f"Could not generate prerequisite: {interview_artifact.error}",
                    }

            # Now generate video guidelines
            artifact = await artifact_service.generate_artifact(
                artifact_id="baseline_video_guidelines",
                session_data=session_data,
                focus_areas=args.get("focus_areas", []),
            )

            if artifact.status == "ready":
                # Save artifact to child
                child.add_artifact(artifact)
                child_service.save_child(child)

            return {
                "status": "generated" if artifact.status == "ready" else "error",
                "artifact_created": "baseline_video_guidelines" if artifact.status == "ready" else None,
                "artifact_id": artifact.artifact_id if artifact else None,
                "error": artifact.error if artifact.status == "error" else None,
            }

        except Exception as e:
            logger.error(f"Failed to generate guidelines: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
            }

    async def _handle_generate_report(
        self,
        family_id: str,
        args: Dict[str, Any],
        gestalt: Gestalt
    ) -> Dict[str, Any]:
        """
        DEPRECATED: This handler is dead code - no tool exposes 'generate_parent_report'.

        This uses the old baseline_interview_summary artifact chain which is
        no longer the active approach.

        Original docstring:
        Trigger parent report generation.
        Wu Wei: Parent report requires professional_report artifact first.
        The full artifact chain is:
        1. interview_summary
        2. video_guidelines
        3. video_analysis (per video)
        4. professional_report (synthesis)
        5. parent_report (simplified version)

        However, we can generate a preliminary parent report even without
        video analysis if the conversation is rich enough.
        """

        # Check prerequisites
        if gestalt.completeness.score < 0.6:
            return {
                "status": "blocked",
                "reason": "insufficient_understanding",
                "completeness": gestalt.completeness.score,
            }

        if gestalt.artifacts.has_parent_report:
            return {
                "status": "already_exists",
                "artifact_id": "baseline_parent_report",
            }

        # Trigger actual generation
        try:
            from app.services.artifact_generation_service import get_artifact_generation_service
            from app.services.child_service import get_child_service

            artifact_service = get_artifact_generation_service()
            child_service = get_child_service()
            child = child_service.get_child(family_id)

            # Build session_data in the format artifact_service expects
            session = await self._unified.get_or_create_session_async(family_id)
            session_data = self._build_session_data_for_artifacts(child, session, gestalt)

            # Check if professional report exists, if not we'll generate parent report directly
            # (The artifact service will handle the dependency chain)
            artifact = await artifact_service.generate_artifact(
                artifact_id="baseline_parent_report",
                session_data=session_data,
                include_recommendations=args.get("include_recommendations", True),
                focus_sections=args.get("focus_sections", []),
            )

            if artifact.status == "ready":
                # Save artifact to child
                child.add_artifact(artifact)
                child_service.save_child(child)

            return {
                "status": "generated" if artifact.status == "ready" else "error",
                "artifact_created": "baseline_parent_report" if artifact.status == "ready" else None,
                "artifact_id": artifact.artifact_id if artifact else None,
                "error": artifact.error if artifact.status == "error" else None,
            }

        except Exception as e:
            logger.error(f"Failed to generate report: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
            }

    async def _handle_request_video(
        self,
        family_id: str,
        args: Dict[str, Any],
        gestalt: Gestalt
    ) -> Dict[str, Any]:
        """
        Handle video observation request - generates personalized guidelines from Gestalt.

        This is called when the LLM determines video observation would help test hypotheses.
        It generates personalized filming guidelines and creates an artifact that appears
        in the child's Space. A context card guides the parent to view instructions.

        Args:
            family_id: Family identifier
            args: Tool arguments (hypothesis_ids_to_test, patterns_to_explore, include_strength_baseline)
            gestalt: Current Gestalt state

        Returns:
            Dict with status, artifact info, and action for UI
        """
        import json

        # Check if parent chose report-only path
        if gestalt.filming_preference == "report_only":
            return {
                "status": "blocked",
                "reason": "parent_chose_report_only",
            }

        # Get child data for guideline generation
        from app.services.child_service import get_child_service
        child_service = get_child_service()
        child = child_service.get_or_create_child(family_id)

        # Get artifact generation service
        from app.services.artifact_generation_service import ArtifactGenerationService
        artifact_service = ArtifactGenerationService()

        try:
            # Generate guidelines from Gestalt
            scenarios_needed = args.get("scenarios_needed", 1)
            include_baseline = args.get("include_strength_baseline", False)
            hypothesis_ids = args.get("hypothesis_ids_to_test", [])
            logger.info(f"🎬 Generating video guidelines from Gestalt for {family_id} (scenarios={scenarios_needed}, baseline={include_baseline})")
            guidelines = await artifact_service.generate_video_guidelines_from_gestalt(
                child=child,
                scenarios_needed=scenarios_needed,
                hypotheses_to_test=hypothesis_ids,
                patterns_to_explore=args.get("patterns_to_explore"),
                include_strength_baseline=include_baseline,
            )

            # Store as artifact using proper Artifact model
            from app.models.artifact import Artifact
            from app.models.exploration import CycleArtifact
            artifact_id = "video_guidelines_from_gestalt"
            artifact = Artifact(
                artifact_id=artifact_id,
                artifact_type="filming_guidelines",
                status="ready",
                content=json.dumps(guidelines, ensure_ascii=False),
                content_format="json",
            )
            artifact.ready_at = datetime.now()

            # Store in the current exploration cycle (creates one if needed)
            cycle_id = None
            current_cycle = child.current_cycle()
            if not current_cycle:
                # Create a cycle for video exploration
                from app.models.exploration import ExplorationCycle
                current_cycle = ExplorationCycle(
                    hypothesis_ids=hypothesis_ids,
                    focus_description="Video observation exploration",
                    status="evidence_gathering",
                )
                child.add_cycle(current_cycle)

            # Create a CycleArtifact for the cycle
            cycle_artifact = CycleArtifact(
                id=artifact_id,
                type="video_guidelines",
                content=guidelines,
                status="ready",
                related_hypothesis_ids=hypothesis_ids,
                expected_videos=len(guidelines.get("scenarios", [])),
            )
            cycle_artifact.mark_ready()
            current_cycle.add_artifact(cycle_artifact)
            # Transition cycle to evidence_gathering
            if current_cycle.status != "evidence_gathering":
                current_cycle.transition_to("evidence_gathering")
            cycle_id = current_cycle.id
            logger.debug(f"Added guidelines artifact to cycle {cycle_id}")

            # Save child
            await child_service.save_child(family_id)

            logger.info(f"✅ Video guidelines generated: {len(guidelines.get('scenarios', []))} scenarios (cycle={cycle_id})")

            # Return success with action to show context card
            return {
                "status": "generated",
                "artifact_id": artifact_id,
                "scenarios_count": len(guidelines.get("scenarios", [])),
                "child_name": guidelines.get("child_name"),
                # This triggers the frontend to show a context card
                "action": {
                    "type": "show_context_card",
                    "card": {
                        "id": "video_guidelines_ready",
                        "type": "artifact_ready",
                        "title": "הנחיות צילום מוכנות",
                        "message": "הכנתי הנחיות צילום מותאמות אישית. תוכלו לצפות בהן במרחב.",
                        "primary_action": {
                            "label": "צפייה בהנחיות",
                            "target": "filming_guidelines",
                            "artifact_id": artifact_id,
                        },
                        "secondary_action": {
                            "label": "העלאת סרטון",
                            "target": "video_upload",
                        },
                    },
                },
            }

        except Exception as e:
            logger.error(f"❌ Failed to generate video guidelines: {e}", exc_info=True)
            return {
                "status": "error",
                "reason": str(e),
            }

    async def _handle_analyze_video(
        self,
        family_id: str,
        args: Dict[str, Any],
        gestalt: Gestalt
    ) -> Dict[str, Any]:
        """
        Trigger video analysis for an uploaded video.

        Wu Wei: Video analysis uses the comprehensive DSM-5 framework
        from video_analysis_prompt.py and produces structured clinical
        observations in video_analysis_schema.py format.
        """

        # Check prerequisites
        if gestalt.observations.pending_video_count == 0:
            return {
                "status": "blocked",
                "reason": "no_pending_videos",
                "video_count": gestalt.observations.video_count,
                "analyzed_count": gestalt.observations.analyzed_video_count,
            }

        if not gestalt.artifacts.has_video_guidelines:
            return {
                "status": "blocked",
                "reason": "no_guidelines",
                "message": "Video guidelines are needed to provide context for analysis",
            }

        try:
            from app.services.video_analysis_service import VideoAnalysisService
            from app.services.child_service import get_child_service

            video_service = VideoAnalysisService()
            child_service = get_child_service()
            child = child_service.get_child(family_id)

            # Get specific video or next pending video
            video_id = args.get("video_id")
            if video_id:
                video = child.get_video(video_id)
            else:
                pending_videos = child.get_videos_pending_analysis()
                video = pending_videos[0] if pending_videos else None

            if not video:
                return {
                    "status": "error",
                    "error": "No video found to analyze",
                }

            # Get video guidelines for analyst context
            guidelines_artifact = child.get_artifact("baseline_video_guidelines")
            analyst_context = {}
            if guidelines_artifact:
                import json
                try:
                    guidelines_content = guidelines_artifact.get("content", "{}")
                    if isinstance(guidelines_content, str):
                        guidelines_data = json.loads(guidelines_content)
                    else:
                        guidelines_data = guidelines_content
                    analyst_context = guidelines_data.get("analyst_context", {})
                except json.JSONDecodeError:
                    pass

            # Build child data for analysis
            child_data = {
                "name": gestalt.identity.name or "Unknown",
                "age_years": int(gestalt.identity.age) if gestalt.identity.age else None,
                "age_months": int((gestalt.identity.age % 1) * 12) if gestalt.identity.age else None,
                "gender": gestalt.identity.gender,
            }

            # Build extracted data (clinical context)
            extracted_data = {
                "primary_concerns": gestalt.concerns.primary_areas,
                "concern_details": gestalt.concerns.details,
                "strengths": gestalt.understanding.strengths,
                "developmental_history": gestalt.understanding.developmental_history,
            }

            # Perform analysis
            logger.info(f"🎥 Analyzing video: {video.video_id}")
            artifact = await video_service.analyze_video(
                video_path=video.file_path,
                child_data=child_data,
                extracted_data=extracted_data,
                analyst_context=analyst_context,
                video_id=video.video_id,
            )

            if artifact.status == "ready":
                # Mark video as analyzed and save artifact
                video.mark_analyzed(artifact.artifact_id)
                child.add_artifact(artifact)
                child_service.save_child(child)

                return {
                    "status": "analyzed",
                    "artifact_created": artifact.artifact_id,
                    "video_id": video.video_id,
                }
            else:
                return {
                    "status": "error",
                    "error": artifact.error,
                    "video_id": video.video_id,
                }

        except Exception as e:
            logger.error(f"Failed to analyze video: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
            }

    def _handle_developmental_question(
        self,
        args: Dict[str, Any],
        gestalt: Gestalt
    ) -> Dict[str, Any]:
        """Handle developmental question - just categorize it"""
        return {
            "status": "categorized",
            "topic": args.get("question_topic"),
            "relates_to_child": args.get("relates_to_child", True),
            "context": {
                "child_name": gestalt.identity.name,
                "concerns": gestalt.concerns.primary_areas,
            }
        }

    def _handle_app_question(
        self,
        args: Dict[str, Any],
        gestalt: Gestalt
    ) -> Dict[str, Any]:
        """Handle app question - provide context for response"""
        topic = args.get("help_topic")

        # Provide relevant context based on topic
        context = {}

        if topic in ["where_to_find_guidelines", "view_guidelines"]:
            context["has_guidelines"] = gestalt.artifacts.has_video_guidelines
            if gestalt.artifacts.has_video_guidelines:
                context["location"] = "The guidelines are in the 'Documents' section"

        elif topic in ["where_to_find_report", "view_report"]:
            context["has_report"] = gestalt.artifacts.has_parent_report
            if gestalt.artifacts.has_parent_report:
                context["location"] = "The report is in the 'Documents' section"

        elif topic == "how_to_upload_video":
            context["has_guidelines"] = gestalt.artifacts.has_video_guidelines
            context["videos_uploaded"] = gestalt.observations.video_count

        elif topic == "next_steps":
            context["completeness"] = gestalt.completeness.level
            context["available_artifacts"] = gestalt.artifacts.available_artifacts()

        return {
            "status": "context_provided",
            "topic": topic,
            "context": context,
        }

    # === Exploration Cycle Handlers ===

    async def _handle_start_exploration(
        self,
        family_id: str,
        args: Dict[str, Any],
        child: Child
    ) -> Dict[str, Any]:
        """
        Start an exploration cycle to test hypotheses.

        An exploration cycle organizes hypothesis testing through
        conversation and/or video methods.
        """
        from app.models.exploration import (
            ExplorationCycle, ConversationMethod, VideoMethod,
            ConversationQuestion, VideoScenario
        )

        goal = args.get("exploration_goal")
        if not goal:
            return {"status": "error", "error": "No exploration goal provided"}

        hypothesis_ids = args.get("hypothesis_ids", [])
        initial_method = args.get("initial_method", "conversation")

        # Create the exploration cycle
        cycle = ExplorationCycle(
            hypothesis_ids=hypothesis_ids,
            focus_description=goal,
            status="active",
        )

        # Initialize methods based on initial_method
        if initial_method in ("conversation", "both"):
            questions = args.get("conversation_questions", [])
            cycle.conversation_method = ConversationMethod()
            for q in questions:
                cycle.conversation_method.add_question(q.get("question", ""))

        if initial_method in ("video", "both"):
            scenarios = args.get("video_scenarios", [])
            cycle.video_method = VideoMethod()
            for s in scenarios:
                scenario = VideoScenario(
                    title=s.get("scenario", ""),
                    what_to_film=s.get("scenario", ""),
                    target_hypothesis=s.get("target_hypothesis_id", ""),
                    what_we_hope_to_learn=s.get("why_we_want_to_see", ""),
                    focus_points=s.get("focus_points", []),
                )
                cycle.video_method.add_scenario(scenario)
            # If video method is active, transition to evidence_gathering
            if scenarios:
                cycle.transition_to("evidence_gathering")

        # Add cycle to child
        child.add_cycle(cycle)

        # Persist child
        from app.services.child_service import get_child_service
        await get_child_service().save_child(family_id)

        logger.info(
            f"🔬 Exploration cycle started: {goal[:50]}... "
            f"(method={initial_method}, hypotheses={len(hypothesis_ids)})"
        )

        return {
            "status": "started",
            "cycle_id": cycle.id,
            "goal": goal,
            "method": initial_method,
            "hypothesis_count": len(hypothesis_ids),
            "questions_count": len(args.get("conversation_questions", [])),
            "scenarios_count": len(args.get("video_scenarios", [])),
        }

    async def _handle_escalate_to_video(
        self,
        family_id: str,
        args: Dict[str, Any],
        child: Child
    ) -> Dict[str, Any]:
        """
        Add video method to the current exploration cycle.

        Called when conversation alone can't answer what we're wondering.
        """
        from app.models.exploration import VideoMethod, VideoScenario

        # Get current active cycle
        cycle = child.current_cycle()
        if not cycle:
            return {
                "status": "error",
                "error": "No active exploration cycle to escalate",
            }

        why_needed = args.get("why_video_needed", "")
        scenarios_data = args.get("scenarios", [])

        if not scenarios_data:
            return {
                "status": "error",
                "error": "No scenarios provided for video escalation",
            }

        # Create or update video method
        if not cycle.video_method:
            cycle.video_method = VideoMethod()

        for s in scenarios_data:
            scenario = VideoScenario(
                title=s.get("scenario", "")[:50],
                what_to_film=s.get("scenario", ""),
                target_hypothesis=s.get("target_hypothesis_id", ""),
                what_we_hope_to_learn=s.get("why_we_want_to_see", ""),
                focus_points=s.get("focus_points", []),
            )
            cycle.video_method.add_scenario(scenario)

        # Transition to evidence_gathering
        cycle.transition_to("evidence_gathering")

        # Persist child
        from app.services.child_service import get_child_service
        await get_child_service().save_child(family_id)

        logger.info(
            f"📹 Exploration escalated to video: {why_needed[:50]}... "
            f"(cycle={cycle.id}, scenarios={len(scenarios_data)})"
        )

        return {
            "status": "escalated",
            "cycle_id": cycle.id,
            "why_needed": why_needed,
            "scenarios_count": len(scenarios_data),
            "cycle_status": cycle.status,
        }

    async def _handle_complete_exploration(
        self,
        family_id: str,
        args: Dict[str, Any],
        child: Child
    ) -> Dict[str, Any]:
        """
        Complete the current exploration cycle with learnings.

        Captures what we learned and updates hypotheses accordingly.
        """
        from app.models.understanding import PendingInsight

        # Get current active cycle
        cycle = child.current_cycle()
        if not cycle:
            return {
                "status": "error",
                "error": "No active exploration cycle to complete",
            }

        what_we_learned = args.get("what_we_learned", "")
        hypotheses_supported = args.get("hypotheses_supported", [])
        hypotheses_contradicted = args.get("hypotheses_contradicted", [])
        new_hypotheses = args.get("new_hypotheses", [])
        remaining_questions = args.get("remaining_questions", [])

        # Update hypotheses based on results
        for hyp_id in hypotheses_supported:
            hypothesis = child.understanding.get_hypothesis(hyp_id)
            if hypothesis:
                hypothesis.confidence = min(1.0, hypothesis.confidence + 0.15)
                if hypothesis.confidence >= 0.85:
                    hypothesis.resolve("confirmed", f"Supported by exploration cycle {cycle.id}")

        for hyp_id in hypotheses_contradicted:
            hypothesis = child.understanding.get_hypothesis(hyp_id)
            if hypothesis:
                hypothesis.confidence = max(0.0, hypothesis.confidence - 0.2)
                if hypothesis.confidence <= 0.25:
                    hypothesis.resolve("rejected", f"Contradicted by exploration cycle {cycle.id}")

        # Create pending insight from learnings
        if what_we_learned:
            insight = PendingInsight(
                content=what_we_learned,
                source="exploration_cycle",
                related_hypotheses=cycle.hypothesis_ids,
                importance="high" if hypotheses_supported or hypotheses_contradicted else "medium",
            )
            child.understanding.add_insight(insight)

        # Mark cycle as complete
        cycle.transition_to("complete")

        # Persist child
        from app.services.child_service import get_child_service
        await get_child_service().save_child(family_id)

        logger.info(
            f"✅ Exploration cycle completed: {cycle.id} "
            f"(supported={len(hypotheses_supported)}, contradicted={len(hypotheses_contradicted)})"
        )

        return {
            "status": "completed",
            "cycle_id": cycle.id,
            "what_we_learned": what_we_learned,
            "hypotheses_supported": hypotheses_supported,
            "hypotheses_contradicted": hypotheses_contradicted,
            "new_hypotheses_suggested": new_hypotheses,
            "remaining_questions": remaining_questions,
        }

    async def _handle_add_exploration_question(
        self,
        family_id: str,
        args: Dict[str, Any],
        child: Child
    ) -> Dict[str, Any]:
        """
        Add a question to the active exploration cycle.
        """
        from app.models.exploration import ConversationQuestion

        cycle = child.current_cycle()
        if not cycle:
            return {
                "status": "error",
                "error": "No active exploration cycle",
            }

        question_text = args.get("question", "")
        what_we_hope_to_learn = args.get("what_we_hope_to_learn", "")
        target_hypothesis_id = args.get("target_hypothesis_id")

        if not question_text:
            return {"status": "error", "error": "Question text is required"}

        # Ensure conversation method is initialized
        if not cycle.conversation_method:
            cycle.start_conversation_exploration([question_text])
        else:
            cycle.conversation_method.add_question(question_text)

        # Save
        from app.services.child_service import get_child_service
        await get_child_service().save_child(family_id)

        logger.info(f"Added exploration question: {question_text[:50]}...")

        return {
            "status": "added",
            "question": question_text,
            "what_we_hope_to_learn": what_we_hope_to_learn,
            "target_hypothesis_id": target_hypothesis_id,
            "total_questions": len(cycle.conversation_method.questions),
        }

    async def _handle_record_question_response(
        self,
        family_id: str,
        args: Dict[str, Any],
        child: Child
    ) -> Dict[str, Any]:
        """
        Record the response to an exploration question.
        """
        from app.models.understanding import Evidence
        from datetime import datetime

        cycle = child.current_cycle()
        if not cycle or not cycle.conversation_method:
            return {
                "status": "error",
                "error": "No active exploration with conversation method",
            }

        question_text = args.get("question", "")
        response_summary = args.get("response_summary", "")
        evidence_produced = args.get("evidence_produced", "")
        evidence_direction = args.get("evidence_direction", "neutral")
        target_hypothesis_id = args.get("target_hypothesis_id")

        # Find and mark the question as answered
        question_found = False
        for q in cycle.conversation_method.questions:
            if q.question == question_text or question_text in q.question:
                q.answered = True
                q.asked_at = datetime.now()
                q.response_summary = response_summary
                question_found = True
                break

        # Create evidence if we have a target hypothesis
        if target_hypothesis_id and evidence_produced:
            hypothesis = child.understanding.get_hypothesis(target_hypothesis_id)
            if hypothesis:
                evidence = Evidence(
                    source="conversation",
                    content=evidence_produced,
                    domain=hypothesis.domain,
                )
                hypothesis.add_evidence(evidence)

                # Adjust confidence based on direction
                if evidence_direction == "supports":
                    hypothesis.confidence = min(1.0, hypothesis.confidence + 0.1)
                elif evidence_direction == "contradicts":
                    hypothesis.confidence = max(0.0, hypothesis.confidence - 0.1)

        # Save
        from app.services.child_service import get_child_service
        await get_child_service().save_child(family_id)

        logger.info(f"Recorded question response: {question_text[:30]}... -> {evidence_direction}")

        return {
            "status": "recorded",
            "question_found": question_found,
            "response_summary": response_summary,
            "evidence_direction": evidence_direction,
            "target_hypothesis_id": target_hypothesis_id,
        }

    async def _handle_add_video_scenario(
        self,
        family_id: str,
        args: Dict[str, Any],
        child: Child
    ) -> Dict[str, Any]:
        """
        Add a video scenario to the active exploration cycle.
        """
        from app.models.exploration import VideoScenario

        cycle = child.current_cycle()
        if not cycle:
            return {
                "status": "error",
                "error": "No active exploration cycle",
            }

        if not cycle.video_method:
            return {
                "status": "error",
                "error": "Video method not active in this cycle. Use escalate_to_video first.",
            }

        scenario_text = args.get("scenario", "")
        why_we_want_to_see = args.get("why_we_want_to_see", "")
        target_hypothesis_id = args.get("target_hypothesis_id", "")
        focus_points = args.get("focus_points", [])

        if not scenario_text:
            return {"status": "error", "error": "Scenario description is required"}

        scenario = VideoScenario(
            title=scenario_text,
            what_to_film=scenario_text,
            target_hypothesis=target_hypothesis_id,
            what_we_hope_to_learn=why_we_want_to_see,
            focus_points=focus_points,
        )
        cycle.video_method.add_scenario(scenario)

        # Save
        from app.services.child_service import get_child_service
        await get_child_service().save_child(family_id)

        logger.info(f"Added video scenario: {scenario_text[:50]}...")

        return {
            "status": "added",
            "scenario_id": scenario.id,
            "scenario": scenario_text,
            "why_we_want_to_see": why_we_want_to_see,
            "total_scenarios": len(cycle.video_method.scenarios),
        }

    async def _handle_generate_synthesis(
        self,
        family_id: str,
        args: Dict[str, Any],
        gestalt: Gestalt
    ) -> Dict[str, Any]:
        """
        Generate a synthesis (parent report) of current understanding.
        """
        purpose = args.get("purpose", "share_with_professional")
        focus_areas = args.get("focus_areas", [])

        # Check if we have enough information
        if not gestalt.identity.name:
            return {
                "status": "error",
                "error": "Cannot generate synthesis - child's name not known yet",
            }

        if not gestalt.strengths.has_strengths:
            return {
                "status": "error",
                "error": "Cannot generate synthesis - strengths not yet captured (strengths come first)",
            }

        # TODO: Generate actual synthesis using LLM
        # For now, return a stub indicating what would be generated
        logger.info(f"Synthesis requested for purpose: {purpose}")

        return {
            "status": "pending",
            "message": "Synthesis generation will be implemented in the next phase",
            "purpose": purpose,
            "focus_areas": focus_areas,
            "gestalt_summary": {
                "child_name": gestalt.identity.name,
                "age": gestalt.identity.age,
                "has_strengths": gestalt.strengths.has_strengths,
                "hypothesis_count": len(gestalt.hypotheses.hypotheses),
                "pattern_count": len(gestalt.patterns.patterns),
            }
        }

    def _get_error_response(self) -> str:
        """Get error response in appropriate language"""
        if self.language == "he":
            return "סליחה, משהו השתבש. אפשר לנסות שוב?"
        return "Sorry, something went wrong. Can you try again?"

    def _build_session_data_for_artifacts(
        self,
        child: Child,
        session: UserSession,
        gestalt: Gestalt
    ) -> Dict[str, Any]:
        """
        Build session_data in the format expected by ArtifactGenerationService.

        The artifact service expects a dict with:
        - child_name, age, primary_concerns, etc.
        - conversation_history
        - extracted_data
        - artifacts (dict of existing artifacts)
        """
        # Build artifacts dict from exploration cycles
        artifacts_dict = {}
        for cycle in child.exploration_cycles:
            for artifact in cycle.artifacts:
                artifacts_dict[artifact.id] = {
                    "exists": True,
                    "content": artifact.content,  # Already a dict in CycleArtifact
                    "status": artifact.status,
                }

        # Build conversation history
        conversation_history = session.get_conversation_history(last_n=50)

        return {
            # Child identity
            "child_name": gestalt.identity.name,
            "age": gestalt.identity.age,
            "gender": gestalt.identity.gender,

            # Concerns
            "primary_concerns": gestalt.concerns.primary_areas,
            "concern_details": gestalt.concerns.details,

            # Understanding
            "strengths": gestalt.understanding.strengths,
            "developmental_history": gestalt.understanding.developmental_history,
            "family_context": gestalt.understanding.family_context,
            "daily_routines": gestalt.understanding.daily_routines,
            "parent_goals": gestalt.understanding.parent_goals,

            # Session context
            "conversation_history": conversation_history,
            "turn_count": session.turn_count,

            # Extracted data (full developmental data from child model)
            "extracted_data": child.developmental_data.to_dict() if hasattr(child.developmental_data, 'to_dict') else {},

            # Existing artifacts
            "artifacts": artifacts_dict,

            # Stories/journal entries
            "recent_stories": gestalt.observations.recent_stories,

            # Completeness
            "completeness": gestalt.completeness.score,
        }

    # === Returning User Handling ===

    def _check_returning_user(
        self,
        session: UserSession,
        child: Child
    ) -> Optional[Dict[str, Any]]:
        """
        Check if this is a returning user (first message after a time gap).

        Uses session.updated_at to detect time gaps. Must be called BEFORE
        any processing updates the session.

        Returns:
            Dict with time context if returning user, None otherwise
        """
        last_active = session.updated_at
        if not last_active:
            return None

        # Calculate time difference
        now = datetime.now()
        if last_active.tzinfo is not None:
            from datetime import timezone
            now = datetime.now(timezone.utc)

        time_diff = now - last_active
        hours = time_diff.total_seconds() / 3600
        days = hours / 24

        # Categorize the gap
        if hours < self.TIME_GAP_SAME_SESSION:
            return None  # Same session, not returning

        if hours < self.TIME_GAP_SHORT_BREAK:
            category = "short_break"
        elif hours < self.TIME_GAP_RETURNING:
            category = "returning"
        else:
            category = "long_absence"

        # Build summary of what we know
        known = get_what_we_know(build_gestalt(child, session))
        summary = self._build_returning_user_summary(known)

        return {
            "category": category,
            "hours_since": hours,
            "days_since": days,
            "summary": summary,
            "known": known,
        }

    def _build_returning_user_summary(self, known: Dict[str, Any]) -> str:
        """Build a text summary of what we know for returning user context"""
        parts = []

        if known.get("child_name"):
            parts.append(f"Child: {known['child_name']}")
        if known.get("age"):
            parts.append(f"Age: {known['age']} years")
        if known.get("concerns"):
            parts.append(f"Concerns: {', '.join(known['concerns'])}")
        if known.get("strengths"):
            parts.append(f"Strengths noted")
        if known.get("artifacts_available"):
            parts.append(f"Artifacts: {', '.join(known['artifacts_available'])}")
        if known.get("videos"):
            v = known["videos"]
            parts.append(f"Videos: {v['analyzed']}/{v['total']}")

        return "; ".join(parts) if parts else "No previous information"

    def _inject_tool_results_context(
        self,
        system_prompt: str,
        tool_results: List[Dict[str, Any]],
        language: str = "he"
    ) -> str:
        """
        Inject tool results into system prompt so Phase 2 knows what happened.

        Uses i18n for all text to support multilingual operation.
        This is critical for blocked actions - the LLM needs to know WHY
        an action was blocked so it can explain it naturally to the parent.
        """
        from app.services.i18n_service import get_i18n
        i18n = get_i18n(language)

        # Check for blocked actions and successful actions
        blocked_actions = []
        successful_actions = []

        for result in tool_results:
            tool_name = result.get("tool", "unknown")
            tool_result = result.get("result", {})
            status = tool_result.get("status", "")

            if status == "blocked":
                reason = tool_result.get("reason", "unknown")
                blocked_actions.append({
                    "tool": tool_name,
                    "reason": reason,
                    "completeness": tool_result.get("completeness"),
                    "message": tool_result.get("message"),
                })
            elif status in ["generated", "analyzed", "updated", "captured", "requested"]:
                successful_actions.append({
                    "tool": tool_name,
                    "status": status,
                    "artifact": tool_result.get("artifact_created"),
                })

        if not blocked_actions and not successful_actions:
            return system_prompt

        # Build injection using i18n
        injection = i18n.get("blocked_actions.section_labels.action_results")

        if blocked_actions:
            injection += i18n.get("blocked_actions.section_labels.blocked_actions")

            for action in blocked_actions:
                tool = action["tool"]
                reason = action["reason"]
                completeness = action.get("completeness", 0)

                # Map tool + reason to i18n key
                i18n_key = self._get_blocked_action_i18n_key(tool, reason)
                if i18n_key and i18n.has_key(i18n_key):
                    # Get translated guidance with placeholders
                    injection += i18n.get(
                        i18n_key,
                        completeness=f"{completeness:.0%}" if completeness else "0%",
                        required="60%" if tool == "generate_parent_report" else "40%"
                    )
                else:
                    # Fallback for unmapped combinations
                    injection += f"- **{tool}**: Blocked ({reason})\n"

        if successful_actions:
            injection += "\n" + i18n.get("blocked_actions.section_labels.completed_actions")
            for action in successful_actions:
                if action.get("artifact"):
                    injection += f"- ✓ {action['tool']}: Created {action['artifact']}\n"
                else:
                    injection += f"- ✓ {action['tool']}: {action['status']}\n"

        return system_prompt + "\n" + injection

    def _get_blocked_action_i18n_key(self, tool: str, reason: str) -> Optional[str]:
        """Map tool + reason to i18n key path."""
        # Map tool names to i18n section names
        tool_map = {
            "generate_parent_report": "parent_report",
            "generate_video_guidelines": "video_guidelines",
            "analyze_video": "video_analysis",
        }

        tool_section = tool_map.get(tool)
        if not tool_section:
            return None

        return f"blocked_actions.{tool_section}.{reason}"

    def _inject_returning_user_context(
        self,
        system_prompt: str,
        context: Dict[str, Any]
    ) -> str:
        """Inject returning user context into the system prompt"""

        # Build time description
        days = context["days_since"]
        if days < 1:
            time_desc = "a few hours"
        elif days < 2:
            time_desc = "about a day"
        elif days < 7:
            time_desc = f"about {int(days)} days"
        elif days < 14:
            time_desc = "about a week"
        elif days < 30:
            time_desc = "a couple of weeks"
        else:
            time_desc = "quite some time"

        injection = f"""

# Returning User Context

The parent is returning after {time_desc}.

**What we know from before:**
{context['summary']}

**Your task:**
1. Warmly acknowledge their return (don't ignore the time gap)
2. Briefly remind them where you left off
3. Ask if anything has changed with the child
4. Be natural and warm - this is a continuation, not a fresh start
"""

        return system_prompt + injection

    # === Semantic Verification ===

    def _should_run_verification(
        self,
        session: UserSession,
        gestalt: Gestalt
    ) -> bool:
        """
        Determine if semantic verification should run this turn.

        Uses exponential backoff and stops once artifacts are generated.
        """
        turn_count = session.turn_count

        # Don't verify if any artifacts exist
        if gestalt.artifacts.has_video_guidelines or gestalt.artifacts.has_parent_report:
            return False

        # Check if this turn matches a verification turn
        if turn_count not in self.VERIFICATION_TURNS:
            return False

        # Check if we already verified at this turn
        if session.semantic_verification_turn == turn_count:
            return False

        return True

    async def _run_verification_background(
        self,
        family_id: str,
        turn_count: int
    ):
        """
        Run semantic completeness verification in background.

        Stores result for next message to use.
        """
        try:
            logger.info(f"🔍 Background verification for {family_id} at turn {turn_count}")

            result = await self._unified.verify_semantic_completeness(family_id)

            # Update session with result
            session = await self._unified.get_or_create_session_async(family_id)
            session.semantic_verification = result
            session.semantic_verification_turn = turn_count
            await self._unified._persist_session(session)

            logger.info(
                f"✅ Verification complete: "
                f"{result.get('overall_completeness', 0)}% completeness"
            )

        except Exception as e:
            logger.error(f"❌ Background verification failed: {e}")


# Singleton
_chitta_service: Optional[ChittaService] = None


def get_chitta_service(language: str = "he") -> ChittaService:
    """Get singleton ChittaService instance"""
    global _chitta_service
    if _chitta_service is None:
        _chitta_service = ChittaService(language)
    return _chitta_service
