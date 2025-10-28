# Chitta Setup Guide

This guide will help you set up the Chitta application on your local machine.

## Prerequisites

- **Node.js** 16+ and npm
- **Python** 3.8+
- **Git**

## Quick Start

### 1. Update Your Local Repository

```bash
# Navigate to your project directory
cd chitta-advanced

# Fetch latest changes from GitHub
git fetch origin

# Check what's new (optional but recommended)
git log HEAD..origin/claude/clarify-task-description-011CUR6BKA4beVRbfq928vjT --oneline

# Merge the new backend integration into your main branch
git checkout main
git merge origin/claude/clarify-task-description-011CUR6BKA4beVRbfq928vjT
```

**Note:** The difference between `fetch` and `pull`:
- `git fetch` - Downloads changes but doesn't apply them (safe, lets you inspect first)
- `git pull` - Combines fetch + merge (faster but less control)

### 2. Backend Setup (Python Virtual Environment)

#### Option A: Automated Setup (Recommended)

```bash
cd backend
./setup.sh
```

This script will:
- Create a Python virtual environment
- Install all required dependencies
- Provide instructions for running the server

#### Option B: Manual Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Linux/Mac
# OR
venv\Scripts\activate     # On Windows

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
# From project root
npm install
```

### 4. Running the Application

#### Start Backend Server

```bash
# From backend directory with activated virtual environment
cd backend
source venv/bin/activate  # If not already activated
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The backend will be available at: http://localhost:8000

Health check: http://localhost:8000/health

#### Start Frontend Development Server

In a **separate terminal**:

```bash
# From project root
npm run dev
```

The frontend will be available at: http://localhost:3000

### 5. Verify Everything Works

Open http://localhost:3000 in your browser. You should see the Chitta chat interface.

Test the integration:
```bash
# In another terminal, test the API
curl http://localhost:8000/health
```

Expected response:
```json
{"status":"healthy","environment":"development","initialized":true}
```

## Architecture Overview

### Backend (`/backend`)

- **FastAPI** web framework
- **Simulated Graphiti** - In-memory temporal knowledge graph (no Neo4j required)
- **Simulated LLM** - Mock Hebrew responses (no API keys required)
- **Multi-tenant** - Isolated data per family using group_id

**Directory Structure:**
```
backend/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── api/
│   │   └── routes.py        # API endpoints
│   └── core/
│       ├── app_state.py     # Application state management
│       ├── simulated_graphiti.py  # In-memory graph storage
│       └── simulated_llm.py       # Mock LLM provider
├── requirements.txt         # Python dependencies
├── setup.sh                 # Automated setup script
├── .env                     # Environment configuration
└── .env.example             # Example environment variables
```

### Frontend (`/src`)

- **React** 18.2.0 with Vite
- **API Client** (`src/api/client.js`) - Clean interface to backend
- **Simplified State** - React hooks, no complex state management

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/` | API info |
| POST | `/api/chat/send` | Send message to Chitta |
| POST | `/api/interview/complete` | Complete interview, generate video guidelines |
| POST | `/api/video/upload` | Upload video |
| POST | `/api/video/analyze` | Analyze all videos |
| POST | `/api/reports/generate` | Generate reports |
| GET | `/api/timeline/{family_id}` | Get journey timeline |

## Environment Configuration

The backend uses environment variables for configuration. Copy `.env.example` to `.env` and modify as needed:

```bash
cd backend
cp .env.example .env
```

Default configuration:
- `LLM_PROVIDER=simulated` - Uses mock LLM (no API calls)
- `ENVIRONMENT=development`
- `LOG_LEVEL=INFO`
- `CORS_ORIGINS=http://localhost:5173,http://localhost:3000`

## Development Workflow

### Activating Virtual Environment

Every time you open a new terminal to work on the backend:

```bash
cd backend
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows
```

You'll see `(venv)` in your terminal prompt when activated.

### Deactivating Virtual Environment

```bash
deactivate
```

### Installing New Python Packages

```bash
# Make sure venv is activated
pip install package-name

# Update requirements.txt
pip freeze > requirements.txt
```

### Running Tests

```bash
# Backend tests (when implemented)
cd backend
pytest

# Frontend tests
npm test
```

## Troubleshooting

### Backend won't start

1. Make sure virtual environment is activated: `source venv/bin/activate`
2. Check Python version: `python --version` (should be 3.8+)
3. Reinstall dependencies: `pip install -r requirements.txt`
4. Check if port 8000 is already in use: `lsof -i :8000`

### Frontend won't start

1. Clear node_modules: `rm -rf node_modules && npm install`
2. Check if port 3000 is in use: `lsof -i :3000`
3. Try a different port: `npm run dev -- --port 3001`

### CORS errors

Make sure both servers are running and the backend CORS settings in `.env` include your frontend URL.

### API not responding

1. Check backend is running: `curl http://localhost:8000/health`
2. Check frontend API client URL in `src/api/client.js` matches backend URL
3. Check browser console for errors

## Next Steps

### Moving from Simulated to Real Services

When ready to use real services:

1. **Real LLM (Google Gemini)**:
   - Set `LLM_PROVIDER=gemini` in `.env`
   - Add `LLM_API_KEY=your_key_here` in `.env`
   - Install: `pip install google-generativeai`

2. **Real Graphiti (Neo4j)**:
   - Install Neo4j locally or use cloud service
   - Install: `pip install graphiti-core neo4j`
   - Update `app/core/app_state.py` to use real Graphiti client
   - Configure Neo4j connection in `.env`

### Development Features to Add

- User authentication
- Video file storage and processing
- Real video analysis with computer vision
- Professional report generation with templates
- Email notifications
- Data persistence (database)
- Deployment configuration

## Project Structure

```
chitta-advanced/
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── core/         # Business logic
│   │   └── main.py       # Application entry
│   ├── venv/             # Virtual environment (not in git)
│   └── requirements.txt
├── src/                  # React frontend
│   ├── api/             # API client
│   ├── components/      # React components
│   └── App.jsx          # Main app component
├── public/              # Static assets
├── SETUP.md            # This file
└── package.json        # Frontend dependencies
```

## Contributing

When making changes:

1. Create a feature branch: `git checkout -b feature-name`
2. Make your changes
3. Test thoroughly
4. Commit with clear messages
5. Push and create a pull request

## Support

For issues or questions:
- Check the [Troubleshooting](#troubleshooting) section
- Review the [API documentation](#api-endpoints)
- Check backend logs for error messages
- Check browser console for frontend errors

---

Built with ❤️ for child development assessment
