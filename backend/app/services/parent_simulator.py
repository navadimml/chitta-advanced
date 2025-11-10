"""
Parent Simulator - Simulates realistic parent personas
Uses real backend processing to test entire system
"""
from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime


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
                "Gives very short answers: 'כן', 'לא יודעת', 'אולי'",
                "Uses vague terms: 'משהו כזה', 'סוג של', 'לא בדיוק'",
                "Struggles to articulate specific examples",
                "Often says 'I don't remember exactly'"
            ],
            "testing_purpose": "Tests Chitta's ability to extract information through probing questions",
            "typical_responses": [
                "אממ... לא יודעת בדיוק",
                "משהו כזה",
                "קשה לי להסביר"
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
                "Answers briefly then immediately asks questions back",
                "Questions everything: 'למה?', 'מה אתם תעשו עם זה?', 'מה הצעד הבא?'",
                "Seeks constant reassurance: 'זה נורמלי?', 'זה רציני?'",
                "Worries about implications: 'מה זה אומר על...?'"
            ],
            "testing_purpose": "Tests Chitta's ability to handle anxious parents and maintain interview flow",
            "typical_responses": [
                "רגע, למה אתם שואלים את זה? מה זה אומר?",
                "אז מה הולך לקרות עכשיו?",
                "זה רציני? אני צריכה לדאוג?"
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
                "Starts answering then goes on tangent about her childhood or other kids",
                "Shares family drama: 'הסבתא שלו תמיד אומרת...'",
                "Compares to other children: 'הבן של השכנה...'",
                "Gets distracted: 'רגע, שכחתי מה שאלת'"
            ],
            "testing_purpose": "Tests Chitta's ability to redirect conversation and stay focused",
            "typical_responses": [
                "אה כן, אז בעצם גם אני בגילו לא אהבתי ירקות, והסבתא שלי תמיד...",
                "רגע, זה מזכיר לי שהבן של השכנה...",
                "נו אבל המורה בגן אמרה משהו אחר..."
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
                "Gives one answer then contradicts: 'הוא מדבר טוב... אה לא, בעצם...'",
                "Changes details: 'זה קרה בגיל 2... או 3? לא זוכר'",
                "Disagrees with spouse: 'אבל אשתי אומרת משהו אחר'",
                "Uncertain: 'אני לא בטוח', 'אולי כן אולי לא'"
            ],
            "testing_purpose": "Tests Chitta's ability to clarify contradictions and establish facts",
            "typical_responses": [
                "הוא כן מדבר... אה רגע, לא, בעצם הוא לא ממש",
                "אשתי אומרת שזה קרה אחרת, אני לא בטוח",
                "רגע, אמרתי 3? התכוונתי ל-4"
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
                "Downplays issues: 'זה לא כזה רציני', 'כולם עושים את זה'",
                "Defensive: 'למה אתם שואלים את זה?', 'זה נורמלי לגיל שלו'",
                "Blames others: 'זו הגננת שמגזימה'",
                "Compares: 'כל הילדים בגילו כאלה'"
            ],
            "testing_purpose": "Tests Chitta's ability to handle resistant parents with empathy",
            "typical_responses": [
                "אבל זה נורמלי לגיל, לא?",
                "הגננת מגזימה, הוא בסדר גמור",
                "למה כולם עושים מזה עניין?"
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
                "Jumps between topics: 'יש דיבור, אה וגם שינה, ועוד...'",
                "Starts answering but gets distracted: 'אז בעצם... רגע, שכחתי'",
                "Mentions everything at once: 'יש כל כך הרבה בעיות'",
                "Partial answers: 'זה מסובך... אני לא יודעת איך להסביר'"
            ],
            "testing_purpose": "Tests Chitta's ability to help parent focus and prioritize",
            "typical_responses": [
                "יש כל כך הרבה... דיבור, שינה, התנהגות...",
                "רגע, איך אני מסבירה את זה? יש גם...",
                "אני כל כך עייפה, קשה לי לחשוב"
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
        llm_provider
    ) -> str:
        """
        Generate realistic parent response using LLM.
        The LLM acts as the parent persona.
        """
        simulation = self.active_simulations.get(family_id)
        if not simulation:
            raise ValueError(f"No active simulation for {family_id}")

        persona = simulation["persona"]
        simulation["message_count"] += 1

        # Build context for LLM with emphasis on behavior patterns
        answer_patterns = persona.context_info.get("answer_patterns", [])
        patterns_text = "\n".join([f"- {p}" for p in answer_patterns]) if answer_patterns else ""

        system_prompt = f"""
You are {persona.parent_name}, a parent participating in an interview about your child {persona.child_name}.

YOUR CHILD:
- Name: {persona.child_name}
- Age: {persona.child_age} years old
- Gender: {persona.child_gender}

YOUR MAIN CONCERN:
{persona.main_concern}

YOUR CHILD'S STRENGTHS:
{', '.join(persona.strengths)}

BACKGROUND:
{self._format_background(persona.background)}

RESPONSE STYLE: {persona.response_style}

HOW YOU ANSWER QUESTIONS (CRITICAL - FOLLOW THESE PATTERNS):
{patterns_text}

CONTEXT INFORMATION:
{self._format_context(persona.context_info)}

IMPORTANT INSTRUCTIONS:
- You MUST follow the answer patterns above - this is how this specific parent communicates
- Answer as this parent would - with their exact knowledge, emotions, and style
- Be natural and realistic - embody this parent's personality completely
- Share relevant details from the background when appropriate
- Show emotion appropriate to the concern level and parent's state
- Respond in Hebrew ONLY
- Keep responses conversational, usually 1-3 sentences
- Stay in character - if parent is vague, BE vague; if defensive, BE defensive

Chitta asked: "{chitta_question}"

Respond as {persona.parent_name} following the answer patterns above:
"""

        # Use LLM to generate response
        from app.services.llm.base import Message
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=chitta_question)
        ]

        response = await llm_provider.chat(messages=messages, temperature=0.8)

        return response.content.strip()

    def _format_background(self, background: dict) -> str:
        """Format background dict into readable text"""
        lines = []
        for key, value in background.items():
            if isinstance(value, dict):
                lines.append(f"{key}:")
                for k, v in value.items():
                    lines.append(f"  - {k}: {v}")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)

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
