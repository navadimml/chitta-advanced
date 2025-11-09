# 🎬 Demo Mode - Interactive Demo in Real UI

## Overview

Demo Mode allows users to experience a complete Chitta journey through a scripted, interactive demo that runs in the **real app UI**. It's triggered by natural language ("show me a demo" / "הראה לי דמו") and showcases the full flow from interview to artifact generation.

**Key Features:**
- ✅ Natural language trigger detection
- ✅ Realistic Chitta-led conversation (15 messages)
- ✅ Auto-play with timed delays (2-4 seconds between messages)
- ✅ Real artifact generation (baseline_video_guidelines)
- ✅ Demo mode card with visual indicators
- ✅ Full state management (pause, skip, stop)

---

## Architecture

### Backend Components

#### 1. DemoOrchestratorService
**Location:** `backend/app/services/demo_orchestrator_service.py`

**Core Models:**
```python
class DemoMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str  # Hebrew text
    delay_ms: int = 2000  # Delay before this message
    trigger_artifact: Optional[str] = None
    card_hint: Optional[str] = None

class DemoScenario(BaseModel):
    scenario_id: str
    name: str  # "דאגות שפה"
    name_en: str  # "Language Development Concerns"
    description: str
    duration_estimate: str  # "2-3 דקות"
    child_profile: Dict[str, Any]  # Mock child data
    messages: List[DemoMessage]  # Scripted conversation
    artifact_trigger_at_step: int = 6
```

**Key Methods:**
- `detect_demo_intent(message: str)` - Detects demo trigger phrases
- `start_demo(scenario_id: str)` - Initializes demo session
- `get_next_step(demo_family_id: str)` - Advances to next message
- `stop_demo(demo_family_id: str)` - Ends demo session

#### 2. API Endpoints
**Location:** `backend/app/api/routes.py`

**Endpoints:**

1. **POST /chat/send** (Enhanced)
   - Detects demo intent in user messages
   - Returns demo mode response if triggered

   ```python
   # Demo response structure:
   {
       "response": "שלום, אני רוצה לדבר על הבן שלי",
       "stage": "demo",
       "ui_data": {
           "demo_mode": True,
           "demo_family_id": "demo_language_concerns_1234567890",
           "demo_scenario": {...},
           "cards": [{...}],
           "suggestions": ["המשך דמו", "עצור דמו"],
           "progress": 0
       }
   }
   ```

2. **POST /demo/start**
   - Manually start a demo
   - Request: `{"scenario_id": "language_concerns"}`
   - Response: First message + demo card

3. **GET /demo/{demo_family_id}/next**
   - Get next message in sequence
   - Auto-triggers artifact generation at step 12
   - Returns: message, demo_card, artifact_generated, is_complete

4. **POST /demo/{demo_family_id}/stop**
   - Stop demo and clean up state
   - Returns: `{"success": true, "message": "..."}`

---

## Demo Scenario: Language Concerns

### Conversation Flow (16 messages)

**Pattern:** Chitta LEADS the conversation (key insight!)

```
Step 1: Parent initiates
"שלום, אני רוצה לדבר על הבן שלי"

Step 2: Chitta asks for name
"שלום! אני צ'יטה 🌟 אשמח מאוד להכיר ולעזור. מה שמו?"

Step 3: Parent shares name + age
"שמו דניאל, הוא בן 3 וחצי"

Step 4: Chitta starts with STRENGTHS (not problems!)
"נעים להכיר את דניאל! לפני שנדבר על אתגרים, בואי נתחיל מהדברים הטובים..."

Step 5: Parent shares strengths
"הוא מאוד אוהב לשחק עם קוביות..."

Step 6-11: Chitta explores concerns, context, impact, goals

Step 12: Parent shares goals → TRIGGERS ARTIFACT GENERATION
"אני רוצה לעזור לו להרגיש בטוח בתקשורת..."
→ generates: baseline_video_guidelines

Step 13: Chitta acknowledges richness and offers guidelines
"תודה שספרת לי על דניאל. אני מרגישה שיש לי תמונה עשירה..."

Step 14-16: Parent accepts, guidelines ready, demo completes
```

### Child Profile (Mock Data)
```python
{
    "child_name": "דניאל",
    "age": 3.5,
    "gender": "male",
    "primary_concerns": ["שפה", "תקשורת"],
    "concern_details": "דניאל מדבר פחות מילדים אחרים...",
    "strengths": "אוהב לשחק עם קוביות, ממוקד, יצירתי",
    "developmental_history": "התפתחות תקינה עד גיל שנתיים",
    "family_context": "משפחה תומכת, דוברי עברית בבית",
    "parent_goals": "לעזור לו להרגיש בטוח בתקשורת"
}
```

---

## Demo Card Structure

### Visual Design
```python
{
    "card_type": "demo_mode",
    "priority": 1000,  # Always on top
    "title": "🎬 מצב הדגמה",
    "title_en": "DEMO MODE",
    "body": "זו סימולציה - לא מידע אמיתי | דאגות שפה",
    "step_indicator": "שלב 5 / 16",
    "progress": 31,  # percentage
    "flashing": True,  # Visual cue
    "actions": ["stop_demo", "pause_demo", "skip_step"]
}
```

### Frontend Rendering Requirements

**Visual Indicators:**
1. **Flashing Banner** - Top of screen, bright color (yellow/orange)
2. **Border** - Colored border around entire conversation
3. **Card Badge** - "🎬 DEMO" badge on every message
4. **Watermark** - Semi-transparent "DEMO MODE" text
5. **Progress Bar** - Show current step / total steps

**Styling Example:**
```css
.demo-mode {
    border: 3px solid #ff9800;
    animation: pulse 2s infinite;
}

.demo-banner {
    background: linear-gradient(90deg, #ff9800, #ffc107);
    color: white;
    font-weight: bold;
    padding: 12px;
    text-align: center;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}
```

---

## Frontend Integration Guide

### Step 1: Detect Demo Mode

```typescript
// In chat message handler
const response = await fetch('/chat/send', {
    method: 'POST',
    body: JSON.stringify({
        family_id: currentFamilyId,
        message: userMessage
    })
});

const data = await response.json();

if (data.ui_data.demo_mode) {
    // Enter demo mode
    startDemoMode(data);
}
```

### Step 2: Auto-Play System

```typescript
async function playNextDemoStep(demoFamilyId: string) {
    const response = await fetch(`/demo/${demoFamilyId}/next`);
    const step = await response.json();

    // Wait for delay
    await sleep(step.message.delay_ms);

    // Display message
    addMessageToUI(step.message);

    // Check for artifact
    if (step.artifact_generated) {
        showArtifactNotification(step.artifact_generated);
    }

    // Show card hint
    if (step.card_hint) {
        updateContextCard(step.card_hint);
    }

    // Continue or complete
    if (!step.is_complete && !demoPaused) {
        playNextDemoStep(demoFamilyId);
    }
}
```

### Step 3: Demo Controls

```typescript
interface DemoControls {
    pause: () => void;
    resume: () => void;
    skip: () => void;
    stop: () => Promise<void>;
}

const demoControls: DemoControls = {
    pause: () => { demoPaused = true; },
    resume: () => {
        demoPaused = false;
        playNextDemoStep(currentDemoId);
    },
    skip: () => { playNextDemoStep(currentDemoId); },
    stop: async () => {
        await fetch(`/demo/${currentDemoId}/stop`, { method: 'POST' });
        exitDemoMode();
    }
};
```

### Step 4: Visual Indicators

```typescript
function enterDemoMode(data: DemoStartResponse) {
    // Add demo class to app
    document.body.classList.add('demo-mode');

    // Render demo banner
    renderDemoBanner({
        scenario: data.scenario.name,
        duration: data.scenario.duration,
        onStop: () => demoControls.stop()
    });

    // Render demo card
    renderDemoCard(data.demo_card);

    // Start auto-play
    playNextDemoStep(data.demo_family_id);
}

function exitDemoMode() {
    document.body.classList.remove('demo-mode');
    removeDemoBanner();
    showMessage("Demo stopped. Ready to start your real conversation! 💙");
}
```

---

## Testing

### Backend Tests
**Location:** `backend/test_demo_api.py`

**Test Coverage:**
1. ✅ Demo intent detection
2. ✅ Demo start flow
3. ✅ Step progression
4. ✅ Artifact generation
5. ✅ Demo stop
6. ✅ Complete flow (16 steps)

**Run Tests:**
```bash
cd backend
python test_demo_api.py
```

**Expected Output:**
```
✅ Test 1 PASSED: All intent detection cases correct
✅ Test 2 PASSED: Demo started successfully
✅ Test 3 PASSED: Demo progression working
✅ Test 4 PASSED: Artifact generation triggered
✅ Test 5 PASSED: Demo properly stopped
✅ Test 6 PASSED: Complete demo flow successful
```

---

## Key Design Decisions

### 1. Chitta Leads the Conversation
**Insight from `interview_prompt.py`:**
- Chitta is the INTERVIEWER who drives conversation
- Asks ONE question per turn
- Starts with STRENGTHS before concerns
- Uses warm, natural Hebrew
- Background function calls are invisible to user

**Why This Matters:**
Demo scenarios must follow this pattern to feel authentic. Parent doesn't drive the conversation - Chitta does.

### 2. Real Artifact Generation
Demo doesn't mock artifacts - it generates real baseline_video_guidelines using the actual ArtifactGenerationService. This ensures:
- Realistic timing (LLM generation takes a few seconds)
- Authentic content (actual markdown guidelines)
- Full Wu Wei integration (artifact stored in session)

### 3. Scripted but Authentic
Messages are pre-written but follow Chitta's actual patterns:
- Natural Hebrew phrasing
- Appropriate delays (2-4 seconds)
- Realistic conversation depth
- Card hints at right moments

### 4. State Management
Demo uses special `demo_*` family IDs:
- Isolated from real sessions
- Easy to identify and clean up
- Can run multiple demos simultaneously
- Proper state tracking (current_step, is_active, is_paused)

---

## Future Enhancements

### Phase 2: Multiple Scenarios
```python
scenarios = {
    "language_concerns": {...},      # Current
    "social_difficulties": {...},    # New
    "behavioral_challenges": {...},  # New
    "motor_development": {...}       # New
}
```

### Phase 3: Speed Controls
```typescript
interface DemoSpeed {
    slow: 4000,    // 4 seconds between messages
    normal: 2000,  // 2 seconds (default)
    fast: 1000,    // 1 second
    instant: 0     // No delay
}
```

### Phase 4: Demo Selection UI
Allow users to choose which scenario to demo:
```
┌─────────────────────────────────┐
│  בחרי תרחיש להדגמה              │
├─────────────────────────────────┤
│  🗣️ דאגות שפה (2-3 דקות)       │
│  👥 קשיים חברתיים (3-4 דקות)   │
│  ⚡ אתגרים התנהגותיים (3-4 דקות)│
└─────────────────────────────────┘
```

### Phase 5: Annotations
Show internal Chitta decision-making:
```
"נשמע שדניאל יצירתי וממוקד - זה נפלא!"
                                    ┌────────────────┐
                                    │ 🧠 Chitta:     │
                                    │ Acknowledging  │
                                    │ strengths      │
                                    │ before asking  │
                                    │ about concerns │
                                    └────────────────┘
```

---

## API Documentation Summary

### POST /chat/send (Enhanced)
Automatically detects demo intent and starts demo if triggered.

**Request:**
```json
{
    "family_id": "user_123",
    "message": "show me a demo"
}
```

**Response (Demo Mode):**
```json
{
    "response": "שלום, אני רוצה לדבר על הבן שלי",
    "stage": "demo",
    "ui_data": {
        "demo_mode": true,
        "demo_family_id": "demo_language_concerns_1234567890",
        "demo_scenario": {
            "id": "language_concerns",
            "name": "דאגות שפה",
            "duration": "2-3 דקות",
            "total_steps": 16
        },
        "cards": [{
            "card_type": "demo_mode",
            "title": "🎬 מצב הדגמה",
            "progress": 0
        }]
    }
}
```

### POST /demo/start
Manually start a demo (alternative to natural language trigger).

**Request:**
```json
{
    "scenario_id": "language_concerns"
}
```

### GET /demo/{demo_family_id}/next
Get next step in demo flow.

**Response:**
```json
{
    "step": 5,
    "total_steps": 16,
    "message": {
        "role": "assistant",
        "content": "נשמע שדניאל יצירתי...",
        "delay_ms": 2500
    },
    "artifact_generated": null,
    "card_hint": "conversation_depth_card",
    "demo_card": {...},
    "is_complete": false
}
```

### POST /demo/{demo_family_id}/stop
Stop demo and clean up.

**Response:**
```json
{
    "success": true,
    "message": "Demo stopped. Ready to start your real conversation! 💙"
}
```

---

## Troubleshooting

### Demo Not Starting
**Check:**
1. Is trigger phrase in `detect_demo_intent()` list?
2. Is `app_state.initialized` true?
3. Check backend logs for errors

### Demo Stuck
**Fix:**
- Call POST `/demo/{id}/stop` to reset
- Check `active_demos` dict in DemoOrchestratorService

### Artifact Not Generating
**Verify:**
1. Demo reaches step 12 (artifact trigger point)
2. `ArtifactGenerationService` is initialized
3. LLM is available and responding

---

## Summary

**✅ Backend Complete:**
- DemoOrchestratorService implemented
- API endpoints working
- Tests passing
- Real artifact generation

**⏳ Frontend Needed:**
- Demo mode detection
- Auto-play system
- Visual indicators (banner, border, card)
- Demo controls (pause, skip, stop)

**🎯 User Experience:**
1. User types "show me a demo"
2. App enters demo mode (visual indicators)
3. Conversation auto-plays (2-4s delays)
4. Artifact generated at right moment
5. User can stop anytime
6. Seamless transition to real conversation

**Ready for stakeholder demos, onboarding, and marketing! 🚀**
