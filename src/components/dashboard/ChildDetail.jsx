import React, { useState, useEffect } from 'react';
import { useParams, NavLink, Routes, Route, useNavigate } from 'react-router-dom';
import {
  ChevronLeft,
  User,
  Lightbulb,
  Eye,
  Sparkles,
  Clock,
  MessageSquare,
  FileText,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';

import { api } from '../../api/client';
import CuriosityExplorer from './CuriosityExplorer';
import CognitiveTimeline from './CognitiveTimeline';

/**
 * Child Detail Component
 *
 * Main container for viewing all internal state of a single child.
 * Provides tabbed navigation to different views.
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
      <div className="p-8 flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          Error loading child: {error}
        </div>
        <button
          onClick={() => navigate('/dashboard/children')}
          className="mt-4 flex items-center gap-2 text-indigo-600 hover:text-indigo-700"
        >
          <ChevronLeft className="w-4 h-4" />
          Back to Children
        </button>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-8 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/dashboard/children')}
              className="p-2 hover:bg-gray-100 rounded-lg transition"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white font-bold">
                {child?.child_name ? child.child_name[0] : '?'}
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900" dir="rtl">
                  {child?.child_name || 'Unnamed Child'}
                </h1>
                <div className="text-sm text-gray-500">
                  ID: {childId}
                  {child?.child_gender && (
                    <span className="ml-2">Gender: {child.child_gender}</span>
                  )}
                </div>
              </div>
            </div>
          </div>
          <button
            onClick={loadChild}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>

        {/* Quick Stats */}
        <div className="flex items-center gap-4 mt-4">
          <QuickStat
            icon={<Eye className="w-4 h-4" />}
            value={child?.understanding?.observations?.length || 0}
            label="Observations"
          />
          <QuickStat
            icon={<Lightbulb className="w-4 h-4" />}
            value={
              (child?.curiosities?.perpetual?.length || 0) +
              (child?.curiosities?.dynamic?.length || 0)
            }
            label="Curiosities"
          />
          <QuickStat
            icon={<Sparkles className="w-4 h-4" />}
            value={child?.understanding?.patterns?.length || 0}
            label="Patterns"
          />
          <QuickStat
            icon={<MessageSquare className="w-4 h-4" />}
            value={child?.session_history_length || 0}
            label="Messages"
          />
          {child?.feedback?.unresolved_flags_count > 0 && (
            <QuickStat
              icon={<AlertCircle className="w-4 h-4" />}
              value={child.feedback.unresolved_flags_count}
              label="Flags"
              alert
            />
          )}
        </div>

        {/* Tab Navigation */}
        <nav className="flex items-center gap-1 mt-4 -mb-px">
          <TabLink to="" end>
            <Lightbulb className="w-4 h-4" />
            Curiosities
          </TabLink>
          <TabLink to="understanding">
            <Eye className="w-4 h-4" />
            Understanding
          </TabLink>
          <TabLink to="crystal">
            <Sparkles className="w-4 h-4" />
            Crystal
          </TabLink>
          <TabLink to="timeline">
            <Clock className="w-4 h-4" />
            Timeline
          </TabLink>
          <TabLink to="conversation">
            <MessageSquare className="w-4 h-4" />
            Conversation
          </TabLink>
          <TabLink to="notes">
            <FileText className="w-4 h-4" />
            Notes & Flags
          </TabLink>
        </nav>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-auto bg-gray-50">
        <Routes>
          <Route
            index
            element={
              <CuriosityExplorer
                childId={childId}
                curiosities={child?.curiosities}
                onRefresh={loadChild}
              />
            }
          />
          <Route
            path="understanding"
            element={<UnderstandingView child={child} />}
          />
          <Route
            path="crystal"
            element={<CrystalView crystal={child?.crystal} />}
          />
          <Route
            path="timeline"
            element={<CognitiveTimeline childId={childId} />}
          />
          <Route
            path="conversation"
            element={<ConversationPlaceholder />}
          />
          <Route
            path="notes"
            element={<NotesPlaceholder childId={childId} feedback={child?.feedback} />}
          />
        </Routes>
      </div>
    </div>
  );
}

/**
 * Quick Stat Component
 */
function QuickStat({ icon, value, label, alert = false }) {
  return (
    <div
      className={`flex items-center gap-2 px-3 py-1.5 rounded-lg ${
        alert ? 'bg-red-50 text-red-700' : 'bg-gray-100 text-gray-700'
      }`}
    >
      {icon}
      <span className="font-medium">{value}</span>
      <span className="text-sm opacity-70">{label}</span>
    </div>
  );
}

/**
 * Tab Link Component
 */
function TabLink({ to, children, end = false }) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        `flex items-center gap-2 px-4 py-2 border-b-2 transition ${
          isActive
            ? 'border-indigo-600 text-indigo-600'
            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
        }`
      }
    >
      {children}
    </NavLink>
  );
}

/**
 * Understanding View
 */
function UnderstandingView({ child }) {
  if (!child?.understanding) {
    return (
      <div className="p-8 text-center text-gray-500">
        No understanding data available
      </div>
    );
  }

  const { observations, patterns, milestones } = child.understanding;

  return (
    <div className="p-8 space-y-8">
      {/* Observations by Domain */}
      <section>
        <h2 className="text-lg font-bold text-gray-900 mb-4">
          Observations ({observations?.length || 0})
        </h2>
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 divide-y divide-gray-100">
          {observations?.length === 0 ? (
            <div className="p-6 text-center text-gray-500">No observations yet</div>
          ) : (
            observations?.map((obs, i) => (
              <div key={i} className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1" dir="rtl">
                    <p className="text-gray-900">{obs.content}</p>
                    <div className="flex items-center gap-3 mt-2 text-sm text-gray-500">
                      <span className="px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded">
                        {obs.domain}
                      </span>
                      <span>Confidence: {(obs.confidence * 100).toFixed(0)}%</span>
                      {obs.source && <span>Source: {obs.source}</span>}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </section>

      {/* Patterns */}
      <section>
        <h2 className="text-lg font-bold text-gray-900 mb-4">
          Patterns ({patterns?.length || 0})
        </h2>
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 divide-y divide-gray-100">
          {patterns?.length === 0 ? (
            <div className="p-6 text-center text-gray-500">No patterns detected yet</div>
          ) : (
            patterns?.map((p, i) => (
              <div key={i} className="p-4">
                <p className="text-gray-900" dir="rtl">{p.description}</p>
                <div className="flex items-center gap-3 mt-2 text-sm text-gray-500">
                  <span>Domains: {p.domains?.join(', ')}</span>
                  <span>Confidence: {(p.confidence * 100).toFixed(0)}%</span>
                </div>
              </div>
            ))
          )}
        </div>
      </section>

      {/* Milestones */}
      <section>
        <h2 className="text-lg font-bold text-gray-900 mb-4">
          Milestones ({milestones?.length || 0})
        </h2>
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 divide-y divide-gray-100">
          {milestones?.length === 0 ? (
            <div className="p-6 text-center text-gray-500">No milestones recorded yet</div>
          ) : (
            milestones?.map((m, i) => (
              <div key={i} className="p-4">
                <p className="text-gray-900" dir="rtl">{m.description}</p>
                <div className="flex items-center gap-3 mt-2 text-sm text-gray-500">
                  <span className="px-2 py-0.5 bg-purple-50 text-purple-700 rounded">
                    {m.type}
                  </span>
                  <span>{m.domain}</span>
                  {m.age_months && (
                    <span>
                      At age: {Math.floor(m.age_months / 12)}y {Math.round(m.age_months % 12)}m
                    </span>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  );
}

/**
 * Crystal View
 */
function CrystalView({ crystal }) {
  if (!crystal) {
    return (
      <div className="p-8 text-center text-gray-500">
        <Sparkles className="w-12 h-12 mx-auto mb-4 text-gray-300" />
        <p>No crystal generated yet</p>
        <p className="text-sm mt-2">Crystal forms when understanding reaches sufficient depth</p>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6">
      {/* Essence Narrative */}
      <section className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-bold text-gray-900 mb-4">Essence Narrative</h2>
        <p className="text-gray-700 text-lg leading-relaxed" dir="rtl">
          {crystal.essence_narrative || 'No essence narrative yet'}
        </p>
      </section>

      {/* Temperament & Qualities */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <section className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Temperament</h2>
          <div className="flex flex-wrap gap-2">
            {crystal.temperament?.map((t, i) => (
              <span
                key={i}
                className="px-3 py-1.5 bg-amber-50 text-amber-700 rounded-full text-sm"
                dir="rtl"
              >
                {t}
              </span>
            )) || <span className="text-gray-500">Not identified yet</span>}
          </div>
        </section>

        <section className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Core Qualities</h2>
          <div className="flex flex-wrap gap-2">
            {crystal.core_qualities?.map((q, i) => (
              <span
                key={i}
                className="px-3 py-1.5 bg-emerald-50 text-emerald-700 rounded-full text-sm"
                dir="rtl"
              >
                {q}
              </span>
            )) || <span className="text-gray-500">Not identified yet</span>}
          </div>
        </section>
      </div>

      {/* Patterns in Crystal */}
      <section className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-bold text-gray-900 mb-4">
          Synthesized Patterns ({crystal.patterns?.length || 0})
        </h2>
        {crystal.patterns?.length === 0 ? (
          <p className="text-gray-500">No patterns in crystal yet</p>
        ) : (
          <div className="space-y-3">
            {crystal.patterns?.map((p, i) => (
              <div
                key={i}
                className="p-4 bg-gray-50 rounded-lg border border-gray-100"
              >
                <p className="text-gray-900" dir="rtl">{p.description}</p>
                <div className="flex items-center gap-3 mt-2 text-sm text-gray-500">
                  <span>Domains: {p.domains?.join(', ')}</span>
                  <span>Confidence: {(p.confidence * 100).toFixed(0)}%</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Metadata */}
      <div className="text-sm text-gray-500 text-center">
        Version {crystal.version || 1}
        {crystal.generated_at && (
          <span className="ml-2">
            | Generated: {new Date(crystal.generated_at).toLocaleString()}
          </span>
        )}
      </div>
    </div>
  );
}

/**
 * Placeholder components for routes not yet fully implemented
 */
function ConversationPlaceholder() {
  return (
    <div className="p-8 text-center text-gray-500">
      <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-300" />
      <p>Conversation Replay coming soon...</p>
    </div>
  );
}

function NotesPlaceholder({ childId, feedback }) {
  return (
    <div className="p-8">
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
        <h2 className="text-lg font-bold text-gray-900 mb-4">Feedback Summary</h2>
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">
              {feedback?.notes_count || 0}
            </div>
            <div className="text-sm text-gray-500">Clinical Notes</div>
          </div>
          <div className="text-center p-4 bg-red-50 rounded-lg">
            <div className="text-2xl font-bold text-red-700">
              {feedback?.unresolved_flags_count || 0}
            </div>
            <div className="text-sm text-gray-500">Unresolved Flags</div>
          </div>
          <div className="text-center p-4 bg-amber-50 rounded-lg">
            <div className="text-2xl font-bold text-amber-700">
              {feedback?.recent_adjustments?.length || 0}
            </div>
            <div className="text-sm text-gray-500">Recent Adjustments</div>
          </div>
        </div>
      </div>

      <div className="text-center text-gray-500">
        <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300" />
        <p>Full Notes & Flags interface coming soon...</p>
      </div>
    </div>
  );
}
