# Chitta Project - Complete Documentation Summary

**Last Updated**: 2024-11-04
**Status**: Frontend Complete, Backend In Development

---

## Executive Summary

Chitta is an AI-powered child development tracking application that helps parents understand their child's developmental journey through conversational AI, video analysis, and expert matching.

**Current State**:
- ✅ Frontend: **COMPLETE** - React app with 16 components, 12 scenarios
- ⏳ Backend: **TO BE IMPLEMENTED** - FastAPI-based backend needed

---

## Document Status Matrix

| Document | Status | Purpose | Notes |
|----------|--------|---------|-------|
| `README.md` | ✅ CURRENT | Project overview | General introduction |
| `ARCHITECTURE.md` | ✅ CURRENT | Frontend architecture patterns | Dumb components, state management |
| `COMPLETE.md` | ✅ CURRENT | Frontend completion summary | All 26 frontend files listed as done |
| `IMPLEMENTATION_STATUS.md` | ⚠️ OUTDATED | Old status tracking | Contradicts COMPLETE.md |
| `BACKEND_ARCHITECTURE.md` | ❌ INVALID | Wrong tech stack | Uses Node.js/Express, should be **FastAPI** |

**Decision**: `IMPLEMENTATION_STATUS.md` should be archived. `BACKEND_ARCHITECTURE.md` should be deleted and recreated for FastAPI.

---

## Frontend Architecture (COMPLETE)

### Technology Stack
- **Framework**: React 18
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Language**: JavaScript (ready for TypeScript migration)
- **State**: React hooks (useState, useEffect)

### Project Structure
```
src/
├── App.jsx                         # Main orchestrator with all state
├── main.jsx                        # React entry point
├── index.css                       # Global styles + animations
├── services/
│   └── api.js                      # Mock API (416 lines, 12 scenarios)
└── components/
    ├── ConversationTranscript.jsx  # Chat interface
    ├── ContextualSurface.jsx       # Dynamic bottom cards
    ├── InputArea.jsx               # Message input
    ├── SuggestionsPopup.jsx        # Suggestion modal
    ├── DemoControls.jsx            # Scenario switcher
    ├── DeepViewManager.jsx         # Modal router
    └── deepviews/                  # 10 modal components
        ├── ConsultationView.jsx
        ├── DocumentUploadView.jsx
        ├── DocumentListView.jsx
        ├── ShareView.jsx
        ├── JournalView.jsx
        ├── ReportView.jsx
        ├── ExpertProfileView.jsx
        ├── VideoGalleryView.jsx
        ├── FilmingInstructionView.jsx
        └── MeetingSummaryView.jsx
```

### Key Design Principles

1. **Dumb Components** - All components are pure, receive props, no business logic
2. **Centralized State** - App.jsx manages all state
3. **Mock API Layer** - `src/services/api.js` simulates backend
4. **Master State Object** - Central data structure for user journey
5. **RTL Support** - Full Hebrew language support

### Data Flow
```
User Action → App.jsx Handler → API Call → State Update → Component Props → UI Update
```

---

## Master State Object

The core data structure representing user journey state:

```javascript
{
  journey_stage: 'interview' | 'consultation' | 'document_upload' |
                 'video_instructions' | 'video_upload' | 'analysis' |
                 'report_ready' | 'expert_search' | 'meeting_prep' | 'sharing',

  child: {
    name: string,
    age: number
  },

  progress: {
    interview: 0-100,
    videos: 0-100,
    documents: 0-100,
    analysis: 0-100
  },

  active_artifacts: [
    {
      type: string,
      count: number,
      total: number,
      status: string,
      viewed: string[],
      ...
    }
  ],

  completed_milestones: string[]
}
```

---

## 12 Scenarios (Mock API)

The frontend includes 12 complete scenarios in `/src/services/api.js`:

1. **interview** - Initial onboarding conversation
2. **consultation** - Q&A mode with Chitta
3. **documentUpload** - Upload diagnosis/reports
4. **returning** - Returning user welcome
5. **instructions** - Video filming instructions
6. **videoUploaded** - Progress after video upload
7. **analyzing** - Video analysis in progress
8. **reportReady** - Analysis complete, reports available
9. **viewReport** - Reading parent report
10. **experts** - Finding professionals
11. **meetingPrep** - Preparation for expert meeting
12. **sharing** - Secure sharing with professionals

Each scenario includes:
- Master State Object
- Messages array (conversation history)
- Context Cards (active now cards)
- Suggestions (contextual prompts)

---

## Frontend Components

### Main Components (6)

| Component | Purpose | Key Features |
|-----------|---------|--------------|
| **ConversationTranscript** | Message display | Auto-scroll, animations, RTL |
| **ContextualSurface** | Bottom cards | Color-coded status, actionable |
| **InputArea** | Text input | Send button, lightbulb icon |
| **SuggestionsPopup** | Modal suggestions | Bottom sheet, color-coded |
| **DemoControls** | Scenario switcher | Pill buttons, gradient |
| **DeepViewManager** | Modal router | Routes to 10 deep views |

### Deep View Components (10)

Rich modal interfaces for specific tasks:
- Consultation Q&A
- Document upload/viewing
- Video gallery
- Share settings
- Journal entries
- Report viewing
- Expert profiles
- Filming instructions
- Meeting summaries

All follow consistent pattern:
- Modal overlay with slide-up animation
- Gradient header with close button
- Scrollable content area
- RTL support

---

## Styling System

### Color Palette
- **Primary Gradient**: `from-indigo-500 to-purple-500`
- **Green**: Success/Completed (#10B981)
- **Orange**: Pending (#F59E0B)
- **Blue**: Action needed (#3B82F6)
- **Purple**: New/Important (#A855F7)
- **Yellow**: Processing (#FBBF24)

### Animations
- **fadeIn**: 0.3s ease-out (messages)
- **slideUp**: 0.3s ease-out (modals)
- **bounce**: typing indicators

### Typography
- **Headers**: Bold, 18-24px
- **Body**: Regular, 14-16px
- **Direction**: RTL for Hebrew

---

## Backend Requirements

### Technology Stack (TO BE IMPLEMENTED)
- **Framework**: **FastAPI** (Python)
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy or Prisma (Python)
- **Cache**: Redis
- **File Storage**: S3 / MinIO
- **AI**: Anthropic Claude API
- **Queue**: Celery or similar

### Core Responsibilities

1. **Authentication**
   - User registration/login
   - JWT token management
   - Session management

2. **Conversation Management**
   - Claude API integration
   - Function calling for state updates
   - Message persistence
   - Master State Object management

3. **File Management**
   - Document upload/storage
   - Video upload/storage
   - File encryption
   - Presigned URL generation

4. **Video Analysis**
   - Async processing queue
   - Thumbnail generation
   - AI analysis (future: custom models)
   - Progress tracking

5. **Report Generation**
   - Parent-friendly reports
   - Professional reports
   - PDF export

6. **Expert Matching**
   - Expert database
   - Matching algorithm
   - Location-based search

7. **Sharing**
   - Secure share links
   - Time-limited access
   - Permission management

### Required Database Tables

Core tables needed:
- `users` - User accounts
- `children` - Child profiles
- `sessions` - User journeys
- `messages` - Conversation history
- `documents` - Uploaded files
- `videos` - Uploaded videos
- `reports` - Generated reports
- `journal_entries` - Parent notes
- `experts` - Professional database
- `expert_matches` - Suggested matches
- `share_links` - Secure sharing

---

## API Endpoints Needed

### Frontend → Backend Contract

The frontend currently calls these mock API methods that need real implementations:

```javascript
// Get scenario data (initial load)
api.getScenario(scenarioKey)
// → Returns: { masterState, messages, contextCards, suggestions }

// Send user message
api.sendMessage(message)
// → Returns: { success, response: { sender, text } }

// Trigger action (open deep view, etc.)
api.triggerAction(actionKey)
// → Returns: { success, deepView }

// Upload file
api.uploadFile(file)
// → Returns: { success, fileId, message }
```

### Required REST Endpoints

```
POST   /api/auth/register
POST   /api/auth/login
POST   /api/auth/logout
GET    /api/auth/me

POST   /api/sessions
GET    /api/sessions/:id
PATCH  /api/sessions/:id/state

POST   /api/conversations/message
GET    /api/conversations/history

POST   /api/documents/upload
GET    /api/documents
GET    /api/documents/:id

POST   /api/videos/upload
GET    /api/videos
GET    /api/videos/:id

GET    /api/reports
POST   /api/reports/generate

GET    /api/experts/search
POST   /api/experts/match

POST   /api/share/create
GET    /api/share/:token

POST   /api/journal/entries
GET    /api/journal/entries
```

---

## Claude Integration Strategy

### System Prompt Components
1. Chitta's personality and role
2. Current session context
3. Child information
4. Conversation history
5. Available functions

### Function Calling
Claude should have access to:
- `update_journey_stage(stage)` - Progress to next stage
- `add_context_card(card)` - Add to contextual surface
- `trigger_deep_view(view)` - Open modal
- `update_progress(type, percentage)` - Update progress bars
- `add_milestone(milestone)` - Mark completion
- `suggest_actions(suggestions)` - Provide suggestions

### Message Flow
```
1. User sends message via frontend
2. Backend receives + retrieves session
3. Backend constructs full context prompt
4. Backend calls Claude with functions
5. Claude responds (message + function calls)
6. Backend executes function calls
7. Backend updates Master State Object
8. Backend returns updated state + message
9. Frontend updates UI
```

---

## Security Requirements

1. **Authentication**: JWT tokens
2. **Encryption**: All files at rest (AES-256)
3. **HTTPS**: All communications
4. **Data Privacy**: GDPR compliant
5. **File Access**: Presigned URLs with expiry
6. **Rate Limiting**: Prevent abuse
7. **Input Validation**: All endpoints

---

## Development Priorities

### Phase 1: Core Backend (Current Sprint)
1. FastAPI project setup
2. PostgreSQL + SQLAlchemy
3. Authentication system
4. Basic CRUD endpoints
5. Claude API integration
6. Session/state management

### Phase 2: File Handling
1. S3/MinIO integration
2. Document upload
3. Video upload
4. Async processing queue

### Phase 3: Advanced Features
1. Report generation
2. Expert matching
3. Sharing functionality
4. Journal entries

### Phase 4: Production
1. Testing suite
2. Deployment setup
3. Monitoring/logging
4. Performance optimization

---

## Migration Path

### Updating Frontend to Use Real Backend

Only one file needs changes: `/src/services/api.js`

**Before (Mock)**:
```javascript
async getScenario(scenarioKey) {
  return SCENARIOS[scenarioKey];
}
```

**After (Real)**:
```javascript
async getScenario(scenarioKey) {
  const response = await fetch(`${API_URL}/api/sessions/${sessionId}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return response.json();
}
```

All components remain unchanged - they don't know about the API!

---

## Key Decisions & Constraints

1. **Tech Stack**: FastAPI (Python) for backend - NOT Node.js
2. **Database**: PostgreSQL with proper schema
3. **AI Provider**: Anthropic Claude (already integrated in concept)
4. **File Storage**: S3-compatible (AWS or MinIO)
5. **State Model**: Master State Object is the source of truth
6. **Frontend**: No changes needed - already complete
7. **Language**: Hebrew (RTL) primary, English secondary

---

## Questions to Resolve

1. **Database ORM**: SQLAlchemy or Prisma Python?
2. **Queue System**: Celery, RQ, or ARQ?
3. **Async Processing**: How to handle video analysis?
4. **Real-time Updates**: WebSockets or polling?
5. **Deployment Target**: AWS, GCP, or other?

---

## Files to Create/Update

### Remove (Wrong Tech Stack)
- ❌ `/backend/package.json` (Node.js)
- ❌ `/backend/tsconfig.json` (TypeScript)
- ❌ `/BACKEND_ARCHITECTURE.md` (Express-based)

### Create (FastAPI)
- ✅ `/backend/pyproject.toml` or `requirements.txt`
- ✅ `/backend/main.py`
- ✅ `/backend/models/` (SQLAlchemy models)
- ✅ `/backend/routers/` (API routes)
- ✅ `/backend/services/` (Business logic)
- ✅ `/backend/schemas/` (Pydantic models)
- ✅ `/BACKEND_ARCHITECTURE_FASTAPI.md`

---

## Success Criteria

✅ **Backend is complete when**:
1. All API endpoints respond correctly
2. Authentication works
3. Claude integration functions
4. Files can be uploaded/retrieved
5. Master State Object updates properly
6. Frontend connects successfully
7. All 12 scenarios work end-to-end

---

**This document represents the single source of truth for the Chitta project as of 2024-11-04.**
