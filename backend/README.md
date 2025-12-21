# Chitta Backend

FastAPI backend implementing the Darshan architecture for child development understanding.

## Quick Start

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python -m app.main
```

Server runs at http://localhost:8000

## Architecture: Darshan/Chitta

The backend implements the **Darshan** (दर्शन - "mutual seeing") architecture:

### Core Components (`app/chitta/`)

| File | Purpose |
|------|---------|
| `service.py` | ChittaService - thin orchestrator, public API |
| `gestalt.py` | Darshan - the observing intelligence |
| `curiosity.py` | Curiosity model (discovery, question, hypothesis, pattern) |
| `models.py` | Data models (Understanding, Evidence, Story, etc.) |
| `tools.py` | LLM perception tools (notice, wonder, capture_story, add_evidence) |
| `synthesis.py` | Portrait/crystal generation with strongest model |
| `cards.py` | Context card derivation from gestalt state |
| `video_service.py` | Video consent → guidelines → upload → analysis |
| `child_space.py` | Living Portrait derivation |
| `sharing.py` | Shareable summary generation |
| `journal_service.py` | Parent journal processing |
| `gestalt_manager.py` | Darshan lifecycle & persistence |

### Two-Phase LLM Architecture

Every message is processed in two phases:

```
Phase 1: Perception (temp=0.0, with tools)
  → Darshan perceives and understands
  → Tool calls: notice, wonder, capture_story, add_evidence

Phase 2: Response (temp=0.7, no tools)
  → Natural Hebrew response generation
  → Warm, empathetic communication
```

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI entry point
│   ├── chitta/                 # Core Darshan architecture
│   │   ├── service.py          # ChittaService (public API)
│   │   ├── gestalt.py          # Darshan (observing intelligence)
│   │   ├── curiosity.py        # Curiosity model
│   │   ├── models.py           # Data models
│   │   ├── tools.py            # Perception tools
│   │   ├── synthesis.py        # Portrait generation
│   │   ├── cards.py            # Card derivation
│   │   ├── video_service.py    # Video workflow
│   │   ├── child_space.py      # Living Portrait
│   │   ├── sharing.py          # Summary sharing
│   │   ├── journal_service.py  # Journal processing
│   │   └── gestalt_manager.py  # Lifecycle management
│   ├── api/
│   │   ├── routes/
│   │   │   ├── chat.py         # Chat V2 endpoints
│   │   │   ├── video.py        # Video upload
│   │   │   ├── state.py        # State & SSE
│   │   │   ├── family.py       # Family management
│   │   │   └── darshan.py      # Darshan API
│   │   └── dev_routes.py       # Development tools
│   ├── services/
│   │   ├── llm/                # LLM provider abstraction
│   │   │   ├── base.py         # Provider interface
│   │   │   ├── gemini_provider.py
│   │   │   └── factory.py
│   │   ├── unified_state_service.py
│   │   ├── session_service.py
│   │   └── sse_notifier.py
│   ├── config/                 # YAML-driven configuration
│   │   ├── workflows/          # Lifecycle events, cards
│   │   └── i18n/               # Internationalization
│   └── core/
│       └── app_state.py        # Application state
├── tests/                      # 153 tests
├── data/                       # Persisted child/session data
├── docs/                       # Architecture documentation
└── config/                     # Configuration files
```

## API Endpoints

### Chat V2 (Current)
```
GET  /api/chat/v2/init/{family_id}     # Initialize session
POST /api/chat/v2/send                  # Send message
GET  /api/chat/v2/curiosity/{family_id} # Get curiosity state
POST /api/chat/v2/synthesis/{family_id} # Request synthesis
```

### Video Workflow
```
POST /api/chat/v2/video/accept          # Accept video suggestion
POST /api/chat/v2/video/decline         # Decline video suggestion
GET  /api/chat/v2/video/guidelines/{family_id}/{cycle_id}
POST /api/chat/v2/video/upload
POST /api/chat/v2/video/analyze/{family_id}/{cycle_id}
```

### State & SSE
```
GET  /api/state/{family_id}             # Complete family state
GET  /api/state/subscribe?family_id=X   # SSE real-time updates
```

## Environment Variables

Create `.env` from `.env.example`:

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | Required |
| `LLM_PROVIDER` | Provider: gemini, anthropic, openai | gemini |
| `ENVIRONMENT` | development, production | development |
| `LOG_LEVEL` | DEBUG, INFO, WARNING, ERROR | INFO |

## Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_curiosity.py -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

153 tests currently passing.

## Development

### Code Guidelines

See `CLAUDE.md` for the complete developer constitution:

- **Curiosity-driven**: Use discovery, question, hypothesis, pattern - not checklists
- **Two-phase LLM**: Tool calls and text responses are separate
- **Natural Hebrew**: "שמתי לב ש..." not "המערכת זיהתה..."
- **Minimum necessary complexity** (פשוט)

### Key Principles

1. Darshan is the **observing intelligence** - not a data container
2. Understanding emerges through **curiosity**, not assessment
3. **Type and certainty are independent**: You can have weak hypotheses or strong discoveries
4. Tool calls and text responses **cannot be combined** in one LLM call

## LLM Configuration

### Model Tiers
| Tier | Models | Use For |
|------|--------|---------|
| Strongest | gemini-3-pro-preview | Pattern detection, synthesis |
| Standard | gemini-2.5-flash | Conversation, memory distillation |

### Critical Settings
```python
# Phase 1: Perception
temperature = 0.0
tool_config = FunctionCallingConfigMode.ANY
automatic_function_calling = disabled

# Phase 2: Response
temperature = 0.7
functions = None  # No tools
```

## Documentation

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Developer constitution & coding guidelines |
| `docs/METAPHOR_ARCHITECTURE.md` | Darshan naming philosophy |
| `docs/CURIOSITY_EXPLORATION_REDESIGN.md` | Curiosity system design |

---

Built with the Darshan philosophy: seeing children clearly through curiosity and conversation.
