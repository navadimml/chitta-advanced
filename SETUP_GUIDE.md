# Chitta - Complete Setup Guide

## Overview

Chitta is a full-stack AI-powered child development assessment platform with:
- **Frontend**: React + Vite + Tailwind CSS
- **Backend**: FastAPI (Python 3.11+)
- **AI**: LLM integration (Gemini/Claude/OpenAI or Simulated mode)
- **Knowledge Graph**: Graphiti with FalkorDB (or Simulated mode)

## Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.11+
- **Git**
- *Optional*: Docker (for FalkorDB)
- *Optional*: API keys for LLM providers (Gemini, Claude, or OpenAI)

## Quick Start (Simulated Mode - No API Keys Needed!)

This is the fastest way to get started - runs completely locally with simulated AI responses:

### 1. Clone and Navigate

```bash
git clone <repository-url>
cd chitta-advanced
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (already configured for simulated mode)
# The .env file is already set up with LLM_PROVIDER=simulated

# Start backend server
python -m app.main
```

Backend will start on: **http://localhost:8000**
- Health Check: http://localhost:8000/health
- API Docs: http://localhost:8000/docs

### 3. Frontend Setup (in a new terminal)

```bash
cd chitta-advanced  # Back to root

# Install dependencies
npm install

# The .env file is already configured to connect to backend

# Start frontend dev server
npm run dev
```

Frontend will start on: **http://localhost:3000**

### 4. Open in Browser

Navigate to **http://localhost:3000** and start chatting with Chitta!

## Production Mode with Real AI

For production deployment with real AI capabilities:

### Backend Configuration

1. Edit `backend/.env`:

```bash
# Choose your LLM provider
LLM_PROVIDER=gemini  # or "anthropic" or "openai"
LLM_MODEL=gemini-2.5-pro  # Recommended for clinical reasoning

# Add your API key
GEMINI_API_KEY=your_actual_api_key_here

# Optional: Set up FalkorDB
GRAPHITI_MODE=real  # Use real FalkorDB instead of simulated
```

### Getting API Keys

#### Google Gemini (Recommended)
1. Visit: https://ai.google.dev/
2. Click "Get API Key"
3. Create a project and generate key
4. **Why Gemini?**
   - FREE during preview
   - Native video analysis (critical for Chitta)
   - 1M token context window
   - Excellent Hebrew support
   - Strong clinical reasoning

#### Anthropic Claude
1. Visit: https://console.anthropic.com/
2. Generate API key
3. Add to `.env`: `ANTHROPIC_API_KEY=your_key_here`

#### OpenAI GPT-4
1. Visit: https://platform.openai.com/
2. Generate API key
3. Add to `.env`: `OPENAI_API_KEY=your_key_here`

### Setting up FalkorDB (Optional)

FalkorDB provides the knowledge graph backend via Graphiti. In development, simulated mode works fine.

#### Using Docker:

```bash
docker run -d \
  --name falkordb \
  -p 6379:6379 \
  falkordb/falkordb:latest
```

Then update `backend/.env`:
```bash
GRAPHITI_MODE=real
FALKORDB_HOST=localhost
FALKORDB_PORT=6379
```

## Project Structure

```
chitta-advanced/
├── backend/                      # FastAPI backend
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── api/
│   │   │   └── routes.py        # API endpoints
│   │   └── core/
│   │       ├── app_state.py     # Application state
│   │       ├── simulated_llm.py # Simulated LLM for dev
│   │       └── simulated_graphiti.py  # Simulated graph
│   ├── requirements.txt
│   ├── .env                     # Backend config
│   └── README.md
│
├── src/                         # React frontend
│   ├── App.jsx                  # Main app component
│   ├── api/
│   │   └── client.js            # Backend API client
│   ├── components/              # UI components
│   │   ├── ConversationTranscript.jsx
│   │   ├── ContextualSurface.jsx
│   │   ├── InputArea.jsx
│   │   └── deepviews/           # Modal views
│   │       ├── VideoUploadView.jsx
│   │       ├── JournalView.jsx
│   │       └── ...
│   └── core/                    # Core conversation engine
│       ├── ConversationController.js
│       ├── JourneyEngine.js
│       └── UIAdapter.js
│
├── .env                         # Frontend config
├── package.json
├── vite.config.js
└── README.md
```

## Available API Endpoints

### Health Check
```bash
GET /health
```

### Chat / Messaging
```bash
POST /api/chat/send
Body: {
  "family_id": "string",
  "message": "string",
  "parent_name": "string"
}
```

### Interview
```bash
POST /api/interview/complete?family_id=string
```

### Video Upload
```bash
POST /api/video/upload
Body: {
  "family_id": "string",
  "video_id": "string",
  "scenario": "string",
  "duration_seconds": number
}
```

### Video Analysis
```bash
POST /api/video/analyze?family_id=string
```

### Journal
```bash
POST /api/journal/add
Body: {
  "family_id": "string",
  "content": "string",
  "category": "string"
}

GET /api/journal/list?family_id=string
```

### Reports
```bash
GET /api/report/generate?family_id=string
```

Full API documentation available at: **http://localhost:8000/docs**

## Testing the Integration

### Test Backend Only:

```bash
# Health check
curl http://localhost:8000/health

# Send a message
curl -X POST http://localhost:8000/api/chat/send \
  -H "Content-Type: application/json" \
  -d '{
    "family_id": "test-family",
    "message": "שלום, רציתי לדבר על הילד שלי"
  }'
```

### Test Full Stack:

1. Open browser to http://localhost:3000
2. Type a message in Hebrew
3. Chitta should respond (with simulated AI or real AI depending on your config)
4. Check browser console for any errors
5. Check backend logs for API calls

## Environment Variables

### Frontend (.env in root)
```bash
VITE_API_URL=http://localhost:8000/api
```

### Backend (backend/.env)
```bash
# LLM Configuration
LLM_PROVIDER=simulated              # or "gemini", "anthropic", "openai"
LLM_MODEL=simulated-model           # or "gemini-2.5-pro", etc.

# API Keys (only needed if not using simulated)
GEMINI_API_KEY=
ANTHROPIC_API_KEY=
OPENAI_API_KEY=

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO

# CORS (both frontend dev ports)
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Graphiti
GRAPHITI_MODE=simulated             # or "real" for FalkorDB
```

## Development Workflow

### Running Both Servers Together

Terminal 1 (Backend):
```bash
cd backend
source venv/bin/activate
python -m app.main
```

Terminal 2 (Frontend):
```bash
npm run dev
```

### Making Changes

#### Frontend Changes
- Edit files in `src/`
- Vite will hot-reload automatically
- Check browser console for errors

#### Backend Changes
- Edit files in `backend/app/`
- FastAPI will auto-reload (with `--reload` flag)
- Check terminal for errors

### Adding New API Endpoints

1. Add route to `backend/app/api/routes.py`
2. Add corresponding method to `src/api/client.js`
3. Use the method in your React components

## Troubleshooting

### Backend won't start
```bash
# Check Python version
python3 --version  # Should be 3.11+

# Make sure virtual environment is activated
which python  # Should point to venv/bin/python

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Frontend won't start
```bash
# Check Node version
node --version  # Should be 18+

# Clear and reinstall
rm -rf node_modules package-lock.json
npm install
```

### CORS Errors
- Make sure `ALLOWED_ORIGINS` in `backend/.env` includes your frontend URL
- Check that both servers are running
- Clear browser cache

### API Connection Errors
- Verify backend is running: `curl http://localhost:8000/health`
- Check `VITE_API_URL` in frontend `.env`
- Check browser network tab for actual error

## Deployment

### Backend Deployment (Production)

1. Set environment variables:
```bash
ENVIRONMENT=production
DEBUG=False
# Add strong JWT secret
# Configure real database URLs
# Set proper CORS origins
```

2. Use production WSGI server:
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Frontend Deployment

1. Build for production:
```bash
npm run build
```

2. Deploy `dist/` folder to:
   - Vercel
   - Netlify
   - AWS S3 + CloudFront
   - Your preferred hosting

3. Update `VITE_API_URL` to point to production backend

## Documentation

- **ARCHITECTURE.md** - System architecture and design principles
- **IMPLEMENTATION_STATUS.md** - Current implementation status
- **FASTAPI_BACKEND_DESIGN.md** - Detailed backend design
- **INTERVIEW_IMPLEMENTATION_GUIDE.md** - Interview system guide
- **VIDEO_ANALYSIS_SYSTEM_PROMPT.md** - Video analysis specs
- **DOCUMENTATION_INDEX.md** - Complete documentation index

## Support

For issues or questions:
1. Check the comprehensive documentation in the root directory
2. Review API docs at http://localhost:8000/docs
3. Check GitHub issues

## License

[Your License Here]

---

**Ready to start?** Just run the Quick Start commands above and you'll be chatting with Chitta in minutes! 🚀
