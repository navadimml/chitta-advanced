import React, { useState } from 'react';
import {
  Lightbulb,
  HelpCircle,
  FlaskConical,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Flag,
  Plus,
  Check,
  X,
  AlertCircle,
  Video,
} from 'lucide-react';

import { api } from '../../api/client';

/**
 * Curiosity Explorer Component
 *
 * Displays all curiosities (perpetual + dynamic) with:
 * - Pull and certainty visualization
 * - Evidence trail
 * - Actions: adjust certainty, add evidence, flag
 */
export default function CuriosityExplorer({ childId, curiosities, onRefresh }) {
  const perpetual = curiosities?.perpetual || [];
  const dynamic = curiosities?.dynamic || [];

  return (
    <div className="p-8 space-y-8">
      {/* Perpetual Curiosities */}
      <section>
        <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
          <Lightbulb className="w-5 h-5 text-amber-500" />
          Perpetual Curiosities ({perpetual.length})
        </h2>
        <p className="text-sm text-gray-500 mb-4">
          Always-active curiosities that guide exploration
        </p>
        <div className="space-y-3">
          {perpetual.map((c, i) => (
            <CuriosityCard
              key={i}
              curiosity={c}
              childId={childId}
              onRefresh={onRefresh}
            />
          ))}
        </div>
      </section>

      {/* Dynamic Curiosities */}
      <section>
        <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-purple-500" />
          Dynamic Curiosities ({dynamic.length})
        </h2>
        <p className="text-sm text-gray-500 mb-4">
          Spawned from conversation and evidence
        </p>
        {dynamic.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8 text-center text-gray-500">
            No dynamic curiosities yet
          </div>
        ) : (
          <div className="space-y-3">
            {dynamic.map((c, i) => (
              <CuriosityCard
                key={i}
                curiosity={c}
                childId={childId}
                onRefresh={onRefresh}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

/**
 * Curiosity Card Component
 */
function CuriosityCard({ curiosity, childId, onRefresh }) {
  const [expanded, setExpanded] = useState(false);
  const [showAdjust, setShowAdjust] = useState(false);
  const [showAddEvidence, setShowAddEvidence] = useState(false);
  const [showFlag, setShowFlag] = useState(false);

  const typeIcon = {
    discovery: <Lightbulb className="w-4 h-4" />,
    question: <HelpCircle className="w-4 h-4" />,
    hypothesis: <FlaskConical className="w-4 h-4" />,
    pattern: <Sparkles className="w-4 h-4" />,
  };

  const typeColor = {
    discovery: 'text-amber-600 bg-amber-50',
    question: 'text-blue-600 bg-blue-50',
    hypothesis: 'text-purple-600 bg-purple-50',
    pattern: 'text-emerald-600 bg-emerald-50',
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition"
      >
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <span className={`flex items-center gap-1.5 px-2 py-1 rounded ${typeColor[curiosity.type] || 'text-gray-600 bg-gray-50'}`}>
              {typeIcon[curiosity.type]}
              {curiosity.type}
            </span>
            {curiosity.is_perpetual && (
              <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">
                perpetual
              </span>
            )}
            {curiosity.domain && (
              <span className="text-xs px-2 py-0.5 bg-indigo-50 text-indigo-600 rounded">
                {curiosity.domain}
              </span>
            )}
          </div>
          <p className="mt-2 text-gray-900 font-medium" dir="rtl">
            {curiosity.focus}
          </p>
          {curiosity.theory && (
            <p className="mt-1 text-sm text-gray-500" dir="rtl">
              Theory: {curiosity.theory}
            </p>
          )}
        </div>

        {/* Pull & Certainty Bars */}
        <div className="flex items-center gap-6 ml-4">
          <div className="w-24">
            <div className="text-xs text-gray-500 mb-1">Pull: {(curiosity.pull * 100).toFixed(0)}%</div>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-amber-500 rounded-full transition-all"
                style={{ width: `${curiosity.pull * 100}%` }}
              />
            </div>
          </div>
          <div className="w-24">
            <div className="text-xs text-gray-500 mb-1">Certainty: {(curiosity.certainty * 100).toFixed(0)}%</div>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-emerald-500 rounded-full transition-all"
                style={{ width: `${curiosity.certainty * 100}%` }}
              />
            </div>
          </div>
          {expanded ? (
            <ChevronUp className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-400" />
          )}
        </div>
      </button>

      {/* Expanded Content */}
      {expanded && (
        <div className="border-t border-gray-100 p-4 bg-gray-50">
          {/* Status Info */}
          <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
            <span>Status: {curiosity.status}</span>
            {curiosity.times_explored > 0 && (
              <span>Explored: {curiosity.times_explored} times</span>
            )}
            {curiosity.last_activated && (
              <span>Last active: {new Date(curiosity.last_activated).toLocaleDateString()}</span>
            )}
          </div>

          {/* Evidence Trail */}
          {curiosity.evidence?.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">
                Evidence ({curiosity.evidence.length})
              </h4>
              <div className="space-y-2">
                {curiosity.evidence.map((e, i) => (
                  <div
                    key={i}
                    className={`p-3 rounded-lg text-sm ${
                      e.effect === 'supports'
                        ? 'bg-emerald-50 border border-emerald-100'
                        : e.effect === 'contradicts'
                        ? 'bg-red-50 border border-red-100'
                        : 'bg-amber-50 border border-amber-100'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className={`text-xs font-medium ${
                        e.effect === 'supports'
                          ? 'text-emerald-700'
                          : e.effect === 'contradicts'
                          ? 'text-red-700'
                          : 'text-amber-700'
                      }`}>
                        {e.effect}
                      </span>
                      <span className="text-xs text-gray-500">
                        {e.source} | {e.timestamp ? new Date(e.timestamp).toLocaleDateString() : 'N/A'}
                      </span>
                    </div>
                    <p className="text-gray-700" dir="rtl">{e.content}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Video Recommendation (for hypotheses) */}
          {curiosity.video_appropriate && (
            <div className="mb-4 p-3 bg-violet-50 border border-violet-100 rounded-lg">
              <div className="flex items-center gap-2 text-violet-700 font-medium text-sm mb-2">
                <Video className="w-4 h-4" />
                Video Recommendation
              </div>
              {curiosity.video_value && (
                <div className="text-sm mb-1">
                  <span className="text-violet-600 font-medium">Type: </span>
                  <span className="px-2 py-0.5 bg-violet-100 text-violet-700 rounded capitalize">
                    {curiosity.video_value}
                  </span>
                </div>
              )}
              {curiosity.video_value_reason && (
                <p className="text-sm text-violet-600" dir="rtl">
                  {curiosity.video_value_reason}
                </p>
              )}
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center gap-2 pt-2 border-t border-gray-200">
            <button
              onClick={() => setShowAdjust(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition"
            >
              Adjust Certainty
            </button>
            <button
              onClick={() => setShowAddEvidence(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition"
            >
              <Plus className="w-4 h-4" />
              Add Evidence
            </button>
            <button
              onClick={() => setShowFlag(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-red-600 bg-white border border-red-200 rounded-lg hover:bg-red-50 transition"
            >
              <Flag className="w-4 h-4" />
              Flag Issue
            </button>
          </div>

          {/* Adjust Certainty Modal */}
          {showAdjust && (
            <AdjustCertaintyModal
              childId={childId}
              curiosityFocus={curiosity.focus}
              currentCertainty={curiosity.certainty}
              onClose={() => setShowAdjust(false)}
              onSuccess={() => {
                setShowAdjust(false);
                onRefresh?.();
              }}
            />
          )}

          {/* Add Evidence Modal */}
          {showAddEvidence && (
            <AddEvidenceModal
              childId={childId}
              curiosityFocus={curiosity.focus}
              onClose={() => setShowAddEvidence(false)}
              onSuccess={() => {
                setShowAddEvidence(false);
                onRefresh?.();
              }}
            />
          )}

          {/* Flag Modal */}
          {showFlag && (
            <FlagModal
              childId={childId}
              targetType="curiosity"
              targetId={curiosity.focus}
              onClose={() => setShowFlag(false)}
              onSuccess={() => {
                setShowFlag(false);
                onRefresh?.();
              }}
            />
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Adjust Certainty Modal
 */
function AdjustCertaintyModal({ childId, curiosityFocus, currentCertainty, onClose, onSuccess }) {
  const [certainty, setCertainty] = useState(currentCertainty);
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!reason.trim()) {
      setError('Reason is required');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await api.adjustCertainty(childId, curiosityFocus, certainty, reason);
      onSuccess();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6" onClick={e => e.stopPropagation()}>
        <h3 className="text-lg font-bold text-gray-900 mb-4">Adjust Certainty</h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              New Certainty: {(certainty * 100).toFixed(0)}%
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={certainty}
              onChange={e => setCertainty(parseFloat(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500">
              <span>0%</span>
              <span>Current: {(currentCertainty * 100).toFixed(0)}%</span>
              <span>100%</span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Reason for adjustment *
            </label>
            <textarea
              value={reason}
              onChange={e => setReason(e.target.value)}
              placeholder="Why are you adjusting the certainty?"
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
              rows={3}
            />
          </div>

          {error && (
            <div className="text-red-600 text-sm">{error}</div>
          )}

          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition disabled:opacity-50"
            >
              {loading ? 'Saving...' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

/**
 * Add Evidence Modal
 */
function AddEvidenceModal({ childId, curiosityFocus, onClose, onSuccess }) {
  const [content, setContent] = useState('');
  const [effect, setEffect] = useState('supports');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!content.trim()) {
      setError('Evidence content is required');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await api.addExpertEvidence(childId, curiosityFocus, content, effect);
      onSuccess();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6" onClick={e => e.stopPropagation()}>
        <h3 className="text-lg font-bold text-gray-900 mb-4">Add Expert Evidence</h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Effect on certainty
            </label>
            <div className="flex gap-2">
              {['supports', 'contradicts', 'transforms'].map(e => (
                <button
                  key={e}
                  type="button"
                  onClick={() => setEffect(e)}
                  className={`flex-1 px-3 py-2 rounded-lg border transition ${
                    effect === e
                      ? e === 'supports'
                        ? 'bg-emerald-50 border-emerald-300 text-emerald-700'
                        : e === 'contradicts'
                        ? 'bg-red-50 border-red-300 text-red-700'
                        : 'bg-amber-50 border-amber-300 text-amber-700'
                      : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  {e}
                </button>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {effect === 'supports' && '+0.1 to certainty'}
              {effect === 'contradicts' && '-0.15 to certainty'}
              {effect === 'transforms' && 'Resets certainty to 0.4'}
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Evidence content *
            </label>
            <textarea
              value={content}
              onChange={e => setContent(e.target.value)}
              placeholder="Describe the evidence..."
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
              rows={4}
              dir="rtl"
            />
          </div>

          {error && (
            <div className="text-red-600 text-sm">{error}</div>
          )}

          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition disabled:opacity-50"
            >
              {loading ? 'Adding...' : 'Add Evidence'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

/**
 * Flag Modal
 */
function FlagModal({ childId, targetType, targetId, onClose, onSuccess }) {
  const [flagType, setFlagType] = useState('incorrect');
  const [reason, setReason] = useState('');
  const [suggestedCorrection, setSuggestedCorrection] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!reason.trim()) {
      setError('Reason is required');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await api.createFlag(childId, targetType, targetId, flagType, reason, suggestedCorrection || null);
      onSuccess();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6" onClick={e => e.stopPropagation()}>
        <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-red-600" />
          Flag Issue
        </h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Flag type
            </label>
            <div className="flex gap-2">
              {['incorrect', 'uncertain', 'needs_review'].map(t => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setFlagType(t)}
                  className={`flex-1 px-3 py-2 rounded-lg border transition ${
                    flagType === t
                      ? 'bg-red-50 border-red-300 text-red-700'
                      : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  {t.replace('_', ' ')}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Reason *
            </label>
            <textarea
              value={reason}
              onChange={e => setReason(e.target.value)}
              placeholder="Why is this flagged?"
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
              rows={3}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Suggested correction (optional)
            </label>
            <textarea
              value={suggestedCorrection}
              onChange={e => setSuggestedCorrection(e.target.value)}
              placeholder="What should it be instead?"
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
              rows={2}
            />
          </div>

          {error && (
            <div className="text-red-600 text-sm">{error}</div>
          )}

          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition disabled:opacity-50"
            >
              {loading ? 'Flagging...' : 'Create Flag'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
