import React, { useState, useEffect } from 'react';
import { useParams, NavLink, Routes, Route, useNavigate, Navigate } from 'react-router-dom';
import {
  ChevronLeft,
  MessageSquare,
  Lightbulb,
  Sparkles,
  BarChart3,
  RefreshCw,
  Eye,
  Video,
  FileText,
} from 'lucide-react';

import { api } from '../../api/client';
import ConversationReplay from './ConversationReplay';

/**
 * Child Detail - Unified Dashboard View
 *
 * Consolidated tabs following COGNITIVE_DASHBOARD_PLAN.md:
 * - 💬 שיחה (Conversation) - Default, unified timeline
 * - 💡 השערות (Hypotheses) - Hypothesis lifecycle
 * - 🔮 קריסטל (Crystal) - Synthesized understanding
 * - 📊 אנליטיקה (Analytics) - Correction patterns
 */
export default function ChildDetail() {
  const { childId } = useParams();
  const navigate = useNavigate();
  const [child, setChild] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadChild();
  }, [childId]);

  async function loadChild() {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getChildFull(childId);
      setChild(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-indigo-200 border-t-indigo-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8" dir="rtl">
        <div className="bg-red-50 border border-red-100 rounded-xl p-6 text-red-700 text-center mb-4">
          שגיאה בטעינת הנתונים
        </div>
        <button
          onClick={() => navigate('/dashboard/children')}
          className="flex items-center gap-2 text-indigo-600 hover:text-indigo-700"
        >
          <ChevronLeft className="w-4 h-4" />
          חזרה לרשימה
        </button>
      </div>
    );
  }

  // Calculate stats
  const observationsCount = child?.understanding?.observations?.length || 0;
  const curiositiesCount =
    (child?.curiosities?.perpetual?.length || 0) +
    (child?.curiosities?.dynamic?.length || 0);
  const hypothesesCount = child?.curiosities?.dynamic?.filter(
    c => c.type === 'hypothesis'
  )?.length || 0;
  const videosCount = child?.videos?.length || 0;
  const messagesCount = child?.session_history_length || 0;

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-100 px-6 py-4">
        <div className="max-w-6xl mx-auto">
          {/* Top row: Back + Child info + Refresh */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/dashboard/children')}
                className="p-2 hover:bg-gray-100 rounded-xl transition"
                title="חזרה"
              >
                <ChevronLeft className="w-5 h-5 text-gray-400" />
              </button>

              <div className="flex items-center gap-3">
                {/* Avatar */}
                <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white text-lg font-bold shadow-sm">
                  {child?.child_name ? child.child_name[0] : '?'}
                </div>

                {/* Name and meta */}
                <div dir="rtl">
                  <h1 className="text-xl font-bold text-gray-800">
                    {child?.child_name || 'ילד ללא שם'}
                  </h1>
                  <p className="text-sm text-gray-400">
                    {child?.child_age_months
                      ? formatAge(child.child_age_months)
                      : ''}
                    {child?.child_gender && (
                      <span className="mr-2">
                        · {child.child_gender === 'male' ? 'בן' : child.child_gender === 'female' ? 'בת' : ''}
                      </span>
                    )}
                  </p>
                </div>
              </div>
            </div>

            <button
              onClick={loadChild}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-xl transition"
              title="רענן"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
          </div>

          {/* Stats row */}
          <div className="flex items-center gap-3 mb-4" dir="rtl">
            <Stat icon={<Eye className="w-4 h-4" />} value={observationsCount} label="תצפיות" />
            <Stat icon={<Lightbulb className="w-4 h-4" />} value={curiositiesCount} label="סקרנויות" />
            <Stat icon={<Lightbulb className="w-4 h-4" />} value={hypothesesCount} label="השערות" color="purple" />
            <Stat icon={<Video className="w-4 h-4" />} value={videosCount} label="סרטונים" color="violet" />
            <Stat icon={<MessageSquare className="w-4 h-4" />} value={messagesCount} label="הודעות" color="blue" />
          </div>

          {/* Tab Navigation */}
          <nav className="flex items-center gap-1 -mb-px" dir="rtl">
            <TabLink to={`/dashboard/children/${childId}`} end>
              <MessageSquare className="w-4 h-4" />
              שיחה
            </TabLink>
            <TabLink to={`/dashboard/children/${childId}/hypotheses`}>
              <Lightbulb className="w-4 h-4" />
              השערות
            </TabLink>
            <TabLink to={`/dashboard/children/${childId}/crystal`}>
              <Sparkles className="w-4 h-4" />
              קריסטל
            </TabLink>
            <TabLink to={`/dashboard/children/${childId}/analytics`}>
              <BarChart3 className="w-4 h-4" />
              אנליטיקה
            </TabLink>
          </nav>
        </div>
      </header>

      {/* Tab Content */}
      <main className="flex-1 overflow-auto">
        <Routes>
          {/* Default: Conversation/Timeline */}
          <Route
            index
            element={<ConversationReplay childId={childId} />}
          />

          {/* Hypotheses */}
          <Route
            path="hypotheses"
            element={
              <HypothesesView
                childId={childId}
                curiosities={child?.curiosities}
              />
            }
          />

          {/* Crystal */}
          <Route
            path="crystal"
            element={<CrystalView crystal={child?.crystal} />}
          />

          {/* Analytics */}
          <Route
            path="analytics"
            element={<AnalyticsView childId={childId} />}
          />

          {/* Redirect old routes */}
          <Route path="timeline" element={<Navigate to={`/dashboard/children/${childId}`} replace />} />
          <Route path="conversation" element={<Navigate to={`/dashboard/children/${childId}`} replace />} />
          <Route path="understanding" element={<Navigate to={`/dashboard/children/${childId}`} replace />} />
          <Route path="notes" element={<Navigate to={`/dashboard/children/${childId}/analytics`} replace />} />
        </Routes>
      </main>
    </div>
  );
}

/**
 * Format age in Hebrew
 */
function formatAge(months) {
  if (!months) return '';
  const years = Math.floor(months / 12);
  const remainingMonths = Math.round(months % 12);

  if (years === 0) {
    return `${remainingMonths} חודשים`;
  } else if (remainingMonths === 0) {
    return `${years} ${years === 1 ? 'שנה' : 'שנים'}`;
  } else {
    return `${years} ${years === 1 ? 'שנה' : 'שנים'} ו-${remainingMonths} חודשים`;
  }
}

/**
 * Stat pill
 */
function Stat({ icon, value, label, color = 'gray' }) {
  const colors = {
    gray: 'bg-gray-100 text-gray-600',
    purple: 'bg-purple-50 text-purple-600',
    violet: 'bg-violet-50 text-violet-600',
    blue: 'bg-blue-50 text-blue-600',
    amber: 'bg-amber-50 text-amber-600',
  };

  return (
    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm ${colors[color]}`}>
      {icon}
      <span className="font-medium">{value}</span>
      <span className="opacity-70">{label}</span>
    </div>
  );
}

/**
 * Tab Link
 */
function TabLink({ to, children, end = false }) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        `flex items-center gap-2 px-4 py-2.5 rounded-t-xl text-sm font-medium transition ${
          isActive
            ? 'bg-gray-50 text-indigo-600 border-b-2 border-indigo-500'
            : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50/50'
        }`
      }
    >
      {children}
    </NavLink>
  );
}

/**
 * Hypotheses View - Shows all hypotheses with lifecycle (plan sections 6.2, 6.3, 6.4, 7)
 */
function HypothesesView({ childId, curiosities }) {
  const [expandedHypothesis, setExpandedHypothesis] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);

  // Filter hypotheses from curiosities
  const hypotheses = [
    ...(curiosities?.dynamic?.filter(c => c.type === 'hypothesis') || []),
  ];

  // Group by status
  const investigating = hypotheses.filter(h => (h.certainty || 0) < 0.7 && (h.certainty || 0) >= 0.3);
  const confirmed = hypotheses.filter(h => (h.certainty || 0) >= 0.7);
  const wondering = hypotheses.filter(h => (h.certainty || 0) < 0.3);

  if (hypotheses.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center" dir="rtl">
        <Lightbulb className="w-12 h-12 text-gray-200 mb-4" />
        <h3 className="text-gray-400 text-lg mb-2">אין השערות עדיין</h3>
        <p className="text-gray-300 text-sm max-w-md">
          השערות נוצרות כאשר צ'יטה מזהה דפוסים שדורשים בדיקה.
          <br />
          המשיכו בשיחה וההשערות יופיעו כאן.
        </p>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto" dir="rtl">
      {/* Header with stats */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-medium text-gray-800">
          השערות ({hypotheses.length})
        </h2>
        <div className="flex items-center gap-3 text-sm">
          {confirmed.length > 0 && (
            <span className="px-2 py-1 bg-emerald-50 text-emerald-600 rounded-lg">
              ● {confirmed.length} מאושרות
            </span>
          )}
          {investigating.length > 0 && (
            <span className="px-2 py-1 bg-amber-50 text-amber-600 rounded-lg">
              ◐ {investigating.length} בבדיקה
            </span>
          )}
          {wondering.length > 0 && (
            <span className="px-2 py-1 bg-gray-100 text-gray-500 rounded-lg">
              ○ {wondering.length} בתחילת דרך
            </span>
          )}
        </div>
      </div>

      {/* Hypothesis cards */}
      <div className="space-y-4">
        {hypotheses.map((h) => (
          <HypothesisLifecycleCard
            key={h.focus}
            hypothesis={h}
            childId={childId}
            isExpanded={expandedHypothesis === h.focus}
            onToggle={() => setExpandedHypothesis(
              expandedHypothesis === h.focus ? null : h.focus
            )}
            onRefresh={() => setRefreshKey(k => k + 1)}
          />
        ))}
      </div>
    </div>
  );
}

// Domain translations for hypotheses view
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

const VIDEO_VALUE_HE = {
  calibration: 'כיול',
  chain: 'שרשרת',
  discovery: 'גילוי',
  reframe: 'מסגור מחדש',
  relational: 'יחסי',
};

const EFFECT_HE = {
  supports: 'תומך',
  contradicts: 'סותר',
  transforms: 'משנה',
};

/**
 * Hypothesis Lifecycle Card - Full view with evidence, video, lifecycle (plan 6.2, 6.3, 6.4, 7)
 */
function HypothesisLifecycleCard({ hypothesis, childId, isExpanded, onToggle, onRefresh }) {
  const [activeSection, setActiveSection] = useState(null); // 'evidence' | 'video' | 'lifecycle' | null
  const [showAddEvidence, setShowAddEvidence] = useState(false);
  const [showAdjustCertainty, setShowAdjustCertainty] = useState(false);

  const certainty = hypothesis.certainty || 0;
  const certaintyPercent = Math.round(certainty * 100);
  const evidence = hypothesis.evidence || [];
  const hasVideoRec = hypothesis.video_appropriate || hypothesis.video_value;

  // Status based on certainty
  const getStatus = () => {
    if (hypothesis.status === 'refuted') return { label: 'נדחה', color: 'red', icon: '✗' };
    if (hypothesis.status === 'transformed') return { label: 'שונה', color: 'blue', icon: '↻' };
    if (certainty >= 0.7) return { label: 'מאושר', color: 'emerald', icon: '●' };
    if (certainty >= 0.3) return { label: 'בבדיקה', color: 'amber', icon: '◐' };
    return { label: 'בתחילת דרך', color: 'gray', icon: '○' };
  };

  const status = getStatus();
  const statusColors = {
    emerald: 'bg-emerald-50 text-emerald-600 border-emerald-200',
    amber: 'bg-amber-50 text-amber-600 border-amber-200',
    gray: 'bg-gray-50 text-gray-500 border-gray-200',
    red: 'bg-red-50 text-red-600 border-red-200',
    blue: 'bg-blue-50 text-blue-600 border-blue-200',
  };

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
      {/* Header - Always visible */}
      <button
        onClick={onToggle}
        className="w-full text-right p-5 hover:bg-gray-50/50 transition"
      >
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="text-purple-500 text-lg">◆</span>
            <span className="text-purple-600 font-medium">💡 השערה</span>
          </div>
          <span className={`px-2.5 py-1 rounded-lg text-xs border ${statusColors[status.color]}`}>
            {status.icon} {status.label}
          </span>
        </div>

        {/* Theory */}
        <p className="text-gray-800 text-lg leading-relaxed mb-4">
          "{hypothesis.theory || hypothesis.focus}"
        </p>

        {/* Certainty bar with value */}
        <div className="mb-3">
          <div className="flex items-center justify-between text-sm text-gray-500 mb-1">
            <span>ודאות</span>
            <span className="font-medium">{certaintyPercent}%</span>
          </div>
          <div className="h-2.5 bg-gray-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${
                certainty >= 0.7 ? 'bg-emerald-400' :
                certainty >= 0.3 ? 'bg-amber-400' : 'bg-gray-300'
              }`}
              style={{ width: `${certaintyPercent}%` }}
            />
          </div>
        </div>

        {/* Quick stats */}
        <div className="flex items-center gap-4 text-sm text-gray-500">
          {hypothesis.domain && (
            <span>תחום: {DOMAIN_HE[hypothesis.domain] || hypothesis.domain}</span>
          )}
          <span>📊 {evidence.length} ראיות</span>
          {hasVideoRec && (
            <span className="text-violet-600">🎬 וידאו מומלץ</span>
          )}
        </div>
      </button>

      {/* Expanded content */}
      {isExpanded && (
        <div className="border-t border-gray-100 p-5 space-y-4">
          {/* Action tabs */}
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => setActiveSection(activeSection === 'evidence' ? null : 'evidence')}
              className={`px-3 py-1.5 rounded-lg text-sm transition ${
                activeSection === 'evidence'
                  ? 'bg-purple-100 text-purple-700'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              📊 ראיות ({evidence.length})
            </button>
            {hasVideoRec && (
              <button
                onClick={() => setActiveSection(activeSection === 'video' ? null : 'video')}
                className={`px-3 py-1.5 rounded-lg text-sm transition ${
                  activeSection === 'video'
                    ? 'bg-violet-100 text-violet-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                🎬 וידאו
              </button>
            )}
            <button
              onClick={() => setActiveSection(activeSection === 'lifecycle' ? null : 'lifecycle')}
              className={`px-3 py-1.5 rounded-lg text-sm transition ${
                activeSection === 'lifecycle'
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              📈 מחזור חיים
            </button>

            <div className="flex-1" />

            {/* Expert actions */}
            <button
              onClick={() => setShowAdjustCertainty(true)}
              className="px-3 py-1.5 bg-amber-50 text-amber-600 rounded-lg text-sm hover:bg-amber-100"
            >
              ✎ התאם ודאות
            </button>
            <button
              onClick={() => setShowAddEvidence(true)}
              className="px-3 py-1.5 bg-emerald-50 text-emerald-600 rounded-lg text-sm hover:bg-emerald-100"
            >
              + הוסף ראיה
            </button>
          </div>

          {/* Evidence Section */}
          {activeSection === 'evidence' && (
            <EvidenceTrail evidence={evidence} />
          )}

          {/* Video Section */}
          {activeSection === 'video' && (
            <VideoWorkflowSection hypothesis={hypothesis} />
          )}

          {/* Lifecycle Section */}
          {activeSection === 'lifecycle' && (
            <LifecycleSection hypothesis={hypothesis} evidence={evidence} />
          )}

          {/* Add Evidence Modal */}
          {showAddEvidence && (
            <AddEvidenceModal
              childId={childId}
              hypothesisFocus={hypothesis.focus}
              onClose={() => setShowAddEvidence(false)}
              onSuccess={() => { setShowAddEvidence(false); onRefresh(); }}
            />
          )}

          {/* Adjust Certainty Modal */}
          {showAdjustCertainty && (
            <AdjustCertaintyModal
              childId={childId}
              hypothesisFocus={hypothesis.focus}
              currentCertainty={certainty}
              onClose={() => setShowAdjustCertainty(false)}
              onSuccess={() => { setShowAdjustCertainty(false); onRefresh(); }}
            />
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Evidence Trail - Shows all evidence with effects (plan 6.3)
 */
function EvidenceTrail({ evidence }) {
  if (evidence.length === 0) {
    return (
      <div className="p-4 bg-gray-50 rounded-xl text-center text-gray-400">
        אין ראיות עדיין
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {evidence.map((e, i) => (
        <div key={i} className="p-4 bg-gray-50 rounded-xl border border-gray-100">
          <div className="flex items-start justify-between mb-2">
            <span className="text-sm text-gray-400">ראיה #{i + 1}</span>
            <span className={`px-2 py-0.5 rounded text-xs ${
              e.effect === 'supports' ? 'bg-emerald-100 text-emerald-700' :
              e.effect === 'contradicts' ? 'bg-red-100 text-red-700' :
              'bg-blue-100 text-blue-700'
            }`}>
              {e.effect === 'supports' ? '⬆ תומך' :
               e.effect === 'contradicts' ? '⬇ סותר' :
               '↻ משנה'}
            </span>
          </div>
          <p className="text-gray-700 mb-2">"{e.content}"</p>
          <div className="flex items-center gap-3 text-xs text-gray-400">
            <span>מקור: {e.source || 'שיחה'}</span>
            {e.timestamp && (
              <span>{new Date(e.timestamp).toLocaleDateString('he-IL')}</span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * Video Workflow Section - Shows video recommendation status (plan 6.4)
 */
function VideoWorkflowSection({ hypothesis }) {
  const steps = [
    {
      num: '1️⃣',
      title: 'הצעה',
      status: hypothesis.video_appropriate ? 'done' : 'pending',
      content: hypothesis.video_value_reason || 'וידאו יכול לעזור לאמת את ההשערה',
    },
    {
      num: '2️⃣',
      title: 'הנחיות',
      status: 'pending',
      content: 'ממתין להנחיות צילום',
    },
    {
      num: '3️⃣',
      title: 'הועלה',
      status: 'pending',
      content: 'ממתין להעלאה',
    },
    {
      num: '4️⃣',
      title: 'נותח',
      status: 'pending',
      content: 'ממתין לניתוח',
    },
  ];

  return (
    <div className="p-4 bg-violet-50/50 rounded-xl border border-violet-100">
      <div className="text-sm font-medium text-violet-700 mb-4">תהליך וידאו</div>
      <div className="space-y-3">
        {steps.map((step, i) => (
          <div
            key={i}
            className={`p-3 rounded-lg ${
              step.status === 'done' ? 'bg-white border border-violet-200' : 'bg-violet-50/50'
            }`}
          >
            <div className="flex items-center gap-2 mb-1">
              <span>{step.num}</span>
              <span className="font-medium text-gray-700">{step.title}</span>
              {step.status === 'done' && (
                <span className="text-emerald-500">✓</span>
              )}
            </div>
            <p className="text-sm text-gray-500 pr-6">{step.content}</p>
          </div>
        ))}
      </div>

      {hypothesis.video_value && (
        <div className="mt-4 p-3 bg-white rounded-lg border border-violet-200">
          <span className="text-xs text-violet-600">סוג ערך:</span>
          <span className="mr-2 px-2 py-0.5 bg-violet-100 text-violet-700 rounded text-sm">
            {VIDEO_VALUE_HE[hypothesis.video_value] || hypothesis.video_value}
          </span>
        </div>
      )}
    </div>
  );
}

/**
 * Lifecycle Section - Shows certainty progression (plan section 7)
 */
function LifecycleSection({ hypothesis, evidence }) {
  const certainty = hypothesis.certainty || 0;

  // Build timeline from evidence
  const events = [
    { label: 'נוצרה', certainty: 0.3, type: 'created' },
    ...evidence.map((e, i) => ({
      label: e.effect === 'supports' ? '+ראיה תומכת' :
             e.effect === 'contradicts' ? '-ראיה סותרת' : '↻ שינוי',
      certainty: 0.3 + (i + 1) * 0.1 * (e.effect === 'contradicts' ? -1 : 1),
      type: e.effect,
    })),
  ];

  return (
    <div className="p-4 bg-blue-50/50 rounded-xl border border-blue-100">
      <div className="text-sm font-medium text-blue-700 mb-4">מחזור חיים</div>

      {/* Status legend */}
      <div className="flex items-center gap-4 mb-4 text-xs">
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-gray-300" /> בתחילת דרך
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-amber-400" /> בבדיקה
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-emerald-400" /> מאושר
        </span>
      </div>

      {/* Certainty progression */}
      <div className="relative h-24 bg-white rounded-lg border border-blue-100 p-3">
        {/* Y-axis labels */}
        <div className="absolute right-0 top-0 bottom-0 w-8 flex flex-col justify-between text-xs text-gray-400 py-1">
          <span>1.0</span>
          <span>0.5</span>
          <span>0.0</span>
        </div>

        {/* Graph area */}
        <div className="mr-10 h-full relative">
          {/* Threshold lines */}
          <div className="absolute top-[30%] left-0 right-0 border-t border-dashed border-emerald-300" />
          <div className="absolute top-[70%] left-0 right-0 border-t border-dashed border-amber-300" />

          {/* Current certainty marker */}
          <div
            className="absolute left-0 right-0 h-0.5 bg-purple-400"
            style={{ top: `${(1 - certainty) * 100}%` }}
          />
          <div
            className="absolute right-0 w-3 h-3 rounded-full bg-purple-500 border-2 border-white shadow"
            style={{ top: `${(1 - certainty) * 100}%`, transform: 'translateY(-50%)' }}
          />
        </div>
      </div>

      {/* Events timeline */}
      <div className="mt-4 flex items-center gap-2 overflow-x-auto py-2">
        {events.map((event, i) => (
          <div
            key={i}
            className={`flex-shrink-0 px-2 py-1 rounded text-xs ${
              event.type === 'created' ? 'bg-gray-100 text-gray-600' :
              event.type === 'supports' ? 'bg-emerald-100 text-emerald-700' :
              event.type === 'contradicts' ? 'bg-red-100 text-red-700' :
              'bg-blue-100 text-blue-700'
            }`}
          >
            {event.label}
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Add Evidence Modal
 */
function AddEvidenceModal({ childId, hypothesisFocus, onClose, onSuccess }) {
  const [content, setContent] = useState('');
  const [effect, setEffect] = useState('supports');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!content.trim()) return;

    setSubmitting(true);
    try {
      await api.addExpertEvidence(childId, hypothesisFocus, content, effect);
      onSuccess();
    } catch (err) {
      console.error('Error:', err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="bg-white rounded-2xl shadow-xl max-w-lg w-full p-6" dir="rtl">
        <h2 className="text-lg font-medium text-gray-800 mb-6">הוסף ראיה</h2>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="text-sm text-gray-600 block mb-2">תוכן הראיה:</label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="תיאור הראיה..."
              className="w-full p-3 border border-gray-200 rounded-xl text-gray-800 placeholder:text-gray-300 h-24 resize-none"
            />
          </div>

          <div>
            <p className="text-sm text-gray-600 mb-3">השפעה על ההשערה:</p>
            <div className="space-y-2">
              {[
                { value: 'supports', label: 'תומך בהשערה', icon: '⬆', color: 'emerald' },
                { value: 'contradicts', label: 'סותר את ההשערה', icon: '⬇', color: 'red' },
                { value: 'transforms', label: 'משנה את ההשערה', icon: '↻', color: 'blue' },
              ].map((opt) => (
                <label key={opt.value} className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="radio"
                    name="effect"
                    checked={effect === opt.value}
                    onChange={() => setEffect(opt.value)}
                    className="w-4 h-4"
                  />
                  <span className={`text-${opt.color}-600`}>{opt.icon}</span>
                  <span className="text-gray-700">{opt.label}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-gray-500 hover:text-gray-700">
              ביטול
            </button>
            <button
              type="submit"
              disabled={submitting || !content.trim()}
              className="px-5 py-2 bg-emerald-500 text-white rounded-xl hover:bg-emerald-600 disabled:opacity-40"
            >
              {submitting ? 'שומר...' : 'הוסף ראיה'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

/**
 * Adjust Certainty Modal
 */
function AdjustCertaintyModal({ childId, hypothesisFocus, currentCertainty, onClose, onSuccess }) {
  const [newCertainty, setNewCertainty] = useState(currentCertainty);
  const [reason, setReason] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!reason.trim()) return;

    setSubmitting(true);
    try {
      await api.adjustCertainty(childId, hypothesisFocus, newCertainty, reason);
      onSuccess();
    } catch (err) {
      console.error('Error:', err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="bg-white rounded-2xl shadow-xl max-w-lg w-full p-6" dir="rtl">
        <h2 className="text-lg font-medium text-gray-800 mb-6">התאם ודאות</h2>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="text-sm text-gray-600 block mb-2">ודאות חדשה: {Math.round(newCertainty * 100)}%</label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={newCertainty}
              onChange={(e) => setNewCertainty(parseFloat(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>0%</span>
              <span>50%</span>
              <span>100%</span>
            </div>
          </div>

          <div>
            <label className="text-sm text-gray-600 block mb-2">סיבה לשינוי:</label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="הסבר את הסיבה להתאמה..."
              className="w-full p-3 border border-gray-200 rounded-xl text-gray-800 placeholder:text-gray-300 h-24 resize-none"
            />
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-gray-500 hover:text-gray-700">
              ביטול
            </button>
            <button
              type="submit"
              disabled={submitting || !reason.trim()}
              className="px-5 py-2 bg-amber-500 text-white rounded-xl hover:bg-amber-600 disabled:opacity-40"
            >
              {submitting ? 'שומר...' : 'שמור שינוי'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

/**
 * Crystal View - Synthesized understanding
 */
function CrystalView({ crystal }) {
  if (!crystal) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center" dir="rtl">
        <Sparkles className="w-12 h-12 text-gray-200 mb-4" />
        <h3 className="text-gray-400 text-lg mb-2">הקריסטל טרם התגבש</h3>
        <p className="text-gray-300 text-sm max-w-md">
          הקריסטל נוצר כאשר ההבנה מגיעה לעומק מספיק.
          <br />
          המשיכו בשיחה והקריסטל יתגבש.
        </p>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6" dir="rtl">
      {/* Essence */}
      <section className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
        <h2 className="text-lg font-medium text-gray-800 mb-4 flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-purple-500" />
          מהות
        </h2>
        <p className="text-gray-700 text-lg leading-relaxed">
          {crystal.essence_narrative || 'טרם נוצר תיאור מהות'}
        </p>
      </section>

      {/* Temperament & Qualities */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <section className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <h3 className="text-gray-600 font-medium mb-3">מזג</h3>
          <div className="flex flex-wrap gap-2">
            {crystal.temperament?.length > 0 ? (
              crystal.temperament.map((t, i) => (
                <span key={i} className="px-3 py-1.5 bg-amber-50 text-amber-700 rounded-full text-sm">
                  {t}
                </span>
              ))
            ) : (
              <span className="text-gray-300">טרם זוהה</span>
            )}
          </div>
        </section>

        <section className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <h3 className="text-gray-600 font-medium mb-3">תכונות ליבה</h3>
          <div className="flex flex-wrap gap-2">
            {crystal.core_qualities?.length > 0 ? (
              crystal.core_qualities.map((q, i) => (
                <span key={i} className="px-3 py-1.5 bg-emerald-50 text-emerald-700 rounded-full text-sm">
                  {q}
                </span>
              ))
            ) : (
              <span className="text-gray-300">טרם זוהו</span>
            )}
          </div>
        </section>
      </div>

      {/* Patterns */}
      {crystal.patterns?.length > 0 && (
        <section className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <h3 className="text-gray-600 font-medium mb-4">דפוסים ({crystal.patterns.length})</h3>
          <div className="space-y-3">
            {crystal.patterns.map((p, i) => (
              <div key={i} className="p-4 bg-gray-50 rounded-xl">
                <p className="text-gray-800">{p.description}</p>
                <div className="flex items-center gap-3 mt-2 text-sm text-gray-400">
                  <span>תחומים: {p.domains?.join(', ')}</span>
                  <span>ודאות: {Math.round((p.confidence || 0) * 100)}%</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Version info */}
      <p className="text-center text-sm text-gray-300">
        גרסה {crystal.version || 1}
        {crystal.generated_at && (
          <span> · נוצר ב-{new Date(crystal.generated_at).toLocaleDateString('he-IL')}</span>
        )}
      </p>
    </div>
  );
}

/**
 * Analytics View - Correction patterns and improvement metrics
 */
function AnalyticsView({ childId }) {
  return (
    <div className="p-6 max-w-4xl mx-auto" dir="rtl">
      <h2 className="text-xl font-medium text-gray-800 mb-6">אנליטיקה</h2>

      {/* Placeholder - will be enhanced */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 text-center">
          <div className="text-3xl font-bold text-gray-800 mb-1">0</div>
          <div className="text-sm text-gray-400">תיקונים</div>
        </div>
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 text-center">
          <div className="text-3xl font-bold text-amber-600 mb-1">0</div>
          <div className="text-sm text-gray-400">אותות שפוספסו</div>
        </div>
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 text-center">
          <div className="text-3xl font-bold text-emerald-600 mb-1">—</div>
          <div className="text-sm text-gray-400">דיוק</div>
        </div>
      </div>

      {/* Coming soon */}
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <BarChart3 className="w-12 h-12 text-gray-200 mb-4" />
        <h3 className="text-gray-400 text-lg mb-2">אנליטיקה מתקדמת בקרוב</h3>
        <p className="text-gray-300 text-sm max-w-md">
          כאן יוצגו דפוסי תיקונים, מדדי שיפור, והמלצות לאימון.
        </p>
      </div>
    </div>
  );
}
