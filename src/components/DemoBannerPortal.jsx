import React from 'react';
import { XCircle, PauseCircle, PlayCircle, SkipForward, Zap } from 'lucide-react';

/**
 * 🎬 Demo Mode Banner Portal
 *
 * Renders via React Portal - appears at top of screen during demo.
 * Controlled by DemoOrchestrator service.
 * App doesn't know about this component!
 */
export default function DemoBannerPortal({
  step,
  total,
  progress,
  speed,
  paused,
  isComplete,
  scenarioName,
  onSpeedChange,
  onPause,
  onResume,
  onSkip,
  onStop
}) {
  return (
    <div className="fixed top-16 left-0 right-0 z-50 px-4 animate-slideDown">
      <div className="max-w-3xl mx-auto">
        <div
          className={`${
            isComplete
              ? 'bg-gradient-to-r from-green-500 to-emerald-600'
              : 'bg-gradient-to-r from-orange-500 to-orange-600'
          } text-white rounded-lg shadow-2xl border-4 ${
            isComplete ? 'border-green-400' : 'border-orange-400'
          } overflow-hidden`}
          style={{
            backdropFilter: 'blur(10px)',
            animation: isComplete ? 'none' : 'pulse 2s ease-in-out infinite'
          }}
        >
          {/* Main Content */}
          <div className="p-4">
            <div className="flex items-center justify-between">
              {/* Title & Description */}
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-2xl">{isComplete ? '🎉' : '🎬'}</span>
                  <h3 className="text-lg font-bold">
                    {isComplete ? 'ההדגמה הושלמה!' : `מצב הדגמה: ${scenarioName}`}
                  </h3>
                </div>
                <p className="text-sm opacity-90">
                  {isComplete
                    ? 'ראית את כל התהליך - מראיון ועד הנחיות מותאמות'
                    : `שלב ${step} מתוך ${total}`}
                </p>
              </div>

              {/* Controls */}
              <div className="flex items-center gap-2 mr-2">
                {!isComplete && (
                  <>
                    {/* Speed Control */}
                    <div className="flex items-center gap-2 bg-white/20 rounded-lg px-3 py-2">
                      <Zap className="w-4 h-4" />
                      <select
                        value={speed}
                        onChange={(e) => onSpeedChange(Number(e.target.value))}
                        className="bg-transparent text-white font-semibold cursor-pointer outline-none text-sm"
                        style={{ direction: 'ltr' }}
                      >
                        <option value="0.5" className="text-gray-900">0.5x</option>
                        <option value="1" className="text-gray-900">1x</option>
                        <option value="2" className="text-gray-900">2x</option>
                        <option value="5" className="text-gray-900">5x</option>
                        <option value="10" className="text-gray-900">10x</option>
                      </select>
                    </div>

                    {/* Pause/Resume */}
                    <button
                      onClick={paused ? onResume : onPause}
                      className="p-2 bg-white/20 hover:bg-white/30 rounded-lg transition-all duration-200 hover:scale-110"
                      title={paused ? 'המשך' : 'השהה'}
                    >
                      {paused ? (
                        <PlayCircle className="w-5 h-5" />
                      ) : (
                        <PauseCircle className="w-5 h-5" />
                      )}
                    </button>

                    {/* Skip */}
                    <button
                      onClick={onSkip}
                      className="p-2 bg-white/20 hover:bg-white/30 rounded-lg transition-all duration-200 hover:scale-110"
                      title="דלג לשלב הבא"
                    >
                      <SkipForward className="w-5 h-5" />
                    </button>
                  </>
                )}

                {/* Stop */}
                <button
                  onClick={onStop}
                  className="p-2 bg-white/20 hover:bg-white/30 rounded-lg transition-all duration-200 hover:scale-110"
                  title="עצור דמו"
                >
                  <XCircle className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Progress Bar */}
            {!isComplete && (
              <div className="mt-3">
                <div className="flex items-center justify-between text-xs mb-1.5">
                  <span className="font-medium">
                    {paused ? '⏸️ מושהה' : '▶️ מתקדם...'}
                  </span>
                  <span className="font-bold">{progress}%</span>
                </div>
                <div className="w-full bg-white/30 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-white h-full transition-all duration-500 ease-out shadow-lg"
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
              </div>
            )}
          </div>

          {/* Pulsing indicator stripe at bottom */}
          {!isComplete && (
            <div className="h-1 bg-gradient-to-r from-yellow-300 via-orange-300 to-yellow-300 opacity-75 animate-shimmer"></div>
          )}
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
