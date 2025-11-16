# Frontend-Backend Integration Guide

## Quick Start

### Option 1: Automatic Startup (Recommended)

```bash
# From project root
./start.sh
```

This starts both frontend and backend automatically!

### Option 2: Manual Startup

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
# From project root
npm run dev
```

---

## URLs

- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Health Check**: http://localhost:8000/health

---

## Testing the Connection

### 1. Check Backend is Running

```bash
curl http://localhost:8000/health
```

**Expected**:
```json
{
  "status": "healthy",
  "environment": "development",
  "initialized": true
}
```

### 2. Test API Endpoint

```bash
curl -X POST http://localhost:8000/api/chat/send \
  -H "Content-Type: application/json" \
  -d '{
    "family_id": "test_001",
    "message": "שלום"
  }'
```

**Expected**: JSON response with Hebrew text

### 3. Open Frontend

Visit http://localhost:3000

You should see:
- ✅ Chitta greeting message
- ✅ Input box at bottom
- ✅ Suggestion chips
- ✅ Clean UI with Hebrew text

### 4. Send a Message

Try typing in the chat:
```
שלום, שמו יוני והוא בן 3.5
```

**Expected**:
- ✅ Your message appears
- ✅ Chitta responds with real AI (not canned response!)
- ✅ Context cards appear showing extracted data
- ✅ Progress bar shows completeness

---

## What to Look For

### Real AI Indicators

🎯 **Natural Responses**: Each response is different (not pre-programmed)
🎯 **Data Extraction**: Cards show "פרופיל: יוני" with age
🎯 **Progress**: Completeness percentage increases
🎯 **Smart Follow-ups**: Questions are context-aware

### In Browser Console

Open DevTools (F12) and check:
```javascript
// You should see API calls like:
POST http://localhost:8000/api/chat/send

// Response will include:
{
  response: "נעים להכיר את יוני!...",
  stage: "interview",
  ui_data: {
    progress: 0.25,
    cards: [...],
    extracted_data: {
      child_name: "יוני",
      age: 3.5
    }
  }
}
```

---

## Common Issues

### Backend Won't Start

**Error**: `Port 8000 already in use`

**Solution**:
```bash
# Kill existing process
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn app.main:app --reload --port 8001
# Then update frontend: VITE_API_URL=http://localhost:8001/api
```

**Error**: `GEMINI_API_KEY not set`

**Solution**:
```bash
cd backend
nano .env  # Add GEMINI_API_KEY=your_key_here
```

### Frontend Won't Connect

**Error**: `CORS error` or `fetch failed`

**Check**:
1. Backend is running: `curl http://localhost:8000/health`
2. CORS is configured: Check `backend/app/main.py` line 33
3. API URL is correct: Check `src/api/client.js` line 6

**Fix**:
```bash
# In backend/.env, ensure:
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### No Response from API

**Check Backend Logs**:
```bash
# If using start.sh
tail -f backend.log

# If running manually
# Look at terminal running uvicorn
```

**Common issues**:
- LLM provider not configured
- GEMINI_API_KEY missing
- Function calling failed (should use fallback)

---

## Development Tips

### Hot Reload

Both frontend and backend support hot reload:
- **Frontend**: Vite automatically reloads on file changes
- **Backend**: `--reload` flag reloads on Python file changes

### View Logs in Real-Time

**Backend logs** (using start.sh):
```bash
tail -f backend.log
```

**Or with colors**:
```bash
tail -f backend.log | grep --color -E "ERROR|WARNING|INFO|$"
```

### Test Different Models

**Flash** (fast, cheap):
```bash
# In backend/.env
LLM_MODEL=gemini-2.0-flash-exp
```

**Pro** (better quality):
```bash
# In backend/.env
LLM_MODEL=gemini-pro-2.5
```

Restart backend to apply changes.

### Debug Mode

**Enable debug logging**:
```bash
# In backend/.env
LOG_LEVEL=DEBUG
```

You'll see:
- Every API call
- Function calls made
- Data extracted
- Completeness calculations

---

## Testing Checklist

### First Conversation

- [ ] Send: "שלום"
  - [ ] Get Hebrew response
  - [ ] Response is natural (not canned)

- [ ] Send: "שמו יוני והוא בן 3.5"
  - [ ] Card appears: "פרופיל: יוני"
  - [ ] Card shows: "גיל 3.5"
  - [ ] Progress increases (check ui_data.progress)

- [ ] Send: "יש לי דאגות לגבי הדיבור שלו"
  - [ ] Card appears with concerns
  - [ ] Progress increases more

- [ ] Continue conversation
  - [ ] Each response is contextual
  - [ ] Completeness keeps increasing
  - [ ] At ~80%: Video upload card appears

### Check Backend Logs

You should see:
```
INFO - Processing message for family family_xxx
INFO - Using LITE mode for family_xxx  (if Flash model)
INFO - LLM response received: 150 chars, 1 function calls
INFO - Extracted data: ['child_name', 'age', 'gender']
INFO - Updated data for family_xxx: completeness=25.0%
```

### Check Frontend Console

You should see:
```javascript
// Successful API call
POST http://localhost:8000/api/chat/send 200 OK

// Response object
{
  response: "...",
  stage: "interview",
  ui_data: {
    progress: 0.25,
    cards: [{...}],
    extracted_data: {...},
    stats: {...}
  }
}
```

---

## Next Steps

Once frontend-backend connection is working:

1. **Test Full Conversation Flow**
   - Complete a full interview (10-15 messages)
   - Verify it reaches 80%+ completeness
   - Check video upload card appears

2. **Test Different Scenarios**
   - Different child names and ages
   - Various concerns (speech, social, attention, etc.)
   - Long vs short responses

3. **Monitor Performance**
   - Response time per message
   - Function calling success rate
   - Completeness calculation accuracy

4. **Prepare for Production**
   - Set up environment variables
   - Configure logging
   - Add error monitoring

---

## Troubleshooting Commands

```bash
# Check what's running on ports
lsof -i :3000  # Frontend
lsof -i :8000  # Backend

# Kill all processes
pkill -f uvicorn  # Backend
pkill -f vite     # Frontend

# Restart everything
./start.sh

# View recent logs
tail -n 100 backend.log
tail -n 100 frontend.log

# Test API directly
curl http://localhost:8000/health
curl http://localhost:8000/api/

# Check environment
cd backend
source venv/bin/activate
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Provider:', os.getenv('LLM_PROVIDER')); print('Model:', os.getenv('LLM_MODEL')); print('Key set:', bool(os.getenv('GEMINI_API_KEY')))"
```

---

## Success!

When everything is working, you should have:
- ✅ Frontend showing at http://localhost:3000
- ✅ Real AI responses (different every time)
- ✅ Data extraction visible in cards
- ✅ Progress tracking working
- ✅ Natural Hebrew conversation
- ✅ No errors in console

**You're now running Chitta with real AI! 🎉**

Start chatting and watch the magic happen!
