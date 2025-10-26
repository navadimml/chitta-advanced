"""
Simulated LLM Provider
מחזיר תשובות מוכנות מראש - לפיתוח ללא API
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class SimulatedLLMProvider:
    """LLM מדומה - מחזיר תשובות מוכנות מראש"""

    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """תגובה מדומה"""
        # חלץ את ההודעה האחרונה
        last_message = messages[-1]["content"] if messages else ""

        # תגובות מוכנות מראש
        if "שם" in last_message or "גיל" in last_message:
            return "תודה שסיפרת לי! ספרי לי קצת על החוזקות של הילד/ה - במה הוא/היא מצטיינים? מה הם אוהבים?"

        elif "חוזק" in last_message or "אוהב" in last_message:
            return "נפלא! עכשיו, ספרי לי בבקשה - מה הדאגות העיקריות שלך? מה הביא אותך לפנות לצ'יטה?"

        elif "קושי" in last_message or "דאגה" in last_message or "קשה" in last_message:
            return "תודה על השיתוף. אני מבינה שזה מאתגר. ספרי לי על שגרות יומיומיות - איך עובר יום רגיל?"

        else:
            return "אני מקשיבה. ספרי לי עוד על זה."

    async def chat_with_structured_output(
        self,
        messages: List[Dict[str, str]],
        response_schema: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """פלט JSON מדומה"""
        if "interview_summary" in str(response_schema):
            return self._generate_mock_interview_summary()
        elif "behavioral_observations" in str(response_schema):
            return self._generate_mock_video_analysis()
        elif "report_markdown" in str(response_schema):
            return self._generate_mock_professional_report()
        elif "parent_letter" in str(response_schema):
            return self._generate_mock_parent_report()

        return {}

    def _generate_mock_interview_summary(self) -> Dict[str, Any]:
        """סיכום ראיון מדומה"""
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
                "scenarios": [
                    {
                        "title": "משחק חופשי",
                        "description": "צלמו את הילד משחק לבד 5-7 דקות",
                        "rationale": "לראות התמדה ותגובה לתסכול",
                        "priority": "essential",
                        "target_areas": ["cognitive", "emotional"]
                    },
                    {
                        "title": "אינטראקציה חברתית",
                        "description": "צלמו משחק עם אח או הורה",
                        "rationale": "לבדוק קשר עין ותקשורת",
                        "priority": "essential",
                        "target_areas": ["social", "communication"]
                    }
                ]
            }
        }

    def _generate_mock_video_analysis(self) -> Dict[str, Any]:
        """ניתוח וידאו מדומה"""
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
                }
            ],
            "key_findings_summary": "נצפו קשיים בקשר עין ובתקשורת, תואם דיווח ההורה"
        }

    def _generate_mock_professional_report(self) -> Dict[str, Any]:
        """דוח מקצועי מדומה"""
        return {
            "report_markdown": "# דוח הערכה התפתחותית\n\nנמצאו קשיים בתקשורת ובאינטראקציה חברתית...",
            "professional_recommendations_data": [
                {
                    "priority": 1,
                    "specialist_type": "developmental_psychologist",
                    "specialist_hebrew": "פסיכולוג/ית התפתחות",
                    "reason": "הערכה מקיפה של קשיים בתקשורת",
                    "urgency": "high"
                }
            ],
            "visual_indicator_data": {
                "concern_levels": {
                    "communication": {"level": "high", "score": 8},
                    "social": {"level": "high", "score": 8},
                    "sensory": {"level": "medium", "score": 5}
                }
            }
        }

    def _generate_mock_parent_report(self) -> Dict[str, Any]:
        """דוח להורה מדומה"""
        return {
            "parent_letter": "שלום! תודה רבה על השיתוף והאמון. יוני הוא ילד עם יכולות יפות...",
            "actionable_next_steps": [
                {
                    "step": "פניה לפסיכולוג/ית התפתחות",
                    "urgency": "high",
                    "timeline": "תוך חודש",
                    "how_to": "דרך קופת החולים או פרטי"
                }
            ],
            "home_strategies": [
                "המתנה של 5 שניות אחרי שאלה",
                "הצטרפות למשחק דרך חיקוי"
            ]
        }

    async def analyze_video(self, video_path: str, prompt: str, **kwargs) -> str:
        """ניתוח וידאו מדומה"""
        return "נצפה קושי בקשר עין ובתקשורת הדדית. הילד הראה התמדה במשחק עצמאי."
