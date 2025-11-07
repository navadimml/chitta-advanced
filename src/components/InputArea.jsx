import React, { useState } from 'react';
import { ArrowRight, Lightbulb } from 'lucide-react';

export default function InputArea({ onSend, onSuggestionsClick, hasSuggestions, value = '', onChange }) {
  const [isFocused, setIsFocused] = useState(false);
  const [isSending, setIsSending] = useState(false);

  const handleSend = async () => {
    if (value.trim()) {
      setIsSending(true);
      await onSend(value);
      // Reset after a brief delay for animation
      setTimeout(() => setIsSending(false), 300);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleChange = (e) => {
    if (onChange) {
      onChange(e.target.value);
    }
  };

  return (
    <div className="bg-white border-t border-gray-200 p-4 shadow-lg">
      {/* Centered container on desktop */}
      <div className="max-w-3xl mx-auto">
        <div className="flex gap-3 transition-all duration-300">
          {hasSuggestions && (
            <button
              onClick={onSuggestionsClick}
              className="p-3.5 bg-gradient-to-br from-amber-400 to-amber-500 text-white rounded-2xl hover:scale-110 hover:shadow-xl hover:shadow-amber-200/50 active:scale-95 transition-all duration-200 flex-shrink-0 group"
              title="הצעות"
            >
              <Lightbulb className="w-6 h-6 group-hover:rotate-12 transition-transform duration-200" />
            </button>
          )}
          <input
            type="text"
            value={value}
            onChange={handleChange}
            onKeyPress={handleKeyPress}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder="כתבי כאן את המחשבות שלך..."
            className={`flex-1 px-6 py-4 text-base bg-gray-50 border-2 rounded-2xl focus:outline-none transition-all duration-300 ${
              isFocused
                ? 'border-indigo-400 bg-white shadow-lg shadow-indigo-100/50'
                : 'border-gray-200 hover:border-gray-300 hover:bg-gray-100'
            }`}
            dir="rtl"
          />
          <button
            onClick={handleSend}
            disabled={!value.trim() || isSending}
            className={`p-3.5 bg-gradient-to-br from-indigo-500 to-purple-600 text-white rounded-2xl transition-all duration-200 flex-shrink-0 ${
              value.trim() && !isSending
                ? 'hover:scale-110 hover:shadow-xl hover:shadow-indigo-200/50 active:scale-95'
                : 'opacity-50 cursor-not-allowed'
            } ${isSending ? 'animate-pulse' : ''}`}
          >
            <ArrowRight className={`w-6 h-6 transition-transform duration-200 ${
              isSending ? 'translate-x-1' : ''
            }`} />
          </button>
        </div>

        {/* Typing indicator - always rendered to prevent layout shift */}
        <div
          className="mt-2 text-xs text-gray-400 text-center transition-opacity duration-200"
          style={{
            opacity: value.length > 0 ? 1 : 0,
            minHeight: '1rem'
          }}
        >
          {value.length > 100 ? '✨ מדהים! המשיכי לשתף' : ''}
        </div>
      </div>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(-4px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
