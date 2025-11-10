import React, { useState, useEffect } from 'react';
import { Menu, MessageCircle } from 'lucide-react';

// API Client
import { api } from './api/client';

// Demo Orchestrator
import { demoOrchestrator } from './services/DemoOrchestrator.jsx';

// UI Components
import ConversationTranscript from './components/ConversationTranscript';
import ContextualSurface from './components/ContextualSurface';
import InputArea from './components/InputArea';
import SuggestionsPopup from './components/SuggestionsPopup';
import DeepViewManager from './components/DeepViewManager';
import VideoGuidelinesView from './components/VideoGuidelinesView';

// Generate unique family ID (in real app, from auth)
const FAMILY_ID = 'family_' + Math.random().toString(36).substr(2, 9);

function App() {
  // Simple state
  const [messages, setMessages] = useState([]);
  const [stage, setStage] = useState('welcome');
  const [cards, setCards] = useState([]);
  const [suggestions, setSuggestions] = useState([
    { text: "שמו יוני והוא בן 3.5", action: null },
    { text: "הילדה שלי בת 5", action: null },
    { text: "רוצה להתחיל בהערכה", action: null }
  ]);
  const [draftMessage, setDraftMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [activeDeepView, setActiveDeepView] = useState(null);
  const [activeViewData, setActiveViewData] = useState(null);
  const [videos, setVideos] = useState([]);
  const [journalEntries, setJournalEntries] = useState([]);
  const [childName, setChildName] = useState('');
  const [videoGuidelines, setVideoGuidelines] = useState(null);
  const [showGuidelinesView, setShowGuidelinesView] = useState(false);

  // Load journey state on mount
  useEffect(() => {
    async function loadJourney() {
      try {
        // Load complete state from backend
        const response = await api.getState(FAMILY_ID);
        const { state, ui } = response;

        // Reconstruct UI from state - everything derives!
        const conversationMessages = state.conversation.map(msg => ({
          sender: msg.role === 'user' ? 'user' : 'chitta',
          text: msg.content,
          timestamp: msg.timestamp
        }));

        // Add greeting message
        setMessages([
          ...conversationMessages,
          {
            sender: 'chitta',
            text: ui.greeting,
            timestamp: new Date().toISOString()
          }
        ]);

        // Set derived UI elements
        setCards(ui.cards);
        setSuggestions(ui.suggestions);

        // Set state data
        if (state.child) {
          setChildName(state.child.name || '');
        }

        if (state.artifacts.baseline_video_guidelines) {
          setVideoGuidelines(state.artifacts.baseline_video_guidelines.content);
        }

        // Set activities
        setVideos(state.videos_uploaded || []);
        setJournalEntries(state.journal_entries || []);

      } catch (error) {
        console.error('Error loading journey:', error);
        // Fallback to default greeting
        setMessages([{
          sender: 'chitta',
          text: 'שלום! אני צ\'יטה 💙\n\nנעים להכיר אותך! אני כאן כדי להכיר את הילד/ה שלך ולהבין איך אפשר לעזור. נשוחח קצת יחד, ואז נמשיך לשלבים הבאים.\n\nבואי נתחיל - מה שם הילד/ה שלך ובן/בת כמה?',
          timestamp: new Date().toISOString()
        }]);
      }
    }

    loadJourney();

    // 🎭 Register injectors with DemoOrchestrator (app doesn't control demo!)
    const messageInjector = (message) => {
      setMessages(prev => [...prev, message]);
    };

    const cardInjector = (card) => {
      setCards(prev => [...prev, card]);
    };

    const guidelinesInjector = (guidelines) => {
      setVideoGuidelines(guidelines);
    };

    // Demo orchestrator can now inject messages/cards/guidelines as if they were real
    demoOrchestrator.messageInjector = messageInjector;
    demoOrchestrator.cardInjector = cardInjector;
    demoOrchestrator.guidelinesInjector = guidelinesInjector;
  }, []);

  // Handle sending a message
  const handleSend = async (message) => {
    if (!message.trim()) return;

    // Add user message to UI immediately
    const userMessage = {
      sender: 'user',
      text: message,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setDraftMessage('');
    setIsTyping(true);

    try {
      // Call backend API (API client handles demo detection and orchestrator start)
      const response = await api.sendMessage(FAMILY_ID, message);

      // 🎭 Check if demo mode was triggered
      if (response.ui_data && response.ui_data.demo_mode) {
        console.log('🎭 Demo mode triggered - orchestrator will take over');

        // Start demo orchestrator with scenario
        const scenario = demoOrchestrator.getScenario();
        await demoOrchestrator.start(
          scenario,
          demoOrchestrator.messageInjector,
          demoOrchestrator.cardInjector
        );

        setIsTyping(false);
        return; // Orchestrator handles everything from here
      }

      // Add assistant response (normal flow)
      const assistantMessage = {
        sender: 'chitta',
        text: response.response,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Update UI from backend response
      if (response.ui_data) {
        if (response.ui_data.suggestions) {
          setSuggestions(response.ui_data.suggestions.map(s =>
            typeof s === 'string' ? { text: s, action: null } : s
          ));
        }
        if (response.ui_data.cards) {
          setCards(response.ui_data.cards);
        }
        // CRITICAL: Save video guidelines when interview completes
        if (response.ui_data.video_guidelines) {
          setVideoGuidelines(response.ui_data.video_guidelines);
        }
      }

      // Update stage
      if (response.stage) {
        setStage(response.stage);
      }

    } catch (error) {
      console.error('Error sending message:', error);

      // Fallback message
      const errorMessage = {
        sender: 'chitta',
        text: 'מצטערת, הייתה בעיה. נסי שוב.',
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  // Handle card click
  const handleCardClick = async (action) => {
    if (!action) return; // Status cards have no action

    if (action === 'view_guidelines') {
      setShowGuidelinesView(true);
      return;
    }

    if (action === 'upload') {
      setActiveDeepView('upload');
      setActiveViewData(null);
    } else if (action === 'view_all_guidelines') {
      // Show all guidelines in instructions view
      setActiveDeepView('instructions');
      setActiveViewData(null);
    } else if (action === 'videoGallery') {
      setActiveDeepView('videoGallery');
      setActiveViewData(null);
    } else if (action === 'journal') {
      setActiveDeepView('journal');
      setActiveViewData(null);
    } else if (action === 'complete_interview') {
      await handleCompleteInterview();
    } else if (action === 'skipAnalysis') {
      await handleSkipAnalysis();
    } else if (action === 'parentReport') {
      setActiveDeepView('parentReport');
      setActiveViewData(null);
    } else if (action === 'proReport') {
      setActiveDeepView('professionalReport');
      setActiveViewData(null);
    } else if (action === 'experts') {
      setActiveDeepView('findExperts');
      setActiveViewData(null);
    } else if (action && action.startsWith('view_guideline_')) {
      // Find the card by action (not by index, as there may be status cards)
      const card = cards.find(c => c.action === action);

      if (card) {
        setActiveDeepView('dynamic_guideline');
        setActiveViewData(card);
      }
    }
  };

  // Handle complete interview
  const handleCompleteInterview = async () => {
    setIsTyping(true);

    try {
      const response = await api.completeInterview(FAMILY_ID);

      // Show video guidelines
      if (response.video_guidelines) {
        const guidelinesMsg = {
          sender: 'chitta',
          text: 'תודה רבה! הכנתי לך הנחיות מותאמות אישית לצילום וידאו.',
          timestamp: new Date().toISOString()
        };

        setMessages(prev => [...prev, guidelinesMsg]);

        // Save guidelines to state
        setVideoGuidelines(response.video_guidelines);
        setStage('video_upload');
      }

    } catch (error) {
      console.error('Error completing interview:', error);
    } finally {
      setIsTyping(false);
    }
  };

  // Handle skip analysis (dev only)
  const handleSkipAnalysis = async () => {
    setIsTyping(true);

    try {
      const response = await api.analyzeVideos(FAMILY_ID);

      if (response.success) {
        const msg = {
          sender: 'chitta',
          text: 'ניתוח הסרטונים הושלם! הדוחות מוכנים לצפייה.',
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, msg]);

        // Update stage
        setStage(response.next_stage || 'report_generation');

        // Refresh cards
        await refreshCards();
      }
    } catch (error) {
      console.error('Error skipping analysis:', error);
      const errorMsg = {
        sender: 'chitta',
        text: 'שגיאה בסימולציה. נסי שוב.',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  // Handle suggestion click
  const handleSuggestionClick = (suggestion) => {
    if (suggestion.action) {
      handleCardClick(suggestion.action);
    } else {
      handleSend(suggestion.text);
    }
    setShowSuggestions(false);
  };

  // Handle deep view close
  const handleCloseDeepView = () => {
    setActiveDeepView(null);
    setActiveViewData(null);
  };

  // Function to refresh cards from backend
  const refreshCards = async () => {
    try {
      const response = await api.getTimeline(FAMILY_ID);
      if (response.ui_data && response.ui_data.cards) {
        setCards(response.ui_data.cards);
      }
    } catch (error) {
      console.error('Error refreshing cards:', error);
    }
  };

  // CRUD handlers for videos
  const handleCreateVideo = async (videoData) => {
    const newVideo = {
      id: 'vid_' + Date.now(),
      title: videoData.title || 'סרטון חדש',
      description: videoData.description || '',
      date: new Date().toLocaleDateString('he-IL'),
      duration: videoData.duration || '0:00',
      thumbnail: videoData.thumbnail || null,
      url: videoData.url || null,
      timestamp: Date.now()
    };

    setVideos(prev => [...prev, newVideo]);

    // Upload to backend
    try {
      await api.uploadVideo(
        FAMILY_ID,
        newVideo.id,
        videoData.scenario || 'general',
        0
      );

      // Refresh cards to show updated progress
      await refreshCards();
    } catch (error) {
      console.error('Error uploading video:', error);
    }

    return { success: true, video: newVideo, message: 'הסרטון הועלה בהצלחה' };
  };

  const handleDeleteVideo = async (videoId) => {
    setVideos(prev => prev.filter(v => v.id !== videoId));
    return { success: true, message: 'הסרטון נמחק' };
  };

  // CRUD handlers for journal entries
  const handleCreateJournalEntry = async (text, status) => {
    const newEntry = {
      id: 'entry_' + Date.now(),
      text,
      status,
      timestamp: 'עכשיו',
      date: new Date()
    };

    setJournalEntries(prev => [newEntry, ...prev]);
    return { success: true, entry: newEntry, message: 'הרשומה נשמרה בהצלחה' };
  };

  const handleDeleteJournalEntry = async (entryId) => {
    setJournalEntries(prev => prev.filter(e => e.id !== entryId));
    return { success: true, message: 'הרשומה נמחקה' };
  };

  // Handle input change
  const handleInputChange = (value) => {
    setDraftMessage(value);
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-blue-50 to-indigo-50" dir="rtl">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-4 flex items-center justify-between shadow-sm">
        <button className="p-2 hover:bg-gray-100 rounded-full transition">
          <Menu className="w-5 h-5 text-gray-600" />
        </button>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <h1 className="text-lg font-bold text-gray-800">Chitta</h1>
            <p className="text-xs text-gray-500">
              {childName ? `המסע ההתפתחותי של ${childName}` : 'המסע ההתפתחותי'}
            </p>
          </div>
          <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full flex items-center justify-center shadow-md">
            <MessageCircle className="w-5 h-5 text-white" />
          </div>
        </div>
      </div>

      {/* Conversation Transcript */}
      <ConversationTranscript messages={messages} isTyping={isTyping} />

      {/* Contextual Surface */}
      <ContextualSurface cards={cards} onCardClick={handleCardClick} />

      {/* Input Area */}
      <InputArea
        onSend={handleSend}
        onSuggestionsClick={() => setShowSuggestions(true)}
        hasSuggestions={suggestions && suggestions.length > 0}
        value={draftMessage}
        onChange={handleInputChange}
      />

      {/* Suggestions Popup */}
      {showSuggestions && (
        <SuggestionsPopup
          suggestions={suggestions}
          onSuggestionClick={handleSuggestionClick}
          onClose={() => setShowSuggestions(false)}
        />
      )}

      {/* Deep View Manager */}
      <DeepViewManager
        activeView={activeDeepView}
        onClose={handleCloseDeepView}
        viewData={activeViewData || { data: { childName } }}
        videos={videos}
        videoGuidelines={videoGuidelines}
        journalEntries={journalEntries}
        onCreateJournalEntry={handleCreateJournalEntry}
        onDeleteJournalEntry={handleDeleteJournalEntry}
        onCreateVideo={handleCreateVideo}
        onDeleteVideo={handleDeleteVideo}
      />

      {/* Video Guidelines View (works for both demo and real mode) */}
      {showGuidelinesView && videoGuidelines && (
        <VideoGuidelinesView
          guidelines={videoGuidelines}
          childName={childName || "דניאל"}
          onClose={() => setShowGuidelinesView(false)}
        />
      )}

      {/* Global Styles */}
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes slideUp {
          from { transform: translateY(100%); }
          to { transform: translateY(0); }
        }
        .animate-fadeIn { animation: fadeIn 0.3s ease-out; }
        .animate-slideUp { animation: slideUp 0.3s ease-out; }
      `}</style>
    </div>
  );
}

export default App;
