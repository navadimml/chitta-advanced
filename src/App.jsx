import React, { useState, useEffect } from 'react';
import { Menu, MessageCircle } from 'lucide-react';
import api from './services/api';
import ConversationTranscript from './components/ConversationTranscript';
import ContextualSurface from './components/ContextualSurface';
import InputArea from './components/InputArea';
import SuggestionsPopup from './components/SuggestionsPopup';
import DemoControls from './components/DemoControls';
import DeepViewManager from './components/DeepViewManager';

function App() {
  const [scenarios, setScenarios] = useState([]);
  const [currentScenario, setCurrentScenario] = useState('interview');
  const [masterState, setMasterState] = useState(null);
  const [messages, setMessages] = useState([]);
  const [contextCards, setContextCards] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [activeDeepView, setActiveDeepView] = useState(null);

  // Load scenarios on mount
  useEffect(() => {
    const loadScenarios = async () => {
      const scenarioList = await api.getAllScenarios();
      setScenarios(scenarioList);
    };
    loadScenarios();
  }, []);

  // Load scenario data when scenario changes
  useEffect(() => {
    const loadScenario = async () => {
      const data = await api.getScenario(currentScenario);
      setMasterState(data.masterState);
      setContextCards(data.contextCards);
      setSuggestions(data.suggestions);
      
      // Clear messages and replay them with delays
      setMessages([]);
      setIsTyping(false);
      
      data.messages.forEach((msg) => {
        setTimeout(() => {
          if (msg.sender === 'chitta') {
            setIsTyping(true);
          }
          setTimeout(() => {
            setMessages(prev => [...prev, msg]);
            setIsTyping(false);
          }, msg.sender === 'chitta' ? 800 : 0);
        }, msg.delay);
      });
    };
    
    loadScenario();
  }, [currentScenario]);

  // Handle scenario change from demo controls
  const handleScenarioChange = (scenarioKey) => {
    setCurrentScenario(scenarioKey);
    setActiveDeepView(null);
    setShowSuggestions(false);
  };

  // Handle sending a message
  const handleSend = async (message) => {
    const userMsg = { sender: 'user', text: message };
    setMessages(prev => [...prev, userMsg]);
    
    setIsTyping(true);
    const response = await api.sendMessage(message);
    setIsTyping(false);
    
    if (response.success) {
      setMessages(prev => [...prev, response.response]);
    }
  };

  // Handle card click
  const handleCardClick = async (action) => {
    const result = await api.triggerAction(action);
    if (result.success && result.deepView) {
      setActiveDeepView(result.deepView);
    }
  };

  // Handle suggestion click
  const handleSuggestionClick = (suggestionText) => {
    handleSend(suggestionText);
    setShowSuggestions(false);
  };

  // Handle deep view close
  const handleCloseDeepView = () => {
    setActiveDeepView(null);
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-blue-50 to-indigo-50" dir="rtl">
      {/* Demo Controls */}
      <DemoControls 
        scenarios={scenarios}
        currentScenario={currentScenario}
        onScenarioChange={handleScenarioChange}
      />

      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-4 flex items-center justify-between shadow-sm">
        <button className="p-2 hover:bg-gray-100 rounded-full transition">
          <Menu className="w-5 h-5 text-gray-600" />
        </button>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <h1 className="text-lg font-bold text-gray-800">Chitta</h1>
            <p className="text-xs text-gray-500">המסע ההתפתחותי של יוני</p>
          </div>
          <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full flex items-center justify-center shadow-md">
            <MessageCircle className="w-5 h-5 text-white" />
          </div>
        </div>
      </div>

      {/* Conversation Transcript */}
      <ConversationTranscript messages={messages} isTyping={isTyping} />

      {/* Contextual Surface */}
      <ContextualSurface cards={contextCards} onCardClick={handleCardClick} />

      {/* Input Area */}
      <InputArea 
        onSend={handleSend} 
        onSuggestionsClick={() => setShowSuggestions(true)}
        hasSuggestions={suggestions && suggestions.length > 0}
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
        viewData={masterState}
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
