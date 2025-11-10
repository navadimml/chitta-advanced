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

        # Build context for LLM
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

CONTEXT INFORMATION:
{self._format_context(persona.context_info)}

IMPORTANT:
- Answer as this parent would - with their knowledge, emotions, and style
- Be natural and realistic
- Share relevant details from the background when appropriate
- Show emotion appropriate to the concern level
- Respond in Hebrew
- Keep responses conversational, 2-4 sentences typically

Chitta asked: "{chitta_question}"

Respond as {persona.parent_name}:
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
