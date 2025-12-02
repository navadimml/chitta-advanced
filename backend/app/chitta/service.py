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
from .tools import get_chitta_tools

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

            tools = get_chitta_tools(gestalt)
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
            system_prompt = build_system_prompt(updated_gestalt, self.language)

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

        if tool_name == "update_child_understanding":
            return await self._handle_update_understanding(family_id, tool_args)

        elif tool_name == "capture_story":
            return await self._handle_capture_story(family_id, tool_args)

        elif tool_name == "detect_milestone":
            return await self._handle_detect_milestone(family_id, tool_args, gestalt)

        elif tool_name == "generate_video_guidelines":
            return await self._handle_generate_guidelines(family_id, tool_args, gestalt)

        elif tool_name == "generate_parent_report":
            return await self._handle_generate_report(family_id, tool_args, gestalt)

        elif tool_name == "request_video_observation":
            return await self._handle_request_video(family_id, tool_args, gestalt)

        elif tool_name == "analyze_video":
            return await self._handle_analyze_video(family_id, tool_args, gestalt)

        elif tool_name == "ask_developmental_question":
            return self._handle_developmental_question(tool_args, gestalt)

        elif tool_name == "ask_about_app":
            return self._handle_app_question(tool_args, gestalt)

        else:
            logger.warning(f"Unknown tool: {tool_name}")
            return {"status": "unknown_tool", "tool": tool_name}

    async def _handle_update_understanding(
        self,
        family_id: str,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update child's developmental data"""
        # Filter out empty values
        update_data = {k: v for k, v in args.items() if v is not None and v != ""}

        if not update_data:
            return {"status": "no_updates"}

        # Update via unified service
        self._unified.update_extracted_data(family_id, update_data)

        # Recalculate completeness
        new_completeness = self._unified.calculate_completeness(family_id)

        logger.info(f"Updated understanding: {list(update_data.keys())}, completeness: {new_completeness:.0%}")

        return {
            "status": "updated",
            "fields_updated": list(update_data.keys()),
            "new_completeness": new_completeness,
        }

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

    async def _handle_generate_guidelines(
        self,
        family_id: str,
        args: Dict[str, Any],
        gestalt: Gestalt
    ) -> Dict[str, Any]:
        """
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
                    child.add_artifact(interview_summary_id, interview_artifact.to_dict())
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
                child.add_artifact("baseline_video_guidelines", artifact.to_dict())
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
                child.add_artifact("baseline_parent_report", artifact.to_dict())
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
        """Handle video observation request"""

        # Check prerequisites
        if not gestalt.artifacts.has_video_guidelines:
            return {
                "status": "blocked",
                "reason": "no_guidelines",
            }

        if gestalt.filming_preference == "report_only":
            return {
                "status": "blocked",
                "reason": "parent_chose_report_only",
            }

        # This triggers UI to show video upload
        # The actual video handling is done by frontend + upload endpoints

        return {
            "status": "requested",
            "scenario": args.get("scenario"),
            "observation_goal": args.get("observation_goal"),
            "focus_points": args.get("focus_points", []),
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
                child.add_artifact(artifact.artifact_id, artifact.to_dict())
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
        # Build artifacts dict from child
        artifacts_dict = {}
        for artifact_id, artifact_data in child.artifacts.items():
            artifacts_dict[artifact_id] = {
                "exists": True,
                "content": artifact_data.get("content"),
                "status": artifact_data.get("status", "ready"),
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
