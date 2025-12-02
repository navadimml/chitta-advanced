"""
Card Derivation Service - Derive UI cards from exploration cycles

Cards are portals to actions and deep views. They derive from:
1. Active exploration cycles and their artifacts
2. Pending insights from reflection
3. Journey milestones

Cards show:
- "Video guidelines ready - review and start filming"
- "2 videos pending analysis - tap to start"
- "New insight about motor development"

Cards do NOT show:
- Internal hypothesis details (would bias parents)
- Raw evidence
- Clinical language
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.models.child import Child
from app.models.user_session import UserSession
from app.models.active_card import ActiveCard, CardDisplayMode
from app.models.exploration import ExplorationCycle, CycleArtifact

logger = logging.getLogger(__name__)


# === Card Types ===

CARD_TYPE_GUIDELINES = "video_guidelines"
CARD_TYPE_VIDEO_PENDING = "video_pending_analysis"
CARD_TYPE_REPORT_READY = "report_ready"
CARD_TYPE_INSIGHT = "pending_insight"
CARD_TYPE_MILESTONE = "journey_milestone"
CARD_TYPE_UPLOAD_PROMPT = "upload_prompt"


def derive_cards_from_child(
    child: Child,
    session: UserSession,
    language: str = "he"
) -> List[ActiveCard]:
    """
    Derive all active cards from child state.

    Cards come from:
    1. Exploration cycle artifacts (guidelines, reports)
    2. Pending videos
    3. Pending insights
    4. Journey milestones

    Returns list of ActiveCard objects.
    """
    cards = []

    # 1. Cards from exploration cycles
    for cycle in child.active_exploration_cycles():
        cards.extend(_cards_from_cycle(cycle, child, language))

    # 2. Cards from pending insights
    cards.extend(_cards_from_insights(child, language))

    # 3. Cards from journey milestones
    cards.extend(_cards_from_milestones(child, session, language))

    # Remove any cards that have been dismissed in this session
    dismissed_ids = set(session.dismissed_card_moments.keys())
    cards = [c for c in cards if c.card_id not in dismissed_ids]

    # Sort by priority
    cards.sort(key=lambda c: c.priority, reverse=True)

    return cards


def _cards_from_cycle(
    cycle: ExplorationCycle,
    child: Child,
    language: str
) -> List[ActiveCard]:
    """Derive cards from an exploration cycle."""
    cards = []

    for artifact in cycle.artifacts:
        if not artifact.is_actionable:
            continue

        if artifact.type == "video_guidelines":
            cards.append(_create_guidelines_card(artifact, cycle, child, language))

        elif artifact.type == "video_analysis":
            # Video analysis ready - part of synthesis flow
            pass  # Handled by pending videos card

        elif artifact.type == "synthesis_report":
            cards.append(_create_report_card(artifact, cycle, child, language))

    # Check for pending videos
    if cycle.status == "evidence_gathering" and cycle.has_pending_videos:
        cards.append(_create_upload_prompt_card(cycle, child, language))

    return [c for c in cards if c is not None]


def _create_guidelines_card(
    artifact: CycleArtifact,
    cycle: ExplorationCycle,
    child: Child,
    language: str
) -> Optional[ActiveCard]:
    """Create card for video guidelines artifact."""
    if artifact.status not in ["ready", "needs_update"]:
        return None

    if language == "he":
        if artifact.status == "needs_update":
            title = "📹 הנחיות צילום מעודכנות"
            body = "יש לנו הנחיות חדשות לצילום בעקבות השיחה שלנו"
        else:
            title = "📹 הנחיות הצילום מוכנות"
            remaining = artifact.videos_remaining
            if remaining > 0:
                body = f"מחכים ל-{remaining} סרטונים. לחצו כדי לראות מה לצלם"
            else:
                body = "צפו בהנחיות הצילום המותאמות אישית"
    else:
        if artifact.status == "needs_update":
            title = "📹 Updated filming guidelines"
            body = "We have new filming guidance based on our conversation"
        else:
            title = "📹 Filming guidelines ready"
            remaining = artifact.videos_remaining
            if remaining > 0:
                body = f"Waiting for {remaining} videos. Tap to see what to film"
            else:
                body = "View your personalized filming guide"

    return ActiveCard(
        card_id=f"guidelines_{artifact.id}",
        display_mode=CardDisplayMode.FLOATING,
        priority=80 if artifact.status == "needs_update" else 70,
        content={
            "title": title,
            "body": body,
            "artifact_id": artifact.id,
            "cycle_id": cycle.id,
            "videos_remaining": artifact.videos_remaining,
        },
        actions=[
            {"action": "view_artifact", "artifact_id": artifact.id},
            {"action": "upload_video", "cycle_id": cycle.id},
        ],
        created_by_moment=f"cycle_{cycle.id}",
    )


def _create_report_card(
    artifact: CycleArtifact,
    cycle: ExplorationCycle,
    child: Child,
    language: str
) -> Optional[ActiveCard]:
    """Create card for synthesis report artifact."""
    if artifact.status not in ["ready", "needs_update"]:
        return None

    child_name = child.name or ("הילד/ה" if language == "he" else "your child")

    if language == "he":
        title = "📋 הסיכום מוכן"
        body = f"הסיכום שלנו על {child_name} מוכן לצפייה"
    else:
        title = "📋 Summary ready"
        body = f"Our summary about {child_name} is ready to view"

    return ActiveCard(
        card_id=f"report_{artifact.id}",
        display_mode=CardDisplayMode.FLOATING,
        priority=90,  # High priority for reports
        content={
            "title": title,
            "body": body,
            "artifact_id": artifact.id,
            "cycle_id": cycle.id,
        },
        actions=[
            {"action": "view_artifact", "artifact_id": artifact.id},
        ],
        created_by_moment=f"cycle_{cycle.id}",
    )


def _create_upload_prompt_card(
    cycle: ExplorationCycle,
    child: Child,
    language: str
) -> Optional[ActiveCard]:
    """Create card prompting video upload."""
    if not cycle.video_method:
        return None

    pending_scenarios = [s for s in cycle.video_method.scenarios if not s.uploaded]
    if not pending_scenarios:
        return None

    if language == "he":
        count = len(pending_scenarios)
        title = f"📱 ממתינים ל-{count} סרטונים"
        body = "העלו את הסרטונים כדי שנוכל להמשיך"
    else:
        count = len(pending_scenarios)
        title = f"📱 Waiting for {count} videos"
        body = "Upload videos so we can continue"

    return ActiveCard(
        card_id=f"upload_prompt_{cycle.id}",
        display_mode=CardDisplayMode.FLOATING,
        priority=75,
        content={
            "title": title,
            "body": body,
            "cycle_id": cycle.id,
            "pending_count": len(pending_scenarios),
            "scenarios": [s.title for s in pending_scenarios],
        },
        actions=[
            {"action": "upload_video", "cycle_id": cycle.id},
        ],
        created_by_moment=f"cycle_{cycle.id}",
    )


def _cards_from_insights(child: Child, language: str) -> List[ActiveCard]:
    """Create cards from pending insights."""
    cards = []

    unshared = child.understanding.unshared_insights()
    # Only show high importance insights as cards
    high_importance = [i for i in unshared if i.importance == "high"]

    for insight in high_importance[:2]:  # Max 2 insight cards
        if language == "he":
            title = "💡 תובנה חדשה"
            body = insight.content[:100]
        else:
            title = "💡 New insight"
            body = insight.content[:100]

        cards.append(ActiveCard(
            card_id=f"insight_{insight.id}",
            display_mode=CardDisplayMode.FLOATING,
            priority=60,
            content={
                "title": title,
                "body": body,
                "insight_id": insight.id,
            },
            actions=[
                {"action": "show_insight", "insight_id": insight.id},
            ],
            created_by_moment=f"insight_{insight.id}",
        ))

    return cards


def _cards_from_milestones(
    child: Child,
    session: UserSession,
    language: str
) -> List[ActiveCard]:
    """Create cards from journey milestones."""
    cards = []

    # Milestone: First video uploaded
    if child.video_count == 1 and child.videos[0].analysis_status == "pending":
        if language == "he":
            title = "🎬 הסרטון הראשון התקבל!"
            body = "נתחיל לנתח אותו ברגע"
        else:
            title = "🎬 First video received!"
            body = "We'll start analyzing it shortly"

        cards.append(ActiveCard(
            card_id="milestone_first_video",
            display_mode=CardDisplayMode.TOAST,
            priority=85,
            content={"title": title, "body": body},
            auto_dismiss_seconds=10,
            created_by_moment="milestone_first_video",
        ))

    # Milestone: All videos analyzed
    total_videos = child.video_count
    analyzed_videos = len(child.analyzed_videos())
    if total_videos > 0 and total_videos == analyzed_videos:
        # Check if we already showed this milestone recently
        milestone_id = f"milestone_all_analyzed_{total_videos}"
        if milestone_id not in session.dismissed_card_moments:
            if language == "he":
                title = "✅ כל הסרטונים נותחו"
                body = "אנחנו מוכנים להמשיך לשלב הבא"
            else:
                title = "✅ All videos analyzed"
                body = "We're ready for the next step"

            cards.append(ActiveCard(
                card_id=milestone_id,
                display_mode=CardDisplayMode.FLOATING,
                priority=80,
                content={"title": title, "body": body},
                created_by_moment=milestone_id,
            ))

    return cards


# === Card Action Handlers ===

def handle_card_action(
    action: str,
    params: Dict[str, Any],
    child: Child,
    session: UserSession
) -> Dict[str, Any]:
    """
    Handle a card action.

    Returns action result dict.
    """
    if action == "view_artifact":
        artifact_id = params.get("artifact_id")
        artifact = child.get_artifact(artifact_id)
        if artifact:
            return {
                "action": "navigate",
                "target": "artifact_view",
                "artifact_id": artifact_id,
                "artifact": artifact,
            }
        return {"error": "Artifact not found"}

    elif action == "upload_video":
        cycle_id = params.get("cycle_id")
        cycle = child.get_cycle(cycle_id)
        if cycle and cycle.video_method:
            return {
                "action": "navigate",
                "target": "video_upload",
                "cycle_id": cycle_id,
                "scenarios": [
                    {"id": s.id, "title": s.title, "what_to_film": s.what_to_film}
                    for s in cycle.video_method.scenarios
                    if not s.uploaded
                ],
            }
        return {"error": "Cycle not found or no video method"}

    elif action == "show_insight":
        insight_id = params.get("insight_id")
        # Mark insight as shared
        for insight in child.understanding.pending_insights:
            if insight.id == insight_id:
                insight.mark_shared()
                return {
                    "action": "show_message",
                    "message": insight.content,
                }
        return {"error": "Insight not found"}

    elif action == "dismiss":
        card_id = params.get("card_id")
        session.dismiss_moment(card_id)
        return {"action": "dismissed", "card_id": card_id}

    return {"error": f"Unknown action: {action}"}
