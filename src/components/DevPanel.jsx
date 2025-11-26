import { useState, useEffect } from 'react';
import { Cog, Database, Trash2, RefreshCw, ChevronDown, ChevronUp, Clock, Loader2, Image } from 'lucide-react';
import { api } from '../api/client';

/**
 * Development Panel - Quick scenario seeding for testing
 *
 * Allows developers to:
 * - Seed test scenarios instantly
 * - Switch between test sessions
 * - Reset sessions
 * - See current session info
 *
 * Only visible in development mode
 */
export default function DevPanel({ currentFamilyId, onFamilyChange }) {
  const [isOpen, setIsOpen] = useState(false);
  const [scenarios, setScenarios] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [recentSessions, setRecentSessions] = useState(() => {
    // Load from localStorage
    const saved = localStorage.getItem('chitta_dev_sessions');
    return saved ? JSON.parse(saved) : [];
  });
  const [timelineLoading, setTimelineLoading] = useState(false);
  const [timelineResult, setTimelineResult] = useState(null);
  const [selectedTimelineStyle, setSelectedTimelineStyle] = useState('warm');

  // Load available scenarios on mount
  useEffect(() => {
    if (isOpen && scenarios.length === 0) {
      loadScenarios();
    }
  }, [isOpen]);

  const loadScenarios = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/dev/scenarios');
      const data = await response.json();
      setScenarios(Object.values(data.scenarios));
    } catch (error) {
      console.error('Failed to load scenarios:', error);
    }
  };

  const seedScenario = async (scenarioName) => {
    setLoading(true);
    setMessage('');

    // Generate a unique family ID
    const familyId = `${scenarioName}_${Date.now().toString(36)}`;

    try {
      const response = await fetch(
        `http://localhost:8000/api/dev/seed/${scenarioName}?family_id=${familyId}`,
        { method: 'POST' }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();

      if (data.success) {
        // Add to recent sessions
        const newSession = {
          familyId,
          scenario: scenarioName,
          description: data.description,
          timestamp: new Date().toISOString(),
        };

        const updated = [newSession, ...recentSessions.filter(s => s.familyId !== familyId)].slice(0, 10);
        setRecentSessions(updated);
        localStorage.setItem('chitta_dev_sessions', JSON.stringify(updated));

        // Show success message
        setMessage(`✅ Seeded: ${data.description}`);

        // Auto-switch to the new family
        setTimeout(() => {
          onFamilyChange(familyId);
          // Reload page to refresh with new data
          window.location.href = `/?family=${familyId}`;
        }, 500);
      }
    } catch (error) {
      setMessage(`❌ Error: ${error.message}`);
      console.error('Seed error:', error);
    } finally {
      setLoading(false);
    }
  };

  const switchToSession = (familyId) => {
    onFamilyChange(familyId);
    window.location.href = `/?family=${familyId}`;
  };

  const resetSession = async (familyId) => {
    if (!confirm(`Reset session ${familyId}?`)) return;

    setLoading(true);
    try {
      await fetch(`http://localhost:8000/api/dev/reset/${familyId}`, {
        method: 'DELETE',
      });

      // Remove from recent sessions
      const updated = recentSessions.filter(s => s.familyId !== familyId);
      setRecentSessions(updated);
      localStorage.setItem('chitta_dev_sessions', JSON.stringify(updated));

      setMessage(`🗑️ Deleted session: ${familyId}`);
    } catch (error) {
      setMessage(`❌ Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const clearAllSessions = () => {
    if (!confirm('Clear all recent sessions from the list?')) return;
    setRecentSessions([]);
    localStorage.removeItem('chitta_dev_sessions');
    setMessage('🗑️ Cleared all sessions');
  };

  const generateTimeline = async () => {
    if (!currentFamilyId) {
      setMessage('❌ No active session - seed a scenario first');
      return;
    }

    setTimelineLoading(true);
    setTimelineResult(null);
    setMessage('');

    try {
      const result = await api.generateTimeline(currentFamilyId, selectedTimelineStyle);

      if (result.success !== false) {
        setTimelineResult(result);
        setMessage(`✅ Timeline generated! ${result.event_count || 0} events`);
      } else {
        setMessage(`❌ Timeline error: ${result.error || 'Unknown error'}`);
      }
    } catch (error) {
      setMessage(`❌ Timeline error: ${error.message}`);
      console.error('Timeline generation error:', error);
    } finally {
      setTimelineLoading(false);
    }
  };

  return (
    <div className="fixed top-4 left-4 z-50">
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="bg-purple-600 text-white px-4 py-2 rounded-lg shadow-lg hover:bg-purple-700 flex items-center gap-2 transition-all"
        title="Developer Tools"
      >
        <Cog className="w-5 h-5" />
        <span className="font-medium">Dev Tools</span>
        {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </button>

      {/* Panel */}
      {isOpen && (
        <div className="mt-2 bg-white rounded-lg shadow-2xl border border-purple-200 w-96 max-h-[80vh] overflow-auto">
          {/* Header */}
          <div className="bg-purple-600 text-white px-4 py-3 rounded-t-lg">
            <h3 className="font-bold text-lg">🛠️ Developer Tools</h3>
            <p className="text-purple-100 text-sm">Quick scenario seeding</p>
          </div>

          {/* Current Session Info */}
          {currentFamilyId && (
            <div className="p-4 bg-purple-50 border-b border-purple-200">
              <div className="text-sm font-medium text-purple-900 mb-1">Current Session:</div>
              <div className="font-mono text-xs text-purple-700 break-all">{currentFamilyId}</div>
            </div>
          )}

          {/* Message */}
          {message && (
            <div className="p-3 bg-blue-50 border-b border-blue-200 text-sm">
              {message}
            </div>
          )}

          {/* Seed New Scenario */}
          <div className="p-4 border-b border-gray-200">
            <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <Database className="w-4 h-4" />
              Seed New Scenario
            </h4>
            <div className="space-y-2">
              {scenarios.map((scenario) => (
                <button
                  key={scenario.name}
                  onClick={() => seedScenario(scenario.name)}
                  disabled={loading}
                  className={`w-full text-left p-3 rounded-lg border transition-all disabled:opacity-50 disabled:cursor-not-allowed ${
                    scenario.name === 'living_dashboard'
                      ? 'border-indigo-400 hover:border-indigo-600 hover:bg-indigo-50 bg-indigo-50/50'
                      : 'border-gray-300 hover:border-purple-500 hover:bg-purple-50'
                  }`}
                >
                  <div className="font-medium text-gray-900 text-sm mb-1">
                    {scenario.name === 'living_dashboard' && '🌟 '}
                    {scenario.name === 'guidelines_ready' && '⭐ '}
                    {scenario.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </div>
                  <div className="text-xs text-gray-600 mb-2">{scenario.description}</div>
                  <div className="flex gap-3 text-xs text-gray-500">
                    <span>📊 {Math.round(scenario.completeness * 100)}%</span>
                    <span>💬 {scenario.message_count} msgs</span>
                  </div>
                </button>
              ))}
            </div>
            {scenarios.length === 0 && (
              <div className="text-sm text-gray-500 text-center py-4">
                <RefreshCw className="w-4 h-4 mx-auto mb-2 animate-spin" />
                Loading scenarios...
              </div>
            )}
          </div>

          {/* Recent Sessions */}
          {recentSessions.length > 0 && (
            <div className="p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                  <RefreshCw className="w-4 h-4" />
                  Recent Sessions
                </h4>
                <button
                  onClick={clearAllSessions}
                  className="text-xs text-red-600 hover:text-red-700"
                  title="Clear all"
                >
                  Clear All
                </button>
              </div>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {recentSessions.map((session) => (
                  <div
                    key={session.familyId}
                    className={`p-3 rounded-lg border ${
                      session.familyId === currentFamilyId
                        ? 'border-purple-500 bg-purple-50'
                        : 'border-gray-300 bg-gray-50'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <div className="font-mono text-xs text-gray-700 truncate mb-1">
                          {session.familyId}
                        </div>
                        <div className="text-xs text-gray-500">{session.description}</div>
                      </div>
                      <div className="flex gap-1 flex-shrink-0">
                        {session.familyId !== currentFamilyId && (
                          <button
                            onClick={() => switchToSession(session.familyId)}
                            className="p-1 text-purple-600 hover:bg-purple-100 rounded"
                            title="Switch to this session"
                          >
                            <RefreshCw className="w-4 h-4" />
                          </button>
                        )}
                        <button
                          onClick={() => resetSession(session.familyId)}
                          className="p-1 text-red-600 hover:bg-red-100 rounded"
                          title="Delete session"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Timeline Generator */}
          <div className="p-4 border-t border-gray-200">
            <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <Clock className="w-4 h-4" />
              Timeline Generator
              <span className="text-xs font-normal text-amber-600 bg-amber-50 px-2 py-0.5 rounded">Gemini 3 Pro</span>
            </h4>

            {/* Style Selection */}
            <div className="flex gap-2 mb-3">
              {[
                { id: 'warm', label: 'חמים', emoji: '🌅' },
                { id: 'professional', label: 'מקצועי', emoji: '💼' },
                { id: 'playful', label: 'משחקי', emoji: '🎨' }
              ].map(style => (
                <button
                  key={style.id}
                  onClick={() => setSelectedTimelineStyle(style.id)}
                  className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all ${
                    selectedTimelineStyle === style.id
                      ? 'bg-amber-500 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {style.emoji} {style.label}
                </button>
              ))}
            </div>

            {/* Generate Button */}
            <button
              onClick={generateTimeline}
              disabled={timelineLoading || !currentFamilyId}
              className="w-full py-3 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white font-bold rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {timelineLoading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Image className="w-5 h-5" />
                  Generate Timeline Infographic
                </>
              )}
            </button>

            {/* Result Preview */}
            {timelineResult && timelineResult.image_url && (
              <div className="mt-3 p-2 bg-amber-50 border border-amber-200 rounded-lg">
                <img
                  src={timelineResult.image_url}
                  alt="Generated Timeline"
                  className="w-full rounded-lg shadow-sm"
                />
                <div className="mt-2 flex gap-2">
                  <a
                    href={timelineResult.image_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 py-2 text-center text-amber-700 bg-white border border-amber-300 rounded-lg text-sm font-medium hover:bg-amber-50"
                  >
                    Open Full Size
                  </a>
                  <a
                    href={timelineResult.image_url}
                    download={`timeline_${currentFamilyId}.png`}
                    className="flex-1 py-2 text-center text-white bg-amber-500 rounded-lg text-sm font-medium hover:bg-amber-600"
                  >
                    Download
                  </a>
                </div>
              </div>
            )}

            {!currentFamilyId && (
              <p className="mt-2 text-xs text-gray-500 text-center">
                Seed a scenario first to generate timeline
              </p>
            )}
          </div>

          {/* Footer */}
          <div className="p-3 bg-gray-50 rounded-b-lg text-xs text-gray-500 text-center border-t border-gray-200">
            💡 Seeding creates new sessions. Guidelines take ~60s to generate.
          </div>
        </div>
      )}
    </div>
  );
}
