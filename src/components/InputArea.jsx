import React, { useState, useRef, useEffect } from 'react';
import { ArrowRight, Lightbulb } from 'lucide-react';

export default function InputArea({ onSend, onSuggestionsClick, hasSuggestions, value = '', onChange }) {
  const [isFocused, setIsFocused] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const textareaRef = useRef(null);

  const handleSend = async () => {
    if (value.trim()) {
      setIsSending(true);
      await onSend(value);
      // Reset after a brief delay for animation
      setTimeout(() => setIsSending(false), 300);
    }
  };

  const handleKeyDown = (e) => {
    // Enter alone = send message
    // Shift+Enter = new line
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleChange = (e) => {
    if (onChange) {
      onChange(e.target.value);
    }
    // Auto-resize textarea
    autoResize();
  };

  const autoResize = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      // Reset height to auto to get the correct scrollHeight
      textarea.style.height = 'auto';
      // Set height to scrollHeight (content height)
      // Max height of 200px (about 8 lines)
      const newHeight = Math.min(textarea.scrollHeight, 200);
      textarea.style.height = `${newHeight}px`;

      // Only show scrollbar when content exceeds max height
      if (textarea.scrollHeight > 200) {
        textarea.style.overflowY = 'auto';
      } else {
        textarea.style.overflowY = 'hidden';
      }
    }
  };

  // Auto-resize on mount and when value changes externally
  useEffect(() => {
    autoResize();
  }, [value]);

  return (
    <div className="bg-white border-t border-gray-200 p-4 shadow-lg">
      {/* Centered container on desktop */}
      <div className="max-w-3xl mx-auto">
        <div className="flex gap-3 items-end transition-all duration-300">
          {hasSuggestions && (
            <button
              onClick={onSuggestionsClick}
              className="p-3.5 bg-gradient-to-br from-amber-400 to-amber-500 text-white rounded-2xl hover:scale-110 hover:shadow-xl hover:shadow-amber-200/50 active:scale-95 transition-all duration-200 flex-shrink-0 group"
              title="הצעות"
            >
              <Lightbulb className="w-6 h-6 group-hover:rotate-12 transition-transform duration-200" />
            </button>
          )}
          <textarea
            ref={textareaRef}
            value={value}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder="כתבי כאן את המחשבות שלך..."
            rows={1}
            className={`flex-1 px-6 py-4 text-base bg-gray-50 border-2 rounded-2xl focus:outline-none transition-all duration-300 resize-none overflow-y-hidden custom-textarea ${
              isFocused
                ? 'border-indigo-400 bg-white shadow-lg shadow-indigo-100/50'
                : 'border-gray-200 hover:border-gray-300 hover:bg-gray-100'
            }`}
            style={{
              minHeight: '56px',
              maxHeight: '200px'
            }}
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

        {/* Typing indicator - always rendered to prevent jumping */}
        <div
          className="mt-2 text-xs text-gray-400 text-center"
          style={{
            minHeight: '16px',
            visibility: value.length > 0 || isFocused ? 'visible' : 'hidden',
            opacity: value.length > 0 || isFocused ? 1 : 0,
            transition: 'opacity 0.2s ease-out'
          }}
        >
          {value.length > 100
            ? '✨ מדהים! המשיכי לשתף'
            : isFocused && value.length === 0
            ? 'Shift+Enter לשורה חדשה • Enter לשליחה'
            : ''}
        </div>
      </div>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(-4px); }
          to { opacity: 1; transform: translateY(0); }
        }

        /* Custom scrollbar styling for textarea in RTL */
        .custom-textarea::-webkit-scrollbar {
          width: 8px;
        }

        .custom-textarea::-webkit-scrollbar-track {
          background: transparent;
          border-radius: 16px;
        }

        .custom-textarea::-webkit-scrollbar-thumb {
          background: rgba(99, 102, 241, 0.3);
          border-radius: 16px;
          border: 2px solid transparent;
          background-clip: padding-box;
        }

        .custom-textarea::-webkit-scrollbar-thumb:hover {
          background: rgba(99, 102, 241, 0.5);
          border: 2px solid transparent;
          background-clip: padding-box;
        }

        /* Firefox scrollbar styling */
        .custom-textarea {
          scrollbar-width: thin;
          scrollbar-color: rgba(99, 102, 241, 0.3) transparent;
        }
      `}</style>
    </div>
  );
}
