import React, { useState } from 'react';
import { ArrowRight, Lightbulb } from 'lucide-react';

export default function InputArea({ onSend, onSuggestionsClick, hasSuggestions, value = '', onChange }) {
  const handleSend = () => {
    if (value.trim()) {
      onSend(value);
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
    <div className="bg-white border-t border-gray-200 p-4">
      <div className="flex gap-2">
        {hasSuggestions && (
          <button
            onClick={onSuggestionsClick}
            className="p-3 bg-amber-100 text-amber-600 rounded-full hover:bg-amber-200 transition flex-shrink-0"
            title="הצעות"
          >
            <Lightbulb className="w-5 h-5" />
          </button>
        )}
        <input
          type="text"
          value={value}
          onChange={handleChange}
          onKeyPress={handleKeyPress}
          placeholder="שאלי אותי משהו..."
          className="flex-1 px-4 py-3 bg-gray-50 border border-gray-200 rounded-full focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
          dir="rtl"
        />
        <button
          onClick={handleSend}
          className="p-3 bg-gradient-to-r from-indigo-500 to-purple-500 text-white rounded-full hover:shadow-lg transition flex-shrink-0"
        >
          <ArrowRight className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}
