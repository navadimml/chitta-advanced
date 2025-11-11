"""
Intent Classification System

This module defines the GENERAL intent categories that work across all domains.
Domain-specific content is separate.
"""

from enum import Enum
from typing import Optional
from dataclasses import dataclass


class IntentCategory(Enum):
    """
    Universal intent categories that work across any domain

    These represent the TYPE of user request, not the specific content.
    """
    # User wants to continue the primary conversation/interview
    DATA_COLLECTION = "data_collection"

    # User wants to perform a specific action (domain-specific)
    ACTION_REQUEST = "action_request"

    # User wants to learn about the app/process/features
    INFORMATION_REQUEST = "information_request"

    # User is seeking consultation about previous conversations, artifacts, or uploaded documents
    CONSULTATION = "consultation"

    # User has a question tangential to the main task
    TANGENT = "tangent"

    # User wants to pause/exit
    PAUSE_EXIT = "pause_exit"


class InformationRequestType(Enum):
    """
    Sub-categories of information requests (still general)
    """
    # "What can I do in this app?"
    APP_FEATURES = "app_features"

    # "How does this process work?"
    PROCESS_EXPLANATION = "process_explanation"

    # "Where am I? What's next?"
    CURRENT_STATE = "current_state"

    # "Why can't I do X yet?"
    PREREQUISITE_EXPLANATION = "prerequisite_explanation"

    # "What happens after X?"
    NEXT_STEPS = "next_steps"

    # Domain-specific question (child development, not app features)
    DOMAIN_QUESTION = "domain_question"


@dataclass
class DetectedIntent:
    """
    Result of intent detection

    This structure works for any domain - only the specific_action
    and information_type are domain-configured.
    """
    category: IntentCategory

    # For ACTION_REQUEST: specific action name (from domain config)
    specific_action: Optional[str] = None

    # For INFORMATION_REQUEST: what type of info
    information_type: Optional[InformationRequestType] = None

    # Original user message
    user_message: str = ""

    # Confidence (0.0 to 1.0)
    confidence: float = 1.0

    # Additional context
    context: dict = None

    def __post_init__(self):
        if self.context is None:
            self.context = {}
