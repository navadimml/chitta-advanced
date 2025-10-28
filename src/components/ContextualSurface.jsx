import React from 'react';
import * as Icons from 'lucide-react';

const getStatusColor = (status) => {
  const colors = {
    completed: 'bg-green-50 border-green-200 text-green-700',
    pending: 'bg-orange-50 border-orange-200 text-orange-700',
    action: 'bg-blue-50 border-blue-200 text-blue-700',
    new: 'bg-purple-50 border-purple-200 text-purple-700',
    processing: 'bg-yellow-50 border-yellow-200 text-yellow-700',
    instruction: 'bg-indigo-50 border-indigo-200 text-indigo-700',
    expert: 'bg-teal-50 border-teal-200 text-teal-700',
    upcoming: 'bg-pink-50 border-pink-200 text-pink-700',
    active: 'bg-violet-50 border-violet-200 text-violet-700',
    progress: 'bg-cyan-50 border-cyan-200 text-cyan-700'
  };
  return colors[status] || 'bg-gray-50 border-gray-200 text-gray-700';
};

export default function ContextualSurface({ cards, onCardClick }) {
  return (
    <div className="bg-white border-t border-gray-200 p-4 shadow-lg">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-bold text-gray-600">פעיל עכשיו</h3>
        <div className="w-8 h-1 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"></div>
      </div>

      <div className="space-y-2">
        {cards.map((card, idx) => {
          const Icon = Icons[card.icon];
          return (
            <div
              key={idx}
              onClick={() => card.action && onCardClick(card.action)}
              className={`${getStatusColor(card.status)} border rounded-xl p-3 flex items-center justify-between ${
                card.action ? 'cursor-pointer hover:shadow-md hover:scale-[1.02]' : ''
              } transition-all duration-300 ease-out group`}
              style={{
                animation: `cardSlideIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) ${idx * 0.08}s both`,
              }}
            >
              <div className="flex items-center gap-3">
                <div className="p-2 bg-white rounded-lg shadow-sm">
                  {Icon && <Icon className="w-5 h-5" />}
                </div>
                <div>
                  <div className="font-semibold text-sm">{card.title}</div>
                  <div className="text-xs opacity-80">{card.subtitle}</div>
                </div>
              </div>
              {card.action && (
                <Icons.ChevronRight className="w-5 h-5 opacity-50 group-hover:opacity-100 transition" />
              )}
            </div>
          );
        })}
      </div>

      <style jsx>{`
        @keyframes cardSlideIn {
          from {
            opacity: 0;
            transform: translateY(12px) scale(0.96);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }
      `}</style>
    </div>
  );
}
