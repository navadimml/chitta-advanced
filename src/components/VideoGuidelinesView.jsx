import React, { useState } from 'react';
import { X, Video, Clock, CheckCircle, Camera, Lightbulb, Upload, Play, FileVideo } from 'lucide-react';

/**
 * 🎬 Video Guidelines Deep View
 *
 * Beautiful, full-screen view for filming instructions artifact.
 * Shows scenarios, tips, and personalized guidance.
 * Each scenario has a direct upload button.
 */
export default function VideoGuidelinesView({ guidelines, childName, uploadedVideos = [], onClose, onUploadForScenario }) {
  if (!guidelines) return null;

  // Parse guidelines if it's markdown or structured data
  const scenarios = guidelines.scenarios || [];
  const generalTips = guidelines.general_tips || [];
  const duration = guidelines.estimated_duration || "2-3 דקות לסרטון";
  // Use child name from guidelines data, with fallback to prop
  const displayChildName = guidelines.child_name || childName || "הילד/ה";

  // Track which videos are being shown (by scenario index)
  const [expandedVideos, setExpandedVideos] = useState({});

  // Helper function to check if a scenario has a video uploaded
  const hasVideoForScenario = (scenario) => {
    return uploadedVideos.some(video =>
      video.scenario === scenario.title ||
      video.title === scenario.title
    );
  };

  // Helper function to get the video for a scenario
  const getVideoForScenario = (scenario) => {
    return uploadedVideos.find(video =>
      video.scenario === scenario.title ||
      video.title === scenario.title
    );
  };

  // Toggle video display for a scenario
  const toggleVideoDisplay = (idx) => {
    setExpandedVideos(prev => ({
      ...prev,
      [idx]: !prev[idx]
    }));
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-backdropIn">
      <div className="absolute inset-0 bg-black/50" />
      <div className="relative bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden animate-panelUp">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white p-6">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-3xl font-bold mb-2 flex items-center gap-3">
                <Video className="w-8 h-8" />
                הנחיות צילום מותאמות
              </h2>
              <p className="text-purple-100 text-lg">
                מיוחד עבור {displayChildName}
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
              <CheckCircle className="w-4 h-4" />
              <span>{scenarios.filter(s => hasVideoForScenario(s)).length} הושלמו</span>
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
              {scenarios.map((scenario, idx) => {
                const hasVideo = hasVideoForScenario(scenario);
                const uploadedVideo = hasVideo ? getVideoForScenario(scenario) : null;
                const isVideoExpanded = expandedVideos[idx];

                return (
                  <div
                    key={idx}
                    className={`border-2 rounded-xl p-6 transition-all duration-300 ${
                      hasVideo
                        ? 'border-green-300 bg-green-50/50 hover:border-green-400'
                        : 'border-purple-200 hover:border-purple-400 hover:shadow-lg'
                    }`}
                  >
                    {/* Scenario Header */}
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-lg ${
                          hasVideo
                            ? 'bg-green-600 text-white'
                            : 'bg-purple-600 text-white'
                        }`}>
                          {hasVideo ? <CheckCircle className="w-6 h-6" /> : idx + 1}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h4 className="text-xl font-bold text-gray-800">{scenario.title}</h4>
                            {hasVideo && (
                              <span className="px-2 py-1 bg-green-600 text-white text-xs font-bold rounded-full">
                                ✓ צולם
                              </span>
                            )}
                          </div>
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

                  {/* Uploaded Video Display */}
                  {uploadedVideo && (
                    <div className="mt-4 p-4 bg-green-50 border-2 border-green-300 rounded-lg">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <CheckCircle className="w-5 h-5 text-green-600" />
                          <span className="font-semibold text-green-900">סרטון הועלה</span>
                        </div>
                        <button
                          onClick={() => toggleVideoDisplay(idx)}
                          className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-sm font-semibold rounded-lg transition flex items-center gap-2"
                        >
                          {isVideoExpanded ? (
                            <>
                              <X className="w-4 h-4" />
                              סגור
                            </>
                          ) : (
                            <>
                              <Play className="w-4 h-4" />
                              צפה בסרטון
                            </>
                          )}
                        </button>
                      </div>

                      {isVideoExpanded && (
                        <div className="mt-3 space-y-2">
                          {uploadedVideo.url ? (
                            <video
                              src={uploadedVideo.url}
                              controls
                              className="w-full rounded-lg bg-black"
                            />
                          ) : (
                            <div className="bg-gray-100 rounded-lg p-6 text-center">
                              <FileVideo className="w-12 h-12 text-gray-400 mx-auto mb-2" />
                              <p className="text-gray-600 text-sm">סרטון הועלה אך אין תצוגה מקדימה זמינה</p>
                            </div>
                          )}
                          <div className="text-sm text-gray-700 space-y-1">
                            <p><span className="font-semibold">תאריך:</span> {uploadedVideo.date}</p>
                            {uploadedVideo.duration && (
                              <p><span className="font-semibold">משך:</span> {uploadedVideo.duration}</p>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Upload Button for This Scenario */}
                  {onUploadForScenario && (
                    <div className="mt-4 flex justify-end">
                      <button
                        onClick={() => onUploadForScenario(scenario, idx)}
                        className={`px-6 py-3 font-semibold rounded-lg transition-all duration-200 shadow-md hover:shadow-lg flex items-center gap-2 ${
                          hasVideo
                            ? 'bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white'
                            : 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white'
                        }`}
                      >
                        <Upload className="w-5 h-5" />
                        {hasVideo ? 'צלם שוב' : 'צלם לתרחיש זה'}
                      </button>
                    </div>
                  )}
                </div>
                );
              })}
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
              המטרה היא לראות את {displayChildName} בפעולה, בצורה הכי טבעית שאפשר.
              קחי את הזמן שצריך, ואין לחץ!
            </p>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="border-t border-gray-200 p-6 bg-gray-50 flex justify-center items-center">
          <button
            onClick={onClose}
            className="px-8 py-3 bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold rounded-lg transition-all duration-200"
          >
            סגור
          </button>
        </div>
      </div>

    </div>
  );
}
