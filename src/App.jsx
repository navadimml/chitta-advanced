import React, { useState, useEffect } from 'react';
import { Menu, MessageCircle } from 'lucide-react';

// API Client
import { api } from './api/client';

// UI Components
import ConversationTranscript from './components/ConversationTranscript';
import ContextualSurface from './components/ContextualSurface';
import InputArea from './components/InputArea';
import SuggestionsPopup from './components/SuggestionsPopup';
import DeepViewManager from './components/DeepViewManager';
import DemoBanner from './components/DemoBanner';

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

  // 🎬 Demo Mode State
  const [demoMode, setDemoMode] = useState(false);
  const [demoFamilyId, setDemoFamilyId] = useState(null);
  const [demoPaused, setDemoPaused] = useState(false);
  const [demoCard, setDemoCard] = useState(null);

  // Initial greeting on mount
  useEffect(() => {
    setMessages([{
      sender: 'chitta',
      text: 'שלום! אני צ\'יטה 💙\n\nנעים להכיר אותך! אני כאן כדי להכיר את הילד/ה שלך ולהבין איך אפשר לעזור. נשוחח קצת יחד, ואז נמשיך לשלבים הבאים.\n\nבואי נתחיל - מה שם הילד/ה שלך ובן/בת כמה?',
      timestamp: new Date().toISOString()
    }]);
  }, []);

  // 🎬 Demo Mode: Auto-play next message
  const playNextDemoStep = async () => {
    if (!demoMode || !demoFamilyId || demoPaused) {
      console.log('🎬 Skipping step:', { demoMode, demoFamilyId, demoPaused });
      return;
    }

    try {
      console.log('🎬 Getting next demo step...');
      const response = await api.getNextDemoStep(demoFamilyId);

      console.log('🎬 Demo step received:', response.step, '/', response.total_steps);

      // Update demo card (separate from normal cards!)
      if (response.demo_card) {
        setDemoCard(response.demo_card);
      }

      // Check if artifact was generated
      if (response.artifact_generated) {
        console.log('🌟 Artifact generated:', response.artifact_generated);

        // Add artifact card to cards array
        const artifactCard = {
          card_type: 'artifact',
          status: 'new',
          icon: 'FileText',
          title: 'הנחיות צילום מוכנות!',
          subtitle: 'לחץ לצפייה בהנחיות מותאמות אישית',
          action: 'view_guidelines',
          color: 'green'
        };
        setCards(prev => [...prev, artifactCard]);
      }

      // Wait for delay BEFORE showing message
      if (response.message.delay_ms > 0) {
        console.log(`🎬 Waiting ${response.message.delay_ms}ms...`);
        await new Promise(resolve => setTimeout(resolve, response.message.delay_ms));
      }

      // Add message to UI
      const newMessage = {
        sender: response.message.role === 'user' ? 'user' : 'chitta',
        text: response.message.content,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, newMessage]);

      // Continue to next step if not complete
      if (!response.is_complete) {
        // Schedule next step
        setTimeout(() => playNextDemoStep(), 100);
      } else {
        // Demo complete!
        console.log('🎬 Demo completed!');
        setDemoMode(false);
        setDemoFamilyId(null);
        setDemoCard(null);
      }
    } catch (error) {
      console.error('🎬 Error playing demo step:', error);
      setDemoMode(false);
      setDemoCard(null);
    }
  };

  // 🎬 Demo Mode: Stop demo
  const stopDemo = async () => {
    if (!demoFamilyId) return;

    try {
      await api.stopDemo(demoFamilyId);
      setDemoMode(false);
      setDemoFamilyId(null);
      setDemoPaused(false);
      setDemoCard(null);

      // Add exit message
      const exitMessage = {
        sender: 'chitta',
        text: 'הדמו הופסק. מוכנה להתחיל את השיחה האמיתית שלך! 💙',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, exitMessage]);

      // Clear cards
      setCards([]);
    } catch (error) {
      console.error('Error stopping demo:', error);
    }
  };

  // 🎬 Demo Mode: Handle demo actions
  const handleDemoAction = async (action) => {
    console.log('🎬 Demo action:', action);

    if (action === 'stop_demo') {
      await stopDemo();
    } else if (action === 'pause_demo') {
      setDemoPaused(true);
    } else if (action === 'resume_demo') {
      setDemoPaused(false);
      // Resume auto-play
      setTimeout(() => playNextDemoStep(), 100);
    } else if (action === 'skip_step') {
      // Skip current delay and play next
      playNextDemoStep();
    }
  };

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
      // Call backend API
      const response = await api.sendMessage(FAMILY_ID, message);

      // Add assistant response
      const assistantMessage = {
        sender: 'chitta',
        text: response.response,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Update UI from backend response
      if (response.ui_data) {
        // 🎬 Check if demo mode was triggered
        if (response.ui_data.demo_mode) {
          console.log('🎬 Demo mode triggered!', response.ui_data);
          setDemoMode(true);
          setDemoFamilyId(response.ui_data.demo_family_id);

          // Set demo card (separate state!)
          if (response.ui_data.cards && response.ui_data.cards.length > 0) {
            setDemoCard(response.ui_data.cards[0]);
          }

          // Set demo suggestions
          if (response.ui_data.suggestions) {
            setSuggestions(response.ui_data.suggestions.map(s =>
              typeof s === 'string' ? { text: s, action: null } : s
            ));
          }

          // Clear normal cards to start fresh
          setCards([]);

          // Start auto-play immediately
          console.log('🎬 Starting auto-play in 500ms...');
          setTimeout(() => {
            console.log('🎬 Triggering first step...');
            playNextDemoStep();
          }, 500);

          return; // Don't process normal flow
        }

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

      {/* 🎬 Demo Mode Banner */}
      {demoMode && demoCard && (
        <DemoBanner
          demoCard={demoCard}
          onAction={handleDemoAction}
          isPaused={demoPaused}
        />
      )}

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
