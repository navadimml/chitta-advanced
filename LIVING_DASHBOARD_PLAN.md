# Living Dashboard Implementation Plan

## Executive Summary

Transform Chitta from a "chat with artifacts" to a "child's development home" with:

1. **Card Lifecycle Decoupling** - Separate card creation (events) from display (state)
2. **Daniel's Space** - Persistent, slot-based artifact access from header
3. **Living Documents** - Threaded conversations embedded in artifacts

---

## Phase 1: Card Lifecycle Decoupling

### Problem
Cards are re-evaluated every message, causing:
- Potential flicker
- No persistence after dismissal
- Progress cards recreated instead of updated

### Solution
Separate creation triggers from display state.

### 1.1 New Model: ActiveCard

**File:** `backend/app/models/active_card.py`

```python
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

class CardDisplayMode(str, Enum):
    FLOATING = "floating"      # Above chat input
    TOAST = "toast"            # Brief notification
    DRAWER_ITEM = "drawer_item" # In artifact drawer (future)

class ActiveCard(BaseModel):
    """Runtime state of a card instance."""
    card_id: str
    instance_id: str  # Unique: card_id + uuid

    # Lifecycle
    created_at: datetime
    created_by_moment: Optional[str] = None
    dismissed: bool = False
    dismissed_at: Optional[datetime] = None

    # Display
    display_mode: CardDisplayMode = CardDisplayMode.FLOATING
    priority: int = 50

    # Content
    content: Dict[str, Any] = {}

    # Dynamic updates
    dynamic_fields: List[str] = []

    # Dismissal rules
    dismiss_when: Optional[Dict[str, Any]] = None
    auto_dismiss_seconds: Optional[int] = None
    dismiss_on_action: Optional[str] = None
```

### 1.2 Update FamilyState

**File:** `backend/app/models/family_state.py`

Add:
```python
from app.models.active_card import ActiveCard

class FamilyState(BaseModel):
    # ... existing fields ...

    # Card lifecycle state
    active_cards: List[ActiveCard] = []
    dismissed_card_moments: Dict[str, datetime] = {}  # Prevent re-trigger

    # Context snapshot for transition detection
    previous_context_snapshot: Optional[Dict[str, Any]] = None
```

### 1.3 New Service: CardLifecycleService

**File:** `backend/app/services/card_lifecycle_service.py`

Key methods:
- `process_transitions(family_state, prev_context, curr_context)` - Create cards on FALSE→TRUE
- `update_active_cards(family_state, context)` - Update content, check dismissals
- `dismiss_card(family_state, card_id, by_action)` - Manual dismissal
- `get_visible_cards(family_state, display_mode)` - Get cards for rendering

### 1.4 Update workflow.yaml Schema

Add lifecycle configuration to card definitions:

```yaml
moments:
  guidelines_ready:
    when:
      artifacts.baseline_video_guidelines.status: "ready"
    card:
      card_id: "guidelines_ready"
      priority: 90

      lifecycle:
        trigger: transition  # Only on state change
        dismiss_when:
          artifacts.baseline_video_guidelines.viewed: true
        dismiss_on_action: "view_guidelines"
        prevent_re_trigger: true

      content:
        title: "ההנחיות מוכנות! 🎬"
        body: "הכנו לך הנחיות צילום מותאמות אישית"
        dynamic:
          # Fields to update without recreating card
          progress: "artifacts.baseline_video_guidelines.progress"
```

### 1.5 Integration Points

**Update:** `backend/app/services/lifecycle_manager.py`
- Add CardLifecycleService
- Call `process_transitions()` in `process_lifecycle_events()`
- Store context snapshot for next comparison

**Update:** `backend/app/api/routes.py`
- Return `active_cards` in conversation response instead of re-evaluating

**Update:** Frontend `App.jsx`
- Receive cards from API, don't compute locally
- Handle card dismissal actions

### 1.6 Tasks

- [ ] Create `active_card.py` model
- [ ] Update `family_state.py` with card fields
- [ ] Create `card_lifecycle_service.py`
- [ ] Update `workflow.yaml` with lifecycle schema for existing cards
- [ ] Update `lifecycle_manager.py` integration
- [ ] Update API response to include active_cards
- [ ] Update frontend to use API-provided cards
- [ ] Test card creation, updates, and dismissal

---

## Phase 2: Daniel's Space (Artifact Slots)

### Problem
Artifacts are buried behind chat. Users can't quickly access "their stuff."

### Solution
Header shows child's space with slot-based artifact access.

### 2.1 Artifact Slot Configuration

**Update:** `backend/config/workflows/artifacts.yaml`

Add slot configuration to each artifact:

```yaml
artifacts:
  baseline_parent_report:
    name: "דוח הורים"
    type: report

    slot:
      slot_id: "current_report"
      slot_name: "הדוח הנוכחי"
      icon: "📄"
      replaces_previous: true
      keep_history: true
      preview_field: "summary"
      primary_action: "view_report"

  updated_parent_report:
    name: "דוח מעודכן"
    type: report

    slot:
      slot_id: "current_report"  # Same slot - replaces
      replaces_previous: true
      keep_history: true

  baseline_video_guidelines:
    name: "הנחיות צילום"
    type: guidelines

    slot:
      slot_id: "filming_guidelines"
      slot_name: "הנחיות צילום"
      icon: "🎬"
      replaces_previous: true
      preview_field: "focus_areas"
      primary_action: "view_guidelines"

  behavioral_videos:
    name: "סרטונים"
    type: video

    slot:
      slot_id: "videos"
      slot_name: "הסרטונים"
      icon: "📹"
      is_collection: true
      collection_view: "videos_list"
      primary_action: "view_videos"
      secondary_action: "upload_video"

  journal_entries:
    name: "יומן"
    type: journal

    slot:
      slot_id: "journal"
      slot_name: "היומן"
      icon: "📝"
      is_collection: true
      collection_view: "journal_list"
      primary_action: "view_journal"
      secondary_action: "add_journal_entry"

# Slot display order
slot_order:
  - current_report
  - filming_guidelines
  - videos
  - journal
```

### 2.2 New Model: ArtifactSlot

**File:** `backend/app/models/artifact_slot.py`

```python
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

class SlotItem(BaseModel):
    """An artifact instance in a slot."""
    artifact_id: str
    artifact_type: str
    version: int = 1
    created_at: datetime
    status: str
    preview: Optional[str] = None

class ArtifactSlot(BaseModel):
    """A slot in Daniel's Space."""
    slot_id: str
    slot_name: str
    icon: str

    # Current item (or collection summary)
    current: Optional[SlotItem] = None

    # For collections
    is_collection: bool = False
    item_count: int = 0
    latest_item: Optional[SlotItem] = None

    # History (for versioned artifacts)
    history: List[SlotItem] = []

    # Actions
    primary_action: Optional[str] = None
    secondary_action: Optional[str] = None

    # State
    has_content: bool = False
    is_generating: bool = False
```

### 2.3 New Service: ChildSpaceService

**File:** `backend/app/services/child_space_service.py`

```python
class ChildSpaceService:
    """Manages Daniel's Space - the artifact slot system."""

    def get_space_summary(self, family_state: FamilyState) -> Dict[str, ArtifactSlot]:
        """Get all slots with current state for header display."""
        pass

    def get_slot_detail(self, family_state: FamilyState, slot_id: str) -> ArtifactSlot:
        """Get detailed slot info including history."""
        pass

    def get_slot_for_artifact(self, artifact_id: str) -> Optional[str]:
        """Which slot does this artifact belong to?"""
        pass
```

### 2.4 API Endpoints

**File:** `backend/app/api/routes.py`

```python
@router.get("/family/{family_id}/space")
async def get_child_space(family_id: str):
    """Get Daniel's Space - all artifact slots."""
    pass

@router.get("/family/{family_id}/space/{slot_id}")
async def get_slot_detail(family_id: str, slot_id: str):
    """Get slot detail with history."""
    pass

@router.get("/family/{family_id}/space/{slot_id}/history")
async def get_slot_history(family_id: str, slot_id: str):
    """Get version history for a slot."""
    pass
```

### 2.5 Frontend Components

**File:** `src/components/ChildSpaceHeader.jsx`
- Shows child name + artifact pills
- Tap to expand full space

**File:** `src/components/ChildSpace.jsx`
- Full-screen artifact grid
- Slot cards with status, preview, actions

**File:** `src/components/SlotCard.jsx`
- Individual slot display
- Handles both single artifacts and collections

### 2.6 Tasks

- [ ] Add slot configuration to `artifacts.yaml`
- [ ] Create `artifact_slot.py` model
- [ ] Create `child_space_service.py`
- [ ] Add space API endpoints
- [ ] Update `artifact_manager.py` to load slot config
- [ ] Create `ChildSpaceHeader.jsx` component
- [ ] Create `ChildSpace.jsx` full view
- [ ] Create `SlotCard.jsx` component
- [ ] Integrate header into main app layout
- [ ] Test slot population and navigation

---

## Phase 3: Living Documents (Threaded Conversations)

### Problem
Conversations about artifacts are lost in chat. Users lose context when asking questions.

### Solution
Embed threaded conversations directly in artifacts, attached to sections.

### 3.1 New Model: ArtifactThread

**File:** `backend/app/models/artifact_thread.py`

```python
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ThreadMessage(BaseModel):
    """A message in an artifact thread."""
    message_id: str
    role: str  # "user" or "assistant"
    content: str
    created_at: datetime

class ArtifactThread(BaseModel):
    """A conversation thread attached to an artifact section."""
    thread_id: str
    family_id: str
    artifact_id: str

    # What this thread is about
    section_id: str  # e.g., "motor_development" or timestamp "0:43"
    section_text: Optional[str] = None  # The text being discussed

    # The conversation
    messages: List[ThreadMessage] = []

    # Metadata
    created_at: datetime
    updated_at: datetime
    is_resolved: bool = False  # User can mark as "got it"
```

### 3.2 Artifact Section Structure

Artifacts need to be structured with identifiable sections.

**File:** `backend/app/models/structured_artifact.py`

```python
class ArtifactSection(BaseModel):
    """A section within an artifact that can have threads."""
    section_id: str
    section_type: str  # "heading", "paragraph", "observation", "timestamp"
    title: Optional[str] = None
    content: str

    # For video artifacts
    timestamp_start: Optional[float] = None
    timestamp_end: Optional[float] = None

    # Thread summary
    thread_count: int = 0
    has_unread: bool = False

class StructuredArtifact(BaseModel):
    """An artifact with sections for threading."""
    artifact_id: str
    artifact_type: str
    title: str

    sections: List[ArtifactSection] = []

    # Overall thread summary
    total_threads: int = 0
    unread_threads: int = 0
```

### 3.3 Artifact Generation Update

When generating artifacts, structure them with sections.

**Update:** `backend/app/services/artifact_generation_service.py`

Reports should be generated with section markers:

```python
async def generate_parent_report(self, ...) -> StructuredArtifact:
    """Generate report with identifiable sections."""
    # LLM generates report with section structure
    # Each section gets a section_id
    pass
```

**Update prompts** to request structured output:

```
Generate the report with the following sections, each clearly marked:
- motor_development: Motor skills assessment
- communication: Speech and language
- social_emotional: Social and emotional development
- recommendations: Recommendations for parents
```

### 3.4 Thread Service

**File:** `backend/app/services/artifact_thread_service.py`

```python
class ArtifactThreadService:
    """Manages threaded conversations on artifacts."""

    async def create_thread(
        self,
        family_id: str,
        artifact_id: str,
        section_id: str,
        initial_question: str
    ) -> ArtifactThread:
        """Start a new thread on an artifact section."""
        pass

    async def add_message_to_thread(
        self,
        thread_id: str,
        role: str,
        content: str
    ) -> ThreadMessage:
        """Add a message to existing thread."""
        pass

    async def get_threads_for_artifact(
        self,
        artifact_id: str
    ) -> List[ArtifactThread]:
        """Get all threads for an artifact."""
        pass

    async def get_thread_context(
        self,
        thread_id: str
    ) -> Dict[str, Any]:
        """Get context for LLM when responding in a thread."""
        # Returns: artifact content, section text, thread history
        pass

    async def generate_thread_response(
        self,
        thread_id: str,
        user_message: str
    ) -> str:
        """Generate Chitta's response in a thread context."""
        # Uses section context + thread history
        pass
```

### 3.5 API Endpoints

**File:** `backend/app/api/routes.py`

```python
@router.get("/artifact/{artifact_id}/structured")
async def get_structured_artifact(artifact_id: str):
    """Get artifact with sections and thread counts."""
    pass

@router.get("/artifact/{artifact_id}/threads")
async def get_artifact_threads(artifact_id: str):
    """Get all threads for an artifact."""
    pass

@router.post("/artifact/{artifact_id}/section/{section_id}/thread")
async def create_thread(
    artifact_id: str,
    section_id: str,
    body: CreateThreadRequest
):
    """Start a new thread on a section."""
    pass

@router.post("/thread/{thread_id}/message")
async def add_thread_message(
    thread_id: str,
    body: ThreadMessageRequest
):
    """Add message to thread and get AI response."""
    pass
```

### 3.6 Storage

**File:** `backend/app/services/thread_storage.py`

Threads stored alongside artifacts:
```
sessions/{session_id}/
  artifacts/
    parent_report.json          # The artifact
    parent_report_threads.json  # All threads for this artifact
```

Or in a dedicated threads collection if using a database.

### 3.7 Frontend Components

**File:** `src/components/LivingDocument.jsx`
- Renders structured artifact with sections
- Shows thread indicators on each section
- Handles thread expansion/collapse

**File:** `src/components/ArtifactSection.jsx`
- Single section with thread button
- Inline thread display when expanded

**File:** `src/components/SectionThread.jsx`
- Thread conversation UI
- Input for new messages
- Collapse/expand

**File:** `src/components/ThreadInput.jsx`
- Contextual input bar
- Shows "Ask about this section..."
- Voice input support

### 3.8 Deep View Updates

**Update:** `src/components/deepviews/`

All artifact deep views should use `LivingDocument`:

```jsx
// ReportView.jsx
const ReportView = ({ artifactId }) => {
  const { artifact, threads } = useStructuredArtifact(artifactId);

  return (
    <LivingDocument
      artifact={artifact}
      threads={threads}
      onCreateThread={handleCreateThread}
      onAddMessage={handleAddMessage}
    />
  );
};
```

### 3.9 Thread Context for LLM

When user asks in a thread, the LLM prompt includes:

```
You are answering a question about a specific section of Daniel's development report.

SECTION BEING DISCUSSED:
---
{section_title}
{section_content}
---

PREVIOUS MESSAGES IN THIS THREAD:
{thread_history}

USER'S QUESTION:
{user_message}

Answer specifically about this section. Be concise and helpful.
The parent is trying to understand their child's development.
```

### 3.10 Tasks

- [ ] Create `artifact_thread.py` model
- [ ] Create `structured_artifact.py` model
- [ ] Create `artifact_thread_service.py`
- [ ] Create `thread_storage.py`
- [ ] Add thread API endpoints
- [ ] Update artifact generation to create sections
- [ ] Update artifact generation prompts for structure
- [ ] Create `LivingDocument.jsx` component
- [ ] Create `ArtifactSection.jsx` component
- [ ] Create `SectionThread.jsx` component
- [ ] Create `ThreadInput.jsx` component
- [ ] Update existing deep views to use LivingDocument
- [ ] Test thread creation and conversation
- [ ] Test thread persistence and reload

---

## Implementation Order

### Week 1: Phase 1 - Card Lifecycle
1. Models (active_card, family_state updates)
2. CardLifecycleService
3. workflow.yaml schema updates
4. Backend integration
5. API updates
6. Frontend updates
7. Testing

### Week 2: Phase 2 - Daniel's Space
1. Slot configuration in artifacts.yaml
2. Models (artifact_slot)
3. ChildSpaceService
4. API endpoints
5. Frontend header component
6. Frontend space view
7. Testing

### Week 3: Phase 3 - Living Documents
1. Models (artifact_thread, structured_artifact)
2. ArtifactThreadService
3. Storage layer
4. API endpoints
5. Update artifact generation
6. Frontend LivingDocument components
7. Update deep views
8. Testing

### Week 4: Integration & Polish
1. End-to-end testing
2. Edge cases and error handling
3. Performance optimization
4. UI polish
5. Documentation

---

## Files to Create

### Backend
```
backend/app/models/
  active_card.py           # Phase 1
  artifact_slot.py         # Phase 2
  artifact_thread.py       # Phase 3
  structured_artifact.py   # Phase 3

backend/app/services/
  card_lifecycle_service.py    # Phase 1
  child_space_service.py       # Phase 2
  artifact_thread_service.py   # Phase 3
  thread_storage.py            # Phase 3
```

### Frontend
```
src/components/
  ChildSpaceHeader.jsx     # Phase 2
  ChildSpace.jsx           # Phase 2
  SlotCard.jsx             # Phase 2
  LivingDocument.jsx       # Phase 3
  ArtifactSection.jsx      # Phase 3
  SectionThread.jsx        # Phase 3
  ThreadInput.jsx          # Phase 3
```

### Config Updates
```
backend/config/workflows/
  workflow.yaml            # Phase 1: Add lifecycle to cards
  artifacts.yaml           # Phase 2: Add slot configuration
```

---

## Success Criteria

### Phase 1
- [ ] Cards persist after creation
- [ ] Cards don't flicker on re-evaluation
- [ ] Progress cards update content without recreation
- [ ] Dismissed cards don't reappear

### Phase 2
- [ ] Header shows artifact pills
- [ ] Tap header opens Daniel's Space
- [ ] Slots show current artifact or collection summary
- [ ] Version history accessible for versioned artifacts
- [ ] One tap to open any artifact

### Phase 3
- [ ] Can ask questions about specific sections
- [ ] Threads persist and show on reload
- [ ] Thread context improves AI answers
- [ ] Collapsed threads show count indicator
- [ ] Works for reports, guidelines, and video analysis

---

## Risk Mitigation

### Complexity Risk
- Start with Phase 1 (isolated change)
- Each phase is independently valuable
- Can ship phases separately

### Data Migration
- New fields are optional with defaults
- Existing artifacts work without sections (show as single section)
- Threads are additive, don't modify artifacts

### Performance
- Thread loading is lazy (on artifact open)
- Section structure is cached
- Card state is part of session, not recalculated

---

*Created: November 2025*
*Status: Ready for Implementation*
