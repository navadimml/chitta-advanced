# Chitta - AI-Powered Child Development Assessment

## Overview
Chitta is a full-stack AI-powered platform for child development assessment, featuring conversation-first architecture with video analysis and clinical insights.

**Status**: ✅ Full stack integrated and functional
**Last Updated**: November 4, 2025
**Version**: 1.0.0

## Stack
- **Frontend**: React + Vite + Tailwind CSS
- **Backend**: FastAPI (Python 3.11+)
- **AI**: Multi-provider LLM abstraction (Gemini/Claude/OpenAI or Simulated)
- **Knowledge Graph**: Graphiti with FalkorDB (or Simulated mode)
- **Languages**: Hebrew + English with RTL support

## Quick Start (No API Keys Required!)

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
```

### Frontend (in new terminal)
```bash
npm install
npm run dev
```

Open **http://localhost:3000** and start chatting! 🚀

> **Note**: Runs in simulated mode by default - no API keys needed for development!

For detailed setup instructions, see [SETUP_GUIDE.md](./SETUP_GUIDE.md)

## What's Implemented

✅ **Full-stack architecture** - Frontend + Backend integrated
✅ **Conversational AI interface** - Natural Hebrew conversation flow
✅ **Interview system** - Dynamic assessment with continuous extraction
✅ **Video upload & analysis** - Multi-scenario video processing
✅ **Journal system** - Parent journaling with categories
✅ **Report generation** - Clinical insights and recommendations
✅ **Knowledge graph** - Persistent family context with Graphiti
✅ **Multi-LLM support** - Gemini, Claude, OpenAI, or Simulated
✅ **RTL support** - Full Hebrew UI with proper text rendering
✅ **Responsive design** - Mobile-first with beautiful animations

## Project Structure
```
src/
├── App.jsx                     # Main orchestrator with all state (170 lines)
├── main.jsx                    # React entry point
├── index.css                   # Global styles with animations
├── services/
│   └── api.js                  # Mock backend with 12 scenarios (400+ lines)
├── components/
│   ├── ConversationTranscript.jsx  # Chat message display
│   ├── ContextualSurface.jsx       # Dynamic bottom cards
│   ├── DeepViewManager.jsx         # Modal routing system
│   ├── InputArea.jsx               # Text input with suggestions
│   ├── SuggestionsPopup.jsx        # Suggestions bottom sheet
│   ├── DemoControls.jsx            # Scenario switcher
│   └── deepviews/                  # 11 modal view components
│       ├── ConsultationView.jsx
│       ├── DocumentUploadView.jsx
│       ├── DocumentListView.jsx
│       ├── ShareView.jsx
│       ├── JournalView.jsx
│       ├── ReportView.jsx
│       ├── ExpertProfileView.jsx
│       ├── VideoGalleryView.jsx
│       ├── VideoUploadView.jsx
│       ├── FilmingInstructionView.jsx
│       └── MeetingSummaryView.jsx
```

**Total Files**: 26 files, ~3,800 lines of code
**Components**: 17 React components (6 main + 11 deep views)

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

## Available Scenarios

The application includes 12 complete scenarios demonstrating the full Chitta workflow:

1. **interview** - Initial interview/onboarding
2. **consultation** - Live Q&A consultation mode
3. **documentUpload** - Document upload interface
4. **returning** - Returning user experience
5. **instructions** - Video filming instructions
6. **videoUploaded** - Post-upload status (33% progress)
7. **analyzing** - Analysis in progress
8. **reportReady** - Reports generated and ready
9. **viewReport** - Active report viewing
10. **experts** - Expert finder and profiles
11. **meetingPrep** - Meeting preparation summary
12. **sharing** - Secure sharing with experts

Switch between scenarios using the demo controls at the top of the app.

## Current Status

✅ **Fully Implemented** - All 17 components working
✅ **12 Scenarios** - Complete data and interactions
✅ **Mock API** - Ready to swap for real backend
✅ **Hebrew Support** - 100% RTL and proper encoding
✅ **Animations** - All visual effects preserved
✅ **Responsive** - Mobile-first design complete

## What's Next?

### For Development:
1. ✅ ~~Review the architecture~~ - Complete
2. ✅ ~~Test all scenarios work correctly~~ - Complete
3. **Add real backend endpoints** - Ready for integration
4. **Add authentication** - User login/session management
5. **Add unit tests** - Jest + React Testing Library
6. **Deploy to production** - Build and deploy

### For Production:
1. Replace mock API with real backend calls
2. Add authentication and user sessions
3. Implement real file upload functionality
4. Add video processing integration
5. Set up analytics and monitoring
6. Deploy to hosting platform

---

**This is Chitta** 💙
