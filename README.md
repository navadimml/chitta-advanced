# Chitta - AI-Powered Child Development Understanding

## Overview

Chitta is a conversation-first platform for understanding child development. Using the **Darshan architecture** (Sanskrit for "mutual seeing"), Chitta helps parents and clinicians see children clearly through natural conversation, video observation, and curiosity-driven exploration.

**Status**: Production-ready
**Version**: 2.0.0
**Architecture**: Darshan/Chitta

## Philosophy

Chitta is an **expert developmental psychologist** (0.5-18 years) - not just a conversationalist.

- **Identity**: An expert guide with deep developmental psychology knowledge
- **Voice**: "שמתי לב ש..." not "המערכת זיהתה..." (Simple words, deep understanding)
- **Goal**: Create space for understanding through **curiosity**, not checklists

## Stack

- **Frontend**: React + Vite + Tailwind CSS
- **Backend**: FastAPI (Python 3.11+)
- **AI**: Gemini 2.5 Flash (conversation), Gemini 3 Pro (synthesis)
- **State**: Darshan gestalt with session persistence
- **Languages**: Hebrew-first with RTL support

## Quick Start

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
```

### Frontend (in new terminal)
```bash
npm install
npm run dev
```

Open **http://localhost:5173** and start chatting!

## Architecture: Darshan

**Darshan** (दर्शन) means "mutual seeing" - the core of Chitta's approach.

### Core Concepts

| Concept | Description |
|---------|-------------|
| **Darshan** | The observing intelligence - holds understanding, notices patterns, acts with curiosity |
| **Curiosity** | Four types: discovery, question, hypothesis, pattern |
| **Crystal** | Synthesized understanding that emerges over time |
| **Exploration** | Video-based observation cycles |

### Two-Phase LLM Architecture

Chitta uses two separate LLM calls per message:

1. **Perception Phase** (temp=0.0, with tools)
   - Darshan perceives and understands
   - Tool calls: notice, wonder, capture_story, add_evidence

2. **Response Phase** (temp=0.7, no tools)
   - Natural Hebrew response generation
   - Warm, empathetic communication

## API Endpoints

### Chat (V2 - Current)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/chat/v2/init/{family_id}` | Initialize chat session |
| POST | `/api/chat/v2/send` | Send message to Chitta |
| GET | `/api/chat/v2/curiosity/{family_id}` | Get curiosity state |
| POST | `/api/chat/v2/synthesis/{family_id}` | Request synthesis report |

### Video Workflow
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat/v2/video/accept` | Accept video suggestion |
| POST | `/api/chat/v2/video/decline` | Decline video suggestion |
| GET | `/api/chat/v2/video/guidelines/{family_id}/{cycle_id}` | Get filming guidelines |
| POST | `/api/chat/v2/video/upload` | Upload video |
| POST | `/api/chat/v2/video/analyze/{family_id}/{cycle_id}` | Analyze videos |

### State & Family
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/state/{family_id}` | Get complete family state |
| GET | `/api/state/subscribe` | SSE real-time updates |
| GET | `/api/family/{family_id}/child-space` | Get child portrait |

## Project Structure

```
chitta-advanced/
├── backend/
│   ├── app/
│   │   ├── chitta/              # Core Darshan architecture
│   │   │   ├── service.py       # ChittaService - thin orchestrator
│   │   │   ├── gestalt.py       # Darshan - the observing intelligence
│   │   │   ├── curiosity.py     # Curiosity model
│   │   │   ├── models.py        # Data models
│   │   │   ├── tools.py         # LLM perception tools
│   │   │   ├── synthesis.py     # Portrait/crystal generation
│   │   │   ├── cards.py         # Context card derivation
│   │   │   ├── video_service.py # Video workflow
│   │   │   └── ...              # Other specialized services
│   │   ├── api/routes/          # API endpoints
│   │   ├── services/llm/        # LLM provider abstraction
│   │   └── config/              # YAML-driven configuration
│   └── tests/                   # 153 tests
├── src/                         # React frontend
│   ├── App.jsx                  # Main state orchestrator
│   ├── api/client.js            # API client
│   └── components/              # UI components
└── CLAUDE.md                    # Developer guide & constitution
```

## Key Documentation

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Developer constitution & coding guidelines |
| `backend/docs/METAPHOR_ARCHITECTURE.md` | Darshan naming philosophy |

## Development

### Running Tests
```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

### Code Quality
All code follows the principles in `CLAUDE.md`:
- Curiosity-driven, not checklist-driven
- Natural Hebrew language
- Minimum necessary complexity (פשוט)
- Two-phase LLM architecture

## What's Implemented

- Natural Hebrew conversation with curiosity-driven exploration
- Video suggestion, upload, and analysis workflow
- Living Portrait (child understanding) synthesis
- Context cards derived from gestalt state
- Session management with memory distillation
- Real-time updates via SSE
- 153 passing tests

---

**Chitta** - Seeing children clearly through curiosity and conversation
