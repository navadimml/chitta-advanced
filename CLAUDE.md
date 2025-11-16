# CLAUDE.md - Chitta Project Context

**Last Updated**: 2025-11-16
**Branch**: `claude/fix-conversation-quality-01Gzw78tMVSaym1ALBHsbP9o`
**Purpose**: Complete context for Claude AI to understand and work with Chitta

---

## Table of Contents

1. [What is Chitta?](#what-is-chitta)
2. [Tech Stack](#tech-stack)
3. [Architecture Overview](#architecture-overview)
4. [Core Innovations](#core-innovations)
5. [Code Structure](#code-structure)
6. [Important File Locations](#important-file-locations)
7. [Code Conventions](#code-conventions)
8. [External Tools & APIs](#external-tools--apis)
9. [Current Implementation Status](#current-implementation-status)
10. [Known Issues & Recent Fixes](#known-issues--recent-fixes)
11. [Development Workflow](#development-workflow)
12. [Key Concepts & Terminology](#key-concepts--terminology)

---

## What is Chitta?

**Chitta** is an AI-powered child development assessment platform that helps parents understand their child's developmental progress through natural conversation, video analysis, and expert recommendations.

### The Core Problem Chitta Solves

**The Fundamental Tension of Chat Interfaces**:
- ✅ Chat is GREAT for conversational flow
- ❌ Chat is TERRIBLE for random access (finding past information)

**Chitta's Innovation**: A two-layer system that combines continuous conversation with AI-curated context cards, eliminating the need for traditional navigation while maintaining perfect recall.

### What Makes Chitta Different

**Traditional Apps**:
- Users navigate menus and tabs
- Users remember where things are
- Structure is spatial (folders, pages)
- Users manage organization

**Chitta**:
- AI navigates for users via natural language
- AI remembers where everything is
- Structure is temporal (conversation + AI-managed context)
- AI manages organization proactively

### User Journey

1. **Interview Phase**: Parent has natural conversation about their child (Hebrew-native)
2. **Video Guidelines**: AI generates personalized filming instructions
3. **Video Upload**: Parent uploads videos of child in different scenarios
4. **Analysis**: AI (Gemini 2.5 Pro) analyzes videos + conversation context
5. **Reports**: Two reports generated - Parent guide + Professional report
6. **Expert Matching**: AI recommends appropriate specialists
7. **Ongoing Partnership**: Journal, consultations, meeting prep, care team coordination

---

## Tech Stack

### Frontend
- **Framework**: React 18.2 + Vite 4
- **Styling**: Tailwind CSS 3.3
- **Icons**: Lucide React
- **Language**: Hebrew with full RTL support
- **State Management**: Component state (no Redux/Zustand)
- **Markdown**: react-markdown for rich content

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Server**: Uvicorn with async/await
- **Data Models**: Pydantic 2.5+
- **Environment**: python-dotenv
- **CORS**: Full CORS middleware for frontend integration

### AI & LLMs
- **Primary Model**: Gemini 2.5 Pro (recommended) or Gemini Flash
- **Providers**: Abstracted - supports Gemini, Claude, GPT-4, or Simulated
- **SDK**: google-genai 0.2.0+ (modern SDK, not legacy)
- **Function Calling**: Native support for structured data extraction
- **Video Analysis**: Gemini's native multimodal capabilities

### Knowledge Graph (Optional/Future)
- **Framework**: Graphiti (temporal knowledge graph)
- **Database Options**:
  - FalkorDB (recommended - 10x faster, 80% less memory)
  - Neo4j (alternative - mature ecosystem)
- **Purpose**: Long-term family context, pattern detection, temporal queries

### Architecture Mode (Configurable)
- **Simplified** (default): 1-2 LLM calls per message (80% cost reduction)
- **Full**: 5-6 LLM calls per message (legacy multi-agent)

---

## Architecture Overview

Chitta uses **three revolutionary architectures** working together:

### 1. Two-Layer UI System (Conversation-First)

**The Innovation**: Solves chat's random-access problem

```
┌─────────────────────────────────────┐
│  LAYER 1: Conversation (Primary)   │
│  - Natural Hebrew dialogue          │
│  - Always active, never "complete"  │
│  - Typing indicator & suggestions   │
└─────────────────────────────────────┘
         ↓ Informs ↓
┌─────────────────────────────────────┐
│  LAYER 2: Contextual Surface        │
│  - AI-curated cards (max 2-4)       │
│  - Updates automatically            │
│  - Clickable → opens deep views     │
│  - Color-coded by status/urgency    │
└─────────────────────────────────────┘
```

**Key Principles**:
- Users NEVER navigate - AI brings info to them
- Conversation is primary, cards are supportive
- Cards appear/disappear based on context
- Everything accessible via natural language

### 2. Wu Wei Architecture (無為 - Effortless Action)

**Philosophy**: "Flow like water" - natural progression over forced stages

**Traditional Apps**:
```
Stage 1 → Complete → Gate → Stage 2 → Complete → Gate → Stage 3
```

**Wu Wei (Chitta)**:
```
Conversation (ongoing)
    ↓
Knowledge accumulates
    ↓
Capabilities emerge when prerequisites met
    ↓
Parent explores freely
    ↓
Chitta guides gently when ready
```

**Key Concepts**:
- **No rigid phases** - Dependency graph determines what's available
- **No "interview complete"** - Conversation is continuous
- **Prerequisites enable, don't gate** - Gentle guidance vs. hard blocks
- **Qualitative progress** - "Getting to know Daniel 💭" not "76% complete"
- **Proactive surfacing** - AI offers capabilities when ready (parent doesn't need to ask)
- **Moments** - Unified configuration for when capabilities unlock

**v3.0 Simplification** (פשוט - נטול חלקים עודפים):
- 208 lines of config (down from 360)
- Unified `moments` structure (no redundancy)
- One place for prerequisites, artifacts, messages, UI, unlocks

### 3. Simplified Conversation Architecture

**The Problem**: Original architecture used 5-6 LLM calls per message:
1. Sage (interpret intent)
2. Hand (decide action)
3. Strategic Advisor (coverage check)
4. Conversation (generate response)
5. Extraction (extract data)
6. Semantic verification (every 3 turns)

**The Solution**: Function calling reduces to 1-2 LLM calls per message

**New Flow**:
```
User message
  ↓
Main LLM call with 5 comprehensive functions:
  - extract_interview_data()
  - ask_developmental_question()
  - ask_about_analysis()
  - ask_about_app()
  - request_action()
  ↓
Process function calls (no LLM calls)
  ↓
Semantic check (every 3 turns) - 1 LLM call
  ↓
Response (1-2 LLM calls total)
```

**Benefits**:
- 80% cost reduction
- 5x faster responses
- Same or better quality
- Easier to maintain

---

## Core Innovations

### 1. Conversation + Context Surface (Two-Layer System)

**Problem**: Chat interfaces lack random access to past information

**Solution**:
- **Primary**: Natural conversation (Hebrew) - user can ask anything anytime
- **Secondary**: AI-curated context cards - show 2-4 most relevant items
- **Deep Views**: Modal overlays for detailed content (reports, videos, etc.)

**Example**:
```
Parent: "Where's my report?"
Chitta: "Opening your parent guide..."
[Report opens in modal, conversation continues below]
```

### 2. Wu Wei Dependency System

**Problem**: Rigid stage-based workflows feel constraining

**Solution**: Capabilities unlock organically based on accumulated knowledge

**Example Configuration** (v3.0):
```yaml
moments:
  guidelines_ready:
    when:
      knowledge_is_rich: true
    artifact: "baseline_video_guidelines"
    message: "ההנחיות מוכנות! 📹"
    ui:
      type: "card"
      default: "תראי את הכרטיס 'הנחיות צילום' ב'פעיל עכשיו' למטה"
    unlocks: ["upload_videos"]
```

**Flow**:
1. Parent shares info about child (no minimum required)
2. When prerequisites met → Chitta proactively offers capability
3. Card appears automatically (parent doesn't search for it)
4. Parent can accept or decline (gentle guidance, never forced)
5. Unlocks next capability when ready

### 3. Proactive Surfacing System

**Critical Insight**: Parents don't know what the app can do - they can't ask for everything

**Solution - Two Information Channels**:

**Channel 1: Conversation** - Chitta proactively offers:
```
Chitta: "יש לי מספיק מידע כדי להכין לך הנחיות צילום
         מותאמות לדניאל. רוצה שאכין?"
```

**Channel 2: Cards** - Appear automatically:
```yaml
[Card appears: "מוכנ/ה להנחיות צילום? 🎬" [כן, תכיני]]
```

**Parent always knows**:
1. What's happening right now (Chitta's message or card title)
2. What they can do (card action button or Chitta's prompt)
3. What's next (Chitta's guidance or next card appearing)

### 4. Simplified Function-Based Architecture

**Problem**: Multiple LLM calls slow and expensive

**Solution**: One LLM call with comprehensive functions

**5 Core Functions**:
1. `extract_interview_data` - Extract structured child info
2. `ask_developmental_question` - General dev questions
3. `ask_about_analysis` - Questions about Chitta's specific analysis
4. `ask_about_app` - Questions about the app/process
5. `request_action` - Parent wants to do something

**Gemini calls appropriate functions automatically** while generating response

---

## Code Structure

### Frontend (`/src`)

```
src/
├── App.jsx                          # Main orchestrator (170 lines)
│   └── State: messages, context cards, deep views, master state
│
├── main.jsx                         # React entry point
├── index.css                        # Global styles + animations
│
├── api/
│   └── client.js                    # Backend API client
│
├── components/
│   ├── ConversationTranscript.jsx   # Chat message display with RTL
│   ├── ContextualSurface.jsx        # AI-curated context cards (max 4)
│   ├── InputArea.jsx                # Text input + lightbulb suggestions
│   ├── SuggestionsPopup.jsx         # Bottom sheet with actions
│   ├── DeepViewManager.jsx          # Modal routing system
│   └── deepviews/                   # 11 modal components
│       ├── ConsultationView.jsx
│       ├── JournalView.jsx
│       ├── ReportView.jsx
│       ├── VideoUploadView.jsx
│       └── ... (7 more)
│
├── config/
│   └── masterState.js               # State schema definitions
│
├── core/
│   ├── ConversationController.js    # Conversation logic
│   ├── JourneyEngine.js             # Journey state management
│   └── UIAdapter.js                 # UI state derivation
│
└── services/
    └── api.js                       # Mock backend (can replace with real)
```

**Key Patterns**:
- **Dumb components** - All UI components are pure (props in, render out)
- **Centralized state** - App.jsx manages everything
- **Deep views** - Modal overlays for rich content
- **RTL-first** - Hebrew text with proper directionality

### Backend (`/backend`)

```
backend/
├── app/
│   ├── main.py                      # FastAPI entry point
│   │   └── CORS, routes, startup/shutdown
│   │
│   ├── api/
│   │   └── routes.py                # API endpoints
│   │       ├── /chat/send           # Main conversation endpoint
│   │       ├── /interview/complete
│   │       ├── /video/*             # Upload & analysis
│   │       ├── /journal/*
│   │       └── /report/*
│   │
│   ├── core/
│   │   ├── app_state.py             # Global application state
│   │   ├── simulated_llm.py         # Simulated LLM (no API keys needed)
│   │   └── simulated_graphiti.py    # Simulated graph DB
│   │
│   ├── models/
│   │   ├── family_state.py          # Family/session state models
│   │   └── artifact.py              # Artifact data models
│   │
│   ├── prompts/
│   │   ├── conversation_functions.py            # 5 comprehensive functions
│   │   ├── comprehensive_prompt_builder.py      # Single comprehensive prompt
│   │   ├── interview_prompt.py                  # Interview system prompt
│   │   ├── dynamic_interview_prompt.py          # Context-aware prompting
│   │   ├── domain_knowledge.py                  # Clinical knowledge base
│   │   └── prerequisites.py                     # Prerequisite checking logic
│   │
│   ├── services/
│   │   ├── conversation_service.py              # Full architecture (5-6 calls)
│   │   ├── conversation_service_simplified.py   # Simplified (1-2 calls) ✅
│   │   ├── consultation_service.py              # Q&A with context
│   │   ├── knowledge_service.py                 # Graph queries
│   │   ├── lifecycle_manager.py                 # Wu Wei moments management
│   │   ├── prerequisite_service.py              # Dependency checking
│   │   ├── artifact_generation_service.py       # Guidelines/reports
│   │   ├── session_service.py                   # Session management
│   │   └── llm/
│   │       ├── base.py                          # LLM provider abstraction
│   │       ├── factory.py                       # Provider factory
│   │       ├── gemini_provider.py               # Gemini implementation
│   │       ├── gemini_provider_enhanced.py      # Enhanced Gemini
│   │       └── simulated_provider.py            # No-API-key testing
│   │
│   ├── config/
│   │   ├── config_loader.py         # YAML config loading
│   │   ├── card_generator.py        # Context card generation
│   │   ├── artifact_manager.py      # Artifact lifecycle
│   │   └── schema_registry.py       # Data schemas
│   │
│   └── utils/
│       └── hebrew_utils.py          # Hebrew text processing
│
├── config/
│   ├── app_config.yaml              # Runtime settings ✅
│   │   └── architecture: "simplified" (default)
│   └── workflows/
│       ├── lifecycle_events.yaml    # Wu Wei v3.0 moments ✅
│       └── context_cards.yaml       # Card display rules
│
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment template
└── README.md                        # Backend setup
```

**Key Patterns**:
- **Service layer** - Business logic separated from routes
- **Provider abstraction** - Easy to switch LLM providers
- **YAML configuration** - Wu Wei moments, cards, settings
- **Async/await** - All I/O operations are async

---

## Important File Locations

### Configuration

| File | Purpose |
|------|---------|
| `backend/config/app_config.yaml` | Runtime settings (architecture mode, features) |
| `backend/config/workflows/lifecycle_events.yaml` | Wu Wei v3.0 moments (unified structure) |
| `backend/config/workflows/context_cards.yaml` | Context card display rules |
| `backend/.env` | Environment variables (API keys, LLM settings) |
| `.env` (root) | Frontend environment (API URL) |

### Core Architecture Files

| File | Purpose |
|------|---------|
| `backend/app/services/conversation_service_simplified.py` | **PRIMARY** - Simplified architecture (1-2 calls) |
| `backend/app/services/conversation_service.py` | Legacy full architecture (5-6 calls) |
| `backend/app/prompts/conversation_functions.py` | 5 comprehensive functions for intent/action |
| `backend/app/prompts/comprehensive_prompt_builder.py` | Builds single comprehensive system prompt |
| `backend/app/services/lifecycle_manager.py` | Wu Wei moments & capability unlocking |
| `backend/app/services/prerequisite_service.py` | Dependency checking |

### LLM Integration

| File | Purpose |
|------|---------|
| `backend/app/services/llm/base.py` | Provider abstraction interface |
| `backend/app/services/llm/factory.py` | Provider factory (Gemini/Claude/GPT-4) |
| `backend/app/services/llm/gemini_provider.py` | Gemini integration |
| `backend/app/services/llm/gemini_provider_enhanced.py` | Enhanced Gemini with AFC disabled |
| `backend/app/prompts/interview_prompt.py` | Interview system prompt (Hebrew) |

### Frontend Core

| File | Purpose |
|------|---------|
| `src/App.jsx` | Main orchestrator - all state management |
| `src/components/ContextualSurface.jsx` | AI-curated context cards |
| `src/components/ConversationTranscript.jsx` | Chat UI with RTL |
| `src/components/DeepViewManager.jsx` | Modal routing |
| `src/api/client.js` | Backend API client |

### Documentation

| File | Purpose |
|------|---------|
| `DOCUMENTATION_INDEX.md` | **START HERE** - Complete doc navigation |
| `WU_WEI_ARCHITECTURE.md` | Wu Wei philosophy & v3.0 implementation |
| `ARCHITECTURE_V2.md` | Two-layer system architecture |
| `CORE_INNOVATION_DETAILED.md` | The fundamental problem we solve |
| `GRAPHITI_INTEGRATION_GUIDE.md` | Knowledge graph + Gemini 2.5 Pro |
| `CONVERSATION_QUALITY_FIXES.md` | Recent fixes (AFC, tokens, etc.) |
| `SIMPLIFIED_ARCHITECTURE_IMPLEMENTATION.md` | 80% cost reduction details |

---

## Code Conventions

### Backend (Python)

**Style**:
- PEP 8 compliant
- Async/await for all I/O operations
- Type hints with Pydantic models
- Descriptive variable names (no abbreviations)

**Patterns**:
```python
# Service pattern
class ConversationService:
    async def process_message(self, family_id: str, message: str) -> dict:
        # Business logic here
        pass

# Dependency injection via factory
llm = LLMFactory.create(
    provider=settings.LLM_PROVIDER,
    api_key=settings.LLM_API_KEY,
    model=settings.LLM_MODEL
)

# Pydantic for data validation
from pydantic import BaseModel

class ExtractedData(BaseModel):
    child_name: Optional[str] = None
    age: Optional[float] = None
    primary_concerns: List[str] = []
```

**Error Handling**:
```python
try:
    result = await service.do_something()
except Exception as e:
    logger.error(f"Failed to do something: {e}")
    return {"error": str(e)}
```

**Logging**:
```python
import logging
logger = logging.getLogger(__name__)

logger.info("✅ Success message")
logger.warning("⚠️  Warning message")
logger.error("❌ Error message")
logger.debug("🔍 Debug info")
```

### Frontend (React)

**Style**:
- Functional components with hooks
- Props destructuring
- Tailwind CSS classes (no CSS modules)
- Hebrew text in JSX (UTF-8)

**Patterns**:
```javascript
// Component pattern (dumb component)
export default function ComponentName({ prop1, prop2, onAction }) {
  return (
    <div className="tailwind classes">
      {/* RTL Hebrew text */}
      <span dir="rtl">טקסט בעברית</span>
    </div>
  );
}

// State management (in App.jsx only)
const [state, setState] = useState(initialValue);

useEffect(() => {
  // Side effects
}, [dependencies]);

// Handler pattern
const handleAction = async () => {
  try {
    const result = await api.doSomething();
    setState(result);
  } catch (error) {
    console.error("Error:", error);
  }
};
```

**Tailwind Patterns**:
```javascript
// Gradient backgrounds
className="bg-gradient-to-r from-indigo-500 to-purple-500"

// RTL support
dir="rtl"
className="text-right" // for Hebrew

// Animations (defined in index.css)
className="animate-fadeIn"
className="animate-slideUp"
className="animate-bounce"

// Responsive
className="flex flex-col md:flex-row"
```

### Configuration (YAML)

**Wu Wei v3.0 Moments**:
```yaml
moments:
  moment_name:
    when:                              # Prerequisites
      field_name: value
      numeric_field: ">= 3"
      OR:                              # Alternative path
        alternative: true

    artifact: "artifact_id"            # Optional

    message: |                         # Optional
      Message text (supports {child_name})

    ui:                                # Optional
      type: "card"                     # card, button, modal, etc.
      default: "Desktop guidance"
      mobile: "Mobile guidance"        # Only if different

    unlocks:                           # Optional
      - capability1
      - capability2
```

---

## External Tools & APIs

### Gemini 2.5 Pro (Primary LLM)

**Why Gemini?**
- FREE during preview (then very cost-effective)
- 1M token context window (entire conversation + family data)
- Native video analysis (multimodal)
- Excellent Hebrew support
- Strong clinical reasoning
- Function calling support

**Models**:
- `gemini-2.5-pro` - **RECOMMENDED** for clinical analysis (strong reasoning)
- `gemini-2.0-flash-exp` - Fast, good for conversations
- `gemini-flash-lite-latest` - ❌ **NOT RECOMMENDED** (weak reasoning)

**SDK**: google-genai 0.2.0+ (modern SDK)

**Setup**:
```bash
pip install google-genai>=0.2.0
```

**Environment**:
```bash
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-pro
GEMINI_API_KEY=your_api_key_here
```

**API Key**: https://ai.google.dev/

**Function Calling**:
```python
from google import genai
from google.genai import types

# CRITICAL: Disable Automatic Function Calling (AFC)
config = types.GenerateContentConfig(
    temperature=0.7,
    max_output_tokens=4000,
    tools=tools,
    tool_config=types.ToolConfig(
        function_calling_config=types.FunctionCallingConfig(
            mode=types.FunctionCallingConfigMode.ANY
        )
    )
)
```

**Known Issues**:
- AFC enabled by default (returns ONLY text, no function_call parts)
- Flash Lite has weak function calling (use 2.5 Pro or 2.0 Flash Exp)
- Safety filters can block test simulations (use Flash Lite for personas)

### Graphiti (Temporal Knowledge Graph)

**Status**: Optional/Future integration

**Purpose**:
- Long-term family memory (months/years of data)
- Pattern detection (recurring issues, consistent progress)
- Context-aware retrieval (pull relevant history for consultations)
- Temporal queries ("Has speech improved over time?")

**Database Options**:

| Feature | FalkorDB (Recommended) | Neo4j |
|---------|----------------------|-------|
| Speed | 10x-30x faster | Baseline |
| Memory | 50-80% less | Baseline |
| Cost | 3x-4x cheaper at scale | Higher |
| Maturity | Newer | Battle-tested |
| Ecosystem | Redis-based | Rich plugins |

**Setup**:
```bash
# FalkorDB (recommended)
docker run -p 6379:6379 falkordb/falkordb:latest

# Neo4j (alternative)
docker run -p 7687:7687 -p 7474:7474 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest
```

**Data Model**:
- **Entities**: Child, Parent, Professional, Observation, Milestone, Concern, Strategy
- **Edges**: HasConcern, ShowsProgress, AchievedMilestone, TreatedBy, TriedStrategy
- **Episodes**: Every interaction (conversation, journal, video analysis)

**Why Later**: Core functionality works without it; add when needed for:
- Multiple children per family
- Long-term progress tracking (> 6 months)
- Pattern detection across families
- Research/analytics

### Provider Comparison

| Provider | Recommended For | Cost | Context | Hebrew | Video |
|----------|----------------|------|---------|--------|-------|
| **Gemini 2.5 Pro** | Clinical analysis, video | Free then $0 | 1M | ✅ | ✅ |
| Gemini 2.0 Flash Exp | Conversations, speed | Low | 1M | ✅ | ✅ |
| Claude 3.5 Sonnet | Interview warmth | $3-15/1M | 200K | ✅ | ❌ |
| GPT-4o | Structured extraction | $2.5-10/1M | 128K | ✅ | ❌ |

---

## Current Implementation Status

### ✅ Completed (Production-Ready)

**Frontend**:
- ✅ Full two-layer UI (conversation + context cards)
- ✅ 11 deep views (modals for rich content)
- ✅ RTL Hebrew support with proper rendering
- ✅ Responsive design (mobile-first)
- ✅ Animations and micro-interactions
- ✅ Demo controls for scenario switching

**Backend - Core**:
- ✅ FastAPI server with CORS
- ✅ Simulated mode (no API keys needed)
- ✅ LLM provider abstraction (Gemini/Claude/GPT-4/Simulated)
- ✅ Session management
- ✅ State persistence

**Backend - Wu Wei v3.0**:
- ✅ Unified moments structure (208 lines, -42% from v2.0)
- ✅ Dependency-based capability unlocking
- ✅ Lifecycle manager with moment detection
- ✅ Prerequisite service
- ✅ Qualitative progress indicators (not percentages)
- ✅ Proactive surfacing system

**Backend - Simplified Architecture**:
- ✅ Function-based intent detection (5 functions)
- ✅ Comprehensive prompt builder (single prompt)
- ✅ 1-2 LLM calls per message (80% cost reduction)
- ✅ Config-driven architecture switching
- ✅ Semantic verification (every 3 turns)

**Backend - Conversation**:
- ✅ Interview system with continuous extraction
- ✅ Hebrew conversation patterns
- ✅ Context-aware responses
- ✅ Function calling for data extraction
- ✅ Knowledge richness tracking

**Backend - Artifacts**:
- ✅ Video guidelines generation
- ✅ Report generation (parent + professional)
- ✅ Artifact status management
- ✅ Prerequisite checking before generation

### 🔧 In Progress

- ⏳ Video upload & storage integration
- ⏳ Video analysis with Gemini 2.5 Pro
- ⏳ Journal system backend
- ⏳ Expert matching algorithm
- ⏳ Meeting preparation summaries

### 📋 Planned (Future)

- 📅 Graphiti integration for long-term memory
- 📅 Care team coordination
- 📅 Multi-child support per family
- 📅 Professional portal
- 📅 Analytics dashboard
- 📅 Mobile app (React Native)

---

## Known Issues & Recent Fixes

### Recent Fixes (2025-11-16)

#### ✅ FIXED: Automatic Function Calling (AFC) Issue
**Problem**: Gemini SDK enables AFC by default, causing zero function calls
**Solution**: Explicitly disable AFC with `FunctionCallingConfigMode.ANY`
**File**: `backend/app/services/llm/gemini_provider_enhanced.py`

#### ✅ FIXED: Message Truncation
**Problem**: Responses cut mid-sentence ("זה יכול להיות רכ...")
**Solution**: Increased `max_tokens` from 2000 to 4000
**Files**: `conversation_service.py`, `conversation_service_simplified.py`

#### ✅ FIXED: Missing Assistant Response in History
**Problem**: Infinite function calling loop (model forgets it called function)
**Solution**: Add assistant's response with function_calls to history BEFORE sending results
**File**: `conversation_service_simplified.py`

#### ✅ FIXED: Empty Responses from Weak Models
**Problem**: Flash Lite returns empty messages after extraction
**Solution**: Intelligent fallback response generation using extracted data
**File**: `conversation_service_simplified.py`

### Current Challenges

#### 1. Model Selection
- `gemini-flash-lite-latest` has weak reasoning (NOT recommended)
- Use `gemini-2.5-pro` for clinical work
- Use `gemini-2.0-flash-exp` for cost-effective conversations

#### 2. Safety Filters
- Gemini safety filters can block parent simulator personas
- Workaround: Use Flash Lite for test simulations (bypass filters)
- Production: Use 2.5 Pro (better safety calibration)

#### 3. Function Calling Reliability
- Ensure AFC is disabled (critical!)
- Always include assistant response in history
- Use max_tokens >= 4000 for Hebrew + function calls

---

## Development Workflow

### Setup

**Backend**:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env: Set LLM_PROVIDER=simulated (or gemini with API key)

# Start server
python -m app.main
```

**Frontend**:
```bash
# In root directory
npm install

# Create .env file
echo "VITE_API_URL=http://localhost:8000/api" > .env

# Start dev server
npm run dev
```

**Access**:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Testing

**Backend**:
```bash
# Run test scripts
python backend/test_conversation_service.py
python backend/test_gemini_interview_enhanced.py
python backend/demo_end_to_end_simple.py
```

**Frontend**:
```bash
# No tests yet - manual testing via demo controls
npm run dev
# Use demo controls dropdown to test scenarios
```

### Configuration Switching

**Architecture Mode**:
```yaml
# backend/config/app_config.yaml
conversation:
  architecture: "simplified"  # 1-2 LLM calls (default)
  # architecture: "full"      # 5-6 LLM calls (legacy)
```

**LLM Provider**:
```bash
# backend/.env
LLM_PROVIDER=gemini           # or anthropic, openai, simulated
LLM_MODEL=gemini-2.5-pro      # or gemini-2.0-flash-exp
GEMINI_API_KEY=your_key_here  # from https://ai.google.dev/
```

### Git Workflow

**Current Branch**: `claude/fix-conversation-quality-01Gzw78tMVSaym1ALBHsbP9o`

**Commit Messages**:
```bash
# Good examples
git commit -m "Fix AFC issue in Gemini provider - disable automatic function calling"
git commit -m "Increase max_tokens to 4000 to prevent message truncation"
git commit -m "Add fallback response generation for weak models"

# Pattern: <action> <what> - <why>
```

**Push**:
```bash
# CRITICAL: Push to branch starting with 'claude/' and ending with session ID
git push -u origin claude/fix-conversation-quality-01Gzw78tMVSaym1ALBHsbP9o
```

---

## Key Concepts & Terminology

### Chitta-Specific Terms

| Term | Meaning |
|------|---------|
| **Chitta** | The AI assistant (named after Sanskrit for "mind/consciousness") |
| **Wu Wei** (無為) | "Effortless action" - our dependency-based architecture |
| **Moment** | Configuration unit for when capabilities unlock (v3.0) |
| **Artifact** | Generated content (guidelines, reports, summaries) |
| **Context Cards** | AI-curated cards showing relevant actions (max 2-4) |
| **Deep View** | Modal overlay for detailed content |
| **Master State Object** | Complete family/session state |
| **Knowledge Richness** | Qualitative measure of conversation depth |
| **Prerequisites** | Conditions that must be met for capabilities to unlock |
| **פשוט** (Pashut) | Hebrew for "simple" - v3.0 design principle |

### Architecture Terms

| Term | Meaning |
|------|---------|
| **Simplified Architecture** | 1-2 LLM calls per message (default) |
| **Full Architecture** | 5-6 LLM calls per message (legacy) |
| **AFC** | Automatic Function Calling (Gemini SDK feature - must disable!) |
| **Function Calling** | LLM calling structured functions for intent/data extraction |
| **Proactive Surfacing** | AI offers capabilities without user asking |
| **Dependency Graph** | System determining what's available based on prerequisites |
| **Two-Layer System** | Conversation (primary) + Context cards (secondary) |

### User Journey Terms

| Term | Meaning |
|------|---------|
| **Interview** | Initial conversation (ongoing, never "complete") |
| **Guidelines** | Personalized video filming instructions |
| **Analysis** | AI processing videos + conversation context |
| **Report** | Parent guide or professional assessment |
| **Consultation** | Q&A with Chitta using full context |
| **Journal** | Parent observations and progress notes |
| **Care Team** | Professionals working with child |

### Technical Terms

| Term | Meaning |
|------|---------|
| **RTL** | Right-to-Left (for Hebrew text) |
| **Pydantic** | Python data validation library |
| **FastAPI** | Modern Python web framework |
| **Uvicorn** | ASGI server for FastAPI |
| **Lucide** | Icon library (React) |
| **Tailwind** | Utility-first CSS framework |

---

## Quick Reference

### Environment Variables

**Backend** (`backend/.env`):
```bash
# LLM Configuration
LLM_PROVIDER=gemini                    # gemini, anthropic, openai, simulated
LLM_MODEL=gemini-2.5-pro               # specific model
GEMINI_API_KEY=your_key                # from ai.google.dev

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Graphiti (optional, future)
GRAPHITI_MODE=simulated                # or "real" for FalkorDB/Neo4j
```

**Frontend** (`.env`):
```bash
VITE_API_URL=http://localhost:8000/api
```

### Common Tasks

**Add new Wu Wei moment**:
1. Edit `backend/config/workflows/lifecycle_events.yaml`
2. Add to `moments` section with `when`, `artifact`, `message`, `ui`, `unlocks`
3. No code changes needed!

**Add new function**:
1. Edit `backend/app/prompts/conversation_functions.py`
2. Add to appropriate Enum (IntentType, QuestionType, ActionType)
3. Update function schema if needed
4. Handler will route automatically

**Add new deep view**:
1. Create `src/components/deepviews/NewView.jsx`
2. Register in `src/components/DeepViewManager.jsx`
3. Add action to context card configuration

**Switch LLM provider**:
1. Edit `backend/.env`: Change `LLM_PROVIDER=gemini` to desired provider
2. Set appropriate API key variable
3. Restart backend
4. No code changes!

---

## Getting Help

**Documentation**:
1. Start with `DOCUMENTATION_INDEX.md` for navigation
2. For architecture: `WU_WEI_ARCHITECTURE.md`, `ARCHITECTURE_V2.md`
3. For specific features: Check index for relevant doc

**Common Questions**:
- "How does Wu Wei work?" → `WU_WEI_ARCHITECTURE.md`
- "How does two-layer UI work?" → `CORE_INNOVATION_DETAILED.md`
- "How to add Gemini?" → `GRAPHITI_INTEGRATION_GUIDE.md`
- "Recent fixes?" → `CONVERSATION_QUALITY_FIXES.md`
- "Cost reduction?" → `SIMPLIFIED_ARCHITECTURE_IMPLEMENTATION.md`

**Code Exploration**:
- Backend entry: `backend/app/main.py`
- Frontend entry: `src/App.jsx`
- Main conversation: `backend/app/services/conversation_service_simplified.py`
- Wu Wei logic: `backend/app/services/lifecycle_manager.py`

---

**This document provides complete context for Claude AI to understand and work effectively with the Chitta codebase. For detailed information on specific topics, refer to the linked documentation files.**

**Last Updated**: 2025-11-16
**Maintainer**: Development Team
**Branch**: `claude/fix-conversation-quality-01Gzw78tMVSaym1ALBHsbP9o`
