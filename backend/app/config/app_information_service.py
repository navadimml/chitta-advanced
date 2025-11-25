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

        # 7. Report location (state-aware)
        if "{report_location}" in template:
            report_location = self._get_report_location(context)
            template = template.replace("{report_location}", report_location)

        return template

    def _build_locked_features_text(self, context: Dict[str, Any]) -> str:
        """Build text describing locked features and when they unlock"""

        message_count = context.get("message_count", 0)
        knowledge_is_rich = context.get("knowledge_is_rich", False)
        has_guidelines = context.get("baseline_video_guidelines.exists", False)
        has_videos = context.get("baseline_videos.exists", False)
        has_report = context.get("baseline_professional_report.exists", False)
        child_name = context.get("child_name", "הילד/ה שלך")

        locked_sections = []

        # Video guidelines locked
        if not knowledge_is_rich:
            messages_needed = max(8 - message_count, 1)
            locked_sections.append(f"""**יהיה זמין בקרוב:**
• **הנחיות צילום** - אחרי שנכיר את {child_name} טוב יותר (עוד ~{messages_needed} הודעות)
• **העלאת סרטונים** - אחרי ההנחיות""")

        # Upload videos locked
        elif knowledge_is_rich and not has_guidelines:
            locked_sections.append("""**יהיה זמין בקרוב:**
• **העלאת סרטונים** - אחרי שאכין הנחיות צילום מותאמות""")

        # Analysis locked
        elif has_guidelines and not has_videos:
            locked_sections.append("""**יהיה זמין אחרי העלאת סרטונים:**
• **ניתוח AI** - ניתוח דפוסי התפתחות (~24 שעות)
• **דוח התפתחותי** - ממצאים והמלצות מפורטים""")

        # Report locked
        elif has_videos and not has_report:
            locked_sections.append("""**בתהליך:**
• **דוח התפתחותי** - אני מנתחת את הסרטונים עכשיו (~24 שעות)""")

        # Everything unlocked
        elif has_report:
            locked_sections.append("""**זמין עכשיו:**
• **דוח התפתחותי** - הדוח מוכן! אפשר לצפות, להוריד, או לשתף עם מומחים""")

        return "\n\n".join(locked_sections) if locked_sections else ""

    def _get_current_state_description(self, context: Dict[str, Any]) -> str:
        """Get current state description based on session"""

        knowledge_is_rich = context.get("knowledge_is_rich", False)
        has_guidelines = context.get("baseline_video_guidelines.exists", False)
        has_videos = context.get("baseline_videos.exists", False)
        has_report = context.get("baseline_professional_report.exists", False)
        child_name = context.get("child_name", "הילד/ה שלך")

        if has_report:
            return f"יש לך דוח מוכן עבור {child_name}"
        elif has_videos:
            return "מנתחים את הסרטונים"
        elif has_guidelines:
            return "ממתינים להעלאת סרטונים"
        elif knowledge_is_rich:
            return f"מוכנים להכין הנחיות צילום עבור {child_name}"
        else:
            return f"בשיחה להכרות עם {child_name}"

    def _get_next_step(self, context: Dict[str, Any]) -> str:
        """Get next step based on current state"""

        knowledge_is_rich = context.get("knowledge_is_rich", False)
        has_guidelines = context.get("baseline_video_guidelines.exists", False)
        has_videos = context.get("baseline_videos.exists", False)
        has_report = context.get("baseline_professional_report.exists", False)
        child_name = context.get("child_name", "הילד/ה")

        if has_report:
            return "הדוח מוכן! תוכלי לצפות בו, להוריד אותו, או לשתף עם מומחים."
        elif has_videos:
            return "אני מנתחת את הסרטונים עכשיו - זה לוקח בערך 24 שעות. בינתיים תוכלי לשאול שאלות או לכתוב ביומן."
        elif has_guidelines:
            return "ההנחיות מוכנות! הצעד הבא הוא לצלם ולהעלות את הסרטונים (בזמנך החופשי)."
        elif knowledge_is_rich:
            return f"הצעד הבא הוא הכנת הנחיות צילום מותאמות אישית עבור {child_name}. רוצה שאכין אותן?"
        else:
            return f"הצעד הבא הוא להמשיך בשיחה - ככל שאני מכירה יותר את {child_name}, כך ההנחיות והניתוח יהיו מדויקים יותר."

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

    def _get_report_location(self, context: Dict[str, Any]) -> str:
        """Get report location info based on state"""

        has_report = context.get("baseline_professional_report.exists", False)

        if not has_report:
            return "הדוח יהיה זמין אחרי שאנתח את הסרטונים (~24 שעות). הוא יופיע בכרטיס למטה ותקבלי הודעה."
        else:
            return """הדוח מוכן!

**איפה למצוא:**
• הדוח מופיע בכרטיס "דוח התפתחותי" למטה בצ'אט
• לחצי על הכרטיס לצפייה בדוח המלא
• יש אופציה להוריד כ-PDF או לשתף עם מומחים

רוצה שאסביר משהו מהדוח?"""

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
