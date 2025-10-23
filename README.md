# Chitta - Refactored Architecture

## Overview
This is the refactored version of the Chitta prototype with clean separation of concerns.

## What's Different?
✅ **Service Layer**: Mock API simulates backend (`src/services/api.js`)
✅ **Component Architecture**: Small, focused, reusable components  
✅ **Dumb Components**: UI components just render props
✅ **State Management**: All state in App.jsx
✅ **Preserved Styling**: ALL original Tailwind classes and animations maintained
✅ **Backend Ready**: Easy to swap mock API for real backend

## Project Structure
```
src/
├── App.jsx                     # Main orchestrator with all state
├── services/
│   └── api.js                  # Mock backend (swap for real API)
├── components/
│   ├── ConversationTranscript.jsx
│   ├── ContextualSurface.jsx
│   ├── DeepViewManager.jsx
│   ├── InputArea.jsx
│   ├── SuggestionsPopup.jsx
│   ├── DemoControls.jsx
│   └── deepviews/
│       ├── ConsultationView.jsx
│       ├── DocumentUploadView.jsx
│       ├── DocumentListView.jsx
│       ├── ShareView.jsx
│       ├── JournalView.jsx
│       ├── ReportView.jsx
│       ├── ExpertProfileView.jsx
│       ├── VideoGalleryView.jsx
│       ├── FilmingInstructionView.jsx
│       └── MeetingSummaryView.jsx
```

## Running the Application

### Install Dependencies
```bash
npm install
```

### Start Development Server
```bash
npm run dev
```

### Build for Production
```bash
npm run build
```

## Architecture Highlights

### 1. Mock API Service
Located in `src/services/api.js`, this simulates the backend:
- Contains all scenario data (Master State Objects)
- Provides async methods that mimic real API calls
- Easy to replace with real endpoints

### 2. Dumb Components
All UI components are pure - they receive props and render:
```jsx
// Example: ConversationTranscript just displays what it's given
<ConversationTranscript messages={messages} isTyping={isTyping} />
```

### 3. Centralized State
App.jsx manages all state and passes it down:
- Master State Object from API
- Messages, context cards, suggestions
- Deep view state
- All handlers

### 4. Deep Views
Modal components for rich interactions:
- Consultation interface
- Document upload/viewing
- Reports
- Expert profiles
- Video gallery
- And more...

## Backend Integration Path

When ready to connect to a real backend:

1. **Update `src/services/api.js`**:
```jsx
// Before (mock):
async getScenario(scenarioKey) {
  return SCENARIOS[scenarioKey];
}

// After (real):
async getScenario(scenarioKey) {
  const response = await fetch(`/api/scenarios/${scenarioKey}`);
  return response.json();
}
```

2. **Components stay unchanged** - they still receive the same props

3. **Master State Object** now comes from real backend

## Styling Notes

- **Preserved**: All original Tailwind classes maintained exactly
- **Animations**: fadeIn, slideUp, bounce - all intact  
- **RTL Support**: Hebrew text with `dir="rtl"` preserved
- **Colors**: Brand gradients (indigo/purple) and status colors unchanged
- **Responsive**: Mobile-first design maintained

## Demo Controls

The refactored version includes scenario switcher at the top:
- Interview
- Consultation
- Document Upload
- Video Upload stages
- Report viewing
- Expert finding
- And more...

## Key Files to Review

1. **ARCHITECTURE.md** - Detailed design patterns and principles
2. **src/services/api.js** - All scenario data and mock backend
3. **src/App.jsx** - State management and component orchestration
4. **src/components/** - Individual UI components

## Development Notes

- All Hebrew text properly encoded
- Lucide React icons used throughout
- Tailwind CSS for styling
- React hooks for state management
- No external state management library needed (could add Redux/Zustand later if needed)

## What's Next?

1. Review the architecture
2. Test all scenarios work correctly
3. Add real backend endpoints
4. Deploy to production

---

**This is Chitta** 💙
