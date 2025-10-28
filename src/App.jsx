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

  // Initial greeting on mount
  useEffect(() => {
    setMessages([{
      sender: 'chitta',
      text: 'שלום! אני Chitta, ואני כאן לעזור לך להבין טוב יותר את ההתפתחות של הילד/ה שלך. בואי נתחיל - מה שם הילד/ה וכמה הוא/היא?',
      timestamp: new Date().toISOString()
    }]);
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
        if (response.ui_data.suggestions) {
          setSuggestions(response.ui_data.suggestions.map(s =>
            typeof s === 'string' ? { text: s, action: null } : s
          ));
        }
        if (response.ui_data.cards) {
          setCards(response.ui_data.cards);
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
    if (action === 'upload') {
      setActiveDeepView('upload');
      setActiveViewData(null);
    } else if (action === 'videoGallery') {
      setActiveDeepView('videoGallery');
      setActiveViewData(null);
    } else if (action === 'journal') {
      setActiveDeepView('journal');
      setActiveViewData(null);
    } else if (action === 'complete_interview') {
      await handleCompleteInterview();
    } else if (action && action.startsWith('view_guideline_')) {
      // Extract guideline index and open dynamic view
      const index = parseInt(action.split('_')[2]);
      const card = cards[index];

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

        // Create cards for scenarios
        const scenarioCards = response.video_guidelines.scenarios.map(scenario => ({
          type: 'video_guideline',
          title: scenario.title,
          description: scenario.description,
          priority: scenario.priority
        }));

        setCards(scenarioCards);
        setStage('video_upload');
      }

    } catch (error) {
      console.error('Error completing interview:', error);
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
