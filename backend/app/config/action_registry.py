"""
Action registry for action graph and prerequisite management.

Provides access to the action graph defined in action_graph.yaml,
including action definitions and availability checks.

🌟 Wu Wei v2.0: Simplified artifact-to-action mapping
- Actions derive availability from artifact existence
- No verbose prerequisite_types section
- always_available list for actions without prerequisites
"""

import ast
import operator
from typing import Dict, Any, List, Optional, Set
from pydantic import BaseModel
import logging

from app.config.config_loader import load_action_graph

logger = logging.getLogger(__name__)


class SafeExpressionEvaluator:
    """
    Safe expression evaluator using AST parsing.

    Only supports:
    - Variable lookups from context
    - Comparison operators (<, >, <=, >=, ==, !=)
    - Boolean operators (and, or, not)
    - Basic arithmetic (+, -, *, /)
    - Numeric and string literals

    Does NOT support:
    - Function calls (except len)
    - Attribute access
    - Subscript access
    - Any form of code execution
    """

    # Allowed operators
    _operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.And: lambda a, b: a and b,
        ast.Or: lambda a, b: a or b,
        ast.Not: operator.not_,
        ast.USub: operator.neg,
    }

    def __init__(self, context: Dict[str, Any]):
        self.context = context

    def evaluate(self, expression: str) -> Any:
        """
        Safely evaluate an expression string.

        Args:
            expression: Expression string to evaluate

        Returns:
            Result of the expression

        Raises:
            ValueError: If expression contains unsafe operations
        """
        try:
            tree = ast.parse(expression, mode='eval')
            return self._eval_node(tree.body)
        except (SyntaxError, TypeError) as e:
            raise ValueError(f"Invalid expression: {expression}") from e

    def _eval_node(self, node: ast.AST) -> Any:
        """Recursively evaluate an AST node."""

        # Numeric literals
        if isinstance(node, ast.Constant):
            return node.value

        # For Python < 3.8 compatibility
        if isinstance(node, ast.Num):
            return node.n
        if isinstance(node, ast.Str):
            return node.s

        # Variable lookup
        if isinstance(node, ast.Name):
            if node.id not in self.context:
                raise ValueError(f"Unknown variable: {node.id}")
            return self.context[node.id]

        # Binary operations (a + b, a < b, etc.)
        if isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op_func = self._operators.get(type(node.op))
            if op_func is None:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
            return op_func(left, right)

        # Comparison operations (a < b, a == b, etc.)
        if isinstance(node, ast.Compare):
            left = self._eval_node(node.left)
            for op, comparator in zip(node.ops, node.comparators):
                right = self._eval_node(comparator)
                op_func = self._operators.get(type(op))
                if op_func is None:
                    raise ValueError(f"Unsupported comparison: {type(op).__name__}")
                if not op_func(left, right):
                    return False
                left = right
            return True

        # Boolean operations (and, or)
        if isinstance(node, ast.BoolOp):
            op_func = self._operators.get(type(node.op))
            if op_func is None:
                raise ValueError(f"Unsupported boolean operator: {type(node.op).__name__}")
            result = self._eval_node(node.values[0])
            for value in node.values[1:]:
                result = op_func(result, self._eval_node(value))
            return result

        # Unary operations (not, -)
        if isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            op_func = self._operators.get(type(node.op))
            if op_func is None:
                raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
            return op_func(operand)

        # Limited function calls (only len)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == 'len':
                if len(node.args) == 1 and not node.keywords:
                    return len(self._eval_node(node.args[0]))
            raise ValueError("Function calls not allowed (except len)")

        # Reject everything else
        raise ValueError(f"Unsupported expression type: {type(node).__name__}")


class ActionDefinition(BaseModel):
    """Definition of a single action."""
    action_id: str
    description: str
    category: str
    triggers_artifact: Optional[str] = None
    creates_artifact: Optional[str] = None
    opens_view: Optional[str] = None
    requires_confirmation: Optional[Dict[str, Any]] = None
    processing: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    enhanced_by: Optional[List[str]] = None


class ActionRegistry:
    """
    Registry for action graph.

    🌟 Wu Wei v2.0: Simplified availability checking
    - always_available: actions with no prerequisites
    - artifact_actions: maps artifacts to enabled actions

    Provides methods to check action availability and get definitions.
    """

    def __init__(self):
        """Initialize action registry."""
        self._action_config = load_action_graph()
        self._actions: Dict[str, ActionDefinition] = {}
        self._always_available: Set[str] = set()
        self._artifact_actions: Dict[str, Dict[str, Any]] = {}
        self._load_actions()
        self._load_availability_config()

    def _load_actions(self) -> None:
        """Load action definitions from configuration."""
        actions_config = self._action_config.get("actions", {})

        for action_id, action_config in actions_config.items():
            try:
                self._actions[action_id] = ActionDefinition(
                    action_id=action_id,
                    **action_config
                )
            except Exception as e:
                logger.error(f"Error loading action {action_id}: {e}")
                raise

        logger.info(f"Loaded {len(self._actions)} action definitions")

    def _load_availability_config(self) -> None:
        """
        🌟 Wu Wei v2.0: Load simplified availability configuration.

        - always_available: list of actions available without prerequisites
        - artifact_actions: maps artifact IDs to enabled actions
        """
        # Load always available actions
        self._always_available = set(self._action_config.get("always_available", []))
        logger.info(f"Loaded {len(self._always_available)} always-available actions")

        # Load artifact-to-action mapping
        self._artifact_actions = self._action_config.get("artifact_actions", {})
        logger.info(f"Loaded artifact_actions for {len(self._artifact_actions)} artifacts")

    def get_action(self, action_id: str) -> Optional[ActionDefinition]:
        """
        Get action definition by ID.

        Args:
            action_id: Action identifier

        Returns:
            ActionDefinition or None if not found
        """
        return self._actions.get(action_id)

    def get_all_actions(self) -> Dict[str, ActionDefinition]:
        """
        Get all action definitions.

        Returns:
            Dictionary of action ID to ActionDefinition
        """
        return self._actions.copy()

    def get_actions_by_category(self, category: str) -> List[ActionDefinition]:
        """
        Get actions by category.

        Args:
            category: Category name (interview, video, reports, etc.)

        Returns:
            List of ActionDefinitions in that category
        """
        return [
            action for action in self._actions.values()
            if action.category == category
        ]

    def _check_artifact_exists(self, artifact_id: str, context: Dict[str, Any]) -> bool:
        """
        🌟 Wu Wei: Check if an artifact exists in context.

        Args:
            artifact_id: Artifact identifier
            context: Context with artifacts dict

        Returns:
            True if artifact exists and is ready
        """
        artifacts = context.get("artifacts", {})

        if artifact_id not in artifacts:
            return False

        artifact = artifacts[artifact_id]

        # Handle both Artifact object and dict format
        if hasattr(artifact, 'exists'):
            return artifact.exists
        elif isinstance(artifact, dict):
            return artifact.get('exists', False)
        else:
            return True  # Exists if present

    def _get_enabling_artifact(self, action_id: str) -> Optional[str]:
        """
        🌟 Wu Wei: Find which artifact enables this action.

        Args:
            action_id: Action identifier

        Returns:
            Artifact ID that enables this action, or None
        """
        for artifact_id, config in self._artifact_actions.items():
            if action_id in config.get("enables", []):
                return artifact_id
        return None

    def _get_explanation_for_action(self, action_id: str) -> Optional[str]:
        """
        🌟 Wu Wei: Get explanation for why action is locked.

        Args:
            action_id: Action identifier

        Returns:
            Explanation string or None
        """
        artifact_id = self._get_enabling_artifact(action_id)
        if artifact_id and artifact_id in self._artifact_actions:
            return self._artifact_actions[artifact_id].get("explanation_when_locked")
        return None

    def check_confirmation_needed(
        self,
        action_id: str,
        context: Dict[str, Any]
    ) -> Optional[str]:
        """
        Check if action requires confirmation based on context.

        Args:
            action_id: Action identifier
            context: Context dictionary with session state

        Returns:
            Formatted confirmation message if needed, None otherwise
        """
        action = self.get_action(action_id)
        if not action or not action.requires_confirmation:
            return None

        # Get confirmation config
        confirmation_config = action.requires_confirmation
        condition = confirmation_config.get("condition")
        message_template = confirmation_config.get("confirmation_message", "")

        if not condition:
            return None

        try:
            # Safely evaluate condition using AST-based evaluator
            evaluator = SafeExpressionEvaluator(context)
            condition_met = evaluator.evaluate(condition)

            if condition_met:
                formatted_message = message_template.format(**context)
                return formatted_message

            return None

        except ValueError as e:
            logger.error(f"Invalid condition expression for {action_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error checking confirmation for {action_id}: {e}")
            return None

    def check_action_availability(
        self,
        action_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        🌟 Wu Wei v2.0: Check if action is available.

        Simplified logic:
        1. If in always_available → available
        2. Otherwise, check if enabling artifact exists

        Args:
            action_id: Action identifier
            context: Context dictionary with artifacts

        Returns:
            Dictionary with available, missing_prerequisites, explanation
        """
        action = self.get_action(action_id)
        if not action:
            return {
                "available": False,
                "missing_prerequisites": [],
                "explanation": f"Unknown action: {action_id}"
            }

        # Check if always available
        if action_id in self._always_available:
            return {
                "available": True,
                "missing_prerequisites": [],
                "explanation": None
            }

        # Check if enabled by an artifact
        enabling_artifact = self._get_enabling_artifact(action_id)

        if enabling_artifact:
            if self._check_artifact_exists(enabling_artifact, context):
                return {
                    "available": True,
                    "missing_prerequisites": [],
                    "explanation": None
                }
            else:
                return {
                    "available": False,
                    "missing_prerequisites": [enabling_artifact],
                    "explanation": self._get_explanation_for_action(action_id)
                }

        # Action not in always_available and not in artifact_actions
        # Default to unavailable (shouldn't happen with proper config)
        logger.warning(f"Action {action_id} has no availability rule configured")
        return {
            "available": False,
            "missing_prerequisites": [],
            "explanation": "Action not configured"
        }

    def get_available_actions(
        self,
        context: Dict[str, Any]
    ) -> List[str]:
        """
        🌟 Wu Wei v2.0: Get list of available action IDs.

        Args:
            context: Context dictionary with artifacts

        Returns:
            List of action IDs that are currently available
        """
        available = set(self._always_available)

        # Add actions enabled by existing artifacts
        artifacts = context.get("artifacts", {})
        for artifact_id, config in self._artifact_actions.items():
            if self._check_artifact_exists(artifact_id, context):
                available.update(config.get("enables", []))

        # Filter to only return actions that actually exist
        return [a for a in available if a in self._actions]

    def get_blocked_actions_with_explanations(
        self,
        context: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Get blocked actions with user-facing explanations.

        Args:
            context: Context dictionary with artifacts

        Returns:
            Dictionary of action_id to explanation string
        """
        blocked = {}
        available = set(self.get_available_actions(context))

        for action_id in self._actions.keys():
            if action_id not in available:
                explanation = self._get_explanation_for_action(action_id)
                if explanation:
                    blocked[action_id] = explanation

        return blocked

# Global singleton instance
_action_registry: Optional[ActionRegistry] = None


def get_action_registry() -> ActionRegistry:
    """
    Get global ActionRegistry instance (singleton pattern).

    Returns:
        ActionRegistry instance
    """
    global _action_registry

    if _action_registry is None:
        _action_registry = ActionRegistry()

    return _action_registry


# Convenience functions
def get_action(action_id: str) -> Optional[ActionDefinition]:
    """Get action definition by ID."""
    return get_action_registry().get_action(action_id)


def check_action_availability(
    action_id: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Check if action is available."""
    return get_action_registry().check_action_availability(action_id, context)


def get_available_actions(context: Dict[str, Any]) -> List[str]:
    """Get list of available action IDs."""
    return get_action_registry().get_available_actions(context)
