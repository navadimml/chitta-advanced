# Chitta Data Model v2: Child-Centric Architecture

## Overview

The child is the core entity. Users interact with Chitta about children they have access to.
This model separates:
- **Child data** (invariant, accumulates over time)
- **User sessions** (per-user interaction state, UI preferences)
- **Conversations** (contextual interactions between user and Chitta about a child)

## Entity Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              CHILD                                       │
│                     (The invariant core entity)                          │
├─────────────────────────────────────────────────────────────────────────┤
│  child_id: str (primary key)                                            │
│                                                                          │
│  PROFILE                                                                 │
│  ├── name: str                                                          │
│  ├── age: float                                                         │
│  ├── gender: str                                                        │
│  └── birth_date: date (optional, for age calculation)                   │
│                                                                          │
│  DEVELOPMENTAL DATA (extracted from all conversations)                   │
│  ├── primary_concerns: List[str]                                        │
│  ├── concern_details: str                                               │
│  ├── strengths: str                                                     │
│  ├── developmental_history: str                                         │
│  ├── family_context: str                                                │
│  ├── daily_routines: str                                                │
│  ├── parent_goals: str                                                  │
│  ├── urgent_flags: List[str]                                            │
│  └── filming_preference: str                                            │
│                                                                          │
│  ARTIFACTS (generated outputs about this child)                          │
│  └── artifacts: Dict[artifact_id, Artifact]                             │
│      ├── baseline_interview_summary                                     │
│      ├── baseline_video_guidelines                                      │
│      ├── baseline_parent_report                                         │
│      └── ...                                                            │
│                                                                          │
│  MEDIA                                                                   │
│  ├── videos: List[Video]                                                │
│  └── documents: List[Document] (future: uploaded PDFs, etc.)            │
│                                                                          │
│  JOURNAL                                                                 │
│  └── journal_entries: List[JournalEntry]                                │
│                                                                          │
│  TIMELINE (future: all events in child's journey)                        │
│  └── timeline_events: List[TimelineEvent]                               │
│                                                                          │
│  COMPLETENESS                                                            │
│  ├── data_completeness: float (0-1, how much we know)                   │
│  └── semantic_verification: Dict (LLM quality check)                    │
│                                                                          │
│  METADATA                                                                │
│  ├── created_at: datetime                                               │
│  └── updated_at: datetime                                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ accessed by
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          CHILD ACCESS                                    │
│                    (Who can see this child)                              │
├─────────────────────────────────────────────────────────────────────────┤
│  child_id: str (FK)                                                     │
│  user_id: str (FK)                                                      │
│  role: str ("parent", "clinician", "teacher", "specialist", "family")   │
│  permissions: List[str] (["view", "edit", "share", "delete"])           │
│  granted_at: datetime                                                   │
│  granted_by: str (user_id who shared)                                   │
│  expires_at: datetime (optional, for temporary access)                  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              USER                                        │
│                    (Anyone who uses Chitta)                              │
├─────────────────────────────────────────────────────────────────────────┤
│  user_id: str (primary key)                                             │
│                                                                          │
│  IDENTITY                                                                │
│  ├── email: str                                                         │
│  ├── name: str                                                          │
│  └── auth_provider: str (google, email, etc.)                           │
│                                                                          │
│  PREFERENCES (global, not per-child)                                     │
│  ├── language: str                                                      │
│  ├── notification_settings: Dict                                        │
│  └── theme: str                                                         │
│                                                                          │
│  METADATA                                                                │
│  ├── created_at: datetime                                               │
│  └── last_active: datetime                                              │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ has sessions
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          USER SESSION                                    │
│              (A user's interaction context for a child)                  │
├─────────────────────────────────────────────────────────────────────────┤
│  session_id: str (primary key)                                          │
│  user_id: str (FK)                                                      │
│  child_id: str (FK)                                                     │
│                                                                          │
│  CONVERSATION                                                            │
│  └── messages: List[Message]                                            │
│      ├── role: "user" | "assistant"                                     │
│      ├── content: str                                                   │
│      └── timestamp: datetime                                            │
│                                                                          │
│  UI STATE (per-user, per-child)                                          │
│  ├── active_cards: List[ActiveCard]                                     │
│  ├── dismissed_card_moments: Dict[moment_id, datetime]                  │
│  ├── current_view: str                                                  │
│  ├── expanded_sections: List[str]                                       │
│  └── previous_context_snapshot: Dict                                    │
│                                                                          │
│  MOMENT TRACKING                                                         │
│  └── last_triggered_moment: Dict                                        │
│                                                                          │
│  METADATA                                                                │
│  ├── created_at: datetime                                               │
│  ├── updated_at: datetime                                               │
│  └── last_message_at: datetime                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### 1. Child Data is Shared, Conversations are Personal

When Mom and Dad both use Chitta for their child Daniel:
- They see the **same** child profile, artifacts, videos, journal
- They have **separate** conversation histories with Chitta
- They have **separate** UI states (dismissed cards, etc.)

When a clinician views Daniel:
- They see the **same** child data (based on permissions)
- They have their **own** conversation with Chitta about Daniel
- Their UI state is separate from the parents'

### 2. Extracted Data Merges into Child

When any user talks to Chitta about a child, extracted information updates the **Child** entity:
- If Mom mentions Daniel's speech concerns, it goes to `child.developmental_data`
- If clinician adds observations, it enriches the same data
- The child's profile is the union of all knowledge from all conversations

### 3. Artifacts Belong to Child

Reports, guidelines, analysis - all belong to the child, not the user session.
Any authorized user can view artifacts for children they have access to.

### 4. UI State is Per-User-Per-Child

Active cards, dismissed moments, view preferences are stored in UserSession.
This allows:
- Mom dismisses "upload video" card → only dismissed for Mom
- Dad still sees the card
- Clinician has completely different card set based on their role

### 5. Simplified for Now (Pre-Production)

For now, we can simplify:
- `user_id` = device/browser ID or simple login
- `child_id` = what we currently call `family_id`
- Single "parent" role by default
- No complex permissions yet

## Migration from Current State

### Current → New Mapping

| Current | New Location |
|---------|--------------|
| `FamilyState.child` | `Child.profile` |
| `FamilyState.conversation` | `UserSession.messages` |
| `FamilyState.artifacts` | `Child.artifacts` |
| `FamilyState.videos_uploaded` | `Child.videos` |
| `FamilyState.journal_entries` | `Child.journal_entries` |
| `FamilyState.active_cards` | `UserSession.active_cards` |
| `FamilyState.dismissed_card_moments` | `UserSession.dismissed_card_moments` |
| `SessionState.extracted_data` | `Child.developmental_data` |
| `SessionState.completeness` | `Child.data_completeness` |
| `SessionState.conversation_history` | `UserSession.messages` |
| `SessionState.semantic_verification` | `Child.semantic_verification` |

### What Gets Consolidated

- `FamilyState` + `SessionState` → split into `Child` + `UserSession`
- No more sync issues because data lives in the right place
- Greeting derives from `Child` data (always available)
- UI state derives from `UserSession` (per-user)

## Implementation Phases

### Phase 1: Core Models (Now)
- Create `Child` model with all child data
- Create `UserSession` model with conversation + UI state
- Simple in-memory + file persistence

### Phase 2: Service Layer
- `ChildService` - CRUD for child data
- `SessionService` - manages user sessions
- Update conversation service to use new models

### Phase 3: Access Control (Future)
- Add `User` model with auth
- Add `ChildAccess` for permissions
- Multi-user support

## File Structure

```
backend/app/models/
├── child.py              # Child entity (the core)
├── user_session.py       # User's interaction session
├── user.py               # User entity (future)
├── child_access.py       # Access control (future)
├── artifact.py           # Keep as-is
├── active_card.py        # Keep as-is
└── __init__.py

backend/app/services/
├── child_service.py      # Manages child data
├── session_service.py    # Manages user sessions (refactored)
└── ...
```
