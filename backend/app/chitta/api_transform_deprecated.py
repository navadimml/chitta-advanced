"""
API Transformation - Strip internal fields from API responses

Parents should see:
- Progress indicators
- Action items (cards)
- Journey milestones
- High-level summaries

Parents should NOT see:
- Hypothesis details (would bias observations)
- Internal evidence chains
- Clinical pattern detection
- Confidence scores

This module provides transformation functions to ensure
internal data doesn't leak to the frontend.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from app.models.child import Child
from app.models.user_session import UserSession
from app.models.exploration import ExplorationCycle, CycleArtifact


def transform_child_for_api(
    child: Child,
    include_artifacts: bool = True,
    include_videos: bool = True,
) -> Dict[str, Any]:
    """
    Transform Child to API-safe representation.

    Strips:
    - understanding (hypotheses, patterns, evidence)
    - exploration_cycles (internal details)

    Keeps:
    - identity
    - essence (high-level)
    - strengths
    - concerns (parent's own words)
    - history (factual)
    - family
    - videos (metadata only)
    - artifacts (references only)
    """
    result = {
        "id": child.id,
        "identity": {
            "name": child.identity.name,
            "age_years": child.identity.age_years,
            "gender": child.identity.gender,
        },
        "essence": {
            "core_qualities": child.essence.core_qualities,
            "energy_pattern": child.essence.energy_pattern,
        },
        "strengths": {
            "abilities": child.strengths.abilities,
            "interests": child.strengths.interests,
            "what_lights_them_up": child.strengths.what_lights_them_up,
        },
        "concerns": {
            "primary_areas": child.concerns.primary_areas,
            # Note: We include parent's own words, not clinical interpretations
            "parent_narrative": child.concerns.parent_narrative,
        },
        "created_at": child.created_at.isoformat(),
        "updated_at": child.updated_at.isoformat(),
    }

    if include_videos:
        result["videos"] = [
            transform_video_for_api(v)
            for v in child.videos
        ]

    if include_artifacts:
        # Build artifacts dict directly from exploration cycles
        result["artifacts"] = {
            artifact.id: transform_artifact_for_api(artifact)
            for cycle in child.exploration_cycles
            for artifact in cycle.artifacts
        }

    # Add high-level progress indicators (no internal details)
    # Count artifacts across all cycles
    total_artifacts = sum(len(cycle.artifacts) for cycle in child.exploration_cycles)
    result["progress"] = {
        "videos_total": child.video_count,
        "videos_analyzed": len(child.analyzed_videos()),
        "active_cycles": len(child.active_exploration_cycles()),
        "artifacts_count": total_artifacts,
    }

    return result


def transform_video_for_api(video) -> Dict[str, Any]:
    """Transform video to API-safe representation."""
    return {
        "id": video.id,
        "scenario": video.scenario,
        "uploaded_at": video.uploaded_at.isoformat(),
        "duration_seconds": video.duration_seconds,
        "analysis_status": video.analysis_status,
        # Note: file_path/file_url not exposed for security
        # Note: analyst_context not exposed (internal)
    }


def transform_artifact_for_api(artifact) -> Dict[str, Any]:
    """Transform artifact to API-safe representation."""
    if hasattr(artifact, 'model_dump'):
        # Pydantic model
        data = artifact.model_dump()
    elif isinstance(artifact, dict):
        data = artifact
    else:
        data = {"content": str(artifact)}

    # Safe fields to expose
    safe_fields = ["artifact_id", "status", "content_format", "created_at", "ready_at"]

    result = {k: data.get(k) for k in safe_fields if k in data}

    # Content is included if it's meant for parents
    # Video guidelines and parent reports are parent-facing
    # Video analysis contains clinical details - strip those
    artifact_type = data.get("artifact_type", data.get("type", ""))
    if artifact_type in ["video_guidelines", "parent_report"]:
        result["content"] = data.get("content")
    elif artifact_type == "video_analysis":
        # Strip clinical details from video analysis
        content = data.get("content", {})
        if isinstance(content, dict):
            result["content"] = {
                "summary": content.get("summary"),
                # Note: observations, clinical_impressions not exposed
            }
        else:
            result["content"] = None

    return result


def transform_session_for_api(session: UserSession) -> Dict[str, Any]:
    """
    Transform session to API-safe representation.

    Strips:
    - memory (internal relationship tracking)
    - reflection tracking
    - semantic verification cache

    Keeps:
    - session identity
    - message count (not content)
    - active cards
    - UI state
    """
    return {
        "session_id": session.session_id,
        "child_id": session.child_id,
        "message_count": session.message_count,
        "turn_count": session.turn_count,
        "active_cards": [
            transform_card_for_api(c)
            for c in session.active_cards
            if not c.dismissed
        ],
        "current_view": session.current_view,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "last_message_at": session.last_message_at.isoformat() if session.last_message_at else None,
    }


def transform_card_for_api(card) -> Dict[str, Any]:
    """Transform card to API-safe representation."""
    return {
        "card_id": card.card_id,
        "instance_id": card.instance_id,
        "display_mode": card.display_mode,
        "priority": card.priority,
        "content": card.content,
        "actions": card.actions,
        "created_at": card.created_at.isoformat(),
    }


def transform_cycle_for_api(cycle: ExplorationCycle) -> Dict[str, Any]:
    """
    Transform exploration cycle to API-safe representation.

    Strips:
    - hypothesis_ids (internal linking)
    - Detailed method configurations
    - Evidence items

    Keeps:
    - High-level status
    - Artifact references
    - Progress indicators
    """
    return {
        "id": cycle.id,
        "status": cycle.status,
        "focus_description": cycle.focus_description,
        "methods_used": cycle.methods_used if hasattr(cycle, 'methods_used') else [],
        "created_at": cycle.created_at.isoformat(),
        "progress": {
            "videos_pending": cycle.has_pending_videos if hasattr(cycle, 'has_pending_videos') else False,
            "artifacts_count": len(cycle.artifacts),
            "artifacts_ready": len([a for a in cycle.artifacts if a.status == "ready"]),
        },
    }


def transform_artifact_summary_for_api(artifact: CycleArtifact) -> Dict[str, Any]:
    """Transform cycle artifact to API summary."""
    return {
        "id": artifact.id,
        "type": artifact.type,
        "status": artifact.status,
        "videos_expected": artifact.expected_videos,
        "videos_uploaded": artifact.uploaded_videos,
        "created_at": artifact.created_at.isoformat(),
    }


# === Convenience functions ===

def build_api_response(
    child: Child,
    session: UserSession,
    cards: List[Any],
    additional_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build a complete API response with all transformations applied.

    This is the main entry point for constructing API responses
    that include child and session data.
    """
    response = {
        "child": transform_child_for_api(child),
        "session": transform_session_for_api(session),
        "cards": [transform_card_for_api(c) for c in cards],
    }

    if additional_data:
        response.update(additional_data)

    return response


def strip_internal_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generic function to strip known internal fields from any dict.

    Use as a safety net for data that might have internal fields.
    """
    internal_fields = {
        # Hypothesis/understanding internals
        "hypotheses", "hypothesis_ids", "related_hypothesis_ids",
        "evidence", "supporting_evidence", "contradicting_evidence",
        "patterns", "pending_insights",
        # Evidence internals
        "evidence_items", "evidence_chain",
        # Confidence/scoring internals
        "confidence", "support_ratio",
        # Internal tracking
        "exploration_cycles", "cycle_id",
        "analyst_context", "focus_points",
        # Memory internals
        "memory", "parent_style", "emotional_patterns",
        "vocabulary_preferences", "context_assets",
        # Session internals
        "semantic_verification", "reflection_tracking",
    }

    result = {}
    for key, value in data.items():
        if key in internal_fields:
            continue
        if isinstance(value, dict):
            result[key] = strip_internal_fields(value)
        elif isinstance(value, list):
            result[key] = [
                strip_internal_fields(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value

    return result
