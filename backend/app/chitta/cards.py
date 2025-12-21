"""
Cards Service - Context card derivation

Derives context cards from Darshan state for the parent UI.

Card Philosophy: Two Categories of Artifacts
=============================================

1. CYCLE-BOUND ARTIFACTS -> Context Cards
   - Emerge from a specific exploration (hypothesis, question)
   - Require timely action from the parent
   - Part of an active investigation flow
   - The gestalt reaching out: "I need something from you to continue"

2. HOLISTIC ARTIFACTS -> ChildSpace (User-Initiated)
   - Reflect the whole understanding (not a specific cycle)
   - Created when the user decides they need them
   - Serve external purposes (sharing, documentation)
   - The user pulls from gestalt: "Show me what you understand"

Card Types:
-----------
ACTION CARDS (request something from parent):
- video_suggestion: Hypothesis formed, video would help, needs consent
- video_guidelines_generating: Parent accepted, generating guidelines
- video_guidelines_ready: Guidelines ready, needs upload
- video_uploaded: Video uploaded, ready for analysis
- video_validation_failed: Video doesn't match request, retry

FEEDBACK CARDS (acknowledge, just needs dismissal):
- video_analyzed: Analysis complete, insights woven into understanding

NOT context cards (holistic, user-initiated from Space):
- Shareable summaries -> Share tab
- Crystal/Essence -> Essence tab
- Synthesis reports -> User requests when ready
"""

from typing import Dict, Any, List, Optional
import logging

from .gestalt import Darshan

logger = logging.getLogger(__name__)


class CardsService:
    """Derives context cards from Darshan state."""

    def derive_cards(self, gestalt: Darshan) -> List[Dict]:
        """
        Derive context cards from current gestalt state.

        Returns list of card dicts ready for frontend consumption.
        """
        cards = []

        for cycle in gestalt.explorations:
            if cycle.status != "active":
                continue

            # === VIDEO CARDS (consent-first) ===

            # Stage 1: Suggest video (parent hasn't decided yet)
            # Guidelines NOT generated - only after consent
            if cycle.can_suggest_video() and (cycle.confidence or 0.5) < 0.7:
                cards.append({
                    "type": "video_suggestion",
                    "title": "אפשר להבין את זה טוב יותר בסרטון",
                    "description": "רוצה שאכין לך הנחיות צילום מותאמות?",
                    "dismissible": True,
                    "actions": [
                        {"label": "כן, בבקשה", "action": "accept_video", "primary": True},
                        {"label": "לא עכשיו", "action": "decline_video"}
                    ],
                    "cycle_id": cycle.id,
                    "priority": "medium",
                })
                break  # One suggestion at a time

            # Stage 1.5: Guidelines generating (parent accepted, waiting for LLM)
            if (cycle.video_accepted and
                cycle.guidelines_status == "generating" and
                not cycle.video_scenarios):
                cards.append({
                    "type": "video_guidelines_generating",
                    "title": "מכין הנחיות צילום...",
                    "description": "רק עוד רגע, מכין הנחיות מותאמות אישית",
                    "dismissible": False,
                    "loading": True,
                    "cycle_id": cycle.id,
                    "priority": "high",
                })
                break

            # Stage 2: Check for validation failures FIRST (takes priority)
            failed_scenarios = [s for s in cycle.video_scenarios if s.status == "validation_failed"]
            if failed_scenarios:
                # Get the first failed scenario's validation message
                failed = failed_scenarios[0]
                validation_result = failed.analysis_result.get("video_validation", {}) if failed.analysis_result else {}
                what_video_shows = validation_result.get("what_video_shows", "")
                cards.append({
                    "type": "video_validation_failed",
                    "title": "הסרטון לא תואם לבקשה",
                    "description": what_video_shows if what_video_shows else "נא להעלות סרטון שמתאים להנחיות",
                    "dismissible": True,
                    "actions": [
                        {"label": "ראה הנחיות", "action": "view_guidelines", "primary": True},
                        {"label": "העלה סרטון חדש", "action": "upload_video"}
                    ],
                    "cycle_id": cycle.id,
                    "scenario_id": failed.id,
                    "validation_issues": validation_result.get("validation_issues", []),
                    "priority": "high",
                })
                break

            # Stage 2.1: Video needs confirmation (has concerns, parent should verify)
            needs_confirmation = [s for s in cycle.video_scenarios if s.status == "needs_confirmation"]
            if needs_confirmation:
                scenario = needs_confirmation[0]
                confirmation_reasons = scenario.analysis_result.get("_confirmation_reasons", []) if scenario.analysis_result else []
                reason_text = confirmation_reasons[0] if confirmation_reasons else "רוצים לוודא שזה הסרטון הנכון"
                cards.append({
                    "type": "video_needs_confirmation",
                    "title": "האם זה הסרטון הנכון?",
                    "description": reason_text,
                    "dismissible": False,
                    "actions": [
                        {"label": "כן, זה נכון", "action": "confirm_video", "primary": True},
                        {"label": "לא, אעלה אחר", "action": "reject_video"}
                    ],
                    "cycle_id": cycle.id,
                    "scenario_id": scenario.id,
                    "confirmation_reasons": confirmation_reasons,
                    "priority": "high",
                })
                break

            # Stage 2.5: Guidelines ready (parent accepted, guidelines generated, no uploads yet)
            # Only show if at least one scenario hasn't been dismissed or rejected
            pending_scenarios = [
                s for s in cycle.video_scenarios
                if s.status == "pending" and not s.reminder_dismissed
            ]
            if (cycle.video_accepted and
                pending_scenarios and
                not cycle.has_pending_videos() and
                not cycle.has_analyzed_videos()):
                cards.append({
                    "type": "video_guidelines_ready",
                    "title": "הנחיות צילום מוכנות",
                    "description": f"{len(pending_scenarios)} תרחישים מותאמים אישית",
                    "dismissible": True,
                    "actions": [
                        {"label": "צפה בהנחיות", "action": "view_guidelines", "primary": True},
                        {"label": "אל תזכיר", "action": "dismiss_reminder"},
                        {"label": "לא רלוונטי", "action": "reject_guidelines"},
                    ],
                    "cycle_id": cycle.id,
                    "scenario_ids": [s.id for s in pending_scenarios],
                    "priority": "high",
                })
                break

            # Stage 3: Video uploaded, waiting for analysis
            if cycle.has_pending_videos():
                pending_count = sum(1 for s in cycle.video_scenarios if s.status == "uploaded")
                cards.append({
                    "type": "video_uploaded",
                    "title": "סרטון מוכן לצפייה",
                    "description": f"{pending_count} סרטונים מחכים לניתוח",
                    "dismissible": False,
                    "actions": [
                        {"label": "נתח את הסרטונים", "action": "analyze_videos", "primary": True}
                    ],
                    "cycle_id": cycle.id,
                    "priority": "high",
                })
                break

            # Stage 4: Video analyzed - FEEDBACK card (not action card)
            # This acknowledges the parent's effort in filming and uploading.
            # Unlike action cards, this just needs dismissal - insights are woven into conversation.
            analyzed_scenarios = [s for s in cycle.video_scenarios if s.status == "analyzed"]
            if analyzed_scenarios:
                cards.append({
                    "type": "video_analyzed",
                    "title": "ראיתי את הסרטון",
                    "description": "יש לי כמה תובנות - נוכל לדבר עליהן בשיחה.",
                    "dismissible": True,
                    "feedback_card": True,  # Marks this as feedback, not action
                    "actions": [
                        {"label": "הבנתי", "action": "dismiss", "primary": True}
                    ],
                    "cycle_id": cycle.id,
                    "scenario_ids": [s.id for s in analyzed_scenarios],
                    "priority": "medium",  # Lower than action cards
                })
                break

        # NOTE: No "synthesis_available" card here.
        # Synthesis/summaries are HOLISTIC artifacts - user pulls them from ChildSpace,
        # not pushed via context cards. Context cards are for CYCLE-BOUND artifacts
        # that need timely parent action.

        # === BASELINE VIDEO SUGGESTION ===
        # Early in conversation, before hypotheses form, suggest baseline video
        # This is a "discovery" video - helps us see the child naturally
        if not cards:  # Only if no other cards pending
            message_count = len(gestalt.session_history)
            has_any_video = any(
                scenario.video_path
                for cycle in gestalt.explorations
                for scenario in cycle.video_scenarios
            )
            if not has_any_video and gestalt._curiosities.should_suggest_baseline_video(message_count):
                cards.append({
                    "type": "baseline_video_suggestion",
                    "title": "אשמח לראות את הילד/ה",
                    "description": "סרטון קצר של רגע יומיומי יעזור לי להכיר אותו/ה טוב יותר.",
                    "dismissible": True,
                    "actions": [
                        {"label": "כן, אכין סרטון", "action": "accept_baseline_video", "primary": True},
                        {"label": "אולי מאוחר יותר", "action": "dismiss", "primary": False},
                    ],
                    "priority": "low",  # Softer suggestion than hypothesis-driven
                })

        return cards


# Singleton accessor
_cards_service: Optional[CardsService] = None


def get_cards_service() -> CardsService:
    """Get the singleton CardsService instance."""
    global _cards_service
    if _cards_service is None:
        _cards_service = CardsService()
    return _cards_service
