"""
App Information Service - Config-Driven FAQ Responses

Wu Wei: Load knowledge from YAML, fill dynamic placeholders based on session state
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class AppInformationService:
    """Provides app information and FAQ responses from YAML config"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "workflows" / "app_information.yaml"

        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        logger.info(f"✅ AppInformationService loaded from {config_path}")

    def get_faq_response(
        self,
        help_topic: str,
        context: Dict[str, Any]
    ) -> Optional[str]:
        """
        Get FAQ response for given help topic with dynamic placeholders filled

        Args:
            help_topic: From ask_about_app() function (e.g., "app_features", "process_explanation")
            context: Session context with:
                - child_name: str
                - message_count: int
                - knowledge_is_rich: bool
                - baseline_video_guidelines.exists: bool
                - baseline_videos.exists: bool
                - baseline_professional_report.exists: bool

        Returns:
            FAQ answer with placeholders filled, or None if not found
        """
        # Map help_topic to FAQ key
        intent_mapping = self.config.get("intent_mapping", {})
        faq_key = intent_mapping.get(help_topic, help_topic)

        # Get FAQ response
        faq_responses = self.config.get("faq_responses", {})
        faq_data = faq_responses.get(faq_key)

        if not faq_data:
            # Try other top-level keys (privacy, what_is_app, etc.)
            other_faqs = ["privacy_and_security", "what_is_app", "why_video",
                         "sharing_professionals", "human_oversight",
                         "expert_recommendations", "about_chitta"]

            for faq_name in other_faqs:
                if faq_name in self.config:
                    faq_data = self.config[faq_name]
                    break

            if not faq_data:
                logger.warning(f"No FAQ response for help_topic: {help_topic}")
                return None

        answer_template = faq_data.get("answer_hebrew", "")

        # Fill dynamic placeholders
        answer = self._fill_placeholders(answer_template, context)

        return answer

    def _fill_placeholders(self, template: str, context: Dict[str, Any]) -> str:
        """Fill dynamic placeholders in FAQ answer based on session state"""

        # 1. Child name
        child_name = context.get("child_name", "הילד/ה שלך")
        template = template.replace("{child_name}", child_name)

        # 2. Process overview
        if "{process_overview}" in template:
            process_overview = self.config["process_overview"]["hebrew"]
            template = template.replace("{process_overview}", process_overview)

        # 3. Locked features (state-aware)
        if "{locked_features}" in template:
            locked_features_text = self._build_locked_features_text(context)
            template = template.replace("{locked_features}", locked_features_text)

        # 4. Current state description
        if "{current_state}" in template:
            state_desc = self._get_current_state_description(context)
            template = template.replace("{current_state}", state_desc)

        # 5. Next step (state-aware)
        if "{next_step}" in template:
            next_step = self._get_next_step(context)
            template = template.replace("{next_step}", next_step)

        # 6. Upload instructions (state-aware)
        if "{upload_instructions}" in template:
            upload_instructions = self._get_upload_instructions(context)
            template = template.replace("{upload_instructions}", upload_instructions)

        # 7. Portrait location (state-aware)
        if "{portrait_location}" in template:
            portrait_location = self._get_portrait_location(context)
            template = template.replace("{portrait_location}", portrait_location)

        # 7b. Legacy report_location (backwards compat)
        if "{report_location}" in template:
            report_location = self._get_portrait_location(context)
            template = template.replace("{report_location}", report_location)

        return template

    def _build_locked_features_text(self, context: Dict[str, Any]) -> str:
        """Build text describing features based on current understanding level"""

        knowledge_is_rich = context.get("knowledge_is_rich", False)
        has_videos = context.get("baseline_videos.exists", False)
        child_name = context.get("child_name", "הילד/ה שלך")

        # No locked features messaging - the app is always available
        # Just provide context about current state
        if not knowledge_is_rich:
            return f"""**ככל שנדבר יותר:**
• הדיוקן של {child_name} יתעמק
• אוכל להציע לראות סרטונים במצבים ספציפיים
• תובנות והמלצות יהיו יותר ממוקדות"""
        elif not has_videos:
            return f"""**כרגע הדיוקן מבוסס על השיחות שלנו**
• אפשר להעמיק עם סרטונים כשתרצי
• אני אציע מתי זה יכול לעזור"""
        else:
            return ""  # Videos exist, full experience available

    def _get_current_state_description(self, context: Dict[str, Any]) -> str:
        """Get current state description based on session"""

        knowledge_is_rich = context.get("knowledge_is_rich", False)
        has_videos = context.get("baseline_videos.exists", False)
        child_name = context.get("child_name", "הילד/ה שלך")

        if has_videos:
            return f"הדיוקן של {child_name} מתעמק עם הסרטונים שהעלית"
        elif knowledge_is_rich:
            return f"אני מכירה את {child_name} די טוב מהשיחות שלנו"
        else:
            return f"אנחנו בתחילת ההכרות עם {child_name}"

    def _get_next_step(self, context: Dict[str, Any]) -> str:
        """Get next step based on current state"""

        knowledge_is_rich = context.get("knowledge_is_rich", False)
        has_videos = context.get("baseline_videos.exists", False)
        child_name = context.get("child_name", "הילד/ה")

        if has_videos:
            return f"הדיוקן של {child_name} מתעדכן כל הזמן. ספרי לי עוד או שאלי שאלות."
        elif knowledge_is_rich:
            return f"ככל שנדבר יותר, כך אבין טוב יותר את {child_name}. לפעמים אציע גם לראות סרטונים."
        else:
            return f"ספרי לי עוד על {child_name} - הכל עוזר לי לבנות תמונה מלאה יותר."

    def _get_upload_instructions(self, context: Dict[str, Any]) -> str:
        """Get video upload instructions based on state"""

        has_guidelines = context.get("baseline_video_guidelines.exists", False)

        if not has_guidelines:
            return "הנחיות הצילום יהיו מוכנות אחרי שנסיים את השיחה. אז תוכלי להעלות סרטונים."
        else:
            return """כדי להעלות סרטונים:
1. לחצי על הכרטיס "הנחיות צילום" למטה
2. צלמי את הסרטונים לפי ההנחיות המותאמות
3. לחצי על כפתור "העלאת סרטון" בכרטיס
4. בחרי את הסרטון מהמכשיר שלך
5. חכי לאישור שהסרטון הועלה בהצלחה

צריכה עזרה נוספת?"""

    def _get_portrait_location(self, context: Dict[str, Any]) -> str:
        """Get portrait/child space location info"""
        child_name = context.get("child_name", "הילד/ה שלך")

        return f"""**איפה למצוא את הדיוקן החי?**

לחצי על האייקון למעלה כדי לפתוח את "החלל של {child_name}".

**מה יש שם?**
• **הדיוקן** - מי {child_name}, מהות, דפוסים, חוזקות
• **המסע** - תגליות שעשינו יחד
• **מה ראינו** - תובנות מסרטונים
• **שיתוף** - סיכומים לאנשי מקצוע

הדיוקן מתעדכן ומתעמק ככל שאנחנו מדברות יותר ומעלים סרטונים."""

    def get_app_name_meaning(self) -> str:
        """Get explanation of Chitta name meaning"""
        return self.config["app_info"]["name_meaning_hebrew"]


# Singleton instance
_app_info_service = None


def get_app_information_service() -> AppInformationService:
    """Get singleton AppInformationService instance"""
    global _app_info_service
    if _app_info_service is None:
        _app_info_service = AppInformationService()
    return _app_info_service
