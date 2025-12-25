import React, { useState, useEffect, useRef } from 'react';
import { useParams, NavLink, Routes, Route, useNavigate, Navigate, Link, useSearchParams } from 'react-router-dom';
import {
  ChevronLeft,
  ChevronUp,
  ChevronDown,
  MessageSquare,
  Lightbulb,
  Sparkles,
  BarChart3,
  RefreshCw,
  Eye,
  Video,
  FileText,
  HelpCircle,
  X,
  Play,
  Clock,
  CheckCircle,
  AlertCircle,
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

            <div className="flex items-center gap-1">
              <Link
                to="/dashboard/guide"
                className="p-2 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-xl transition"
                title="מדריך למומחה"
              >
                <HelpCircle className="w-5 h-5" />
              </Link>
              <button
                onClick={loadChild}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-xl transition"
                title="רענן"
              >
                <RefreshCw className="w-5 h-5" />
              </button>
            </div>
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
              סקירת השערות
            </TabLink>
            <TabLink to={`/dashboard/children/${childId}/crystal`}>
              <Sparkles className="w-4 h-4" />
              קריסטל
            </TabLink>
            <TabLink to={`/dashboard/children/${childId}/videos`}>
              <Video className="w-4 h-4" />
              סרטונים
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
            element={<ConversationReplay childId={childId} curiosities={child?.curiosities} />}
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

          {/* Videos */}
          <Route
            path="videos"
            element={<VideosView childId={childId} />}
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
 * Hypotheses View - Overview of all hypotheses with lifecycle (plan sections 6.2, 6.3, 6.4, 7)
 * This is an overview page - full hypothesis details appear in the Conversation timeline
 */
function HypothesesView({ childId, curiosities }) {
  const navigate = useNavigate();
  const [expandedHypothesis, setExpandedHypothesis] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [videos, setVideos] = useState([]);

  // Load videos for this child
  useEffect(() => {
    async function loadVideos() {
      try {
        const data = await api.getChildVideos(childId);
        setVideos(data.videos || []);
      } catch (err) {
        console.error('Error loading videos:', err);
      }
    }
    loadVideos();
  }, [childId, refreshKey]);

  // Filter hypotheses from curiosities
  const hypotheses = [
    ...(curiosities?.dynamic?.filter(c => c.type === 'hypothesis') || []),
  ];

  // Group by status
  const investigating = hypotheses.filter(h => (h.certainty || 0) < 0.7 && (h.certainty || 0) >= 0.3);
  const confirmed = hypotheses.filter(h => (h.certainty || 0) >= 0.7);
  const wondering = hypotheses.filter(h => (h.certainty || 0) < 0.3);

  // Get videos for a specific hypothesis
  const getVideosForHypothesis = (hypothesisFocus) => {
    return videos.filter(v => v.target_hypothesis_focus === hypothesisFocus);
  };

  // Navigate to conversation (default tab)
  const goToConversation = () => {
    navigate(`/dashboard/children/${childId}`);
  };

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
      {/* Header with stats and info */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xl font-medium text-gray-800">
            סקירת השערות ({hypotheses.length})
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

        {/* Overview info banner */}
        <div className="bg-indigo-50/50 border border-indigo-100 rounded-xl p-4 flex items-center justify-between">
          <p className="text-sm text-indigo-700">
            📋 זוהי סקירה כללית של כל ההשערות. לצפייה בהשערה בהקשר המלא של השיחה, לחצו על "ראה בשיחה".
          </p>
          <button
            onClick={goToConversation}
            className="flex items-center gap-1 px-3 py-1.5 bg-indigo-100 text-indigo-700 rounded-lg text-sm hover:bg-indigo-200 transition"
          >
            <MessageSquare className="w-4 h-4" />
            לציר הזמן
          </button>
        </div>
      </div>

      {/* Hypothesis cards */}
      <div className="space-y-4">
        {hypotheses.map((h) => (
          <HypothesisLifecycleCard
            key={h.focus}
            hypothesis={h}
            childId={childId}
            videos={getVideosForHypothesis(h.focus)}
            isExpanded={expandedHypothesis === h.focus}
            onToggle={() => setExpandedHypothesis(
              expandedHypothesis === h.focus ? null : h.focus
            )}
            onRefresh={() => setRefreshKey(k => k + 1)}
            onGoToConversation={goToConversation}
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
function HypothesisLifecycleCard({ hypothesis, childId, videos = [], isExpanded, onToggle, onRefresh, onGoToConversation }) {
  const [activeSection, setActiveSection] = useState(null); // 'evidence' | 'video' | 'lifecycle' | null
  const [showAddEvidence, setShowAddEvidence] = useState(false);
  const [showAdjustCertainty, setShowAdjustCertainty] = useState(false);
  const [showFlag, setShowFlag] = useState(false);

  const certainty = hypothesis.certainty || 0;
  const certaintyPercent = Math.round(certainty * 100);
  const evidence = hypothesis.evidence || [];
  const hasVideoRec = hypothesis.video_appropriate || hypothesis.video_value;

  // Check video workflow status
  const hasVideos = videos.length > 0;
  const analyzedVideos = videos.filter(v => v.status === 'analyzed');
  const uploadedVideos = videos.filter(v => v.status === 'uploaded');
  const pendingVideos = videos.filter(v => v.status === 'pending');

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
      <div
        onClick={onToggle}
        className="w-full text-right p-5 hover:bg-gray-50/50 transition cursor-pointer"
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && onToggle()}
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

        {/* Quick stats and conversation link */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4 text-sm text-gray-500">
            {hypothesis.domain && (
              <span>תחום: {DOMAIN_HE[hypothesis.domain] || hypothesis.domain}</span>
            )}
            <span>📊 {evidence.length} ראיות</span>
            {hasVideoRec && (
              <span className="text-violet-600">🎬 וידאו מומלץ</span>
            )}
          </div>

          {/* See in conversation button */}
          {onGoToConversation && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onGoToConversation();
              }}
              className="flex items-center gap-1 px-3 py-1.5 bg-indigo-50 text-indigo-600 rounded-lg text-sm hover:bg-indigo-100 transition"
            >
              <MessageSquare className="w-4 h-4" />
              ראה בשיחה
            </button>
          )}
        </div>
      </div>

      {/* Expanded content */}
      {isExpanded && (
        <div className="border-t border-gray-100 p-5 space-y-4">
          {/* Close button row */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">פרטי השערה</span>
            <button
              onClick={onToggle}
              className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition"
            >
              סגור
              <ChevronUp className="w-4 h-4" />
            </button>
          </div>

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
            <button
              onClick={() => setShowFlag(true)}
              className="px-3 py-1.5 bg-red-50 text-red-600 rounded-lg text-sm hover:bg-red-100"
            >
              🚩 סמן בעיה
            </button>
          </div>

          {/* Section content with scroll */}
          <div className="max-h-96 overflow-y-auto">
            {/* Evidence Section */}
            {activeSection === 'evidence' && (
              <EvidenceTrail evidence={evidence} />
            )}

            {/* Video Section */}
            {activeSection === 'video' && (
              <VideoWorkflowSection hypothesis={hypothesis} videos={videos} childId={childId} />
            )}

            {/* Lifecycle Section */}
            {activeSection === 'lifecycle' && (
              <LifecycleSection hypothesis={hypothesis} evidence={evidence} />
            )}
          </div>

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

          {/* Flag Modal */}
          {showFlag && (
            <FlagModal
              childId={childId}
              targetType="hypothesis"
              targetId={hypothesis.focus}
              targetLabel={hypothesis.theory || hypothesis.focus}
              onClose={() => setShowFlag(false)}
              onSuccess={() => { setShowFlag(false); onRefresh(); }}
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
function VideoWorkflowSection({ hypothesis, videos = [], childId }) {
  const navigate = useNavigate();

  // Determine status for each step based on real data
  const hasRecommendation = hypothesis.video_appropriate || hypothesis.video_value;
  const analyzedVideos = videos.filter(v => v.status === 'analyzed');
  const uploadedVideos = videos.filter(v => v.status === 'uploaded' || v.status === 'analyzed');
  const hasGuidelines = videos.some(v => v.what_to_film); // Guidelines were generated if any video has filming instructions

  const steps = [
    {
      num: '1️⃣',
      title: 'הצעה',
      status: hasRecommendation ? 'done' : 'pending',
      content: hypothesis.video_value_reason || 'וידאו יכול לעזור לאמת את ההשערה',
    },
    {
      num: '2️⃣',
      title: 'הנחיות',
      status: hasGuidelines ? 'done' : (hasRecommendation ? 'waiting' : 'pending'),
      content: hasGuidelines ? 'הנחיות צילום נוצרו' : 'ממתין להנחיות צילום',
    },
    {
      num: '3️⃣',
      title: 'הועלה',
      status: uploadedVideos.length > 0 ? 'done' : (hasGuidelines ? 'waiting' : 'pending'),
      content: uploadedVideos.length > 0
        ? `${uploadedVideos.length} סרטונים הועלו`
        : 'ממתין להעלאה',
    },
    {
      num: '4️⃣',
      title: 'נותח',
      status: analyzedVideos.length > 0 ? 'done' : (uploadedVideos.length > 0 ? 'waiting' : 'pending'),
      content: analyzedVideos.length > 0
        ? `${analyzedVideos.length} סרטונים נותחו`
        : 'ממתין לניתוח',
    },
  ];

  const getStatusIcon = (status) => {
    if (status === 'done') return <CheckCircle className="w-4 h-4 text-emerald-500" />;
    if (status === 'waiting') return <Clock className="w-4 h-4 text-amber-500 animate-pulse" />;
    return <span className="w-4 h-4 rounded-full border-2 border-gray-300" />;
  };

  return (
    <div className="p-4 bg-violet-50/50 rounded-xl border border-violet-100">
      <div className="flex items-center justify-between mb-4">
        <div className="text-sm font-medium text-violet-700">תהליך וידאו</div>
        {videos.length > 0 && (
          <button
            onClick={() => navigate(`/dashboard/children/${childId}/videos?hypothesis=${encodeURIComponent(hypothesis.focus)}`)}
            className="flex items-center gap-1 text-xs text-violet-600 hover:text-violet-800"
          >
            צפה בסרטונים ({videos.length})
            <ChevronLeft className="w-3 h-3 rotate-180" />
          </button>
        )}
      </div>

      <div className="space-y-3">
        {steps.map((step, i) => (
          <div
            key={i}
            className={`p-3 rounded-lg transition-all ${
              step.status === 'done'
                ? 'bg-white border border-emerald-200'
                : step.status === 'waiting'
                  ? 'bg-amber-50/50 border border-amber-200'
                  : 'bg-violet-50/50'
            }`}
          >
            <div className="flex items-center gap-2 mb-1">
              <span>{step.num}</span>
              <span className="font-medium text-gray-700">{step.title}</span>
              {getStatusIcon(step.status)}
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

      {/* Show analyzed video summaries */}
      {analyzedVideos.length > 0 && (
        <div className="mt-4 space-y-2">
          <div className="text-xs text-violet-600 font-medium">סיכום ניתוחים:</div>
          {analyzedVideos.slice(0, 2).map((video, i) => (
            <div key={i} className="p-3 bg-white rounded-lg border border-gray-100 text-sm">
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium text-gray-700">{video.title}</span>
                <span className="text-xs text-gray-400">
                  {video.observations?.length || 0} תצפיות
                </span>
              </div>
              {video.certainty_after !== null && (
                <div className="text-xs text-purple-600">
                  ודאות לאחר ניתוח: {Math.round((video.certainty_after || 0) * 100)}%
                </div>
              )}
            </div>
          ))}
          {analyzedVideos.length > 2 && (
            <p className="text-xs text-gray-400 text-center">
              +{analyzedVideos.length - 2} סרטונים נוספים
            </p>
          )}
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
 * Flag Modal - Flag something as problematic
 */
function FlagModal({ childId, targetType, targetId, targetLabel, onClose, onSuccess }) {
  const [flagType, setFlagType] = useState('incorrect_inference');
  const [reason, setReason] = useState('');
  const [suggestedCorrection, setSuggestedCorrection] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const flagTypes = [
    { value: 'incorrect_inference', label: 'מסקנה שגויה', description: 'ההשערה או ההבנה לא נכונה' },
    { value: 'needs_review', label: 'דורש בדיקה', description: 'צריך לבחון שוב עם מידע נוסף' },
    { value: 'potentially_harmful', label: 'עלול להזיק', description: 'עלול להוביל להכוונה שגויה' },
    { value: 'premature', label: 'מוקדם מדי', description: 'אין מספיק מידע להסקה זו' },
    { value: 'outdated', label: 'לא עדכני', description: 'המידע כבר לא רלוונטי' },
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!reason.trim()) return;

    setSubmitting(true);
    try {
      await api.createFlag(childId, targetType, targetId, flagType, reason, suggestedCorrection || null);
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
        <h2 className="text-lg font-medium text-gray-800 mb-2">סמן בעיה</h2>
        <p className="text-sm text-gray-500 mb-6">"{targetLabel}"</p>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Flag type selection */}
          <div>
            <label className="text-sm text-gray-600 block mb-3">סוג הבעיה:</label>
            <div className="space-y-2">
              {flagTypes.map((ft) => (
                <label
                  key={ft.value}
                  className={`flex items-start gap-3 p-3 rounded-xl border cursor-pointer transition ${
                    flagType === ft.value
                      ? 'border-red-300 bg-red-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <input
                    type="radio"
                    name="flagType"
                    value={ft.value}
                    checked={flagType === ft.value}
                    onChange={(e) => setFlagType(e.target.value)}
                    className="mt-1"
                  />
                  <div>
                    <span className="font-medium text-gray-700">{ft.label}</span>
                    <p className="text-xs text-gray-500">{ft.description}</p>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Reason */}
          <div>
            <label className="text-sm text-gray-600 block mb-2">הסבר:</label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="תאר את הבעיה..."
              className="w-full p-3 border border-gray-200 rounded-xl text-gray-800 placeholder:text-gray-300 h-24 resize-none"
              required
            />
          </div>

          {/* Suggested correction (optional) */}
          <div>
            <label className="text-sm text-gray-600 block mb-2">הצעה לתיקון (אופציונלי):</label>
            <textarea
              value={suggestedCorrection}
              onChange={(e) => setSuggestedCorrection(e.target.value)}
              placeholder="מה היית מציע במקום?"
              className="w-full p-3 border border-gray-200 rounded-xl text-gray-800 placeholder:text-gray-300 h-20 resize-none"
            />
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-gray-500 hover:text-gray-700">
              ביטול
            </button>
            <button
              type="submit"
              disabled={submitting || !reason.trim()}
              className="px-5 py-2 bg-red-500 text-white rounded-xl hover:bg-red-600 disabled:opacity-40"
            >
              {submitting ? 'שומר...' : 'שמור סימון'}
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

// Correction type translations
const CORRECTION_TYPE_HE = {
  domain_change: 'שינוי תחום',
  extraction_error: 'שגיאת חילוץ',
  missed_signal: 'אות שפוספס',
  hallucination: 'המצאה',
  evidence_reclassify: 'סיווג ראיה מחדש',
  timing_issue: 'בעיית תזמון',
  certainty_adjustment: 'התאמת ודאות',
};

const TARGET_TYPE_HE = {
  observation: 'תצפית',
  curiosity: 'סקרנות',
  hypothesis: 'השערה',
  evidence: 'ראיה',
  video: 'וידאו',
  response: 'תשובה',
};

const SEVERITY_HE = {
  low: 'נמוכה',
  medium: 'בינונית',
  high: 'גבוהה',
};

/**
 * Analytics View - Correction patterns and improvement metrics (plan section 11)
 */
function AnalyticsView({ childId }) {
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState(null);
  const [patterns, setPatterns] = useState(null);
  const [corrections, setCorrections] = useState(null);
  const [missedSignals, setMissedSignals] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadAnalytics();
  }, []);

  async function loadAnalytics() {
    setLoading(true);
    try {
      const [overviewData, patternsData, correctionsData, missedData] = await Promise.all([
        api.getDashboardAnalytics(),
        api.getCorrectionPatterns(1),
        api.getCorrectionAnalytics(),
        api.getMissedSignalAnalytics(),
      ]);
      setOverview(overviewData);
      setPatterns(patternsData);
      setCorrections(correctionsData);
      setMissedSignals(missedData);
    } catch (err) {
      console.error('Error loading analytics:', err);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-indigo-200 border-t-indigo-600" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-5xl mx-auto" dir="rtl">
      <h2 className="text-xl font-medium text-gray-800 mb-6">אנליטיקה</h2>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <SummaryCard
          value={overview?.total_children || 0}
          label="ילדים"
          color="indigo"
        />
        <SummaryCard
          value={corrections?.total || 0}
          label="תיקונים"
          color="purple"
        />
        <SummaryCard
          value={missedSignals?.total || 0}
          label="אותות שפוספסו"
          color="amber"
        />
        <SummaryCard
          value={overview?.total_unresolved_flags || 0}
          label="דגלים פתוחים"
          color="red"
        />
      </div>

      {/* Tab navigation */}
      <div className="flex gap-2 mb-6">
        {[
          { id: 'overview', label: '📊 סקירה' },
          { id: 'patterns', label: '🔍 דפוסים' },
          { id: 'corrections', label: '✏️ תיקונים' },
          { id: 'missed', label: '⚠️ אותות שפוספסו' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition ${
              activeTab === tab.id
                ? 'bg-indigo-100 text-indigo-700'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === 'overview' && (
        <OverviewTab overview={overview} corrections={corrections} missedSignals={missedSignals} />
      )}
      {activeTab === 'patterns' && (
        <PatternsTab patterns={patterns} />
      )}
      {activeTab === 'corrections' && (
        <CorrectionsTab corrections={corrections} />
      )}
      {activeTab === 'missed' && (
        <MissedSignalsTab missedSignals={missedSignals} />
      )}
    </div>
  );
}

function SummaryCard({ value, label, color = 'gray' }) {
  const colors = {
    gray: 'text-gray-800',
    indigo: 'text-indigo-600',
    purple: 'text-purple-600',
    amber: 'text-amber-600',
    red: 'text-red-600',
    emerald: 'text-emerald-600',
  };

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 text-center">
      <div className={`text-3xl font-bold mb-1 ${colors[color]}`}>{value}</div>
      <div className="text-sm text-gray-400">{label}</div>
    </div>
  );
}

function OverviewTab({ overview, corrections, missedSignals }) {
  return (
    <div className="space-y-6">
      {/* System stats */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
        <h3 className="text-lg font-medium text-gray-800 mb-4">📈 סטטיסטיקות מערכת</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <div className="text-2xl font-bold text-gray-800">{overview?.total_observations || 0}</div>
            <div className="text-sm text-gray-400">תצפיות</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-800">{overview?.total_curiosities || 0}</div>
            <div className="text-sm text-gray-400">סקרנויות</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-800">{overview?.total_patterns || 0}</div>
            <div className="text-sm text-gray-400">דפוסים</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-emerald-600">{overview?.children_with_crystal || 0}</div>
            <div className="text-sm text-gray-400">עם קריסטל</div>
          </div>
        </div>
      </div>

      {/* Correction breakdown */}
      {corrections && Object.keys(corrections.by_type || {}).length > 0 && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <h3 className="text-lg font-medium text-gray-800 mb-4">✏️ תיקונים לפי סוג</h3>
          <div className="space-y-2">
            {Object.entries(corrections.by_type || {}).map(([type, count]) => (
              <div key={type} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                <span className="text-gray-700">{CORRECTION_TYPE_HE[type] || type}</span>
                <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-lg font-medium">
                  {count}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Missed signals by domain */}
      {missedSignals && Object.keys(missedSignals.by_domain || {}).length > 0 && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <h3 className="text-lg font-medium text-gray-800 mb-4">⚠️ אותות שפוספסו לפי תחום</h3>
          <div className="space-y-2">
            {Object.entries(missedSignals.by_domain || {}).map(([domain, count]) => (
              <div key={domain} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                <span className="text-gray-700">{DOMAIN_HE[domain] || domain}</span>
                <span className="px-3 py-1 bg-amber-100 text-amber-700 rounded-lg font-medium">
                  {count}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {(!corrections?.total && !missedSignals?.total) && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-8 text-center">
          <BarChart3 className="w-12 h-12 text-gray-200 mx-auto mb-4" />
          <h3 className="text-gray-500 mb-2">אין נתוני תיקונים עדיין</h3>
          <p className="text-gray-400 text-sm">
            נתוני אנליטיקה יופיעו כאשר מומחים יתחילו לסקור ולתקן.
          </p>
        </div>
      )}
    </div>
  );
}

function PatternsTab({ patterns }) {
  if (!patterns || (patterns.correction_patterns?.length === 0 && patterns.missed_signal_patterns?.length === 0)) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-8 text-center">
        <BarChart3 className="w-12 h-12 text-gray-200 mx-auto mb-4" />
        <h3 className="text-gray-500 mb-2">לא זוהו דפוסים עדיין</h3>
        <p className="text-gray-400 text-sm">
          דפוסים יזוהו כאשר יצטברו תיקונים חוזרים.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Correction patterns */}
      {patterns.correction_patterns?.length > 0 && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <h3 className="text-lg font-medium text-gray-800 mb-4">
            🔍 דפוסי תיקונים ({patterns.correction_patterns.length})
          </h3>
          <div className="space-y-3">
            {patterns.correction_patterns.map((pattern, i) => (
              <PatternCard key={i} pattern={pattern} />
            ))}
          </div>
        </div>
      )}

      {/* Missed signal patterns */}
      {patterns.missed_signal_patterns?.length > 0 && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <h3 className="text-lg font-medium text-gray-800 mb-4">
            ⚠️ דפוסי אותות שפוספסו ({patterns.missed_signal_patterns.length})
          </h3>
          <div className="space-y-3">
            {patterns.missed_signal_patterns.map((pattern, i) => (
              <div key={i} className="p-4 bg-amber-50 rounded-xl border border-amber-100">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-amber-800">
                    {DOMAIN_HE[pattern.domain] || pattern.domain}
                  </span>
                  <span className="px-2 py-1 bg-amber-200 text-amber-800 rounded text-sm font-medium">
                    {pattern.count} מקרים
                  </span>
                </div>
                {pattern.examples?.length > 0 && (
                  <div className="text-sm text-amber-700">
                    דוגמה: {pattern.examples[0]}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function PatternCard({ pattern }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="p-4 bg-purple-50 rounded-xl border border-purple-100">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full text-right"
      >
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="font-medium text-purple-800">
              {CORRECTION_TYPE_HE[pattern.correction_type] || pattern.correction_type}
            </span>
            <span className="text-purple-600 text-sm">
              → {TARGET_TYPE_HE[pattern.target_type] || pattern.target_type}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-1 bg-purple-200 text-purple-800 rounded text-sm font-medium">
              {pattern.count} מקרים
            </span>
            {pattern.severity_score >= 2 && (
              <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs">
                חומרה גבוהה
              </span>
            )}
          </div>
        </div>
      </button>

      {expanded && pattern.examples?.length > 0 && (
        <div className="mt-3 pt-3 border-t border-purple-200 space-y-2">
          <div className="text-sm text-purple-600 font-medium">דוגמאות:</div>
          {pattern.examples.map((ex, i) => (
            <div key={i} className="p-2 bg-white rounded-lg text-sm text-gray-600">
              {ex.expert_reasoning || 'ללא הסבר'}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function CorrectionsTab({ corrections }) {
  if (!corrections || corrections.total === 0) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-8 text-center">
        <FileText className="w-12 h-12 text-gray-200 mx-auto mb-4" />
        <h3 className="text-gray-500 mb-2">אין תיקונים עדיין</h3>
        <p className="text-gray-400 text-sm">
          תיקונים יופיעו כאשר מומחים יסמנו שגיאות בתצפיות או בסקרנויות.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
          <h4 className="text-sm text-gray-500 mb-3">לפי חומרה</h4>
          <div className="space-y-2">
            {Object.entries(corrections.by_severity || {}).map(([sev, count]) => (
              <div key={sev} className="flex items-center justify-between">
                <span className={`text-sm ${
                  sev === 'high' ? 'text-red-600' :
                  sev === 'medium' ? 'text-amber-600' : 'text-gray-600'
                }`}>
                  {SEVERITY_HE[sev] || sev}
                </span>
                <span className="font-medium">{count}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
          <h4 className="text-sm text-gray-500 mb-3">לפי יעד</h4>
          <div className="space-y-2">
            {Object.entries(corrections.by_target_type || {}).map(([target, count]) => (
              <div key={target} className="flex items-center justify-between">
                <span className="text-sm text-gray-600">{TARGET_TYPE_HE[target] || target}</span>
                <span className="font-medium">{count}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
          <h4 className="text-sm text-gray-500 mb-3">מצב אימון</h4>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">ממתינים לאימון</span>
              <span className="font-medium text-amber-600">{corrections.unused_for_training || 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">שומשו באימון</span>
              <span className="font-medium text-emerald-600">
                {(corrections.total || 0) - (corrections.unused_for_training || 0)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent examples */}
      {corrections.recent_examples?.length > 0 && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <h3 className="text-lg font-medium text-gray-800 mb-4">תיקונים אחרונים</h3>
          <div className="space-y-3">
            {corrections.recent_examples.map((ex, i) => (
              <div key={i} className="p-4 bg-gray-50 rounded-xl">
                <div className="flex items-center gap-2 mb-2">
                  <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs">
                    {CORRECTION_TYPE_HE[ex.correction_type] || ex.correction_type}
                  </span>
                  <span className="px-2 py-0.5 bg-gray-200 text-gray-600 rounded text-xs">
                    {TARGET_TYPE_HE[ex.target_type] || ex.target_type}
                  </span>
                  <span className={`px-2 py-0.5 rounded text-xs ${
                    ex.severity === 'high' ? 'bg-red-100 text-red-700' :
                    ex.severity === 'medium' ? 'bg-amber-100 text-amber-700' :
                    'bg-gray-100 text-gray-600'
                  }`}>
                    {SEVERITY_HE[ex.severity] || ex.severity}
                  </span>
                </div>
                <p className="text-gray-700 text-sm">{ex.expert_reasoning}</p>
                <p className="text-gray-400 text-xs mt-2">
                  {ex.created_at && new Date(ex.created_at).toLocaleDateString('he-IL')}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function MissedSignalsTab({ missedSignals }) {
  if (!missedSignals || missedSignals.total === 0) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-8 text-center">
        <Eye className="w-12 h-12 text-gray-200 mx-auto mb-4" />
        <h3 className="text-gray-500 mb-2">אין אותות שפוספסו</h3>
        <p className="text-gray-400 text-sm">
          אותות שפוספסו יופיעו כאשר מומחים יזהו דברים שצ'יטה לא שמה לב אליהם.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* By signal type */}
      {Object.keys(missedSignals.by_signal_type || {}).length > 0 && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <h3 className="text-lg font-medium text-gray-800 mb-4">לפי סוג אות</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {Object.entries(missedSignals.by_signal_type || {}).map(([type, count]) => (
              <div key={type} className="p-3 bg-amber-50 rounded-xl text-center">
                <div className="text-2xl font-bold text-amber-600">{count}</div>
                <div className="text-sm text-amber-700">{type}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent examples */}
      {missedSignals.recent_examples?.length > 0 && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <h3 className="text-lg font-medium text-gray-800 mb-4">דוגמאות אחרונות</h3>
          <div className="space-y-3">
            {missedSignals.recent_examples.map((ex, i) => (
              <div key={i} className="p-4 bg-amber-50 rounded-xl border border-amber-100">
                <div className="flex items-center gap-2 mb-2">
                  <span className="px-2 py-0.5 bg-amber-200 text-amber-800 rounded text-xs">
                    {ex.signal_type}
                  </span>
                  {ex.domain && (
                    <span className="px-2 py-0.5 bg-gray-200 text-gray-600 rounded text-xs">
                      {DOMAIN_HE[ex.domain] || ex.domain}
                    </span>
                  )}
                </div>
                <p className="text-gray-800 text-sm mb-2">{ex.content}</p>
                {ex.why_important && (
                  <p className="text-amber-700 text-sm">
                    <span className="font-medium">למה חשוב:</span> {ex.why_important}
                  </p>
                )}
                <p className="text-gray-400 text-xs mt-2">
                  {ex.created_at && new Date(ex.created_at).toLocaleDateString('he-IL')}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// Video status translations
const VIDEO_STATUS_HE = {
  pending: 'ממתין',
  uploaded: 'הועלה',
  analyzed: 'נותח',
  validation_failed: 'נכשל',
  needs_confirmation: 'ממתין לאישור',
  acknowledged: 'אושר',
  rejected: 'נדחה',
};

// Video category translations
const VIDEO_CATEGORY_HE = {
  hypothesis_test: 'בדיקת השערה',
  pattern_exploration: 'חקירת דפוס',
  strength_baseline: 'בסיס חוזקות',
  baseline: 'בסיס',
  long_absence: 'היעדרות ארוכה',
  returning: 'חזרה',
};

/**
 * Videos View - Video gallery with analysis (plan 6.5, 9)
 * Supports filtering by hypothesis via URL query parameter
 */
function VideosView({ childId }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedVideo, setSelectedVideo] = useState(null);
  const [statusFilter, setStatusFilter] = useState(null);

  // Get hypothesis filter from URL
  const hypothesisFilter = searchParams.get('hypothesis');

  useEffect(() => {
    loadVideos();
  }, [childId, statusFilter]);

  async function loadVideos() {
    setLoading(true);
    try {
      const data = await api.getChildVideos(childId, statusFilter);
      setVideos(data.videos || []);
    } catch (err) {
      console.error('Error loading videos:', err);
    } finally {
      setLoading(false);
    }
  }

  // Clear hypothesis filter
  const clearHypothesisFilter = () => {
    searchParams.delete('hypothesis');
    setSearchParams(searchParams);
  };

  // Filter videos by hypothesis if filter is active
  const filteredVideos = hypothesisFilter
    ? videos.filter(v => v.target_hypothesis_focus === hypothesisFilter)
    : videos;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-violet-200 border-t-violet-600" />
      </div>
    );
  }

  if (videos.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center" dir="rtl">
        <Video className="w-12 h-12 text-gray-200 mb-4" />
        <h3 className="text-gray-400 text-lg mb-2">אין סרטונים עדיין</h3>
        <p className="text-gray-300 text-sm max-w-md">
          סרטונים יופיעו כאן כאשר ההורה יעלה סרטונים בעקבות המלצות וידאו.
        </p>
      </div>
    );
  }

  // Group filtered videos by status
  const analyzed = filteredVideos.filter(v => v.status === 'analyzed');
  const uploaded = filteredVideos.filter(v => v.status === 'uploaded');
  const pending = filteredVideos.filter(v => v.status === 'pending');
  const failed = filteredVideos.filter(v => v.status === 'validation_failed');

  return (
    <div className="p-6 max-w-5xl mx-auto" dir="rtl">
      {/* Hypothesis filter banner */}
      {hypothesisFilter && (
        <div className="mb-4 p-3 bg-purple-50 border border-purple-100 rounded-xl flex items-center justify-between">
          <div className="flex items-center gap-2 text-purple-700">
            <span className="text-lg">◆</span>
            <span className="text-sm">
              מציג סרטונים עבור השערה: <strong>"{hypothesisFilter}"</strong>
            </span>
          </div>
          <button
            onClick={clearHypothesisFilter}
            className="flex items-center gap-1 px-2 py-1 text-purple-600 hover:bg-purple-100 rounded-lg text-sm transition"
          >
            <X className="w-4 h-4" />
            הצג הכל
          </button>
        </div>
      )}

      {/* Empty state for filtered view */}
      {hypothesisFilter && filteredVideos.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <Video className="w-12 h-12 text-gray-200 mb-4" />
          <h3 className="text-gray-400 text-lg mb-2">אין סרטונים להשערה זו</h3>
          <p className="text-gray-300 text-sm max-w-md mb-4">
            עדיין לא הועלו סרטונים לבדיקת השערה זו.
          </p>
          <button
            onClick={clearHypothesisFilter}
            className="px-4 py-2 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 transition"
          >
            הצג את כל הסרטונים
          </button>
        </div>
      )}

      {/* Header with filter */}
      {filteredVideos.length > 0 && (
        <>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-medium text-gray-800">
              סרטונים ({filteredVideos.length}{hypothesisFilter ? ` מתוך ${videos.length}` : ''})
            </h2>
            <div className="flex items-center gap-2 text-sm">
              {analyzed.length > 0 && (
                <span className="px-2 py-1 bg-emerald-50 text-emerald-600 rounded-lg">
                  ✓ {analyzed.length} נותחו
                </span>
              )}
              {uploaded.length > 0 && (
                <span className="px-2 py-1 bg-violet-50 text-violet-600 rounded-lg">
                  ⬆ {uploaded.length} הועלו
                </span>
              )}
              {pending.length > 0 && (
                <span className="px-2 py-1 bg-gray-100 text-gray-500 rounded-lg">
                  ○ {pending.length} ממתינים
                </span>
              )}
            </div>
          </div>

          {/* Video grid or detail view */}
          {selectedVideo ? (
            <VideoAnalysisView
              video={selectedVideo}
              childId={childId}
              hypothesisFocus={hypothesisFilter}
              onBack={() => setSelectedVideo(null)}
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredVideos.map((video) => (
                <VideoCard
                  key={video.id}
                  video={video}
                  onClick={() => setSelectedVideo(video)}
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

/**
 * Video Card - Thumbnail card in gallery
 */
function VideoCard({ video, onClick }) {
  const statusColors = {
    pending: 'bg-gray-100 text-gray-600',
    uploaded: 'bg-violet-50 text-violet-600',
    analyzed: 'bg-emerald-50 text-emerald-600',
    validation_failed: 'bg-red-50 text-red-600',
    needs_confirmation: 'bg-amber-50 text-amber-600',
  };

  return (
    <button
      onClick={onClick}
      className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden text-right hover:border-violet-200 hover:shadow-md transition"
    >
      {/* Thumbnail placeholder */}
      <div className="aspect-video bg-gradient-to-br from-violet-100 to-purple-100 flex items-center justify-center">
        <Video className="w-12 h-12 text-violet-300" />
      </div>

      {/* Info */}
      <div className="p-4">
        <div className="flex items-start justify-between mb-2">
          <h3 className="font-medium text-gray-800 text-sm line-clamp-2">
            {video.title}
          </h3>
          <span className={`px-2 py-0.5 rounded text-xs flex-shrink-0 mr-2 ${statusColors[video.status] || 'bg-gray-100'}`}>
            {VIDEO_STATUS_HE[video.status] || video.status}
          </span>
        </div>

        {/* Category badge */}
        {video.category && video.category !== 'hypothesis_test' && (
          <p className="text-xs text-indigo-500 mb-1">
            {VIDEO_CATEGORY_HE[video.category] || video.category}
          </p>
        )}

        {/* Hypothesis link */}
        {video.target_hypothesis_focus && (
          <p className="text-xs text-purple-600 mb-2 line-clamp-1">
            ◆ {video.target_hypothesis_focus}
          </p>
        )}

        {/* Analysis stats */}
        {video.status === 'analyzed' && (
          <div className="flex items-center gap-3 text-xs text-gray-400">
            <span>📍 {video.observations?.length || 0} תצפיות</span>
            {video.strengths_observed?.length > 0 && (
              <span>💪 {video.strengths_observed.length} חוזקות</span>
            )}
          </div>
        )}

        {/* Upload date */}
        {video.uploaded_at && (
          <p className="text-xs text-gray-300 mt-2">
            הועלה: {new Date(video.uploaded_at).toLocaleDateString('he-IL')}
          </p>
        )}
      </div>
    </button>
  );
}

/**
 * Parse timestamp string (e.g., "0:30", "1:25", "00:01:30") to seconds
 */
function parseTimestamp(timestamp) {
  if (!timestamp) return 0;
  const parts = timestamp.split(':').map(Number);
  if (parts.length === 3) {
    // HH:MM:SS
    return parts[0] * 3600 + parts[1] * 60 + parts[2];
  } else if (parts.length === 2) {
    // MM:SS
    return parts[0] * 60 + parts[1];
  }
  return 0;
}

/**
 * Video Analysis View - Detailed view with player and observations (plan 6.5)
 * Now with clickable timestamps and expert feedback capabilities
 */
function VideoAnalysisView({ video, childId, hypothesisFocus, onBack }) {
  const videoRef = useRef(null);
  const [activeTab, setActiveTab] = useState('observations');
  const [currentTime, setCurrentTime] = useState(0);

  // Seek video to specific timestamp
  const seekToTimestamp = (timestamp) => {
    if (videoRef.current && timestamp) {
      const seconds = parseTimestamp(timestamp);
      videoRef.current.currentTime = seconds;
      videoRef.current.play();
    }
  };

  // Track current time for highlighting active observation
  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  return (
    <div className="space-y-6">
      {/* Back button */}
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-gray-500 hover:text-gray-700"
      >
        <ChevronLeft className="w-4 h-4" />
        חזרה לגלריה
      </button>

      {/* Video header */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-xl font-medium text-gray-800 mb-1">{video.title}</h2>
            {video.category && (
              <p className="text-indigo-500 text-sm mb-1">
                {VIDEO_CATEGORY_HE[video.category] || video.category}
              </p>
            )}
            {video.target_hypothesis_focus && (
              <p className="text-purple-600 text-sm">
                ◆ קשור להשערה: {video.target_hypothesis_focus}
              </p>
            )}
          </div>
          <span className={`px-3 py-1 rounded-lg text-sm ${
            video.status === 'analyzed' ? 'bg-emerald-50 text-emerald-600' :
            video.status === 'uploaded' ? 'bg-violet-50 text-violet-600' :
            'bg-gray-100 text-gray-600'
          }`}>
            {VIDEO_STATUS_HE[video.status] || video.status}
          </span>
        </div>

        {/* Video player with ref for seeking */}
        <div className="aspect-video bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl flex items-center justify-center mb-4 overflow-hidden">
          {video.video_path ? (
            <video
              ref={videoRef}
              src={`/uploads/${video.video_path.split('/').slice(-2).join('/')}`}
              controls
              onTimeUpdate={handleTimeUpdate}
              className="w-full h-full rounded-xl"
            />
          ) : (
            <div className="text-center">
              <Video className="w-16 h-16 text-gray-600 mx-auto mb-3" />
              <p className="text-gray-500">סרטון לא זמין</p>
            </div>
          )}
        </div>

        {/* Video meta */}
        <div className="flex items-center gap-4 text-sm text-gray-400">
          {video.duration_suggestion && (
            <span>⏱ {video.duration_suggestion}</span>
          )}
          {video.uploaded_at && (
            <span>📅 הועלה: {new Date(video.uploaded_at).toLocaleDateString('he-IL')}</span>
          )}
          {video.analyzed_at && (
            <span>✓ נותח: {new Date(video.analyzed_at).toLocaleDateString('he-IL')}</span>
          )}
        </div>
      </div>

      {/* Analysis tabs */}
      {video.status === 'analyzed' && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
          {/* Tab buttons */}
          <div className="flex border-b border-gray-100">
            {[
              { id: 'observations', label: `📍 תצפיות (${video.observations?.length || 0})` },
              { id: 'strengths', label: `💪 חוזקות (${video.strengths_observed?.length || 0})` },
              { id: 'insights', label: `💡 תובנות (${video.insights?.length || 0})` },
              { id: 'details', label: '🔧 פרטים' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 py-3 text-sm font-medium transition ${
                  activeTab === tab.id
                    ? 'text-violet-600 border-b-2 border-violet-500'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="p-6">
            {activeTab === 'observations' && (
              <VideoObservationsList
                observations={video.observations || []}
                onSeek={seekToTimestamp}
                currentTime={currentTime}
              />
            )}
            {activeTab === 'strengths' && (
              <div className="space-y-2">
                {video.strengths_observed?.length > 0 ? (
                  video.strengths_observed.map((strength, i) => (
                    <div key={i} className="p-3 bg-emerald-50 rounded-xl text-emerald-700">
                      💪 {strength}
                    </div>
                  ))
                ) : (
                  <p className="text-gray-400 text-center py-8">לא זוהו חוזקות</p>
                )}
              </div>
            )}
            {activeTab === 'insights' && (
              <div className="space-y-2">
                {video.insights?.length > 0 ? (
                  video.insights.map((insight, i) => (
                    <div key={i} className="p-3 bg-amber-50 rounded-xl text-amber-700">
                      💡 {insight}
                    </div>
                  ))
                ) : (
                  <p className="text-gray-400 text-center py-8">לא זוהו תובנות</p>
                )}
              </div>
            )}
            {activeTab === 'details' && (
              <div className="space-y-4">
                {video.what_to_film && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-600 mb-1">מה לצלם:</h4>
                    <p className="text-gray-800">{video.what_to_film}</p>
                  </div>
                )}
                {video.what_we_hope_to_learn && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-600 mb-1">מטרת הניתוח:</h4>
                    <p className="text-gray-800">{video.what_we_hope_to_learn}</p>
                  </div>
                )}
                {video.focus_points?.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-600 mb-2">נקודות מיקוד:</h4>
                    <ul className="list-disc list-inside text-gray-700 space-y-1">
                      {video.focus_points.map((point, i) => (
                        <li key={i}>{point}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {video.certainty_after !== null && (
                  <div className="p-3 bg-purple-50 rounded-xl">
                    <span className="text-sm text-purple-600">
                      ודאות ההשערה לאחר הניתוח: {Math.round((video.certainty_after || 0) * 100)}%
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Pending/uploaded state */}
      {video.status !== 'analyzed' && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          {video.status === 'uploaded' && (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-4 border-violet-200 border-t-violet-600 mx-auto mb-4" />
              <h3 className="text-gray-600 mb-2">הסרטון ממתין לניתוח</h3>
              <p className="text-gray-400 text-sm">הניתוח יתבצע אוטומטית</p>
            </div>
          )}
          {video.status === 'pending' && (
            <div className="text-center py-8">
              <Video className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-gray-600 mb-2">ממתין להעלאת סרטון</h3>
              {video.what_to_film && (
                <p className="text-gray-500 text-sm max-w-md mx-auto">
                  {video.what_to_film}
                </p>
              )}
            </div>
          )}
        </div>
      )}

      {/* Expert Feedback Panel */}
      <ExpertVideoFeedbackPanel
        video={video}
        childId={childId}
        hypothesisFocus={hypothesisFocus}
      />
    </div>
  );
}

/**
 * Expert Video Feedback Panel - Allows experts to give feedback on videos
 */
function ExpertVideoFeedbackPanel({ video, childId, hypothesisFocus }) {
  const navigate = useNavigate();
  const [feedback, setFeedback] = useState('');
  const [videoQuality, setVideoQuality] = useState(null); // 'adequate' | 'inadequate' | null
  const [showCertaintyModal, setShowCertaintyModal] = useState(false);
  const [newCertainty, setNewCertainty] = useState(0.5);
  const [certaintyReason, setCertaintyReason] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  // Only show for analyzed videos
  if (video.status !== 'analyzed') {
    return null;
  }

  const handleSubmitFeedback = async () => {
    if (!feedback.trim() && !videoQuality) return;

    setSubmitting(true);
    try {
      // In a real implementation, this would call an API to save the feedback
      console.log('Expert feedback:', {
        videoId: video.id,
        childId,
        hypothesisFocus,
        videoQuality,
        feedback,
      });
      setSubmitted(true);
    } catch (err) {
      console.error('Error submitting feedback:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdateCertainty = async () => {
    if (!hypothesisFocus || !certaintyReason.trim()) return;

    setSubmitting(true);
    try {
      await api.adjustCertainty(childId, hypothesisFocus, newCertainty, certaintyReason);
      setShowCertaintyModal(false);
      setSubmitted(true);
    } catch (err) {
      console.error('Error updating certainty:', err);
    } finally {
      setSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div className="bg-emerald-50 rounded-2xl border border-emerald-100 p-6 text-center">
        <CheckCircle className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
        <h3 className="text-emerald-700 font-medium mb-1">המשוב נשמר בהצלחה</h3>
        <p className="text-emerald-600 text-sm">תודה על הסקירה</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
      <h3 className="text-lg font-medium text-gray-800 mb-4 flex items-center gap-2">
        <Eye className="w-5 h-5 text-indigo-500" />
        משוב מומחה
      </h3>

      {/* Linked hypothesis info */}
      {video.target_hypothesis_focus && (
        <div className="mb-4 p-3 bg-purple-50 rounded-xl border border-purple-100">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-purple-600">◆</span>
              <span className="text-sm text-purple-700">
                קשור להשערה: <strong>{video.target_hypothesis_focus}</strong>
              </span>
            </div>
            <button
              onClick={() => setShowCertaintyModal(true)}
              className="flex items-center gap-1 px-2 py-1 bg-purple-100 text-purple-700 rounded-lg text-xs hover:bg-purple-200 transition"
            >
              <RefreshCw className="w-3 h-3" />
              עדכן ודאות
            </button>
          </div>
          {video.certainty_after !== null && (
            <p className="text-xs text-purple-500 mt-2">
              ודאות נוכחית: {Math.round((video.certainty_after || 0) * 100)}%
            </p>
          )}
        </div>
      )}

      {/* Video quality assessment */}
      <div className="mb-4">
        <p className="text-sm text-gray-600 mb-2">האם הסרטון מספק את המידע הנדרש?</p>
        <div className="flex gap-2">
          <button
            onClick={() => setVideoQuality('adequate')}
            className={`flex-1 py-2 px-4 rounded-xl text-sm font-medium transition ${
              videoQuality === 'adequate'
                ? 'bg-emerald-100 text-emerald-700 border-2 border-emerald-300'
                : 'bg-gray-100 text-gray-600 border-2 border-transparent hover:bg-gray-200'
            }`}
          >
            <CheckCircle className={`w-4 h-4 inline-block ml-1 ${videoQuality === 'adequate' ? 'text-emerald-600' : 'text-gray-400'}`} />
            מספק
          </button>
          <button
            onClick={() => setVideoQuality('inadequate')}
            className={`flex-1 py-2 px-4 rounded-xl text-sm font-medium transition ${
              videoQuality === 'inadequate'
                ? 'bg-amber-100 text-amber-700 border-2 border-amber-300'
                : 'bg-gray-100 text-gray-600 border-2 border-transparent hover:bg-gray-200'
            }`}
          >
            <AlertCircle className={`w-4 h-4 inline-block ml-1 ${videoQuality === 'inadequate' ? 'text-amber-600' : 'text-gray-400'}`} />
            לא מספק
          </button>
        </div>
      </div>

      {/* Feedback notes */}
      <div className="mb-4">
        <label className="text-sm text-gray-600 mb-1 block">הערות ומשוב:</label>
        <textarea
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          placeholder="הוסף הערות על איכות הסרטון, התצפיות, או הצעות לשיפור..."
          className="w-full p-3 border border-gray-200 rounded-xl text-sm resize-none h-24 focus:outline-none focus:border-indigo-300"
          dir="rtl"
        />
      </div>

      {/* Submit button */}
      <button
        onClick={handleSubmitFeedback}
        disabled={submitting || (!feedback.trim() && !videoQuality)}
        className="w-full py-2.5 bg-indigo-500 text-white rounded-xl font-medium hover:bg-indigo-600 transition disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {submitting ? 'שומר...' : 'שמור משוב'}
      </button>

      {/* Certainty update modal */}
      {showCertaintyModal && (
        <Modal onClose={() => setShowCertaintyModal(false)}>
          <div className="p-6">
            <h3 className="text-lg font-medium text-gray-800 mb-4">
              עדכון ודאות ההשערה מהוידאו
            </h3>

            <div className="mb-4 p-3 bg-purple-50 rounded-xl">
              <p className="text-sm text-purple-700">
                השערה: <strong>{video.target_hypothesis_focus}</strong>
              </p>
              {video.certainty_after !== null && (
                <p className="text-xs text-purple-500 mt-1">
                  ודאות נוכחית: {Math.round((video.certainty_after || 0) * 100)}%
                </p>
              )}
            </div>

            <div className="mb-4">
              <label className="text-sm text-gray-600 mb-2 block">ודאות חדשה:</label>
              <input
                type="range"
                min="0"
                max="100"
                value={newCertainty * 100}
                onChange={(e) => setNewCertainty(Number(e.target.value) / 100)}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>0%</span>
                <span className="text-indigo-600 font-medium">{Math.round(newCertainty * 100)}%</span>
                <span>100%</span>
              </div>
            </div>

            <div className="mb-4">
              <label className="text-sm text-gray-600 mb-1 block">סיבה לשינוי:</label>
              <textarea
                value={certaintyReason}
                onChange={(e) => setCertaintyReason(e.target.value)}
                placeholder="הסבר מדוע הוידאו משפיע על הודאות..."
                className="w-full p-3 border border-gray-200 rounded-xl text-sm resize-none h-20 focus:outline-none focus:border-indigo-300"
                dir="rtl"
              />
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => setShowCertaintyModal(false)}
                className="flex-1 py-2 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition"
              >
                ביטול
              </button>
              <button
                onClick={handleUpdateCertainty}
                disabled={submitting || !certaintyReason.trim()}
                className="flex-1 py-2 bg-purple-500 text-white rounded-xl hover:bg-purple-600 transition disabled:opacity-50"
              >
                {submitting ? 'שומר...' : 'עדכן ודאות'}
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}

/**
 * Video Observations List - Timeline of observations with clickable timestamps
 */
function VideoObservationsList({ observations, onSeek, currentTime }) {
  if (observations.length === 0) {
    return (
      <p className="text-gray-400 text-center py-8">לא זוהו תצפיות</p>
    );
  }

  // Check if an observation is currently playing
  const isActive = (obs) => {
    if (!currentTime || !obs.timestamp_start) return false;
    const startSec = parseTimestamp(obs.timestamp_start);
    const endSec = obs.timestamp_end ? parseTimestamp(obs.timestamp_end) : startSec + 10;
    return currentTime >= startSec && currentTime <= endSec;
  };

  return (
    <div className="space-y-3">
      {/* Instruction hint */}
      {onSeek && (
        <p className="text-xs text-gray-400 mb-2 flex items-center gap-1">
          <Play className="w-3 h-3" />
          לחץ על זמן כדי לדלג לנקודה בסרטון
        </p>
      )}

      {observations.map((obs, i) => {
        const active = isActive(obs);
        return (
          <div
            key={i}
            className={`p-4 rounded-xl border transition-all ${
              active
                ? 'bg-violet-50 border-violet-200 shadow-sm'
                : 'bg-gray-50 border-gray-100'
            }`}
          >
            <div className="flex items-start justify-between mb-2">
              {/* Clickable timestamp */}
              {onSeek && obs.timestamp_start ? (
                <button
                  onClick={() => onSeek(obs.timestamp_start)}
                  className="flex items-center gap-1 text-sm text-violet-600 hover:text-violet-800 hover:bg-violet-100 px-2 py-1 -mx-2 -my-1 rounded-lg transition group"
                >
                  <Play className={`w-3 h-3 ${active ? 'text-violet-600' : 'text-violet-400 group-hover:text-violet-600'}`} />
                  <span className="font-medium">{obs.timestamp_start}</span>
                  {obs.timestamp_end && obs.timestamp_end !== obs.timestamp_start && (
                    <span className="text-violet-400"> - {obs.timestamp_end}</span>
                  )}
                </button>
              ) : (
                <span className="text-sm text-violet-600">
                  📍 {obs.timestamp_start || '—'}
                  {obs.timestamp_end && obs.timestamp_end !== obs.timestamp_start && (
                    <span> - {obs.timestamp_end}</span>
                  )}
                </span>
              )}
              {obs.domain && (
                <span className="px-2 py-0.5 bg-gray-200 text-gray-600 rounded text-xs">
                  {DOMAIN_HE[obs.domain] || obs.domain}
                </span>
              )}
            </div>
            <p className="text-gray-700">{obs.content}</p>
            {obs.effect && obs.effect !== 'neutral' && (
              <span className={`mt-2 inline-block px-2 py-0.5 rounded text-xs ${
                obs.effect === 'supports' ? 'bg-emerald-100 text-emerald-700' :
                obs.effect === 'contradicts' ? 'bg-red-100 text-red-700' :
                'bg-blue-100 text-blue-700'
              }`}>
                {EFFECT_HE[obs.effect] || obs.effect}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}
