"""
Reflection Service - Deep Background Processing

The "slow brain" of Chitta. While conversation runs fast (1-2 sec),
reflection runs in the background to:
1. Detect patterns across hypotheses
2. Update hypothesis confidence based on evidence
3. Distill conversation memory
4. Check artifact staleness
5. Generate pending insights

Design principles:
- Flow-based: Queue immediately, process when ready
- Batching: Collect all pending tasks for a child before processing
- Non-blocking: Never delays conversation response
- Eventual consistency: Updates appear in next context build
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict

from app.models.child import Child
from app.models.user_session import UserSession
from app.models.memory import ConversationMemory
from app.models.understanding import (
    Evidence,
    Hypothesis,
    Pattern,
    PendingInsight,
)
from app.models.exploration import check_artifact_staleness

logger = logging.getLogger(__name__)


class ReflectionTask:
    """A task waiting for reflection processing."""

    def __init__(
        self,
        child_id: str,
        task_type: str,
        data: Dict[str, Any],
    ):
        self.child_id = child_id
        self.task_type = task_type  # "conversation", "video_analyzed", "evidence_added"
        self.data = data
        self.created_at = datetime.now()


class ReflectionQueue:
    """
    Queue for reflection tasks.

    Batches tasks by child_id so all pending tasks for a child
    are processed together.
    """

    def __init__(self):
        self._tasks: Dict[str, List[ReflectionTask]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self._processing: set = set()  # Children currently being processed

    async def add(self, task: ReflectionTask):
        """Add a task to the queue."""
        async with self._lock:
            self._tasks[task.child_id].append(task)
            logger.debug(f"Queued reflection task: {task.task_type} for {task.child_id}")

    async def get_tasks_for_child(self, child_id: str) -> List[ReflectionTask]:
        """Get and clear all tasks for a child (batching)."""
        async with self._lock:
            if child_id in self._processing:
                return []  # Already being processed
            tasks = self._tasks.pop(child_id, [])
            if tasks:
                self._processing.add(child_id)
            return tasks

    async def mark_complete(self, child_id: str):
        """Mark processing complete for a child."""
        async with self._lock:
            self._processing.discard(child_id)

    def pending_children(self) -> List[str]:
        """Get list of children with pending tasks."""
        return list(self._tasks.keys())

    def pending_count(self, child_id: str) -> int:
        """Get count of pending tasks for a child."""
        return len(self._tasks.get(child_id, []))


class ReflectionService:
    """
    Service for deep background processing.

    Usage:
        service = ReflectionService()

        # Queue a task (immediate, non-blocking)
        await service.queue_conversation_reflection(child_id, session)

        # Process pending tasks (background)
        asyncio.create_task(service.process_pending(child_id))
    """

    def __init__(self):
        self._queue = ReflectionQueue()
        self._llm = None  # Lazy initialization

    def _get_llm(self):
        """Lazy load LLM provider (using strong model for reflection)."""
        if self._llm is None:
            import os
            from app.services.llm.factory import create_llm_provider

            # Use strong model for reflection (deep reasoning)
            model = os.getenv("STRONG_LLM_MODEL", "gemini-2.5-pro")
            provider = os.getenv("LLM_PROVIDER", "gemini")

            self._llm = create_llm_provider(
                provider_type=provider,
                model=model,
                use_enhanced=True
            )
        return self._llm

    # === Queue Methods ===

    async def queue_conversation_reflection(
        self,
        child_id: str,
        session: UserSession,
    ):
        """Queue reflection after conversation turns."""
        # Get messages to analyze (archived + recent active)
        archived = session.archived_messages()
        recent = session.active_messages()[-10:]  # Last 10 active

        task = ReflectionTask(
            child_id=child_id,
            task_type="conversation",
            data={
                "session_id": session.session_id,
                "archived_messages": [
                    {"role": m.role, "content": m.content}
                    for m in archived
                ],
                "recent_messages": [
                    {"role": m.role, "content": m.content}
                    for m in recent
                ],
                "turn_count": session.turn_count,
            }
        )
        await self._queue.add(task)

    async def queue_evidence_reflection(
        self,
        child_id: str,
        evidence: Evidence,
        hypothesis_id: Optional[str] = None,
    ):
        """Queue reflection after new evidence added."""
        task = ReflectionTask(
            child_id=child_id,
            task_type="evidence_added",
            data={
                "evidence_id": evidence.id,
                "evidence_content": evidence.content,
                "evidence_source": evidence.source,
                "evidence_domain": evidence.domain,
                "related_hypothesis_id": hypothesis_id,
            }
        )
        await self._queue.add(task)

    async def queue_video_reflection(
        self,
        child_id: str,
        video_id: str,
        analysis_artifact_id: str,
    ):
        """Queue reflection after video analysis."""
        task = ReflectionTask(
            child_id=child_id,
            task_type="video_analyzed",
            data={
                "video_id": video_id,
                "analysis_artifact_id": analysis_artifact_id,
            }
        )
        await self._queue.add(task)

    # === Processing Methods ===

    async def process_pending(self, child_id: str) -> Dict[str, Any]:
        """
        Process all pending reflection tasks for a child.

        Batches all tasks and processes them together.
        """
        tasks = await self._queue.get_tasks_for_child(child_id)
        if not tasks:
            return {"status": "no_tasks"}

        logger.info(f"🧠 Processing {len(tasks)} reflection tasks for {child_id}")

        try:
            # Get current state
            from app.services.unified_state_service import get_unified_state_service
            unified = get_unified_state_service()
            child = unified.get_child(child_id)
            session = await unified.get_or_create_session_async(child_id)

            results = {
                "patterns_detected": [],
                "hypotheses_updated": [],
                "insights_generated": [],
                "memory_updated": False,
                "artifacts_checked": [],
            }

            # Process by task type
            conversation_tasks = [t for t in tasks if t.task_type == "conversation"]
            evidence_tasks = [t for t in tasks if t.task_type == "evidence_added"]
            video_tasks = [t for t in tasks if t.task_type == "video_analyzed"]

            # 1. Distill conversation memory
            if conversation_tasks:
                memory_result = await self._distill_conversation_memory(
                    child, session, conversation_tasks
                )
                if memory_result.get("updated"):
                    results["memory_updated"] = True

            # 2. Process evidence and detect patterns
            if evidence_tasks or conversation_tasks:
                pattern_result = await self._detect_patterns(child, tasks)
                results["patterns_detected"] = pattern_result.get("patterns", [])
                results["hypotheses_updated"] = pattern_result.get("hypotheses_updated", [])

            # 3. Process video analyses
            if video_tasks:
                video_result = await self._process_video_insights(child, video_tasks)
                results["insights_generated"].extend(video_result.get("insights", []))

            # 4. Check artifact staleness
            staleness_result = self._check_artifact_staleness(child)
            results["artifacts_checked"] = staleness_result.get("checked", [])

            # 5. Generate pending insights
            insights_result = await self._generate_insights(child, results)
            results["insights_generated"].extend(insights_result.get("insights", []))

            # Persist updates
            from app.services.child_service import get_child_service
            get_child_service().save_child(child)

            session.mark_reflection_complete()
            await unified._persist_session(session)

            logger.info(f"✅ Reflection complete for {child_id}: {results}")
            return {"status": "complete", "results": results}

        except Exception as e:
            logger.error(f"Reflection failed for {child_id}: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

        finally:
            await self._queue.mark_complete(child_id)

    async def _distill_conversation_memory(
        self,
        child: Child,
        session: UserSession,
        tasks: List[ReflectionTask],
    ) -> Dict[str, Any]:
        """
        Distill conversation into memory.

        Updates:
        - parent_style (communication style)
        - vocabulary_preferences (words parent uses)
        - topics_discussed (with depth)
        - context_assets (people, places, things mentioned)
        """
        # Collect all messages from tasks
        all_messages = []
        for task in tasks:
            all_messages.extend(task.data.get("archived_messages", []))
            all_messages.extend(task.data.get("recent_messages", []))

        if not all_messages:
            return {"updated": False}

        # Build prompt for memory distillation
        conversation_text = "\n".join([
            f"{m['role']}: {m['content']}"
            for m in all_messages
        ])

        prompt = f"""Analyze this conversation and extract relationship memory.

<conversation>
{conversation_text}
</conversation>

<current_memory>
parent_style: {session.memory.parent_style or "unknown"}
emotional_patterns: {session.memory.emotional_patterns or "unknown"}
vocabulary: {session.memory.vocabulary_preferences}
topics_discussed: {[t.topic for t in session.memory.topics_discussed]}
context_assets: {session.memory.context_assets}
</current_memory>

Extract:
1. parent_style: How does this parent communicate? (e.g., "anxious, needs reassurance", "direct, practical")
2. emotional_patterns: How do they open up? (e.g., "shares more when feeling heard")
3. new_vocabulary: Hebrew words/expressions they use (for mirroring)
4. topics_with_depth: Topics discussed and depth ("mentioned", "explored", "deep_dive")
5. new_context_assets: Specific people, places, toys mentioned (e.g., "סבתא רחל", "לגו נינג'ה")

Return JSON:
{{
  "parent_style": "...",
  "emotional_patterns": "...",
  "new_vocabulary": ["word1", "word2"],
  "topics": [{{"topic": "motor_concerns", "depth": "explored"}}],
  "new_context_assets": ["asset1", "asset2"]
}}
"""

        try:
            from app.services.llm.base import Message
            llm = self._get_llm()

            response = await llm.chat(
                messages=[Message(role="user", content=prompt)],
                temperature=0.3,
                max_tokens=1000,
            )

            import json
            # Parse JSON from response
            content = response.content or "{}"
            # Extract JSON if wrapped in markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            data = json.loads(content.strip())

            # Update memory
            if data.get("parent_style"):
                session.memory.update_style(data["parent_style"])
            if data.get("emotional_patterns"):
                session.memory.update_emotional_patterns(data["emotional_patterns"])
            for word in data.get("new_vocabulary", []):
                session.memory.add_vocabulary(word)
            for topic_data in data.get("topics", []):
                session.memory.mark_topic_discussed(
                    topic_data["topic"],
                    topic_data.get("depth", "mentioned")
                )
            for asset in data.get("new_context_assets", []):
                session.memory.add_context_asset(asset)

            return {"updated": True, "data": data}

        except Exception as e:
            logger.error(f"Memory distillation failed: {e}")
            return {"updated": False, "error": str(e)}

    async def _detect_patterns(
        self,
        child: Child,
        tasks: List[ReflectionTask],
    ) -> Dict[str, Any]:
        """
        Detect patterns across hypotheses.

        Looks for:
        - Connections between domains (motor + sensory -> sensory processing)
        - Contradictions that need new hypotheses
        - Hypotheses needing confidence updates
        """
        active_hypotheses = child.active_hypotheses()
        if len(active_hypotheses) < 2:
            return {"patterns": [], "hypotheses_updated": []}

        # Build hypothesis summary
        hypothesis_text = "\n".join([
            f"- [{h.id}] {h.theory} (domain: {h.domain}, confidence: {h.confidence:.0%}, evidence: {len(h.evidence)})"
            for h in active_hypotheses
        ])

        # Get evidence from tasks
        new_evidence = []
        for task in tasks:
            if task.task_type == "evidence_added":
                new_evidence.append(task.data)
            elif task.task_type == "conversation":
                # Extract potential evidence from conversation
                for msg in task.data.get("recent_messages", []):
                    if msg["role"] == "user":
                        new_evidence.append({
                            "content": msg["content"],
                            "source": "conversation",
                        })

        evidence_text = "\n".join([
            f"- {e.get('content', '')[:100]}... (source: {e.get('source', 'unknown')})"
            for e in new_evidence[:10]
        ])

        prompt = f"""Analyze hypotheses and recent evidence for patterns.

<active_hypotheses>
{hypothesis_text}
</active_hypotheses>

<recent_evidence>
{evidence_text}
</recent_evidence>

Detect:
1. Patterns: Connections across hypotheses (e.g., "motor + transitions + food textures → sensory processing")
2. Evidence effects: How new evidence affects hypothesis confidence
3. Contradictions: Evidence that contradicts hypotheses

Return JSON:
{{
  "patterns": [
    {{
      "theme": "sensory processing involvement",
      "description": "Motor, transition, and food texture concerns may all relate to sensory processing",
      "related_hypothesis_ids": ["h1", "h2"],
      "confidence": 0.7
    }}
  ],
  "evidence_effects": [
    {{
      "hypothesis_id": "h1",
      "effect": "supports",
      "reason": "Parent mentioned specific texture avoidance"
    }}
  ],
  "contradictions": []
}}
"""

        try:
            from app.services.llm.base import Message
            llm = self._get_llm()

            response = await llm.chat(
                messages=[Message(role="user", content=prompt)],
                temperature=0.3,
                max_tokens=1500,
            )

            import json
            content = response.content or "{}"
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            data = json.loads(content.strip())

            patterns_created = []
            hypotheses_updated = []

            # Create patterns
            for p_data in data.get("patterns", []):
                pattern = Pattern(
                    theme=p_data["theme"],
                    description=p_data["description"],
                    related_hypotheses=p_data.get("related_hypothesis_ids", []),
                    confidence=p_data.get("confidence", 0.5),
                    source="reflection",
                )
                child.add_pattern(pattern)
                patterns_created.append(pattern.theme)

            # Apply evidence effects
            for effect in data.get("evidence_effects", []):
                hyp_id = effect.get("hypothesis_id")
                hypothesis = child.get_hypothesis(hyp_id)
                if hypothesis:
                    # Create synthetic evidence from the effect
                    evidence = Evidence(
                        source="reflection",
                        content=effect.get("reason", "Pattern detected"),
                        domain=hypothesis.domain,
                    )
                    hypothesis.add_evidence(evidence, effect.get("effect", "neutral"))
                    hypotheses_updated.append(hyp_id)

            return {
                "patterns": patterns_created,
                "hypotheses_updated": hypotheses_updated,
            }

        except Exception as e:
            logger.error(f"Pattern detection failed: {e}")
            return {"patterns": [], "hypotheses_updated": [], "error": str(e)}

    async def _process_video_insights(
        self,
        child: Child,
        tasks: List[ReflectionTask],
    ) -> Dict[str, Any]:
        """
        Process insights from video analyses.

        Links video observations to hypotheses and creates new evidence.
        """
        insights = []

        for task in tasks:
            video_id = task.data.get("video_id")
            artifact_id = task.data.get("analysis_artifact_id")

            # Get the analysis artifact
            artifact = child.get_artifact(artifact_id)
            if not artifact:
                continue

            # Extract observations from artifact content
            content = artifact.content if hasattr(artifact, 'content') else {}
            if isinstance(content, str):
                import json
                try:
                    content = json.loads(content)
                except:
                    continue

            observations = content.get("observations", [])

            # Create evidence for relevant hypotheses
            for obs in observations:
                domain = obs.get("domain")
                description = obs.get("description", "")

                # Find hypotheses in same domain
                for hypothesis in child.active_hypotheses():
                    if hypothesis.domain == domain:
                        evidence = Evidence(
                            source="video",
                            content=f"[Video {video_id}] {description}",
                            domain=domain,
                        )
                        # Determine effect based on observation
                        effect = "neutral"
                        if obs.get("supports_concerns"):
                            effect = "supports"
                        elif obs.get("contradicts_concerns"):
                            effect = "contradicts"

                        hypothesis.add_evidence(evidence, effect)
                        insights.append({
                            "video_id": video_id,
                            "hypothesis_id": hypothesis.id,
                            "effect": effect,
                        })

        return {"insights": insights}

    def _check_artifact_staleness(self, child: Child) -> Dict[str, Any]:
        """
        Check if any artifacts are stale and need updating.

        Uses the check_artifact_staleness function from exploration module.
        """
        checked = []

        for cycle in child.active_exploration_cycles():
            # Build hypothesis dict for staleness check
            hypotheses = {h.id: h for h in child.understanding.hypotheses}
            check_artifact_staleness(cycle, hypotheses)
            checked.append(cycle.id)

        return {"checked": checked}

    async def _generate_insights(
        self,
        child: Child,
        reflection_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate pending insights to share in conversation.

        Insights are queued for natural sharing, not immediate display.
        """
        insights = []

        # Generate insight for new patterns
        for pattern in reflection_results.get("patterns_detected", []):
            insight = PendingInsight(
                content=f"שמתי לב לקשר אפשרי: {pattern}",
                importance="medium",
                share_when="when_relevant",
            )
            child.understanding.add_insight(insight)
            insights.append(insight.content)

        # Generate insight if multiple hypotheses strengthened
        updated = reflection_results.get("hypotheses_updated", [])
        if len(updated) >= 2:
            insight = PendingInsight(
                content="יש לי כמה תובנות חדשות על מה שדיברנו",
                importance="medium",
                share_when="next_turn",
            )
            child.understanding.add_insight(insight)
            insights.append(insight.content)

        return {"insights": insights}


# Singleton
_reflection_service: Optional[ReflectionService] = None


def get_reflection_service() -> ReflectionService:
    """Get singleton ReflectionService instance."""
    global _reflection_service
    if _reflection_service is None:
        _reflection_service = ReflectionService()
    return _reflection_service
