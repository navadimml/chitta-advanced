import React, { useState, useEffect, useRef } from 'react';
import { Menu, MessageCircle } from 'lucide-react';

// API Client
import { api } from './api/client';

// Test Mode Orchestrator
import { testModeOrchestrator } from './services/TestModeOrchestrator.jsx';

// UI Components
import ConversationTranscript from './components/ConversationTranscript';
import ContextualSurface from './components/ContextualSurface';
import InputArea from './components/InputArea';
import SuggestionsPopup from './components/SuggestionsPopup';
import DeepViewManager from './components/DeepViewManager';
import VideoGuidelinesView from './components/VideoGuidelinesView';
import { TestModeBannerPortal } from './components/TestModeBannerPortal.jsx';

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

  // Test mode state
  const [testMode, setTestMode] = useState(false);
  const [testPersonas, setTestPersonas] = useState([]);
  const [showPersonaSelector, setShowPersonaSelector] = useState(false);
  const [testFamilyId, setTestFamilyId] = useState(null); // Track test mode family ID

  // Ref to track last processed message (prevent duplicate triggers)
  const lastProcessedMessageRef = useRef(null);

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
          const content = state.artifacts.baseline_video_guidelines.content;
          // Parse JSON content (artifact stores structured data as JSON string)
          const guidelinesData = typeof content === 'string' ? JSON.parse(content) : content;
          setVideoGuidelines(guidelinesData);
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

    // 🧪 Setup test mode orchestrator callbacks
    testModeOrchestrator.onError = (error) => {
      console.error('🧪 Test mode error:', error);
      const errorMessage = {
        sender: 'chitta',
        text: 'שגיאה במצב בדיקה. בודק...',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    };
  }, []);

  // 🧪 Monitor messages and trigger next response in test mode
  useEffect(() => {
    if (!testModeOrchestrator.isActive() || !testModeOrchestrator.isAutoRunning()) {
      return;
    }

    // Find last Chitta message
    const lastMessage = messages[messages.length - 1];
    if (lastMessage && lastMessage.sender === 'chitta') {
      // CRITICAL: Prevent duplicate triggers by checking if we already processed this message
      if (lastProcessedMessageRef.current === lastMessage.timestamp) {
        console.log('🧪 [App] Already triggered for this message, skipping...');
        return;
      }

      console.log('🧪 [App] Chitta responded, triggering next parent response');
      lastProcessedMessageRef.current = lastMessage.timestamp;

      // Trigger next response after a small delay
      setTimeout(() => {
        testModeOrchestrator.generateNextResponse(messages, handleSend);
      }, 500);
    }
  }, [messages]);

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
      // 🧪 Check for test mode trigger
      const testTriggers = ['test mode', 'start test', 'מצב בדיקה', 'התחל בדיקה', 'טסט'];
      const isTestTrigger = testTriggers.some(trigger =>
        message.toLowerCase().includes(trigger)
      );

      if (isTestTrigger) {
        console.log('🧪 Test mode triggered - loading personas');
        setIsTyping(true);

        try {
          // Load available personas
          const { personas } = await api.getTestPersonas();
          setTestPersonas(personas);
          setShowPersonaSelector(true);

          // Show Chitta's response
          const assistantMessage = {
            sender: 'chitta',
            text: 'מצוין! 🧪\n\nנכנסנו למצב בדיקה. בחרי אחת מהפרסונות לסימולציה:',
            timestamp: new Date().toISOString()
          };
          setMessages(prev => [...prev, assistantMessage]);
        } catch (error) {
          console.error('Error loading test personas:', error);
          const errorMessage = {
            sender: 'chitta',
            text: 'שגיאה בטעינת פרסונות בדיקה.',
            timestamp: new Date().toISOString()
          };
          setMessages(prev => [...prev, errorMessage]);
        }

        setIsTyping(false);
        return;
      }

      // Call backend API (use test family ID if in test mode)
      const activeFamilyId = testMode && testFamilyId ? testFamilyId : FAMILY_ID;
      const response = await api.sendMessage(activeFamilyId, message);

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
      // 🌟 Wu Wei: Fetch the artifact content before showing the view
      const activeFamilyId = testMode && testFamilyId ? testFamilyId : FAMILY_ID;

      console.log('📹 Fetching video guidelines for family:', activeFamilyId);

      try {
        const artifact = await api.getArtifact(activeFamilyId, 'baseline_video_guidelines');
        console.log('📦 Artifact received:', artifact);

        if (artifact && artifact.content) {
          console.log('📄 Content type:', typeof artifact.content);
          console.log('📄 Content preview:', typeof artifact.content === 'string'
            ? artifact.content.substring(0, 200)
            : JSON.stringify(artifact.content).substring(0, 200));

          // Check if content is old markdown format (starts with #)
          if (typeof artifact.content === 'string' && artifact.content.trim().startsWith('#')) {
            console.warn('⚠️ Old markdown format detected. Guidelines need regeneration.');
            alert('ההנחיות במבנה ישן. נא להתחיל שיחה חדשה כדי ליצור הנחיות מעודכנות.');
            return;
          }

          // Parse JSON content (artifact stores structured data as JSON string)
          let guidelinesData;
          try {
            guidelinesData = typeof artifact.content === 'string'
              ? JSON.parse(artifact.content)
              : artifact.content;
          } catch (parseError) {
            console.error('❌ Failed to parse guidelines JSON:', parseError);
            console.error('Content was:', artifact.content.substring(0, 500));
            alert('שגיאה בקריאת ההנחיות. נא לנסות שוב או להתחיל שיחה חדשה.');
            return;
          }

          console.log('✅ Parsed guidelines:', guidelinesData);
          console.log('✅ Has scenarios:', guidelinesData.scenarios?.length);

          setVideoGuidelines(guidelinesData);
          setShowGuidelinesView(true);
        } else {
          console.error('❌ Artifact not ready or missing content:', artifact);
          alert('ההנחיות עדיין לא מוכנות. נא לנסות שוב בעוד רגעים.');
        }
      } catch (error) {
        console.error('❌ Error fetching video guidelines:', error);
        alert('שגיאה בטעינת ההנחיות. נא לנסות שוב.');
      }
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

      {/* 🧪 Test Mode Banner (shows when test mode is active) */}
      <TestModeBannerPortal />

      {/* 🧪 Test Mode: Persona Selector */}
      {showPersonaSelector && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full p-6">
            <h2 className="text-2xl font-bold mb-4 text-gray-800">בחר פרסונה לבדיקה</h2>
            <p className="text-gray-600 mb-6">כל פרסונה מייצגת מקרה בדיקה מציאותי עם רקע מפורט</p>

            <div className="space-y-4">
              {testPersonas.map((persona) => (
                <button
                  key={persona.id}
                  onClick={async () => {
                    setShowPersonaSelector(false);
                    setIsTyping(true);

                    try {
                      // Start test with this persona - PRESERVE existing family_id to maintain session!
                      const result = await api.startTest(persona.id, FAMILY_ID);

                      // Show Chitta's initial greeting (same as real conversation)
                      const greetingMessage = {
                        sender: 'chitta',
                        text: 'שלום! אני צ\'יטה 💙\n\nנעים להכיר אותך! אני כאן כדי להכיר את הילד/ה שלך ולהבין איך אפשר לעזור. נשוחח קצת יחד, ואז נמשיך לשלבים הבאים.\n\nבואי נתחיל - מה שם הילד/ה שלך ובן/בת כמה?',
                        timestamp: new Date().toISOString()
                      };

                      // Set messages with greeting
                      const newMessages = [...messages, greetingMessage];
                      setMessages(newMessages);

                      // Mark test mode as active
                      setTestMode(true);

                      // Reset tracking ref
                      lastProcessedMessageRef.current = null;

                      // 🧪 Store test family ID and start orchestrator
                      const testFamId = result.family_id;
                      setTestFamilyId(testFamId); // Store for API calls
                      console.log('🧪 Test mode using family ID:', testFamId);

                      await testModeOrchestrator.start(
                        persona.id,
                        persona,
                        testFamId
                      );

                      // Start auto-conversation flow with updated messages
                      console.log('🧪 Starting auto-conversation with Chitta greeting');
                      testModeOrchestrator.startAutoConversation(newMessages, handleSend);

                    } catch (error) {
                      console.error('Error starting test:', error);
                    }

                    setIsTyping(false);
                  }}
                  className="w-full p-4 bg-gradient-to-r from-purple-50 to-indigo-50 hover:from-purple-100 hover:to-indigo-100 border-2 border-purple-200 rounded-xl transition-all duration-200 hover:scale-105 text-right"
                >
                  <div className="font-bold text-lg text-gray-800 mb-1">
                    {persona.parent} - {persona.child}
                  </div>
                  <div className="text-sm text-gray-600">{persona.concern}</div>
                </button>
              ))}
            </div>

            <button
              onClick={() => setShowPersonaSelector(false)}
              className="mt-6 w-full py-2 bg-gray-200 hover:bg-gray-300 rounded-lg transition"
            >
              ביטול
            </button>
          </div>
        </div>
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
