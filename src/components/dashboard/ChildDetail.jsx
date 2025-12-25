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
 * Hypotheses View - Shows all hypotheses with lifecycle
 */
function HypothesesView({ childId, curiosities }) {
  // Filter hypotheses from curiosities
  const hypotheses = [
    ...(curiosities?.dynamic?.filter(c => c.type === 'hypothesis') || []),
  ];

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
      <h2 className="text-xl font-medium text-gray-800 mb-6">
        השערות ({hypotheses.length})
      </h2>

      <div className="space-y-4">
        {hypotheses.map((h, i) => (
          <HypothesisCard key={h.focus || i} hypothesis={h} />
        ))}
      </div>
    </div>
  );
}

/**
 * Hypothesis Card - Matches plan section 6.2
 */
function HypothesisCard({ hypothesis }) {
  const certainty = hypothesis.certainty || 0;
  const certaintyPercent = Math.round(certainty * 100);

  // Status based on certainty and state
  const getStatus = () => {
    if (certainty >= 0.7) return { label: 'מאושר', color: 'emerald', icon: '●' };
    if (certainty >= 0.4) return { label: 'בבדיקה', color: 'amber', icon: '◐' };
    return { label: 'בתחילת דרך', color: 'gray', icon: '○' };
  };

  const status = getStatus();

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-lg">◆</span>
          <span className="text-purple-600 font-medium">💡 השערה</span>
        </div>
        <span className={`px-2 py-1 rounded-lg text-xs bg-${status.color}-50 text-${status.color}-600`}>
          {status.icon} {status.label}
        </span>
      </div>

      {/* Theory */}
      <p className="text-gray-800 text-lg leading-relaxed mb-4">
        "{hypothesis.theory || hypothesis.about}"
      </p>

      {/* Certainty bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between text-sm text-gray-500 mb-1">
          <span>ודאות</span>
          <span>{certaintyPercent}%</span>
        </div>
        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${
              certainty >= 0.7 ? 'bg-emerald-400' :
              certainty >= 0.4 ? 'bg-amber-400' : 'bg-gray-300'
            }`}
            style={{ width: `${certaintyPercent}%` }}
          />
        </div>
      </div>

      {/* Meta */}
      <div className="flex items-center gap-4 text-sm text-gray-400">
        {hypothesis.domain && (
          <span>תחום: {hypothesis.domain}</span>
        )}
        {hypothesis.evidence_count > 0 && (
          <span>📊 {hypothesis.evidence_count} ראיות</span>
        )}
        {hypothesis.video_status && (
          <span>🎬 {hypothesis.video_status}</span>
        )}
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
