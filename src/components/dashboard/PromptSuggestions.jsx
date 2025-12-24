import React, { useState, useEffect } from 'react';
import {
  Lightbulb,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  FileCode,
  BookOpen,
  Clock,
  Target,
  Layers,
  RefreshCw,
  Filter,
  Eye,
  X,
} from 'lucide-react';
import { api } from '../../api/client';

/**
 * Prompt Suggestions Component
 *
 * Displays AI prompt improvement suggestions based on expert corrections.
 * Part of the Training Pipeline - Phase 7.
 */
export default function PromptSuggestions() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [report, setReport] = useState(null);
  const [expandedSuggestion, setExpandedSuggestion] = useState(null);
  const [selectedExample, setSelectedExample] = useState(null);
  const [unusedOnly, setUnusedOnly] = useState(true);
  const [minCorrections, setMinCorrections] = useState(1);

  useEffect(() => {
    loadSuggestions();
  }, [unusedOnly, minCorrections]);

  async function loadSuggestions() {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getPromptSuggestions(unusedOnly, minCorrections);
      setReport(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center h-96">
        <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          Error loading suggestions: {error}
        </div>
      </div>
    );
  }

  const hasCorrections = report?.total_corrections > 0 || report?.total_missed_signals > 0;

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Prompt Improvement Suggestions</h1>
          <p className="text-gray-500 mt-1">
            AI-generated suggestions based on {report?.total_corrections || 0} corrections and {report?.total_missed_signals || 0} missed signals
          </p>
        </div>

        <button
          onClick={loadSuggestions}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 mb-6">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <span className="text-sm text-gray-600">Filters:</span>
          </div>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={unusedOnly}
              onChange={(e) => setUnusedOnly(e.target.checked)}
              className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
            />
            <span className="text-sm text-gray-700">Unused corrections only</span>
          </label>

          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">Min corrections:</span>
            <input
              type="number"
              value={minCorrections}
              onChange={(e) => setMinCorrections(Math.max(1, parseInt(e.target.value) || 1))}
              min="1"
              className="w-16 px-2 py-1 border border-gray-300 rounded text-sm"
            />
          </div>
        </div>
      </div>

      {!hasCorrections ? (
        /* Empty State */
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <Lightbulb className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <h2 className="text-xl font-semibold text-gray-600 mb-2">No Corrections Yet</h2>
          <p className="text-gray-500 max-w-md mx-auto">
            Start reviewing AI decisions in the Timeline view and add corrections.
            Once you have corrections, prompt improvement suggestions will appear here.
          </p>
        </div>
      ) : (
        <>
          {/* Stats Summary */}
          <div className="grid grid-cols-4 gap-4 mb-6">
            <StatCard
              icon={<Target className="w-5 h-5 text-amber-600" />}
              label="Suggestions"
              value={report?.suggestion_count || 0}
            />
            <StatCard
              icon={<AlertTriangle className="w-5 h-5 text-red-600" />}
              label="Total Corrections"
              value={report?.total_corrections || 0}
            />
            <StatCard
              icon={<Eye className="w-5 h-5 text-purple-600" />}
              label="Missed Signals"
              value={report?.total_missed_signals || 0}
            />
            <StatCard
              icon={<Layers className="w-5 h-5 text-blue-600" />}
              label="Correction Types"
              value={Object.keys(report?.stats?.corrections?.by_type || {}).length}
            />
          </div>

          {/* Suggestions List */}
          {report?.suggestions?.length === 0 ? (
            <div className="bg-gray-50 rounded-lg p-8 text-center text-gray-500">
              <p>No suggestions generated. Try adjusting the minimum corrections filter.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {report?.suggestions?.map((suggestion, index) => (
                <SuggestionCard
                  key={index}
                  suggestion={suggestion}
                  isExpanded={expandedSuggestion === index}
                  onToggle={() => setExpandedSuggestion(
                    expandedSuggestion === index ? null : index
                  )}
                  onViewExample={setSelectedExample}
                />
              ))}
            </div>
          )}

          {/* Stats Breakdown */}
          {report?.stats && (
            <div className="mt-8 grid grid-cols-2 gap-6">
              <StatsBreakdown
                title="Corrections by Type"
                data={report.stats.corrections?.by_type || {}}
              />
              <StatsBreakdown
                title="Corrections by Severity"
                data={report.stats.corrections?.by_severity || {}}
                colorMap={{
                  critical: 'bg-red-100 text-red-700',
                  high: 'bg-orange-100 text-orange-700',
                  medium: 'bg-yellow-100 text-yellow-700',
                  low: 'bg-green-100 text-green-700',
                }}
              />
            </div>
          )}
        </>
      )}

      {/* Example Modal */}
      {selectedExample && (
        <ExampleModal
          example={selectedExample}
          onClose={() => setSelectedExample(null)}
        />
      )}
    </div>
  );
}

/**
 * Stat Card Component
 */
function StatCard({ icon, label, value }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-gray-50 rounded-lg">{icon}</div>
        <div>
          <div className="text-xl font-bold text-gray-900">{value}</div>
          <div className="text-xs text-gray-500">{label}</div>
        </div>
      </div>
    </div>
  );
}

/**
 * Suggestion Card Component
 */
function SuggestionCard({ suggestion, isExpanded, onToggle, onViewExample }) {
  const priorityColors = {
    1: 'bg-red-100 text-red-700 border-red-200',
    2: 'bg-orange-100 text-orange-700 border-orange-200',
    3: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  };

  const priorityColor = priorityColors[suggestion.priority] || 'bg-gray-100 text-gray-700 border-gray-200';

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div
        className="p-4 cursor-pointer hover:bg-gray-50 transition"
        onClick={onToggle}
      >
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3 flex-1">
            <span className={`px-2 py-0.5 rounded text-xs font-medium border ${priorityColor}`}>
              #{suggestion.priority}
            </span>

            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <FileCode className="w-4 h-4 text-gray-400" />
                <span className="text-sm font-medium text-gray-700">{suggestion.section}</span>
              </div>
              <h3 className="font-medium text-gray-900">{suggestion.issue}</h3>
            </div>

            <div className="flex items-center gap-4 text-sm text-gray-500">
              <span title="Correction count">
                {suggestion.correction_count} corrections
              </span>
              <span title="Severity score" className="font-medium">
                Score: {suggestion.severity_score}
              </span>
            </div>
          </div>

          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-400" />
          )}
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="border-t border-gray-100 p-4 bg-gray-50">
          {/* Suggestion */}
          <div className="mb-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
              <Lightbulb className="w-4 h-4 text-amber-500" />
              Suggested Fix
            </h4>
            <p className="text-sm text-gray-600 bg-white rounded-lg p-3 border border-gray-200">
              {suggestion.suggestion}
            </p>
          </div>

          {/* Examples */}
          {suggestion.examples?.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-blue-500" />
                Expert Examples ({suggestion.examples.length})
              </h4>
              <div className="space-y-2">
                {suggestion.examples.map((example, idx) => (
                  <div
                    key={idx}
                    className="bg-white rounded-lg p-3 border border-gray-200 cursor-pointer hover:border-indigo-300 transition"
                    onClick={(e) => {
                      e.stopPropagation();
                      onViewExample(example);
                    }}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="text-xs text-gray-500 mb-1">
                          {example.target_type} • {example.severity}
                        </div>
                        <p className="text-sm text-gray-700 line-clamp-2" dir="rtl">
                          {example.expert_reasoning}
                        </p>
                      </div>
                      <Eye className="w-4 h-4 text-gray-400 ml-2 flex-shrink-0" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Stats Breakdown Component
 */
function StatsBreakdown({ title, data, colorMap = {} }) {
  const entries = Object.entries(data);

  if (entries.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <h3 className="text-sm font-medium text-gray-700 mb-3">{title}</h3>
      <div className="space-y-2">
        {entries.map(([key, value]) => (
          <div key={key} className="flex items-center justify-between">
            <span className={`text-sm px-2 py-0.5 rounded ${colorMap[key] || 'bg-gray-100 text-gray-700'}`}>
              {key.replace(/_/g, ' ')}
            </span>
            <span className="text-sm font-medium text-gray-900">{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Example Modal Component
 */
function ExampleModal({ example, onClose }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl max-w-2xl w-full max-h-[80vh] overflow-hidden shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-100">
          <h3 className="font-semibold text-gray-900">Correction Example</h3>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded transition"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto max-h-[calc(80vh-120px)]">
          {/* Meta */}
          <div className="flex items-center gap-4 mb-4 text-sm">
            <span className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded">
              {example.target_type}
            </span>
            <span className={`px-2 py-0.5 rounded ${
              example.severity === 'critical' ? 'bg-red-100 text-red-700' :
              example.severity === 'high' ? 'bg-orange-100 text-orange-700' :
              example.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
              'bg-green-100 text-green-700'
            }`}>
              {example.severity}
            </span>
          </div>

          {/* Expert Reasoning - The GOLD */}
          <div className="mb-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Expert Reasoning</h4>
            <div className="bg-amber-50 border border-amber-100 rounded-lg p-3" dir="rtl">
              <p className="text-sm text-amber-900">{example.expert_reasoning}</p>
            </div>
          </div>

          {/* Original vs Corrected */}
          {(example.original || example.corrected_value) && (
            <div className="grid grid-cols-2 gap-4">
              {example.original && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Original</h4>
                  <pre className="bg-red-50 border border-red-100 rounded-lg p-3 text-xs overflow-auto">
                    {JSON.stringify(example.original, null, 2)}
                  </pre>
                </div>
              )}
              {example.corrected_value && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Corrected</h4>
                  <pre className="bg-green-50 border border-green-100 rounded-lg p-3 text-xs overflow-auto">
                    {JSON.stringify(example.corrected_value, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}

          {/* Why Important (for missed signals) */}
          {example.why_important && (
            <div className="mt-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Why Important</h4>
              <div className="bg-purple-50 border border-purple-100 rounded-lg p-3" dir="rtl">
                <p className="text-sm text-purple-900">{example.why_important}</p>
              </div>
            </div>
          )}

          {/* Content (for missed signals) */}
          {example.content && (
            <div className="mt-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Missed Content</h4>
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-3" dir="rtl">
                <p className="text-sm text-gray-700">{example.content}</p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-100 bg-gray-50">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
