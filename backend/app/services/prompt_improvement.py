"""
Prompt Improvement Service

Analyzes expert corrections to generate actionable prompt improvement suggestions.

This service:
1. Aggregates correction patterns by type, severity, and target
2. Maps corrections to specific prompt/tool sections
3. Generates ranked suggestions based on frequency and severity
4. Includes expert reasoning as examples for prompt improvements
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from collections import defaultdict
from datetime import datetime

from app.db.repositories import UnitOfWork


# =============================================================================
# CORRECTION TYPE TO PROMPT MAPPING
# =============================================================================

# Maps correction types to the prompt/tool sections they affect
CORRECTION_TO_PROMPT_SECTION = {
    # Tool-specific issues
    "domain_change": {
        "section": "TOOL_NOTICE → domain",
        "description": "AI chose wrong developmental domain",
        "affects": ["domain enum definitions", "domain selection guidance"],
    },
    "extraction_error": {
        "section": "TOOL_NOTICE, TOOL_CAPTURE_STORY",
        "description": "Observation text doesn't match what parent said",
        "affects": ["observation extraction instructions", "situational language guidance"],
    },
    "missed_signal": {
        "section": "Perception System Prompt",
        "description": "AI missed something important in the message",
        "affects": ["what to look for", "domains to consider", "signal sensitivity"],
    },
    "hallucination": {
        "section": "All tools",
        "description": "AI invented information not in the conversation",
        "affects": ["grounding instructions", "confidence thresholds"],
    },
    "evidence_reclassify": {
        "section": "TOOL_ADD_EVIDENCE → effect",
        "description": "Wrong supports/contradicts/transforms classification",
        "affects": ["effect definitions", "evidence interpretation guidance"],
    },
    "timing_issue": {
        "section": "TOOL_WONDER → video_appropriate",
        "description": "Video suggested too early or when not needed",
        "affects": ["video_value guidance", "when to suggest video"],
    },
    "certainty_adjustment": {
        "section": "TOOL_WONDER, TOOL_NOTICE → certainty",
        "description": "Certainty value was wrong",
        "affects": ["certainty scale calibration", "confidence guidance"],
    },
    "response_issue": {
        "section": "Response Generation Prompt",
        "description": "Problem with the AI's conversational response",
        "affects": ["response tone", "response content", "turn guidance"],
    },
}

# Maps missed signal types to what should be enhanced
SIGNAL_TYPE_TO_ENHANCEMENT = {
    "observation": "Enhance notice tool usage - AI missed extractable observations",
    "curiosity": "Enhance wonder tool usage - AI missed exploration opportunities",
    "hypothesis": "Enhance hypothesis generation - AI missed testable theories",
}


@dataclass
class PromptSuggestion:
    """A single suggestion for improving the prompts."""
    priority: int  # 1 = highest priority
    section: str  # Which prompt section to modify
    issue: str  # What's wrong
    suggestion: str  # How to fix it
    examples: List[Dict[str, Any]] = field(default_factory=list)  # Expert reasoning examples
    correction_count: int = 0  # How many corrections this is based on
    severity_score: float = 0.0  # Weighted severity (critical=4, high=3, medium=2, low=1)


@dataclass
class PromptImprovementReport:
    """Complete report of prompt improvement suggestions."""
    generated_at: datetime
    total_corrections: int
    total_missed_signals: int
    suggestions: List[PromptSuggestion]
    stats: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "generated_at": self.generated_at.isoformat(),
            "total_corrections": self.total_corrections,
            "total_missed_signals": self.total_missed_signals,
            "suggestion_count": len(self.suggestions),
            "suggestions": [
                {
                    "priority": s.priority,
                    "section": s.section,
                    "issue": s.issue,
                    "suggestion": s.suggestion,
                    "examples": s.examples,
                    "correction_count": s.correction_count,
                    "severity_score": round(s.severity_score, 2),
                }
                for s in self.suggestions
            ],
            "stats": self.stats,
        }


class PromptImprovementService:
    """
    Service for generating prompt improvement suggestions.

    Analyzes expert corrections to find patterns and generates
    actionable suggestions for improving the AI's prompts.
    """

    # Severity weights for prioritization
    SEVERITY_WEIGHTS = {
        "critical": 4.0,
        "high": 3.0,
        "medium": 2.0,
        "low": 1.0,
    }

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def generate_suggestions(
        self,
        unused_only: bool = True,
        min_corrections: int = 1,
    ) -> PromptImprovementReport:
        """
        Generate prompt improvement suggestions based on correction patterns.

        Args:
            unused_only: Only analyze corrections not yet used in training
            min_corrections: Minimum corrections needed to generate a suggestion

        Returns:
            PromptImprovementReport with ranked suggestions
        """
        # Get correction stats
        correction_stats = await self.uow.dashboard.corrections.get_correction_stats()
        signal_stats = await self.uow.dashboard.missed_signals.get_signal_stats()

        # Get all corrections for analysis
        corrections = await self.uow.dashboard.corrections.get_all_with_context(
            used_in_training=False if unused_only else None
        )

        # Get all missed signals
        missed_signals = await self.uow.dashboard.missed_signals.get_all()

        # Analyze patterns
        suggestions = []

        # 1. Analyze corrections by type
        type_suggestions = self._analyze_by_correction_type(corrections, min_corrections)
        suggestions.extend(type_suggestions)

        # 2. Analyze missed signals
        signal_suggestions = self._analyze_missed_signals(missed_signals, min_corrections)
        suggestions.extend(signal_suggestions)

        # 3. Rank suggestions by priority
        suggestions = self._rank_suggestions(suggestions)

        # Assign priorities
        for i, suggestion in enumerate(suggestions):
            suggestion.priority = i + 1

        return PromptImprovementReport(
            generated_at=datetime.utcnow(),
            total_corrections=correction_stats["total"],
            total_missed_signals=signal_stats["total"],
            suggestions=suggestions,
            stats={
                "corrections": correction_stats,
                "missed_signals": signal_stats,
            },
        )

    def _analyze_by_correction_type(
        self,
        corrections: List,
        min_corrections: int,
    ) -> List[PromptSuggestion]:
        """Analyze corrections grouped by type."""
        by_type = defaultdict(list)

        for correction in corrections:
            by_type[correction.correction_type].append(correction)

        suggestions = []

        for correction_type, type_corrections in by_type.items():
            if len(type_corrections) < min_corrections:
                continue

            # Get mapping info
            mapping = CORRECTION_TO_PROMPT_SECTION.get(correction_type, {
                "section": "General",
                "description": f"Corrections of type {correction_type}",
                "affects": ["Unknown section"],
            })

            # Calculate severity score
            severity_score = sum(
                self.SEVERITY_WEIGHTS.get(c.severity, 2.0)
                for c in type_corrections
            )

            # Extract examples (expert reasoning is GOLD)
            examples = []
            for c in type_corrections[:5]:  # Top 5 examples
                example = {
                    "original": c.original_value,
                    "corrected": c.corrected_value,
                    "expert_reasoning": c.expert_reasoning,
                    "target_type": c.target_type,
                    "severity": c.severity,
                }
                examples.append(example)

            # Generate suggestion text
            suggestion_text = self._generate_suggestion_text(
                correction_type,
                type_corrections,
                mapping,
            )

            suggestions.append(PromptSuggestion(
                priority=0,  # Will be set later
                section=mapping["section"],
                issue=f"{mapping['description']} ({len(type_corrections)} occurrences)",
                suggestion=suggestion_text,
                examples=examples,
                correction_count=len(type_corrections),
                severity_score=severity_score,
            ))

        return suggestions

    def _analyze_missed_signals(
        self,
        missed_signals: List,
        min_corrections: int,
    ) -> List[PromptSuggestion]:
        """Analyze missed signals grouped by type and domain."""
        by_type = defaultdict(list)
        by_domain = defaultdict(list)

        for signal in missed_signals:
            by_type[signal.signal_type].append(signal)
            if signal.domain:
                by_domain[signal.domain].append(signal)

        suggestions = []

        # Suggestions by signal type
        for signal_type, type_signals in by_type.items():
            if len(type_signals) < min_corrections:
                continue

            enhancement = SIGNAL_TYPE_TO_ENHANCEMENT.get(
                signal_type,
                f"Enhance {signal_type} detection"
            )

            examples = []
            for s in type_signals[:5]:
                examples.append({
                    "content": s.content,
                    "domain": s.domain,
                    "why_important": s.why_important,
                    "expert_name": s.expert_name,
                })

            suggestions.append(PromptSuggestion(
                priority=0,
                section="Perception System Prompt",
                issue=f"Missed {signal_type} signals ({len(type_signals)} occurrences)",
                suggestion=f"{enhancement}. Expert examples show what was missed.",
                examples=examples,
                correction_count=len(type_signals),
                severity_score=len(type_signals) * 2.5,  # Missed signals are important
            ))

        # Suggestions by domain (if certain domains are frequently missed)
        for domain, domain_signals in by_domain.items():
            if len(domain_signals) < min_corrections:
                continue

            examples = []
            for s in domain_signals[:3]:
                examples.append({
                    "content": s.content,
                    "why_important": s.why_important,
                })

            suggestions.append(PromptSuggestion(
                priority=0,
                section=f"Domain: {domain}",
                issue=f"Frequently missing signals in {domain} domain ({len(domain_signals)} times)",
                suggestion=f"Add more specific guidance for detecting {domain} signals. Consider adding examples in the domain description.",
                examples=examples,
                correction_count=len(domain_signals),
                severity_score=len(domain_signals) * 2.0,
            ))

        return suggestions

    def _generate_suggestion_text(
        self,
        correction_type: str,
        corrections: List,
        mapping: Dict,
    ) -> str:
        """Generate actionable suggestion text based on correction type."""
        base_suggestions = {
            "domain_change": (
                "Review domain enum definitions and add clearer boundaries. "
                "Consider adding examples in tool description showing which domain to use for ambiguous cases. "
                f"Affects: {', '.join(mapping.get('affects', []))}."
            ),
            "extraction_error": (
                "Strengthen instructions for extracting observations from parent messages. "
                "Add emphasis on using parent's exact words where possible. "
                "Review situational language examples."
            ),
            "missed_signal": (
                "Expand the list of signals to look for in the perception prompt. "
                "Add specific examples of subtle but important signals. "
                "Consider lowering threshold for signal detection."
            ),
            "hallucination": (
                "Add stronger grounding instructions. "
                "Emphasize that AI must ONLY use information explicitly present in conversation. "
                "Add validation step before each tool call."
            ),
            "evidence_reclassify": (
                "Clarify the distinction between supports/contradicts/transforms. "
                "Add more examples in add_evidence tool description. "
                "Consider adding intermediate options if needed."
            ),
            "timing_issue": (
                "Review video_appropriate and video_value guidance. "
                "Add clearer criteria for when video is truly needed. "
                "Emphasize not suggesting video too early in conversation."
            ),
            "certainty_adjustment": (
                "Recalibrate certainty scale with clearer anchors. "
                "Add examples: 'certainty 0.3 means X, 0.7 means Y'. "
                "Consider reducing default certainty values."
            ),
            "response_issue": (
                "Review response generation prompt for tone and content. "
                "Check turn guidance generation. "
                "Ensure warm Hebrew language guidelines are followed."
            ),
        }

        return base_suggestions.get(
            correction_type,
            f"Review and update {mapping['section']} based on expert feedback."
        )

    def _rank_suggestions(
        self,
        suggestions: List[PromptSuggestion],
    ) -> List[PromptSuggestion]:
        """Rank suggestions by priority (severity score * correction count)."""
        # Sort by combined score (higher = more important)
        return sorted(
            suggestions,
            key=lambda s: s.severity_score * (1 + s.correction_count * 0.1),
            reverse=True,
        )

    async def get_correction_examples_for_type(
        self,
        correction_type: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get detailed examples for a specific correction type."""
        corrections = await self.uow.dashboard.corrections.get_all_with_context(
            correction_type=correction_type
        )

        examples = []
        for c in corrections[:limit]:
            examples.append({
                "id": str(c.id),
                "turn_id": c.turn_id,
                "child_id": c.child_id,
                "target_type": c.target_type,
                "target_id": c.target_id,
                "original_value": c.original_value,
                "corrected_value": c.corrected_value,
                "expert_reasoning": c.expert_reasoning,
                "expert_name": c.expert_name,
                "severity": c.severity,
                "created_at": c.created_at.isoformat(),
            })

        return examples
