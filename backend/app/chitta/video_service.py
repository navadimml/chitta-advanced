"""
Video Service - Video workflow orchestration

Handles the complete video workflow:
- Consent: Parent accepts/declines video suggestions
- Guidelines: Personalized filming instructions (LLM-generated)
- Upload: Recording video uploads and status
- Analysis: Sophisticated video analysis with Gemini

Philosophy:
- Video is hypothesis-driven (testing specific theories)
- Guidelines are personalized using parent's vocabulary
- Strengths are ALWAYS documented (non-negotiable)
- Parent NEVER sees internal hypotheses
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Callable, Awaitable
import logging
import json
import os

from .gestalt import Darshan
from .curiosity_types import BaseCuriosity, Hypothesis, Discovery, Question
from .models import VideoScenario, Evidence as VideoEvidence, TemporalFact, InvestigationContext

logger = logging.getLogger(__name__)


class VideoService:
    """Orchestrates the complete video workflow."""

    def __init__(
        self,
        get_darshan: Callable[[str], Awaitable[Optional[Darshan]]],
        persist_darshan: Callable[[str, Darshan], Awaitable[None]],
        get_cards_callback: Callable[[Darshan], List[Dict]],
    ):
        """
        Initialize VideoService with required callbacks.

        Args:
            get_darshan: Async function to retrieve Darshan by family_id
            persist_darshan: Async function to persist Darshan changes
            get_cards_callback: Function to derive cards from Darshan state
        """
        self._get_darshan = get_darshan
        self._persist_darshan = persist_darshan
        self._get_cards = get_cards_callback

    # ========================================
    # VIDEO CONSENT & GUIDELINES
    # ========================================

    async def accept_video_suggestion(
        self,
        family_id: str,
        cycle_id: str,
        generate_async: bool = True
    ) -> Dict[str, Any]:
        """
        Parent accepted video suggestion.

        Two modes:
        - generate_async=True (default): Mark accepted, return immediately,
          generate guidelines in background and send SSE when ready
        - generate_async=False: Block until guidelines generated (for testing)

        Guidelines are personalized using:
        - Parent's own words from stories
        - Specific people, places, toys mentioned
        - The hypothesis we're testing (internal, not revealed to parent)

        Returns guidelines in parent-facing format (no hypothesis revealed).
        """
        darshan = await self._get_darshan(family_id)
        if not darshan:
            return {"error": "Family not found"}

        # Find curiosity by investigation ID
        curiosity = darshan._curiosities.get_curiosity_by_investigation_id(cycle_id)

        if not curiosity or not curiosity.investigation:
            return {"error": "Investigation not found"}

        if not curiosity.video_appropriate:
            return {"error": "Video not appropriate for this investigation"}

        investigation = curiosity.investigation

        # Mark as accepted
        curiosity.accept_video()

        # Set generating status
        investigation.guidelines_status = "generating"

        # Persist immediately so UI can show "generating" state
        await self._persist_darshan(family_id, darshan)

        if generate_async:
            # Start background task for guidelines generation
            import asyncio
            asyncio.create_task(
                self._generate_guidelines_background(family_id, cycle_id)
            )

            return {
                "status": "generating",
                "cycle_id": cycle_id,
                "message": "מכין הנחיות צילום מותאמות אישית...",
            }
        else:
            # Synchronous generation (for testing)
            scenarios = await self._generate_personalized_video_guidelines(darshan, curiosity)

            if not scenarios:
                return {"error": "Failed to generate video guidelines"}

            investigation.video_scenarios = scenarios
            investigation.guidelines_status = "ready"
            await self._persist_darshan(family_id, darshan)

            return {
                "status": "ready",
                "cycle_id": cycle_id,
                "guidelines": self._build_guidelines_response(darshan, scenarios),
            }

    async def _generate_guidelines_background(self, family_id: str, cycle_id: str):
        """Background task to generate guidelines and send SSE when ready."""
        try:
            darshan = await self._get_darshan(family_id)
            if not darshan:
                logger.error(f"Background guidelines: family {family_id} not found")
                return

            # Find curiosity by investigation ID
            curiosity = darshan._curiosities.get_curiosity_by_investigation_id(cycle_id)

            if not curiosity or not curiosity.investigation:
                logger.error(f"Background guidelines: investigation {cycle_id} not found")
                return

            investigation = curiosity.investigation

            # Generate guidelines
            logger.info(f"🎬 Background generating guidelines for {family_id}/{cycle_id}")
            scenarios = await self._generate_personalized_video_guidelines(darshan, curiosity)

            if scenarios:
                investigation.video_scenarios = scenarios
                investigation.guidelines_status = "ready"
                await self._persist_darshan(family_id, darshan)

                # Send SSE to update cards
                from app.services.sse_notifier import get_sse_notifier
                updated_cards = self._get_cards(darshan)
                await get_sse_notifier().notify_cards_updated(family_id, updated_cards)

                logger.info(f"✅ Background guidelines ready for {family_id}/{cycle_id}")
            else:
                investigation.guidelines_status = "error"
                await self._persist_darshan(family_id, darshan)
                logger.error(f"❌ Background guidelines failed for {family_id}/{cycle_id}")

        except Exception as e:
            logger.error(f"Background guidelines error: {e}", exc_info=True)

    async def decline_video_suggestion(self, family_id: str, cycle_id: str) -> Dict[str, Any]:
        """
        Parent declined video suggestion.

        Respect their choice - don't ask again for this investigation.
        Continue exploring via conversation.
        """
        darshan = await self._get_darshan(family_id)
        if not darshan:
            return {"error": "Family not found"}

        # Find curiosity by investigation ID
        curiosity = darshan._curiosities.get_curiosity_by_investigation_id(cycle_id)
        if curiosity:
            curiosity.decline_video()
            await self._persist_darshan(family_id, darshan)
            return {
                "status": "declined",
                "cycle_id": cycle_id,
                "message": "בסדר גמור! נמשיך להכיר דרך השיחה שלנו.",
            }

        return {"error": "Investigation not found"}

    async def accept_baseline_video(
        self,
        family_id: str,
        generate_async: bool = True,
    ) -> Dict[str, Any]:
        """
        Parent accepted baseline video suggestion.

        Creates a "discovery" curiosity with investigation - not tied to a hypothesis,
        just curiosity about who this child is.

        Guidelines are simple: "film any everyday moment."
        """
        darshan = await self._get_darshan(family_id)
        if not darshan:
            return {"error": "Family not found"}

        # Mark baseline video as requested (prevents re-suggestion)
        darshan._curiosities.mark_baseline_video_requested()

        # Create a discovery curiosity with investigation
        child_name = darshan.child_name or "הילד/ה"

        # Create discovery with video-appropriate settings
        # Note: Discovery doesn't have video fields, so we create a Hypothesis for video testing
        curiosity = Hypothesis.create(
            focus=f"להכיר את {child_name}",
            theory=f"תצפית בסיסית להכרת {child_name}",
            domain="essence",
            reasoning="baseline video observation",
            video_appropriate=True,
            video_value="discovery",
            video_value_reason="baseline observation to see the child naturally",
        )

        # Start investigation and accept video
        curiosity.start_investigation()
        curiosity.accept_video()

        investigation = curiosity.investigation

        # Create a simple baseline scenario (no LLM needed)
        scenario = VideoScenario.create(
            title="רגע יומיומי טבעי",
            what_to_film=f"צלמו סרטון קצר (3-5 דקות) של {child_name} ברגע יומיומי רגיל - משחק, ארוחה, או כל פעילות טבעית אחרת.",
            rationale_for_parent="זה יעזור לי להכיר אותו/ה בסביבה הטבעית שלו/ה, לראות את האופי, הסגנון, והאנרגיה. לא צריך להכין שום דבר מיוחד - ככל שהמצב יותר רגיל, יותר טוב!",
            target_hypothesis_id=investigation.id,
            what_we_hope_to_learn="Baseline observation of the child's natural behavior, temperament, regulation, and interaction style.",
            focus_points=[
                "General demeanor and mood",
                "Play style and interests",
                "Communication patterns",
                "Regulation and transitions",
                "Natural parent-child interaction",
            ],
            category="baseline",
        )
        investigation.video_scenarios = [scenario]

        darshan._curiosities.add_curiosity(curiosity)
        await self._persist_darshan(family_id, darshan)

        return {
            "status": "accepted",
            "exploration_id": investigation.id,
            "scenarios": [
                {
                    "id": scenario.id,
                    "title": scenario.title,
                    "what_to_film": scenario.what_to_film,
                    "rationale": scenario.rationale_for_parent,
                    "duration": scenario.duration_suggestion,
                }
            ],
            "message": f"נהדר! אשמח לראות את {child_name}. הנחיות פשוטות מוכנות.",
        }

    async def dismiss_baseline_video(self, family_id: str) -> Dict[str, Any]:
        """
        Parent dismissed baseline video suggestion (אולי מאוחר יותר).

        Just marks it as requested so it doesn't show again.
        """
        darshan = await self._get_darshan(family_id)
        if not darshan:
            return {"error": "Family not found"}

        # Mark baseline video as requested (prevents re-suggestion)
        darshan._curiosities.mark_baseline_video_requested()
        await self._persist_darshan(family_id, darshan)

        return {
            "status": "dismissed",
            "message": "אין בעיה, אפשר לחזור לזה בהמשך.",
        }

    async def get_video_guidelines(self, family_id: str, cycle_id: str) -> Dict[str, Any]:
        """Get video guidelines for an investigation (parent-facing format only)."""
        darshan = await self._get_darshan(family_id)
        if not darshan:
            return {"error": "Family not found"}

        curiosity = darshan._curiosities.get_curiosity_by_investigation_id(cycle_id)
        if curiosity and curiosity.investigation and curiosity.investigation.video_scenarios:
            return self._build_guidelines_response(darshan, curiosity.investigation.video_scenarios)

        return {"error": "No video guidelines found for this investigation"}

    async def dismiss_scenario_reminders(
        self, family_id: str, scenario_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Dismiss reminder cards for scenarios but keep guidelines accessible.

        Parent chose "Don't remind me" - we stop showing the card,
        but the guidelines remain in ChildSpace Observations tab.
        """
        darshan = await self._get_darshan(family_id)
        if not darshan:
            return {"error": "Family not found"}

        dismissed_count = 0
        for curiosity in darshan._curiosities.get_all():
            if isinstance(curiosity, Hypothesis) and curiosity.investigation:
                for scenario in curiosity.investigation.video_scenarios:
                    if scenario.id in scenario_ids:
                        scenario.dismiss_reminder()
                        dismissed_count += 1

        if dismissed_count > 0:
            await self._persist_darshan(family_id, darshan)
            return {
                "status": "dismissed",
                "count": dismissed_count,
                "message": "לא אזכיר, ההנחיות עדיין זמינות בחלל הילד",
            }

        return {"error": "No matching scenarios found"}

    async def reject_scenarios(
        self, family_id: str, scenario_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Reject scenarios - parent decided not to film.

        Parent chose "Not relevant" - we mark these scenarios as rejected.
        They won't appear in reminders or in ChildSpace pending list.
        """
        darshan = await self._get_darshan(family_id)
        if not darshan:
            return {"error": "Family not found"}

        rejected_count = 0
        for curiosity in darshan._curiosities.get_all():
            if isinstance(curiosity, Hypothesis) and curiosity.investigation:
                for scenario in curiosity.investigation.video_scenarios:
                    if scenario.id in scenario_ids:
                        scenario.reject()
                        rejected_count += 1

        if rejected_count > 0:
            await self._persist_darshan(family_id, darshan)
            return {
                "status": "rejected",
                "count": rejected_count,
                "message": "בסדר, נמשיך להכיר בדרכים אחרות",
            }

        return {"error": "No matching scenarios found"}

    async def acknowledge_video_insights(
        self, family_id: str, scenario_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Acknowledge video insights - parent saw the 'video analyzed' feedback.

        This dismisses the video_analyzed card by marking scenarios as acknowledged.
        The insights are already woven into the understanding.
        """
        darshan = await self._get_darshan(family_id)
        if not darshan:
            return {"error": "Family not found"}

        acknowledged_count = 0
        for curiosity in darshan._curiosities.get_all():
            if isinstance(curiosity, Hypothesis) and curiosity.investigation:
                for scenario in curiosity.investigation.video_scenarios:
                    if scenario.id in scenario_ids and scenario.status == "analyzed":
                        scenario.status = "acknowledged"
                        acknowledged_count += 1

        if acknowledged_count > 0:
            await self._persist_darshan(family_id, darshan)
            return {
                "status": "acknowledged",
                "count": acknowledged_count,
            }

        return {"error": "No matching scenarios found"}

    async def confirm_video(
        self, family_id: str, scenario_id: str
    ) -> Dict[str, Any]:
        """
        Parent confirms the video is correct despite validation concerns.

        Proceeds with analysis - marks as analyzed and processes the evidence.
        """
        darshan = await self._get_darshan(family_id)
        if not darshan:
            return {"error": "Family not found"}

        for curiosity in darshan._curiosities.get_all():
            if not isinstance(curiosity, Hypothesis) or not curiosity.investigation:
                continue
            for scenario in curiosity.investigation.video_scenarios:
                if scenario.id == scenario_id and scenario.status == "needs_confirmation":
                    # Parent confirmed - proceed with the analysis result we already have
                    analysis_result = scenario.analysis_result
                    if analysis_result:
                        # Remove the confirmation flag and mark as analyzed
                        analysis_result.pop("_needs_confirmation", None)
                        analysis_result.pop("_confirmation_reasons", None)
                        scenario.mark_analyzed(analysis_result)

                        # Process evidence from the analysis
                        for observation in analysis_result.get("observations", []):
                            evidence = VideoEvidence.create(
                                content=observation.get("content", ""),
                                effect=observation.get("effect", "supports"),
                                source="video",
                            )
                            curiosity.investigation.evidence.append(evidence)

                        await self._persist_darshan(family_id, darshan)
                        return {
                            "status": "confirmed",
                            "scenario_id": scenario_id,
                            "message": "תודה על האישור! ניתחתי את הסרטון.",
                        }

        return {"error": "Scenario not found or not awaiting confirmation"}

    async def reject_confirmed_video(
        self, family_id: str, scenario_id: str
    ) -> Dict[str, Any]:
        """
        Parent rejects the video that was flagged for confirmation.

        Resets the scenario to pending so parent can upload a different video.
        """
        darshan = await self._get_darshan(family_id)
        if not darshan:
            return {"error": "Family not found"}

        for curiosity in darshan._curiosities.get_all():
            if not isinstance(curiosity, Hypothesis) or not curiosity.investigation:
                continue
            for scenario in curiosity.investigation.video_scenarios:
                if scenario.id == scenario_id and scenario.status == "needs_confirmation":
                    # Reset to pending - parent will upload a new video
                    scenario.status = "pending"
                    scenario.video_path = None
                    scenario.uploaded_at = None
                    scenario.analysis_result = None

                    await self._persist_darshan(family_id, darshan)
                    return {
                        "status": "rejected",
                        "scenario_id": scenario_id,
                        "message": "בסדר, אפשר להעלות סרטון אחר.",
                    }

        return {"error": "Scenario not found or not awaiting confirmation"}

    async def record_video_upload(
        self,
        family_id: str,
        scenario_id: str,
        file_path: str,
        duration_seconds: int = 0
    ) -> Dict[str, Any]:
        """
        Record that a video was uploaded for a scenario.

        Updates the scenario status to 'uploaded' and stores file path.
        This triggers card change from 'guidelines_ready' to 'video_uploaded'.

        scenario_id can be either:
        - The actual scenario ID (like "scenario_001")
        - The scenario title (like "מעבר מפעילות לפעילות")
        """
        darshan = await self._get_darshan(family_id)
        if not darshan:
            return {"error": "Family not found"}

        # Find the scenario across all curiosities (by ID or title)
        for curiosity in darshan._curiosities.get_all():
            if not isinstance(curiosity, Hypothesis) or not curiosity.investigation:
                continue
            for scenario in curiosity.investigation.video_scenarios:
                # Match by ID or title
                if scenario.id == scenario_id or scenario.title == scenario_id:
                    scenario.status = "uploaded"
                    scenario.video_path = file_path  # Model uses video_path, not file_path
                    scenario.uploaded_at = datetime.now()

                    await self._persist_darshan(family_id, darshan)

                    logger.info(f"📹 Video uploaded for scenario '{scenario.title}' (id={scenario.id}) in investigation {curiosity.investigation.id}")
                    return {
                        "status": "uploaded",
                        "scenario_id": scenario.id,
                        "scenario_title": scenario.title,
                        "cycle_id": curiosity.investigation.id,
                        "message": "הסרטון התקבל! אפשר לנתח אותו כשתהיו מוכנים.",
                    }

        logger.warning(f"⚠️ Scenario not found: '{scenario_id}' in family {family_id}")
        available = [(s.id, s.title) for c in darshan._curiosities.get_all() if isinstance(c, Hypothesis) and c.investigation for s in c.investigation.video_scenarios]
        logger.warning(f"   Available scenarios: {available}")
        return {"error": f"Scenario '{scenario_id}' not found"}

    def _build_guidelines_response(self, darshan: Darshan, scenarios: List) -> Dict[str, Any]:
        """Build parent-facing guidelines response."""
        child_name = darshan.child_name or "הילד/ה"
        return {
            "child_name": child_name,
            "introduction": f"הסרטונים יעזרו לי לראות את {child_name} בסביבה הטבעית שלו ולהבין אותו טוב יותר.",
            "scenarios": [s.to_parent_facing_dict() for s in scenarios],
            "general_tips": [
                "צלמו בסביבה טבעית - בית, גן, או כל מקום שנוח לכם",
                "אורך מומלץ: 2-5 דקות לכל סרטון",
                f"אין צורך בהכנה מיוחדת - אנחנו רוצים לראות את {child_name} כמו שהוא",
                "תאורה טובה עוזרת, אבל לא חייבת להיות מושלמת",
            ],
        }

    async def _generate_personalized_video_guidelines(
        self,
        darshan: Darshan,
        curiosity: Hypothesis,
    ) -> List[VideoScenario]:
        """
        Generate PERSONALIZED video guidelines using LLM.

        The LLM receives:
        - All stories we've captured (rich with context)
        - All facts about the child
        - The hypothesis we're testing (internal)
        - Child's strengths and interests

        The LLM generates:
        - Warm, concrete instructions using parent's own words
        - Specific people, places, toys from their stories
        - Sandwich rationale (validate → explain → reassure)

        Parent NEVER sees the hypothesis - only warm filming instructions.
        """
        from app.services.llm.base import Message as LLMMessage

        child_name = darshan.child_name or "הילד/ה"

        # Build rich context from stories and facts
        stories_context = self._format_stories_for_llm(darshan.stories)
        observations_context = self._format_observations_for_llm(darshan.understanding.observations)
        strengths_context = self._extract_strengths(darshan)

        # Build the prompt
        prompt = f"""# Generate Personalized Video Guidelines (Hebrew)

## Your Role
You are Chitta, a warm and supportive child development expert.
Write directly to the Israeli parent in natural Hebrew.

## CRITICAL: Use Their World
Extract from the stories and facts:
- **People** they mentioned (סבתא, הגננת, אח/אחות - use their names if given)
- **Places** in their life (הגן, מגרש המשחקים, הסלון, המטבח)
- **Toys/Objects** the child loves (specific toys, games, items mentioned)
- **Parent's own words** - mirror their language, not clinical terms

## Child Context
**Name:** {child_name}

## Stories Shared (RICH CONTEXT - USE THIS!)
{stories_context}

## Facts We Know
{observations_context}

## Strengths & Interests
{strengths_context}

## What We're Exploring (INTERNAL - DO NOT REVEAL TO PARENT)
**Focus:** {curiosity.focus}
**Domain:** {curiosity.domain or "general"}
**Theory (if hypothesis):** {curiosity.theory or "N/A"}
**Question (if question):** {curiosity.question or "N/A"}
**Video Value Type:** {curiosity.video_value or "general"}
**Why Video Helps:** {curiosity.video_value_reason or "N/A"}

## VIDEO VALUE FRAMING (Use this to shape your approach!)
{self._get_video_value_framing(curiosity.video_value)}

## Generate ONE Video Scenario

### Required Output (JSON):
{{
  "title": "Short Hebrew title - warm, not clinical",
  "what_to_film": "CONCRETE instructions using THEIR specific toys/places/people. Example: 'שבו ליד שולחן המטבח עם [הצעצוע שהם הזכירו]. שחקו יחד 5 דקות.'",
  "rationale_for_parent": "Sandwich structure: 1) Validate ('שמעתי ש...'), 2) Explain why this helps, 3) Reassure ('אל תדאגו מ...')",
  "duration_suggestion": "3-5 דקות",
  "example_situations": ["Situation 1 using their context", "Situation 2 using their context"],
  "focus_points": ["Internal analysis point 1 - NOT for parent", "Internal analysis point 2"],
  "what_we_hope_to_learn": "Clinical goal - NOT for parent"
}}

### Quality Checklist:
❌ BAD: "צלמו משחק" (too generic)
✅ GOOD: "שבו ליד השולחן במטבח, תנו ל{child_name} את הדינוזאורים שהוא אוהב, ושחקו יחד 5 דקות"

❌ BAD: "צלמו אינטראקציה חברתית" (clinical)
✅ GOOD: "כשסבתא מגיעה לביקור, צלמו כמה דקות של משחק יחד"

❌ BAD: Generic rationale
✅ GOOD: "שמעתי שהבקרים שלכם עמוסים ושקשה לו עם מעברים. לראות רגע כזה יעזור לי להבין בדיוק מה קורה ואיך אפשר לעזור. אל תנסו 'לסדר' את המצב - אנחנו רוצים לראות את המציאות."

Generate the scenario JSON now:
"""

        try:
            # Use STRONG LLM for guidelines generation (from STRONG_LLM_MODEL env var)
            llm = darshan._get_strong_llm()
            response = await llm.chat(
                messages=[LLMMessage(role="user", content=prompt)],
                functions=None,
                temperature=0.7,
                max_tokens=2000,
            )

            # Parse the JSON response
            response_text = response.content or ""

            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            scenario_data = json.loads(response_text)

            # Create VideoScenario from LLM response
            investigation_id = curiosity.investigation.id if curiosity.investigation else curiosity.focus
            scenario = VideoScenario.create(
                title=scenario_data.get("title", "תצפית"),
                what_to_film=scenario_data.get("what_to_film", "צלמו מצב יומיומי טבעי"),
                rationale_for_parent=scenario_data.get("rationale_for_parent", ""),
                target_hypothesis_id=investigation_id,
                what_we_hope_to_learn=scenario_data.get("what_we_hope_to_learn", curiosity.focus),
                focus_points=scenario_data.get("focus_points", []),
                duration_suggestion=scenario_data.get("duration_suggestion", "3-5 דקות"),
                example_situations=scenario_data.get("example_situations", []),
                category="hypothesis_test" if isinstance(curiosity, Hypothesis) else "exploration",
            )

            logger.info(f"✅ Generated personalized video guidelines for curiosity: {curiosity.focus}")
            return [scenario]

        except Exception as e:
            logger.error(f"Error generating video guidelines: {e}")
            # Fallback to simple scenario
            return [self._create_fallback_scenario(darshan, curiosity)]

    def _get_video_value_framing(self, video_value: Optional[str]) -> str:
        """
        Get specific framing instructions based on video_value type.

        This shapes how we ask parents to film and what we emphasize.
        """
        framings = {
            "calibration": """
**CALIBRATION VIDEO** - Parent used absolutes ("never", "always") about significant behavior.
- Frame as: "I'd love to see a regular moment so I can understand the full picture"
- Goal: See the actual reality vs parent's perception
- Reassure: "Every child has good and tough moments - I want to see both"
- DON'T make it sound like you're testing their claim
""",
            "chain": """
**CHAIN VIDEO** - Multiple domains seem connected, we want to see the sequence.
- Frame as: "I'm curious how things unfold - film the whole flow"
- Goal: See the chain of events (trigger → response → result)
- Ask for: Full moment, not just the "problem" part
- Emphasize: "Don't cut the video short - the before and after matter"
""",
            "discovery": """
**DISCOVERY VIDEO** - Baseline observation to see this child for the first time.
- Frame as: "I'd love to see [name] being [name] - just a regular moment"
- Goal: See who this child IS in their natural environment
- Keep it open: Don't specify what to look for
- Warmest tone: "This helps me get to know them beyond our conversations"
""",
            "reframe": """
**REFRAME VIDEO** - Parent describes concern that might be a strength in context.
- Frame as: "Let me see this in their natural setting"
- Goal: See if what parent calls "problem" is actually adaptive/positive
- Careful: Don't reveal you think it might be reframed
- Look for: Context, what triggers it, what follows
""",
            "relational": """
**RELATIONAL VIDEO** - The parent-child interaction pattern is the question.
- Frame as: "Film a moment together with [name]"
- Goal: See the dance between parent and child
- Sensitive: This is about their relationship, be extra warm
- Ask for: Natural interaction, play, daily routine moment together
""",
        }

        return framings.get(video_value, """
**GENERAL VIDEO** - Exploration without specific video value type.
- Frame as helpful observation for understanding
- Keep instructions concrete and warm
- Focus on natural, everyday moments
""")

    def _format_stories_for_llm(self, stories: List) -> str:
        """Format stories for LLM context - preserve the richness."""
        if not stories:
            return "No stories captured yet."

        lines = []
        for story in stories[-5:]:  # Last 5 stories
            lines.append(f"- {story.summary}")
            if story.reveals:
                lines.append(f"  (Reveals: {', '.join(story.reveals[:3])})")
        return "\n".join(lines)

    def _format_observations_for_llm(self, facts: List) -> str:
        """Format facts for LLM context."""
        if not facts:
            return "Still getting to know this child."

        # Group by domain
        by_domain = {}
        for fact in facts:
            domain = fact.domain or "general"
            if domain not in by_domain:
                by_domain[domain] = []
            by_domain[domain].append(fact.content)

        lines = []
        for domain, contents in by_domain.items():
            lines.append(f"**{domain}:** {'; '.join(contents[:3])}")
        return "\n".join(lines)

    def _extract_strengths(self, darshan: Darshan) -> str:
        """Extract strengths from facts and stories."""
        strength_facts = [
            f.content for f in darshan.understanding.observations
            if f.domain in ["strengths", "essence", "interests"]
        ]
        if strength_facts:
            return "\n".join(f"- {s}" for s in strength_facts[:5])
        return "Not yet identified - explore through video."

    def _create_fallback_scenario(self, darshan: Darshan, curiosity: Hypothesis) -> VideoScenario:
        """Create a simple fallback scenario if LLM fails."""
        child_name = darshan.child_name or "הילד/ה"
        investigation_id = curiosity.investigation.id if curiosity.investigation else curiosity.focus

        return VideoScenario.create(
            title="תצפית יומיומית",
            what_to_film=f"צלמו את {child_name} במצב יומיומי טבעי - משחק, אוכל, או אינטראקציה עם בני משפחה.",
            rationale_for_parent=f"לראות את {child_name} בסביבה הטבעית יעזור לי להבין אותו טוב יותר. אל תדאגו מ'לסדר' את המצב - אנחנו רוצים לראות את המציאות.",
            target_hypothesis_id=investigation_id,
            what_we_hope_to_learn=curiosity.focus,
            focus_points=[f"בדיקת: {curiosity.focus}"],
            duration_suggestion="3-5 דקות",
            example_situations=["משחק בבית", "ארוחה משפחתית"],
            category="exploration",
        )

    # ========================================
    # VIDEO UPLOAD & ANALYSIS
    # ========================================

    async def mark_video_uploaded(
        self,
        family_id: str,
        cycle_id: str,
        scenario_id: str,
        video_path: str,
    ) -> Dict[str, Any]:
        """
        Mark a video scenario as uploaded.

        Called after file is saved by the API endpoint.
        """
        darshan = await self._get_darshan(family_id)
        if not darshan:
            return {"error": "Family not found"}

        # Find curiosity by investigation ID
        curiosity = darshan._curiosities.get_curiosity_by_investigation_id(cycle_id)
        if curiosity and curiosity.investigation:
            # Find the scenario
            scenario = None
            for s in curiosity.investigation.video_scenarios:
                if s.id == scenario_id:
                    scenario = s
                    break

            if not scenario:
                return {"error": "Scenario not found"}

            scenario.mark_uploaded(video_path)
            await self._persist_darshan(family_id, darshan)

            return {
                "status": "uploaded",
                "scenario_id": scenario_id,
                "video_path": video_path,
            }

        return {"error": "Investigation not found"}

    async def analyze_cycle_videos(
        self,
        family_id: str,
        cycle_id: str,
    ) -> Dict[str, Any]:
        """
        Analyze all uploaded videos for an investigation.

        Uses sophisticated video analysis to:
        1. Analyze video with hypothesis-driven prompt
        2. Extract objective observations as evidence
        3. Update hypothesis confidence based on verdict
        4. Capture strengths (non-negotiable)
        5. Generate warm parent-facing insights

        Returns insights for the parent (no hypothesis revealed).
        """
        darshan = await self._get_darshan(family_id)
        if not darshan:
            return {"error": "Family not found"}

        # Find curiosity by investigation ID
        curiosity = darshan._curiosities.get_curiosity_by_investigation_id(cycle_id)

        if not curiosity or not curiosity.investigation:
            return {"error": "Investigation not found"}

        investigation = curiosity.investigation

        # Get uploaded (not yet analyzed) videos
        pending_scenarios = [s for s in investigation.video_scenarios if s.status == "uploaded"]
        if not pending_scenarios:
            return {"error": "No videos to analyze"}

        insights = []
        evidence_added = 0
        strengths_found = []
        confidence_before = curiosity.confidence
        hypothesis_evidence = {}  # Initialize for return statement
        validation_failed_count = 0

        for scenario in pending_scenarios:
            # Analyze the video with sophisticated prompt
            analysis_result = await self._analyze_video(darshan, curiosity, scenario)

            if analysis_result:
                # Check if video validation failed
                video_validation = analysis_result.get("video_validation", {})
                is_usable = video_validation.get("is_usable", True)

                if not is_usable:
                    # Validation failed - mark as such, don't add evidence
                    scenario.mark_validation_failed(analysis_result)
                    validation_failed_count += 1
                    logger.warning(f"⚠️ Video validation failed for scenario {scenario.id}")
                    logger.warning(f"   Issues: {video_validation.get('validation_issues', [])}")
                    # Add a single insight about the failed validation
                    insights.append(
                        f"הסרטון שהועלה לא תואם לבקשה. "
                        f"{video_validation.get('what_video_shows', '')}. "
                        f"אפשר להעלות סרטון חדש."
                    )
                    continue  # Skip evidence processing for this scenario

                # Check if video needs parent confirmation (has concerns but not failed)
                if analysis_result.get("_needs_confirmation"):
                    scenario.status = "needs_confirmation"
                    scenario.analysis_result = analysis_result
                    logger.warning(f"⚠️ Video needs confirmation for scenario {scenario.id}")
                    logger.warning(f"   Reasons: {analysis_result.get('_confirmation_reasons', [])}")
                    continue  # Wait for parent confirmation before processing

                # Mark scenario as analyzed with full result
                scenario.mark_analyzed(analysis_result)

                # Create evidence from observations and add to investigation
                for observation in analysis_result.get("observations", []):
                    evidence = VideoEvidence.create(
                        content=observation.get("content", ""),
                        effect=observation.get("effect", "supports"),
                        source="video",
                    )
                    curiosity.investigation.evidence.append(evidence)
                    evidence_added += 1

                # Update confidence based on hypothesis_evidence verdict
                hypothesis_evidence = analysis_result.get("hypothesis_evidence", {})
                verdict = hypothesis_evidence.get("overall_verdict", "inconclusive")
                confidence_level = hypothesis_evidence.get("confidence_level", "Low")

                if isinstance(curiosity, Hypothesis) and curiosity.confidence is not None:
                    # More nuanced confidence update based on verdict
                    if verdict == "supports":
                        boost = 0.15 if confidence_level == "High" else 0.10 if confidence_level == "Moderate" else 0.05
                        curiosity.confidence = min(1.0, curiosity.confidence + boost)
                    elif verdict == "contradicts":
                        drop = 0.20 if confidence_level == "High" else 0.15 if confidence_level == "Moderate" else 0.10
                        curiosity.confidence = max(0.0, curiosity.confidence - drop)
                    elif verdict == "mixed":
                        # Mixed evidence - slight increase if more supports than contradicts
                        supporting = len(hypothesis_evidence.get("supporting_evidence", []))
                        contradicting = len(hypothesis_evidence.get("contradicting_evidence", []))
                        if supporting > contradicting:
                            curiosity.confidence = min(1.0, curiosity.confidence + 0.05)
                        elif contradicting > supporting:
                            curiosity.confidence = max(0.0, curiosity.confidence - 0.05)
                        # Equal: no change

                # Capture strengths as facts (strengths are GOLD)
                # AND connect to curiosity engine so video learnings boost curiosities
                for strength in analysis_result.get("strengths_observed", []):
                    strength_fact = TemporalFact.from_observation(
                        content=strength.get("strength", ""),
                        domain="strengths",
                        confidence=0.8,  # High confidence from direct observation
                    )
                    darshan.understanding.add_fact(strength_fact)
                    # Connect video learnings to curiosity engine
                    darshan._curiosities.on_observation_learned(strength_fact)
                    strengths_found.append(strength.get("strength", ""))

                # Also capture general observations as facts for understanding
                for observation in analysis_result.get("observations", []):
                    obs_domain = observation.get("domain", curiosity.domain or "general")
                    obs_fact = TemporalFact.from_observation(
                        content=observation.get("content", ""),
                        domain=obs_domain,
                        confidence=0.75,  # Good confidence from video observation
                    )
                    darshan.understanding.add_fact(obs_fact)
                    # Connect to curiosity engine
                    darshan._curiosities.on_observation_learned(obs_fact)

                # Add insights (parent-facing, no hypothesis)
                insights.extend(analysis_result.get("insights", []))

                # Capture capacity revealed and add to essence
                capacity = hypothesis_evidence.get("capacity_revealed", {})
                if capacity.get("description"):
                    logger.info(f"💪 Capacity revealed: {capacity.get('description')}")
                    # Add capacity as a strength fact
                    capacity_fact = TemporalFact.from_observation(
                        content=f"כוח שנצפה: {capacity.get('description')}",
                        domain="strengths",
                        confidence=0.85,
                    )
                    darshan.understanding.add_fact(capacity_fact)
                    darshan._curiosities.on_observation_learned(capacity_fact)
                    # Also add to essence core_qualities if essence exists
                    if darshan.understanding.essence:
                        if capacity.get('description') not in darshan.understanding.essence.core_qualities:
                            darshan.understanding.essence.core_qualities.append(capacity.get('description'))

                # Create curiosities from new questions raised by video
                # This makes video discoveries actionable for future exploration
                new_questions = hypothesis_evidence.get("new_questions_raised", [])
                for question_text in new_questions[:3]:  # Limit to top 3 to avoid overwhelm
                    logger.info(f"🔮 New curiosity from video: {question_text}")
                    new_curiosity = Question.create(
                        focus=question_text,
                        question=question_text,
                        domain=curiosity.domain,  # Inherit domain from parent curiosity
                        reasoning="New question raised from video analysis",
                        pull=0.6,  # Start moderately active
                    )
                    darshan._curiosities.add_curiosity(new_curiosity)

        # Persist changes
        await self._persist_darshan(family_id, darshan)

        # Determine overall status
        if validation_failed_count == len(pending_scenarios):
            status = "validation_failed"
        elif validation_failed_count > 0:
            status = "partial"  # Some passed, some failed
        else:
            status = "analyzed"

        return {
            "status": status,
            "cycle_id": cycle_id,
            "insights": insights,
            "evidence_added": evidence_added,
            "strengths_found": strengths_found,
            "validation_failed_count": validation_failed_count,
            "confidence_update": {
                "before": confidence_before,
                "after": curiosity.confidence,
                "verdict": hypothesis_evidence.get("overall_verdict", "unknown"),
            } if isinstance(curiosity, Hypothesis) and hypothesis_evidence else None,
        }

    async def _analyze_video(
        self,
        darshan: Darshan,
        curiosity: Hypothesis,
        scenario: VideoScenario,
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze a single video using Gemini's video capabilities.

        Adapted from the original VideoAnalysisService with wisdom:
        - Hypothesis-driven: PRIMARY job is evidence for/against hypothesis
        - Strengths-based: ALWAYS find strengths (non-negotiable)
        - Objective Evidence Protocol: Signs vs Symptoms, Show Don't Tell
        - Vocabulary mirroring: Use parent's words from stories/facts
        - Living Gestalt: See the whole child, not just problems

        Returns:
        - observations: List of {content, effect, timestamp} for evidence
        - insights: Parent-facing insights (warm, no hypothesis revealed)
        - hypothesis_evidence: Detailed evidence assessment
        - strengths_observed: Documented strengths from video
        """
        from pathlib import Path as PathLib

        child_name = darshan.child_name or "הילד/ה"

        # Build context from darshan
        stories_context = self._format_stories_for_llm(darshan.stories)
        observations_context = self._format_observations_for_llm(darshan.understanding.observations)
        strengths_context = self._extract_strengths(darshan)

        # Extract vocabulary from stories (parent's words)
        vocab_examples = self._extract_vocabulary_from_stories(darshan.stories)

        # Build the hypothesis-driven analysis prompt
        prompt = f"""# Role: Chitta - Hypothesis-Driven Video Analysis

**Role:** You are "Chitta," an expert AI child behavior analyst. Your framework combines **clinical observation standards** with **hypothesis-driven exploration** and **strengths-based developmental psychology**.

**Objective:** Analyze this video as part of an EXPLORATION CYCLE. Your primary job is to:
1. **Test the specific hypothesis** this video was designed to explore
2. **Provide evidence** - what supports or contradicts our working theories?
3. **See the whole child** - strengths, essence, and capacity alongside concerns

## Living Gestalt Philosophy

You see the WHOLE child, not just problems:
- **Essence first** - Who is this child? Temperament, energy, qualities
- **Strengths are data** - What they do well reveals capacity
- **Hypotheses are held lightly** - We're exploring, not confirming bias
- **Contradictions are gold** - When behavior doesn't fit, that's information

## VIDEO VALIDATION (CRITICAL - THIS IS A GATE!)

**STOP! Before ANY analysis, you MUST validate the video. If validation FAILS, you must NOT proceed with hypothesis testing.**

### Step 1: Scenario Match Check
Compare what was REQUESTED vs what was FILMED:
- **Requested:** "{scenario.what_to_film}"
- **Question:** Does the video show THIS scenario, or something completely different?

Examples of FAILED scenario match:
- Asked for "מעבר מפעילות לפעילות" but video shows child just playing/spinning
- Asked for "ארוחת בוקר" but video shows child at playground
- Asked for specific interaction but video shows unrelated activity

### Step 2: Child Verification Check
- Is ANY child visible in the video?
- If we know the child is ~3.5 years old, does the child in video match roughly?
- If the video shows a clearly different child (wrong age, different gender), this FAILS

### Step 3: GATE DECISION

**IF is_usable = false:**
- Set verdict to "inconclusive"
- Set confidence_level to "Low"
- Leave observations_for_evidence EMPTY []
- Leave supporting_evidence and contradicting_evidence EMPTY []
- Put ONE insight: "הסרטון שהועלה לא תואם למה שביקשנו לצלם. נא להעלות סרטון של [what was requested]"
- DO NOT analyze the video content for hypothesis evidence!

**IF is_usable = true:**
- Proceed with full analysis below

## Input Data

**Child Profile:**
- Name: **{child_name}**
- Known facts: {observations_context}

**Child's Strengths (IMPORTANT - document when you see these!):**
{strengths_context}

**Stories Shared by Parent (use their vocabulary!):**
{stories_context}

**Parent's Vocabulary to Mirror:**
{json.dumps(vocab_examples, ensure_ascii=False)}

## Hypothesis Being Tested (CRITICAL)

**Target Hypothesis:** {curiosity.theory or curiosity.focus}
**What We Hope to Learn:** {scenario.what_we_hope_to_learn}
**Focus Points (internal - what to look for):**
{chr(10).join(f'  - {fp}' for fp in scenario.focus_points)}

**Your PRIMARY TASK:** Provide evidence that helps confirm OR refute this hypothesis.
- What would we see if the hypothesis is TRUE?
- What would we see if it's FALSE?
- What do we actually observe?

## Video Assignment Context

**Title Given to Parent:** {scenario.title}
**Filming Instructions:** {scenario.what_to_film}
**Duration:** {scenario.duration_suggestion}

## CRITICAL: THE OBJECTIVE EVIDENCE PROTOCOL

You must strictly adhere to these rules when describing "Evidence":

1. **Signs vs. Symptoms:**
   - **Subjective (The Story):** "Child says they are upset." (This is narrative).
   - **Objective (The Observation):** "Child states 'I don't want to' while averting gaze, hunching shoulders, and lowering voice volume." (This is behavior).
   - **Rule:** NEVER accept a child's self-report as factual evidence. Instead, report the **act of saying it** and the **affect** shown.

2. **The "Show, Don't Tell" Rule:**
   - ❌ BAD: "Child was anxious"
   - ✅ GOOD: "Child bit lip, fidgeted with shirt hem, and had rapid breathing"

3. **Contextualize Speech:** If the evidence is verbal, describe the **prosody** (tone, volume, speed) and **accompanying gesture**.

4. **Use MM:SS Timestamps:** Every observation must include BOTH start and end times (e.g., "timestamp_start": "01:15", "timestamp_end": "01:23") to enable video clip extraction for reports

---

## Output JSON Structure

Return a valid JSON object with this structure.

**IMPORTANT: If video_validation.is_usable is FALSE, leave all evidence arrays EMPTY and set verdict to "inconclusive"!**

```json
{{
  "video_validation": {{
    "is_usable": "<boolean: FALSE if video doesn't match requested scenario or shows wrong child>",
    "scenario_matches": "<boolean: does video show what was requested in filming instructions?>",
    "what_video_shows": "<Brief description: 'ילד מסתובב על כיסא' not 'מעבר בין פעילויות'>",
    "child_visible": "<boolean: is child clearly visible?>",
    "child_appears_consistent": "<boolean: does child match expected age/profile?>",
    "validation_issues": ["<List specific issues: 'הסרטון מראה ילד משחק, לא מעבר בין פעילויות'>"],
    "recommendation": "<proceed_with_analysis|request_new_video>"
  }},

  "hypothesis_evidence": {{
    "// IMPORTANT": "If is_usable=false, set verdict=inconclusive, confidence=Low, and leave evidence arrays EMPTY",
    "target_hypothesis": "{curiosity.theory or curiosity.focus}",
    "overall_verdict": "<supports|contradicts|mixed|inconclusive>",
    "confidence_level": "<High|Moderate|Low>",
    "reasoning": "<2-3 sentences explaining what the video tells us about the hypothesis>",
    "supporting_evidence": [
      {{
        "observation": "<Specific behavior using parent's vocabulary>",
        "timestamp_start": "<MM:SS - when behavior starts>",
        "timestamp_end": "<MM:SS - when behavior ends>",
        "why_this_supports": "<Explain the connection>"
      }}
    ],
    "contradicting_evidence": [
      {{
        "observation": "<Specific behavior that contradicts>",
        "timestamp_start": "<MM:SS - when behavior starts>",
        "timestamp_end": "<MM:SS - when behavior ends>",
        "why_this_contradicts": "<Explain>"
      }}
    ],
    "capacity_revealed": {{
      "description": "<What capacity did the child demonstrate?>",
      "conditions_that_enabled_it": "<What conditions allowed this?>"
    }},
    "new_questions_raised": ["<Questions that emerged>"]
  }},

  "observations_for_evidence": [
    {{
      "content": "<Objective observation in Hebrew using parent's vocabulary>",
      "effect": "<supports|contradicts|transforms>",
      "timestamp_start": "<MM:SS - when behavior starts>",
      "timestamp_end": "<MM:SS - when behavior ends>",
      "domain": "<social|emotional|motor|cognitive|sensory|regulation>"
    }}
  ],

  "strengths_observed": [
    {{
      "strength": "<What the child did well>",
      "timestamp_start": "<MM:SS - when behavior starts>",
      "timestamp_end": "<MM:SS - when behavior ends>",
      "clinical_value": "<Why this matters developmentally>"
    }}
  ],

  "parent_facing_insights": [
    "<Warm insight 1 - NO hypothesis revealed, uses their vocabulary>",
    "<Warm insight 2 - focuses on what you SAW the child do>"
  ],

  "holistic_summary": {{
    "temperament_observed": "<What temperament qualities showed?>",
    "regulation_state": "<Regulated|Hypoaroused|Hyperaroused|Fluctuating>",
    "parent_child_dynamic": "<What did you notice about their interaction?>"
  }},

  "focus_point_findings": [
    {{
      "focus_point": "<From scenario.focus_points>",
      "finding": "<What we observed>",
      "confidence": "<High|Moderate|Low>"
    }}
  ],

  "suggested_next_steps": [
    {{
      "type": "<conversation|video|observation>",
      "description": "<What to explore next>",
      "why": "<Why this would help>"
    }}
  ]
}}
```

**CRITICAL REMINDERS:**
1. **VALIDATION IS A GATE** - If video doesn't match scenario, set is_usable=false and DO NOT analyze!
2. Use parent's vocabulary when describing behaviors
3. ALWAYS find strengths - this is NON-NEGOTIABLE (only if video is usable)
4. Use MM:SS format for all timestamps - include BOTH start AND end times for each observation
5. The parent NEVER sees the hypothesis - insights must be warm and general
6. Contradictions are valuable - if behavior doesn't match hypothesis, that's data
7. Return ONLY valid JSON, no additional text
8. **TIMESTAMPS ARE CRITICAL** - Each observation needs timestamp_start AND timestamp_end for video evidence in reports

**EXAMPLE OF FAILED VALIDATION:**
If asked to film "מעבר מפעילות לפעילות" but video shows child spinning on chair:
- is_usable: false
- scenario_matches: false
- what_video_shows: "ילד מסתובב על כיסא"
- validation_issues: ["הסרטון לא מראה מעבר בין פעילויות - מראה ילד משחק על כיסא"]
- verdict: "inconclusive"
- observations_for_evidence: []
- parent_facing_insights: ["הסרטון שהועלה לא תואם למה שביקשנו לצלם. נא להעלות סרטון של מעבר בין פעילויות."]
"""

        try:
            # Resolve video path - handle both relative and absolute paths
            video_path = scenario.video_path
            if video_path and not os.path.isabs(video_path):
                # Relative path - resolve from backend directory
                backend_dir = PathLib(__file__).parent.parent.parent  # chitta/video_service.py -> chitta -> app -> backend
                video_path = str(backend_dir / video_path)

            # Check if video file exists
            if not video_path or not os.path.exists(video_path):
                logger.warning(f"Video file not found: {video_path} (original: {scenario.video_path})")
                return self._create_simulated_analysis(child_name, curiosity, scenario)

            # Use Gemini's video analysis capability
            from google import genai
            from google.genai import types

            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.error("GEMINI_API_KEY not found")
                return self._create_simulated_analysis(child_name, curiosity, scenario)

            client = genai.Client(api_key=api_key)

            # Upload video to Gemini File API
            logger.info(f"📤 Uploading video to Gemini: {video_path}")
            uploaded_file = client.files.upload(file=video_path)

            # Wait for processing
            import time
            max_wait = 60
            wait_time = 0
            while uploaded_file.state == "PROCESSING" and wait_time < max_wait:
                logger.info(f"   Processing video... ({wait_time}s)")
                time.sleep(3)
                wait_time += 3
                uploaded_file = client.files.get(name=uploaded_file.name)

            if uploaded_file.state != "ACTIVE":
                logger.error(f"Video processing failed: {uploaded_file.state}")
                return self._create_simulated_analysis(child_name, curiosity, scenario)

            logger.info("🤖 Analyzing video with Gemini...")

            # Send video + prompt for analysis (use STRONG model from env)
            strong_model = os.getenv("STRONG_LLM_MODEL", "gemini-2.5-pro")
            logger.info(f"🎥 Using strong model for video analysis: {strong_model}")
            response = client.models.generate_content(
                model=strong_model,
                contents=[
                    uploaded_file,
                    prompt
                ],
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=6000,
                    response_mime_type="application/json",
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(
                        disable=True,
                        maximum_remote_calls=0
                    )
                )
            )

            # Extract content from response
            content = ""
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                content += part.text

            if not content:
                logger.error("Empty response from Gemini")
                return self._create_simulated_analysis(child_name, curiosity, scenario)

            # Parse JSON response
            result = json.loads(content)

            # Transform to our internal format
            return self._transform_analysis_result(result)

        except Exception as e:
            logger.error(f"Error analyzing video: {e}", exc_info=True)
            return self._create_simulated_analysis(child_name, curiosity, scenario)

    def _extract_vocabulary_from_stories(self, stories: List) -> Dict[str, str]:
        """Extract vocabulary patterns from parent's stories."""
        vocab = {}
        for story in stories[-5:]:
            # Simple extraction - in production would use NLP
            if "מרחף" in story.summary:
                vocab["מרחף"] = "לתאר קשיי קשב"
            if "מתפרץ" in story.summary:
                vocab["מתפרץ"] = "לתאר התנהגות אימפולסיבית"
            if "נסגר" in story.summary:
                vocab["נסגר"] = "לתאר נסיגה חברתית"
        return vocab

    def _transform_analysis_result(self, result: Dict) -> Dict[str, Any]:
        """Transform Gemini analysis to our internal format."""
        # Check video validation first
        video_validation = result.get("video_validation", {})
        is_usable = video_validation.get("is_usable", True)
        validation_issues = video_validation.get("validation_issues", [])

        if not is_usable or validation_issues:
            logger.warning(f"⚠️ Video validation issues: {validation_issues}")
            logger.warning(f"   What video shows: {video_validation.get('what_video_shows', 'unknown')}")
            logger.warning(f"   Recommendation: {video_validation.get('recommendation', 'unknown')}")

        # Extract observations for evidence
        observations = []
        for obs in result.get("observations_for_evidence", []):
            observations.append({
                "content": obs.get("content", ""),
                "effect": obs.get("effect", "supports"),
                "timestamp_start": obs.get("timestamp_start", obs.get("timestamp", "")),  # fallback for old format
                "timestamp_end": obs.get("timestamp_end", ""),
                "domain": obs.get("domain", "general"),
            })

        # Extract parent-facing insights
        insights = result.get("parent_facing_insights", [])

        # If validation failed, add a note to insights
        if not is_usable and validation_issues:
            insights = [f"שים לב: הסרטון שהועלה לא תואם לבקשה - {', '.join(validation_issues)}"] + insights

        # Extract hypothesis evidence for cycle update
        hypothesis_evidence = result.get("hypothesis_evidence", {})

        # If validation failed, override verdict to inconclusive
        if not is_usable:
            hypothesis_evidence["overall_verdict"] = "inconclusive"
            hypothesis_evidence["confidence_level"] = "Low"
            hypothesis_evidence["reasoning"] = f"Video validation failed: {', '.join(validation_issues) if validation_issues else 'unknown issue'}"

        # Extract strengths
        strengths = result.get("strengths_observed", [])

        # Determine verdict for insights view (parent-facing)
        verdict = "inconclusive"
        if is_usable:
            verdict = hypothesis_evidence.get("overall_verdict", "inconclusive")

        return {
            "observations": observations,
            "insights": insights,
            "hypothesis_evidence": hypothesis_evidence,
            "strengths_observed": strengths,
            "holistic_summary": result.get("holistic_summary", {}),
            "focus_point_findings": result.get("focus_point_findings", []),
            "suggested_next_steps": result.get("suggested_next_steps", []),
            # Video validation info for insights view
            "video_validation": video_validation,
            "verdict": verdict,
            "confidence_level": hypothesis_evidence.get("confidence_level", "Low"),
            # Parent-facing insight list
            "insights_for_parent": insights,
        }

    def _create_simulated_analysis(
        self,
        child_name: str,
        curiosity: Hypothesis,
        scenario: VideoScenario,
    ) -> Dict[str, Any]:
        """Create simulated analysis when video cannot be processed."""
        return {
            "observations": [{
                "content": f"צפיתי בסרטון של {child_name} - ניתוח מלא יתבצע כשהקובץ יהיה זמין",
                "effect": "neutral",
                "timestamp_start": "00:00",
                "timestamp_end": "00:00",
                "domain": "general",
            }],
            "insights": [
                f"קיבלתי את הסרטון של {child_name}. אעבור עליו בקרוב ואשתף תובנות.",
            ],
            "hypothesis_evidence": {
                "target_hypothesis": curiosity.theory or curiosity.focus,
                "overall_verdict": "inconclusive",
                "confidence_level": "Low",
                "reasoning": "ניתוח הסרטון בהמתנה",
                "supporting_evidence": [],
                "contradicting_evidence": [],
            },
            "strengths_observed": [],
            "holistic_summary": {},
            "focus_point_findings": [],
            "suggested_next_steps": [],
        }


# Singleton accessor
_video_service: Optional[VideoService] = None


def get_video_service(
    get_darshan: Callable[[str], Awaitable[Optional[Darshan]]] = None,
    persist_darshan: Callable[[str, Darshan], Awaitable[None]] = None,
    get_cards_callback: Callable[[Darshan], List[Dict]] = None,
) -> VideoService:
    """
    Get the VideoService instance.

    On first call, must provide callbacks. Subsequent calls return cached instance.
    """
    global _video_service
    if _video_service is None:
        if not all([get_darshan, persist_darshan, get_cards_callback]):
            raise ValueError("VideoService requires callbacks on first initialization")
        _video_service = VideoService(
            get_darshan=get_darshan,
            persist_darshan=persist_darshan,
            get_cards_callback=get_cards_callback,
        )
    return _video_service
