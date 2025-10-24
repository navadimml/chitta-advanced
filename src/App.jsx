import React, { useState, useEffect, useRef } from 'react';
import { Menu, MessageCircle } from 'lucide-react';

// New architecture imports
import JourneyEngine from './core/JourneyEngine';
import ConversationController from './core/ConversationController';
import UIAdapter from './core/UIAdapter';
import childDevelopmentJourney from './config/childDevelopmentJourney';

// UI Components
import ConversationTranscript from './components/ConversationTranscript';
import ContextualSurface from './components/ContextualSurface';
import InputArea from './components/InputArea';
import SuggestionsPopup from './components/SuggestionsPopup';
import DeepViewManager from './components/DeepViewManager';

// Initialize the journey engine once
const journeyEngine = new JourneyEngine(childDevelopmentJourney);
const conversationController = new ConversationController(journeyEngine);
const uiAdapter = new UIAdapter(childDevelopmentJourney);

function App() {
  const [state, setState] = useState(journeyEngine.getState());
  const [ui, setUI] = useState(uiAdapter.generateUI(state));
  const [isTyping, setIsTyping] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [activeDeepView, setActiveDeepView] = useState(null);

  // Track videos and journal entries for DeepViewManager
  const [videos, setVideos] = useState([]);
  const [journalEntries, setJournalEntries] = useState([]);

  // Subscribe to state changes
  useEffect(() => {
    const unsubscribe = journeyEngine.subscribe((newState) => {
      setState(newState);
      const newUI = uiAdapter.generateUI(newState);
      setUI(newUI);

      // Update videos and journal entries from state
      if (newState.data.videos) {
        setVideos(newState.data.videos);
      }
      if (newState.data.journalEntries) {
        setJournalEntries(newState.data.journalEntries);
      }
    });

    // Start proactive monitoring
    conversationController.startProactiveMonitoring();

    // Check for proactive message on mount (e.g., welcome back)
    const proactiveMsg = conversationController.getProactiveMessage();
    if (proactiveMsg) {
      setTimeout(() => {
        conversationController.addMessage({ sender: 'chitta', text: proactiveMsg.text });
      }, 1000);
    }

    return () => {
      unsubscribe();
      conversationController.stopProactiveMonitoring();
    };
  }, []);

  // Handle sending a message
  const handleSend = async (message) => {
    setIsTyping(true);
    await conversationController.sendMessage(message);
    setIsTyping(false);
  };

  // Handle card click
  const handleCardClick = async (action) => {
    // Special handling for certain actions
    if (action === 'upload') {
      setActiveDeepView('upload');
    } else if (action === 'videoGallery') {
      setActiveDeepView('videoGallery');
    } else if (action === 'journal') {
      setActiveDeepView('journal');
    } else if (action === 'parentReport') {
      setActiveDeepView('parentReport');
    } else if (action === 'proReport') {
      setActiveDeepView('proReport');
    } else if (action === 'experts') {
      setActiveDeepView('experts');
    } else if (action === 'uploadDoc') {
      setActiveDeepView('uploadDoc');
    } else if (action === 'viewDocs') {
      setActiveDeepView('viewDocs');
    } else if (action === 'shareExpert') {
      setActiveDeepView('shareExpert');
    } else if (action?.startsWith('view_instruction_')) {
      setActiveDeepView('instructions');
    }
  };

  // Handle suggestion click
  const handleSuggestionClick = (suggestionText, action) => {
    if (action) {
      // If suggestion has an action, handle it
      if (action === 'upload') {
        setActiveDeepView('upload');
      } else if (action === 'journal') {
        setActiveDeepView('journal');
      } else if (action === 'videoGallery') {
        setActiveDeepView('videoGallery');
      } else if (action === 'uploadDoc') {
        setActiveDeepView('uploadDoc');
      } else {
        // Otherwise send as message
        handleSend(suggestionText);
      }
    } else {
      handleSend(suggestionText);
    }
    setShowSuggestions(false);
  };

  // Handle deep view close
  const handleCloseDeepView = () => {
    setActiveDeepView(null);
  };

  // CRUD handlers for videos
  const handleCreateVideo = async (videoData) => {
    const newVideo = {
      id: journeyEngine.generateId(),
      title: videoData.title || 'סרטון חדש',
      description: videoData.description || '',
      date: new Date().toLocaleDateString('he-IL'),
      duration: videoData.duration || '0:00',
      thumbnail: videoData.thumbnail || null,
      url: videoData.url || null,
      timestamp: Date.now()
    };

    const currentVideos = state.data.videos || [];
    journeyEngine.updateData('videos', [...currentVideos, newVideo]);

    return { success: true, video: newVideo, message: 'הסרטון הועלה בהצלחה' };
  };

  const handleDeleteVideo = async (videoId) => {
    const currentVideos = state.data.videos || [];
    const filtered = currentVideos.filter(v => v.id !== videoId);
    journeyEngine.updateData('videos', filtered);

    return { success: true, message: 'הסרטון נמחק' };
  };

  // CRUD handlers for journal entries
  const handleCreateJournalEntry = async (text, status) => {
    const newEntry = {
      id: journeyEngine.generateId(),
      text,
      status,
      timestamp: 'עכשיו',
      date: new Date()
    };

    const currentEntries = state.data.journalEntries || [];
    journeyEngine.updateData('journalEntries', [newEntry, ...currentEntries]);

    return { success: true, entry: newEntry, message: 'הרשומה נשמרה בהצלחה' };
  };

  const handleDeleteJournalEntry = async (entryId) => {
    const currentEntries = state.data.journalEntries || [];
    const filtered = currentEntries.filter(e => e.id !== entryId);
    journeyEngine.updateData('journalEntries', filtered);

    return { success: true, message: 'הרשומה נמחקה' };
  };

  // Handle input change (for draft saving)
  const handleInputChange = (value) => {
    conversationController.updateDraft(value);
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
              {state.data.childName ? `המסע ההתפתחותי של ${state.data.childName}` : 'המסע ההתפתחותי'}
            </p>
          </div>
          <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full flex items-center justify-center shadow-md">
            <MessageCircle className="w-5 h-5 text-white" />
          </div>
        </div>
      </div>

      {/* Conversation Transcript */}
      <ConversationTranscript messages={ui.messages} isTyping={isTyping} />

      {/* Contextual Surface */}
      <ContextualSurface cards={ui.cards} onCardClick={handleCardClick} />

      {/* Input Area */}
      <InputArea
        onSend={handleSend}
        onSuggestionsClick={() => setShowSuggestions(true)}
        hasSuggestions={ui.suggestions && ui.suggestions.length > 0}
        value={state.ui.draftMessage}
        onChange={handleInputChange}
      />

      {/* Suggestions Popup */}
      {showSuggestions && (
        <SuggestionsPopup
          suggestions={ui.suggestions}
          onSuggestionClick={(suggestion) => {
            handleSuggestionClick(suggestion.text, suggestion.action);
          }}
          onClose={() => setShowSuggestions(false)}
        />
      )}

      {/* Deep View Manager */}
      <DeepViewManager
        activeView={activeDeepView}
        onClose={handleCloseDeepView}
        viewData={state}
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
