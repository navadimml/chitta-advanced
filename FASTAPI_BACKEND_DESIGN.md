# Chitta Backend: FastAPI Implementation Design

**Last Updated**: 2025-11-04
**Purpose**: Complete FastAPI backend implementation guide based on comprehensive documentation analysis

---

## 📋 Table of Contents

1. [Project Structure](#project-structure)
2. [Technology Stack](#technology-stack)
3. [Core Architecture](#core-architecture)
4. [API Endpoints](#api-endpoints)
5. [Data Models](#data-models)
6. [Services Layer](#services-layer)
7. [LLM Integration](#llm-integration)
8. [Graphiti Integration](#graphiti-integration)
9. [Video Processing](#video-processing)
10. [Authentication & Security](#authentication--security)
11. [Deployment](#deployment)
12. [Testing Strategy](#testing-strategy)

---

## 🏗️ Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app entry point
│   ├── config.py                    # Settings & environment vars
│   ├── dependencies.py              # Dependency injection
│   │
│   ├── api/                         # API routes
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── families.py          # Family management
│   │   │   ├── messages.py          # Conversation endpoints
│   │   │   ├── videos.py            # Video upload & analysis
│   │   │   ├── reports.py           # Report generation & viewing
│   │   │   ├── experts.py           # Expert search
│   │   │   ├── journal.py           # Journal entries
│   │   │   └── auth.py              # Authentication
│   │   │
│   │   └── router.py                # API router aggregation
│   │
│   ├── models/                      # Pydantic models
│   │   ├── __init__.py
│   │   ├── family.py
│   │   ├── message.py
│   │   ├── context_card.py
│   │   ├── video.py
│   │   ├── report.py
│   │   ├── expert.py
│   │   └── journal.py
│   │
│   ├── services/                    # Business logic
│   │   ├── __init__.py
│   │   ├── conversation_service.py  # Message processing
│   │   ├── interview_service.py     # Interview extraction
│   │   ├── prerequisite_service.py  # Dependency checking
│   │   ├── context_card_service.py  # Card generation
│   │   ├── video_service.py         # Video analysis
│   │   ├── report_service.py        # Report generation
│   │   ├── expert_service.py        # Expert matching
│   │   ├── graphiti_service.py      # Graphiti integration
│   │   │
│   │   └── llm/                     # LLM abstraction
│   │       ├── __init__.py
│   │       ├── base.py              # Base LLM interface
│   │       ├── factory.py           # LLM factory
│   │       ├── anthropic_provider.py
│   │       ├── openai_provider.py
│   │       └── gemini_provider.py   # RECOMMENDED
│   │
│   ├── prompts/                     # System prompts
│   │   ├── __init__.py
│   │   ├── interview_prompt.py
│   │   ├── video_analysis_prompt.py
│   │   ├── parent_report_prompt.py
│   │   └── professional_report_prompt.py
│   │
│   ├── core/                        # Core utilities
│   │   ├── __init__.py
│   │   ├── exceptions.py            # Custom exceptions
│   │   ├── logging.py               # Logging configuration
│   │   └── storage.py               # File storage (S3/local)
│   │
│   └── db/                          # Database (if using PostgreSQL)
│       ├── __init__.py
│       ├── session.py
│       └── models.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api/
│   ├── test_services/
│   └── test_integration/
│
├── scripts/
│   ├── init_graphiti.py             # Initialize Graphiti
│   └── seed_data.py                 # Seed test data
│
├── .env.example                     # Example environment variables
├── .env                             # Environment variables (gitignored)
├── requirements.txt                 # Python dependencies
├── Dockerfile                       # Docker configuration
├── docker-compose.yml               # Docker Compose setup
└── README.md                        # Backend README

```

---

## 🛠️ Technology Stack

### Core Framework

```txt
# requirements.txt

# FastAPI & Web
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
python-multipart>=0.0.6          # File uploads
websockets>=12.0                  # WebSocket support (optional)

# Async & Utils
aiofiles>=23.2.1                  # Async file operations
python-dotenv>=1.0.0              # Environment variables
pydantic>=2.5.0                   # Data validation
pydantic-settings>=2.1.0          # Settings management

# LLM Providers (install what you need)
google-genai>=0.2.0               # Gemini (RECOMMENDED)
# anthropic>=0.18.0               # Claude (optional)
# openai>=1.12.0                  # GPT-4 (optional)

# Graphiti & Graph Database
graphiti-core>=0.1.0              # Temporal knowledge graph
neo4j>=5.14.0                     # Graph database driver
# OR
# redis>=5.0.0                    # For FalkorDB (Redis-based)

# Storage
boto3>=1.34.0                     # AWS S3 (if using cloud storage)
# Or use local filesystem

# Auth & Security
python-jose[cryptography]>=3.3.0  # JWT tokens
passlib[bcrypt]>=1.7.4            # Password hashing
python-multipart>=0.0.6

# Database (optional - if not using Graphiti only)
# sqlalchemy>=2.0.23
# alembic>=1.13.0
# psycopg2-binary>=2.9.9           # PostgreSQL

# Monitoring & Logging
python-json-logger>=2.0.7
sentry-sdk[fastapi]>=1.39.0       # Error tracking (optional)

# Testing
pytest>=7.4.3
pytest-asyncio>=0.21.1
httpx>=0.25.2                     # Async HTTP client for tests
faker>=20.1.0                     # Test data generation

# Development
black>=23.12.0                    # Code formatting
ruff>=0.1.8                       # Linting
mypy>=1.7.1                       # Type checking
```

### Python Version

**Minimum**: Python 3.11
**Recommended**: Python 3.12

```bash
# Check Python version
python --version
# Python 3.12.x
```

---

## 🏛️ Core Architecture

### Layered Architecture

```
┌─────────────────────────────────────────┐
│          API Layer (FastAPI)            │
│   ├── Routes (endpoints)                │
│   ├── Request validation (Pydantic)     │
│   ├── Response serialization            │
│   └── Dependency injection              │
└─────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│          Services Layer                 │
│   ├── ConversationService              │
│   ├── InterviewService                 │
│   ├── VideoService                     │
│   ├── ReportService                    │
│   ├── PrerequisiteService              │
│   └── ContextCardService               │
└─────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│       Integration Layer                 │
│   ├── LLM Providers (abstracted)        │
│   ├── Graphiti Service                 │
│   ├── Storage Service                  │
│   └── External APIs                    │
└─────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│          Data Layer                     │
│   ├── Graphiti (primary)               │
│   ├── Neo4j/FalkorDB (graph)           │
│   ├── PostgreSQL (optional)            │
│   └── S3/Local (files)                 │
└─────────────────────────────────────────┘
```

### Key Principles

1. **Async First**: All I/O operations are async
2. **Dependency Injection**: Use FastAPI's DI system
3. **Service Pattern**: Business logic in services, not routes
4. **LLM Abstraction**: Provider-agnostic LLM interface
5. **Graphiti Primary**: Temporal knowledge graph is source of truth
6. **Stateless API**: No session storage in API layer

---

## 🔌 API Endpoints

### Complete API Specification

#### 1. Family Management

```python
POST   /api/v1/families
Request:
{
  "parent_name": "string",
  "parent_email": "string",
  "parent_phone": "string?",
  "language": "he" | "en"
}
Response:
{
  "family_id": "uuid",
  "created_at": "datetime",
  "access_token": "jwt_token"
}

GET    /api/v1/families/{family_id}
Response:
{
  "family_id": "uuid",
  "child_name": "string?",
  "child_age": "float?",
  "child_gender": "string?",
  "interview_completeness": "int (0-100)",
  "videos_uploaded": "int",
  "analysis_status": "pending|processing|complete|error",
  "created_at": "datetime"
}
```

#### 2. Conversation (Core)

```python
POST   /api/v1/messages
Request:
{
  "family_id": "uuid",
  "message": "string"
}
Response:
{
  "message_id": "uuid",
  "response": "string",                    # Chitta's response
  "context_cards": [                       # AI-generated cards
    {
      "id": "uuid",
      "title": "string",
      "subtitle": "string",
      "status": "completed|pending|action|new|processing|...",
      "icon": "string",
      "action": "string?"                  # Deep view key or null
    }
  ],
  "suggestions": [                         # Optional suggestions
    {
      "icon": "string",
      "text": "string",
      "color": "string"
    }
  ],
  "interview_completeness": "int",         # 0-100
  "function_called": "boolean",            # Did LLM extract data?
  "timestamp": "datetime"
}

GET    /api/v1/messages/{family_id}
Query params:
  - limit: int (default: 50)
  - offset: int (default: 0)
Response:
{
  "messages": [
    {
      "id": "uuid",
      "role": "user|assistant|system",
      "content": "string",
      "timestamp": "datetime"
    }
  ],
  "total": "int",
  "has_more": "boolean"
}
```

#### 3. Video Management

```python
POST   /api/v1/videos/upload
Request: multipart/form-data
  - file: video file (mp4, mov, avi)
  - family_id: uuid
  - scenario: string (e.g., "free_play", "mealtime", "focused_activity")
Response:
{
  "video_id": "uuid",
  "filename": "string",
  "size_bytes": "int",
  "duration_seconds": "int?",
  "storage_url": "string",
  "uploaded_at": "datetime"
}

GET    /api/v1/videos/{family_id}
Response:
{
  "videos": [
    {
      "id": "uuid",
      "filename": "string",
      "scenario": "string",
      "duration_seconds": "int?",
      "uploaded_at": "datetime",
      "analysis_status": "pending|processing|complete|error"
    }
  ]
}

POST   /api/v1/videos/{video_id}/analyze
Request:
{
  "force_reanalyze": "boolean?"  # Default: false
}
Response:
{
  "analysis_id": "uuid",
  "status": "processing",
  "estimated_completion": "datetime"
}

GET    /api/v1/videos/{video_id}/analysis
Response:
{
  "analysis_id": "uuid",
  "video_id": "uuid",
  "status": "pending|processing|complete|error",
  "observations": [/* DSM-5 structured observations */],
  "completed_at": "datetime?",
  "error": "string?"
}
```

#### 4. Reports

```python
GET    /api/v1/reports/{family_id}/parent
Response:
{
  "report_id": "uuid",
  "type": "parent",
  "sections": [
    {
      "title": "string",
      "content": "string",           # Hebrew markdown
      "icon": "string",
      "order": "int"
    }
  ],
  "generated_at": "datetime",
  "language": "he"
}

GET    /api/v1/reports/{family_id}/professional
Response:
{
  "report_id": "uuid",
  "type": "professional",
  "child_info": {/* ... */},
  "interview_summary": {/* ... */},
  "video_observations": [/* ... */],
  "dsm5_indicators": {/* ... */},
  "recommendations": [/* ... */],
  "generated_at": "datetime",
  "language": "he"
}

POST   /api/v1/reports/{report_id}/share
Request:
{
  "recipient_email": "string",
  "recipient_name": "string",
  "expiry_days": "int?"            # Default: 30
}
Response:
{
  "share_id": "uuid",
  "share_link": "string",
  "expires_at": "datetime"
}
```

#### 5. Context & Prerequisites

```python
GET    /api/v1/context/{family_id}
Response:
{
  "cards": [/* Context card objects */],
  "available_actions": ["string"],
  "blocked_actions": [
    {
      "action": "string",
      "missing": ["string"]          # Prerequisites needed
    }
  ],
  "interview_completeness": "int",
  "videos_uploaded": "int",
  "analysis_status": "string"
}

GET    /api/v1/context/{family_id}/completeness
Response:
{
  "completeness": "int (0-100)",
  "breakdown": {
    "basic_info": "int",
    "primary_concerns": "int",
    "concern_details": "int",
    "developmental_history": "int",
    "family_context": "int",
    "conversation_richness": "int"
  },
  "missing_areas": ["string"]
}
```

#### 6. Experts (Future)

```python
GET    /api/v1/experts/search
Query params:
  - specialty: string?
  - location: string?
  - language: string?
Response:
{
  "experts": [
    {
      "id": "uuid",
      "name": "string",
      "specialty": "string",
      "bio": "string",
      "avatar_url": "string?",
      "rating": "float",
      "contact_info": {/* ... */}
    }
  ]
}

GET    /api/v1/experts/{expert_id}
Response: {/* Expert details */}
```

#### 7. Journal

```python
POST   /api/v1/journal/entries
Request:
{
  "family_id": "uuid",
  "content": "string",
  "mood": "string?",
  "milestones": ["string"]?
}
Response:
{
  "entry_id": "uuid",
  "created_at": "datetime"
}

GET    /api/v1/journal/{family_id}
Query params:
  - start_date: date?
  - end_date: date?
  - limit: int?
Response:
{
  "entries": [
    {
      "id": "uuid",
      "content": "string",
      "mood": "string?",
      "milestones": ["string"],
      "created_at": "datetime"
    }
  ]
}
```

#### 8. Authentication

```python
POST   /api/v1/auth/register
Request:
{
  "email": "string",
  "password": "string",
  "name": "string"
}
Response:
{
  "family_id": "uuid",
  "access_token": "jwt",
  "refresh_token": "jwt",
  "token_type": "bearer"
}

POST   /api/v1/auth/login
Request:
{
  "email": "string",
  "password": "string"
}
Response: {/* Same as register */}

POST   /api/v1/auth/refresh
Request:
{
  "refresh_token": "jwt"
}
Response:
{
  "access_token": "jwt",
  "refresh_token": "jwt"
}
```

---

## 📊 Data Models

### Pydantic Models

#### app/models/family.py

```python
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum

class AnalysisStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    ERROR = "error"

class FamilyCreate(BaseModel):
    parent_name: str = Field(..., min_length=1, max_length=100)
    parent_email: EmailStr
    parent_phone: Optional[str] = None
    language: str = Field(default="he", pattern="^(he|en)$")

class FamilyResponse(BaseModel):
    family_id: str
    child_name: Optional[str] = None
    child_age: Optional[float] = None
    child_gender: Optional[str] = None
    interview_completeness: int = Field(default=0, ge=0, le=100)
    videos_uploaded: int = Field(default=0, ge=0)
    analysis_status: AnalysisStatus = AnalysisStatus.PENDING
    created_at: datetime

    class Config:
        from_attributes = True
```

#### app/models/message.py

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal, List
from datetime import datetime

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ContextCard(BaseModel):
    id: str
    title: str
    subtitle: str
    status: str  # "completed", "pending", "action", "new", "processing", etc.
    icon: str
    action: Optional[str] = None  # Deep view key or action name

class Suggestion(BaseModel):
    icon: str
    text: str
    color: str

class MessageRequest(BaseModel):
    family_id: str
    message: str = Field(..., min_length=1, max_length=2000)

class MessageResponse(BaseModel):
    message_id: str
    response: str
    context_cards: List[ContextCard]
    suggestions: List[Suggestion] = []
    interview_completeness: int
    function_called: bool
    timestamp: datetime

class Message(BaseModel):
    id: str
    family_id: str
    role: MessageRole
    content: str
    timestamp: datetime
    function_call: Optional[dict] = None

class MessageListResponse(BaseModel):
    messages: List[Message]
    total: int
    has_more: bool
```

#### app/models/video.py

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class VideoAnalysisStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    ERROR = "error"

class VideoUploadResponse(BaseModel):
    video_id: str
    filename: str
    size_bytes: int
    duration_seconds: Optional[int] = None
    storage_url: str
    uploaded_at: datetime

class VideoInfo(BaseModel):
    id: str
    filename: str
    scenario: str
    duration_seconds: Optional[int]
    uploaded_at: datetime
    analysis_status: VideoAnalysisStatus

class VideoAnalysisRequest(BaseModel):
    force_reanalyze: bool = False

class DSMObservation(BaseModel):
    category: str
    observed_behaviors: List[str]
    timestamps: List[dict]  # [{timestamp_s: int, behavior: str}]
    clinical_relevance: str

class VideoAnalysisResponse(BaseModel):
    analysis_id: str
    video_id: str
    status: VideoAnalysisStatus
    observations: List[DSMObservation] = []
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
```

#### app/models/report.py

```python
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
from enum import Enum

class ReportType(str, Enum):
    PARENT = "parent"
    PROFESSIONAL = "professional"

class ReportSection(BaseModel):
    title: str
    content: str  # Hebrew markdown
    icon: str
    order: int

class ParentReportResponse(BaseModel):
    report_id: str
    type: ReportType = ReportType.PARENT
    sections: List[ReportSection]
    generated_at: datetime
    language: str = "he"

class ProfessionalReportResponse(BaseModel):
    report_id: str
    type: ReportType = ReportType.PROFESSIONAL
    child_info: Dict[str, Any]
    interview_summary: Dict[str, Any]
    video_observations: List[Dict[str, Any]]
    dsm5_indicators: Dict[str, Any]
    recommendations: List[str]
    generated_at: datetime
    language: str = "he"

class ShareReportRequest(BaseModel):
    recipient_email: str
    recipient_name: str
    expiry_days: int = Field(default=30, ge=1, le=365)

class ShareReportResponse(BaseModel):
    share_id: str
    share_link: str
    expires_at: datetime
```

---

## 🔧 Services Layer

### 1. ConversationService

#### app/services/conversation_service.py

```python
from typing import Dict, List, Optional
from datetime import datetime
from app.services.llm.factory import LLMFactory
from app.services.llm.base import Message
from app.services.graphiti_service import GraphitiService
from app.services.interview_service import InterviewService
from app.services.context_card_service import ContextCardService
from app.services.prerequisite_service import PrerequisiteService
from app.prompts.interview_prompt import INTERVIEW_SYSTEM_PROMPT
from app.config import settings

class ConversationService:
    def __init__(self):
        self.llm = LLMFactory.create(
            provider=settings.LLM_PROVIDER,
            api_key=settings.LLM_API_KEY,
            model=settings.LLM_MODEL
        )
        self.graphiti = GraphitiService()
        self.interview_service = InterviewService()
        self.context_card_service = ContextCardService()
        self.prerequisite_service = PrerequisiteService()

    async def process_message(
        self,
        family_id: str,
        user_message: str
    ) -> Dict:
        """
        Core message processing with function calling and continuous extraction.
        """

        # 1. Load family context from Graphiti
        family_context = await self.graphiti.get_family_context(family_id)

        # 2. Get conversation history
        history = await self.graphiti.get_conversation_history(family_id, last_n=20)

        # 3. Calculate current completeness
        completeness = self.interview_service.calculate_completeness(family_context)

        # 4. Build system prompt with current state
        system_prompt = INTERVIEW_SYSTEM_PROMPT.format(
            child_name=family_context.get("child_name", "unknown"),
            age=family_context.get("age", "unknown"),
            gender=family_context.get("gender", "unknown"),
            concerns=", ".join(family_context.get("primary_concerns", [])),
            completeness=completeness
        )

        # 5. Build messages for LLM
        messages = [
            Message(role="system", content=system_prompt),
            *[Message(role=h["role"], content=h["content"]) for h in history],
            Message(role="user", content=user_message)
        ]

        # 6. Call LLM with function calling
        llm_response = await self.llm.chat_completion(
            messages=messages,
            functions=self.interview_service.get_function_definitions(),
            function_call="auto",
            temperature=0.7
        )

        # 7. Handle function calls if any
        function_called = False
        if llm_response.function_call:
            await self._handle_function_call(
                family_id=family_id,
                function_call=llm_response.function_call,
                family_context=family_context
            )
            function_called = True

        # 8. Save conversation to Graphiti
        await self.graphiti.add_episode(
            name=f"conversation_{family_id}_{datetime.now().isoformat()}",
            episode_body=f"User: {user_message}\nChitta: {llm_response.content}",
            source_description="Interview conversation",
            reference_time=datetime.now(),
            group_id=f"family_{family_id}"
        )

        # 9. Reload context (may have been updated by function call)
        updated_context = await self.graphiti.get_family_context(family_id)
        updated_completeness = self.interview_service.calculate_completeness(updated_context)

        # 10. Check if video instructions should be generated
        if (updated_completeness >= 80 and
            not updated_context.get("video_instructions_generated")):
            await self.interview_service.generate_video_instructions(
                family_id=family_id,
                context=updated_context
            )

        # 11. Generate context cards dynamically
        context_cards = await self.context_card_service.generate_cards(
            family_id=family_id,
            family_context=updated_context,
            completeness=updated_completeness
        )

        # 12. Generate suggestions
        suggestions = await self.context_card_service.generate_suggestions(
            family_context=updated_context
        )

        return {
            "response": llm_response.content,
            "context_cards": context_cards,
            "suggestions": suggestions,
            "interview_completeness": updated_completeness,
            "function_called": function_called,
            "timestamp": datetime.now()
        }

    async def _handle_function_call(
        self,
        family_id: str,
        function_call,
        family_context: Dict
    ):
        """Handle LLM function calls."""

        if function_call.name == "extract_interview_data":
            await self.interview_service.handle_extraction(
                family_id=family_id,
                data=function_call.arguments
            )

        elif function_call.name == "user_wants_action":
            await self.prerequisite_service.handle_action_request(
                family_id=family_id,
                action=function_call.arguments["action"],
                context=family_context
            )

        elif function_call.name == "user_is_stuck":
            await self._handle_user_stuck(
                family_id=family_id,
                confusion_type=function_call.arguments["confusion_type"]
            )

    async def _handle_user_stuck(self, family_id: str, confusion_type: str):
        """Log user confusion for analytics."""
        await self.graphiti.add_episode(
            name=f"user_stuck_{family_id}_{datetime.now().isoformat()}",
            episode_body=f"User confusion type: {confusion_type}",
            source_description="User stuck event",
            reference_time=datetime.now(),
            group_id=f"family_{family_id}"
        )
```

### 2. InterviewService

#### app/services/interview_service.py

```python
from typing import Dict, List
from datetime import datetime
from app.services.graphiti_service import GraphitiService

class InterviewService:
    def __init__(self):
        self.graphiti = GraphitiService()

    def get_function_definitions(self) -> List[Dict]:
        """Return LLM function definitions for interview."""
        return [
            {
                "name": "extract_interview_data",
                "description": "Extract structured child development data from conversation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "child_name": {
                            "type": "string",
                            "description": "Child's name if mentioned"
                        },
                        "age": {
                            "type": "number",
                            "description": "Child's age in years (decimal, e.g., 3.5)"
                        },
                        "gender": {
                            "type": "string",
                            "enum": ["male", "female", "unknown"]
                        },
                        "primary_concerns": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["speech", "social", "attention", "motor",
                                        "sensory", "emotional", "behavioral", "learning"]
                            }
                        },
                        "concern_details": {
                            "type": "string",
                            "description": "Detailed description with examples"
                        },
                        "strengths": {"type": "string"},
                        "developmental_history": {"type": "string"},
                        "family_context": {"type": "string"},
                        "urgent_flags": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                }
            },
            {
                "name": "user_wants_action",
                "description": "User wants to perform an action",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["view_report", "upload_video", "view_guidelines", "consultation"]
                        }
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "user_is_stuck",
                "description": "User seems confused or wants to pause",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "confusion_type": {
                            "type": "string",
                            "enum": ["unclear_question", "wants_pause", "off_topic", "other"]
                        }
                    }
                }
            }
        ]

    async def handle_extraction(self, family_id: str, data: Dict):
        """Save extracted interview data to Graphiti (additive)."""

        # Build facts from extracted data
        facts = []

        if data.get("child_name"):
            facts.append(f"Child's name is {data['child_name']}")
        if data.get("age"):
            facts.append(f"Child is {data['age']} years old")
        if data.get("gender"):
            facts.append(f"Child's gender is {data['gender']}")
        if data.get("primary_concerns"):
            concerns_str = ", ".join(data['primary_concerns'])
            facts.append(f"Primary concerns: {concerns_str}")
        if data.get("concern_details"):
            facts.append(f"Concern details: {data['concern_details']}")
        if data.get("strengths"):
            facts.append(f"Child's strengths: {data['strengths']}")
        if data.get("developmental_history"):
            facts.append(f"Developmental history: {data['developmental_history']}")
        if data.get("family_context"):
            facts.append(f"Family context: {data['family_context']}")

        # Add episode to Graphiti
        await self.graphiti.add_episode(
            name=f"interview_extraction_{family_id}_{datetime.now().isoformat()}",
            episode_body="\n".join(facts),
            source_description="Interview data extraction",
            reference_time=datetime.now(),
            group_id=f"family_{family_id}"
        )

        # Handle urgent flags
        if data.get("urgent_flags"):
            await self._handle_urgent_flags(family_id, data['urgent_flags'])

    def calculate_completeness(self, context: Dict) -> int:
        """Calculate interview completeness percentage (0-100)."""

        score = 0

        # Basic information (20 points)
        if context.get('child_name'):
            score += 5
        if context.get('age'):
            score += 10  # Essential
        if context.get('gender'):
            score += 5

        # Primary concerns (30 points)
        concerns = context.get('primary_concerns', [])
        if concerns:
            score += 15
        concern_details = context.get('concern_details', '')
        if concern_details and len(concern_details) > 100:
            score += 15

        # Strengths (10 points)
        if context.get('strengths'):
            score += 10

        # Developmental areas (20 points)
        areas_covered = 0
        raw_text = context.get('raw_text', '').lower()
        for area in ['communication', 'social', 'behavior', 'attention',
                     'learning', 'sensory', 'daily_routines']:
            if area in raw_text:
                areas_covered += 1
        score += min(20, areas_covered * 3)

        # History (10 points)
        if context.get('developmental_history'):
            score += 5
        if context.get('family_context'):
            score += 5

        # Examples and specificity (10 points)
        if 'example' in raw_text:
            score += 5
        if len(raw_text) > 500:
            score += 5

        return min(100, score)

    async def generate_video_instructions(self, family_id: str, context: Dict):
        """Generate personalized video filming instructions based on interview."""

        # Use LLM to generate personalized instructions
        # (Implementation details omitted for brevity)
        # Save to Graphiti with flag video_instructions_generated=True
        pass

    async def _handle_urgent_flags(self, family_id: str, flags: List[str]):
        """Handle urgent safety concerns."""
        # Log and potentially notify administrators
        pass
```

### 3. ContextCardService

#### app/services/context_card_service.py

```python
from typing import Dict, List
from app.services.prerequisite_service import PrerequisiteService

class ContextCardService:
    def __init__(self):
        self.prerequisite_service = PrerequisiteService()

    async def generate_cards(
        self,
        family_id: str,
        family_context: Dict,
        completeness: int
    ) -> List[Dict]:
        """
        Generate 2-4 context cards dynamically based on current state.
        """

        cards = []

        # Get available and blocked actions
        available = await self.prerequisite_service.get_available_actions(family_id, family_context)

        # Priority 1: Time-sensitive items (NEW reports, meetings, etc.)
        if family_context.get("reports_ready") and not family_context.get("reports_viewed"):
            cards.append({
                "id": f"card_{len(cards)}",
                "title": "מדריך להורים מוכן!",
                "subtitle": "הממצאים והמלצות",
                "status": "new",
                "icon": "FileText",
                "action": "view_parent_report"
            })

        # Priority 2: Blocking prerequisites (must do to progress)
        if completeness < 80:
            cards.append({
                "id": f"card_{len(cards)}",
                "title": "מדברים על הילד/ה",
                "subtitle": f"התקדמנו {completeness}%",
                "status": "progress",
                "icon": "MessageCircle",
                "action": None
            })

        # Priority 3: Available actions
        if "upload_video" in available:
            videos_uploaded = family_context.get("videos_uploaded", 0)
            cards.append({
                "id": f"card_{len(cards)}",
                "title": "העלאת סרטון",
                "subtitle": f"{videos_uploaded}/3 הועלו",
                "status": "action",
                "icon": "Video",
                "action": "upload_video"
            })

        if "view_guidelines" in available:
            cards.append({
                "id": f"card_{len(cards)}",
                "title": "הנחיות צילום",
                "subtitle": "3 תרחישים מותאמים אישית",
                "status": "new",
                "icon": "FileVideo",
                "action": "view_guidelines"
            })

        # Priority 4: Always available actions
        if "journal" in available:
            entry_count = family_context.get("journal_entry_count", 0)
            cards.append({
                "id": f"card_{len(cards)}",
                "title": "יומן התקדמות",
                "subtitle": f"{entry_count} רשומות",
                "status": "action",
                "icon": "BookOpen",
                "action": "journal"
            })

        # Limit to max 4 cards
        return cards[:4]

    async def generate_suggestions(self, family_context: Dict) -> List[Dict]:
        """Generate contextual suggestions for lightbulb button."""

        suggestions = []

        # Based on current state, suggest helpful actions
        if family_context.get("interview_completeness", 0) < 80:
            suggestions.append({
                "icon": "HelpCircle",
                "text": "מה המטרה של השיחה?",
                "color": "bg-blue-500"
            })

        if family_context.get("videos_uploaded", 0) > 0:
            suggestions.append({
                "icon": "Info",
                "text": "איך עובד ניתוח הסרטונים?",
                "color": "bg-purple-500"
            })

        return suggestions
```

### 4. PrerequisiteService

#### app/services/prerequisite_service.py

```python
from typing import Dict, List, Tuple

class PrerequisiteService:
    """Check prerequisite dependencies for actions."""

    PREREQUISITES = {
        'generate_video_instructions': {
            'requires': ['interview_complete'],
            'data_needed': ['child_profile', 'concerns', 'age']
        },
        'upload_video': {
            'requires': ['video_instructions_generated']
        },
        'analyze_videos': {
            'requires': ['interview_complete', 'videos_uploaded'],
            'minimum_videos': 3
        },
        'view_report': {
            'requires': ['analysis_complete']
        },
        'consultation': {
            'requires': []  # Always available
        },
        'journal': {
            'requires': []  # Always available
        }
    }

    async def check_action(
        self,
        action: str,
        family_context: Dict
    ) -> Tuple[bool, List[str]]:
        """
        Check if action is possible.

        Returns:
            (feasible: bool, missing: List[str])
        """

        if action not in self.PREREQUISITES:
            return (False, [f"Unknown action: {action}"])

        prereqs = self.PREREQUISITES[action]
        missing = []

        for requirement in prereqs.get('requires', []):
            if requirement == 'interview_complete':
                if family_context.get('interview_completeness', 0) < 80:
                    missing.append('interview_complete')

            elif requirement == 'video_instructions_generated':
                if not family_context.get('video_instructions_generated'):
                    missing.append('video_instructions_generated')

            elif requirement == 'videos_uploaded':
                min_videos = prereqs.get('minimum_videos', 1)
                if family_context.get('videos_uploaded', 0) < min_videos:
                    missing.append(f'videos_uploaded (need {min_videos})')

            elif requirement == 'analysis_complete':
                if family_context.get('analysis_status') != 'complete':
                    missing.append('analysis_complete')

        return (len(missing) == 0, missing)

    async def get_available_actions(
        self,
        family_id: str,
        family_context: Dict
    ) -> List[str]:
        """Get list of currently available actions."""

        available = []

        for action in self.PREREQUISITES.keys():
            feasible, _ = await self.check_action(action, family_context)
            if feasible:
                available.append(action)

        return available

    async def handle_action_request(
        self,
        family_id: str,
        action: str,
        context: Dict
    ):
        """Handle user wanting to perform an action."""

        feasible, missing = await self.check_action(action, context)

        if not feasible:
            # Log blocked action attempt for analytics
            print(f"Action '{action}' blocked for {family_id}. Missing: {missing}")

        # The LLM will explain gracefully via conversation
```

---

## 🎥 Video Analysis Integration

### app/services/video_service.py

```python
import json
from typing import Dict
from datetime import datetime
from app.services.llm.factory import LLMFactory
from app.services.graphiti_service import GraphitiService
from app.config import settings

class VideoService:
    def __init__(self):
        # Use Gemini 2.5 Pro for video analysis (CRITICAL)
        self.llm = LLMFactory.create(
            provider="gemini",
            api_key=settings.GEMINI_API_KEY,
            model="gemini-2.5-pro"  # NOT Flash
        )
        self.graphiti = GraphitiService()

    async def analyze_video(
        self,
        family_id: str,
        video_path: str,
        video_id: str
    ) -> Dict:
        """
        Analyze video using Gemini 2.5 Pro with interview context.
        """

        # 1. Get interview summary from Graphiti
        family_context = await self.graphiti.get_family_context(family_id)
        interview_summary = self._build_interview_summary(family_context)

        # 2. Load video analysis prompt
        from app.prompts.video_analysis_prompt import VIDEO_ANALYSIS_PROMPT

        prompt = VIDEO_ANALYSIS_PROMPT.format(
            AGE=family_context.get("age", "unknown"),
            GENDER=family_context.get("gender", "unknown"),
            interview_summary_json=json.dumps(interview_summary, ensure_ascii=False, indent=2)
        )

        # 3. Analyze video with Gemini
        response = await self.llm.analyze_video(
            video_path=video_path,
            prompt=prompt,
            temperature=0.3  # Lower for clinical accuracy
        )

        # 4. Parse JSON response
        try:
            analysis_results = json.loads(response.content)
        except json.JSONDecodeError:
            # Handle markdown-wrapped JSON
            import re
            json_match = re.search(r'```json\n(.*?)\n```', response.content, re.DOTALL)
            if json_match:
                analysis_results = json.loads(json_match.group(1))
            else:
                raise ValueError("Could not parse video analysis JSON")

        # 5. Save to Graphiti
        await self.graphiti.add_episode(
            name=f"video_analysis_{video_id}_{datetime.now().isoformat()}",
            episode_body=json.dumps(analysis_results, ensure_ascii=False),
            source_description="Gemini video analysis with interview integration",
            reference_time=datetime.now(),
            group_id=f"family_{family_id}"
        )

        return {
            "analysis": analysis_results,
            "tokens_used": response.tokens_used,
            "model": response.model,
            "timestamp": datetime.now()
        }

    def _build_interview_summary(self, family_context: Dict) -> Dict:
        """Build structured interview summary for video analysis."""
        return {
            "child_name": family_context.get("child_name"),
            "age": family_context.get("age"),
            "gender": family_context.get("gender"),
            "difficulties_detailed": family_context.get("concern_details", []),
            "parent_concerns_summary": family_context.get("primary_concerns", [])
        }
```

---

Due to length limits, I'll continue in the next response with Authentication, Deployment, and Testing sections. Should I proceed?

