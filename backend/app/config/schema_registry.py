"""
Schema registry for extraction schema management.

Provides access to the extraction schema defined in extraction_schema.yaml,
including field definitions, weights, types, and completeness calculation.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging

from app.config.config_loader import load_extraction_schema

logger = logging.getLogger(__name__)


class FieldDefinition(BaseModel):
    """Definition of a single extraction field."""
    name: str
    type: str
    description: str
    description_he: Optional[str] = None
    required: bool = False
    weight: Optional[float] = None  # Simple fixed weight
    weight_calculation: Optional[Dict[str, Any]] = None  # Complex weight calculation

    @property
    def max_weight(self) -> float:
        """Get maximum possible weight for this field."""
        # Handle simple weight field (for basic fields)
        if self.weight is not None:
            return self.weight

        # Handle weight_calculation (for complex fields)
        if self.weight_calculation is None:
            return 0.0

        calc_type = self.weight_calculation.get("type")

        if calc_type == "fixed":
            return self.weight_calculation.get("weight", 0.0)

        elif calc_type == "length_based":
            thresholds = self.weight_calculation.get("thresholds", [])
            if thresholds:
                return max(t.get("weight", 0.0) for t in thresholds)
            return 0.0

        elif calc_type == "binary":
            return self.weight_calculation.get("weight", 0.0)

        elif calc_type == "count_items":
            max_items = self.weight_calculation.get("max_items_counted", 1)
            weight_per_item = self.weight_calculation.get("weight_per_item", 0.0)
            return max_items * weight_per_item

        else:
            logger.warning(f"Unknown weight calculation type: {calc_type}")
            return 0.0


class SchemaRegistry:
    """
    Registry for extraction schema.

    Provides methods to access field definitions, calculate completeness,
    and validate extracted data against the schema.
    """

    def __init__(self):
        """Initialize schema registry."""
        self._schema_config = load_extraction_schema()
        self._fields: Dict[str, FieldDefinition] = {}
        self._load_fields()

    def _load_fields(self) -> None:
        """Load field definitions from configuration."""
        fields_config = self._schema_config.get("fields", {})

        for field_name, field_config in fields_config.items():
            try:
                self._fields[field_name] = FieldDefinition(
                    name=field_name,
                    **field_config
                )
            except Exception as e:
                logger.error(f"Error loading field {field_name}: {e}")
                raise

        logger.info(f"Loaded {len(self._fields)} field definitions")

    def get_field(self, field_name: str) -> Optional[FieldDefinition]:
        """
        Get field definition by name.

        Args:
            field_name: Name of the field

        Returns:
            FieldDefinition or None if not found
        """
        return self._fields.get(field_name)

    def get_all_fields(self) -> Dict[str, FieldDefinition]:
        """
        Get all field definitions.

        Returns:
            Dictionary of field name to FieldDefinition
        """
        return self._fields.copy()

    def get_field_names(self) -> List[str]:
        """
        Get list of all field names.

        Returns:
            List of field names
        """
        return list(self._fields.keys())

    def get_required_fields(self) -> List[str]:
        """
        Get list of required field names.

        Returns:
            List of required field names
        """
        return [
            name for name, field in self._fields.items()
            if field.required
        ]

    def calculate_field_weight(
        self,
        field_name: str,
        value: Any
    ) -> float:
        """
        Calculate weight contribution of a field value.

        Args:
            field_name: Name of the field
            value: Value to calculate weight for

        Returns:
            Weight contribution (0.0 to field's max weight)
        """
        field = self.get_field(field_name)
        if not field:
            logger.warning(f"Unknown field: {field_name}")
            return 0.0

        # If value is None or empty, no weight
        if value is None:
            return 0.0

        # Handle simple weight field (presence check)
        if field.weight is not None:
            return field.weight

        # Handle weight_calculation
        if field.weight_calculation is None:
            return 0.0

        calc_type = field.weight_calculation.get("type")

        if calc_type == "fixed":
            # Simple presence check
            return field.weight_calculation.get("weight", 0.0)

        elif calc_type == "binary":
            # Boolean field
            if isinstance(value, bool) and value:
                return field.weight_calculation.get("weight", 0.0)
            return 0.0

        elif calc_type == "length_based":
            # Based on text length
            if not isinstance(value, str):
                return 0.0

            length = len(value)
            thresholds = field.weight_calculation.get("thresholds", [])

            # Sort thresholds by length (descending)
            sorted_thresholds = sorted(
                thresholds,
                key=lambda t: t.get("length", 0),
                reverse=True
            )

            # Find first threshold that matches
            for threshold in sorted_thresholds:
                if length >= threshold.get("length", 0):
                    return threshold.get("weight", 0.0)

            return 0.0

        elif calc_type == "count_items":
            # Based on list/array length
            if not isinstance(value, (list, tuple)):
                return 0.0

            count = len(value)
            max_items = field.weight_calculation.get("max_items_counted", count)
            weight_per_item = field.weight_calculation.get("weight_per_item", 0.0)

            # Cap at max_items
            counted = min(count, max_items)
            return counted * weight_per_item

        else:
            logger.warning(f"Unknown weight calculation type: {calc_type}")
            return 0.0

    def calculate_completeness(
        self,
        extracted_data: Dict[str, Any]
    ) -> float:
        """
        Calculate completeness score for extracted data.

        Args:
            extracted_data: Dictionary of field name to value

        Returns:
            Completeness score (0.0 to 1.0)
        """
        total_weight = 0.0

        for field_name in self._fields.keys():
            value = extracted_data.get(field_name)
            weight = self.calculate_field_weight(field_name, value)
            total_weight += weight

        # Get total possible weight from config
        total_possible = self._schema_config.get(
            "completeness",
            {}
        ).get("total_weight", 1.0)

        # Calculate percentage
        completeness = min(total_weight / total_possible, 1.0)

        return completeness

    def get_missing_fields_summary(
        self,
        extracted_data: Dict[str, Any],
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get summary of most important missing/incomplete fields.

        Args:
            extracted_data: Dictionary of field name to value
            top_n: Number of fields to return

        Returns:
            List of field summaries sorted by importance (max weight)
        """
        missing = []

        for field_name, field in self._fields.items():
            value = extracted_data.get(field_name)
            current_weight = self.calculate_field_weight(field_name, value)
            max_weight = field.max_weight

            # If not at max weight, field is incomplete
            if current_weight < max_weight:
                missing.append({
                    "field_name": field_name,
                    "description": field.description,
                    "description_he": field.description_he,
                    "current_weight": current_weight,
                    "max_weight": max_weight,
                    "gap": max_weight - current_weight
                })

        # Sort by gap (most important missing first)
        missing.sort(key=lambda x: x["gap"], reverse=True)

        return missing[:top_n]

    def get_function_calling_schema(self) -> Dict[str, Any]:
        """
        Generate function calling schema for LLM extraction.

        This converts the extraction schema into a format suitable for
        OpenAI/Anthropic function calling.

        Returns:
            Function schema dictionary
        """
        properties = {}
        required = []

        for field_name, field in self._fields.items():
            # Map field types to JSON schema types
            type_mapping = {
                "string": "string",
                "longtext": "string",
                "array": "array",
                "boolean": "boolean",
                "integer": "integer",
                "float": "number"
            }

            json_type = type_mapping.get(field.type, "string")

            field_schema = {
                "type": json_type,
                "description": field.description
            }

            # Add array item type if applicable
            if field.type == "array":
                field_schema["items"] = {"type": "string"}

            properties[field_name] = field_schema

            if field.required:
                required.append(field_name)

        return {
            "name": self._schema_config.get("schema_name", "extract_data"),
            "description": self._schema_config.get(
                "description",
                "Extract information from conversation"
            ),
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }

    def get_completeness_threshold(self, phase: str = "screening") -> float:
        """
        Get completeness threshold for a phase.

        Args:
            phase: Phase name (from phases.yaml)

        Returns:
            Completeness threshold (0.0 to 1.0)
        """
        # This would ideally come from phase config
        # For now, return default from schema
        completeness_config = self._schema_config.get("completeness", {})
        return completeness_config.get("threshold", 0.80)


# Global singleton instance
_schema_registry: Optional[SchemaRegistry] = None


def get_schema_registry() -> SchemaRegistry:
    """
    Get global SchemaRegistry instance (singleton pattern).

    Returns:
        SchemaRegistry instance
    """
    global _schema_registry

    if _schema_registry is None:
        _schema_registry = SchemaRegistry()

    return _schema_registry


# Convenience functions
def get_field(field_name: str) -> Optional[FieldDefinition]:
    """Get field definition by name."""
    return get_schema_registry().get_field(field_name)


def calculate_completeness(extracted_data: Dict[str, Any]) -> float:
    """Calculate completeness score for extracted data."""
    return get_schema_registry().calculate_completeness(extracted_data)


def get_missing_fields(
    extracted_data: Dict[str, Any],
    top_n: int = 5
) -> List[Dict[str, Any]]:
    """Get summary of most important missing fields."""
    return get_schema_registry().get_missing_fields_summary(extracted_data, top_n)


def get_function_calling_schema() -> Dict[str, Any]:
    """Get function calling schema for LLM extraction."""
    return get_schema_registry().get_function_calling_schema()
