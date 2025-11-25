# Development Quick Start Guide

Quick ways to bypass the conversation and test features at different stages.

## Quick Commands

### 1. Seed "Guidelines Ready" Scenario (Most Common)

```bash
curl -X POST "http://localhost:8000/api/dev/seed/guidelines_ready?family_id=test123"
```

Then open: `http://localhost:3000/?family=test123`

This will:
- ✅ Load rich conversation data
- ✅ Trigger guideline generation (takes ~60s)
- ✅ Show the video guidelines card
- ✅ Enable video upload

### 2. Seed Early Conversation

```bash
curl -X POST "http://localhost:8000/api/dev/seed/early_conversation?family_id=test123"
```

### 3. Seed Videos Uploaded

```bash
curl -X POST "http://localhost:8000/api/dev/seed/videos_uploaded?family_id=test123"
```

### 4. List All Available Scenarios

```bash
curl "http://localhost:8000/api/dev/scenarios" | jq
```

### 5. Reset a Session

```bash
curl -X DELETE "http://localhost:8000/api/dev/reset/test123"
```

## Using the Interactive Script

```bash
cd backend
./test_dev_seed.sh
```

## Available Scenarios

### `early_conversation`
- **Purpose**: Test early interview stage
- **Completeness**: 30%
- **Messages**: 3
- **What you get**: Basic child info, no guidelines yet

### `guidelines_ready` ⭐ (Most Used)
- **Purpose**: Test video upload and guidelines display
- **Completeness**: 80%
- **Messages**: 12
- **What you get**:
  - Rich child development data
  - Video guidelines will auto-generate (~60s)
  - Video upload enabled
  - Guidelines card appears

### `videos_uploaded`
- **Purpose**: Test video analysis flow
- **Completeness**: 85%
- **Messages**: 15
- **What you get**:
  - Everything from `guidelines_ready`
  - Simulated 3 videos uploaded
  - Ready for analysis testing

## Typical Development Workflow

1. **Start backend** (if not running):
   ```bash
   cd backend
   source venv/bin/activate
   python -m app.main
   ```

2. **Seed your test scenario**:
   ```bash
   curl -X POST "http://localhost:8000/api/dev/seed/guidelines_ready?family_id=dev1"
   ```

3. **Open frontend** with the test family:
   ```
   http://localhost:3000/?family=dev1
   ```

4. **Work on your feature** - the data is already loaded!

5. **Reset when needed**:
   ```bash
   curl -X DELETE "http://localhost:8000/api/dev/reset/dev1"
   ```

## Tips

- Use **different family IDs** for different tests: `dev1`, `dev2`, `test_upload`, etc.
- The **guidelines take ~60 seconds** to generate (it's a real LLM call)
- **Reset sessions** between tests to avoid stale state
- Check backend logs for generation progress

## Frontend Integration (Optional)

You can add a dev panel to your frontend to trigger these endpoints from the UI.

Add to `App.jsx`:

```javascript
// In development only
{import.meta.env.DEV && (
  <div style={{position: 'fixed', top: 10, right: 10, background: '#f0f0f0', padding: 10}}>
    <button onClick={() => fetch('http://localhost:8000/api/dev/seed/guidelines_ready?family_id=' + familyId, {method: 'POST'})}>
      🌱 Seed Guidelines Ready
    </button>
  </div>
)}
```

## Troubleshooting

### "Guidelines still generating after 2 minutes"

Check backend logs for errors. Guidelines generation can fail if:
- Gemini API key is missing
- Schema errors (should be fixed now!)
- Network issues

### "Session not found"

The family_id in the URL must match what you seeded:
- ❌ `http://localhost:3000/?family=wrong_id`
- ✅ `http://localhost:3000/?family=test123`

### "Backend says 404 on /dev/seed"

Make sure:
1. Backend is running
2. `ENVIRONMENT=development` in your `.env`
3. Backend has been restarted after adding dev routes
