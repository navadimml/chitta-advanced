"""
Card generator for context card management.

Generates and manages context cards based on session state,
using context_cards.yaml configuration.
"""

from typing import Dict, Any, List, Optional
import logging

from app.config.config_loader import load_context_cards

logger = logging.getLogger(__name__)


class CardGenerator:
    """
    Generator for context cards.

    Evaluates display conditions and generates appropriate cards
    based on current session state.
    """

    def __init__(self):
        """Initialize card generator."""
        self._card_config = load_context_cards()
        self._cards: Dict[str, Dict[str, Any]] = {}
        self._card_types: Dict[str, Dict[str, Any]] = {}
        self._load_card_types()
        self._load_cards()

    def _load_card_types(self) -> None:
        """🌟 Wu Wei: Load card type definitions from YAML."""
        card_types_config = self._card_config.get("card_types", {})
        self._card_types = card_types_config
        logger.info(f"Loaded {len(self._card_types)} card type definitions from YAML")

    def _load_cards(self) -> None:
        """Load card definitions from configuration."""
        cards_config = self._card_config.get("cards", {})
        self._cards = cards_config
        logger.info(f"Loaded {len(self._cards)} card definitions")

    def get_card(self, card_id: str) -> Optional[Dict[str, Any]]:
        """
        Get card definition by ID.

        Args:
            card_id: Card identifier

        Returns:
            Card configuration dict or None
        """
        return self._cards.get(card_id)

    def get_all_cards(self) -> Dict[str, Dict[str, Any]]:
        """Get all card definitions."""
        return self._cards.copy()

    def evaluate_display_conditions(
        self,
        card_id: str,
        context: Dict[str, Any]
    ) -> bool:
        """
        Evaluate if a card should be displayed based on display_conditions.

        Args:
            card_id: Card identifier
            context: Session context

        Returns:
            True if card should be displayed
        """
        card = self.get_card(card_id)
        if not card:
            return False

        conditions = card.get("display_conditions", {})
        if not conditions:
            return True  # No conditions = always show

        # DEPRECATED: Phase-based conditions (keeping for backwards compatibility)
        # 🌟 Wu Wei: Cards now use artifact-based prerequisites instead of phases
        required_phase = conditions.get("phase")
        if required_phase:
            current_phase = context.get("phase", "screening")
            if isinstance(required_phase, list):
                if current_phase not in required_phase:
                    return False
            elif required_phase != current_phase:
                return False

        # Behavioral flags that should not be evaluated as context conditions
        behavioral_flags = {
            "show_once",
            "auto_dismiss_when",
            "re_show_after_days",
            "updates_dynamically",
            "phase",  # DEPRECATED: phase is no longer a display condition
        }

        # 🌟 Wu Wei: Check all prerequisite conditions
        for condition_key, condition_value in conditions.items():
            # Skip behavioral flags - they control card behavior, not display
            if condition_key in behavioral_flags:
                continue

            # 🌟 Wu Wei: Special handling for .exists checks (artifact existence)
            # When checking "baseline_parent_report.exists: false", if artifact is missing,
            # treat it as exists=False (not None)
            if ".exists" in condition_key:
                artifact_path = condition_key.replace(".exists", "")
                artifact_value = self._get_nested_value(context, artifact_path)

                # Determine if artifact exists
                # If artifact is missing (None) or has no "exists" field, consider exists=False
                if artifact_value is None:
                    actual_exists = False
                elif isinstance(artifact_value, dict) and "exists" in artifact_value:
                    actual_exists = bool(artifact_value.get("exists"))
                else:
                    # Artifact object exists but no explicit "exists" field
                    actual_exists = True

                expected_exists = bool(condition_value)

                if actual_exists != expected_exists:
                    return False

                continue  # Condition checked, move to next

            # Handle dotted notation for nested attributes (e.g., "artifacts.video_guidelines.status")
            if "." in condition_key:
                context_value = self._get_nested_value(context, condition_key)
            else:
                context_value = context.get(condition_key)

            # Handle string conditions with operators (e.g., "< 0.80", ">= 3", "!= ready")
            if isinstance(condition_value, str):
                if not self._evaluate_string_condition(condition_value, context_value):
                    return False
            # Handle boolean conditions
            elif isinstance(condition_value, bool):
                if context_value != condition_value:
                    return False
            # Handle numeric conditions
            elif isinstance(condition_value, (int, float)):
                if context_value != condition_value:
                    return False
            # Handle list conditions (value must be in list)
            elif isinstance(condition_value, list):
                if context_value not in condition_value:
                    return False

        return True

    def _get_nested_value(self, context: Dict[str, Any], key_path: str) -> Any:
        """
        🌟 Wu Wei: Get value from nested dictionary using dot notation.

        Args:
            context: Context dictionary
            key_path: Dotted path like "baseline_parent_report.exists" or "artifacts.video_guidelines.status"

        Returns:
            Value at the path, or None if not found
        """
        keys = key_path.split(".")
        value = context

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return None
            else:
                return None

        return value

    def _translate_concerns(self, concerns: List[str]) -> List[str]:
        """
        Translate concern categories to Hebrew using observational language.

        Chitta is NOT a diagnostic tool - we use descriptive, observational
        language that focuses on what parents observe, not clinical categories.
        """
        translations = {
            "speech": "שפה ותקשורת",           # Language and communication (not just "speech")
            "social": "קשרים עם אחרים",        # Connections with others (observational)
            "attention": "ריכוז וקשב",         # Focus and attention
            "motor": "תנועה ותיאום",            # Movement and coordination (descriptive)
            "sensory": "חוויות חושיות",        # Sensory experiences (not diagnostic)
            "emotional": "ויסות רגשי",          # Emotional regulation (functional, not diagnostic)
            "behavioral": "תגובות והסתגלות",   # Reactions and adjustment (observational)
            "learning": "למידה והבנה",         # Learning and understanding
            "sleep": "שגרות שינה",             # Sleep routines (observational)
            "eating": "הרגלי אכילה",           # Eating habits (observational)
            "other": "נושאים נוספים"          # Additional topics
        }
        return [translations.get(c, c) for c in concerns]

    def _get_knowledge_depth_indicator(self, context: Dict[str, Any]) -> tuple[str, str]:
        """
        🌟 Wu Wei: Calculate qualitative knowledge depth indicator.

        Returns qualitative text based on conversation richness, NOT percentages.
        This respects Wu Wei principle of flow without rigid measurement.

        Args:
            context: Session context with extracted data

        Returns:
            Tuple of (emoji, text_in_hebrew)
        """
        # Check what information we have
        has_basic_info = bool(context.get("child_name") and context.get("age"))
        has_concerns = bool(context.get("primary_concerns") or context.get("concerns"))
        has_strengths = bool(context.get("strengths"))
        has_context = bool(context.get("other_info"))
        message_count = context.get("message_count", 0)

        # Qualitative assessment based on knowledge richness
        if not has_basic_info:
            return ("👋", "מתחילים להכיר")
        elif has_basic_info and not has_concerns and message_count < 5:
            return ("💬", "השיחה מתחילה")
        elif has_concerns and not has_strengths and message_count < 10:
            return ("🌱", "השיחה מתפתחת")
        elif has_concerns and has_strengths and not has_context:
            return ("💭", "השיחה מתעמקת")
        elif has_concerns and has_strengths and has_context:
            return ("✨", "השיחה עשירה")
        else:
            # Default based on message count
            if message_count < 5:
                return ("💬", "השיחה מתחילה")
            elif message_count < 10:
                return ("🌱", "השיחה מתפתחת")
            else:
                return ("💭", "השיחה מתעמקת")


    def _apply_formatters(
        self,
        text: str,
        context: Dict[str, Any]
    ) -> str:
        """
        🌟 Wu Wei: Apply convention-based formatters to placeholders.

        Convention-based suffix formatters:
        - {concerns_list} → auto-join with ", " and translate
        - {strengths_preview} → auto-truncate to 150 chars
        - {concerns_summary} → count + Hebrew plural
        - {concerns_count} → just the number
        - {missing_areas} → remove (placeholder for future)

        Args:
            text: Text with placeholders
            context: Session context

        Returns:
            Text with formatters applied
        """
        if not text:
            return text

        import re

        # Find all placeholders {placeholder_name}
        placeholders = re.findall(r'\{(\w+)\}', text)

        for placeholder in placeholders:
            # Extract base field name and detect suffix convention
            field_name = placeholder

            # Check suffix conventions and apply formatters
            if placeholder.endswith('_list'):
                # _list → join with commas, translate if needed
                base_field = placeholder[:-5]  # Remove '_list'

                # Try to find the field in context with smart matching
                value = None
                if base_field in context:
                    value = context.get(base_field)
                elif f"primary_{base_field}" in context:
                    value = context.get(f"primary_{base_field}")
                else:
                    value = []

                if value:
                    # Auto-translate concerns
                    if 'concern' in base_field:
                        value = self._translate_concerns(value)
                    # Join with comma
                    formatted = ", ".join(value[:3]) if isinstance(value, list) else str(value)
                else:
                    formatted = ""

                text = text.replace(f"{{{placeholder}}}", formatted)

            elif placeholder.endswith('_preview'):
                # _preview → truncate to 150 chars at sentence boundary
                base_field = placeholder[:-8]  # Remove '_preview'

                # Try to find the field in context
                value = context.get(base_field, "")

                if value:
                    # Convert lists to string (join with newlines)
                    if isinstance(value, list):
                        value = "\n".join(str(item) for item in value)

                    # Ensure value is string
                    value = str(value)

                    preview = value[:150]
                    if len(value) > 150:
                        # Try to cut at sentence boundary
                        last_period = preview.rfind(".")
                        if last_period > 50:
                            preview = preview[:last_period + 1]
                        else:
                            preview = preview + "..."
                    formatted = preview
                else:
                    formatted = ""

                text = text.replace(f"{{{placeholder}}}", formatted)

            elif placeholder.endswith('_summary'):
                # _summary → count + Hebrew plural
                base_field = placeholder[:-8]  # Remove '_summary'

                # Try to find the field in context with smart matching
                value = None
                if base_field in context:
                    value = context.get(base_field)
                elif f"primary_{base_field}" in context:
                    value = context.get(f"primary_{base_field}")
                else:
                    value = []

                if value and isinstance(value, list) and len(value) > 0:
                    count = len(value)
                    # Hebrew pluralization for concerns
                    if 'concern' in base_field:
                        if count == 1:
                            formatted = f"{count} תחום התפתחות"
                        else:
                            formatted = f"{count} תחומי התפתחות"
                    else:
                        formatted = str(count)
                else:
                    formatted = ""

                # Smart removal of trailing comma if empty
                if formatted:
                    # Has value: just replace placeholder (keeps comma)
                    text = text.replace(f"{{{placeholder}}}", formatted)
                else:
                    # No value: remove placeholder and any preceding comma
                    text = text.replace(f", {{{placeholder}}}", "")
                    text = text.replace(f"{{{placeholder}}}", "")

            elif placeholder.endswith('_count'):
                # _count → just the number
                base_field = placeholder[:-6]  # Remove '_count'

                # Try to find the field in context with smart matching
                value = None
                if base_field in context:
                    value = context.get(base_field)
                elif f"primary_{base_field}" in context:
                    value = context.get(f"primary_{base_field}")
                else:
                    value = []

                if isinstance(value, list):
                    formatted = str(len(value))
                else:
                    formatted = "0"

                text = text.replace(f"{{{placeholder}}}", formatted)

            elif placeholder == 'missing_areas':
                # Placeholder for future - remove for now
                text = text.replace(f"{{{placeholder}}}", "")

            else:
                # Simple variable replacement (parent_name, child_name, etc.)
                value = context.get(placeholder)

                if value is not None:
                    formatted = str(value)
                else:
                    # Check common mappings
                    if placeholder == "parent_name":
                        formatted = "הורה"
                    elif placeholder == "child_name":
                        formatted = context.get("child_name", "הילד/ה")
                    elif placeholder == "child_age":
                        formatted = str(context.get("child_age", ""))
                    elif placeholder == "knowledge_depth_indicator_emoji":
                        # 🌟 Wu Wei: Qualitative depth indicator (emoji only)
                        emoji, _ = self._get_knowledge_depth_indicator(context)
                        formatted = emoji
                    elif placeholder == "knowledge_depth_indicator_text":
                        # 🌟 Wu Wei: Qualitative depth indicator (text only)
                        _, text = self._get_knowledge_depth_indicator(context)
                        formatted = text
                    elif placeholder == "completeness_percentage":
                        # DEPRECATED: Legacy support for old templates
                        # Wu Wei prefers qualitative indicators
                        formatted = f"{int(context.get('completeness', 0) * 100)}"
                    elif placeholder == "uploaded_count":
                        formatted = str(context.get("uploaded_video_count", 0))
                    elif placeholder == "journal_entry_count":
                        formatted = str(context.get("journal_entry_count", 0))
                    elif placeholder == "phase":
                        # DEPRECATED: Phase is no longer used in Wu Wei architecture
                        # Keeping for backwards compatibility only
                        formatted = context.get("phase", "screening")
                    else:
                        formatted = ""

                # Ensure formatted is always a string (never None)
                if formatted is None:
                    formatted = ""

                text = text.replace(f"{{{placeholder}}}", formatted)

        return text

    def _replace_template_vars(
        self,
        text: str,
        context: Dict[str, Any]
    ) -> str:
        """
        DEPRECATED: Use _apply_formatters instead.
        Kept for backwards compatibility.
        """
        return self._apply_formatters(text, context)

    def _evaluate_string_condition(
        self,
        condition: str,
        context_value: Any
    ) -> bool:
        """
        Evaluate a string condition that may contain operators.

        Args:
            condition: Condition string (e.g., "< 0.80", ">= 3", "!= ready")
            context_value: Actual value from context

        Returns:
            True if condition matches
        """
        condition = condition.strip()

        # Check for operators
        if condition.startswith(">="):
            threshold = float(condition[2:].strip())
            return context_value is not None and float(context_value) >= threshold
        elif condition.startswith("<="):
            threshold = float(condition[2:].strip())
            return context_value is not None and float(context_value) <= threshold
        elif condition.startswith(">"):
            threshold = float(condition[1:].strip())
            return context_value is not None and float(context_value) > threshold
        elif condition.startswith("<"):
            threshold = float(condition[1:].strip())
            return context_value is not None and float(context_value) < threshold
        elif condition.startswith("!="):
            expected = condition[2:].strip()

            # Handle special cases
            if expected == "None":
                # Check if value exists and is not empty
                if context_value is None:
                    return False
                # Also check for empty strings
                if isinstance(context_value, str) and not context_value.strip():
                    return False
                return True
            elif expected == "[]":
                return context_value != [] and context_value is not None and len(context_value) > 0

            # Try to parse as number if possible
            try:
                expected_num = float(expected)
                return context_value != expected_num
            except ValueError:
                return context_value != expected
        else:
            # Direct string equality
            return context_value == condition

    def get_visible_cards(
        self,
        context: Dict[str, Any],
        max_cards: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Get cards that should be visible in current context.

        Args:
            context: Session context
            max_cards: Maximum number of cards to return

        Returns:
            List of card configurations in frontend-compatible format
        """
        visible = []

        # 🌟 Wu Wei: Legacy status mapping (for old frontend compatibility)
        # Maps card_type → status for animation/behavior hints
        legacy_status_hints = {
            "progress": "processing",
            "action_needed": "action",
            "success": "new",
            "guidance": "instruction",
            "ongoing_support": "processing",
        }

        for card_id, card in self._cards.items():
            if self.evaluate_display_conditions(card_id, context):
                card_type = card.get("card_type", "guidance")

                # Get content (could be content dict or content_by_state dict)
                content = card.get("content", {})

                # Handle content_by_state (like journal_card)
                if not content and "content_by_state" in card:
                    # Use first state as default (should be improved to check actual state)
                    content_by_state = card.get("content_by_state", {})
                    if content_by_state:
                        first_state_key = list(content_by_state.keys())[0]
                        content = content_by_state[first_state_key]

                # Extract title and subtitle
                title = content.get("title", card.get("name", ""))
                body = content.get("body", content.get("body_template", ""))

                # Handle progress_description_by_range (for interview_progress_card)
                # This is a special card-specific feature defined in YAML
                if "progress_description_by_range" in content:
                    completeness = context.get("completeness", 0)
                    progress_pct = int(completeness * 100)

                    # Determine which range applies
                    progress_desc = ""
                    if progress_pct < 30:
                        progress_desc = content["progress_description_by_range"].get("0-30", {}).get("text", "")
                    elif progress_pct < 60:
                        progress_desc = content["progress_description_by_range"].get("30-60", {}).get("text", "")
                    else:
                        progress_desc = content["progress_description_by_range"].get("60-80", {}).get("text", "")

                    # Replace {progress_description} in body
                    body = body.replace("{progress_description}", progress_desc)

                # 🌟 Wu Wei: Apply convention-based formatters to ALL placeholders
                title = self._apply_formatters(title, context)
                body = self._apply_formatters(body, context)

                # Use first meaningful line of body as subtitle
                subtitle = ""
                for line in body.split("\n"):
                    line = line.strip()
                    # Skip empty lines and markdown headers
                    if line and not line.startswith("#"):
                        # Remove markdown formatting
                        line = line.replace("**", "").replace("*", "")
                        # Skip bullet points with just placeholders
                        if not line.startswith("•") and not line.startswith("-"):
                            subtitle = line
                            break
                        elif len(line) > 3:  # Has content after bullet
                            subtitle = line
                            break

                # Limit subtitle length
                if len(subtitle) > 100:
                    subtitle = subtitle[:97] + "..."

                # 🌟 Wu Wei: Get card type config from YAML
                card_type_config = self._card_types.get(card_type, {})

                # Get icon from YAML (convert icon name to Lucide icon component name)
                icon_mapping = {
                    "progress-bar": "TrendingUp",
                    "alert-circle": "AlertCircle",
                    "check-circle": "CheckCircle",
                    "lightbulb": "Lightbulb",
                    "heart": "Heart",
                    "alert-triangle": "AlertTriangle",
                }
                yaml_icon = card_type_config.get("icon", "info")
                icon = icon_mapping.get(yaml_icon, "Info")

                # Get color from YAML
                color = card_type_config.get("color", "gray")

                # 🌟 Wu Wei: Extract action from available_actions
                # Actions can be:
                # - Simple string: "upload_video"
                # - Complex dict: {"name": "לחצי לצפייה", "action": "view_guidelines", "tracks": "..."}
                action = None
                action_label = None
                available_actions = card.get("available_actions", [])
                if available_actions:
                    first_action = available_actions[0]
                    if isinstance(first_action, str):
                        # Simple string action
                        action = first_action
                    elif isinstance(first_action, dict):
                        # Complex dict action - extract the action field
                        action = first_action.get("action")
                        action_label = first_action.get("name")

                # 🌟 Wu Wei: Check if card is linked to an artifact
                # This helps frontend know what artifact to fetch when clicking
                artifact_id = None
                if "artifacts." in str(card.get("display_conditions", {})):
                    # Extract artifact_id from display_conditions
                    # e.g., "artifacts.video_guidelines.exists: true" → "video_guidelines"
                    for condition_key in card.get("display_conditions", {}).keys():
                        if condition_key.startswith("artifacts."):
                            parts = condition_key.split(".")
                            if len(parts) >= 2:
                                artifact_id = parts[1]  # e.g., "video_guidelines"
                                break
                # Also check legacy fields (for backwards compatibility)
                if not artifact_id and card.get("video_guidelines_status"):
                    artifact_id = "baseline_video_guidelines"

                # Build card in frontend format with Wu Wei dynamic config
                card_data = {
                    "type": card_id,  # Card identifier
                    "card_type": card_type,  # 🌟 Wu Wei: YAML card_type
                    "color": color,  # 🌟 Wu Wei: YAML color (dynamic!)
                    "title": title,
                    "subtitle": subtitle,
                    "icon": icon,  # 🌟 Wu Wei: Icon from YAML card_types
                    "status": legacy_status_hints.get(card_type, "instruction"),  # Legacy support
                    "action": action,  # 🌟 Wu Wei: Properly extracted action
                    "action_label": action_label,  # Button label if specified
                    "artifact_id": artifact_id,  # 🌟 Wu Wei: Linked artifact if any
                }

                visible.append(card_data)

        # Sort by priority (higher priority first)
        # Get priority from original card config
        visible.sort(key=lambda c: self._cards.get(c["type"], {}).get("priority", 0), reverse=True)

        return visible[:max_cards]


# Global singleton
_card_generator: Optional[CardGenerator] = None


def get_card_generator() -> CardGenerator:
    """Get global CardGenerator instance."""
    global _card_generator
    if _card_generator is None:
        _card_generator = CardGenerator()
    return _card_generator
