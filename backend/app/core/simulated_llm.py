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
        """תגובה מדומה עם זרימה משופרת"""
        # חלץ את ההודעה האחרונה
        last_message = messages[-1]["content"].lower() if messages else ""

        # ספירת הודעות למעקב אחר התקדמות
        user_messages = [m for m in messages if m.get("role") == "user"]
        message_count = len(user_messages)

        # זיהוי תשובות חיוביות לסיום ראיון
        affirmative_words = ["כן", "בטח", "מוכנה", "מוכן", "בוא", "בואי", "הבא", "המשך"]
        if any(word in last_message for word in affirmative_words) and message_count >= 6:
            return "INTERVIEW_COMPLETE"  # Signal to complete interview

        # שלב 1: שם וגיל
        if any(word in last_message for word in ["שם", "גיל", "בן", "בת", "שנים", "חודשים"]) or message_count == 1:
            return "תודה שסיפרת לי! ספרי לי קצת על החוזקות של הילד/ה - במה הוא/היא מצטיינים? מה הם אוהבים לעשות?"

        # שלב 2: חוזקות
        elif any(word in last_message for word in ["חוזק", "אוהב", "מצטיין", "טוב", "יכול", "משחק", "פאזל"]) or message_count == 2:
            return "נפלא! עכשיו, ספרי לי בבקשה - מה הדאגות העיקריות שלך? מה הביא אותך לפנות לצ'יטה?"

        # שלב 3: דאגות
        elif any(word in last_message for word in ["קושי", "דאגה", "קשה", "בעיה", "לא", "מדבר", "עין", "תקשורת", "חברתי"]) or message_count == 3:
            return "תודה על השיתוף. אני מבינה שזה מאתגר. ספרי לי על שגרות יומיומיות - איך עובר יום רגיל? איך הילד/ה בגן או בבית?"

        # שלב 4: שגרה יומית
        elif any(word in last_message for word in ["יום", "בוקר", "גן", "בית", "שגרה", "שינה", "אוכל", "משחק"]) or message_count == 4:
            return "אני מבינה. עוד דבר אחרון - מה המטרות שלך? מה את מקווה שישתפר או ישתנה?"

        # שלב 5: מטרות - סיום ראיון
        elif any(word in last_message for word in ["מטרה", "רוצה", "מקווה", "ישתפר", "שיוכל", "שתהיה"]) or message_count >= 5:
            return "תודה רבה על השיתוף! סיימנו את הראיון ההתפתחותי. עכשיו אני יכולה ליצור עבורך הנחיות מותאמות אישית לצילומי וידאו שיעזרו לי להבין טוב יותר את הילד/ה שלך. האם את מוכנה לעבור לשלב הבא?"

        # ברירת מחדל - עידוד להמשיך
        else:
            return "תודה! ספרי לי עוד - מה עוד חשוב לך שאדע?"

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
                        "description": "צלמו את הילד משחק לבד או עם ילדים אחרים למשך 5-7 דקות",
                        "detailed_description": """רוצים לראות את הילד במשחק טבעי וחופשי, כשהוא בוחר בעצמו במה לשחק וקובע את קצב המשחק. זה יכול להיות:
• משחק עם צעצועים (מכוניות, בובות, קוביות לגו)
• פעילות יצירתית (ציור, פיסול בפלסטלינה)
• משחק דמיון (להעמיד פנים שהוא דמות מסוימת)
• משחק חצר (כדור, טיפוס, רכיבה על אופניים)

חשוב: לא לכוון אותו מה לעשות - תנו לו לבחור בעצמו!""",
                        "rationale": "משחק חופשי מגלה איך הילד בוחר פעילויות, כמה זמן הוא מתמיד, ואיך הוא מגיב לתסכול",
                        "detailed_rationale": """במשחק חופשי אנחנו יכולים לראות:

**התפתחות קוגניטיבית:**
• האם הילד מתכנן את המשחק או פועל באימפולס?
• איך הוא פותר בעיות (למשל, מגדל שקורס)?
• האם יש משחק דמיון והעמדת פנים?

**ויסות רגשי:**
• איך הילד מגיב כשמשהו לא מצליח?
• האם הוא ממשיך לנסות או נותן ויתור מהר?
• כמה זמן הוא יכול להתמקד בפעילות אחת?

**מוטוריקה:**
• תנועות עדינות (אוחז בעפרון, בונה מגדל)
• תיאום עין-יד
• תנועות גסות אם משחק פעיל

זו הזדמנות לראות את הילד "כמו שהוא" ללא הנחיות.""",
                        "priority": "essential",
                        "target_areas": ["cognitive", "emotional", "motor"],
                        "filming_tips": [
                            "מרחק של 2-3 מטרים - לא צמוד מדי",
                            "ודאו שרואים את הפנים והידיים של הילד",
                            "אל תתערבו - תנו לו לשחק בחופשיות",
                            "גם אם נראה משעמם, המשיכו לצלם - זה חשוב!",
                            "שמעו שהסאונד ברור אם הילד מדבר לעצמו"
                        ],
                        "example_situations": [
                            "ילד בונה מגדל מקוביות ומתסכל כשהוא קורס",
                            "ילדה משחקת 'בית-בובות' ומדברת עם הבובות",
                            "ילד רוכב על אופניים ונופל ומחליט אם לנסות שוב",
                            "ילדה מציירת ומספרת סיפור על הציור"
                        ],
                        "what_to_look_for": [
                            "כמה זמן הילד מחזיק מעמד בפעילות אחת?",
                            "האם יש משחק דמיון ויצירתיות?",
                            "איך הוא מגיב לתסכול - זועק, בוכה, או מנסה שוב?",
                            "האם הוא מדבר לעצמו במהלך המשחק?"
                        ]
                    },
                    {
                        "title": "אינטראקציה חברתית",
                        "description": "צלמו את הילד במשחק או שיחה עם ילד אחר, אח/אחות, או הורה",
                        "detailed_description": """רוצים לראות את הילד באינטראקציה עם אדם אחר - ילד או מבוגר. אפשרויות:
• משחק משותף עם ילד אחר (בגינה, בבית חבר, עם אח/אחות)
• משחק משותף עם הורה (קלפים, משחק לוח, משחק דמיון)
• פעילות יומיומית משותפת (הכנת עוגה ביחד, קריאת ספר)
• שיחה רגילה על שולחן האוכל או בזמן נסיעה ברכב

חשוב: המצב צריך להרגיש טבעי - לא "הופעה" מול המצלמה""",
                        "rationale": "אינטראקציה חברתית מגלה תקשורת, קשר עין, תגובה רגשית, ויכולת לשתף פעולה",
                        "detailed_rationale": """באינטראקציה חברתית אנחנו בודקים:

**תקשורת:**
• האם הילד יוזם שיחה או רק מגיב?
• איך הוא מבקש דברים? (מצביע, מושך, או משתמש במילים)
• האם הוא מבין הוראות פשוטות?
• כמה ברור הדיבור שלו?

**קשר עין:**
• האם הילד מסתכל על בן השיח?
• האם יש קשר עין כשהוא מבקש משהו או מדבר?
• האם הוא מסתכל על דברים שבן השיח מצביע עליהם?

**הבנה חברתית:**
• האם הילד קולט רמזים חברתיים? (למשל, אם האחר עצוב)
• איך הוא מגיב כשהאחר לוקח לו משהו?
• האם הוא מחכה לתורו במשחק?
• האם הוא משתף צעצועים?

**ויסות בקבוצה:**
• מה קורה כשיש חילוקי דעות?
• איך הוא מתמודד עם חוקי משחק?
• האם הוא מבין הומור ומשחק חברתי?""",
                        "priority": "essential",
                        "target_areas": ["social", "communication", "emotional"],
                        "filming_tips": [
                            "צלמו מזווית שרואה את פני שני המשתתפים",
                            "ודאו שהסאונד תופס את השיחה ביניהם",
                            "אל תתערבו - תנו להם לנהל את המשחק בעצמם",
                            "5-7 דקות מספיק",
                            "זה בסדר אם יש קונפליקטים קטנים - זה חלק מהתהליך!"
                        ],
                        "example_situations": [
                            "שני ילדים בונים ביחד מגדל וצריכים לחלוק קוביות",
                            "הורה ושואל את הילד 'מה עשית היום בגן?' והילד מספר",
                            "אח ואחות משחקים ומתווכחים מי קודם",
                            "הורה וילד קוראים ספר ביחד ומדברים על התמונות"
                        ],
                        "what_to_look_for": [
                            "האם יש קשר עין במהלך השיחה או המשחק?",
                            "איך הילד מבקש דברים - מילים, מחוות, או משיכה?",
                            "האם הוא מבין מה האחר אומר לו?",
                            "איך הוא מגיב רגשית - לשמחה, לעצב, לכעס של האחר?"
                        ]
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
