"""
Child Space Service - Living Portrait derivation (read-only)

Derives child space data for the Living Portrait UI:
- essence: The living portrait (narrative, strengths, explorations, facts)
- discoveries: Timeline of discovery milestones
- observations: Video gallery with AI insights
- share: Sharing options and status

This is pure read-only aggregation of Darshan state - no mutations.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from .gestalt import Darshan

logger = logging.getLogger(__name__)


class ChildSpaceService:
    """Derives child space data for Living Portrait UI."""

    def derive_child_space_full(self, gestalt: Darshan) -> Dict[str, Any]:
        """
        Derive complete ChildSpace data for the Living Portrait UI.

        Returns data for all four tabs:
        - essence: The living portrait (narrative, strengths, explorations, facts)
        - discoveries: Timeline of discovery milestones
        - observations: Video gallery with AI insights
        - share: Sharing options and status
        """
        return {
            "child_name": gestalt.child_name,
            "essence": self._derive_essence(gestalt),
            "discoveries": self._derive_discoveries(gestalt),
            "observations": self._derive_observations(gestalt),
            "share": self._derive_share_options(gestalt),
        }

    def derive_child_space_header(self, gestalt: Darshan) -> Dict[str, Any]:
        """
        Derive child space data for header.

        Returns minimal data for ChildSpaceHeader component:
        - child_name: For display
        - badges: Empty - status info belongs in context cards, not duplicated here

        The header is just a simple entry point to ChildSpace.
        All actionable status (videos, guidelines, insights) is shown via context cards.
        """
        return {
            "child_name": gestalt.child_name,
            "badges": [],
        }

    def _derive_essence(self, gestalt: Darshan) -> Dict[str, Any]:
        """
        Derive the Essence tab - the living portrait.

        REQUIRES Crystal to exist - the route ensures this via ensure_crystal_fresh().
        Crystal provides:
        - Essence narrative, temperament, core qualities
        - Cross-domain patterns
        - Intervention pathways

        This is the HOLISTIC view of the child - not fragments, but connections.
        """
        has_crystal = hasattr(gestalt, 'crystal') and gestalt.crystal is not None
        is_crystal_stale = has_crystal and gestalt.is_crystal_stale()

        # === 1. ESSENCE NARRATIVE ===
        narrative = None
        temperament = []
        core_qualities = []

        if has_crystal:
            crystal = gestalt.crystal
            narrative = crystal.essence_narrative
            temperament = crystal.temperament or []
            core_qualities = crystal.core_qualities or []

        # === 2. CROSS-DOMAIN PATTERNS ===
        patterns = []

        if has_crystal:
            for pattern in gestalt.crystal.patterns:
                patterns.append({
                    "description": pattern.description,
                    "domains": pattern.domains_involved,
                    "confidence": pattern.confidence,
                })

        # === 3. STRENGTHS & INTERESTS ===
        strengths = []
        interests = []

        for fact in gestalt.understanding.observations:
            if fact.domain == "strengths":
                strengths.append({
                    "domain": "general",  # LLM already categorized as "strengths"
                    "title_he": self._extract_strength_title(fact.content),
                    "content": fact.content,
                    "source": fact.source,
                })
            elif fact.domain == "interests":
                interests.append({
                    "content": fact.content,
                    "source": fact.source,
                })

        # Add strengths from video observations
        for cycle in gestalt.explorations:
            for scenario in cycle.video_scenarios:
                if scenario.analysis_result and scenario.status == "analyzed":
                    for strength in scenario.analysis_result.get("strengths_observed", []):
                        strength_text = strength.get("strength", "") if isinstance(strength, dict) else strength
                        if strength_text:
                            strengths.append({
                                "domain": "observed",
                                "title_he": strength_text,
                                "content": f"נצפה בסרטון: {scenario.title}",
                                "source": "video",
                            })

        # === 4. INTERVENTION PATHWAYS ===
        intervention_pathways = []

        if has_crystal:
            for pathway in gestalt.crystal.intervention_pathways:
                intervention_pathways.append({
                    "hook": pathway.hook,
                    "concern": pathway.concern,
                    "suggestion": pathway.suggestion,
                    "confidence": pathway.confidence,
                })

        # === 5. ACTIVE EXPLORATIONS ===
        active_explorations = []
        for cycle in gestalt.explorations:
            if cycle.status == "active":
                evidence_list = [
                    {"content": ev.content, "effect": ev.effect, "source": ev.source}
                    for ev in cycle.evidence
                ]
                has_video_pending = any(
                    s.status in ("pending", "uploaded") and s.video_path
                    for s in cycle.video_scenarios
                )
                has_video_analyzed = any(s.status == "analyzed" for s in cycle.video_scenarios)

                active_explorations.append({
                    "id": cycle.id,
                    "question": cycle.focus,
                    "theory": cycle.theory,
                    "confidence": cycle.confidence or 0.5,
                    "evidence_count": len(cycle.evidence),
                    "evidence": evidence_list,
                    "has_video_pending": has_video_pending,
                    "has_video_analyzed": has_video_analyzed,
                    "video_appropriate": cycle.video_appropriate,
                })

        # === 6. FACTS BY DOMAIN ===
        facts_by_domain = {}
        for fact in gestalt.understanding.observations:
            domain = fact.domain or "general"
            if domain in ("strengths", "interests"):
                continue
            if domain not in facts_by_domain:
                facts_by_domain[domain] = []
            facts_by_domain[domain].append(fact.content)

        # === 7. OPEN QUESTIONS ===
        open_questions = []
        if has_crystal:
            open_questions = gestalt.crystal.open_questions or []

        # === 8. EXPERT RECOMMENDATIONS ===
        expert_recommendations = []
        if has_crystal:
            for rec in gestalt.crystal.expert_recommendations or []:
                expert_recommendations.append({
                    "profession": rec.profession,
                    "specialization": rec.specialization,
                    "why_this_match": rec.why_this_match,
                    "recommended_approach": rec.recommended_approach,
                    "why_this_approach": rec.why_this_approach,
                    "what_to_look_for": rec.what_to_look_for,
                    "professional_summaries": [
                        {
                            "recipient_type": ps.recipient_type,
                            "who_this_child_is": ps.who_this_child_is,
                            "strengths_and_interests": ps.strengths_and_interests,
                            "what_parents_shared": ps.what_parents_shared,
                            "what_we_noticed": ps.what_we_noticed,
                            "what_remains_open": ps.what_remains_open,
                            "role_specific_section": ps.role_specific_section,
                            "invitation": ps.invitation,
                        }
                        for ps in (rec.professional_summaries or [])
                    ],
                    "confidence": rec.confidence,
                    "priority": rec.priority,
                })

        # === 9. PORTRAIT SECTIONS ===
        portrait_sections = []
        if has_crystal:
            for section in gestalt.crystal.portrait_sections or []:
                portrait_sections.append({
                    "title": section.title,
                    "icon": section.icon,
                    "content": section.content,
                    "content_type": section.content_type,
                })

        # Determine narrative status
        narrative_status = "available" if narrative else "forming"
        if is_crystal_stale:
            narrative_status = "updating"

        return {
            "narrative": narrative,
            "narrative_status": narrative_status,
            "temperament": temperament,
            "core_qualities": core_qualities,
            "patterns": patterns,
            "intervention_pathways": intervention_pathways,
            "interests": interests[:4],
            "expert_recommendations": expert_recommendations,
            "strengths": strengths[:6],
            "active_explorations": active_explorations,
            "open_questions": open_questions,
            "facts_by_domain": facts_by_domain,
            "portrait_sections": portrait_sections,
            "crystal_status": {
                "has_crystal": has_crystal,
                "is_stale": is_crystal_stale,
                "version": gestalt.crystal.version if has_crystal else 0,
            },
        }

    def _derive_discoveries(self, gestalt: Darshan) -> Dict[str, Any]:
        """Derive the Discoveries tab - journey timeline."""
        milestones = []

        milestone_type_icons = {
            "achievement": "✓",
            "concern": "⚠",
            "regression": "↓",
            "intervention": "→",
            "birth": "◯",
        }

        for dev_milestone in gestalt.understanding.milestones:
            timestamp = dev_milestone.occurred_at or dev_milestone.recorded_at
            age_str = ""
            if dev_milestone.age_months is not None:
                if dev_milestone.age_months < 0:
                    age_str = "בהריון"
                elif dev_milestone.age_months == 0:
                    age_str = "בלידה"
                else:
                    years = dev_milestone.age_months // 12
                    months = dev_milestone.age_months % 12
                    if years > 0 and months > 0:
                        age_str = f"גיל {years} שנים ו-{months} חודשים"
                    elif years > 0:
                        age_str = f"גיל {years} שנים" if years > 1 else "גיל שנה"
                    else:
                        age_str = f"גיל {months} חודשים"
            elif dev_milestone.age_description:
                age_str = dev_milestone.age_description

            icon = milestone_type_icons.get(dev_milestone.milestone_type, "·")
            milestones.append({
                "id": f"dev_{dev_milestone.id}",
                "timestamp": timestamp.isoformat() if timestamp else None,
                "type": "developmental",
                "title_he": f"{icon} {dev_milestone.description}",
                "description_he": age_str,
                "domain": dev_milestone.domain,
                "milestone_type": dev_milestone.milestone_type,
                "significance": "major" if dev_milestone.milestone_type in ["concern", "regression"] else "normal",
                "age_months": dev_milestone.age_months,
            })

        entry_type_mapping = {
            "session_started": "started",
            "exploration_started": "exploration_began",
            "story_captured": "insight",
            "milestone_recorded": "insight",
            "pattern_found": "pattern",
            "insight": "insight",
        }

        for entry in gestalt.journal:
            milestone_type = entry_type_mapping.get(entry.entry_type, "insight")

            milestones.append({
                "id": f"journal_{entry.timestamp.isoformat()}",
                "timestamp": entry.timestamp.isoformat(),
                "type": milestone_type,
                "title_he": entry.summary,
                "description_he": ", ".join(entry.learned) if entry.learned else "",
                "significance": "major" if entry.significance == "notable" else "normal",
            })

        for cycle in gestalt.explorations:
            for scenario in cycle.video_scenarios:
                if scenario.status == "analyzed" and scenario.analyzed_at:
                    insights = []
                    if scenario.analysis_result:
                        insights = scenario.analysis_result.get("insights", [])
                    description = insights[0] if insights else "ניתוח הסרטון הושלם"

                    milestones.append({
                        "id": f"video_{scenario.id}",
                        "timestamp": scenario.analyzed_at.isoformat(),
                        "type": "video_analyzed",
                        "title_he": f"צפינו: {scenario.title}",
                        "description_he": description if isinstance(description, str) else "",
                        "video_id": scenario.id,
                        "exploration_id": cycle.id,
                        "significance": "major",
                    })

        milestones.sort(key=lambda m: m["timestamp"] or "", reverse=True)

        days_since_start = 0
        if gestalt.journal:
            first_entry = min(gestalt.journal, key=lambda e: e.timestamp)
            days_since_start = (datetime.now() - first_entry.timestamp).days

        total_videos = sum(
            len([s for s in c.video_scenarios if s.video_path])
            for c in gestalt.explorations
        )

        insights_count = len([
            s for c in gestalt.explorations
            for s in c.video_scenarios
            if s.status == "analyzed"
        ])

        return {
            "milestones": milestones[:20],
            "days_since_start": days_since_start,
            "total_conversations": len(gestalt.journal),
            "total_videos": total_videos,
            "insights_discovered": insights_count,
        }

    def _derive_observations(self, gestalt: Darshan) -> Dict[str, Any]:
        """Derive the Observations tab - video gallery and pending scenarios."""
        videos = []
        pending_scenarios = []

        for cycle in gestalt.explorations:
            for scenario in cycle.video_scenarios:
                if scenario.video_path:
                    observations = []
                    strengths = []
                    insights = []

                    if scenario.analysis_result and scenario.status == "analyzed":
                        for obs in scenario.analysis_result.get("observations", []):
                            observations.append({
                                "content": obs.get("content", ""),
                                "timestamp_start": obs.get("timestamp_start", obs.get("timestamp", "")),
                                "timestamp_end": obs.get("timestamp_end", ""),
                                "domain": obs.get("domain", "general"),
                                "effect": obs.get("effect", "neutral"),
                            })

                        for s in scenario.analysis_result.get("strengths_observed", []):
                            if isinstance(s, dict):
                                strengths.append(s.get("strength", ""))
                            elif isinstance(s, str):
                                strengths.append(s)

                        insights = scenario.analysis_result.get("insights", [])

                    validation_info = {}
                    if scenario.status == "validation_failed" and scenario.analysis_result:
                        video_validation = scenario.analysis_result.get("video_validation", {})
                        validation_info = {
                            "what_video_shows": video_validation.get("what_video_shows", ""),
                            "validation_issues": video_validation.get("validation_issues", []),
                        }

                    videos.append({
                        "id": scenario.id,
                        "title": scenario.title,
                        "video_path": scenario.video_path,
                        "duration_seconds": 0,
                        "uploaded_at": scenario.uploaded_at.isoformat() if scenario.uploaded_at else None,
                        "status": scenario.status,
                        "analyzed_at": scenario.analyzed_at.isoformat() if scenario.analyzed_at else None,
                        "hypothesis_title": cycle.theory or cycle.focus,
                        "hypothesis_id": cycle.id,
                        "observations": observations,
                        "strengths_observed": strengths,
                        "insights": insights,
                        "what_to_film": scenario.what_to_film,
                        "rationale_for_parent": scenario.rationale_for_parent,
                        **validation_info,
                    })
                elif scenario.status == "pending" and scenario.what_to_film:
                    pending_scenarios.append({
                        "id": scenario.id,
                        "title": scenario.title,
                        "what_to_film": scenario.what_to_film,
                        "rationale_for_parent": scenario.rationale_for_parent,
                        "duration_suggestion": scenario.duration_suggestion,
                        "example_situations": scenario.example_situations or [],
                        "hypothesis_title": cycle.theory or cycle.focus,
                        "hypothesis_id": cycle.id,
                        "cycle_focus": cycle.focus,
                        "created_at": scenario.created_at.isoformat() if scenario.created_at else None,
                        "reminder_dismissed": scenario.reminder_dismissed,
                    })

        videos.sort(
            key=lambda v: v["uploaded_at"] or "1970-01-01",
            reverse=True
        )

        analyzed = sum(1 for v in videos if v["status"] == "analyzed")
        pending = sum(1 for v in videos if v["status"] in ["pending", "uploaded"])

        return {
            "videos": videos,
            "pending_scenarios": pending_scenarios,
            "total_videos": len(videos),
            "analyzed_count": analyzed,
            "pending_count": pending,
        }

    def _derive_share_options(self, gestalt: Darshan) -> Dict[str, Any]:
        """
        Derive the Share tab options.

        COHERENCE PRINCIPLE: Share is an extension of Crystal - the expert recommendations
        that appear in Crystal also appear here, making it feel like one unified experience.
        """
        has_observations = len(gestalt.understanding.observations) >= 3
        has_exploration = len(gestalt.explorations) > 0
        can_generate = has_observations and has_exploration

        not_ready_reason = None
        if not can_generate:
            if not has_observations:
                not_ready_reason = "עדיין לא צברנו מספיק מידע. המשיכו לשוחח איתנו."
            else:
                not_ready_reason = "נשמח להכיר את הילד קצת יותר לפני שנוכל לשתף."

        expert_recommendations = []
        has_crystal = hasattr(gestalt, 'crystal') and gestalt.crystal is not None
        if has_crystal and gestalt.crystal.expert_recommendations:
            for rec in gestalt.crystal.expert_recommendations:
                expert_recommendations.append({
                    "profession": rec.profession,
                    "specialization": rec.specialization,
                    "why_this_match": rec.why_this_match,
                    "recommended_approach": rec.recommended_approach,
                    "why_this_approach": rec.why_this_approach,
                    "what_to_look_for": rec.what_to_look_for,
                    "professional_summaries": [
                        {
                            "recipient_type": ps.recipient_type,
                            "who_this_child_is": ps.who_this_child_is,
                            "strengths_and_interests": ps.strengths_and_interests,
                            "what_parents_shared": ps.what_parents_shared,
                            "what_we_noticed": ps.what_we_noticed,
                            "what_remains_open": ps.what_remains_open,
                            "role_specific_section": ps.role_specific_section,
                            "invitation": ps.invitation,
                        }
                        for ps in (rec.professional_summaries or [])
                    ],
                    "confidence": rec.confidence,
                    "priority": rec.priority,
                })

        previous_summaries = []
        if hasattr(gestalt, 'shared_summaries') and gestalt.shared_summaries:
            sorted_summaries = sorted(
                gestalt.shared_summaries,
                key=lambda s: s.created_at,
                reverse=True
            )
            for summary in sorted_summaries[:10]:
                previous_summaries.append({
                    "id": summary.id,
                    "recipient": summary.recipient_description,
                    "created_at": summary.created_at.isoformat(),
                    "comprehensive": summary.comprehensive,
                    "preview": (summary.content[:100] + "...") if len(summary.content) > 100 else summary.content,
                })

        return {
            "can_generate": can_generate,
            "not_ready_reason": not_ready_reason,
            "expert_recommendations": expert_recommendations,
            "previous_summaries": previous_summaries,
        }

    def _extract_strength_title(self, content: str) -> str:
        """Extract a short title from strength content."""
        words = content.split()
        if len(words) <= 4:
            return content
        return " ".join(words[:4]) + "..."


# Singleton accessor
_child_space_service: Optional[ChildSpaceService] = None


def get_child_space_service() -> ChildSpaceService:
    """Get the singleton ChildSpaceService instance."""
    global _child_space_service
    if _child_space_service is None:
        _child_space_service = ChildSpaceService()
    return _child_space_service
