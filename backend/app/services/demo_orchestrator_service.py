"""
Demo Orchestrator Service

Manages interactive demo mode that runs in the real UI.
Triggers with natural language ("show me a demo" / "הראה לי דמו").
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from app.services.interview_service import get_interview_service, ExtractedData
from app.services.artifact_generation_service import ArtifactGenerationService
from app.models.artifact import Artifact

logger = logging.getLogger(__name__)


class DemoMessage(BaseModel):
    """Single message in demo scenario"""
    role: str  # "user" or "assistant"
    content: str  # Hebrew text
    delay_ms: int = 2000  # Delay before this message
    trigger_artifact: Optional[str] = None  # Artifact to generate after this
    card_hint: Optional[str] = None  # Which card should appear


class DemoScenario(BaseModel):
    """Complete demo scenario"""
    scenario_id: str
    name: str  # Hebrew
    name_en: str
    description: str
    duration_estimate: str  # "2-3 minutes"

    # Mock child profile
    child_profile: Dict[str, Any]

    # Scripted conversation (Chitta-led!)
    messages: List[DemoMessage]

    # When to trigger artifact generation
    artifact_trigger_at_step: int = 6  # After message 6


class DemoState(BaseModel):
    """Current demo session state"""
    demo_family_id: str
    scenario_id: str
    current_step: int = 0
    started_at: datetime
    is_paused: bool = False
    is_active: bool = True


class DemoOrchestratorService:
    """
    Orchestrates interactive demo mode

    Features:
    - Natural language trigger detection
    - Auto-play scripted conversation
    - Real artifact generation
    - Demo cards and visual indicators
    - User controls (pause, skip, stop)
    """

    def __init__(self):
        self.active_demos: Dict[str, DemoState] = {}
        self.scenarios = self._load_scenarios()
        logger.info(f"DemoOrchestrator initialized with {len(self.scenarios)} scenarios")

    def _load_scenarios(self) -> Dict[str, DemoScenario]:
        """Load demo scenarios"""
        scenarios = {}

        # Scenario 1: Language Concerns (most common)
        scenarios["language_concerns"] = DemoScenario(
            scenario_id="language_concerns",
            name="דאגות שפה",
            name_en="Language Development Concerns",
            description="הורה מודאג לגבי התפתחות שפה של ילד בן 3.5",
            duration_estimate="2-3 דקות",

            child_profile={
                "child_name": "דניאל",
                "age": 3.5,
                "gender": "male",
                "primary_concerns": ["שפה", "תקשורת"],
                "concern_details": "דניאל מדבר פחות מילדים אחרים בגילו. הוא משתמש במילים בודדות וקשה לו לבנות משפטים. בגן הוא שקט ולא משתתף בפעילויות קבוצתיות.",
                "strengths": "אוהב מאוד לשחק עם קוביות ולבנות מגדלים, ממוקד ויצירתי, משחק יפה עם ילד אחד",
                "developmental_history": "התפתחות תקינה עד גיל שנתיים, אח קטן נולד לפני שנה",
                "family_context": "משפחה תומכת, דוברי עברית בבית",
                "parent_goals": "לעזור לו להרגיש בטוח בתקשורת ולהתבטא טוב יותר"
            },

            messages=[
                # Opening - Chitta greets FIRST (exactly like real app!)
                DemoMessage(
                    role="assistant",
                    content="שלום! אני צ'יטה 💙\n\nנעים להכיר אותך! אני כאן כדי להכיר את הילד/ה שלך ולהבין איך אפשר לעזור. נשוחח קצת יחד, ואז נמשיך לשלבים הבאים.\n\nבואי נתחיל - מה שם הילד/ה שלך ובן/בת כמה?",
                    delay_ms=0  # First message appears immediately
                ),

                # Parent shares name and age
                DemoMessage(
                    role="user",
                    content="שמו דניאל, הוא בן 3 וחצי",
                    delay_ms=3000
                ),

                # Chitta starts with STRENGTHS (as per interview guide!)
                DemoMessage(
                    role="assistant",
                    content="נעים להכיר את דניאל! לפני שנדבר על אתגרים, בואי נתחיל מהדברים הטובים. במה דניאל אוהב לעסוק? מה הוא עושה טוב?",
                    delay_ms=2500
                ),

                # Parent shares strengths
                DemoMessage(
                    role="user",
                    content="הוא מאוד אוהב לשחק עם קוביות ולבנות מגדלים. הוא ממוקד ויצירתי. וגם משחק יפה עם ילד אחד.",
                    delay_ms=3500
                ),

                # Chitta acknowledges and asks about concerns
                DemoMessage(
                    role="assistant",
                    content="נשמע שדניאל יצירתי וממוקד - זה נפלא! עכשיו ספרי לי, מה הביא אותך אלינו? מה מדאיג אותך לגבי דניאל?",
                    delay_ms=2500,
                    card_hint="conversation_depth_card"  # Should show "השיחה מתפתחת"
                ),

                # Parent shares main concern
                DemoMessage(
                    role="user",
                    content="יש לי דאגות לגבי הדיבור שלו. הוא מדבר הרבה פחות מילדים אחרים בגיל שלו.",
                    delay_ms=4000
                ),

                # Chitta asks for specific example
                DemoMessage(
                    role="assistant",
                    content="אני שומעת. תני לי דוגמה ספציפית - מה קורה בדיוק? איך הוא מתקשר איתך?",
                    delay_ms=2500
                ),

                # Parent gives specific details
                DemoMessage(
                    role="user",
                    content="הוא משתמש במילים בודדות, קשה לו לבנות משפטים. למשל אומר 'מים' במקום 'אני רוצה מים'. ובגן הוא שקט, לא משתתף בפעילויות.",
                    delay_ms=4500,
                    card_hint="conversation_depth_card"  # Now "השיחה מתעמקת"
                ),

                # Chitta explores context
                DemoMessage(
                    role="assistant",
                    content="אני מבינה. ואיך זה משפיע על היום יום שלכם? איך אתם מתמודדים עם זה?",
                    delay_ms=2500
                ),

                # Parent shares family context
                DemoMessage(
                    role="user",
                    content="זה מתסכל לפעמים. יש לו אח קטן שנולד לפני שנה, ולפעמים קשה לי לדעת מה דניאל צריך.",
                    delay_ms=4000
                ),

                # Chitta asks about goals
                DemoMessage(
                    role="assistant",
                    content="זה מאתגר. ספרי לי - מה הייתם רוצים לראות מתקדם? מה חשוב לכם?",
                    delay_ms=2500
                ),

                # Parent shares goals - THIS COMPLETES RICH KNOWLEDGE!
                DemoMessage(
                    role="user",
                    content="אני רוצה לעזור לו להרגיש בטוח בתקשורת. שיוכל להתבטא טוב יותר ולהצליח בגן.",
                    delay_ms=3500,
                    trigger_artifact="baseline_video_guidelines"  # Wu Wei triggers!
                ),

                # Chitta acknowledges richness and offers guidelines
                DemoMessage(
                    role="assistant",
                    content="תודה שספרת לי על דניאל. אני מרגישה שיש לי תמונה עשירה שלו - החוזקות שלו, האתגרים, והמטרות שלכם. אני יכולה להכין עבורך הנחיות צילום מותאמות אישית שיעזרו לי להבין את דניאל טוב יותר. רוצה לראות אותן?",
                    delay_ms=3000,
                    card_hint="guidelines_offer_card"  # Card should appear!
                ),

                # Parent accepts
                DemoMessage(
                    role="user",
                    content="כן, בטח!",
                    delay_ms=2000
                ),

                # Chitta confirms guidelines are ready
                DemoMessage(
                    role="assistant",
                    content="מעולה! ההנחיות מוכנות 📋 תראי אותן בכרטיס למטה. הן מותאמות במיוחד לדניאל - 3 מצבים שיעזרו לי לראות את התקשורת שלו. קחי את הזמן שצריך, אין לחץ 💙",
                    delay_ms=2500,
                    card_hint="guidelines_ready_card"
                ),
            ],

            artifact_trigger_at_step=11  # After parent shares goals (step 11 now)
        )

        return scenarios

    def detect_demo_intent(self, message: str) -> Optional[str]:
        """
        Detect if user wants to start demo

        Returns scenario_id if demo requested, None otherwise
        """
        message_lower = message.lower().strip()

        demo_triggers = [
            "show me a demo",
            "start demo",
            "demo mode",
            "run demo",
            "הראה לי דמו",
            "הדגמה",
            "מצב הדגמה",
            "דוגמה",
            "הראה דוגמה"
        ]

        for trigger in demo_triggers:
            if trigger in message_lower:
                # Default to language_concerns scenario
                return "language_concerns"

        return None

    async def start_demo(
        self,
        scenario_id: str = "language_concerns"
    ) -> Dict[str, Any]:
        """
        Start a demo session

        Returns:
            Initial demo state with first message
        """
        scenario = self.scenarios.get(scenario_id)
        if not scenario:
            raise ValueError(f"Unknown scenario: {scenario_id}")

        # Create demo family ID
        demo_family_id = f"demo_{scenario_id}_{int(datetime.now().timestamp())}"

        # Initialize demo session
        interview_service = get_interview_service()
        session = interview_service.get_or_create_session(demo_family_id)

        # Set up child profile
        session.extracted_data = ExtractedData(**scenario.child_profile)

        # Create demo state
        demo_state = DemoState(
            demo_family_id=demo_family_id,
            scenario_id=scenario_id,
            current_step=0,
            started_at=datetime.now(),
            is_active=True
        )

        self.active_demos[demo_family_id] = demo_state

        logger.info(f"🎬 Demo started: {scenario_id} -> {demo_family_id}")

        # Return initial response
        first_message = scenario.messages[0]

        return {
            "demo_family_id": demo_family_id,
            "scenario": {
                "id": scenario.scenario_id,
                "name": scenario.name,
                "name_en": scenario.name_en,
                "description": scenario.description,
                "duration": scenario.duration_estimate,
                "total_steps": len(scenario.messages)
            },
            "first_message": {
                "role": first_message.role,
                "content": first_message.content,
                "delay_ms": first_message.delay_ms
            },
            "demo_card": self._build_demo_card(demo_state, scenario)
        }

    async def get_next_step(
        self,
        demo_family_id: str
    ) -> Dict[str, Any]:
        """
        Get next message in demo flow

        Returns:
            Next message, artifacts to generate, cards to show
        """
        demo_state = self.active_demos.get(demo_family_id)
        if not demo_state or not demo_state.is_active:
            raise ValueError(f"No active demo: {demo_family_id}")

        scenario = self.scenarios[demo_state.scenario_id]

        # Move to next step
        demo_state.current_step += 1

        if demo_state.current_step >= len(scenario.messages):
            # Demo complete!
            return await self._complete_demo(demo_family_id)

        current_message = scenario.messages[demo_state.current_step]

        # Update session with message
        interview_service = get_interview_service()
        session = interview_service.get_or_create_session(demo_family_id)

        session.conversation_history.append({
            "role": current_message.role,
            "content": current_message.content
        })

        # Check if we should generate artifact
        artifact_generated = None
        if current_message.trigger_artifact:
            logger.info(f"🎬 Demo triggering artifact: {current_message.trigger_artifact}")
            artifact_service = ArtifactGenerationService()

            session_data = {
                "family_id": demo_family_id,
                "extracted_data": session.extracted_data.model_dump(),
                "child_name": scenario.child_profile["child_name"],
                "age": scenario.child_profile["age"],
                "primary_concerns": scenario.child_profile["primary_concerns"],
                "concern_details": scenario.child_profile["concern_details"],
                "strengths": scenario.child_profile["strengths"]
            }

            artifact = await artifact_service.generate_video_guidelines(session_data)
            session.add_artifact(artifact)

            artifact_generated = {
                "artifact_id": artifact.artifact_id,
                "status": artifact.status,
                "content_length": len(artifact.content) if artifact.content else 0
            }

        # Build response
        return {
            "step": demo_state.current_step,
            "total_steps": len(scenario.messages),
            "message": {
                "role": current_message.role,
                "content": current_message.content,
                "delay_ms": current_message.delay_ms
            },
            "artifact_generated": artifact_generated,
            "card_hint": current_message.card_hint,
            "demo_card": self._build_demo_card(demo_state, scenario),
            "is_complete": False
        }

    async def stop_demo(
        self,
        demo_family_id: str
    ) -> Dict[str, Any]:
        """Stop demo and return to normal mode"""
        demo_state = self.active_demos.get(demo_family_id)
        if demo_state:
            demo_state.is_active = False
            del self.active_demos[demo_family_id]

        logger.info(f"🎬 Demo stopped: {demo_family_id}")

        return {
            "success": True,
            "message": "Demo stopped. Ready to start your real conversation! 💙"
        }

    async def _complete_demo(
        self,
        demo_family_id: str
    ) -> Dict[str, Any]:
        """Handle demo completion"""
        demo_state = self.active_demos[demo_family_id]
        scenario = self.scenarios[demo_state.scenario_id]

        logger.info(f"🎬 Demo completed: {demo_family_id}")

        return {
            "step": len(scenario.messages),
            "total_steps": len(scenario.messages),
            "message": {
                "role": "system",
                "content": "ההדגמה הושלמה! 🎉 ראית את כל התהליך - מראיון ועד להנחיות מותאמות. רוצה להתחיל בשיחה אמיתית?",
                "delay_ms": 0
            },
            "is_complete": True,
            "demo_card": {
                "title": "🎬 ההדגמה הסתיימה",
                "body": "כל הכבוד! ראית את התהליך המלא",
                "actions": ["start_real_conversation", "replay_demo", "exit_demo"]
            }
        }

    def _build_demo_card(
        self,
        demo_state: DemoState,
        scenario: DemoScenario
    ) -> Dict[str, Any]:
        """Build demo mode card"""
        progress_pct = int((demo_state.current_step / len(scenario.messages)) * 100)

        return {
            "card_type": "demo_mode",
            "priority": 1000,  # Always on top
            "title": "🎬 מצב הדגמה",
            "title_en": "DEMO MODE",
            "body": f"זו סימולציה - לא מידע אמיתי | {scenario.name}",
            "step_indicator": f"שלב {demo_state.current_step} / {len(scenario.messages)}",
            "progress": progress_pct,
            "flashing": True,  # Visual indicator
            "actions": ["stop_demo", "pause_demo", "skip_step"]
        }


# Global singleton
_demo_orchestrator: Optional[DemoOrchestratorService] = None


def get_demo_orchestrator() -> DemoOrchestratorService:
    """Get global demo orchestrator instance"""
    global _demo_orchestrator
    if _demo_orchestrator is None:
        _demo_orchestrator = DemoOrchestratorService()
    return _demo_orchestrator
