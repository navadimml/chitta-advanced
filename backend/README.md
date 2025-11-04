# Chitta Backend (FastAPI)

AI-powered child development screening platform - Backend API

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Neo4j database (for Graphiti knowledge graph)
- Gemini API key (free at https://ai.google.dev/)

### Setup

1. **Create and activate virtual environment:**

```bash
cd backend
python -m venv venv

# On Linux/Mac:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Set up environment variables:**

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your API keys
# Minimum required:
# - GEMINI_API_KEY (get from https://ai.google.dev/)
# - NEO4J_PASSWORD (if using Neo4j)
```

4. **Start Neo4j database (using Docker):**

```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password \
  neo4j:latest
```

5. **Run the development server:**

```bash
# Option 1: Using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Option 2: Using Python
python -m app.main
```

6. **Access the API:**

- API: http://localhost:8000/
- Interactive Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## 📁 Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app entry point
│   ├── config.py                    # Settings management
│   │
│   ├── api/                         # API routes
│   │   └── v1/
│   │       ├── messages.py          # (TODO) Conversation endpoints
│   │       ├── videos.py            # (TODO) Video upload & analysis
│   │       ├── reports.py           # (TODO) Report generation
│   │       └── families.py          # (TODO) Family management
│   │
│   ├── models/                      # (TODO) Pydantic models
│   │   ├── family.py
│   │   ├── message.py
│   │   ├── video.py
│   │   └── report.py
│   │
│   ├── services/                    # (TODO) Business logic
│   │   ├── conversation_service.py
│   │   ├── interview_service.py
│   │   ├── video_service.py
│   │   ├── report_service.py
│   │   └── llm/                     # LLM provider abstraction
│   │       ├── base.py
│   │       ├── factory.py
│   │       └── gemini_provider.py
│   │
│   ├── prompts/                     # (TODO) System prompts
│   │   ├── interview_prompt.py
│   │   └── video_analysis_prompt.py
│   │
│   └── core/                        # (TODO) Core utilities
│       ├── exceptions.py
│       └── storage.py
│
├── tests/                           # (TODO) Test suite
│   ├── test_api/
│   └── test_services/
│
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
├── .env                             # Your local env (create this)
└── README.md                        # This file
```

## 🎯 Current Status

✅ **Completed:**
- Basic FastAPI application setup
- Configuration management
- CORS middleware
- Health check endpoint

❌ **TODO (Next Steps):**
1. Implement LLM provider abstraction (Gemini/Claude/OpenAI)
2. Set up Graphiti integration for knowledge graph
3. Create conversation/message endpoint with function calling
4. Implement interview service with continuous extraction
5. Add video upload and analysis endpoints
6. Create report generation services
7. Implement authentication (JWT)

## 📚 Documentation

For detailed implementation guidance, see:
- **COMPREHENSIVE_DOCS_SUMMARY.md** - Complete architecture overview
- **FASTAPI_BACKEND_DESIGN.md** - Detailed implementation guide
- **INTERVIEW_IMPLEMENTATION_GUIDE.md** - Interview system specs
- **VIDEO_ANALYSIS_SYSTEM_PROMPT.md** - Video analysis specs

## 🔧 Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
# Format code
black app/

# Lint code
ruff check app/
```

### API Documentation

After starting the server, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🌐 Environment Variables

Key environment variables (see `.env.example` for complete list):

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `NEO4J_URI` | Neo4j connection URI | Yes |
| `NEO4J_PASSWORD` | Neo4j password | Yes |
| `ALLOWED_ORIGINS` | CORS allowed origins | Yes |
| `JWT_SECRET_KEY` | JWT signing key | Yes |

## 🚀 Deployment

### Docker (TODO)

```bash
docker build -t chitta-backend .
docker run -p 8000:8000 chitta-backend
```

### Production Checklist

- [ ] Set `DEBUG=False` in production
- [ ] Use strong `JWT_SECRET_KEY`
- [ ] Configure proper CORS origins
- [ ] Set up proper Neo4j production instance
- [ ] Configure S3 for video storage
- [ ] Add rate limiting
- [ ] Set up monitoring (Sentry)
- [ ] Enable HTTPS

## 🔑 Getting API Keys

### Gemini API (Recommended)
1. Go to https://ai.google.dev/
2. Click "Get API Key"
3. Create a new project
4. Copy your API key
5. Add to `.env`: `GEMINI_API_KEY=your_key_here`

**Why Gemini?**
- FREE during preview period
- Native video analysis (crucial for Chitta)
- 1M token context window
- Excellent Hebrew support
- Strong reasoning for clinical analysis

### Alternative: Anthropic Claude
1. Go to https://console.anthropic.com/
2. Generate API key
3. Add to `.env`: `ANTHROPIC_API_KEY=your_key_here`

### Alternative: OpenAI
1. Go to https://platform.openai.com/
2. Generate API key
3. Add to `.env`: `OPENAI_API_KEY=your_key_here`

## 📞 Support

For questions or issues:
1. Check the comprehensive documentation files in the root directory
2. Review the API docs at `/docs` endpoint
3. Check GitHub issues

## 📄 License

[Your License Here]
