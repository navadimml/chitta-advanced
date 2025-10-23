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
