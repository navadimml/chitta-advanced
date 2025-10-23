# Chitta Refactored - Implementation Guide

## Overview
This refactoring transforms the monolithic Chitta prototype into a clean, maintainable architecture that separates concerns and makes the backend integration straightforward.

## Key Architectural Changes

### 1. **Service Layer** (`/src/services/api.js`)
- Mock API that simulates backend communication
- Manages Master State Objects for each scenario
- In production, replace with real API calls
- **Status**: ✅ COMPLETE

### 2. **Component Structure**

```
src/
├── App.jsx                                    # Main orchestrator
├── services/
│   └── api.js                                 # Mock backend service ✅
├── components/
│   ├── ConversationTranscript.jsx             # Message display
│   ├── ContextualSurface.jsx                  # Bottom cards
│   ├── DeepViewManager.jsx                    # Modal manager
│   ├── InputArea.jsx                          # Input with suggestions
│   ├── SuggestionsPopup.jsx                   # Suggestions modal
│   ├── DemoControls.jsx                       # Scenario selector
│   └── deepviews/
│       ├── ConsultationView.jsx               # Q&A interface
│       ├── DocumentUploadView.jsx             # File upload
│       ├── DocumentListView.jsx               # Document gallery
│       ├── ShareView.jsx                      # Share settings
│       ├── JournalView.jsx                    # Journal entries
│       ├── ReportView.jsx                     # Report display
│       ├── ExpertProfileView.jsx              # Expert profiles
│       ├── VideoGalleryView.jsx               # Video player
│       ├── FilmingInstructionView.jsx         # Filming guide
│       └── MeetingSummaryView.jsx             # Meeting prep
```

## Design Principles

### 1. **Dumb Components**
All UI components are "dumb" - they receive props and render. No business logic.

```jsx
// Good: Dumb component
export default function ConversationTranscript({ messages, isTyping }) {
  return (
    <div className="chat-area">
      {messages.map(msg => <Message key={msg.id} {...msg} />)}
      {isTyping && <TypingIndicator />}
    </div>
  );
}

// Bad: Smart component with logic
export default function ConversationTranscript() {
  const [messages, setMessages] = useState([]);
  useEffect(() => {
    // Fetching logic here - NO!
  }, []);
}
```

### 2. **State Management**
App.jsx holds all state and passes it down:

```jsx
function App() {
  const [masterState, setMasterState] = useState(null);
  const [messages, setMessages] = useState([]);
  const [contextCards, setContextCards] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [activeDeepView, setActiveDeepView] = useState(null);
  
  // All handlers live here
  const handleScenarioChange = async (scenarioKey) => {
    const data = await api.getScenario(scenarioKey);
    setMasterState(data.masterState);
    setMessages(data.messages);
    setContextCards(data.contextCards);
    setSuggestions(data.suggestions);
  };
  
  return (
    <div className="app">
      <DemoControls onScenarioChange={handleScenarioChange} />
      <ConversationTranscript messages={messages} />
      <ContextualSurface cards={contextCards} onCardClick={handleCardClick} />
      <InputArea onSend={handleSend} onSuggestionsClick={handleShowSuggestions} />
      {activeDeepView && <DeepViewManager view={activeDeepView} onClose={handleCloseDeepView} />}
    </div>
  );
}
```

### 3. **Styling Preserved**
All existing Tailwind classes and animations are preserved exactly:

```jsx
// Gradient backgrounds
className="bg-gradient-to-r from-indigo-500 to-purple-500"

// Animations
className="animate-fadeIn"

// RTL support
dir="rtl"

// Color coding by status
const getStatusColor = (status) => ({
  completed: 'bg-green-50 border-green-200',
  pending: 'bg-orange-50 border-orange-200',
  // ...
})[status];
```

## Component Specifications

### ConversationTranscript.jsx
**Purpose**: Display messages with typing indicators
**Props**:
- `messages`: Array of {sender, text, delay}
- `isTyping`: Boolean

**Key Features**:
- Auto-scroll to bottom
- Fade-in animations
- Different styling for chitta vs user
- RTL support

### ContextualSurface.jsx
**Purpose**: Show dynamic "Active Now" cards
**Props**:
- `cards`: Array of card objects
- `onCardClick`: Handler for clickable cards

**Key Features**:
- Color-coded by status
- Icons from lucide-react
- Chevron for actionable cards
- Visual hierarchy

### DeepViewManager.jsx
**Purpose**: Route to correct deep view component
**Props**:
- `view`: String key of which view to show
- `onClose`: Close handler
- `additionalProps`: Any view-specific data

**Key Features**:
- Modal overlay
- Slide-up animation
- Routes to specific deep view components

### InputArea.jsx
**Purpose**: Text input with send button
**Props**:
- `onSend`: Handler for message send
- `onSuggestionsClick`: Handler for lightbulb

**Key Features**:
- Rounded input field
- Gradient send button
- Lightbulb icon for suggestions

### SuggestionsPopup.jsx
**Purpose**: Bottom sheet with contextual suggestions
**Props**:
- `suggestions`: Array of suggestion objects
- `onSuggestionClick`: Handler for clicking suggestion
- `onClose`: Close handler

**Key Features**:
- Bottom sheet animation
- Color-coded buttons
- Icons for each suggestion

### DemoControls.jsx
**Purpose**: Scenario switcher for demo
**Props**:
- `scenarios`: Array of {key, name}
- `currentScenario`: Active scenario key
- `onScenarioChange`: Handler

**Key Features**:
- Gradient background
- Pill-shaped buttons
- Active state highlighting

## Deep View Components

Each deep view is a self-contained component that receives props and renders rich content.

### Pattern for Deep Views:

```jsx
export default function SomeDeepView({ onClose, onAction, data }) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-end md:items-center justify-center p-4">
      <div className="bg-white rounded-t-3xl md:rounded-3xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col animate-slideUp">
        
        {/* Header */}
        <div className="bg-gradient-to-r from-indigo-500 to-purple-500 text-white p-5 flex items-center justify-between">
          <h3 className="text-lg font-bold">כותרת</h3>
          <button onClick={onClose}>
            <X className="w-6 h-6" />
          </button>
        </div>
        
        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-5">
          {/* Rich content here */}
        </div>
        
      </div>
    </div>
  );
}
```

## Data Flow

```
User Action
    ↓
App.jsx Handler
    ↓
API Call (mock or real)
    ↓
State Update
    ↓
Props to Components
    ↓
UI Update
```

## Migration Path

### Phase 1: Frontend Refactoring (Current)
- [✅] Create mock API service
- [ ] Build dumb components
- [ ] Wire everything in App.jsx
- [ ] Test all scenarios work

### Phase 2: Real Backend Integration
- Replace mock API with real endpoints
- Keep component code unchanged
- Master State Object comes from backend
- Function calling integrated into conversation service

### Phase 3: Advanced Features
- Add voice input
- Add real-time updates
- Add authentication
- Add data persistence

## Example: Complete Component

```jsx
// ConversationTranscript.jsx
import React, { useEffect, useRef } from 'react';

export default function ConversationTranscript({ messages, isTyping }) {
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.map((msg, idx) => (
        <div
          key={idx}
          className={`flex ${msg.sender === 'user' ? 'justify-start' : 'justify-end'} animate-fadeIn`}
        >
          <div
            className={`max-w-[80%] rounded-2xl px-4 py-3 shadow-sm ${
              msg.sender === 'user'
                ? 'bg-white text-gray-800 border border-gray-200'
                : 'bg-gradient-to-r from-indigo-500 to-purple-500 text-white'
            }`}
            style={{ whiteSpace: 'pre-line' }}
          >
            {msg.text}
          </div>
        </div>
      ))}
      
      {isTyping && (
        <div className="flex justify-end">
          <div className="bg-gradient-to-r from-indigo-500 to-purple-500 text-white rounded-2xl px-4 py-3 shadow-sm">
            <div className="flex gap-1">
              <div className="w-2 h-2 bg-white rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{animationDelay: '150ms'}}></div>
              <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{animationDelay: '300ms'}}></div>
            </div>
          </div>
        </div>
      )}
      
      <div ref={chatEndRef} />
    </div>
  );
}
```

## Next Steps

1. Review this architecture
2. I'll implement all components following this pattern
3. Wire everything in App.jsx
4. Test all scenarios
5. Provide complete downloadable package

## Benefits of This Architecture

✅ **Clean Separation**: UI components know nothing about data fetching
✅ **Easy Testing**: Each component can be tested in isolation
✅ **Backend Ready**: Swap mock API for real API without changing components
✅ **Maintainable**: Clear data flow and responsibilities
✅ **Scalable**: Easy to add new deep views or features
✅ **Type-Safe Ready**: Easy to add TypeScript later
