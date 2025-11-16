import React, { useState } from 'react';
import { X, Video, CheckCircle, Camera, Upload, Target, Lightbulb } from 'lucide-react';
import VideoUploadView from './VideoUploadView';

export default function DynamicGuidelineView({ viewKey, onClose, data, onCreateVideo }) {
  const [showVideoUpload, setShowVideoUpload] = useState(false);

  if (!data) {
    return null;
  }

  const { title, subtitle, rationale, target_areas, priority } = data;

  // Generate tips based on priority and type
  const generateTips = () => {
    return [
      'צלמי מרחק של 2-3 מטרים כדי לראות את הילד בבירור',
      'אורך מומלץ: 5-7 דקות',
      'ודאי שהתאורה טובה והסאונד ברור',
      'אל תתערבי - תני לילד להיות טבעי',
      'אפשר לצלם מספר פעמים ולבחור את הטוב ביותר'
    ];
  };

  const tips = generateTips();

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-end md:items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-t-3xl md:rounded-3xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col animate-slideUp"
        onClick={(e) => e.stopPropagation()}
      >

        {/* Header */}
        <div className="bg-gradient-to-r from-indigo-500 to-purple-500 text-white p-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Video className="w-6 h-6" />
            <h3 className="text-lg font-bold">{title}</h3>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white hover:bg-opacity-20 rounded-full transition"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">

          {/* What to film */}
          <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4">
            <h4 className="font-bold text-indigo-900 mb-2 flex items-center gap-2">
              <Video className="w-5 h-5" />
              מה לצלם?
            </h4>
            <p className="text-indigo-800 text-sm leading-relaxed">
              {subtitle}
            </p>
          </div>

          {/* Why it's important */}
          {rationale && (
            <div className="bg-purple-50 border border-purple-200 rounded-xl p-4">
              <h4 className="font-bold text-purple-900 mb-2 flex items-center gap-2">
                <Lightbulb className="w-5 h-5" />
                למה זה חשוב?
              </h4>
              <p className="text-purple-800 text-sm leading-relaxed">
                {rationale}
              </p>
            </div>
          )}

          {/* Target areas */}
          {target_areas && target_areas.length > 0 && (
            <div className="bg-teal-50 border border-teal-200 rounded-xl p-4">
              <h4 className="font-bold text-teal-900 mb-2 flex items-center gap-2">
                <Target className="w-5 h-5" />
                תחומים שנבדקים
              </h4>
              <div className="flex flex-wrap gap-2">
                {target_areas.map((area, idx) => (
                  <span
                    key={idx}
                    className="bg-teal-100 text-teal-800 px-3 py-1 rounded-full text-xs font-semibold"
                  >
                    {area}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Filming tips */}
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
            <h4 className="font-bold text-blue-900 mb-3">טיפים לצילום:</h4>
            <div className="space-y-2 text-sm text-blue-800">
              {tips.map((tip, idx) => (
                <div key={idx} className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  <span>{tip}</span>
                </div>
              ))}
            </div>
          </div>

          {/* When to film */}
          <div className="bg-green-50 border border-green-200 rounded-xl p-4">
            <h4 className="font-bold text-green-900 mb-2">מתי לצלם?</h4>
            <p className="text-green-800 text-sm">
              בכל זמן שנוח לך ושהילד/ה יהיה במצב טבעי ונינוח. זה לא צריך להיות "הופעה" - רק הצצה לחיי היומיום.
            </p>
          </div>

          {/* Priority indicator */}
          {priority === 'essential' && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-3">
              <p className="text-red-800 text-sm font-semibold text-center">
                ⚠️ סרטון זה הוא חיוני להערכה
              </p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-xl p-4">
            <h5 className="font-bold text-amber-900 mb-3 text-center">מוכנה לצלם?</h5>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => setShowVideoUpload(true)}
                className="bg-gradient-to-r from-red-500 to-pink-500 text-white py-3 px-4 rounded-xl font-bold hover:shadow-lg transition flex items-center justify-center gap-2"
              >
                <Camera className="w-5 h-5" />
                <span>צילום עכשיו</span>
              </button>
              <button
                onClick={() => setShowVideoUpload(true)}
                className="bg-gradient-to-r from-blue-500 to-cyan-500 text-white py-3 px-4 rounded-xl font-bold hover:shadow-lg transition flex items-center justify-center gap-2"
              >
                <Upload className="w-5 h-5" />
                <span>העלאת וידאו</span>
              </button>
            </div>
            <p className="text-xs text-amber-700 text-center mt-2">
              את יכולה לצלם ישירות או להעלות קובץ קיים
            </p>
          </div>
        </div>

      </div>

      {/* Video Upload Modal */}
      {showVideoUpload && (
        <VideoUploadView
          onClose={() => {
            setShowVideoUpload(false);
            onClose(); // Close the guideline view too
          }}
          onCreateVideo={onCreateVideo}
          scenarioData={{ title, subtitle }}
        />
      )}
    </div>
  );
}
