# Testing Gemini Interview Implementation

## Implementation Status

✅ **Phase 1: LLM Provider Abstraction Layer** - COMPLETE
- Created base provider interface with standardized Message/Response models
- Implemented Gemini provider using modern google-genai SDK (2024+)
- Implemented simulated provider for development
- Factory pattern for easy provider switching
- All providers return consistent LLMResponse format

✅ **Phase 2: Interview System Prompt & Functions** - COMPLETE
- Dynamic interview prompt builder with state tracking
- Three interview functions for LLM:
  - `extract_interview_data`: Continuous extraction during conversation
  - `user_wants_action`: Detect when user wants to do something
  - `check_interview_completeness`: Evaluate if interview is ready to conclude
- Prerequisite system for action dependencies
- Comprehensive Hebrew prompt with empathy guidelines

🔧 **Ready for Testing** - Implementation complete, needs real API key verification

## Testing Locally with Real Gemini API

### Step 1: Configure Environment

Edit `backend/.env`:

```bash
# Change from simulated to gemini
LLM_PROVIDER=gemini

# For conversation: Fast model
LLM_MODEL=gemini-flash-lite-latest

# For extraction: Strong model with stable function calling
EXTRACTION_MODEL=gemini-2.5-flash

# Add your real API key
GEMINI_API_KEY=your_actual_api_key_here
```

### Step 2: Ensure Dependencies Installed

```bash
cd backend
source venv/bin/activate
pip install google-genai
```

**Expected version:** google-genai==1.48.0 or later

### Step 3: Run Comprehensive Test Suite

```bash
cd backend
python test_gemini_interview.py
```

This runs 4 tests:

1. **Basic Chat**: Verifies Gemini connection and Hebrew support
2. **Function Calling**: Tests `extract_interview_data` extraction
3. **Multi-Turn Conversation**: Tests continuous extraction across multiple messages
4. **Completeness Check**: Tests interview completion detection

### Step 4: Test via API Endpoint

Start backend:
```bash
cd backend
./venv/bin/python -m uvicorn app.main:app --reload
```

Send test message:
```bash
curl -X POST http://localhost:8000/api/chat/send \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session",
    "message": "היי, שמי רונית והילד שלי יוני בן 3.5 ויש לי דאגות לגבי הדיבור",
    "family_id": "test-family"
  }'
```

### Step 5: Test with Frontend

Start frontend:
```bash
cd frontend
npm run dev
```

Navigate to: http://localhost:5173

Start a conversation and observe:
- Hebrew responses should be natural and warm
- LLM should extract data continuously (check backend logs)
- Conversation should feel natural, not like a form

## What to Verify

### ✅ Connection & Basic Functionality
- [ ] Gemini provider initializes without errors
- [ ] Server logs show: "✅ Gemini provider initialized: gemini-2.5-flash" or "gemini-flash-lite-latest"
- [ ] Basic chat returns Hebrew responses
- [ ] No API errors or authentication failures

### ✅ Function Calling
- [ ] `extract_interview_data` is called when parent shares information
- [ ] Extracted data includes child_name, age, gender when mentioned
- [ ] `primary_concerns` array populated correctly (e.g., ["speech", "social"])
- [ ] `concern_details` includes specific examples from parent

**Example extraction from:** "שמי רונית והילד שלי יוני בן 3.5 ויש דאגות לגבי הדיבור"

Expected function call:
```json
{
  "name": "extract_interview_data",
  "arguments": {
    "child_name": "יוני",
    "age": 3.5,
    "gender": "male",
    "primary_concerns": ["speech"],
    "concern_details": "הורה מדווח על דאגות לגבי הדיבור"
  }
}
```

### ✅ Conversation Quality
- [ ] Responses are warm and empathetic (not clinical)
- [ ] One primary question per turn
- [ ] Builds on previously mentioned information
- [ ] Hebrew grammar is natural and correct
- [ ] No repeated "אני מבינה" - empathy is implicit

### ✅ Multi-Turn Extraction
- [ ] Each turn extracts relevant new information
- [ ] Extraction is partial/incremental (doesn't wait for "complete" answers)
- [ ] Previously extracted data is not re-extracted
- [ ] Conversation flows naturally without feeling like data collection

### ✅ Completeness Checking
- [ ] When parent signals they're done, `check_interview_completeness` is called
- [ ] Completeness estimate is reasonable (0-100%)
- [ ] Missing critical info is correctly identified
- [ ] Interview doesn't conclude prematurely

## Expected Test Output

### Test 1: Basic Chat
```
TEST 1: Basic Chat with Gemini
✅ Provider initialized: Gemini (gemini-2.5-flash)
📝 Response: שלום! אני עובד/ת
🏁 Finish reason: STOP
🔧 Function calls: 0
```

### Test 2: Function Calling
```
TEST 2: Function Calling - Interview Data Extraction
📝 Response content: תודה רונית! נעים מאוד. ספרי לי על יוני - במה הוא אוהב לעסוק?
🔧 Function calls: 1
  Function 1: extract_interview_data
  Arguments: {
    'child_name': 'יוני',
    'age': 3.5,
    'gender': 'male',
    'primary_concerns': ['speech'],
    'concern_details': 'הורה מדאג לגבי הדיבור של הילד'
  }
  ✅ Extracted data:
     - Child name: יוני
     - Age: 3.5
     - Gender: male
     - Concerns: ['speech']
```

### Test 3: Multi-Turn Conversation
```
TEST 3: Multi-Turn Conversation
📝 Assistant response: מעניין! רכבות ובנייה זה נהדר. ספרי לי יותר על הדיבור - תני לי דוגמה, מה הוא אומר?
🔧 Function calls: 1
  Function 1: extract_interview_data
  ✅ Extracted in this turn:
     - Strengths: אוהב רכבות ובנייה
     - Concerns added: ['speech']
     - Details: מדבר במילים בודדות בלבד
```

### Test 4: Completeness Check
```
TEST 4: Interview Completeness Check
📝 Response: תודה רבה על כל המידע! יש לי תמונה טובה של יוני. אני מכינה עכשיו הנחיות צילום מותאמות אישית.
✅ Interview completeness check called!
   Ready to complete: true
   Completeness: 85%
   Missing: []
```

## Troubleshooting

### Error: "google-genai not installed"
```bash
cd backend
source venv/bin/activate
pip install google-genai
```

### Error: "GEMINI_API_KEY not set"
Check your `.env` file:
```bash
cat backend/.env | grep GEMINI
```
Should show:
```
GEMINI_API_KEY=your_actual_key_here
```

### Error: 401 Unauthorized
- API key is invalid or expired
- Get new key from: https://aistudio.google.com/app/apikey

### Error: 429 Rate Limit
- Free tier has limits
- Wait a few seconds between tests
- Consider upgrading API tier

### Function Calling Not Working
- Check Gemini model supports function calling (2.0-flash does)
- Verify function definitions are being passed in API call
- Check backend logs for function call detection

### Responses in English Instead of Hebrew
- System prompt should be in Hebrew context
- Check `interview_prompt.py` is being used
- Verify messages include Hebrew content

## Implementation Architecture

### Message Flow

```
User Message (Hebrew)
    ↓
API Route (/api/chat/send)
    ↓
Create Message objects
    ↓
Build dynamic system prompt (interview_prompt.py)
    ↓
Include function definitions (interview_functions.py)
    ↓
LLM Provider (Gemini/Simulated)
    ↓
Parse Response:
  - content: Hebrew response to user
  - function_calls: Extracted data, actions, completeness checks
    ↓
Process function calls:
  - extract_interview_data → Update session state
  - user_wants_action → Check prerequisites, respond appropriately
  - check_interview_completeness → Evaluate if ready to conclude
    ↓
Return response to user
```

### Key Files

**LLM Providers:**
- `app/services/llm/base.py` - Base interfaces (Message, LLMResponse, BaseLLMProvider)
- `app/services/llm/gemini_provider.py` - Gemini implementation with modern SDK
- `app/services/llm/simulated_provider.py` - Development fallback
- `app/services/llm/factory.py` - Provider creation

**Interview System:**
- `app/prompts/interview_prompt.py` - Dynamic system prompt builder
- `app/prompts/interview_functions.py` - Function definitions for LLM
- `app/prompts/prerequisites.py` - Action dependency graph

**API:**
- `app/api/routes.py` - API endpoints (updated to use Message objects)
- `app/core/app_state.py` - App initialization (uses factory)

## Next Steps After Testing

Once testing confirms function calling works:

1. **Phase 3: ConversationService**
   - Implement conversation management service
   - Handle function call processing
   - Track interview state and completeness

2. **Phase 4: InterviewService**
   - Generate personalized video guidelines
   - Manage interview completion workflow
   - Integration with graphiti for knowledge tracking

3. **Phase 5: Frontend Integration**
   - Real-time extraction feedback
   - Progress visualization
   - Prerequisite-aware UI

## Notes

- **Local .env changes**: Keep your API key local, don't commit to git
- **Model selection**:
  - Conversation: `gemini-flash-lite-latest` (fast, free)
  - Extraction: `gemini-2.5-flash` (stable function calling, accurate)
  - Analysis/Reports: `gemini-2.5-pro` (most capable)
- **Rate limits**: Free tier is generous but not unlimited
- **Hebrew support**: Gemini 2.5 has excellent Hebrew language understanding
- **Function calling**: Modern SDK uses `types.Tool` and `types.FunctionDeclaration`

## Contact

If you encounter issues with the Gemini implementation:
1. Check logs in `backend/` directory
2. Verify .env configuration
3. Test with simulated provider first to isolate API issues
4. Review test output for specific error messages
