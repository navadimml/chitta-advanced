# Real Interview Implementation Plan

**Created**: November 4, 2025
**Purpose**: Roadmap for implementing real interview system with LLM function calling
**Current State**: Simulated responses → **Target State**: Real AI-powered continuous extraction

---

## Executive Summary

Based on comprehensive documentation analysis, the implementation follows these principles:

1. **Conversation-First Architecture** - No rigid stages, natural dialogue
2. **Continuous Extraction** - LLM extracts data opportunistically via function calling
3. **Prerequisite Graph** - Backend tracks dependencies, invisible to user
4. **Single Agent** - One LLM with tools, not multiple specialized agents
5. **Graceful Prerequisite Handling** - LLM explains and guides when actions aren't yet possible

---

## Current State Assessment

### ✅ What We Have (Simulated)

```
backend/
├── app/
│   ├── main.py                    ✅ FastAPI app with CORS
│   ├── api/routes.py              ✅ All endpoints defined
│   ├── core/
│   │   ├── app_state.py           ✅ Session management
│   │   ├── simulated_llm.py       ✅ Mock responses (to be replaced)
│   │   └── simulated_graphiti.py  ✅ In-memory graph (to be replaced)
│   └── .env                       ✅ Environment config
```

**What works**:
- Backend server running
- API endpoints functional
- Frontend-backend communication
- Session management
- Basic conversation flow

**What's simulated**:
- LLM responses (hardcoded branching logic)
- Data extraction (mock JSON)
- Knowledge graph (in-memory dict)

---

## Implementation Phases

---

## Phase 1: LLM Provider Abstraction Layer

### Goal
Create a flexible LLM provider that supports Gemini, Claude, OpenAI with function calling.

### Files to Create

#### 1. `backend/app/services/llm/base.py`
```python
"""
Base LLM Provider Interface
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class Message(BaseModel):
    role: str  # "system", "user", "assistant"
    content: str

class FunctionCall(BaseModel):
    name: str
    arguments: Dict[str, Any]

class LLMResponse(BaseModel):
    content: str
    function_calls: List[FunctionCall] = []

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""

    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        functions: Optional[List[Dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> LLMResponse:
        """Send chat completion request"""
        pass

    @abstractmethod
    async def chat_with_structured_output(
        self,
        messages: List[Message],
        response_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get structured JSON output"""
        pass
```

#### 2. `backend/app/services/llm/gemini_provider.py`
```python
"""
Google Gemini Provider (Recommended)
"""
import google.generativeai as genai
from typing import List, Dict, Any, Optional
from .base import BaseLLMProvider, Message, LLMResponse, FunctionCall

class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-2.5-pro"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    async def chat(
        self,
        messages: List[Message],
        functions: Optional[List[Dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> LLMResponse:
        """
        Send chat with function calling support
        """
        # Convert messages to Gemini format
        gemini_messages = self._convert_messages(messages)

        # Configure with functions if provided
        tools = None
        if functions:
            tools = [self._convert_function_to_tool(f) for f in functions]

        # Generate response
        response = await self.model.generate_content_async(
            gemini_messages,
            tools=tools,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens
            }
        )

        # Parse response
        return self._parse_response(response)

    async def chat_with_structured_output(
        self,
        messages: List[Message],
        response_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get structured JSON using Gemini's JSON mode
        """
        # Gemini 2.5 Pro supports JSON schema
        response = await self.model.generate_content_async(
            self._convert_messages(messages),
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": response_schema
            }
        )

        return response.text  # Already JSON

    def _convert_messages(self, messages: List[Message]) -> List[Dict]:
        """Convert to Gemini message format"""
        # Implementation details
        pass

    def _convert_function_to_tool(self, function: Dict) -> Dict:
        """Convert function definition to Gemini tool format"""
        # Implementation details
        pass

    def _parse_response(self, response) -> LLMResponse:
        """Parse Gemini response into LLMResponse"""
        # Check for function calls
        function_calls = []
        if hasattr(response, 'function_calls'):
            for fc in response.function_calls:
                function_calls.append(FunctionCall(
                    name=fc.name,
                    arguments=dict(fc.args)
                ))

        return LLMResponse(
            content=response.text if response.text else "",
            function_calls=function_calls
        )
```

#### 3. `backend/app/services/llm/factory.py`
```python
"""
LLM Factory - Creates appropriate provider
"""
import os
from .base import BaseLLMProvider
from .gemini_provider import GeminiProvider
from .simulated_provider import SimulatedLLMProvider

def create_llm_provider() -> BaseLLMProvider:
    """Create LLM provider based on environment config"""
    provider_type = os.getenv("LLM_PROVIDER", "simulated")

    if provider_type == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set")
        model = os.getenv("LLM_MODEL", "gemini-2.5-pro")
        return GeminiProvider(api_key=api_key, model=model)

    elif provider_type == "anthropic":
        # Future: Claude implementation
        raise NotImplementedError("Claude provider not yet implemented")

    elif provider_type == "openai":
        # Future: OpenAI implementation
        raise NotImplementedError("OpenAI provider not yet implemented")

    else:  # simulated
        return SimulatedLLMProvider()
```

### Dependencies to Add
```txt
# requirements.txt additions
google-genai>=0.2.0           # Gemini SDK
anthropic>=0.18.0             # Claude (optional)
openai>=1.12.0                # GPT-4 (optional)
```

### Testing Phase 1
```bash
# Test LLM provider
pytest tests/test_llm_provider.py

# Test with real API
LLM_PROVIDER=gemini GEMINI_API_KEY=xxx pytest tests/test_integration/test_chat.py
```

---

## Phase 2: Interview System Prompt & Functions

### Goal
Implement the refactored interview prompt with function calling for continuous extraction.

### Files to Create

#### 1. `backend/app/prompts/interview_functions.py`
```python
"""
Function definitions for interview conductor
"""

INTERVIEW_FUNCTIONS = [
    {
        "name": "extract_interview_data",
        "description": "Extract structured child development data from conversation. Call this whenever the parent shares relevant information - don't wait for complete answers.",
        "parameters": {
            "type": "object",
            "properties": {
                "child_name": {
                    "type": "string",
                    "description": "Child's name if mentioned"
                },
                "age": {
                    "type": "number",
                    "description": "Child's exact age in years (can be decimal like 3.5)"
                },
                "gender": {
                    "type": "string",
                    "enum": ["male", "female", "unknown"],
                    "description": "Child's gender"
                },
                "primary_concerns": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": [
                            "speech", "social", "attention", "motor",
                            "sensory", "emotional", "behavioral", "learning", "other"
                        ]
                    },
                    "description": "Categories of concerns mentioned by parent"
                },
                "concern_details": {
                    "type": "string",
                    "description": "Detailed description of concerns with specific examples from parent"
                },
                "strengths": {
                    "type": "string",
                    "description": "Child's interests, favorite activities, things they're good at"
                },
                "developmental_history": {
                    "type": "string",
                    "description": "Pregnancy, birth, developmental milestones, medical history"
                },
                "family_context": {
                    "type": "string",
                    "description": "Siblings, family developmental history, educational setting, support systems"
                },
                "daily_routines": {
                    "type": "string",
                    "description": "Description of typical day, routines, behaviors at home/school"
                },
                "parent_goals": {
                    "type": "string",
                    "description": "What parent hopes to achieve, what they want to improve"
                },
                "urgent_flags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Any safety concerns or red flags requiring immediate attention"
                }
            }
        }
    },
    {
        "name": "user_wants_action",
        "description": "Call this when the user clearly wants to perform an action or move to a different task",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "view_report",
                        "upload_video",
                        "view_video_guidelines",
                        "consultation_mode",
                        "add_journal_entry",
                        "view_journal",
                        "find_experts",
                        "share_report"
                    ],
                    "description": "The action the user wants to perform"
                },
                "details": {
                    "type": "string",
                    "description": "Additional context about what the user wants"
                }
            },
            "required": ["action"]
        }
    },
    {
        "name": "check_interview_completeness",
        "description": "Call this to check if enough information has been gathered to complete the interview and generate video guidelines",
        "parameters": {
            "type": "object",
            "properties": {
                "ready_to_complete": {
                    "type": "boolean",
                    "description": "True if sufficient information has been collected"
                },
                "missing_critical_info": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of critical information still needed"
                }
            },
            "required": ["ready_to_complete"]
        }
    }
]
```

#### 2. `backend/app/prompts/interview_prompt.py`
```python
"""
Interview Conductor System Prompt
"""

def build_interview_prompt(
    child_name: str = "unknown",
    age: str = "unknown",
    gender: str = "unknown",
    concerns: list = None,
    completeness: float = 0.0,
    context_summary: str = ""
) -> str:
    """
    Build dynamic interview prompt based on current state
    """
    concerns = concerns or []
    concerns_str = ", ".join(concerns) if concerns else "none yet"

    return f"""You are Chitta (צ'יטה), an empathetic AI assistant helping parents understand their child's development.

## Your Role

You conduct a **conversational interview** to gather information about a child's development. This should feel like a natural conversation between friends, not a rigid questionnaire.

You have access to these functions:
- **extract_interview_data**: Call this to save structured data from the conversation
- **user_wants_action**: Call this when user wants to do something specific
- **check_interview_completeness**: Call this to evaluate if interview is ready to conclude

## Core Principles

1. **Warm, Natural Hebrew**: Speak like a caring friend. Use everyday language, not clinical terms.

2. **Implicit Empathy**: Show you're listening through thoughtful follow-ups, not repeated "I understand" statements.

3. **One Primary Question Per Turn**: Each response should focus on ONE main question. You can acknowledge previous answers first.

4. **Extract Opportunistically**: Call `extract_interview_data` whenever parent shares relevant information. Do this continuously - don't wait for "complete" answers.

5. **Information Gathering Only**: Your job is to collect information. Never give advice or recommendations.

6. **Build on Facts Only**: Never assume information. If you don't know something, ask directly.

7. **Handle Tangents Gracefully**: If parent asks a question or goes off-topic, answer naturally then guide back.

## Current Interview State

- **Child name**: {child_name}
- **Age**: {age}
- **Gender**: {gender}
- **Concerns discussed**: {concerns_str}
- **Interview completeness**: {completeness:.0%}

{context_summary}

Use this to:
- Avoid asking what you already know
- Know how much more to collect
- Decide when to naturally wrap up

## Information to Gather

Collect this naturally through conversation. Order is flexible - follow the parent's lead.

### 1. Basic Information (Required - ~10% completeness)
- Child's name (optional, say "totally fine if you prefer not to share")
- Exact age (essential for context)
- Gender (infer from Hebrew grammar if possible, otherwise ask)

### 2. Strengths and Interests (~20% completeness)
**Opening**: "לפני שנדבר על אתגרים, בואי נתחיל מהדברים הטובים. במה [שם הילד] אוהב/ת לעסוק?"

Get 2-3 specific interests/strengths with brief details.

### 3. Primary Challenges (~40% completeness)
**Opening**: "מה הביא אותך אלינו היום? מה מדאיג אותך לגבי [שם]?"

For each concern:
1. Ask for specific example
2. 1-2 clarifying questions (when/where/with who/triggers)
3. Frequency and intensity
4. Duration and impact on daily life
5. Previous assessments or interventions

### 4. Additional Developmental Areas (~60% completeness)
Brief check-in on areas not mentioned: motor skills, sleep, eating, sensory sensitivities.

### 5. Developmental History (~75% completeness)
Pregnancy, birth, early milestones, medical history.

### 6. Family Context (~85% completeness)
Siblings, family history, educational setting, support systems.

### 7. Daily Routines (~90% completeness)
Typical day, routines, behaviors at home vs. school/gan.

### 8. Parent Goals (~100% completeness)
What parent hopes to achieve, what they want to improve.

## Wrapping Up the Interview

When completeness reaches ~90% and you have:
- Basic information
- Clear concerns with examples
- Some developmental context
- Parent goals

Ask: "תודה רבה על כל המידע! אני חושבת שיש לי תמונה טובה. האם יש עוד משהו חשוב שלא דיברנו עליו?"

If yes: Continue naturally
If no: Call `check_interview_completeness` with `ready_to_complete: true`

The system will then generate personalized video filming guidelines.

## Examples of Natural Flow

**Good - Natural extraction:**
```
Parent: "יוני בן 3.5, והוא לא ממש מדבר, רק מילים בודדות"
Chitta: [Calls extract_interview_data with: name="יוני", age=3.5, gender="male", concerns=["speech"], details="מילים בודדות"]
       "תודה שסיפרת לי על יוני. לפני שנדבר על הדיבור, ספרי לי - במה יוני אוהב לעסוק? מה הוא עושה בזמן החופשי?"
```

**Good - Handling question mid-interview:**
```
Parent: "יש לי שאלה - זה נורמלי שהוא לא מסתכל בעיניים?"
Chitta: "זו תצפית חשובה מאוד. קשר עין מתפתח אחרת בכל ילד, וזה אחד הדברים שאבחן בסרטונים כדי לקבל תמונה מלאה יותר.

        תודה שציינת את זה - רשמתי את הדאגה הזו.
        [Calls extract_interview_data with: concerns=["social"], details="נמנע מקשר עין"]

        חזרה לדיבור - האם יוני משלב מילים? למשל 'רוצה מים' או 'בא בחוץ'?"
```

## Remember

- You are warm, professional, and naturally conversational
- Extract data continuously, not at milestones
- One focused question at a time
- Build on what you know
- Guide conversation gently but let parent lead
- No advice - only information gathering

Let's help this family understand their child better!
"""
```

### Testing Phase 2
```bash
# Test prompt generation
pytest tests/test_prompts/test_interview_prompt.py

# Test with real LLM
pytest tests/test_integration/test_interview_flow.py
```

---

## Phase 3: Conversation Service with Continuous Extraction

### Goal
Build the core conversation service that processes messages with continuous extraction.

### Files to Create

#### 1. `backend/app/services/interview_service.py`
```python
"""
Interview Service - Handles interview extraction and completeness
"""
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class InterviewService:
    """Manages interview state and extraction"""

    def __init__(self, graphiti_client, llm_provider):
        self.graphiti = graphiti_client
        self.llm = llm_provider

    async def get_interview_context(self, family_id: str) -> Dict[str, Any]:
        """
        Get current interview state from Graphiti
        """
        # Search for all interview-related episodes
        episodes = await self.graphiti.search(
            query=f"family:{family_id} AND type:interview_data",
            limit=100
        )

        # Aggregate extracted data
        context = {
            "child_name": "unknown",
            "age": "unknown",
            "gender": "unknown",
            "primary_concerns": [],
            "concern_details": "",
            "strengths": "",
            "developmental_history": "",
            "family_context": "",
            "daily_routines": "",
            "parent_goals": "",
            "urgent_flags": []
        }

        # Merge all episodes
        for episode in episodes:
            data = episode.get("episode_body", {})
            for key in context.keys():
                if key in data and data[key]:
                    if isinstance(context[key], list):
                        if isinstance(data[key], list):
                            context[key].extend(data[key])
                        else:
                            context[key].append(data[key])
                    else:
                        context[key] = data[key]

        return context

    def calculate_completeness(self, context: Dict[str, Any]) -> float:
        """
        Calculate interview completeness (0.0 to 1.0)
        """
        score = 0.0

        # Basic info (10%)
        if context["child_name"] != "unknown":
            score += 0.03
        if context["age"] != "unknown":
            score += 0.05
        if context["gender"] != "unknown":
            score += 0.02

        # Strengths (10%)
        if context["strengths"]:
            score += 0.10

        # Concerns (30%)
        if context["primary_concerns"]:
            score += 0.15
        if context["concern_details"]:
            score += 0.15

        # Developmental history (15%)
        if context["developmental_history"]:
            score += 0.15

        # Family context (10%)
        if context["family_context"]:
            score += 0.10

        # Daily routines (10%)
        if context["daily_routines"]:
            score += 0.10

        # Parent goals (15%)
        if context["parent_goals"]:
            score += 0.15

        return min(score, 1.0)

    async def save_extracted_data(
        self,
        family_id: str,
        extracted_data: Dict[str, Any]
    ):
        """
        Save extracted interview data to Graphiti
        """
        # Create episode
        await self.graphiti.add_episode(
            name=f"interview_extraction_{datetime.now().isoformat()}",
            episode_body=extracted_data,
            group_id=family_id,
            metadata={
                "type": "interview_data",
                "timestamp": datetime.now().isoformat()
            }
        )

        logger.info(f"Saved interview extraction for family {family_id}: {list(extracted_data.keys())}")
```

#### 2. `backend/app/services/conversation_service.py`
```python
"""
Conversation Service - Main message processing with function calling
"""
import logging
from typing import Dict, Any, List
from datetime import datetime

from app.prompts.interview_prompt import build_interview_prompt
from app.prompts.interview_functions import INTERVIEW_FUNCTIONS
from app.services.interview_service import InterviewService

logger = logging.getLogger(__name__)

class ConversationService:
    """Processes messages with continuous extraction"""

    def __init__(self, graphiti_client, llm_provider, interview_service: InterviewService):
        self.graphiti = graphiti_client
        self.llm = llm_provider
        self.interview = interview_service

    async def process_message(
        self,
        family_id: str,
        message: str,
        conversation_history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Process a user message with continuous extraction

        Returns:
            {
                "response": str,
                "ui_data": dict,
                "stage": str,
                "extracted_data": dict or None
            }
        """
        # 1. Get current interview context
        interview_context = await self.interview.get_interview_context(family_id)
        completeness = self.interview.calculate_completeness(interview_context)

        logger.info(f"Interview completeness for {family_id}: {completeness:.2%}")

        # 2. Build system prompt with current state
        system_prompt = build_interview_prompt(
            child_name=interview_context.get("child_name", "unknown"),
            age=str(interview_context.get("age", "unknown")),
            gender=interview_context.get("gender", "unknown"),
            concerns=interview_context.get("primary_concerns", []),
            completeness=completeness
        )

        # 3. Build messages for LLM
        messages = [
            {"role": "system", "content": system_prompt}
        ]

        # Add conversation history (last 10 messages)
        for msg in conversation_history[-10:]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        # Add current user message
        messages.append({
            "role": "user",
            "content": message
        })

        # 4. Call LLM with function calling
        llm_response = await self.llm.chat(
            messages=messages,
            functions=INTERVIEW_FUNCTIONS,
            temperature=0.7,
            max_tokens=500
        )

        # 5. Process function calls
        extracted_data = None
        interview_complete = False
        action_requested = None

        for function_call in llm_response.function_calls:
            if function_call.name == "extract_interview_data":
                # Save extracted data
                extracted_data = function_call.arguments
                await self.interview.save_extracted_data(family_id, extracted_data)

                # Recalculate completeness
                interview_context = await self.interview.get_interview_context(family_id)
                completeness = self.interview.calculate_completeness(interview_context)

            elif function_call.name == "check_interview_completeness":
                if function_call.arguments.get("ready_to_complete"):
                    interview_complete = True

            elif function_call.name == "user_wants_action":
                action_requested = function_call.arguments.get("action")

        # 6. Determine stage and UI data
        stage = "interview"
        if interview_complete:
            stage = "video_upload"
        elif action_requested:
            stage = self._map_action_to_stage(action_requested)

        # 7. Generate UI data
        ui_data = await self._generate_ui_data(
            family_id=family_id,
            stage=stage,
            interview_context=interview_context,
            completeness=completeness,
            action_requested=action_requested
        )

        # 8. Save conversation to Graphiti
        await self.graphiti.add_episode(
            name=f"conversation_{datetime.now().isoformat()}",
            episode_body={
                "user_message": message,
                "assistant_response": llm_response.content,
                "extracted_data": extracted_data
            },
            group_id=family_id
        )

        return {
            "response": llm_response.content,
            "ui_data": ui_data,
            "stage": stage,
            "extracted_data": extracted_data
        }

    def _map_action_to_stage(self, action: str) -> str:
        """Map action to stage"""
        mapping = {
            "upload_video": "video_upload",
            "view_video_guidelines": "video_upload",
            "view_report": "view_report",
            "consultation_mode": "consultation",
            "add_journal_entry": "journal",
            "view_journal": "journal",
            "find_experts": "experts",
            "share_report": "sharing"
        }
        return mapping.get(action, "interview")

    async def _generate_ui_data(
        self,
        family_id: str,
        stage: str,
        interview_context: Dict,
        completeness: float,
        action_requested: str = None
    ) -> Dict[str, Any]:
        """Generate UI data (suggestions, cards, etc.)"""

        # Generate contextual suggestions
        suggestions = self._generate_suggestions(stage, completeness, interview_context)

        # Generate context cards
        cards = self._generate_cards(stage, completeness, interview_context)

        return {
            "suggestions": suggestions,
            "cards": cards,
            "progress": completeness,
            "stage": stage
        }

    def _generate_suggestions(
        self,
        stage: str,
        completeness: float,
        context: Dict
    ) -> List[str]:
        """Generate contextual suggestions"""
        if stage == "interview":
            if completeness < 0.3:
                return [
                    "הילד שלי בן/בת...",
                    "הדאגה העיקרית שלי היא...",
                    "רציתי לדבר על..."
                ]
            elif completeness < 0.7:
                return [
                    "ספר/י לי עוד על...",
                    "יש לי שאלה",
                    "סיימתי לספר"
                ]
            else:
                return [
                    "זה הכל, תודה",
                    "יש לי עוד משהו להוסיף",
                    "מה השלב הבא?"
                ]
        elif stage == "video_upload":
            return [
                "אעלה סרטון עכשיו",
                "תראה לי את ההנחיות",
                "יש לי שאלה על הצילום"
            ]

        return []

    def _generate_cards(
        self,
        stage: str,
        completeness: float,
        context: Dict
    ) -> List[Dict]:
        """Generate context cards"""
        cards = []

        if stage == "interview":
            cards.append({
                "type": "interview_status",
                "title": "מתנהל ראיון",
                "subtitle": f"התקדמות: {completeness:.0%}",
                "icon": "MessageCircle",
                "status": "processing" if completeness < 0.9 else "completed",
                "action": None
            })

            if context.get("primary_concerns"):
                cards.append({
                    "type": "concerns_summary",
                    "title": "דאגות שצוינו",
                    "subtitle": ", ".join(context["primary_concerns"]),
                    "icon": "AlertCircle",
                    "status": "info",
                    "action": None
                })

        elif stage == "video_upload":
            cards.append({
                "type": "video_guidelines",
                "title": "הנחיות צילום",
                "subtitle": "הוכנו עבורך הנחיות מותאמות אישית",
                "icon": "Video",
                "status": "success",
                "action": "view_guidelines"
            })

        return cards
```

### Testing Phase 3
```bash
# Test conversation service
pytest tests/test_services/test_conversation_service.py

# Test full flow with real LLM
pytest tests/test_integration/test_interview_extraction.py -v
```

---

## Phase 4: Prerequisite Checking & Intent Routing

### Goal
Implement the prerequisite graph and intent routing so the system gracefully handles requests that aren't yet possible.

### File to Create

#### `backend/app/services/prerequisite_service.py`
```python
"""
Prerequisite Service - Checks if actions are possible
"""
from typing import Dict, List, Tuple, Any
from enum import Enum

class Action(str, Enum):
    """Available actions in the system"""
    UPLOAD_VIDEO = "upload_video"
    VIEW_VIDEO_GUIDELINES = "view_video_guidelines"
    ANALYZE_VIDEOS = "analyze_videos"
    VIEW_REPORT = "view_report"
    CONSULTATION = "consultation"
    JOURNAL_ENTRY = "journal_entry"
    VIEW_JOURNAL = "view_journal"
    FIND_EXPERTS = "find_experts"
    SHARE_REPORT = "share_report"

class PrerequisiteService:
    """Checks prerequisites for actions"""

    # Prerequisite graph
    PREREQUISITES = {
        Action.VIEW_VIDEO_GUIDELINES: {
            "requires": ["interview_complete"],
            "description": "Interview must be completed to generate personalized guidelines"
        },
        Action.UPLOAD_VIDEO: {
            "requires": ["interview_complete"],
            "description": "Interview must be completed before video upload"
        },
        Action.ANALYZE_VIDEOS: {
            "requires": ["interview_complete", "videos_uploaded"],
            "minimum_videos": 3,
            "description": "Need at least 3 videos to perform analysis"
        },
        Action.VIEW_REPORT: {
            "requires": ["analysis_complete"],
            "description": "Video analysis must be complete to generate report"
        },
        Action.FIND_EXPERTS: {
            "requires": ["reports_available"],
            "recommended": True,
            "description": "Reports help match with appropriate experts (but can browse anytime)"
        },
        Action.SHARE_REPORT: {
            "requires": ["reports_available"],
            "description": "Must have reports to share"
        },
        # These are always available
        Action.CONSULTATION: {
            "requires": [],
            "description": "Consultation available anytime"
        },
        Action.JOURNAL_ENTRY: {
            "requires": [],
            "description": "Journaling available anytime"
        },
        Action.VIEW_JOURNAL: {
            "requires": [],
            "description": "View journal anytime"
        }
    }

    def __init__(self, graphiti_client, interview_service):
        self.graphiti = graphiti_client
        self.interview = interview_service

    async def check_action_feasibility(
        self,
        action: Action,
        family_id: str
    ) -> Tuple[bool, List[str], str]:
        """
        Check if action is currently feasible

        Returns:
            (is_feasible, missing_prerequisites, explanation)
        """
        prereqs = self.PREREQUISITES.get(action, {})
        required = prereqs.get("requires", [])

        if not required:
            return (True, [], "")

        # Check current state
        state = await self._get_family_state(family_id)

        missing = []
        for req in required:
            if not state.get(req, False):
                missing.append(req)

        # Special case: minimum videos
        if "videos_uploaded" in required:
            min_videos = prereqs.get("minimum_videos", 1)
            if state.get("video_count", 0) < min_videos:
                missing.append(f"minimum_{min_videos}_videos")

        is_feasible = len(missing) == 0
        explanation = prereqs.get("description", "")

        return (is_feasible, missing, explanation)

    async def _get_family_state(self, family_id: str) -> Dict[str, Any]:
        """Get current state of family's screening process"""

        # Get interview completeness
        interview_context = await self.interview.get_interview_context(family_id)
        completeness = self.interview.calculate_completeness(interview_context)
        interview_complete = completeness >= 0.9

        # Count videos
        video_episodes = await self.graphiti.search(
            query=f"family:{family_id} AND type:video_upload",
            limit=100
        )
        video_count = len(video_episodes)
        videos_uploaded = video_count > 0

        # Check for analysis
        analysis_episodes = await self.graphiti.search(
            query=f"family:{family_id} AND type:video_analysis",
            limit=1
        )
        analysis_complete = len(analysis_episodes) > 0

        # Check for reports
        report_episodes = await self.graphiti.search(
            query=f"family:{family_id} AND type:report_generated",
            limit=1
        )
        reports_available = len(report_episodes) > 0

        return {
            "interview_complete": interview_complete,
            "videos_uploaded": videos_uploaded,
            "video_count": video_count,
            "analysis_complete": analysis_complete,
            "reports_available": reports_available,
            "completeness": completeness
        }

    async def get_available_actions(self, family_id: str) -> Dict[str, bool]:
        """Get list of all actions and their feasibility"""
        result = {}
        for action in Action:
            is_feasible, _, _ = await self.check_action_feasibility(action, family_id)
            result[action.value] = is_feasible
        return result
```

### Testing Phase 4
```bash
# Test prerequisite checking
pytest tests/test_services/test_prerequisite_service.py

# Test with different states
pytest tests/test_integration/test_prerequisite_flow.py
```

---

## Phase 5: Real Graphiti with FalkorDB

### Goal
Replace simulated Graphiti with real Graphiti connected to FalkorDB.

### Setup FalkorDB

```bash
# Using Docker (recommended for development)
docker run -d \
  --name falkordb \
  -p 6379:6379 \
  falkordb/falkordb:latest

# Or using Docker Compose
# backend/docker-compose.yml
```

### File to Update

#### `backend/app/services/graphiti_service.py`
```python
"""
Real Graphiti Service
"""
from graphiti_core import Graphiti
from graphiti_core.llm_client import LLMClient
from graphiti_core.embedder import Embedder
import logging

logger = logging.getLogger(__name__)

class GraphitiService:
    """Real Graphiti integration with FalkorDB"""

    def __init__(
        self,
        falkordb_host: str,
        falkordb_port: int,
        graph_name: str,
        llm_client: LLMClient,
        embedder: Embedder
    ):
        self.client = Graphiti(
            uri=f"redis://{falkordb_host}:{falkordb_port}",
            graph_name=graph_name,
            llm_client=llm_client,
            embedder=embedder
        )

    async def initialize(self):
        """Initialize Graphiti connection"""
        await self.client.build_indices()
        logger.info("✅ Graphiti connected to FalkorDB")

    async def add_episode(
        self,
        name: str,
        episode_body: str or dict,
        group_id: str,
        metadata: dict = None
    ):
        """Add an episode to the knowledge graph"""
        await self.client.add_episode(
            name=name,
            episode_body=str(episode_body) if isinstance(episode_body, dict) else episode_body,
            source_description=f"Family {group_id}",
            reference_time=metadata.get("timestamp") if metadata else None,
            group_id=group_id
        )

    async def search(
        self,
        query: str,
        group_ids: list = None,
        limit: int = 10
    ) -> list:
        """Search knowledge graph"""
        results = await self.client.search(
            query=query,
            group_ids=group_ids,
            limit=limit
        )
        return results

    async def close(self):
        """Close connection"""
        await self.client.close()
```

### Update app_state.py

```python
# backend/app/core/app_state.py
from app.services.graphiti_service import GraphitiService
from app.services.llm.factory import create_llm_provider

async def initialize(self):
    # Create real LLM provider
    self.llm = create_llm_provider()

    # Create real Graphiti (if not simulated)
    if os.getenv("GRAPHITI_MODE") != "simulated":
        self.graphiti = GraphitiService(
            falkordb_host=os.getenv("FALKORDB_HOST", "localhost"),
            falkordb_port=int(os.getenv("FALKORDB_PORT", "6379")),
            graph_name=os.getenv("FALKORDB_GRAPH", "chitta"),
            llm_client=self.llm,  # Graphiti uses LLM for entity extraction
            embedder=create_embedder()  # Create embedder
        )
        await self.graphiti.initialize()
    else:
        self.graphiti = SimulatedGraphitiClient()
```

### Dependencies
```txt
# requirements.txt
graphiti-core>=0.3.0
redis>=5.0.0
```

### Testing Phase 5
```bash
# Test Graphiti connection
pytest tests/test_graphiti/test_connection.py

# Test episode storage and retrieval
pytest tests/test_graphiti/test_episode_storage.py
```

---

## Phase 6: Context Cards & UI Data Generation

Already partially implemented in Phase 3. Enhance with:

- Dynamic card generation based on prerequisites
- Progress tracking visualization
- Actionable cards with proper status

---

## Phase 7: Testing & Refinement

### Integration Tests

```python
# tests/test_integration/test_full_interview_flow.py

async def test_complete_interview_flow():
    """Test full interview from start to video guidelines"""

    family_id = "test_family_" + str(uuid.uuid4())

    # Message 1: Basic info
    response1 = await api.send_message(
        family_id=family_id,
        message="שלום, שמו יוני והוא בן 3.5"
    )
    assert response1["stage"] == "interview"
    assert "יוני" in response1["response"]

    # Message 2: Strengths
    response2 = await api.send_message(
        family_id=family_id,
        message="הוא אוהב מאוד פאזלים ויש לו זיכרון מעולה"
    )

    # Message 3: Concerns
    response3 = await api.send_message(
        family_id=family_id,
        message="הדאגה העיקרית שלי היא שהוא מדבר מעט מאוד, רק מילים בודדות"
    )

    # ... continue conversation until complete

    # Final message should trigger interview completion
    response_final = await api.send_message(
        family_id=family_id,
        message="זה הכל, תודה"
    )

    # Should transition to video upload stage
    assert response_final["stage"] == "video_upload"
    assert "video_guidelines" in response_final["ui_data"]
```

### Manual Testing Checklist

- [ ] Natural conversation flow (not robotic)
- [ ] Hebrew language quality
- [ ] Continuous extraction working (check Graphiti)
- [ ] Completeness calculation accurate
- [ ] Interview wraps up naturally when complete
- [ ] Video guidelines generated properly
- [ ] Prerequisite checking blocks premature actions
- [ ] Context cards update dynamically
- [ ] Suggestions are contextual and relevant

---

## Deployment Checklist

### Environment Variables

```bash
# Production .env
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-pro
GEMINI_API_KEY=<production_key>

GRAPHITI_MODE=real
FALKORDB_HOST=<production_host>
FALKORDB_PORT=6379
FALKORDB_PASSWORD=<secure_password>
FALKORDB_GRAPH=chitta_production

ENVIRONMENT=production
LOG_LEVEL=INFO

ALLOWED_ORIGINS=https://chitta.app,https://www.chitta.app
```

### Monitoring

- Set up Sentry for error tracking
- Log all LLM function calls for analysis
- Monitor API latency
- Track interview completion rates
- Monitor Graphiti query performance

---

## Success Criteria

✅ Interview feels natural, not like a form
✅ Continuous extraction works seamlessly
✅ Completeness tracking is accurate
✅ Prerequisites prevent premature actions but guide users forward
✅ Graphiti stores full context persistently
✅ Video guidelines are personalized and relevant
✅ System handles tangents and questions gracefully
✅ Hebrew language quality is excellent
✅ Response times are acceptable (<3 seconds)
✅ System scales to multiple concurrent users

---

## Estimated Timeline

- **Phase 1 (LLM Provider)**: 1-2 days
- **Phase 2 (Prompts & Functions)**: 1-2 days
- **Phase 3 (Conversation Service)**: 2-3 days
- **Phase 4 (Prerequisites)**: 1-2 days
- **Phase 5 (Real Graphiti)**: 1-2 days
- **Phase 6 (UI Enhancement)**: 1 day
- **Phase 7 (Testing & Refinement)**: 2-3 days

**Total**: ~10-15 days for full implementation with testing

---

## Next Steps

1. **Review this plan** - Discuss any concerns or modifications
2. **Set up API keys** - Get Gemini API key (free at https://ai.google.dev/)
3. **Start Phase 1** - Implement LLM provider abstraction
4. **Iterate rapidly** - Test each phase before moving to next
5. **Deploy incrementally** - Can deploy with simulated Graphiti first, then switch to real

---

**Ready to start?** Let's begin with Phase 1: LLM Provider Abstraction! 🚀
