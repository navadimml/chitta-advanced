# Chitta Backend Architecture - FastAPI

**Version**: 1.0
**Tech Stack**: FastAPI + Python
**Last Updated**: 2024-11-04

---

## Overview

This document outlines the FastAPI-based backend architecture for Chitta, designed to replace the mock API service (`src/services/api.js`) with a production-ready Python backend.

---

## Technology Stack

### Core
- **Language**: Python 3.11+
- **Framework**: FastAPI 0.104+
- **ASGI Server**: Uvicorn
- **Database**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0+
- **Migrations**: Alembic
- **Validation**: Pydantic V2

### AI Integration
- **Anthropic SDK**: `anthropic` Python package
- **Model**: Claude 3.5 Sonnet (`claude-3-5-sonnet-20241022`)
- **Features**: Function calling, streaming responses

### File Storage
- **Primary**: AWS S3
- **Local Dev**: MinIO (S3-compatible)
- **Library**: `boto3`
- **Security**: Presigned URLs, encryption at rest

### Async Processing
- **Queue**: Celery with Redis broker
- **Tasks**: Video analysis, report generation, email notifications
- **Monitoring**: Flower (Celery monitoring)

### Caching & Sessions
- **Redis**: Session storage, caching, Celery broker
- **Library**: `redis-py`, `aioredis`

### Additional Libraries
- **Auth**: `python-jose[cryptography]`, `passlib[bcrypt]`
- **HTTP Client**: `httpx` (async)
- **Environment**: `python-dotenv`
- **Logging**: `structlog`
- **Testing**: `pytest`, `pytest-asyncio`
- **File Processing**: `python-multipart`, `Pillow`
- **PDF Generation**: `reportlab` or `weasyprint`

---

## Architecture Overview

```
┌─────────────────────────────────────┐
│     Frontend (React + Vite)         │
│         Port: 5173                  │
└──────────────┬──────────────────────┘
               │ HTTP/REST + CORS
┌──────────────▼──────────────────────┐
│       FastAPI Application            │
│         Port: 8000                   │
├──────────────────────────────────────┤
│      Middleware Stack                │
│  - CORS                              │
│  - Authentication (JWT)              │
│  - Request Validation (Pydantic)     │
│  - Error Handling                    │
│  - Rate Limiting                     │
│  - Logging                           │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│         API Routers                  │
│  /api/auth/*                         │
│  /api/sessions/*                     │
│  /api/conversations/*                │
│  /api/documents/*                    │
│  /api/videos/*                       │
│  /api/reports/*                      │
│  /api/experts/*                      │
│  /api/share/*                        │
│  /api/journal/*                      │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│       Service Layer                  │
│  - AuthService                       │
│  - SessionService                    │
│  - ConversationService               │
│  - DocumentService                   │
│  - VideoService                      │
│  - ReportService                     │
│  - ExpertService                     │
│  - ShareService                      │
└──────────┬──────────┬────────────────┘
           │          │
     ┌─────▼──┐  ┌───▼────┐
     │Database│  │ Claude │
     │ Layer  │  │  API   │
     └─────┬──┘  └────────┘
           │
┌──────────▼──────────────────────────┐
│     Data Access Layer                │
│  PostgreSQL + SQLAlchemy             │
│  Redis (Cache + Sessions)            │
│  S3/MinIO (File Storage)             │
│  Celery (Async Tasks)                │
└──────────────────────────────────────┘
```

---

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI application entry point
│   ├── config.py                    # Configuration & environment variables
│   ├── database.py                  # Database connection & session
│   ├── dependencies.py              # Common dependencies (auth, db session)
│   │
│   ├── models/                      # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── child.py
│   │   ├── session.py
│   │   ├── message.py
│   │   ├── document.py
│   │   ├── video.py
│   │   ├── report.py
│   │   ├── journal.py
│   │   ├── expert.py
│   │   └── share.py
│   │
│   ├── schemas/                     # Pydantic models (request/response)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── auth.py
│   │   ├── session.py
│   │   ├── message.py
│   │   ├── document.py
│   │   ├── video.py
│   │   ├── report.py
│   │   ├── journal.py
│   │   ├── expert.py
│   │   ├── master_state.py          # Master State Object schema
│   │   └── share.py
│   │
│   ├── routers/                     # API route handlers
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── sessions.py
│   │   ├── conversations.py
│   │   ├── documents.py
│   │   ├── videos.py
│   │   ├── reports.py
│   │   ├── experts.py
│   │   ├── share.py
│   │   └── journal.py
│   │
│   ├── services/                    # Business logic
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── session_service.py
│   │   ├── conversation_service.py  # Claude integration
│   │   ├── document_service.py
│   │   ├── video_service.py
│   │   ├── report_service.py
│   │   ├── expert_service.py
│   │   ├── share_service.py
│   │   ├── storage_service.py       # S3/MinIO
│   │   └── claude_service.py        # Claude API wrapper
│   │
│   ├── tasks/                       # Celery tasks
│   │   ├── __init__.py
│   │   ├── video_tasks.py           # Video processing
│   │   ├── report_tasks.py          # Report generation
│   │   └── email_tasks.py           # Email notifications
│   │
│   ├── core/                        # Core utilities
│   │   ├── __init__.py
│   │   ├── security.py              # JWT, password hashing
│   │   ├── logging.py               # Structured logging
│   │   ├── exceptions.py            # Custom exceptions
│   │   └── constants.py             # Constants, enums
│   │
│   └── middleware/                  # Custom middleware
│       ├── __init__.py
│       ├── error_handler.py
│       ├── logging_middleware.py
│       └── rate_limiter.py
│
├── alembic/                         # Database migrations
│   ├── versions/
│   └── env.py
│
├── tests/                           # Test suite
│   ├── unit/
│   ├── integration/
│   └── conftest.py
│
├── scripts/                         # Utility scripts
│   ├── seed_db.py
│   └── create_admin.py
│
├── requirements.txt                 # Python dependencies
├── requirements-dev.txt             # Development dependencies
├── .env.example                     # Environment template
├── alembic.ini                      # Alembic configuration
├── pytest.ini                       # Pytest configuration
├── Dockerfile                       # Docker image
├── docker-compose.yml               # Local development stack
└── README.md                        # Backend documentation
```

---

## Database Schema (SQLAlchemy Models)

### users
```python
class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(default=True)
    is_verified: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login: Mapped[Optional[datetime]]

    # Relationships
    children: Mapped[List["Child"]] = relationship(back_populates="user")
    sessions: Mapped[List["Session"]] = relationship(back_populates="user")
```

### children
```python
class Child(Base):
    __tablename__ = "children"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(255))
    date_of_birth: Mapped[date]
    age_months: Mapped[int]  # Auto-calculated
    gender: Mapped[Optional[str]] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="children")
    sessions: Mapped[List["Session"]] = relationship(back_populates="child")
```

### sessions
```python
class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    child_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("children.id"))
    journey_stage: Mapped[str] = mapped_column(String(50))  # enum
    master_state: Mapped[dict] = mapped_column(JSON)  # JSONB in PostgreSQL
    is_active: Mapped[bool] = mapped_column(default=True)
    started_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    last_activity: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]]

    # Relationships
    user: Mapped["User"] = relationship(back_populates="sessions")
    child: Mapped["Child"] = relationship(back_populates="sessions")
    messages: Mapped[List["Message"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    documents: Mapped[List["Document"]] = relationship(back_populates="session")
    videos: Mapped[List["Video"]] = relationship(back_populates="session")
```

### messages
```python
class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sessions.id"))
    sender: Mapped[str] = mapped_column(String(20))  # 'user' or 'chitta'
    content: Mapped[str] = mapped_column(Text)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)

    # Relationships
    session: Mapped["Session"] = relationship(back_populates="messages")
```

### documents
```python
class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sessions.id"))
    type: Mapped[str] = mapped_column(String(50))  # 'diagnosis', 'report', 'medical'
    filename: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str] = mapped_column(String(500))  # S3 key
    mime_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int]
    analysis_result: Mapped[Optional[dict]] = mapped_column(JSON)
    uploaded_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    analyzed_at: Mapped[Optional[datetime]]

    # Relationships
    session: Mapped["Session"] = relationship(back_populates="documents")
```

### videos
```python
class Video(Base):
    __tablename__ = "videos"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sessions.id"))
    scenario_type: Mapped[str] = mapped_column(String(50))  # 'free_play', 'meal_time', 'focused_activity'
    filename: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str] = mapped_column(String(500))
    thumbnail_key: Mapped[Optional[str]] = mapped_column(String(500))
    duration_seconds: Mapped[Optional[int]]
    size_bytes: Mapped[int]
    status: Mapped[str] = mapped_column(String(20))  # 'uploaded', 'processing', 'analyzed', 'error'
    analysis_result: Mapped[Optional[dict]] = mapped_column(JSON)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    uploaded_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    analyzed_at: Mapped[Optional[datetime]]

    # Relationships
    session: Mapped["Session"] = relationship(back_populates="videos")
```

### reports
```python
class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sessions.id"))
    variant: Mapped[str] = mapped_column(String(20))  # 'parent', 'professional'
    content: Mapped[dict] = mapped_column(JSON)
    pdf_storage_key: Mapped[Optional[str]] = mapped_column(String(500))
    generated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    viewed_at: Mapped[Optional[datetime]]
    shared_with: Mapped[Optional[list]] = mapped_column(JSON)  # Array of share info

    # Relationships
    session: Mapped["Session"] = relationship()
```

### journal_entries
```python
class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sessions.id"))
    date: Mapped[date]
    content: Mapped[str] = mapped_column(Text)
    tags: Mapped[Optional[list]] = mapped_column(JSON)  # Array of strings
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    session: Mapped["Session"] = relationship()
```

### experts
```python
class Expert(Base):
    __tablename__ = "experts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(255))
    specialties: Mapped[list] = mapped_column(JSON)  # Array of strings
    location: Mapped[str] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(100), index=True)
    latitude: Mapped[Optional[float]]
    longitude: Mapped[Optional[float]]
    rating: Mapped[Optional[float]]
    review_count: Mapped[int] = mapped_column(default=0)
    bio: Mapped[Optional[str]] = mapped_column(Text)
    contact_info: Mapped[dict] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(default=True)
    verified: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    matches: Mapped[List["ExpertMatch"]] = relationship(back_populates="expert")
```

### expert_matches
```python
class ExpertMatch(Base):
    __tablename__ = "expert_matches"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sessions.id"))
    expert_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("experts.id"))
    match_score: Mapped[float]
    reasons: Mapped[list] = mapped_column(JSON)  # Array of strings
    status: Mapped[str] = mapped_column(String(20))  # 'suggested', 'contacted', 'scheduled', 'completed'
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    session: Mapped["Session"] = relationship()
    expert: Mapped["Expert"] = relationship(back_populates="matches")
```

### share_links
```python
class ShareLink(Base):
    __tablename__ = "share_links"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sessions.id"))
    expert_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("experts.id"))
    share_token: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    permissions: Mapped[dict] = mapped_column(JSON)  # What can be accessed
    expires_at: Mapped[datetime]
    accessed_at: Mapped[Optional[datetime]]
    access_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    revoked_at: Mapped[Optional[datetime]]

    # Relationships
    session: Mapped["Session"] = relationship()
    expert: Mapped[Optional["Expert"]] = relationship()
```

---

## Pydantic Schemas (Request/Response)

### Master State Schema
```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum

class JourneyStage(str, Enum):
    INTERVIEW = "interview"
    CONSULTATION = "consultation"
    DOCUMENT_UPLOAD = "document_upload"
    VIDEO_INSTRUCTIONS = "video_instructions"
    VIDEO_UPLOAD = "video_upload"
    ANALYSIS = "analysis"
    REPORT_READY = "report_ready"
    EXPERT_SEARCH = "expert_search"
    MEETING_PREP = "meeting_prep"
    SHARING = "sharing"

class ChildInfo(BaseModel):
    name: str
    age: float

class Progress(BaseModel):
    interview: int = Field(ge=0, le=100)
    videos: int = Field(ge=0, le=100)
    documents: Optional[int] = Field(default=0, ge=0, le=100)
    analysis: Optional[int] = Field(default=0, ge=0, le=100)

class Artifact(BaseModel):
    type: str
    count: Optional[int] = None
    total: Optional[int] = None
    status: Optional[str] = None
    viewed: Optional[List[str]] = []
    metadata: Optional[Dict[str, Any]] = {}

class MasterState(BaseModel):
    journey_stage: JourneyStage
    child: ChildInfo
    progress: Progress
    active_artifacts: List[Artifact] = []
    completed_milestones: List[str] = []
    metadata: Optional[Dict[str, Any]] = {}
```

---

## API Endpoints (FastAPI Routes)

### Authentication (`/api/auth`)
```python
@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register new user"""

@router.post("/login", response_model=TokenResponse)
async def login(credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login and get JWT token"""

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """Refresh access token"""

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout (invalidate token)"""

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
```

### Sessions (`/api/sessions`)
```python
@router.post("/", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new session for a child"""

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get session details including master state"""

@router.get("/", response_model=List[SessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    child_id: Optional[UUID] = None,
    is_active: bool = True
):
    """List user's sessions"""

@router.patch("/{session_id}/state", response_model=SessionResponse)
async def update_session_state(
    session_id: UUID,
    state_update: MasterStateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update session master state"""
```

### Conversations (`/api/conversations`)
```python
@router.post("/message", response_model=ConversationResponse)
async def send_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send message to Chitta and get response.
    This integrates with Claude API and updates master state.
    """

@router.get("/{session_id}/history", response_model=List[MessageResponse])
async def get_conversation_history(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    """Get conversation history for a session"""

@router.post("/action", response_model=ActionResponse)
async def trigger_action(
    action_data: ActionTrigger,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger a deep view or action (e.g., open upload modal)"""
```

### Documents (`/api/documents`)
```python
@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    session_id: UUID = Form(...),
    file: UploadFile = File(...),
    document_type: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service)
):
    """Upload document (PDF, image, Word) and queue for analysis"""

@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List documents for a session"""

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get document details"""

@router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service)
):
    """Get presigned URL for document download"""

@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service)
):
    """Delete document"""
```

### Videos (`/api/videos`)
```python
@router.post("/upload", response_model=VideoResponse)
async def upload_video(
    session_id: UUID = Form(...),
    scenario_type: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service)
):
    """Upload video and queue for processing"""

@router.get("/", response_model=List[VideoResponse])
async def list_videos(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List videos for a session"""

@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get video details"""

@router.get("/{video_id}/stream")
async def stream_video(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service)
):
    """Get presigned URL for video streaming"""

@router.delete("/{video_id}", status_code=204)
async def delete_video(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service)
):
    """Delete video"""
```

### Reports (`/api/reports`)
```python
@router.get("/", response_model=List[ReportResponse])
async def list_reports(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List reports for a session"""

@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get report details"""

@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    report_data: ReportGenerate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger report generation (async task)"""

@router.get("/{report_id}/pdf")
async def download_report_pdf(
    report_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service)
):
    """Download report as PDF"""
```

---

## Claude Integration

### Service Implementation

```python
# app/services/claude_service.py
from anthropic import AsyncAnthropic
from app.core.config import settings
from app.schemas.master_state import MasterState

class ClaudeService:
    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL

    async def send_message(
        self,
        conversation_history: List[Dict],
        master_state: MasterState,
        child_info: Dict,
        tools: List[Dict]
    ) -> Dict:
        """
        Send message to Claude with full context and function calling.

        Returns:
            {
                "message": str,
                "function_calls": List[Dict],
                "updated_state": Optional[MasterState]
            }
        """

        system_prompt = self._build_system_prompt(master_state, child_info)

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_prompt,
            messages=conversation_history,
            tools=tools
        )

        return self._process_response(response)

    def _build_system_prompt(self, master_state: MasterState, child_info: Dict) -> str:
        """Build comprehensive system prompt with context"""
        return f"""
You are Chitta, an empathetic AI assistant specialized in child development.

CURRENT CONTEXT:
- Child: {child_info['name']}, Age: {child_info['age']} years
- Journey Stage: {master_state.journey_stage}
- Progress: Interview {master_state.progress.interview}%, Videos {master_state.progress.videos}%
- Completed Milestones: {', '.join(master_state.completed_milestones)}

YOUR ROLE:
- Provide empathetic, supportive guidance to parents
- Guide them through the journey stages
- Use function calling to update state and trigger actions
- Speak in Hebrew when appropriate
- Never provide medical diagnosis

AVAILABLE FUNCTIONS:
You have access to functions to update the journey state, trigger deep views, and more.
"""

    def _get_function_definitions(self) -> List[Dict]:
        """Define functions available to Claude"""
        return [
            {
                "name": "update_journey_stage",
                "description": "Move to the next stage of the journey",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "new_stage": {
                            "type": "string",
                            "enum": ["interview", "consultation", "video_upload", ...]
                        },
                        "reason": {"type": "string"}
                    },
                    "required": ["new_stage"]
                }
            },
            {
                "name": "add_context_card",
                "description": "Add a card to the contextual surface",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "icon": {"type": "string"},
                        "title": {"type": "string"},
                        "subtitle": {"type": "string"},
                        "status": {"type": "string"},
                        "action": {"type": "string"}
                    },
                    "required": ["icon", "title", "subtitle", "status"]
                }
            },
            {
                "name": "trigger_deep_view",
                "description": "Open a specific deep view modal",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "view_name": {
                            "type": "string",
                            "enum": ["uploadDoc", "viewDocs", "uploadVideo", ...]
                        }
                    },
                    "required": ["view_name"]
                }
            },
            {
                "name": "update_progress",
                "description": "Update progress percentage",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["interview", "videos", "documents", "analysis"]
                        },
                        "percentage": {"type": "integer", "minimum": 0, "maximum": 100}
                    },
                    "required": ["type", "percentage"]
                }
            },
            {
                "name": "add_milestone",
                "description": "Mark a milestone as completed",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "milestone": {"type": "string"}
                    },
                    "required": ["milestone"]
                }
            }
        ]
```

---

## Environment Variables

```env
# App Configuration
APP_NAME=Chitta Backend
APP_VERSION=1.0.0
DEBUG=True
ENVIRONMENT=development
HOST=0.0.0.0
PORT=8000

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:5173

# Database
DATABASE_URL=postgresql+asyncpg://chitta:chitta_password@localhost:5432/chitta_db

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# JWT Authentication
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# Anthropic API
ANTHROPIC_API_KEY=sk-ant-xxxxx
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_MAX_TOKENS=4096

# File Storage (S3 or MinIO)
USE_MINIO=True
S3_BUCKET=chitta-files
S3_REGION=us-east-1

# AWS S3 (if USE_MINIO=False)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# MinIO (if USE_MINIO=True)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=False

# File Upload Limits
MAX_VIDEO_SIZE_MB=500
MAX_DOCUMENT_SIZE_MB=10
ALLOWED_VIDEO_EXTENSIONS=.mp4,.mov,.avi,.mkv
ALLOWED_DOCUMENT_EXTENSIONS=.pdf,.doc,.docx,.jpg,.jpeg,.png

# Celery
CELERY_TASK_ALWAYS_EAGER=False  # Set to True for synchronous testing

# Logging
LOG_LEVEL=DEBUG
LOG_FORMAT=json

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=10
```

---

## Development Setup

### 1. Clone and Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Environment
```bash
cp .env.example .env
# Edit .env with your values
```

### 3. Start Services (Docker)
```bash
docker-compose up -d
# Starts: PostgreSQL, Redis, MinIO
```

### 4. Database Migrations
```bash
alembic upgrade head
```

### 5. Seed Database (Optional)
```bash
python scripts/seed_db.py
```

### 6. Run Development Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Run Celery Worker
```bash
celery -A app.tasks.celery_app worker --loglevel=info
```

### 8. Test API
```bash
# Visit: http://localhost:8000/docs (Swagger UI)
# Or: http://localhost:8000/redoc (ReDoc)
```

---

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_auth.py

# Run integration tests
pytest tests/integration/
```

---

## Deployment

### Docker Production Build
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose (Production)
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env.production
    depends_on:
      - db
      - redis

  worker:
    build: .
    command: celery -A app.tasks.celery_app worker --loglevel=info
    env_file:
      - .env.production
    depends_on:
      - db
      - redis

  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
```

---

## Monitoring & Logging

### Structured Logging
```python
import structlog

logger = structlog.get_logger()

logger.info("user_registered", user_id=user.id, email=user.email)
logger.error("video_processing_failed", video_id=video.id, error=str(e))
```

### Metrics (Optional: Prometheus)
- Request latency
- Error rates
- Claude API usage
- File storage usage
- Active users

---

## Security Checklist

- ✅ JWT authentication
- ✅ Password hashing (bcrypt)
- ✅ HTTPS/TLS in production
- ✅ CORS properly configured
- ✅ Rate limiting
- ✅ Input validation (Pydantic)
- ✅ SQL injection protection (SQLAlchemy ORM)
- ✅ File upload validation
- ✅ Presigned URLs for file access
- ✅ Environment variables for secrets

---

## Next Steps

1. ✅ Review this architecture document
2. Create project structure
3. Implement database models
4. Implement authentication
5. Implement core API endpoints
6. Integrate Claude API
7. Implement file upload/storage
8. Implement async video processing
9. Create report generation
10. Testing
11. Deploy to staging
12. Production deployment

---

**End of FastAPI Backend Architecture Document**
