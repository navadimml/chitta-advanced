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
        <h3 className="text-base font-bold text-gray-600">פעיל עכשיו</h3>
        <div className="w-8 h-1 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"></div>
      </div>

      <div className="space-y-2">
        {cards.map((card, idx) => {
          const Icon = Icons[card.icon];
          const isStatusCard = card.type === 'status' && card.journey_step && card.journey_total;

          return (
            <div
              key={idx}
              onClick={() => card.action && onCardClick(card.action)}
              className={`${getStatusColor(card.status)} ${
                card.status === 'instruction' ? 'border-2 p-4' : 'border p-3'
              } rounded-xl ${
                card.action ? 'cursor-pointer hover:shadow-lg hover:scale-[1.03] active:scale-[0.99]' : ''
              } ${card.status === 'processing' ? 'animate-pulse-subtle' : ''} transition-all duration-300 ease-out group relative overflow-hidden`}
              style={{
                animation: `cardSlideIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) ${idx * 0.08}s both`,
              }}
            >
              {/* Shimmer overlay for 'new' cards */}
              {card.status === 'new' && (
                <div className="absolute inset-0 shimmer-overlay"></div>
              )}

              <div className="flex items-center justify-between relative z-10">
                <div className="flex items-center gap-3 flex-1">
                  <div className={`p-2 bg-white rounded-lg shadow-sm ${
                    card.status === 'processing' ? 'animate-spin-slow' : ''
                  } ${card.status === 'instruction' ? 'p-3' : ''} transition-all duration-300`}>
                    {Icon && <Icon className={`${
                      card.status === 'instruction' ? 'w-7 h-7' : 'w-5 h-5'
                    } ${
                      card.status === 'processing' ? 'text-yellow-600' : ''
                    }`} />}
                  </div>
                  <div className="flex-1">
                    <div className={`font-semibold flex items-center gap-2 ${
                      card.status === 'instruction' ? 'text-lg' : 'text-base'
                    }`}>
                      {card.title}
                      {card.status === 'processing' && (
                        <span className="loading-dots">
                          <span className="dot"></span>
                          <span className="dot"></span>
                          <span className="dot"></span>
                        </span>
                      )}
                    </div>
                    <div className={`opacity-90 leading-relaxed ${
                      card.status === 'instruction' ? 'text-base mt-1' : 'text-sm opacity-80'
                    }`}>{card.subtitle}</div>

                    {/* Breadcrumbs - ברור ובולט */}
                    {isStatusCard && (
                      <div className="mt-2.5 flex items-center gap-1.5 text-[11px]">
                        {/* ראיון */}
                        <span className={`flex items-center gap-1 ${card.journey_step >= 1 ? 'text-violet-500 font-medium' : 'text-gray-400'}`}>
                          {card.journey_step > 1 && <span className="text-[9px]">✓</span>}
                          <span>ראיון</span>
                        </span>
                        <span className="text-gray-300 text-[10px]">→</span>

                        {/* צילום */}
                        <span className={`flex items-center gap-1 ${
                          card.journey_step === 2
                            ? 'bg-violet-100 text-violet-700 font-semibold px-2 py-0.5 rounded-md'
                            : card.journey_step > 2
                            ? 'text-violet-500 font-medium'
                            : 'text-gray-400'
                        }`}>
                          {card.journey_step > 2 && <span className="text-[9px]">✓</span>}
                          <span>צילום</span>
                        </span>
                        <span className="text-gray-300 text-[10px]">→</span>

                        {/* ניתוח */}
                        <span className={`flex items-center gap-1 ${
                          card.journey_step === 3
                            ? 'bg-violet-100 text-violet-700 font-semibold px-2 py-0.5 rounded-md'
                            : card.journey_step > 3
                            ? 'text-violet-500 font-medium'
                            : 'text-gray-400'
                        }`}>
                          {card.journey_step > 3 && <span className="text-[9px]">✓</span>}
                          <span>ניתוח</span>
                        </span>
                        <span className="text-gray-300 text-[10px]">→</span>

                        {/* דוחות */}
                        <span className={`flex items-center gap-1 ${
                          card.journey_step === 4
                            ? 'bg-violet-100 text-violet-700 font-semibold px-2 py-0.5 rounded-md'
                            : card.journey_step > 4
                            ? 'text-violet-500 font-medium'
                            : 'text-gray-400'
                        }`}>
                          {card.journey_step > 4 && <span className="text-[9px]">✓</span>}
                          <span>דוחות</span>
                        </span>
                        <span className="text-gray-300 text-[10px]">→</span>

                        {/* ייעוץ */}
                        <span className={`flex items-center gap-1 ${
                          card.journey_step === 5
                            ? 'bg-violet-100 text-violet-700 font-semibold px-2 py-0.5 rounded-md'
                            : card.journey_step > 5
                            ? 'text-violet-500 font-medium'
                            : 'text-gray-400'
                        }`}>
                          {card.journey_step > 5 && <span className="text-[9px]">✓</span>}
                          <span>ייעוץ</span>
                        </span>
                      </div>
                    )}
                  </div>
                </div>
                {card.action && (
                  <Icons.ChevronRight className="w-5 h-5 opacity-50 group-hover:opacity-100 transition" />
                )}
              </div>
            </div>
          );
        })}
      </div>

      <style>{`
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

        @keyframes pulseSubtle {
          0%, 100% {
            opacity: 1;
            box-shadow: 0 0 0 0 rgba(251, 191, 36, 0.2);
          }
          50% {
            opacity: 0.95;
            box-shadow: 0 0 0 6px rgba(251, 191, 36, 0);
          }
        }

        @keyframes shimmerMove {
          0% {
            transform: translateX(-100%);
          }
          100% {
            transform: translateX(100%);
          }
        }

        @keyframes spinSlow {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }

        .animate-pulse-subtle {
          animation: pulseSubtle 2s ease-in-out infinite;
        }

        .animate-spin-slow {
          animation: spinSlow 3s linear infinite;
        }

        .shimmer-overlay {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: linear-gradient(
            90deg,
            transparent 0%,
            rgba(255, 255, 255, 0.4) 50%,
            transparent 100%
          );
          animation: shimmerMove 2.5s ease-in-out infinite;
          pointer-events: none;
        }

        @keyframes dotBounce {
          0%, 80%, 100% {
            opacity: 0.3;
            transform: scale(0.8);
          }
          40% {
            opacity: 1;
            transform: scale(1);
          }
        }

        .loading-dots {
          display: inline-flex;
          gap: 3px;
          align-items: center;
        }

        .loading-dots .dot {
          width: 4px;
          height: 4px;
          background-color: currentColor;
          border-radius: 50%;
          display: inline-block;
          animation: dotBounce 1.4s ease-in-out infinite;
        }

        .loading-dots .dot:nth-child(1) {
          animation-delay: 0s;
        }

        .loading-dots .dot:nth-child(2) {
          animation-delay: 0.2s;
        }

        .loading-dots .dot:nth-child(3) {
          animation-delay: 0.4s;
        }
      `}</style>
    </div>
  );
}
