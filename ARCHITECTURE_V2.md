# Chitta Architecture Guide v2.0

**Last Updated**: November 2, 2025
**Purpose**: Complete architectural blueprint for conversation-first AI applications

---

## 🎯 Design Philosophy

Chitta is built on a **conversation-first, AI-curated interface** that solves chat's fundamental problem: great for flow, terrible for random access.

### Core Innovation

The app uses a **two-layer system**:
1. **Conversation Layer** - Primary interface for all interactions
2. **Contextual Surface** - AI-managed persistent context (max 2-4 cards)
3. **Smart Suggestions** - On-demand help via lightbulb button

**Key Principle**: Users never navigate. The AI brings relevant information to them.

---

## 🏗️ Domain-Agnostic Architecture

### How to Adapt This App to Any Domain

Chitta's architecture is **highly generalizable**. The core patterns can power:
- **Therapy/Counseling Apps** - Patient journeys, session notes, progress tracking
- **Education Platforms** - Student progress, assignments, learning paths
- **Customer Support** - Ticket management, knowledge base, FAQ
- **Healthcare** - Patient intake, symptom tracking, care coordination
- **Legal Services** - Case management, document review, client communication
- **Financial Advisory** - Goal tracking, document uploads, recommendations

### The Three-Layer Pattern

```
┌─────────────────────────────────────────────────────────┐
│                   APPLICATION CORE                      │
│                 (Domain-Agnostic)                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. Conversation Engine                                │
│     - Message flow with delays                         │
│     - Typing indicators                                │
│     - Auto-scroll                                      │
│     - User/AI message differentiation                  │
│                                                         │
│  2. Contextual Surface Manager                         │
│     - Card generation (max 2-4)                        │
│     - Card click actions → Deep views                  │
│     - Color-coded status system                        │
│     - Icon-driven visual language                      │
│                                                         │
│  3. Suggestions System                                 │
│     - Lightbulb trigger                                │
│     - Bottom sheet popup                               │
│     - Contextual action buttons                        │
│                                                         │
│  4. Deep View Router                                   │
│     - Modal overlay system                             │
│     - Slide-up animation                               │
│     - Dynamic component loading                        │
│     - Close/dismiss handling                           │
│                                                         │
│  5. State Management                                   │
│     - Master state object                              │
│     - Scenario/journey stage tracking                  │
│     - Progress indicators                              │
│     - Active artifacts list                            │
│                                                         │
│  6. API Service Layer                                  │
│     - Scenario loading                                 │
│     - Message handling                                 │
│     - Action triggering                                │
│     - File uploads                                     │
│                                                         │
└─────────────────────────────────────────────────────────┘
         ↓ Implemented via Configuration ↓
┌─────────────────────────────────────────────────────────┐
│                  DOMAIN LAYER                           │
│              (Customizable per Use Case)                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  • Scenarios (workflow states)                         │
│  • MasterState schema                                  │
│  • Card types and actions                              │
│  • Deep view components                                │
│  • Conversation content                                │
│  • Language/locale                                     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 Core Components

### 1. App Container (`App.jsx`)

**Responsibility**: Orchestrate all major systems

```javascript
State Management:
- scenarios[]          // Available workflow states
- currentScenario      // Active state key
- masterState          // Domain-specific state object
- messages[]           // Conversation history
- contextCards[]       // AI-curated cards (max 2-4)
- suggestions[]        // Smart action suggestions
- isTyping             // Typing indicator state
- showSuggestions      // Suggestions popup visibility
- activeDeepView       // Current modal view

Handlers:
- handleScenarioChange()    // Switch workflow state
- handleSend()              // Process user message
- handleCardClick()         // Open deep view from card
- handleSuggestionClick()   // Send suggestion as message
- handleCloseDeepView()     // Dismiss modal
```

**Domain Adaptation**: Replace `scenarios` with your workflow states (e.g., "onboarding", "active_case", "completed")

---

### 2. ConversationTranscript (`ConversationTranscript.jsx`)

**Responsibility**: Display message history with animations

**Features**:
- Auto-scroll to latest message
- Animated message appearance (fadeIn)
- User vs AI visual differentiation
- Typing indicator (3 bouncing dots)
- RTL support for Hebrew/Arabic
- Pre-line whitespace support for multi-line messages

**Domain Adaptation**: Change color scheme, add message types (system, notification), customize bubble styles

```javascript
Message Structure:
{
  sender: 'user' | 'chitta',  // Change 'chitta' to your AI name
  text: string,
  delay: number               // Animation delay in ms
}
```

---

### 3. ContextualSurface (`ContextualSurface.jsx`)

**Responsibility**: AI-curated context cards (max 2-4)

**Features**:
- 10 color-coded status types
- Click-to-action pattern
- Icon-driven visual language
- Hover effects
- Chevron indicator for actionable cards

**Domain Adaptation**: Define your own status types and color palette

```javascript
Card Structure:
{
  icon: 'LucideIconName',     // From lucide-react
  title: string,              // Primary text
  subtitle: string,           // Secondary text
  status: StatusKey,          // Color/urgency indicator
  action?: ActionKey          // Optional click handler
}

Status Types (Customizable):
- completed   → Green (success, done)
- pending     → Orange (waiting, needs attention)
- action      → Blue (clickable action)
- new         → Purple (new information)
- processing  → Yellow (in progress)
- instruction → Indigo (guidance)
- expert      → Teal (profile/person)
- upcoming    → Pink (scheduled)
- active      → Violet (currently active)
- progress    → Cyan (tracking progress)
```

---

### 4. InputArea (`InputArea.jsx`)

**Responsibility**: User input with suggestions trigger

**Features**:
- Text input with Enter key support
- Lightbulb button (conditional)
- Send button with gradient
- Rounded pill design
- RTL input support

**Domain Adaptation**: Add voice input, file attach button, formatting toolbar

---

### 5. SuggestionsPopup (`SuggestionsPopup.jsx`)

**Responsibility**: Contextual action suggestions

**Features**:
- Bottom sheet modal
- Backdrop dismiss
- Icon + text buttons
- Color-coded by category
- Slide-up animation

**Domain Adaptation**: Change trigger icon, customize button layouts, add categories

```javascript
Suggestion Structure:
{
  icon: 'LucideIconName',
  text: string,
  color: 'bg-{color}-500'    // Tailwind class
}
```

---

### 6. DeepViewManager (`DeepViewManager.jsx`)

**Responsibility**: Route to modal deep views

**Pattern**:
```javascript
const viewComponents = {
  actionKey: ComponentName,
  ...
};

// Dynamic component rendering
const ViewComponent = viewComponents[activeView];
return <ViewComponent onClose={onClose} data={viewData} />;
```

**Domain Adaptation**: Create your own deep view components, map to action keys

---

### 7. Deep View Components (Example: `ReportView.jsx`)

**Responsibility**: Full-screen modal for detailed content

**Standard Pattern**:
```jsx
<div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-end md:items-center justify-center p-4" onClick={onClose}>
  <div className="bg-white rounded-t-3xl md:rounded-3xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col animate-slideUp" onClick={(e) => e.stopPropagation()}>

    {/* Header with gradient */}
    <div className="bg-gradient-to-r from-indigo-500 to-purple-500 text-white p-5 flex items-center justify-between">
      <h3 className="text-lg font-bold">View Title</h3>
      <button onClick={onClose} className="p-2 hover:bg-white hover:bg-opacity-20 rounded-full transition">
        <X className="w-6 h-6" />
      </button>
    </div>

    {/* Scrollable Content */}
    <div className="flex-1 overflow-y-auto p-5 space-y-4">
      {/* Content here */}
    </div>

  </div>
</div>
```

**Domain Adaptation**: Create domain-specific views (DocumentViewer, FormEditor, Analytics Dashboard, etc.)

---

## 🔄 Data Flow

### Message Flow

```
User types message
        ↓
handleSend()
        ↓
Add user message to messages[]
        ↓
Set isTyping = true
        ↓
api.sendMessage() [Mock or Real Backend]
        ↓
Set isTyping = false
        ↓
Add AI response to messages[]
        ↓
Auto-scroll to bottom
```

### Card Click Flow

```
User clicks context card
        ↓
handleCardClick(action)
        ↓
api.triggerAction(action)
        ↓
Set activeDeepView = action
        ↓
DeepViewManager renders modal
        ↓
User closes modal
        ↓
Set activeDeepView = null
```

### Scenario Change Flow

```
User selects new scenario (via DemoControls)
        ↓
handleScenarioChange(scenarioKey)
        ↓
api.getScenario(scenarioKey)
        ↓
Update masterState, contextCards, suggestions
        ↓
Clear messages[]
        ↓
Replay messages with delays
        ↓
Animate typing indicator per message
```

---

## 🎨 State Schema

### MasterState Structure (Domain-Specific Example)

```javascript
{
  journey_stage: string,           // Current workflow state

  // Entity Data (customize per domain)
  child: {
    name: string,
    age: number
  },

  // Progress Tracking
  progress: {
    interview: number,             // 0-100
    videos: number,
    analysis: number
  },

  // Active Items
  active_artifacts: [
    {
      type: string,                // 'report', 'video', 'document'
      status: string,              // 'new', 'viewing', 'processing'
      ...
    }
  ],

  // Milestones Completed
  completed_milestones: string[]   // ['interview', 'video_1', ...]
}
```

**Domain Adaptation**: Replace `child` with your entity (e.g., `patient`, `student`, `customer`, `case`)

---

## 🔌 API Service Layer

### Mock API (`services/api.js`)

**Purpose**: Simulate backend during development

**Methods**:
```javascript
class ChittaAPI {
  async getScenario(scenarioKey)     // Load workflow state
  async getAllScenarios()             // List all states
  async sendMessage(message)          // Process user input
  async triggerAction(actionKey)      // Handle card clicks
  async uploadFile(file)              // File upload
}
```

**Production Migration**:
```javascript
// Replace mock delays with real API calls
async sendMessage(message) {
  const response = await fetch('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ message }),
    headers: { 'Content-Type': 'application/json' }
  });
  return response.json();
}
```

---

## 🧩 Extensibility Points

### Adding a New Scenario

1. **Define in `api.js`:**
```javascript
SCENARIOS.newScenario = {
  name: 'Display Name',
  masterState: { /* your state */ },
  messages: [
    { sender: 'chitta', text: '...', delay: 0 }
  ],
  contextCards: [
    { icon: 'Icon', title: '...', status: 'pending', action: 'key' }
  ],
  suggestions: [
    { icon: 'Icon', text: '...', color: 'bg-blue-500' }
  ]
}
```

2. **Add to DemoControls dropdown** (if using demo mode)

### Adding a New Deep View

1. **Create component** in `src/components/deepviews/NewView.jsx`:
```jsx
export default function NewView({ viewKey, onClose, data }) {
  return (
    <div className="fixed inset-0..." onClick={onClose}>
      {/* Standard modal pattern */}
    </div>
  );
}
```

2. **Register in DeepViewManager:**
```javascript
import NewView from './deepviews/NewView';

const viewComponents = {
  ...existing,
  newAction: NewView
};
```

3. **Add action to context card:**
```javascript
contextCards: [
  { icon: 'Icon', title: 'New Feature', status: 'action', action: 'newAction' }
]
```

### Adding a New Card Status Type

1. **Define color in ContextualSurface.jsx:**
```javascript
const getStatusColor = (status) => {
  const colors = {
    ...existing,
    myStatus: 'bg-emerald-50 border-emerald-200 text-emerald-700'
  };
  return colors[status] || 'bg-gray-50...';
};
```

2. **Use in scenario:**
```javascript
{ icon: 'Icon', title: 'Custom', status: 'myStatus' }
```

---

## 🌐 Internationalization

### Current Implementation

- **RTL Support**: `dir="rtl"` on containers
- **Hebrew UI**: All text in Hebrew
- **Font**: System fonts with Hebrew support

### Adding New Locales

1. **Create language files:**
```javascript
// src/i18n/he.js
export default {
  app: {
    title: 'Chitta',
    subtitle: 'המסע ההתפתחותי של יוני'
  },
  ...
}

// src/i18n/en.js
export default {
  app: {
    title: 'Chitta',
    subtitle: "Yoni's Developmental Journey"
  },
  ...
}
```

2. **Implement i18n library** (e.g., react-i18next)

3. **Set `dir` dynamically:**
```jsx
<div dir={locale === 'he' || locale === 'ar' ? 'rtl' : 'ltr'}>
```

---

## 🚀 Migration to Production

### Step 1: Replace Mock API

```javascript
// Before (Mock)
export default new ChittaAPI();

// After (Real)
import axios from 'axios';

class ChittaAPI {
  constructor() {
    this.client = axios.create({
      baseURL: process.env.REACT_APP_API_URL,
      headers: { 'Content-Type': 'application/json' }
    });
  }

  async sendMessage(message) {
    const { data } = await this.client.post('/chat', { message });
    return data;
  }

  // ... other methods
}
```

### Step 2: Implement State Persistence

```javascript
// Save to backend on every state change
useEffect(() => {
  if (masterState) {
    api.saveMasterState(masterState);
  }
}, [masterState]);

// Load on mount
useEffect(() => {
  const loadState = async () => {
    const state = await api.loadMasterState();
    setMasterState(state);
  };
  loadState();
}, []);
```

### Step 3: Real-Time Message Streaming

```javascript
// Server-Sent Events for streaming AI responses
const handleSend = async (message) => {
  const userMsg = { sender: 'user', text: message };
  setMessages(prev => [...prev, userMsg]);

  const eventSource = new EventSource(`/api/chat/stream?message=${encodeURIComponent(message)}`);

  let accumulatedText = '';
  eventSource.onmessage = (event) => {
    accumulatedText += event.data;
    setMessages(prev => [
      ...prev.slice(0, -1),
      { sender: 'chitta', text: accumulatedText }
    ]);
  };

  eventSource.onerror = () => {
    eventSource.close();
  };
};
```

### Step 4: Add Authentication

```javascript
// Context provider
const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);

  // Login, logout, session management

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

// Protected routes
if (!user) return <Navigate to="/login" />;
```

---

## 🔒 Production Considerations

### Security
- Sanitize user input
- Implement rate limiting
- Use HTTPS only
- Encrypt sensitive data
- Add CORS policies

### Performance
- Lazy load deep view components
- Virtualize long message lists
- Debounce typing indicators
- Optimize animations for 60fps
- Cache scenario data

### Accessibility
- ARIA labels for all interactive elements
- Keyboard navigation
- Screen reader support
- Focus management in modals
- High contrast mode

### Monitoring
- Track scenario completion rates
- Log errors to service (Sentry, LogRocket)
- Monitor API response times
- Analytics for card click patterns
- A/B test conversation flows

---

## 📊 Scalability

### Horizontal Scaling
- Stateless frontend (React SPA)
- Backend API can scale independently
- Use CDN for static assets
- Load balancer for API servers

### Data Management
- **Graphiti** for temporal knowledge graphs (see GRAPHITI_INTEGRATION_GUIDE.md)
- **Redis** for session caching
- **PostgreSQL** for relational data
- **S3** for file uploads (videos, documents)

### Multi-Tenancy
- Namespace data by `group_id` or `tenant_id`
- Isolate scenarios per user/organization
- Custom branding per tenant

---

## 🎓 Learning Path for Developers

### To Adapt This App to Your Domain:

1. **Understand the Scenarios**
   - Map your workflow to scenarios (states)
   - Define what data each state needs

2. **Design Your MasterState**
   - What entity are you tracking? (child → patient, student, etc.)
   - What progress metrics matter?
   - What artifacts does the user create/view?

3. **Create Your Deep Views**
   - What detailed information needs full-screen?
   - What actions can users take?

4. **Define Your Card Types**
   - What contextual information is most important?
   - What statuses/urgencies exist?

5. **Build Your Conversations**
   - What does the AI say at each stage?
   - What questions does it ask?
   - What suggestions does it offer?

6. **Replace Mock API**
   - Implement backend endpoints
   - Connect to real data sources

7. **Customize Styling**
   - Change color palette
   - Adjust animations
   - Rebrand icons/logo

---

## 📚 Related Documentation

- **UI_UX_STYLE_GUIDE.md** - Complete visual design system
- **GRAPHITI_INTEGRATION_GUIDE.md** - Temporal knowledge graph architecture
- **CORE_INNOVATION_DETAILED.md** - The fundamental problem we solve

---

**This architecture is proven, production-ready, and domain-agnostic. The core patterns can power any conversation-first application.**
