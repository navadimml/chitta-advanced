# How to Use the Dev Panel 🛠️

## What is it?

A **visual UI** in your frontend that lets you:
- ✅ See all available test scenarios
- ✅ Click buttons to seed data instantly
- ✅ Switch between test sessions
- ✅ Reset sessions when done
- ✅ No need to remember commands or URLs!

## Quick Start

### 1. Restart Backend

```bash
# Stop backend (Ctrl+C), then:
cd backend
source venv/bin/activate
python -m app.main
```

Wait for: `✅ Chitta Backend ready!`

### 2. Start Frontend

```bash
# In new terminal:
npm run dev
```

### 3. Open App

Go to: `http://localhost:3000`

You'll see a **purple "Dev Tools" button** in the top-left corner!

---

## Using the Dev Panel

### **Open the Panel**

Click the **purple "Dev Tools"** button in the top-left:

```
┌─────────────────┐
│ 🔧 Dev Tools ▼  │
└─────────────────┘
```

The panel opens with 3 sections:

---

### **Section 1: Current Session**

Shows which test session you're currently using:

```
┌────────────────────────────────┐
│ Current Session:               │
│ guidelines_ready_abc123        │
└────────────────────────────────┘
```

---

### **Section 2: Seed New Scenario**

Click any button to create a new test session:

```
┌────────────────────────────────────────────┐
│ 📦 Seed New Scenario                      │
│                                            │
│ ┌────────────────────────────────────────┐│
│ │ ⭐ Guidelines Ready                     ││
│ │ Rich knowledge - guidelines generate   ││
│ │ 📊 80%  💬 12 msgs                     ││
│ └────────────────────────────────────────┘│
│                                            │
│ ┌────────────────────────────────────────┐│
│ │ Early Conversation                      ││
│ │ Basic info, no guidelines yet          ││
│ │ 📊 30%  💬 3 msgs                      ││
│ └────────────────────────────────────────┘│
│                                            │
│ ┌────────────────────────────────────────┐│
│ │ Videos Uploaded                         ││
│ │ Simulated videos ready for analysis    ││
│ │ 📊 85%  💬 15 msgs                     ││
│ └────────────────────────────────────────┘│
└────────────────────────────────────────────┘
```

**When you click a button:**
1. ✅ New session created with that scenario's data
2. ✅ Page automatically reloads with the new session
3. ✅ Guidelines start generating (~60 seconds)

---

### **Section 3: Recent Sessions**

Shows all your recent test sessions:

```
┌────────────────────────────────────────────┐
│ 🔄 Recent Sessions             Clear All   │
│                                            │
│ ┌────────────────────────────────────────┐│
│ │ guidelines_ready_abc123         🔄 🗑 ││
│ │ Rich knowledge - guidelines generate   ││
│ └────────────────────────────────────────┘│
│                                            │
│ ┌────────────────────────────────────────┐│
│ │ early_conversation_xyz789       🔄 🗑 ││
│ │ Basic info only                        ││
│ └────────────────────────────────────────┘│
└────────────────────────────────────────────┘
```

**Buttons:**
- 🔄 = Switch to this session
- 🗑 = Delete this session

---

## Example Workflow

### **Testing Video Upload**

1. **Open Dev Panel** (purple button top-left)

2. **Click "⭐ Guidelines Ready"**
   - Creates new session with rich data
   - Page reloads automatically

3. **Wait ~60 seconds**
   - Guidelines generate in background
   - "Video Guidelines" card appears

4. **Test video upload!**
   - Upload button is now enabled
   - Full context is loaded

5. **Done testing? Click 🗑 to delete**

---

### **Testing Multiple Scenarios**

1. **Click "Guidelines Ready"** → Test feature A
2. **Click "Early Conversation"** → Test feature B
3. **Switch back** → Click 🔄 on first session
4. **Clean up** → Click "Clear All" when done

---

## Features

### ✅ **No Commands to Remember**
Everything is visual - just click buttons!

### ✅ **Automatic URL Updates**
When you seed a scenario, the URL updates automatically:
- Before: `http://localhost:3000`
- After: `http://localhost:3000/?family=guidelines_ready_abc123`

### ✅ **Session History**
All your recent test sessions are saved and easy to switch between.

### ✅ **One-Click Reset**
Delete test sessions when you're done - keeps things clean.

### ✅ **Dev Mode Only**
The panel only appears in development (`npm run dev`), not in production.

---

## Tips

### **Use Guidelines Ready for Most Testing**
It's marked with ⭐ because it's the most useful - gives you:
- Full conversation context
- Guidelines generation
- Video upload enabled

### **Create Multiple Sessions for Different Tests**
- One for testing video upload
- One for testing cards
- One for testing early conversation

### **Session Names are Unique**
Each time you seed a scenario, it gets a unique ID like:
- `guidelines_ready_k7x2m9`
- `early_conversation_p4n8q1`

### **Guidelines Take Time**
After seeding "Guidelines Ready", wait ~60 seconds for the LLM to generate them. You'll see a "preparing" card, then the real card appears.

---

## Troubleshooting

### **"Dev Tools button doesn't appear"**

**Solution**: Make sure you're running in dev mode:
```bash
npm run dev  # NOT npm run build
```

### **"Scenarios don't load"**

**Solution**: Backend might not be running or dev routes not loaded:
```bash
# Restart backend
cd backend
python -m app.main
```

### **"Session doesn't switch"**

The page should reload automatically. If not, manually refresh the browser.

### **"Guidelines stuck in generating"**

Check backend logs for errors. Common issues:
- Missing `GEMINI_API_KEY` in `.env`
- Backend crashed during generation
- Network issues

---

## What You Get

### **Guidelines Ready** (⭐ Most Used)
- Child name: דני
- Age: 3
- Concerns: Speech, social
- Full developmental history
- 12 conversation messages
- 80% completeness
- → Triggers guideline generation

### **Early Conversation**
- Child name: דני
- Age: 3
- Basic concerns only
- 3 conversation messages
- 30% completeness
- → No guidelines yet

### **Videos Uploaded**
- Everything from "Guidelines Ready"
- Plus: 3 simulated videos uploaded
- → Ready for analysis testing

---

## That's It!

**No more:**
- ❌ Remembering curl commands
- ❌ Typing family IDs manually
- ❌ Switching URLs
- ❌ Going through full conversations

**Now:**
- ✅ Click button
- ✅ Test instantly
- ✅ Switch sessions easily
- ✅ Clean up when done

**Just click and test!** 🚀
