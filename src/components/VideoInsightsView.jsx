import React from 'react';
import {
  X,
  Sparkles,
  Lightbulb,
  Star,
  TrendingUp,
  CheckCircle,
  AlertCircle,
  HelpCircle,
  Video,
  Clock,
  AlertTriangle,
} from 'lucide-react';

/**
 * Video Insights Deep View
 *
 * Beautiful, full-screen view for video analysis insights.
 * Shows what was learned from the analyzed videos in a warm, parent-friendly way.
 */
export default function VideoInsightsView({ insights, onClose }) {
  if (!insights) return null;

  const { focus, insights: scenarioInsights, total_analyzed } = insights;

  // Verdict to icon and color mapping
  const verdictConfig = {
    supports: {
      icon: CheckCircle,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-50',
      borderColor: 'border-emerald-200',
      label: 'תומך',
    },
    contradicts: {
      icon: AlertCircle,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
      borderColor: 'border-orange-200',
      label: 'מראה תמונה שונה',
    },
    inconclusive: {
      icon: HelpCircle,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200',
      label: 'צריך עוד מידע',
    },
  };

  // Confidence level to stars
  const confidenceStars = (level) => {
    const levels = { low: 1, medium: 2, high: 3 };
    const count = levels[level] || 2;
    return Array(count).fill(0);
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 animate-backdropIn">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" />

      {/* Modal Panel */}
      <div
        className="relative bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden animate-panelUp"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-pink-500 to-rose-500 text-white p-6">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-2xl font-bold mb-2 flex items-center gap-3">
                <Sparkles className="w-7 h-7" />
                תובנות מניתוח הסרטונים
              </h2>
              <p className="text-pink-100">
                {focus}
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/20 rounded-full transition-all duration-200"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Quick Stats */}
          <div className="mt-4 flex gap-4 text-sm">
            <div className="flex items-center gap-2 bg-white/20 rounded-lg px-3 py-2">
              <Video className="w-4 h-4" />
              <span>{total_analyzed} סרטונים נותחו</span>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="overflow-y-auto max-h-[calc(90vh-200px)] p-6 space-y-6">
          {scenarioInsights && scenarioInsights.length > 0 ? (
            scenarioInsights.map((scenario, idx) => {
              const verdict = verdictConfig[scenario.verdict] || verdictConfig.inconclusive;
              const VerdictIcon = verdict.icon;

              return (
                <div
                  key={scenario.scenario_id || idx}
                  className={`
                    rounded-2xl border ${verdict.borderColor} ${verdict.bgColor}
                    overflow-hidden transition-all duration-300
                  `}
                >
                  {/* Scenario Header */}
                  <div className="p-4 bg-white/50 border-b border-inherit">
                    <div className="flex items-center justify-between flex-wrap gap-2">
                      <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                        <Video className="w-5 h-5 text-gray-600" />
                        {scenario.title}
                      </h3>
                      <div className={`flex items-center gap-2 px-3 py-1 rounded-full ${verdict.bgColor}`}>
                        <VerdictIcon className={`w-4 h-4 ${verdict.color}`} />
                        <span className={`text-sm font-medium ${verdict.color}`}>
                          {verdict.label}
                        </span>
                        {scenario.confidence_level && (
                          <span className="flex gap-0.5">
                            {confidenceStars(scenario.confidence_level).map((_, i) => (
                              <Star key={i} className={`w-3 h-3 ${verdict.color} fill-current`} />
                            ))}
                          </span>
                        )}
                      </div>
                    </div>
                    {scenario.analyzed_at && (
                      <p className="text-xs text-gray-500 mt-1 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        נותח: {new Date(scenario.analyzed_at).toLocaleDateString('he-IL')}
                      </p>
                    )}
                  </div>

                  {/* Video Validation Warning */}
                  {scenario.video_validation && !scenario.video_validation.is_usable && (
                    <div className="p-4 bg-amber-50 border-b border-amber-200">
                      <div className="flex items-start gap-3">
                        <AlertTriangle className="w-6 h-6 text-amber-600 flex-shrink-0 mt-0.5" />
                        <div>
                          <h4 className="font-semibold text-amber-800 mb-1">
                            הסרטון לא תואם לבקשה
                          </h4>
                          {scenario.video_validation.what_video_shows && (
                            <p className="text-amber-700 text-sm mb-2">
                              <span className="font-medium">מה שצולם: </span>
                              {scenario.video_validation.what_video_shows}
                            </p>
                          )}
                          {scenario.video_validation.validation_issues?.length > 0 && (
                            <ul className="text-sm text-amber-700 space-y-1">
                              {scenario.video_validation.validation_issues.map((issue, i) => (
                                <li key={i} className="flex items-start gap-2">
                                  <span className="text-amber-500">•</span>
                                  {issue}
                                </li>
                              ))}
                            </ul>
                          )}
                          <p className="text-amber-600 text-xs mt-2">
                            מומלץ להעלות סרטון חדש שמתאים להנחיות המקוריות
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Insights Section */}
                  {scenario.insights_for_parent && scenario.insights_for_parent.length > 0 && (
                    <div className="p-4">
                      <div className="flex items-center gap-2 mb-3">
                        <Lightbulb className="w-5 h-5 text-amber-500" />
                        <h4 className="font-semibold text-gray-700">מה למדנו</h4>
                      </div>
                      <ul className="space-y-2">
                        {scenario.insights_for_parent.map((insight, i) => (
                          <li
                            key={i}
                            className="flex items-start gap-3 bg-white/70 rounded-lg p-3 shadow-sm"
                          >
                            <span className="w-6 h-6 rounded-full bg-amber-100 text-amber-600 flex items-center justify-center text-sm font-bold flex-shrink-0">
                              {i + 1}
                            </span>
                            <span className="text-gray-700 leading-relaxed">{insight}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Strengths Section */}
                  {scenario.strengths_observed && scenario.strengths_observed.length > 0 && (
                    <div className="p-4 bg-emerald-50/50 border-t border-emerald-100">
                      <div className="flex items-center gap-2 mb-3">
                        <TrendingUp className="w-5 h-5 text-emerald-600" />
                        <h4 className="font-semibold text-emerald-800">חוזקות שנצפו</h4>
                      </div>
                      <ul className="space-y-2">
                        {scenario.strengths_observed.map((strength, i) => (
                          <li
                            key={i}
                            className="flex items-start gap-3 bg-white/70 rounded-lg p-3 shadow-sm"
                          >
                            <Star className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                            <span className="text-gray-700 leading-relaxed">{strength}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              );
            })
          ) : (
            <div className="text-center py-12 text-gray-500">
              <Sparkles className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p className="text-lg">אין עדיין תובנות זמינות</p>
              <p className="text-sm mt-2">הסרטונים נמצאים בתהליך ניתוח</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 bg-gray-50 border-t border-gray-200">
          <div className="flex justify-center">
            <button
              onClick={onClose}
              className="px-6 py-2 bg-gradient-to-r from-pink-500 to-rose-500 text-white rounded-xl font-medium hover:brightness-110 transition-all shadow-md"
            >
              הבנתי, תודה!
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
