"""
Simulated LLM Provider

For development without API keys - returns pre-programmed responses
מחזיר תשובות מוכנות מראש - לפיתוח ללא API
"""

import logging
from typing import List, Dict, Any, Optional

from .base import BaseLLMProvider, Message, LLMResponse, FunctionCall

logger = logging.getLogger(__name__)


class SimulatedLLMProvider(BaseLLMProvider):
    """
    Simulated LLM for development without API costs

    Returns pre-programmed Hebrew responses based on simple pattern matching.
    Useful for:
    - Local development without API keys
    - Testing frontend without backend costs
    - Demo purposes
    """

    def __init__(self):
        logger.info("✅ Simulated LLM provider initialized (no API calls)")

    async def chat(
        self,
        messages: List[Message],
        functions: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> LLMResponse:
        """
        Return simulated response with improved conversation flow

        Simulates:
        - Natural Hebrew conversation
        - Progressive interview questions
        - Interview completion detection
        """
        # Extract last message
        last_message = messages[-1].content.lower() if messages else ""

        # Count user messages for progress tracking
        user_messages = [m for m in messages if m.role == "user"]
        message_count = len(user_messages)

        # Check if interview should complete
        affirmative_words = ["כן", "בטח", "מוכנה", "מוכן", "בוא", "בואי", "הבא", "המשך", "סיימתי"]
        if any(word in last_message for word in affirmative_words) and message_count >= 6:
            # Signal interview completion
            # In real implementation, would call check_interview_completeness function
            return LLMResponse(
                content="מעולה! יצרתי עבורך הנחיות צילום מותאמות אישית. תראי אותן למטה. כשתהיי מוכנה, תוכלי להעלות את הסרטונים.",
                function_calls=[],
                finish_reason="stop"
            )

        # Progressive interview questions based on conversation stage
        response_text = self._get_interview_response(last_message, message_count)

        return LLMResponse(
            content=response_text,
            function_calls=[],
            finish_reason="stop"
        )

    def _get_interview_response(self, last_message: str, message_count: int) -> str:
        """Get appropriate response based on message content and count"""

        # Stage 1: Name and age
        if any(word in last_message for word in ["שם", "גיל", "בן", "בת", "שנים", "חודשים"]) or message_count == 1:
            return "תודה שסיפרת לי! ספרי לי קצת על החוזקות של הילד/ה - במה הוא/היא מצטיינים? מה הם אוהבים לעשות?"

        # Stage 2: Strengths
        elif any(word in last_message for word in ["חוזק", "אוהב", "מצטיין", "טוב", "יכול", "משחק", "פאזל"]) or message_count == 2:
            return "נפלא! עכשיו, ספרי לי בבקשה - מה הדאגות העיקריות שלך? מה הביא אותך לפנות לצ'יטה?"

        # Stage 3: Concerns
        elif any(word in last_message for word in ["קושי", "דאגה", "קשה", "בעיה", "לא", "מדבר", "עין", "תקשורת", "חברתי"]) or message_count == 3:
            return "תודה על השיתוף. אני מבינה שזה מאתגר. ספרי לי על שגרות יומיומיות - איך עובר יום רגיל? איך הילד/ה בגן או בבית?"

        # Stage 4: Daily routine
        elif any(word in last_message for word in ["יום", "בוקר", "גן", "בית", "שגרה", "שינה", "אוכל"]) or message_count == 4:
            return "אני מבינה. עוד דבר אחרון - מה המטרות שלך? מה את מקווה שישתפר או ישתנה?"

        # Stage 5: Goals - wrap up
        elif any(word in last_message for word in ["מטרה", "רוצה", "מקווה", "ישתפר", "שיוכל", "שתהיה"]) or message_count >= 5:
            return "תודה רבה על השיתוף! סיימנו את הראיון ההתפתחותי. עכשיו אני יכולה ליצור עבורך הנחיות מותאמות אישית לצילומי וידאו שיעזרו לי להבין טוב יותר את הילד/ה שלך. האם את מוכנה לעבור לשלב הבא?"

        # Default - encourage more sharing
        else:
            return "תודה! ספרי לי עוד - מה עוד חשוב לך שאדע?"

    async def chat_with_structured_output(
        self,
        messages: List[Message],
        response_schema: Dict[str, Any],
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Return simulated structured JSON output

        Simulates structured extraction for:
        - Interview summaries
        - Video analysis
        - Report generation
        """
        schema_str = str(response_schema)

        if "interview_summary" in schema_str:
            return self._generate_mock_interview_summary()
        elif "behavioral_observations" in schema_str:
            return self._generate_mock_video_analysis()
        elif "report_markdown" in schema_str:
            return self._generate_mock_professional_report()
        elif "parent_letter" in schema_str:
            return self._generate_mock_parent_report()

        return {}

    def _generate_mock_interview_summary(self) -> Dict[str, Any]:
        """Generate mock interview summary with video guidelines"""
        return {
            "interview_summary": {
                "child_profile": {
                    "name": "יוני",
                    "age_years": 3,
                    "age_months": 6,
                    "gender": "זכר"
                },
                "concerns": [
                    {
                        "area": "communication_speech",
                        "description": "מילים בודדות, קושי בבניית משפטים",
                        "severity_score": 7.0,
                        "reported_by": "אמא"
                    },
                    {
                        "area": "social_interaction",
                        "description": "נמנע מקשר עין",
                        "severity_score": 8.0,
                        "reported_by": "אמא"
                    }
                ],
                "strengths": [
                    {
                        "area": "cognitive_learning",
                        "description": "זיכרון מצוין, אוהב פאזלים"
                    }
                ],
                "parent_goals": [
                    "שישתפר בתקשורת",
                    "שיוכל לשחק עם ילדים אחרים"
                ]
            },
            "video_guidelines": {
                "general_tips": "צלמו בתאורה טובה, הילד במרכז הפריים",
                "why_these_scenarios": "בחרתי את התרחישים האלה על סמך מה שסיפרת לי בראיון.",
                "scenarios": [
                    {
                        "title": "משחק חופשי",
                        "description": "צלמו את הילד משחק לבד או עם ילדים אחרים למשך 5-7 דקות",
                        "priority": "essential",
                        "filming_tips": [
                            "מרחק של 2-3 מטרים",
                            "ודאו שרואים את הפנים והידיים"
                        ]
                    },
                    {
                        "title": "אינטראקציה חברתית",
                        "description": "צלמו את הילד במשחק או שיחה עם ילד אחר",
                        "priority": "essential",
                        "filming_tips": [
                            "צלמו מזווית שרואה את פני שני המשתתפים",
                            "ודאו שהסאונד תופס את השיחה"
                        ]
                    },
                    {
                        "title": "שגרה יומיומית",
                        "description": "צלמו פעילות יומיומית - אוכל, הלבשה, צחצוח שיניים",
                        "priority": "recommended",
                        "filming_tips": [
                            "צלמו מצב טבעי",
                            "אל תמהרו אותו"
                        ]
                    }
                ]
            }
        }

    def _generate_mock_video_analysis(self) -> Dict[str, Any]:
        """Generate mock video analysis"""
        return {
            "child_name": "יוני",
            "behavioral_observations": [
                {
                    "domain": "social_interaction",
                    "description": "קשר עין רק לאחר קריאה חוזרת",
                    "video_id": "vid_001",
                    "timestamp": "01:23",
                    "significance": "high",
                    "finding_type": "confirmation"
                },
                {
                    "domain": "communication",
                    "description": "שימוש במילים בודדות, ללא משפטים",
                    "video_id": "vid_002",
                    "timestamp": "02:15",
                    "significance": "high",
                    "finding_type": "confirmation"
                }
            ],
            "key_findings_summary": "נצפו קשיים בקשר עין ובתקשורת, תואם דיווח ההורה"
        }

    def _generate_mock_professional_report(self) -> Dict[str, Any]:
        """Generate mock professional report"""
        return {
            "report_markdown": """# דוח הערכה התפתחותית - יוני

## סיכום מנהלים
נמצאו קשיים משמעותיים בתקשורת ובאינטראקציה חברתית המצדיקים הפניה להערכה מקיפה.

## ממצאים עיקריים
- קשר עין מוגבל
- תקשורת במילים בודדות
- קשיים באינטראקציה חברתית

## המלצות
1. הפניה לפסיכולוג/ית התפתחות
2. שיקול הערכת תקשורת
3. מעקב התפתחותי""",
            "professional_recommendations_data": [
                {
                    "priority": 1,
                    "specialist_type": "developmental_psychologist",
                    "specialist_hebrew": "פסיכולוג/ית התפתחות",
                    "reason": "הערכה מקיפה של קשיים בתקשורת ובאינטראקציה חברתית",
                    "urgency": "high"
                },
                {
                    "priority": 2,
                    "specialist_type": "speech_therapist",
                    "specialist_hebrew": "קלינאי/ת תקשורת",
                    "reason": "הערכת שפה ותקשורת",
                    "urgency": "medium"
                }
            ],
            "visual_indicator_data": {
                "concern_levels": {
                    "communication": {"level": "high", "score": 8},
                    "social": {"level": "high", "score": 8},
                    "motor": {"level": "low", "score": 2},
                    "sensory": {"level": "medium", "score": 5}
                }
            }
        }

    def _generate_mock_parent_report(self) -> Dict[str, Any]:
        """Generate mock parent report"""
        return {
            "parent_letter": """שלום!

תודה רבה על השיתוף והאמון. יוני הוא ילד עם יכולות יפות - הזיכרון המצוין שלו והאהבה לפאזלים הם חוזקות משמעותיות.

מהראיון והסרטונים, ראיתי כמה תחומים שכדאי לתת להם תשומת לב:

**תקשורת**: יוני משתמש במילים בודדות. בגילו, ילדים רבים כבר מרכיבים משפטים של 2-3 מילים.

**קשר עין**: ראיתי שיוני מתקשה בקשר עין, במיוחד בזמן שיחה.

**אינטראקציה חברתית**: יוני נראה מעדיף משחק עצמאי ומתקשה במשחק עם ילדים אחרים.

ההמלצה שלי היא להתייעץ עם פסיכולוג/ית התפתחות שיוכלו לבצע הערכה מקיפה ולהמליץ על תמיכה מתאימה.

בהצלחה!
צ'יטה""",
            "actionable_next_steps": [
                {
                    "step": "פניה לפסיכולוג/ית התפתחות",
                    "urgency": "high",
                    "timeline": "תוך חודש",
                    "how_to": "דרך קופת החולים או פרטי"
                },
                {
                    "step": "תיעוד התנהגויות",
                    "urgency": "medium",
                    "timeline": "מהיום",
                    "how_to": "רישום יומי של תקשורת ואינטראקציות"
                }
            ],
            "home_strategies": [
                "המתנה של 5 שניות אחרי שאלה לתת לו זמן להגיב",
                "הצטרפות למשחק דרך חיקוי של מה שהוא עושה",
                "שימוש במשפטים קצרים ופשוטים בשיחה",
                "יצירת הזדמנויות למשחק עם ילד אחד במשך זמן קצר"
            ]
        }

    def supports_function_calling(self) -> bool:
        """Simulated provider has limited function calling support"""
        return False

    def supports_structured_output(self) -> bool:
        """Simulated provider supports structured output"""
        return True

    def get_provider_name(self) -> str:
        return "Simulated (No API)"
