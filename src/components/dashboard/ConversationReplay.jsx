import React, { useState, useEffect } from 'react';
import {
  MessageSquare,
  Bot,
  User,
  ChevronDown,
  ChevronUp,
  Eye,
  Lightbulb,
  FlaskConical,
  BookOpen,
  Video,
  AlertTriangle,
  Plus,
  Clock,
  Sparkles,
  Brain,
  Check,
  X,
  RefreshCw,
} from 'lucide-react';
import { api } from '../../api/client';

/**
 * ConversationReplay Component
 *
 * Natural chat-like view of the conversation with inline annotations
 * showing what the AI perceived at each turn.
 *
 * This is the human-friendly version of CognitiveTimeline -
 * designed for expert reviewers to quickly understand the dialogue
 * and spot issues.
 */
export default function ConversationReplay({ childId }) {
  const [timeline, setTimeline] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedTurn, setExpandedTurn] = useState(null);
  const [showCorrectionForm, setShowCorrectionForm] = useState(null);
  const [showMissedSignalForm, setShowMissedSignalForm] = useState(null);

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
          Error loading conversation: {error}
        </div>
      </div>
    );
  }

  if (!timeline?.turns?.length) {
    return (
      <div className="p-8 text-center text-gray-500">
        <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-300" />
        <p>No conversation yet</p>
        <p className="text-sm mt-2">
          Conversations will appear here as they happen
        </p>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-indigo-600" />
            Conversation Replay
          </h2>
          <p className="text-sm text-gray-500">
            {timeline.total_turns} turns • Click any turn to see AI's thinking
          </p>
        </div>
        <button
          onClick={loadTimeline}
          className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition text-sm"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Conversation Thread */}
      <div className="space-y-1">
        {timeline.turns.map((turn, index) => (
          <ConversationTurn
            key={turn.turn_id}
            turn={turn}
            turnNumber={index + 1}
            isExpanded={expandedTurn === turn.turn_id}
            onToggleExpand={() => setExpandedTurn(
              expandedTurn === turn.turn_id ? null : turn.turn_id
            )}
            showCorrectionForm={showCorrectionForm === turn.turn_id}
            showMissedSignalForm={showMissedSignalForm === turn.turn_id}
            onShowCorrectionForm={() => setShowCorrectionForm(turn.turn_id)}
            onShowMissedSignalForm={() => setShowMissedSignalForm(turn.turn_id)}
            onCloseForms={() => {
              setShowCorrectionForm(null);
              setShowMissedSignalForm(null);
            }}
            childId={childId}
            onRefresh={loadTimeline}
          />
        ))}
      </div>

      {/* Legend */}
      <div className="mt-8 p-4 bg-gray-50 rounded-lg">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Legend</h3>
        <div className="flex flex-wrap gap-4 text-sm">
          <LegendItem icon={<Eye className="w-4 h-4 text-emerald-600" />} label="Noticed (observation)" />
          <LegendItem icon={<Lightbulb className="w-4 h-4 text-amber-600" />} label="Wondered (curiosity)" />
          <LegendItem icon={<FlaskConical className="w-4 h-4 text-purple-600" />} label="Hypothesis" />
          <LegendItem icon={<BookOpen className="w-4 h-4 text-indigo-600" />} label="Captured story" />
          <LegendItem icon={<Video className="w-4 h-4 text-violet-600" />} label="Video recommended" />
        </div>
      </div>
    </div>
  );
}

/**
 * Legend Item Component
 */
function LegendItem({ icon, label }) {
  return (
    <div className="flex items-center gap-2 text-gray-600">
      {icon}
      <span>{label}</span>
    </div>
  );
}

/**
 * Conversation Turn Component
 *
 * Shows a single turn in chat format with:
 * - Parent message (bubble on right)
 * - Inline perception badges
 * - AI response (bubble on left)
 * - Expandable cognitive details
 */
function ConversationTurn({
  turn,
  turnNumber,
  isExpanded,
  onToggleExpand,
  showCorrectionForm,
  showMissedSignalForm,
  onShowCorrectionForm,
  onShowMissedSignalForm,
  onCloseForms,
  childId,
  onRefresh,
}) {
  const hasIssues = turn.corrections_count > 0 || turn.missed_signals_count > 0;

  // Extract what AI perceived from tool calls
  const perceptions = extractPerceptions(turn.tool_calls || []);

  return (
    <div className={`relative ${hasIssues ? 'bg-amber-50/50 rounded-lg' : ''}`}>
      {/* Turn number indicator */}
      <div className="absolute left-0 top-4 w-6 h-6 rounded-full bg-gray-100 flex items-center justify-center text-xs text-gray-500 font-medium">
        {turnNumber}
      </div>

      <div className="pl-10 py-3">
        {/* Parent Message */}
        <div className="flex justify-end mb-2">
          <div className="max-w-[75%]">
            <div className="flex items-center gap-2 justify-end mb-1">
              <span className="text-xs text-gray-400">
                {new Date(turn.timestamp).toLocaleTimeString()}
              </span>
              <User className="w-4 h-4 text-gray-400" />
            </div>
            <div
              className="bg-indigo-600 text-white px-4 py-3 rounded-2xl rounded-tr-md"
              dir="rtl"
            >
              {turn.parent_message}
            </div>
          </div>
        </div>

        {/* Perception Badges - What AI noticed */}
        {perceptions.length > 0 && (
          <div className="flex flex-wrap gap-2 my-3 ml-12">
            {perceptions.map((p, i) => (
              <PerceptionBadge key={i} perception={p} />
            ))}
          </div>
        )}

        {/* AI Response */}
        {turn.response_text && (
          <div className="flex justify-start">
            <div className="max-w-[75%]">
              <div className="flex items-center gap-2 mb-1">
                <Bot className="w-4 h-4 text-indigo-600" />
                <span className="text-xs text-gray-400">Chitta</span>
                {turn.perceived_intent && (
                  <span className="text-xs px-1.5 py-0.5 bg-purple-100 text-purple-700 rounded">
                    {turn.perceived_intent}
                  </span>
                )}
              </div>
              <div
                className="bg-gray-100 text-gray-800 px-4 py-3 rounded-2xl rounded-tl-md"
                dir="rtl"
              >
                {turn.response_text}
              </div>
            </div>
          </div>
        )}

        {/* Issue indicator */}
        {hasIssues && (
          <div className="flex items-center gap-2 mt-2 ml-12">
            <span className="text-xs px-2 py-1 bg-amber-100 text-amber-700 rounded-full flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" />
              {turn.corrections_count + turn.missed_signals_count} expert feedback
            </span>
          </div>
        )}

        {/* Expand/Collapse Toggle */}
        <button
          onClick={onToggleExpand}
          className="flex items-center gap-2 mt-3 ml-12 text-sm text-gray-500 hover:text-gray-700 transition"
        >
          <Brain className="w-4 h-4" />
          {isExpanded ? 'Hide AI thinking' : 'Show AI thinking'}
          {isExpanded ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </button>

        {/* Expanded Cognitive Details */}
        {isExpanded && (
          <CognitiveDetails
            turn={turn}
            childId={childId}
            showCorrectionForm={showCorrectionForm}
            showMissedSignalForm={showMissedSignalForm}
            onShowCorrectionForm={onShowCorrectionForm}
            onShowMissedSignalForm={onShowMissedSignalForm}
            onCloseForms={onCloseForms}
            onRefresh={onRefresh}
          />
        )}
      </div>
    </div>
  );
}

/**
 * Extract perceptions from tool calls for display
 */
function extractPerceptions(toolCalls) {
  const perceptions = [];

  for (const tc of toolCalls) {
    const { tool_name, arguments: args } = tc;

    if (tool_name === 'notice') {
      perceptions.push({
        type: 'noticed',
        icon: <Eye className="w-3 h-3" />,
        color: 'bg-emerald-100 text-emerald-700',
        text: args?.observation?.substring(0, 40) + (args?.observation?.length > 40 ? '...' : ''),
        domain: args?.domain,
      });
    } else if (tool_name === 'wonder') {
      const isHypothesis = args?.type === 'hypothesis';
      perceptions.push({
        type: isHypothesis ? 'hypothesis' : 'wondered',
        icon: isHypothesis ? <FlaskConical className="w-3 h-3" /> : <Lightbulb className="w-3 h-3" />,
        color: isHypothesis ? 'bg-purple-100 text-purple-700' : 'bg-amber-100 text-amber-700',
        text: args?.about?.substring(0, 40) + (args?.about?.length > 40 ? '...' : ''),
        hasVideo: args?.video_appropriate || args?.video_value,
      });
    } else if (tool_name === 'capture_story') {
      perceptions.push({
        type: 'story',
        icon: <BookOpen className="w-3 h-3" />,
        color: 'bg-indigo-100 text-indigo-700',
        text: 'Captured story',
      });
    } else if (tool_name === 'set_child_identity') {
      const parts = [];
      if (args?.name) parts.push(args.name);
      if (args?.age) parts.push(`${args.age}y`);
      if (args?.gender) parts.push(args.gender);
      if (parts.length > 0) {
        perceptions.push({
          type: 'identity',
          icon: <User className="w-3 h-3" />,
          color: 'bg-purple-100 text-purple-700',
          text: `Identity: ${parts.join(', ')}`,
        });
      }
    }
  }

  return perceptions;
}

/**
 * Perception Badge Component
 */
function PerceptionBadge({ perception }) {
  return (
    <div
      className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs ${perception.color}`}
      title={perception.text}
    >
      {perception.icon}
      <span className="max-w-32 truncate" dir="rtl">{perception.text}</span>
      {perception.domain && (
        <span className="opacity-60">({perception.domain})</span>
      )}
      {perception.hasVideo && (
        <Video className="w-3 h-3 text-violet-600" />
      )}
    </div>
  );
}

/**
 * Cognitive Details - Expanded view of AI's thinking
 */
function CognitiveDetails({
  turn,
  childId,
  showCorrectionForm,
  showMissedSignalForm,
  onShowCorrectionForm,
  onShowMissedSignalForm,
  onCloseForms,
  onRefresh,
}) {
  return (
    <div className="mt-4 ml-12 p-4 bg-white rounded-xl border border-gray-200 space-y-4">
      {/* Turn Guidance */}
      {turn.turn_guidance && (
        <div>
          <h4 className="text-xs font-medium text-gray-500 uppercase mb-1">Turn Guidance</h4>
          <p className="text-sm text-gray-600 bg-gray-50 p-2 rounded" dir="rtl">
            {turn.turn_guidance}
          </p>
        </div>
      )}

      {/* State Changes */}
      {turn.state_delta && (
        <div>
          <h4 className="text-xs font-medium text-gray-500 uppercase mb-2">State Changes</h4>
          <div className="flex flex-wrap gap-2">
            {turn.state_delta.observations_added > 0 && (
              <StateBadge
                label="observations"
                value={turn.state_delta.observations_added}
                color="emerald"
              />
            )}
            {turn.state_delta.curiosities_spawned > 0 && (
              <StateBadge
                label="curiosities"
                value={turn.state_delta.curiosities_spawned}
                color="amber"
              />
            )}
            {turn.state_delta.evidence_added > 0 && (
              <StateBadge
                label="evidence"
                value={turn.state_delta.evidence_added}
                color="blue"
              />
            )}
            {turn.state_delta.stories_captured > 0 && (
              <StateBadge
                label="stories"
                value={turn.state_delta.stories_captured}
                color="indigo"
              />
            )}
            {turn.state_delta.child_identity_set && (
              <span className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded-full">
                Identity set
              </span>
            )}
          </div>
        </div>
      )}

      {/* Full Tool Calls */}
      {turn.tool_calls?.length > 0 && (
        <div>
          <h4 className="text-xs font-medium text-gray-500 uppercase mb-2">
            All Tool Calls ({turn.tool_calls.length})
          </h4>
          <div className="space-y-2">
            {turn.tool_calls.map((tc, i) => (
              <ToolCallDetail key={i} toolCall={tc} />
            ))}
          </div>
        </div>
      )}

      {/* Active Curiosities */}
      {turn.active_curiosities?.length > 0 && (
        <div>
          <h4 className="text-xs font-medium text-gray-500 uppercase mb-2">Active Curiosities</h4>
          <div className="flex flex-wrap gap-2">
            {turn.active_curiosities.map((c, i) => (
              <span
                key={i}
                className="text-xs px-2 py-1 bg-amber-50 text-amber-700 rounded-full"
                dir="rtl"
              >
                {c}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Expert Actions */}
      <div className="pt-3 border-t border-gray-100">
        <div className="flex items-center gap-2">
          <button
            onClick={onShowCorrectionForm}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-red-50 text-red-700 rounded-lg hover:bg-red-100 transition text-sm"
          >
            <AlertTriangle className="w-4 h-4" />
            Add Correction
          </button>
          <button
            onClick={onShowMissedSignalForm}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-50 text-amber-700 rounded-lg hover:bg-amber-100 transition text-sm"
          >
            <Plus className="w-4 h-4" />
            Missed Signal
          </button>
        </div>
      </div>

      {/* Correction Form */}
      {showCorrectionForm && (
        <CorrectionForm
          childId={childId}
          turnId={turn.turn_id}
          onClose={onCloseForms}
          onSuccess={() => {
            onCloseForms();
            onRefresh();
          }}
        />
      )}

      {/* Missed Signal Form */}
      {showMissedSignalForm && (
        <MissedSignalForm
          childId={childId}
          turnId={turn.turn_id}
          onClose={onCloseForms}
          onSuccess={() => {
            onCloseForms();
            onRefresh();
          }}
        />
      )}
    </div>
  );
}

/**
 * State Badge Component
 */
function StateBadge({ label, value, color }) {
  const colors = {
    emerald: 'bg-emerald-100 text-emerald-700',
    amber: 'bg-amber-100 text-amber-700',
    blue: 'bg-blue-100 text-blue-700',
    indigo: 'bg-indigo-100 text-indigo-700',
  };

  return (
    <span className={`text-xs px-2 py-1 rounded-full ${colors[color]}`}>
      +{value} {label}
    </span>
  );
}

/**
 * Tool Call Detail Component
 */
function ToolCallDetail({ toolCall }) {
  const { tool_name, arguments: args } = toolCall;

  const toolConfig = {
    notice: { icon: <Eye className="w-4 h-4" />, color: 'border-emerald-200 bg-emerald-50' },
    wonder: { icon: <Lightbulb className="w-4 h-4" />, color: 'border-amber-200 bg-amber-50' },
    capture_story: { icon: <BookOpen className="w-4 h-4" />, color: 'border-indigo-200 bg-indigo-50' },
    add_evidence: { icon: <Plus className="w-4 h-4" />, color: 'border-blue-200 bg-blue-50' },
    set_child_identity: { icon: <User className="w-4 h-4" />, color: 'border-purple-200 bg-purple-50' },
  };

  const config = toolConfig[tool_name] || { icon: '🔧', color: 'border-gray-200 bg-gray-50' };

  return (
    <div className={`p-3 rounded-lg border ${config.color}`}>
      <div className="flex items-center gap-2 mb-1">
        {config.icon}
        <span className="font-mono text-sm font-medium">{tool_name}</span>
        {args?.type && (
          <span className={`text-xs px-1.5 py-0.5 rounded ${
            args.type === 'hypothesis' ? 'bg-purple-200 text-purple-800' : 'bg-gray-200 text-gray-700'
          }`}>
            {args.type}
          </span>
        )}
        {args?.domain && (
          <span className="text-xs px-1.5 py-0.5 bg-gray-200 text-gray-700 rounded">
            {args.domain}
          </span>
        )}
      </div>

      {/* Content based on tool type */}
      <div className="text-sm text-gray-700" dir="rtl">
        {tool_name === 'notice' && args?.observation}
        {tool_name === 'wonder' && (
          <div className="space-y-1">
            <p>{args?.about}</p>
            {args?.theory && (
              <p className="text-purple-700 bg-purple-100 p-2 rounded mt-1">
                💡 {args.theory}
              </p>
            )}
            {(args?.video_appropriate || args?.video_value) && (
              <div className="flex items-center gap-2 mt-1 text-violet-700">
                <Video className="w-4 h-4" />
                <span>Video: {args.video_value || 'recommended'}</span>
              </div>
            )}
          </div>
        )}
        {tool_name === 'capture_story' && (
          <div>
            <p>{args?.summary}</p>
            {args?.reveals?.length > 0 && (
              <div className="mt-1 text-xs text-gray-500">
                Reveals: {args.reveals.join(', ')}
              </div>
            )}
          </div>
        )}
        {tool_name === 'set_child_identity' && (
          <div className="flex gap-4">
            {args?.name && <span>Name: {args.name}</span>}
            {args?.age && <span>Age: {args.age}</span>}
            {args?.gender && <span>Gender: {args.gender}</span>}
          </div>
        )}
        {tool_name === 'add_evidence' && args?.evidence}
      </div>
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
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-medium text-red-800">Add Correction</h4>
        <button onClick={onClose} className="text-red-600 hover:text-red-800">
          <X className="w-4 h-4" />
        </button>
      </div>
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Target</label>
            <select
              value={targetType}
              onChange={(e) => setTargetType(e.target.value)}
              className="w-full px-2 py-1.5 border border-gray-200 rounded text-sm"
            >
              <option value="observation">Observation</option>
              <option value="curiosity">Curiosity</option>
              <option value="evidence">Evidence</option>
              <option value="response">Response</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Type</label>
            <select
              value={correctionType}
              onChange={(e) => setCorrectionType(e.target.value)}
              className="w-full px-2 py-1.5 border border-gray-200 rounded text-sm"
            >
              {correctionTypes.map((ct) => (
                <option key={ct.value} value={ct.value}>{ct.label}</option>
              ))}
            </select>
          </div>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Severity</label>
          <div className="flex gap-1">
            {['low', 'medium', 'high', 'critical'].map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setSeverity(s)}
                className={`px-2 py-1 rounded text-xs capitalize ${
                  severity === s
                    ? 'bg-red-600 text-white'
                    : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Expert Reasoning
          </label>
          <textarea
            value={reasoning}
            onChange={(e) => setReasoning(e.target.value)}
            placeholder="Explain what was wrong..."
            className="w-full px-2 py-1.5 border border-gray-200 rounded text-sm h-20"
            dir="rtl"
          />
        </div>
        <div className="flex justify-end gap-2">
          <button type="button" onClick={onClose} className="px-3 py-1.5 text-gray-600 text-sm">
            Cancel
          </button>
          <button
            type="submit"
            disabled={submitting || !reasoning.trim()}
            className="flex items-center gap-1 px-3 py-1.5 bg-red-600 text-white rounded text-sm hover:bg-red-700 disabled:opacity-50"
          >
            <Check className="w-3 h-3" />
            Save
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
      alert('Failed to report missed signal');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mt-4">
      <div className="flex items-center justify-between mb-3">
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
              className="w-full px-2 py-1.5 border border-gray-200 rounded text-sm"
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
              className="w-full px-2 py-1.5 border border-gray-200 rounded text-sm"
            >
              <option value="">Select...</option>
              <option value="motor">Motor</option>
              <option value="language">Language</option>
              <option value="social">Social</option>
              <option value="emotional">Emotional</option>
              <option value="cognitive">Cognitive</option>
              <option value="sensory">Sensory</option>
            </select>
          </div>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            What was missed
          </label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Describe what should have been noticed..."
            className="w-full px-2 py-1.5 border border-gray-200 rounded text-sm h-16"
            dir="rtl"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Why important
          </label>
          <textarea
            value={whyImportant}
            onChange={(e) => setWhyImportant(e.target.value)}
            placeholder="Clinical significance..."
            className="w-full px-2 py-1.5 border border-gray-200 rounded text-sm h-16"
            dir="rtl"
          />
        </div>
        <div className="flex justify-end gap-2">
          <button type="button" onClick={onClose} className="px-3 py-1.5 text-gray-600 text-sm">
            Cancel
          </button>
          <button
            type="submit"
            disabled={submitting || !content.trim() || !whyImportant.trim()}
            className="flex items-center gap-1 px-3 py-1.5 bg-amber-600 text-white rounded text-sm hover:bg-amber-700 disabled:opacity-50"
          >
            <Check className="w-3 h-3" />
            Report
          </button>
        </div>
      </form>
    </div>
  );
}
