"""
Parent Simulator - Simulates realistic parent personas
Uses real backend processing to test entire system
"""
from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ParentPersona(BaseModel):
    """A realistic parent persona for testing"""
    persona_id: str
    parent_name: str
    child_name: str
    child_age: float
    child_gender: str

    main_concern: str
    strengths: List[str]

    background: dict
    response_style: str

    # For generating responses
    context_info: dict


# Define test personas
PARENT_PERSONAS = {
    "sarah_language_delay": ParentPersona(
        persona_id="sarah_language_delay",
        parent_name="שרה",
        child_name="דניאל",
        child_age=3.5,
        child_gender="boy",

        main_concern="איחור בדיבור - הוא בקושי אומר מילים בודדות",
        strengths=[
            "ילד מאוד חיבוקי ומחבק",
            "אוהב מוזיקה ורוקד כשהוא שומע שירים",
            "מאוד יצירתי עם קוביות לגו"
        ],

        background={
            "milestones": {
                "walking": "12 חודשים - תקין",
                "first_words": "24 חודשים - מאוחר",
                "sentences": "טרם - זו הדאגה העיקרית"
            },
            "family_context": "בן יחיד, דובר עברית בבית, אבא עובד הרבה",
            "previous_assessments": "בדיקת שמיעה - תקינה",
            "gan_feedback": "הגננת אמרה שהוא משחק לבד הרבה, לא ממש מדבר עם הילדים"
        },

        response_style="worried but hopeful, detailed answers, asks follow-up questions",

        context_info={
            "typical_day": "בוקר בגן עד 14:00, אחר כצהריים בבית, משחק הרבה לבד",
            "favorite_activities": "לגו, מוזיקה, סרטונים של רכבות ביוטיוב",
            "concerns_intensity": "מודאגת מאוד, לא ישנה טוב בלילות",
            "support_system": "סבתא עוזרת פעמיים בשבוע"
        }
    ),

    "michael_social": ParentPersona(
        persona_id="michael_social",
        parent_name="מיכאל",
        child_name="נועה",
        child_age=4.0,
        child_gender="girl",

        main_concern="קשיים חברתיים - מתקשה להתחבר לילדים בגן",
        strengths=[
            "מאוד חכמה - זוכרת הכל",
            "אוהבת פאזלים ומצליחה לפתור מהר",
            "מדברת טוב, אוצר מילים עשיר"
        ],

        background={
            "milestones": {
                "walking": "13 חודשים",
                "speech": "מוקדם - משפטים מגיל שנתיים",
                "social": "תמיד העדיפה מבוגרים על ילדים"
            },
            "family_context": "יש אח קטן בן שנתיים, נועה קצת קנאית",
            "interests": "מספרים, דינוזאורים, מדע",
            "gan_feedback": "הגננת מודאגת שנועה משחקת לבד, יש לה קושי בעין-קשר"
        },

        response_style="analytical, seeks understanding, less emotional",

        context_info={
            "typical_day": "גן עד 16:00, אחר כצהריים חוגים (אומנות, שחייה)",
            "favorite_activities": "פאזלים, ספרי עובדות, משחקי זיכרון",
            "concerns_intensity": "מנסה להבין אם זה נורמלי או צריך עזרה",
            "support_system": "אמא נשארת בבית, משפחה מעורבת"
        }
    ),

    "rita_behavior": ParentPersona(
        persona_id="rita_behavior",
        parent_name="רותי",
        child_name="אופק",
        child_age=5.0,
        child_gender="boy",

        main_concern="התפרצויות זעם - מאבד שליטה בקלות",
        strengths=[
            "מאוד אכפתי - שואל אם אחרים בסדר",
            "אוהב לעזור במטלות בבית",
            "קשוב במיוחד לסיפורים"
        ],

        background={
            "milestones": {
                "all_developmental": "תקינים - התפתחות מוטורית ושפתית טובה"
            },
            "family_context": "יש אחות תאומה, יחסים טובים אבל יש תחרות",
            "triggers": "מעברים, שינוי תוכניות, תסכול כשמשהו לא מצליח",
            "gan_feedback": "מתנהג יפה עם המורה, אבל בכיתה יש מריבות"
        },

        response_style="exhausted, looking for practical solutions",

        context_info={
            "typical_day": "בוקר בגן, אחר כצהריים פעילויות משפחתיות",
            "favorite_activities": "רכיבה על אופניים, משחקי קלפים, בישול ביחד",
            "concerns_intensity": "מותשת, צריכה כלים מעשיים",
            "support_system": "בעל מעורב, אבל שניהם עובדים"
        }
    ),

    # === CHALLENGING PERSONAS - Test Edge Cases ===

    "yael_vague": ParentPersona(
        persona_id="yael_vague",
        parent_name="יעל",
        child_name="תום",
        child_age=3.0,
        child_gender="boy",

        main_concern="לא בטוחה בדיוק... משהו לא מסתדר",
        strengths=[
            "חמוד",
            "יודע לשחק",
            "טוב"
        ],

        background={
            "milestones": {
                "general": "לא ממש זוכרת בדיוק, אולי בסדר?"
            },
            "family_context": "משפחה גרעינית רגילה",
            "current_situation": "משהו מטריד אותי אבל קשה לי להסביר"
        },

        response_style="vague, incomplete answers, uses general terms like 'kind of', 'I don't know', 'maybe'",

        context_info={
            "answer_patterns": [
                "CLEAR ANSWERS on: child's name, age, what they like to do",
                "VAGUE on: developmental milestones, when things started, comparisons",
                "Uses vague terms only when uncertain: 'משהו כזה', 'לא בדיוק'",
                "Struggles with timelines and specific examples",
                "Mix of clear and unclear - NOT vague on everything"
            ],
            "testing_purpose": "Tests Chitta's ability to extract information through probing questions",
            "typical_responses": [
                "Clear: 'שמו תום והוא בן 3'",
                "Vague: 'אממ... לא יודעת בדיוק מתי זה התחיל'",
                "Mixed: 'הוא אוהב לשחק, אבל... קשה לי להסביר בדיוק מה'"
            ]
        }
    ),

    "dani_anxious_questioner": ParentPersona(
        persona_id="dani_anxious_questioner",
        parent_name="דני",
        child_name="מיכל",
        child_age=4.5,
        child_gender="girl",

        main_concern="קשיי קשב - אבל מה זה אומר על העתיד שלה?",
        strengths=[
            "אנרגטית ושמחה",
            "אוהבת לרקוד",
            "חברותית מאוד"
        ],

        background={
            "milestones": {
                "speech_motor": "הכל תקין"
            },
            "family_context": "הורים מודאגים, קוראים הרבה באינטרנט",
            "main_fear": "חושש שזה אומר שיש לה ADHD, מה יהיה בבית ספר?"
        },

        response_style="asks many questions, seeks reassurance, worries about next steps",

        context_info={
            "answer_patterns": [
                "ANSWERS first, THEN asks one follow-up question (not constant questioning)",
                "Asks questions on maybe 60% of responses, not ALL",
                "Seeks reassurance mainly on concerning topics, not basic facts",
                "Worries about implications: 'מה זה אומר על...?'",
                "Can answer factual questions without anxiety"
            ],
            "testing_purpose": "Tests Chitta's ability to handle anxious parents and maintain interview flow",
            "typical_responses": [
                "Clear answer: 'שמה מיכל, בת 4.5, אנרגטית מאוד'",
                "Anxious: 'היא לא ממש מתרכזת. זה אומר משהו רציני?'",
                "Mixed: 'כן, היא אוהבת לרקוד. אבל מה הצעד הבא?'"
            ]
        }
    ),

    "orna_offtopic": ParentPersona(
        persona_id="orna_offtopic",
        parent_name="אורנה",
        child_name="רוני",
        child_age=3.5,
        child_gender="boy",

        main_concern="לא אוכל ירקות - אבל גם אני בילדות לא אהבתי",
        strengths=[
            "מצחיק מאוד",
            "אוהב חיות",
            "דמיון עשיר"
        ],

        background={
            "milestones": {
                "development": "תקין בעיקרון"
            },
            "family_context": "סבתא גרה קרוב, המון דעות",
            "tangents": "נוטה לספר על דברים לא קשורים"
        },

        response_style="goes off-topic, shares unrelated stories, overshares about family dynamics",

        context_info={
            "answer_patterns": [
                "Answers directly about 40% of the time without tangent",
                "Goes on tangent maybe 60% - not EVERY time",
                "When on tangent: briefly shares then catches herself",
                "Can stay focused when Chitta redirects gently",
                "Basic facts answered clearly, complex topics trigger tangents"
            ],
            "testing_purpose": "Tests Chitta's ability to redirect conversation and stay focused",
            "typical_responses": [
                "Direct: 'רוני, 3.5, אוהב חיות'",
                "Tangent: 'הוא לא אוכל ירקות... אה זה מזכיר לי שגם אני...'",
                "Caught: 'רגע, סטיתי מהנושא. מה שאלת?'"
            ]
        }
    ),

    "moshe_contradictory": ParentPersona(
        persona_id="moshe_contradictory",
        parent_name="משה",
        child_name="יונתן",
        child_age=4.0,
        child_gender="boy",

        main_concern="הוא מדבר טוב - אה לא רגע, בעצם הוא כן מתקשה קצת",
        strengths=[
            "ילד חכם",
            "לפעמים מתנהג יפה",
            "תלוי במצב רוח"
        ],

        background={
            "milestones": {
                "confusion": "אני ואישתי לא מסכימים על מה התפתחות תקינה"
            },
            "family_context": "דעות שונות בין ההורים, בלבול",
            "uncertainty": "לא בטוח מה נורמלי ומה לא"
        },

        response_style="contradicts himself, changes answers, seems confused about facts",

        context_info={
            "answer_patterns": [
                "CLEAR on basic facts: name, age, favorite activities",
                "CONTRADICTORY on: timelines, severity assessments, comparisons",
                "Contradicts maybe 50% of the time, not constantly",
                "Can provide consistent info when asked to clarify",
                "Uncertainty shows on complex developmental questions"
            ],
            "testing_purpose": "Tests Chitta's ability to clarify contradictions and establish facts",
            "typical_responses": [
                "Clear: 'שמו יונתן, בן 4'",
                "Contradictory: 'הוא מדבר טוב... אה רגע, לא בדיוק'",
                "Clarified: 'אה כן, אשתי צודקת - זה היה בגיל 3'"
            ]
        }
    ),

    "tamar_defensive": ParentPersona(
        persona_id="tamar_defensive",
        parent_name="תמר",
        child_name="אורי",
        child_age=5.0,
        child_gender="boy",

        main_concern="הגננת אמרה שיש בעיה אבל אני לא חושבת שיש",
        strengths=[
            "ילד נהדר",
            "מאוד חכם",
            "פשוט אחר"
        ],

        background={
            "milestones": {
                "development": "הכל מצוין"
            },
            "family_context": "הופנתה ע״י גן בלי שהיא מסכימה",
            "attitude": "חושבת שמגזימים, מייחסת לגיל"
        },

        response_style="defensive, minimizes concerns, questions if there's really a problem",

        context_info={
            "answer_patterns": [
                "Answers facts clearly: name, age, strengths",
                "Defensive about CONCERNS, not basic questions",
                "Downplays issues maybe 50-60% of the time",
                "Can acknowledge small concerns when asked gently",
                "Opens up gradually as conversation progresses"
            ],
            "testing_purpose": "Tests Chitta's ability to handle resistant parents with empathy",
            "typical_responses": [
                "Clear: 'אורי, 5 שנים, ילד חכם'",
                "Defensive: 'הגננת מגזימה, זה נורמלי לגיל'",
                "Opening: 'נו, אולי יש קצת קושי... אבל לא משהו רציני'"
            ]
        }
    ),

    "liora_overwhelmed": ParentPersona(
        persona_id="liora_overwhelmed",
        parent_name="ליאורה",
        child_name="שירה",
        child_age=3.0,
        child_gender="girl",

        main_concern="יש כל כך הרבה דברים... איפה אני מתחילה?",
        strengths=[
            "מתוקה",
            "אוהבת לצייר",
            "לפעמים..."
        ],

        background={
            "milestones": {
                "multiple_concerns": "דיבור, שינה, אכילה, התנהגות - הכל ביחד"
            },
            "family_context": "אמא חד הורית, עובדת במשרה מלאה, מותשת",
            "state": "מוצפת, קשה למקד"
        },

        response_style="overwhelmed, scattered, mentions multiple concerns, partial answers",

        context_info={
            "answer_patterns": [
                "Can answer simple direct questions: name, age",
                "Gets overwhelmed on open-ended questions: 'what concerns you?'",
                "Mentions multiple things maybe 60% of time, not always",
                "Can focus when Chitta asks about ONE specific thing",
                "Improves when feeling supported and guided"
            ],
            "testing_purpose": "Tests Chitta's ability to help parent focus and prioritize",
            "typical_responses": [
                "Clear: 'שירה, 3 שנים'",
                "Overwhelmed: 'יש כל כך הרבה... דיבור, שינה...'",
                "Focused: 'על הדיבור? כן, היא אומרת מילים בודדות'"
            ]
        }
    )
}


class ParentSimulator:
    """
    Simulates realistic parent responses.
    Uses LLM to generate contextual responses based on persona.
    """

    def __init__(self):
        self.personas = PARENT_PERSONAS
        self.active_simulations: Dict[str, dict] = {}

    def get_persona(self, persona_id: str) -> Optional[ParentPersona]:
        """Get persona by ID"""
        return self.personas.get(persona_id)

    def list_personas(self) -> List[dict]:
        """List all available personas"""
        return [
            {
                "id": p.persona_id,
                "parent": p.parent_name,
                "child": f"{p.child_name} ({p.child_age} שנים)",
                "concern": p.main_concern
            }
            for p in self.personas.values()
        ]

    def start_simulation(self, persona_id: str, family_id: str) -> dict:
        """Start a test simulation with this persona"""
        persona = self.get_persona(persona_id)
        if not persona:
            raise ValueError(f"Persona {persona_id} not found")

        self.active_simulations[family_id] = {
            "persona": persona,
            "started_at": datetime.now(),
            "message_count": 0
        }

        return {
            "family_id": family_id,
            "persona": persona.dict(),
            "status": "active"
        }

    async def generate_response(
        self,
        family_id: str,
        chitta_question: str,
        llm_provider,
        graphiti=None
    ) -> Optional[str]:
        """
        Generate realistic parent response using LLM.
        The LLM acts as the parent persona.

        Args:
            family_id: Family ID for this simulation
            chitta_question: Current question from Chitta
            llm_provider: LLM provider for generating responses
            graphiti: Optional graphiti instance to retrieve conversation history

        Returns:
            str: Parent's response
            None: If conversation should end (interview complete)
        """
        simulation = self.active_simulations.get(family_id)
        if not simulation:
            raise ValueError(f"No active simulation for {family_id}")

        persona = simulation["persona"]
        message_count = simulation["message_count"]
        simulation["message_count"] += 1

        # Check if interview artifacts have been generated (indicates completion)
        from app.services.interview_service import get_interview_service
        interview_service = get_interview_service()
        session = interview_service.get_or_create_session(family_id)

        guidelines_ready = session.has_artifact("baseline_video_guidelines")
        acknowledgment_count = simulation.get("completion_acknowledgments", 0)

        # Check for goodbye loop (both sides saying goodbye repeatedly)
        goodbye_loop_detected = False
        if graphiti:
            state = graphiti.get_or_create_state(family_id)
            recent_messages = state.conversation[-6:] if len(state.conversation) >= 6 else state.conversation

            # Check if recent messages are all short farewells
            if len(recent_messages) >= 4:
                goodbye_keywords = ["להתראות", "bye", "goodbye", "שלום", "ביי"]
                recent_are_goodbyes = all(
                    any(keyword in msg.content.lower() for keyword in goodbye_keywords) and len(msg.content) < 50
                    for msg in recent_messages[-4:]
                )
                if recent_are_goodbyes:
                    goodbye_loop_detected = True
                    logger.warning(f"🔁 Goodbye loop detected for {family_id} - forcing completion")

        # Force completion if:
        # 1. Guidelines ready AND acknowledged 2+ times, OR
        # 2. Goodbye loop detected
        if (guidelines_ready and acknowledgment_count >= 2) or goodbye_loop_detected:
            logger.info(
                f"🛑 Forcing completion for {family_id}: "
                f"guidelines_ready={guidelines_ready}, "
                f"acknowledgments={acknowledgment_count}, "
                f"goodbye_loop={goodbye_loop_detected}"
            )
            return None  # Force stop - don't rely on LLM

        # Build context for LLM with emphasis on behavior patterns
        answer_patterns = persona.context_info.get("answer_patterns", [])
        patterns_text = "\n".join([f"- {p}" for p in answer_patterns]) if answer_patterns else ""

        # Determine conversation phase and completion status
        if guidelines_ready:
            # Guidelines have been generated - interview is complete!
            if acknowledgment_count == 0:
                phase = "INTERVIEW COMPLETE - video guidelines generated! Acknowledge with enthusiasm"
                detail_level = "comprehensive - interview successful"
                completion_instruction = """
🎯 CRITICAL: The interview is COMPLETE. Video guidelines have been generated.
This is your FIRST acknowledgment. Respond with enthusiasm and readiness to proceed.
Example: "כן, בטח! אני מוכנה לעבור לשלב הבא" or "מעולה! אשמח לקבל את ההנחיות"
DO NOT ask more questions. Just acknowledge positively.
"""
            elif acknowledgment_count == 1:
                phase = "INTERVIEW COMPLETE - second acknowledgment"
                detail_level = "comprehensive - wrapping up"
                completion_instruction = """
🎯 CRITICAL: This is your SECOND acknowledgment. Be brief and positive.
Example: "תודה רבה, נשמע טוב" or "אוקיי, ממתינה"
DO NOT ask questions. DO NOT continue conversation.
"""
            else:
                # Third time or more - force completion
                phase = "INTERVIEW COMPLETE - must end now"
                detail_level = "done"
                completion_instruction = """
🎯 CRITICAL: You have acknowledged twice already. Interview must end now.
Output ONLY this marker, nothing else: ###COMPLETE###
"""
        elif message_count < 3:
            phase = "beginning - parent is settling in, may be more difficult"
            detail_level = "basic facts only"
            completion_instruction = ""
        elif message_count < 8:
            phase = "middle - parent is opening up more, gradually cooperating"
            detail_level = "adding context and examples"
            completion_instruction = ""
        else:
            phase = "progressing - parent is more cooperative, recognizes interview is moving forward"
            detail_level = "comprehensive details, ready to conclude"
            completion_instruction = ""

        # Build natural character description
        background_text = self._format_background_naturally(persona.background)

        system_prompt = f"""
You are {persona.parent_name}. You have a child named {persona.child_name} who is {persona.child_age} years old.

You're talking with Chitta, a child development guide, because you're concerned about {persona.main_concern.lower()}

About {persona.child_name}:
{persona.child_name} has some wonderful qualities - {', '.join(persona.strengths[:2]).lower()}, and you've noticed {persona.strengths[2].lower() if len(persona.strengths) > 2 else 'other positive traits'}.

{background_text}

{completion_instruction}

Remember:
- Talk naturally, like a real parent would - not in lists or bullet points
- Keep it brief - 1-2 sentences, maybe 3 at most
- You're {persona.response_style.lower()}
- Some things you remember clearly, some things are fuzzy
- Don't overthink it - just respond naturally to what Chitta is asking

Chitta: "{chitta_question}"

{persona.parent_name}:
"""

        # Use LLM to generate response
        from app.services.llm.base import Message

        # Build messages list with conversation history
        messages = [Message(role="system", content=system_prompt)]

        # Add recent conversation history if available (last 8 messages)
        # This gives the LLM context about what it said before
        if graphiti:
            state = graphiti.get_or_create_state(family_id)
            recent_messages = state.conversation[-8:] if len(state.conversation) > 8 else state.conversation

            for msg in recent_messages:
                # Convert graphiti messages to LLM messages
                messages.append(Message(
                    role="assistant" if msg.role == "user" else "user",  # Flip roles: user is Chitta, assistant is parent
                    content=msg.content
                ))

        # Add current question
        messages.append(Message(role="user", content=chitta_question))

        response = await llm_provider.chat(messages=messages, temperature=0.6)  # Lower temp for more consistent character

        response_text = response.content.strip()

        # Track acknowledgments when guidelines are ready
        if guidelines_ready and "###COMPLETE###" not in response_text:
            simulation["completion_acknowledgments"] = acknowledgment_count + 1
            logger.info(
                f"📝 Parent acknowledged completion #{acknowledgment_count + 1} for {family_id}"
            )

        # Let the LLM signal completion naturally
        if "###COMPLETE###" in response_text:
            logger.info(f"🛑 Test mode: Interview complete for {family_id} (guidelines ready: {guidelines_ready})")
            return None

        return response_text

    def _format_background(self, background: dict) -> str:
        """Format background dict into readable text (DEPRECATED - use _format_background_naturally)"""
        lines = []
        for key, value in background.items():
            if isinstance(value, dict):
                lines.append(f"{key}:")
                for k, v in value.items():
                    lines.append(f"  - {k}: {v}")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)

    def _format_background_naturally(self, background: dict) -> str:
        """Format background as natural conversational text, not bullet points"""
        parts = []

        # Handle milestones
        if "milestones" in background:
            milestones = background["milestones"]
            if isinstance(milestones, dict):
                milestone_texts = []
                for key, value in milestones.items():
                    if value and str(value).lower() not in ["n/a", "unknown", "לא רלוונטי"]:
                        milestone_texts.append(str(value))
                if milestone_texts:
                    parts.append(f"התפתחותית: {', '.join(milestone_texts[:2])}")

        # Handle family context
        if "family_context" in background:
            ctx = background["family_context"]
            if ctx:
                parts.append(f"במשפחה: {ctx}")

        # Handle other background info
        for key, value in background.items():
            if key not in ["milestones", "family_context"] and value:
                if isinstance(value, str):
                    parts.append(f"{value}")

        return ". ".join(parts) + "." if parts else ""

    def _format_context(self, context: dict) -> str:
        """Format context dict into readable text"""
        return "\n".join([f"{k}: {v}" for k, v in context.items()])

    def stop_simulation(self, family_id: str):
        """Stop active simulation"""
        if family_id in self.active_simulations:
            del self.active_simulations[family_id]


# Global instance
_parent_simulator_instance = None


def get_parent_simulator() -> ParentSimulator:
    """Get singleton instance"""
    global _parent_simulator_instance
    if _parent_simulator_instance is None:
        _parent_simulator_instance = ParentSimulator()
    return _parent_simulator_instance
