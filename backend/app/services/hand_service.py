"""
Hand Service - Action Decision Layer

The Hand acts naturally based on the Sage's wisdom. It converts natural interpretation
into structured actions - deciding which services to invoke and how.

This is Wu Wei: Natural action flowing from clear understanding.

Separation of concerns:
- Sage = "What does this mean?" (interpretation)
- Hand = "What do we do about it?" (action)
- Services = Execute the action
"""

import logging
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
from .sage_service import SageWisdom
from .llm.factory import create_llm_provider
from .llm.base import Message

logger = logging.getLogger(__name__)


class ActionMode(Enum):
    """
    Natural action modes that flow from the Sage's wisdom.

    These are not rigid categories - they describe what we'll do,
    not what the user "is".
    """
    CONVERSATION = "conversation"  # Continue natural dialogue with extraction
    CONSULTATION = "consultation"  # Provide expert developmental guidance
    DELIVER_ARTIFACT = "deliver_artifact"  # Deliver specific report/document
    EXPLAIN_PROCESS = "explain_process"  # Explain app features/process
    EXECUTE_ACTION = "execute_action"  # Execute specific action


@dataclass
class HandGuidance:
    """
    The Hand's decision on what action to take.

    This is structured guidance for the conversation service to execute.
    """
    mode: ActionMode
    reasoning: str  # Why this action?

    # Mode-specific parameters
    extraction_needed: bool = True  # For CONVERSATION mode
    consultation_type: Optional[str] = None  # For CONSULTATION: "general" or "specific"
    artifact_id: Optional[str] = None  # For DELIVER_ARTIFACT
    action_name: Optional[str] = None  # For EXECUTE_ACTION
    information_type: Optional[str] = None  # For EXPLAIN_PROCESS

    # Context for response generation
    response_context: Dict[str, Any] = None

    def __post_init__(self):
        if self.response_context is None:
            self.response_context = {}


class HandService:
    """
    The Hand - converts wisdom into structured action decisions

    Wu Wei approach: Actions flow naturally from understanding.
    The Sage tells us what's happening, the Hand decides what to do.
    """

    def __init__(self, llm_provider=None):
        """Initialize Hand service with LLM provider"""
        self.llm = llm_provider or create_llm_provider()
        logger.info("HandService initialized - The Hand is ready to act")

    async def decide_action(
        self,
        wisdom: SageWisdom,
        user_message: str,
        available_artifacts: Optional[list] = None,
        available_actions: Optional[list] = None
    ) -> HandGuidance:
        """
        The Hand decides what action to take based on the Sage's wisdom.

        This converts natural interpretation into structured action guidance.

        Args:
            wisdom: The Sage's interpretation
            user_message: Original user message
            available_artifacts: What artifacts exist
            available_actions: What actions are available

        Returns:
            HandGuidance with structured action decision
        """
        # Build action decision prompt
        available_artifacts_text = ", ".join(available_artifacts) if available_artifacts else "none yet"
        available_actions_text = ", ".join(available_actions) if available_actions else "none available"

        decision_prompt = f"""You are the Hand - you convert wisdom into action.

**The Sage's wisdom:**

{wisdom.interpretation}

**Suggested approach:** {wisdom.suggested_approach}

**Emotional state:** {wisdom.emotional_state}

**User message:** "{user_message}"

**Available resources:**
- Artifacts: {available_artifacts_text}
- Actions: {available_actions_text}

---

**Your task:** Decide which action mode best serves this parent right now.

**Action Modes:**

1. **CONVERSATION** - Continue natural dialogue flow
   - Parent is sharing/responding
   - Need to capture information
   - Keep conversation flowing naturally
   - Extraction happens in background

2. **CONSULTATION** - Provide expert developmental guidance
   - Parent asking developmental question
   - Need expert knowledge + child's specific context
   - Two types:
     * "general" - General developmental question (e.g., "What is sensory seeking?")
     * "specific" - Question about Chitta's analysis (e.g., "Why did you say he has sensory seeking?")

3. **DELIVER_ARTIFACT** - Deliver specific report/document
   - Parent requests specific artifact
   - Clear what they want
   - Just deliver it

4. **EXPLAIN_PROCESS** - Explain app features/process
   - Parent asking about the app itself
   - Meta questions about how things work
   - Information types: "app_features", "process_explanation", "current_state"

5. **EXECUTE_ACTION** - Execute specific action
   - Parent wants something specific done
   - Action name from available actions list

---

**Respond in JSON format:**

{{
  "mode": "<ACTION_MODE>",
  "reasoning": "<Why this action mode in 1-2 sentences>",
  "extraction_needed": <true/false (for CONVERSATION mode)>,
  "consultation_type": "<general or specific (for CONSULTATION mode)>",
  "artifact_id": "<artifact name (for DELIVER_ARTIFACT mode)>",
  "action_name": "<action name (for EXECUTE_ACTION mode)>",
  "information_type": "<info type (for EXPLAIN_PROCESS mode)>",
  "response_context": {{
    "sage_wisdom": "<brief summary of what sage understood>",
    "emotional_tone": "<how to respond emotionally: warm, reassuring, professional, etc.>"
  }}
}}

**Examples:**

Example 1:
Sage: "Parent is responding warmly to Chitta's question about speech..."
→ {{"mode": "CONVERSATION", "reasoning": "Parent is sharing information that should be captured", "extraction_needed": true}}

Example 2:
Sage: "Parent wants to understand professional terminology 'sensory seeking'..."
→ {{"mode": "CONSULTATION", "reasoning": "Parent needs expert explanation of developmental concept", "consultation_type": "general"}}

Example 3:
Sage: "Parent asking why Chitta identified sensory seeking in the report..."
→ {{"mode": "CONSULTATION", "reasoning": "Parent wants to understand Chitta's specific analysis", "consultation_type": "specific"}}

Example 4:
Sage: "Clear request for the report artifact..."
→ {{"mode": "DELIVER_ARTIFACT", "reasoning": "Direct request for specific artifact", "artifact_id": "baseline_parent_report"}}

---

**Now decide the action:**
"""

        try:
            # Define JSON schema for Hand's decision
            decision_schema = {
                "type": "object",
                "properties": {
                    "mode": {"type": "string", "enum": ["CONVERSATION", "CONSULTATION", "PROVIDE_INFORMATION", "VIEW_ARTIFACT"]},
                    "reasoning": {"type": "string"},
                    "extraction_needed": {"type": "boolean"},
                    "consultation_type": {"type": "string"},
                    "artifact_id": {"type": "string"},
                    "action_name": {"type": "string"},
                    "information_type": {"type": "string"}
                },
                "required": ["mode", "reasoning"]
            }

            # Use structured output instead of text parsing
            decision_json = await self.llm.chat_with_structured_output(
                messages=[
                    Message(role="system", content=decision_prompt),
                    Message(role="user", content="What action should we take?")
                ],
                response_schema=decision_schema,
                temperature=0.1
            )

            # Convert to ActionMode enum
            mode_str = decision_json.get("mode", "CONVERSATION").upper()
            mode = ActionMode[mode_str] if mode_str in ActionMode.__members__ else ActionMode.CONVERSATION

            guidance = HandGuidance(
                mode=mode,
                reasoning=decision_json.get("reasoning", "Continue natural flow"),
                extraction_needed=decision_json.get("extraction_needed", True),
                consultation_type=decision_json.get("consultation_type"),
                artifact_id=decision_json.get("artifact_id"),
                action_name=decision_json.get("action_name"),
                information_type=decision_json.get("information_type"),
                response_context=decision_json.get("response_context", {})
            )

            logger.info(f"👋 Hand's decision: {mode.value} - {guidance.reasoning[:80]}...")

            return guidance

        except Exception as e:
            logger.error(f"Hand action decision failed: {e}")
            # Fallback to conversation mode
            return HandGuidance(
                mode=ActionMode.CONVERSATION,
                reasoning="Defaulting to natural conversation flow",
                extraction_needed=True,
                response_context={
                    "sage_wisdom": wisdom.interpretation[:100],
                    "emotional_tone": "warm and supportive"
                }
            )

    def convert_to_intent_category(self, guidance: HandGuidance) -> str:
        """
        Convert Hand guidance to legacy intent category for backwards compatibility.

        This allows the new Sage/Hand architecture to work with existing
        conversation service structure while we transition.
        """
        mode_to_category = {
            ActionMode.CONVERSATION: "DATA_COLLECTION",
            ActionMode.CONSULTATION: "CONSULTATION",
            ActionMode.DELIVER_ARTIFACT: "ACTION_REQUEST",
            ActionMode.EXECUTE_ACTION: "ACTION_REQUEST",
            ActionMode.EXPLAIN_PROCESS: "INFORMATION_REQUEST"
        }
        return mode_to_category.get(guidance.mode, "DATA_COLLECTION")


# Singleton instance
_hand_service = None


def get_hand_service() -> HandService:
    """Get or create singleton Hand service instance"""
    global _hand_service
    if _hand_service is None:
        _hand_service = HandService()
    return _hand_service
