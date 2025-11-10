import React from 'react';
import { XCircle, PauseCircle, PlayCircle, SkipForward, Play } from 'lucide-react';

/**
 * 🎬 Demo Mode Banner
 *
 * Floating banner at top of screen during demo mode.
 * Semi-transparent to not block the view.
 * Shows progress and control buttons.
 */
export default function DemoBanner({ demoCard, onAction, isPaused, isStarted }) {
  if (!demoCard) return null;

  return (
    <div className="fixed top-16 left-0 right-0 z-50 px-4 animate-slideDown">
      <div className="max-w-3xl mx-auto">
        <div
          className="bg-gradient-to-r from-orange-500 to-orange-600 text-white rounded-lg shadow-2xl border-4 border-orange-400 overflow-hidden"
          style={{
            backdropFilter: 'blur(10px)',
            animation: 'pulse 2s ease-in-out infinite'
          }}
        >
          {/* Main Content */}
          <div className="p-4">
            <div className="flex items-center justify-between">
              {/* Title & Description */}
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-2xl">🎬</span>
                  <h3 className="text-lg font-bold">{demoCard.title}</h3>
                </div>
                <p className="text-sm opacity-90">{demoCard.body}</p>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2 mr-2">
                {!isStarted ? (
                  /* START Button - Large and prominent */
                  <button
                    onClick={() => onAction('start_demo')}
                    className="px-6 py-2 bg-white text-orange-600 font-bold rounded-lg shadow-lg hover:shadow-xl transition-all duration-200 hover:scale-110 flex items-center gap-2"
                  >
                    <Play className="w-5 h-5" />
                    התחל הדגמה
                  </button>
                ) : (
                  /* Normal controls when started */
                  <>
                    <button
                      onClick={() => onAction(isPaused ? 'resume_demo' : 'pause_demo')}
                      className="p-2 bg-white/20 hover:bg-white/30 rounded-lg transition-all duration-200 hover:scale-110"
                      title={isPaused ? 'המשך' : 'השהה'}
                    >
                      {isPaused ? (
                        <PlayCircle className="w-5 h-5" />
                      ) : (
                        <PauseCircle className="w-5 h-5" />
                      )}
                    </button>
                    <button
                      onClick={() => onAction('skip_step')}
                      className="p-2 bg-white/20 hover:bg-white/30 rounded-lg transition-all duration-200 hover:scale-110"
                      title="דלג"
                    >
                      <SkipForward className="w-5 h-5" />
                    </button>
                  </>
                )}
                <button
                  onClick={() => onAction('stop_demo')}
                  className="p-2 bg-white/20 hover:bg-white/30 rounded-lg transition-all duration-200 hover:scale-110"
                  title="עצור דמו"
                >
                  <XCircle className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Progress Bar */}
            {demoCard.progress !== undefined && (
              <div className="mt-3">
                <div className="flex items-center justify-between text-xs mb-1.5">
                  <span className="font-medium">{demoCard.step_indicator || 'בהדגמה...'}</span>
                  <span className="font-bold">{demoCard.progress}%</span>
                </div>
                <div className="w-full bg-white/30 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-white h-full transition-all duration-500 ease-out shadow-lg"
                    style={{ width: `${demoCard.progress}%` }}
                  ></div>
                </div>
              </div>
            )}
          </div>

          {/* Pulsing indicator stripe at bottom */}
          <div className="h-1 bg-gradient-to-r from-yellow-300 via-orange-300 to-yellow-300 opacity-75 animate-shimmer"></div>
        </div>
      </div>

      <style>{`
        @keyframes slideDown {
          from {
            transform: translateY(-100%);
            opacity: 0;
          }
          to {
            transform: translateY(0);
            opacity: 1;
          }
        }

        @keyframes pulse {
          0%, 100% {
            box-shadow: 0 4px 20px rgba(251, 146, 60, 0.5);
          }
          50% {
            box-shadow: 0 4px 30px rgba(251, 146, 60, 0.8);
          }
        }

        @keyframes shimmer {
          0% {
            background-position: -100% 0;
          }
          100% {
            background-position: 200% 0;
          }
        }

        .animate-slideDown {
          animation: slideDown 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
        }

        .animate-shimmer {
          background-size: 200% 100%;
          animation: shimmer 2s linear infinite;
        }
      `}</style>
    </div>
  );
}
