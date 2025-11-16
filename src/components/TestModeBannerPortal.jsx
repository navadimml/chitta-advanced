/**
 * Test Mode Banner Portal
 *
 * Floating banner that shows test mode is active with controls.
 * Shows persona info and allows controlling the automated conversation.
 */

import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { testModeOrchestrator } from '../services/TestModeOrchestrator.jsx';

export function TestModeBannerPortal() {
  const [state, setState] = useState(testModeOrchestrator.getState());

  // Update state when orchestrator state changes
  useEffect(() => {
    const interval = setInterval(() => {
      setState(testModeOrchestrator.getState());
    }, 100);

    return () => clearInterval(interval);
  }, []);

  if (!state.active) {
    return null;
  }

  const { personaInfo, paused, speed, autoRunning } = state;

  const banner = (
    <div className="fixed top-0 left-0 right-0 z-50 bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-lg">
      <div className="max-w-6xl mx-auto px-6 py-3">
        <div className="flex items-center justify-between gap-4">
          {/* Left: Test Mode Info */}
          <div className="flex items-center gap-3">
            <div className="bg-white/20 px-3 py-1 rounded-full text-sm font-bold">
              🧪 מצב בדיקה
            </div>
            {personaInfo && (
              <div className="text-sm">
                <span className="font-semibold">{personaInfo.parent}</span>
                {' · '}
                <span className="opacity-90">{personaInfo.child}</span>
              </div>
            )}
          </div>

          {/* Center: Controls */}
          <div className="flex items-center gap-2">
            {/* Speed Control */}
            <div className="flex items-center gap-2 bg-white/10 rounded-lg px-3 py-1">
              <span className="text-xs opacity-75">מהירות:</span>
              <select
                value={speed}
                onChange={(e) => testModeOrchestrator.setSpeed(parseFloat(e.target.value))}
                className="bg-white/20 text-white text-sm rounded px-2 py-0.5 border-0 outline-none cursor-pointer"
              >
                <option value="0.5">0.5x</option>
                <option value="1">1x</option>
                <option value="2">2x</option>
                <option value="5">5x</option>
                <option value="10">10x</option>
              </select>
            </div>

            {/* Pause/Resume Button */}
            {autoRunning && (
              <button
                onClick={() => {
                  if (paused) {
                    testModeOrchestrator.resume();
                  } else {
                    testModeOrchestrator.pause();
                  }
                }}
                className="bg-white/20 hover:bg-white/30 px-4 py-1 rounded-lg text-sm font-medium transition"
              >
                {paused ? '▶️ המשך' : '⏸️ השהה'}
              </button>
            )}

            {/* Stop Button */}
            <button
              onClick={() => {
                if (window.confirm('האם לעצור את מצב הבדיקה?')) {
                  testModeOrchestrator.stop();
                  window.location.reload(); // Reload to reset state
                }
              }}
              className="bg-red-500 hover:bg-red-600 px-4 py-1 rounded-lg text-sm font-medium transition"
            >
              ⏹️ עצור
            </button>
          </div>

          {/* Right: Status */}
          <div className="flex items-center gap-2">
            {autoRunning && !paused && (
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-xs opacity-75">פעיל</span>
              </div>
            )}
            {paused && (
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
                <span className="text-xs opacity-75">מושהה</span>
              </div>
            )}
          </div>
        </div>

        {/* Persona Details (Expandable) */}
        {personaInfo && (
          <div className="mt-2 text-xs opacity-75 border-t border-white/20 pt-2">
            <strong>דאגה עיקרית:</strong> {personaInfo.concern}
          </div>
        )}
      </div>
    </div>
  );

  return createPortal(banner, document.body);
}
