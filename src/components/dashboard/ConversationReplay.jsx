import React, { useState, useEffect } from 'react';
import {
  ChevronDown,
  ChevronUp,
  Plus,
  RefreshCw,
  MessageSquare,
  Video,
  FlaskConical,
  Sparkles,
} from 'lucide-react';
import { api } from '../../api/client';

/**
 * ConversationReplay - Clean, friendly UI for reviewing conversation turns
 *
 * Design principles (from COGNITIVE_DASHBOARD_PLAN.md):
 * - Minimal visual noise
 * - Progressive disclosure (collapsed by default)
 * - Warm, approachable Hebrew
 * - Subtle correction buttons
 * - Technical details hidden by default
 * - Special cards for hypotheses and video events
 */

// Domain translations
const DOMAIN_HE = {
  motor: 'מוטורי',
  language: 'שפתי',
  social: 'חברתי',
  emotional: 'רגשי',
  cognitive: 'קוגניטיבי',
  sensory: 'חושי',
  behavioral: 'התנהגותי',
  daily_living: 'תפקוד יומיומי',
  play: 'משחק',
  creativity: 'יצירתיות',
};

const TYPE_HE = {
  discovery: 'גילוי',
  question: 'שאלה',
  hypothesis: 'השערה',
  pattern: 'דפוס',
};

const VIDEO_VALUE_HE = {
  calibration: 'כיול',
  chain: 'שרשרת',
  discovery: 'גילוי',
  reframe: 'מסגור מחדש',
  relational: 'יחסי',
};

export default function ConversationReplay({ childId }) {
  const [timeline, setTimeline] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedTurns, setExpandedTurns] = useState(new Set());

  useEffect(() => {
    loadTimeline();
  }, [childId]);

  async function loadTimeline() {
    setLoading(true);
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
    setExpandedTurns(prev => {
      const next = new Set(prev);
      next.has(turnId) ? next.delete(turnId) : next.add(turnId);
      return next;
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-indigo-200 border-t-indigo-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-100 rounded-xl p-6 text-red-700 text-center">
          שגיאה בטעינת השיחה
        </div>
      </div>
    );
  }

  if (!timeline?.turns?.length) {
    return (
      <div className="py-16 text-center">
        <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-200" />
        <p className="text-gray-400">אין שיחה עדיין</p>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto" dir="rtl">
      {/* Simple header */}
      <div className="flex items-center justify-between mb-8">
        <h2 className="text-xl font-medium text-gray-800">ציר הזמן</h2>
        <button
          onClick={loadTimeline}
          className="p-2 text-gray-400 hover:text-gray-600 transition"
          title="רענן"
        >
          <RefreshCw className="w-5 h-5" />
        </button>
      </div>

      {/* Timeline - lots of space between cards */}
      <div className="space-y-4">
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
 * TurnCard - The core cognitive trace display
 *
 * Collapsed: 3 lines (turn#, message, summary with special icons)
 * Expanded: Full details with clean sections and special cards
 */
function TurnCard({ turn, childId, isExpanded, onToggle, onRefresh }) {
  const [showTechnical, setShowTechnical] = useState(false);
  const [modal, setModal] = useState(null);

  // Extract and categorize perceptions
  const observations = turn.tool_calls?.filter(tc => tc.tool_name === 'notice') || [];
  const allCuriosities = turn.tool_calls?.filter(tc => tc.tool_name === 'wonder') || [];

  // Separate hypotheses from other curiosities
  const hypotheses = allCuriosities.filter(c => c.arguments?.type === 'hypothesis');
  const otherCuriosities = allCuriosities.filter(c => c.arguments?.type !== 'hypothesis');

  // Build summary for collapsed state
  const summaryParts = [];
  if (observations.length > 0) {
    const domains = [...new Set(observations.map(o => o.arguments?.domain).filter(Boolean))];
    const domainText = domains.length ? `(${domains.map(d => DOMAIN_HE[d] || d).join(', ')})` : '';
    summaryParts.push({ icon: '📌', text: `+${observations.length} תצפית ${domainText}` });
  }
  if (hypotheses.length > 0) {
    summaryParts.push({ icon: '◆', text: `+${hypotheses.length} השערה`, special: 'hypothesis' });
  }
  if (otherCuriosities.length > 0) {
    summaryParts.push({ icon: '❓', text: `+${otherCuriosities.length} סקרנות` });
  }

  const time = new Date(turn.timestamp).toLocaleTimeString('he-IL', {
    hour: '2-digit',
    minute: '2-digit'
  });

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
      {/* Collapsed Header - Always Visible */}
      <button
        onClick={onToggle}
        className="w-full text-right px-6 py-5 hover:bg-gray-50/50 transition"
      >
        {/* Line 1: Turn indicator */}
        <div className="flex items-center gap-2 text-sm text-gray-400 mb-2">
          <span className="w-2 h-2 rounded-full bg-indigo-400" />
          <span>תור #{turn.turn_number}</span>
          <span>·</span>
          <span>{time}</span>
        </div>

        {/* Line 2: Parent message */}
        <p className="text-gray-800 text-lg leading-relaxed line-clamp-2 mb-2">
          "{turn.parent_message}"
        </p>

        {/* Line 3: Summary + expand */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4 text-sm">
            {summaryParts.map((part, i) => (
              <span
                key={i}
                className={
                  part.special === 'hypothesis'
                    ? 'text-purple-600 font-medium'
                    : 'text-gray-500'
                }
              >
                {part.icon} {part.text}
              </span>
            ))}
            {summaryParts.length === 0 && (
              <span className="text-gray-300">—</span>
            )}
          </div>
          <span className="flex items-center gap-1 text-sm text-indigo-500">
            {isExpanded ? 'צמצם' : 'הרחב'}
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </span>
        </div>
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="border-t border-gray-50 px-6 py-6">

          {/* 💬 Parent Section */}
          <Section emoji="💬" title="ההורה:">
            <div className="bg-indigo-50/50 rounded-xl p-5 text-gray-800 text-lg leading-relaxed">
              "{turn.parent_message}"
            </div>
          </Section>

          <Divider />

          {/* 🧠 What Chitta Understood */}
          <Section emoji="🧠" title="מה הבינה צ'יטה:">
            <div className="space-y-4">
              {/* Regular Observations */}
              {observations.map((obs, i) => (
                <PerceptionCard
                  key={`obs-${i}`}
                  type="תצפית"
                  content={obs.arguments?.observation || obs.arguments?.content}
                  domain={obs.arguments?.domain}
                  onApprove={() => console.log('approved')}
                  onReject={() => setModal({ type: 'correction', target: 'observation', data: obs })}
                />
              ))}

              {/* Hypotheses - Special Card */}
              {hypotheses.map((hyp, i) => (
                <HypothesisCard
                  key={`hyp-${i}`}
                  hypothesis={hyp}
                  turnNumber={turn.turn_number}
                  onApprove={() => console.log('hypothesis approved')}
                  onReject={() => setModal({ type: 'correction', target: 'hypothesis', data: hyp })}
                />
              ))}

              {/* Other Curiosities */}
              {otherCuriosities.map((cur, i) => (
                <PerceptionCard
                  key={`cur-${i}`}
                  type="סקרנות חדשה"
                  content={cur.arguments?.about}
                  domain={cur.arguments?.domain}
                  curiosityType={cur.arguments?.type}
                  onApprove={() => console.log('approved')}
                  onReject={() => setModal({ type: 'correction', target: 'curiosity', data: cur })}
                />
              ))}

              {observations.length === 0 && allCuriosities.length === 0 && (
                <p className="text-gray-300 py-4">לא זוהו תובנות בתור זה</p>
              )}

              {/* Add missed signal */}
              <button
                onClick={() => setModal({ type: 'missed' })}
                className="flex items-center gap-1 text-amber-600 hover:text-amber-700 text-sm mt-2"
              >
                <Plus className="w-4 h-4" />
                הוסף משהו שפוספס
              </button>
            </div>
          </Section>

          <Divider />

          {/* 💭 Chitta's Response */}
          {turn.response_text && (
            <>
              <Section emoji="💭" title="תשובת צ'יטה:">
                <div className="bg-gray-50/70 rounded-xl p-5">
                  <p className="text-gray-800 leading-relaxed mb-4">
                    "{turn.response_text}"
                  </p>
                  <div className="flex items-center justify-end gap-3 text-sm">
                    <button className="text-emerald-600 hover:text-emerald-700">
                      ✓ תשובה מתאימה
                    </button>
                    <button
                      onClick={() => setModal({ type: 'correction', target: 'response', data: turn })}
                      className="text-red-400 hover:text-red-500"
                    >
                      ✗ בעיה
                    </button>
                  </div>
                </div>
              </Section>

              <Divider />
            </>
          )}

          {/* 🔧 Technical Details */}
          <button
            onClick={() => setShowTechnical(!showTechnical)}
            className="flex items-center gap-2 text-sm text-gray-400 hover:text-gray-500"
          >
            🔧 פרטים טכניים
            {showTechnical ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {showTechnical && (
            <div className="mt-4 p-4 bg-gray-50 rounded-xl text-sm space-y-4">
              {turn.turn_guidance && (
                <div>
                  <p className="text-gray-400 mb-1">הנחיית תור:</p>
                  <p className="text-gray-600">{turn.turn_guidance}</p>
                </div>
              )}
              <div>
                <p className="text-gray-400 mb-1">קריאות כלים:</p>
                <pre className="text-xs text-gray-500 bg-white p-3 rounded-lg border border-gray-100 overflow-x-auto text-left" dir="ltr">
                  {JSON.stringify(turn.tool_calls, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Modal dialogs */}
      {modal?.type === 'missed' && (
        <MissedSignalModal
          childId={childId}
          turnId={turn.turn_id}
          parentMessage={turn.parent_message}
          onClose={() => setModal(null)}
          onSuccess={() => { setModal(null); onRefresh(); }}
        />
      )}
      {modal?.type === 'correction' && (
        <CorrectionModal
          childId={childId}
          turnId={turn.turn_id}
          target={modal}
          onClose={() => setModal(null)}
          onSuccess={() => { setModal(null); onRefresh(); }}
        />
      )}
    </div>
  );
}

/**
 * Section - A labeled content area with emoji header
 */
function Section({ emoji, title, children }) {
  return (
    <div className="py-2">
      <h3 className="text-gray-500 text-sm mb-3 flex items-center gap-2">
        <span>{emoji}</span>
        <span>{title}</span>
      </h3>
      {children}
    </div>
  );
}

/**
 * Divider - Subtle separator line
 */
function Divider() {
  return <div className="border-t border-gray-100 my-4" />;
}

/**
 * HypothesisCard - Special card for hypotheses (plan section 6.2)
 *
 * Design: ◆ diamond icon, certainty bar, video recommendation
 */
function HypothesisCard({ hypothesis, turnNumber, onApprove, onReject }) {
  const [expanded, setExpanded] = useState(false);
  const args = hypothesis.arguments || {};

  const hasVideoRec = args.video_appropriate || args.video_value;
  const certainty = args.initial_certainty || 0.3; // Default starting certainty
  const certaintyPercent = Math.round(certainty * 100);

  return (
    <div className="relative border-2 border-purple-200 rounded-xl bg-gradient-to-br from-purple-50/50 to-white">
      {/* Title badge */}
      <div className="absolute -top-2.5 right-4 px-2 bg-white">
        <span className="text-xs text-purple-600 font-medium flex items-center gap-1">
          <span>◆</span> השערה חדשה
        </span>
      </div>

      <div className="p-5 pt-6">
        {/* Theory */}
        <p className="text-gray-800 text-lg leading-relaxed mb-4">
          "{args.theory || args.about}"
        </p>

        {/* Certainty bar */}
        <div className="mb-4">
          <div className="flex items-center justify-between text-sm text-gray-500 mb-1">
            <span>ודאות התחלתית</span>
            <span>{certaintyPercent}%</span>
          </div>
          <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-purple-400 rounded-full transition-all"
              style={{ width: `${certaintyPercent}%` }}
            />
          </div>
        </div>

        {/* Meta info */}
        <div className="flex items-center gap-3 text-sm text-gray-500 mb-3">
          {args.domain && (
            <span>תחום: {DOMAIN_HE[args.domain] || args.domain}</span>
          )}
          {args.question && (
            <span className="text-purple-600">❓ {args.question}</span>
          )}
        </div>

        {/* Video recommendation - Special section */}
        {hasVideoRec && (
          <div className="p-4 bg-violet-50 border border-violet-100 rounded-xl mb-3">
            <div className="flex items-center gap-2 text-violet-700 font-medium mb-2">
              <Video className="w-4 h-4" />
              המלצת וידאו
            </div>
            <div className="flex items-center gap-2 flex-wrap text-sm">
              {args.video_value && (
                <span className="px-2 py-1 bg-violet-100 text-violet-700 rounded-lg">
                  {VIDEO_VALUE_HE[args.video_value] || args.video_value}
                </span>
              )}
              {args.video_appropriate && !args.video_value && (
                <span className="text-violet-600">מתאים לבדיקה בוידאו</span>
              )}
            </div>
            {args.video_value_reason && (
              <p className="text-violet-600 text-sm mt-2">{args.video_value_reason}</p>
            )}
          </div>
        )}

        {/* Actions row */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-sm text-purple-600 hover:text-purple-700 flex items-center gap-1"
          >
            {expanded ? 'פחות פרטים' : 'עוד פרטים'}
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {/* Approve/Reject */}
          <div className="flex items-center gap-1 text-sm">
            <button
              onClick={onApprove}
              className="w-7 h-7 flex items-center justify-center text-gray-300 hover:text-emerald-500 transition"
              title="השערה נכונה"
            >
              ✓
            </button>
            <button
              onClick={onReject}
              className="w-7 h-7 flex items-center justify-center text-gray-300 hover:text-red-400 transition"
              title="השערה שגויה"
            >
              ✗
            </button>
          </div>
        </div>

        {/* Expanded details */}
        {expanded && (
          <div className="mt-4 pt-4 border-t border-purple-100 space-y-3">
            {/* Close button */}
            <div className="flex justify-end">
              <button
                onClick={() => setExpanded(false)}
                className="flex items-center gap-1 px-3 py-1.5 text-sm text-purple-600 hover:text-purple-700 hover:bg-purple-50 rounded-lg transition"
              >
                סגור
                <ChevronUp className="w-4 h-4" />
              </button>
            </div>

            {/* Raw arguments for debugging/full info */}
            <div className="text-sm max-h-64 overflow-y-auto">
              <p className="text-gray-400 mb-1">פרטים מלאים:</p>
              <div className="p-3 bg-white rounded-lg border border-gray-100">
                {args.about && (
                  <p className="text-gray-600 mb-1"><strong>נושא:</strong> {args.about}</p>
                )}
                {args.theory && (
                  <p className="text-gray-600 mb-1"><strong>תיאוריה:</strong> {args.theory}</p>
                )}
                {args.question && (
                  <p className="text-gray-600 mb-1"><strong>שאלה:</strong> {args.question}</p>
                )}
                {args.domain && (
                  <p className="text-gray-600"><strong>תחום:</strong> {DOMAIN_HE[args.domain]}</p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * PerceptionCard - Observation or regular Curiosity card
 */
function PerceptionCard({ type, content, domain, curiosityType, theory, onApprove, onReject }) {
  return (
    <div className="relative border border-gray-200 rounded-xl bg-white">
      {/* Title in border line effect */}
      <div className="absolute -top-2.5 right-4 px-2 bg-white">
        <span className="text-xs text-gray-400">{type}</span>
      </div>

      <div className="p-4 pt-5">
        {/* Content */}
        <p className="text-gray-800 leading-relaxed mb-3">
          "{content}"
        </p>

        {/* Labels row */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 text-sm text-gray-500">
            {curiosityType && (
              <span>סוג: {TYPE_HE[curiosityType] || curiosityType}</span>
            )}
            {domain && (
              <>
                {curiosityType && <span className="text-gray-300">|</span>}
                <span>תחום: {DOMAIN_HE[domain] || domain}</span>
              </>
            )}
          </div>

          {/* Tiny approve/reject buttons */}
          <div className="flex items-center gap-1 text-sm">
            <button
              onClick={onApprove}
              className="w-7 h-7 flex items-center justify-center text-gray-300 hover:text-emerald-500 transition"
              title="נכון"
            >
              ✓
            </button>
            <button
              onClick={onReject}
              className="w-7 h-7 flex items-center justify-center text-gray-300 hover:text-red-400 transition"
              title="לא נכון"
            >
              ✗
            </button>
          </div>
        </div>

        {/* Theory for non-hypothesis curiosities that might have a theory */}
        {theory && (
          <div className="mt-3 p-3 bg-purple-50 rounded-lg text-purple-700 text-sm">
            💡 {theory}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Modal backdrop
 */
function Modal({ children, onClose }) {
  return (
    <div
      className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-white rounded-2xl shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto" dir="rtl">
        {children}
      </div>
    </div>
  );
}

/**
 * MissedSignalModal - Add something that was missed
 */
function MissedSignalModal({ childId, turnId, parentMessage, onClose, onSuccess }) {
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
      console.error('Error:', err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal onClose={onClose}>
      <div className="p-6">
        <h2 className="text-lg font-medium text-gray-800 mb-6">הוסף משהו שפוספס</h2>

        {/* Context */}
        <div className="bg-gray-50 rounded-xl p-4 mb-6">
          <p className="text-sm text-gray-400 mb-1">בתור זה, ההורה אמר/ה:</p>
          <p className="text-gray-700">"{parentMessage}"</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Type selection */}
          <div>
            <p className="text-sm text-gray-600 mb-3">סוג:</p>
            <div className="space-y-2">
              {[
                { value: 'observation', label: 'תצפית שפוספסה' },
                { value: 'curiosity', label: 'סקרנות שהיתה צריכה להיווצר' },
                { value: 'hypothesis', label: 'השערה שהיתה צריכה להיווצר' },
              ].map((opt) => (
                <label key={opt.value} className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="radio"
                    name="type"
                    checked={signalType === opt.value}
                    onChange={() => setSignalType(opt.value)}
                    className="w-4 h-4 text-amber-500"
                  />
                  <span className="text-gray-700">{opt.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Content */}
          <div>
            <label className="text-sm text-gray-600 block mb-2">תוכן:</label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="מה היה צריך להיות מזוהה..."
              className="w-full p-3 border border-gray-200 rounded-xl text-gray-800 placeholder:text-gray-300 h-24 resize-none"
            />
          </div>

          {/* Domain */}
          <div>
            <label className="text-sm text-gray-600 block mb-2">תחום:</label>
            <select
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              className="w-full p-3 border border-gray-200 rounded-xl text-gray-800"
            >
              <option value="">בחר תחום...</option>
              {Object.entries(DOMAIN_HE).map(([key, label]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>
          </div>

          {/* Why important */}
          <div>
            <label className="text-sm text-gray-600 block mb-2">הסבר למה זה חשוב:</label>
            <textarea
              value={whyImportant}
              onChange={(e) => setWhyImportant(e.target.value)}
              placeholder="הסבר קליני..."
              className="w-full p-3 border border-gray-200 rounded-xl text-gray-800 placeholder:text-gray-300 h-24 resize-none"
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-500 hover:text-gray-700"
            >
              ביטול
            </button>
            <button
              type="submit"
              disabled={submitting || !content.trim() || !whyImportant.trim()}
              className="px-5 py-2 bg-amber-500 text-white rounded-xl hover:bg-amber-600 disabled:opacity-40"
            >
              {submitting ? 'שומר...' : 'הוסף'}
            </button>
          </div>
        </form>
      </div>
    </Modal>
  );
}

/**
 * CorrectionModal - Flag incorrect perception
 */
function CorrectionModal({ childId, turnId, target, onClose, onSuccess }) {
  const [correctionType, setCorrectionType] = useState('domain_change');
  const [newDomain, setNewDomain] = useState('');
  const [reasoning, setReasoning] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const targetName = {
    observation: 'תצפית',
    curiosity: 'סקרנות',
    hypothesis: 'השערה',
    response: 'תשובה',
  }[target.target] || target.target;

  const correctionTypes = [
    { value: 'domain_change', label: 'התחום שגוי' },
    { value: 'extraction_error', label: 'ההבנה לא מדויקת' },
    { value: 'hallucination', label: 'המציאה משהו שלא נאמר' },
    { value: 'missed_context', label: 'פספסה הקשר חשוב' },
    { value: 'premature_hypothesis', label: 'השערה מוקדמת מדי' },
    { value: 'wrong_theory', label: 'תיאוריה שגויה' },
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!reasoning.trim()) return;

    setSubmitting(true);
    try {
      await api.createCorrection(childId, turnId, {
        target_type: target.target,
        correction_type: correctionType,
        original_value: target.data?.arguments || target.data,
        corrected_value: newDomain ? { domain: newDomain } : null,
        expert_reasoning: reasoning,
        severity: 'medium',
      });
      onSuccess();
    } catch (err) {
      console.error('Error:', err);
    } finally {
      setSubmitting(false);
    }
  };

  // Extract what to show
  const originalContent = target.data?.arguments?.observation
    || target.data?.arguments?.about
    || target.data?.arguments?.theory
    || target.data?.response_text
    || '';
  const originalDomain = target.data?.arguments?.domain;

  return (
    <Modal onClose={onClose}>
      <div className="p-6">
        <h2 className="text-lg font-medium text-gray-800 mb-6">תיקון {targetName}</h2>

        {/* What Chitta understood */}
        <div className="bg-gray-50 rounded-xl p-4 mb-6">
          <p className="text-sm text-gray-400 mb-1">צ'יטה הבינה:</p>
          <p className="text-gray-700 mb-2">"{originalContent}"</p>
          {originalDomain && (
            <span className="text-sm text-gray-500">
              תחום: {DOMAIN_HE[originalDomain] || originalDomain}
            </span>
          )}
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* What's wrong */}
          <div>
            <p className="text-sm text-gray-600 mb-3">מה לא נכון?</p>
            <div className="space-y-2">
              {correctionTypes.map((opt) => (
                <label key={opt.value} className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="radio"
                    name="type"
                    checked={correctionType === opt.value}
                    onChange={() => setCorrectionType(opt.value)}
                    className="w-4 h-4 text-red-400"
                  />
                  <span className="text-gray-700">{opt.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* New domain if domain change */}
          {correctionType === 'domain_change' && (
            <div>
              <label className="text-sm text-gray-600 block mb-2">התחום הנכון:</label>
              <select
                value={newDomain}
                onChange={(e) => setNewDomain(e.target.value)}
                className="w-full p-3 border border-gray-200 rounded-xl text-gray-800"
              >
                <option value="">בחר תחום...</option>
                {Object.entries(DOMAIN_HE).map(([key, label]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
            </div>
          )}

          {/* Clinical reasoning */}
          <div>
            <label className="text-sm text-gray-600 block mb-2">הסבר קליני:</label>
            <textarea
              value={reasoning}
              onChange={(e) => setReasoning(e.target.value)}
              placeholder="הסבר למה הפרשנות שגויה ומה היה הנכון..."
              className="w-full p-3 border border-gray-200 rounded-xl text-gray-800 placeholder:text-gray-300 h-28 resize-none"
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-500 hover:text-gray-700"
            >
              ביטול
            </button>
            <button
              type="submit"
              disabled={submitting || !reasoning.trim()}
              className="px-5 py-2 bg-red-400 text-white rounded-xl hover:bg-red-500 disabled:opacity-40"
            >
              {submitting ? 'שומר...' : 'שמור תיקון'}
            </button>
          </div>
        </form>
      </div>
    </Modal>
  );
}
