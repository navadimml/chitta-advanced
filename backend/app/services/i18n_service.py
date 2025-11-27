"""
I18n Service - Framework Layer for Internationalization

🌟 Wu Wei: Generic translation service, no domain knowledge.
This service only knows how to:
1. Load YAML translation files
2. Get text by key path
3. Substitute placeholders

Domain-specific logic (what keys exist, what placeholders mean)
lives in the YAML files and domain services.
"""

import os
import re
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)

# Configuration
I18N_DIR = Path(__file__).parent.parent.parent / "config" / "i18n"
DEFAULT_LANGUAGE = os.getenv("CHITTA_LANGUAGE", "he")


class I18nService:
    """
    Generic internationalization service.

    Usage:
        i18n = I18nService()

        # Simple key
        text = i18n.get("greetings.first_visit")

        # With placeholders
        text = i18n.get("greetings.returning.after_days",
                        child_name="יוני", time_ago="אתמול")

        # Get nested section
        concerns = i18n.get_section("domain.concerns")
    """

    _instance: Optional["I18nService"] = None

    def __init__(self, language: str = None):
        self.language = language or DEFAULT_LANGUAGE
        self._translations: Dict[str, Any] = {}
        self._load_translations()

    @classmethod
    def get_instance(cls, language: str = None) -> "I18nService":
        """Get singleton instance"""
        if cls._instance is None or (language and cls._instance.language != language):
            cls._instance = cls(language)
        return cls._instance

    def _load_translations(self) -> None:
        """Load translation file for current language"""
        file_path = I18N_DIR / f"{self.language}.yaml"

        if not file_path.exists():
            logger.warning(f"Translation file not found: {file_path}, falling back to {DEFAULT_LANGUAGE}")
            file_path = I18N_DIR / f"{DEFAULT_LANGUAGE}.yaml"

        if not file_path.exists():
            logger.error(f"Default translation file not found: {file_path}")
            self._translations = {}
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self._translations = yaml.safe_load(f) or {}
            logger.info(f"Loaded translations for language: {self.language}")
        except Exception as e:
            logger.error(f"Error loading translations: {e}")
            self._translations = {}

    def get(self, key: str, **placeholders) -> str:
        """
        Get translated text by dot-notation key path.

        Args:
            key: Dot-notation path (e.g., "greetings.first_visit")
            **placeholders: Values to substitute (e.g., child_name="יוני")

        Returns:
            Translated text with placeholders filled, or key if not found
        """
        value = self._get_by_path(key)

        if value is None:
            logger.warning(f"Translation key not found: {key}")
            return f"[{key}]"

        if not isinstance(value, str):
            logger.warning(f"Translation key is not a string: {key}")
            return f"[{key}]"

        # Substitute placeholders
        return self._substitute(value, placeholders)

    def get_section(self, key: str) -> Dict[str, Any]:
        """
        Get a nested section of translations.

        Args:
            key: Dot-notation path to section (e.g., "domain.concerns")

        Returns:
            Dictionary of translations, or empty dict if not found
        """
        value = self._get_by_path(key)

        if value is None:
            logger.warning(f"Translation section not found: {key}")
            return {}

        if not isinstance(value, dict):
            logger.warning(f"Translation key is not a section: {key}")
            return {}

        return value

    def get_list(self, key: str) -> list:
        """
        Get a list of translations.

        Args:
            key: Dot-notation path to list

        Returns:
            List of translations, or empty list if not found
        """
        value = self._get_by_path(key)

        if value is None:
            return []

        if isinstance(value, list):
            return value

        return []

    def has_key(self, key: str) -> bool:
        """Check if a translation key exists"""
        return self._get_by_path(key) is not None

    def get_language_info(self) -> Dict[str, Any]:
        """
        Get current language metadata for UI configuration.

        Returns:
            Dict with:
            - code: ISO language code (e.g., "he")
            - name: Native language name (e.g., "עברית")
            - direction: "rtl" or "ltr"
            - locale: Full locale code (e.g., "he-IL")
            - font_family: Recommended font (e.g., "Heebo")
            - is_rtl: Boolean convenience flag
        """
        direction = self._translations.get("direction", "ltr")
        return {
            "code": self.language,
            "name": self._translations.get("name", self.language),
            "direction": direction,
            "locale": self._translations.get("locale", self.language),
            "font_family": self._translations.get("font_family"),
            "is_rtl": direction == "rtl"
        }

    def is_rtl(self) -> bool:
        """Check if current language is RTL"""
        return self._translations.get("direction", "ltr") == "rtl"

    def get_text_align(self) -> str:
        """Get CSS text-align value for current language"""
        return "right" if self.is_rtl() else "left"

    def get_flex_direction(self) -> str:
        """Get CSS flex-direction for horizontal layouts"""
        return "row-reverse" if self.is_rtl() else "row"

    def _get_by_path(self, path: str) -> Any:
        """
        Navigate to nested value by dot-notation path.

        Handles both dot and slash notation:
        - "greetings.first_visit"
        - "greetings.returning.after_days"
        """
        keys = path.split(".")
        current = self._translations

        for key in keys:
            if not isinstance(current, dict):
                return None
            if key not in current:
                return None
            current = current[key]

        return current

    def _substitute(self, text: str, placeholders: Dict[str, Any]) -> str:
        """
        Substitute {placeholder} patterns in text.

        Args:
            text: Text with {placeholder} patterns
            placeholders: Values to substitute

        Returns:
            Text with placeholders replaced
        """
        if not placeholders:
            return text

        result = text
        for key, value in placeholders.items():
            pattern = "{" + key + "}"
            result = result.replace(pattern, str(value))

        # Log any remaining unsubstituted placeholders
        remaining = re.findall(r"\{(\w+)\}", result)
        if remaining:
            logger.debug(f"Unsubstituted placeholders: {remaining}")

        return result

    def format_time_ago(self, days: int) -> str:
        """
        Get localized time expression.

        Args:
            days: Number of days ago

        Returns:
            Localized time expression (e.g., "אתמול", "לפני 3 ימים")
        """
        if days == 1:
            return self.get("time.yesterday")
        elif days < 7:
            return self.get("time.days_ago", days=days)
        elif days == 7:
            return self.get("time.week_ago")
        else:
            weeks = days // 7
            return self.get("time.weeks_ago", weeks=weeks)


# Convenience functions for simple access
_default_service: Optional[I18nService] = None


def get_i18n(language: str = None) -> I18nService:
    """Get i18n service instance"""
    global _default_service
    if _default_service is None or (language and _default_service.language != language):
        _default_service = I18nService(language)
    return _default_service


def t(key: str, **placeholders) -> str:
    """
    Quick translation function.

    Usage:
        from app.services.i18n_service import t

        greeting = t("greetings.first_visit")
        message = t("greetings.returning.after_days", child_name="יוני", time_ago="אתמול")
    """
    return get_i18n().get(key, **placeholders)


def t_section(key: str) -> Dict[str, Any]:
    """Quick section access"""
    return get_i18n().get_section(key)


def get_language_config() -> Dict[str, Any]:
    """
    Get language configuration for frontend/API responses.

    Returns dict suitable for including in API responses:
    {
        "code": "he",
        "name": "עברית",
        "direction": "rtl",
        "locale": "he-IL",
        "font_family": "Heebo",
        "is_rtl": true
    }
    """
    return get_i18n().get_language_info()


def is_rtl() -> bool:
    """Check if current language is RTL"""
    return get_i18n().is_rtl()
