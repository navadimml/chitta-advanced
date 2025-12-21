# Chitta Setup Guide

Complete setup guide for the Chitta development environment.

## Prerequisites

- **Python** 3.11+
- **Node.js** 18+ and npm
- **Git**

## Quick Start

### 1. Clone & Setup Backend

```bash
cd chitta-advanced/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 2. Setup Frontend

```bash
cd chitta-advanced
npm install
```

### 3. Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python -m app.main
```

**Terminal 2 - Frontend:**
```bash
npm run dev
```

Open http://localhost:5173 in your browser.

## Environment Configuration

### Backend (.env)

```bash
# Required
GEMINI_API_KEY=your_key_here

# Optional (defaults shown)
LLM_PROVIDER=gemini
ENVIRONMENT=development
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Getting a Gemini API Key

1. Go to https://ai.google.dev/
2. Click "Get API Key"
3. Create a new project
4. Copy your API key
5. Add to `.env`: `GEMINI_API_KEY=your_key_here`

## Verifying Installation

### Backend Health Check
```bash
curl http://localhost:8000/api/
# Expected: {"message":"Chitta API","version":"2.0.0","architecture":"darshan"}
```

### Run Tests
```bash
cd backend
source venv/bin/activate
pytest tests/ -v
# Expected: 153 tests passed
```

## Architecture Overview

### Darshan/Chitta Architecture

Chitta uses the **Darshan** architecture:

```
Message arrives
    ↓
Phase 1: Perception (with tools, temp=0)
    - Darshan perceives and understands
    - Tool calls: notice, wonder, capture_story, add_evidence
    ↓
Apply Learnings (update gestalt)
    ↓
Phase 2: Response (without tools, temp=0.7)
    - Natural Hebrew response
    ↓
Persist + Return
```

### Key Directories

```
backend/
├── app/chitta/          # Core Darshan architecture
│   ├── service.py       # ChittaService (thin orchestrator)
│   ├── gestalt.py       # Darshan (observing intelligence)
│   ├── curiosity.py     # Curiosity model
│   └── ...
├── app/api/routes/      # API endpoints
├── app/services/llm/    # LLM provider abstraction
└── tests/               # 153 tests

src/                     # React frontend
├── App.jsx              # Main state orchestrator
├── api/client.js        # API client
└── components/          # UI components
```

## API Endpoints

### Chat V2
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/chat/v2/init/{family_id}` | Initialize session |
| POST | `/api/chat/v2/send` | Send message |
| GET | `/api/chat/v2/curiosity/{family_id}` | Get curiosity state |
| POST | `/api/chat/v2/synthesis/{family_id}` | Request synthesis |

### Video Workflow
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat/v2/video/accept` | Accept video suggestion |
| POST | `/api/chat/v2/video/decline` | Decline video suggestion |
| GET | `/api/chat/v2/video/guidelines/{family_id}/{cycle_id}` | Get guidelines |
| POST | `/api/chat/v2/video/upload` | Upload video |
| POST | `/api/chat/v2/video/analyze/{family_id}/{cycle_id}` | Analyze videos |

### State
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/state/{family_id}` | Get family state |
| GET | `/api/state/subscribe` | SSE updates |

## Development Workflow

### Virtual Environment

Always activate the virtual environment when working on backend:
```bash
cd backend
source venv/bin/activate  # (venv) appears in prompt
```

Deactivate when done:
```bash
deactivate
```

### Running Tests
```bash
cd backend
source venv/bin/activate
pytest tests/ -v           # All tests
pytest tests/test_curiosity.py -v  # Specific file
```

### Code Guidelines

See `CLAUDE.md` for the complete developer constitution:

1. **Curiosity-driven**: Use discovery, question, hypothesis, pattern
2. **Two-phase LLM**: Tool calls and text responses are separate
3. **Natural Hebrew**: "שמתי לב ש..." not "המערכת זיהתה..."
4. **פשוט**: Minimum necessary complexity

## Troubleshooting

### Backend won't start

1. Check virtual environment is activated: `source venv/bin/activate`
2. Check Python version: `python --version` (needs 3.11+)
3. Reinstall dependencies: `pip install -r requirements.txt`
4. Check port 8000: `lsof -i :8000`

### Frontend won't start

1. Reinstall: `rm -rf node_modules && npm install`
2. Check port: `lsof -i :5173`

### API not responding

1. Check backend: `curl http://localhost:8000/api/`
2. Check CORS settings in `.env`
3. Check browser console for errors

### Tests failing

1. Make sure venv is activated
2. Check for missing dependencies: `pip install -r requirements.txt`
3. Run with verbose: `pytest tests/ -v --tb=short`

## Key Documentation

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Developer constitution & coding guidelines |
| `README.md` | Project overview |
| `backend/README.md` | Backend architecture |
| `backend/docs/METAPHOR_ARCHITECTURE.md` | Darshan naming philosophy |

---

For questions, check the documentation or review the test files for usage examples.
