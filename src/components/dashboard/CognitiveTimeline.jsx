import React, { useState, useEffect } from 'react';
import {
  Clock,
  ChevronDown,
  ChevronUp,
  MessageSquare,
  Wrench,
  Brain,
  ArrowRight,
  Lightbulb,
  AlertTriangle,
  Plus,
  Check,
  X,
  Video,
  FlaskConical,
  Eye,
  HelpCircle,
} from 'lucide-react';
import { api } from '../../api/client';

/**
 * Cognitive Timeline Component
 *
 * Displays the full cognitive trace for each conversation turn.
 * Allows experts to review AI's thinking and add corrections.
 */
export default function CognitiveTimeline({ childId }) {
  const [timeline, setTimeline] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedTurns, setExpandedTurns] = useState(new Set());

  useEffect(() => {
    loadTimeline();
  }, [childId]);

  async function loadTimeline() {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getCognitiveTimeline(childId);
      setTimeline(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const toggleTurn = (turnId) => {
    const newExpanded = new Set(expandedTurns);
    if (newExpanded.has(turnId)) {
      newExpanded.delete(turnId);
    } else {
      newExpanded.add(turnId);
    }
    setExpandedTurns(newExpanded);
  };

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          Error loading timeline: {error}
        </div>
      </div>
    );
  }

  if (!timeline?.turns?.length) {
    return (
      <div className="p-8 text-center text-gray-500">
        <Clock className="w-12 h-12 mx-auto mb-4 text-gray-300" />
        <p>No cognitive traces recorded yet</p>
        <p className="text-sm mt-2">
          Cognitive traces are recorded for each conversation turn
        </p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Cognitive Timeline</h2>
          <p className="text-sm text-gray-500">
            {timeline.total_turns} turns | {timeline.total_corrections} corrections | {timeline.total_missed_signals} missed signals
          </p>
        </div>
        <button
          onClick={loadTimeline}
          className="px-4 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition text-sm"
        >
          Refresh
        </button>
      </div>

      {/* Timeline */}
      <div className="space-y-3">
        {timeline.turns.map((turn) => (
          <TurnCard
            key={turn.turn_id}
            turn={turn}
            childId={childId}
            isExpanded={expandedTurns.has(turn.turn_id)}
            onToggle={() => toggleTurn(turn.turn_id)}
            onRefresh={loadTimeline}
          />
        ))}
      </div>
    </div>
  );
}

/**
 * Turn Card Component
 * Displays a single cognitive turn with expandable details
 */
function TurnCard({ turn, childId, isExpanded, onToggle, onRefresh }) {
  const [showCorrectionForm, setShowCorrectionForm] = useState(false);
  const [showMissedSignalForm, setShowMissedSignalForm] = useState(false);

  const hasIssues = turn.corrections_count > 0 || turn.missed_signals_count > 0;

  return (
    <div
      className={`bg-white rounded-xl shadow-sm border ${
        hasIssues ? 'border-amber-200' : 'border-gray-100'
      } overflow-hidden`}
    >
      {/* Header - Always visible */}
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition"
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 font-medium text-sm">
            #{turn.turn_number}
          </div>
          <div className="text-right" dir="rtl">
            <p className="text-gray-900 font-medium truncate max-w-md">
              {turn.parent_message.substring(0, 80)}
              {turn.parent_message.length > 80 ? '...' : ''}
            </p>
            <div className="flex items-center gap-2 text-xs text-gray-500 mt-1">
              <Clock className="w-3 h-3" />
              {new Date(turn.timestamp).toLocaleString()}
              {turn.perceived_intent && (
                <span className="px-1.5 py-0.5 bg-purple-50 text-purple-700 rounded">
                  {turn.perceived_intent}
                </span>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {hasIssues && (
            <span className="px-2 py-1 bg-amber-100 text-amber-700 text-xs rounded-full">
              {turn.corrections_count + turn.missed_signals_count} issues
            </span>
          )}
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-400" />
          )}
        </div>
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="border-t border-gray-100 p-4 space-y-4">
          {/* Parent Message */}
          <Section title="Parent Message" icon={<MessageSquare className="w-4 h-4" />}>
            <p className="text-gray-700 bg-gray-50 p-3 rounded-lg" dir="rtl">
              {turn.parent_message}
            </p>
            {turn.parent_role && (
              <span className="text-xs text-gray-500 mt-1 block">
                Role: {turn.parent_role}
              </span>
            )}
          </Section>

          {/* Tool Calls */}
          {turn.tool_calls?.length > 0 && (
            <Section title="Tool Calls (Perception)" icon={<Wrench className="w-4 h-4" />}>
              <div className="space-y-2">
                {turn.tool_calls.map((tc, i) => (
                  <ToolCallCard key={i} toolCall={tc} />
                ))}
              </div>
            </Section>
          )}

          {/* State Delta */}
          {turn.state_delta && (
            <Section title="State Changes" icon={<Brain className="w-4 h-4" />}>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                <DeltaItem
                  label="Observations Added"
                  value={turn.state_delta.observations_added || 0}
                  color="emerald"
                />
                <DeltaItem
                  label="Curiosities Spawned"
                  value={turn.state_delta.curiosities_spawned || 0}
                  color="amber"
                />
                <DeltaItem
                  label="Evidence Added"
                  value={turn.state_delta.evidence_added || 0}
                  color="blue"
                />
                {turn.state_delta.child_identity_set && (
                  <div className="px-3 py-2 bg-purple-50 rounded-lg">
                    <span className="text-xs text-purple-600">Identity Set</span>
                  </div>
                )}
              </div>
            </Section>
          )}

          {/* Active Curiosities */}
          {turn.active_curiosities?.length > 0 && (
            <Section title="Active Curiosities" icon={<Lightbulb className="w-4 h-4" />}>
              <div className="flex flex-wrap gap-2">
                {turn.active_curiosities.map((c, i) => (
                  <span
                    key={i}
                    className="px-2 py-1 bg-amber-50 text-amber-700 text-sm rounded-full"
                    dir="rtl"
                  >
                    {c}
                  </span>
                ))}
              </div>
            </Section>
          )}

          {/* Turn Guidance */}
          {turn.turn_guidance && (
            <Section title="Turn Guidance" icon={<ArrowRight className="w-4 h-4" />}>
              <p className="text-gray-600 bg-gray-50 p-3 rounded-lg text-sm" dir="rtl">
                {turn.turn_guidance}
              </p>
            </Section>
          )}

          {/* Response */}
          {turn.response_text && (
            <Section title="AI Response" icon={<MessageSquare className="w-4 h-4" />}>
              <div className="bg-indigo-50 p-3 rounded-lg" dir="rtl">
                <p className="text-indigo-900">{turn.response_text}</p>
              </div>
            </Section>
          )}

          {/* Expert Actions */}
          <div className="border-t border-gray-100 pt-4 mt-4">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowCorrectionForm(true)}
                className="flex items-center gap-2 px-3 py-2 bg-red-50 text-red-700 rounded-lg hover:bg-red-100 transition text-sm"
              >
                <AlertTriangle className="w-4 h-4" />
                Add Correction
              </button>
              <button
                onClick={() => setShowMissedSignalForm(true)}
                className="flex items-center gap-2 px-3 py-2 bg-amber-50 text-amber-700 rounded-lg hover:bg-amber-100 transition text-sm"
              >
                <Plus className="w-4 h-4" />
                Report Missed Signal
              </button>
            </div>
          </div>

          {/* Correction Form */}
          {showCorrectionForm && (
            <CorrectionForm
              childId={childId}
              turnId={turn.turn_id}
              onClose={() => setShowCorrectionForm(false)}
              onSuccess={() => {
                setShowCorrectionForm(false);
                onRefresh();
              }}
            />
          )}

          {/* Missed Signal Form */}
          {showMissedSignalForm && (
            <MissedSignalForm
              childId={childId}
              turnId={turn.turn_id}
              onClose={() => setShowMissedSignalForm(false)}
              onSuccess={() => {
                setShowMissedSignalForm(false);
                onRefresh();
              }}
            />
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Section Component
 */
function Section({ title, icon, children }) {
  return (
    <div>
      <div className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
        {icon}
        {title}
      </div>
      {children}
    </div>
  );
}

/**
 * Delta Item Component
 */
function DeltaItem({ label, value, color }) {
  if (value === 0) return null;

  const colors = {
    emerald: 'bg-emerald-50 text-emerald-700',
    amber: 'bg-amber-50 text-amber-700',
    blue: 'bg-blue-50 text-blue-700',
  };

  return (
    <div className={`px-3 py-2 rounded-lg ${colors[color]}`}>
      <div className="text-lg font-bold">{value}</div>
      <div className="text-xs">{label}</div>
    </div>
  );
}

/**
 * Tool Call Card Component - Renders tool calls with special formatting for hypothesis/video
 */
function ToolCallCard({ toolCall }) {
  const { tool_name, arguments: args } = toolCall;

  // Color coding based on tool type
  const toolColors = {
    set_child_identity: 'bg-purple-50 border-purple-100',
    notice: 'bg-emerald-50 border-emerald-100',
    wonder: 'bg-amber-50 border-amber-100',
    add_evidence: 'bg-blue-50 border-blue-100',
    capture_story: 'bg-indigo-50 border-indigo-100',
  };

  const toolIcons = {
    set_child_identity: '👤',
    notice: <Eye className="w-4 h-4 text-emerald-600" />,
    wonder: args?.type === 'hypothesis'
      ? <FlaskConical className="w-4 h-4 text-purple-600" />
      : <HelpCircle className="w-4 h-4 text-amber-600" />,
    add_evidence: '📎',
    capture_story: '📖',
  };

  const bgColor = toolColors[tool_name] || 'bg-gray-50 border-gray-100';
  const icon = toolIcons[tool_name] || '🔧';

  // Check if this is a hypothesis with video recommendation
  const isHypothesis = tool_name === 'wonder' && args?.type === 'hypothesis';
  const hasVideoRec = args?.video_appropriate || args?.video_value;

  return (
    <div className={`p-3 rounded-lg border ${bgColor}`}>
      {/* Tool header */}
      <div className="flex items-center gap-2 mb-2">
        <span className="text-lg">{typeof icon === 'string' ? icon : icon}</span>
        <span className="font-mono text-sm font-medium text-gray-800">{tool_name}</span>
        {args?.type && (
          <span className={`text-xs px-2 py-0.5 rounded ${
            args.type === 'hypothesis' ? 'bg-purple-100 text-purple-700' :
            args.type === 'question' ? 'bg-blue-100 text-blue-700' :
            'bg-gray-100 text-gray-700'
          }`}>
            {args.type}
          </span>
        )}
        {args?.domain && (
          <span className="text-xs px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded">
            {args.domain}
          </span>
        )}
      </div>

      {/* Main content based on tool type */}
      {tool_name === 'set_child_identity' && (
        <div className="grid grid-cols-3 gap-2 text-sm">
          {args?.name && <div><span className="text-gray-500">Name:</span> <span className="font-medium" dir="rtl">{args.name}</span></div>}
          {args?.age && <div><span className="text-gray-500">Age:</span> {args.age}</div>}
          {args?.gender && <div><span className="text-gray-500">Gender:</span> {args.gender}</div>}
        </div>
      )}

      {tool_name === 'notice' && args?.observation && (
        <p className="text-sm text-gray-700" dir="rtl">{args.observation}</p>
      )}

      {tool_name === 'wonder' && (
        <div className="space-y-2">
          {args?.about && (
            <p className="text-sm font-medium text-gray-800" dir="rtl">{args.about}</p>
          )}
          {args?.question && (
            <p className="text-sm text-gray-600" dir="rtl">❓ {args.question}</p>
          )}
          {isHypothesis && args?.theory && (
            <p className="text-sm text-purple-700 bg-purple-50 p-2 rounded" dir="rtl">
              💡 {args.theory}
            </p>
          )}

          {/* Video Recommendation */}
          {hasVideoRec && (
            <div className="mt-2 p-2 bg-violet-50 border border-violet-100 rounded">
              <div className="flex items-center gap-2 text-violet-700 text-sm font-medium mb-1">
                <Video className="w-4 h-4" />
                Video Recommendation
              </div>
              {args?.video_value && (
                <span className="text-xs px-2 py-0.5 bg-violet-100 text-violet-700 rounded capitalize">
                  {args.video_value}
                </span>
              )}
              {args?.video_value_reason && (
                <p className="text-xs text-violet-600 mt-1" dir="rtl">{args.video_value_reason}</p>
              )}
            </div>
          )}
        </div>
      )}

      {/* Fallback: show raw JSON for other tools */}
      {!['set_child_identity', 'notice', 'wonder'].includes(tool_name) && (
        <pre className="text-xs text-gray-600 mt-1 overflow-x-auto">
          {JSON.stringify(args, null, 2)}
        </pre>
      )}
    </div>
  );
}

/**
 * Correction Form Component
 */
function CorrectionForm({ childId, turnId, onClose, onSuccess }) {
  const [targetType, setTargetType] = useState('observation');
  const [correctionType, setCorrectionType] = useState('extraction_error');
  const [reasoning, setReasoning] = useState('');
  const [severity, setSeverity] = useState('medium');
  const [submitting, setSubmitting] = useState(false);

  const correctionTypes = [
    { value: 'domain_change', label: 'Wrong Domain' },
    { value: 'extraction_error', label: 'Extraction Error' },
    { value: 'hallucination', label: 'Hallucination' },
    { value: 'evidence_reclassify', label: 'Wrong Evidence Classification' },
    { value: 'timing_issue', label: 'Timing Issue' },
    { value: 'certainty_adjustment', label: 'Wrong Certainty' },
    { value: 'response_issue', label: 'Response Issue' },
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!reasoning.trim()) return;

    setSubmitting(true);
    try {
      await api.createCorrection(childId, turnId, {
        target_type: targetType,
        correction_type: correctionType,
        expert_reasoning: reasoning,
        severity,
      });
      onSuccess();
    } catch (err) {
      console.error('Error creating correction:', err);
      alert('Failed to create correction');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4 mt-4">
      <div className="flex items-center justify-between mb-4">
        <h4 className="font-medium text-red-800">Add Correction</h4>
        <button onClick={onClose} className="text-red-600 hover:text-red-800">
          <X className="w-4 h-4" />
        </button>
      </div>
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Target Type</label>
            <select
              value={targetType}
              onChange={(e) => setTargetType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
            >
              <option value="observation">Observation</option>
              <option value="curiosity">Curiosity</option>
              <option value="evidence">Evidence</option>
              <option value="response">Response</option>
              <option value="video">Video</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Correction Type</label>
            <select
              value={correctionType}
              onChange={(e) => setCorrectionType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
            >
              {correctionTypes.map((ct) => (
                <option key={ct.value} value={ct.value}>{ct.label}</option>
              ))}
            </select>
          </div>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Severity</label>
          <div className="flex gap-2">
            {['low', 'medium', 'high', 'critical'].map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setSeverity(s)}
                className={`px-3 py-1 rounded-lg text-sm capitalize ${
                  severity === s
                    ? 'bg-red-600 text-white'
                    : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50'
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Expert Reasoning (GOLD for training)
          </label>
          <textarea
            value={reasoning}
            onChange={(e) => setReasoning(e.target.value)}
            placeholder="Explain what was wrong and why..."
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm h-24"
            dir="rtl"
          />
        </div>
        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-gray-600 hover:text-gray-800"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={submitting || !reasoning.trim()}
            className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
          >
            <Check className="w-4 h-4" />
            {submitting ? 'Saving...' : 'Save Correction'}
          </button>
        </div>
      </form>
    </div>
  );
}

/**
 * Missed Signal Form Component
 */
function MissedSignalForm({ childId, turnId, onClose, onSuccess }) {
  const [signalType, setSignalType] = useState('observation');
  const [content, setContent] = useState('');
  const [domain, setDomain] = useState('');
  const [whyImportant, setWhyImportant] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!content.trim() || !whyImportant.trim()) return;

    setSubmitting(true);
    try {
      await api.createMissedSignal(childId, turnId, {
        signal_type: signalType,
        content,
        domain: domain || null,
        why_important: whyImportant,
      });
      onSuccess();
    } catch (err) {
      console.error('Error creating missed signal:', err);
      alert('Failed to create missed signal');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mt-4">
      <div className="flex items-center justify-between mb-4">
        <h4 className="font-medium text-amber-800">Report Missed Signal</h4>
        <button onClick={onClose} className="text-amber-600 hover:text-amber-800">
          <X className="w-4 h-4" />
        </button>
      </div>
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Signal Type</label>
            <select
              value={signalType}
              onChange={(e) => setSignalType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
            >
              <option value="observation">Observation</option>
              <option value="curiosity">Curiosity</option>
              <option value="hypothesis">Hypothesis</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Domain</label>
            <select
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
            >
              <option value="">Select domain...</option>
              <option value="motor">Motor</option>
              <option value="language">Language</option>
              <option value="social">Social</option>
              <option value="emotional">Emotional</option>
              <option value="cognitive">Cognitive</option>
              <option value="sensory">Sensory</option>
              <option value="daily_living">Daily Living</option>
            </select>
          </div>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            What should have been noticed
          </label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Describe the signal that was missed..."
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm h-20"
            dir="rtl"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Why is this important?
          </label>
          <textarea
            value={whyImportant}
            onChange={(e) => setWhyImportant(e.target.value)}
            placeholder="Explain the clinical significance..."
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm h-20"
            dir="rtl"
          />
        </div>
        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-gray-600 hover:text-gray-800"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={submitting || !content.trim() || !whyImportant.trim()}
            className="flex items-center gap-2 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:opacity-50"
          >
            <Check className="w-4 h-4" />
            {submitting ? 'Saving...' : 'Report Signal'}
          </button>
        </div>
      </form>
    </div>
  );
}
