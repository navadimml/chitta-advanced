import React from 'react';
import { X, Lightbulb } from 'lucide-react';
import * as Icons from 'lucide-react';

export default function SuggestionsPopup({ suggestions, onSuggestionClick, onClose }) {
  if (!suggestions || suggestions.length === 0) return null;

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-30 z-40 flex items-end justify-center" 
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-t-3xl w-full max-w-2xl p-5 shadow-2xl animate-slideUp" 
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-amber-500" />
            <h4 className="font-bold text-gray-900">הצעות</h4>
          </div>
          <button 
            onClick={onClose} 
            className="p-2 hover:bg-gray-100 rounded-full"
          >
            <X className="w-5 h-5 text-gray-600" />
          </button>
        </div>
        <div className="space-y-2">
          {suggestions.map((suggestion, idx) => {
            const Icon = Icons[suggestion.icon];
            return (
              <button
                key={idx}
                onClick={() => onSuggestionClick(suggestion.text)}
                className={`w-full ${suggestion.color} text-white px-4 py-3 rounded-xl text-sm font-semibold flex items-center gap-3 hover:shadow-lg transition`}
              >
                {Icon && <Icon className="w-5 h-5" />}
                {suggestion.text}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
