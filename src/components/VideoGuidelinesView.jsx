import React from 'react';
import { X, Video, Clock, CheckCircle, Camera, Lightbulb } from 'lucide-react';

/**
 * 🎬 Video Guidelines Deep View
 *
 * Beautiful, full-screen view for filming instructions artifact.
 * Shows scenarios, tips, and personalized guidance.
 */
export default function VideoGuidelinesView({ guidelines, childName, onClose }) {
  if (!guidelines) return null;

  // Parse guidelines if it's markdown or structured data
  const scenarios = guidelines.scenarios || [];
  const generalTips = guidelines.general_tips || [];
  const duration = guidelines.estimated_duration || "2-3 דקות לסרטון";

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden animate-slideUp">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white p-6">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-3xl font-bold mb-2 flex items-center gap-3">
                <Video className="w-8 h-8" />
                הנחיות צילום מותאמות
              </h2>
              <p className="text-purple-100 text-lg">
                {childName ? `מיוחד עבור ${childName}` : 'מותאם אישית עבורך'}
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
              <Camera className="w-4 h-4" />
              <span>{scenarios.length} תרחישים</span>
            </div>
            <div className="flex items-center gap-2 bg-white/20 rounded-lg px-3 py-2">
              <Clock className="w-4 h-4" />
              <span>{duration}</span>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="overflow-y-auto max-h-[calc(90vh-200px)] p-6">
          {/* Introduction */}
          {guidelines.introduction && (
            <div className="mb-8 p-6 bg-indigo-50 border-r-4 border-indigo-500 rounded-lg">
              <div className="flex items-start gap-3">
                <Lightbulb className="w-6 h-6 text-indigo-600 flex-shrink-0 mt-1" />
                <div>
                  <h3 className="font-bold text-lg text-indigo-900 mb-2">למה זה חשוב?</h3>
                  <p className="text-indigo-800 leading-relaxed">
                    {guidelines.introduction}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Scenarios */}
          <div className="mb-8">
            <h3 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
              <Video className="w-6 h-6 text-purple-600" />
              תרחישי הצילום
            </h3>

            <div className="space-y-6">
              {scenarios.map((scenario, idx) => (
                <div
                  key={idx}
                  className="border-2 border-purple-200 rounded-xl p-6 hover:border-purple-400 transition-all duration-300 hover:shadow-lg"
                >
                  {/* Scenario Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-purple-600 text-white rounded-full flex items-center justify-center font-bold text-lg">
                        {idx + 1}
                      </div>
                      <div>
                        <h4 className="text-xl font-bold text-gray-800">{scenario.title}</h4>
                        <p className="text-sm text-gray-600 mt-1">{scenario.context}</p>
                      </div>
                    </div>
                    {scenario.duration && (
                      <div className="flex items-center gap-1 text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
                        <Clock className="w-4 h-4" />
                        {scenario.duration}
                      </div>
                    )}
                  </div>

                  {/* What to Film */}
                  <div className="mb-4">
                    <h5 className="font-semibold text-gray-700 mb-2 flex items-center gap-2">
                      <Camera className="w-4 h-4 text-purple-600" />
                      מה לצלם:
                    </h5>
                    <p className="text-gray-700 leading-relaxed bg-purple-50 p-4 rounded-lg">
                      {scenario.what_to_film}
                    </p>
                  </div>

                  {/* Why This Matters - Always displayed at the end */}
                  {scenario.why_matters && (
                    <div className="mt-4 p-4 bg-indigo-50 rounded-lg border-r-2 border-indigo-400">
                      <p className="text-sm text-indigo-800">
                        <span className="font-semibold">💡 למה זה חשוב: </span>
                        {scenario.why_matters}
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* General Tips */}
          {generalTips.length > 0 && (
            <div className="mb-8">
              <h3 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                <Lightbulb className="w-6 h-6 text-yellow-600" />
                טיפים כלליים
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {generalTips.map((tip, idx) => (
                  <div
                    key={idx}
                    className="flex items-start gap-3 p-4 bg-yellow-50 border border-yellow-200 rounded-lg hover:shadow-md transition-shadow"
                  >
                    <CheckCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                    <p className="text-gray-700">{tip}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Footer Note */}
          <div className="mt-8 p-6 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-xl border border-purple-200">
            <p className="text-gray-700 leading-relaxed text-center">
              <span className="font-semibold text-purple-800">💙 זכרי:</span> אין נכון ולא נכון.
              המטרה היא לראות את {childName || 'הילד/ה'} בפעולה, בצורה הכי טבעית שאפשר.
              קחי את הזמן שצריך, ואין לחץ!
            </p>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="border-t border-gray-200 p-6 bg-gray-50 flex justify-between items-center">
          <button
            onClick={onClose}
            className="px-6 py-3 bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold rounded-lg transition-all duration-200"
          >
            סגור
          </button>
          <button
            className="px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-semibold rounded-lg transition-all duration-200 shadow-lg hover:shadow-xl"
          >
            התחל צילום →
          </button>
        </div>
      </div>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-fadeIn {
          animation: fadeIn 0.3s ease-out;
        }
        .animate-slideUp {
          animation: slideUp 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
      `}</style>
    </div>
  );
}
