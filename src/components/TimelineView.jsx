import React, { useState } from 'react';
import { X, Clock, Loader2, Download, Share2, Sparkles } from 'lucide-react';
import { api } from '../api/client';

/**
 * TimelineView - Visual Timeline Infographic
 *
 * Displays and generates beautiful timeline infographics
 * showing the child's journey through Chitta.
 */
export default function TimelineView({ familyId, childName, onClose }) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [timeline, setTimeline] = useState(null);
  const [error, setError] = useState(null);
  const [selectedStyle, setSelectedStyle] = useState('warm');

  const styles = [
    { id: 'warm', name: 'חמים', description: 'צבעים רכים ומזמינים' },
    { id: 'professional', name: 'מקצועי', description: 'עיצוב נקי ומודרני' },
    { id: 'playful', name: 'משחקי', description: 'צבעים עליזים וכיפיים' }
  ];

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);

    try {
      const result = await api.generateTimeline(familyId, selectedStyle);

      if (result.success) {
        setTimeline(result);
      } else {
        setError(result.error || 'שגיאה ביצירת ציר הזמן');
      }
    } catch (err) {
      console.error('Timeline generation error:', err);
      setError('שגיאה בחיבור לשרת');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownload = () => {
    if (timeline?.image_url) {
      const link = document.createElement('a');
      link.href = timeline.image_url;
      link.download = `timeline_${childName || 'child'}.png`;
      link.click();
    }
  };

  const handleShare = async () => {
    if (timeline?.image_url && navigator.share) {
      try {
        await navigator.share({
          title: `המסע של ${childName}`,
          text: 'ציר זמן מ-Chitta',
          url: window.location.origin + timeline.image_url
        });
      } catch (err) {
        console.log('Share cancelled');
      }
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-backdropIn">
      <div className="absolute inset-0 bg-black/50" />
      <div className="relative bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden animate-panelUp">
        {/* Header */}
        <div className="bg-gradient-to-r from-amber-500 to-orange-500 text-white p-6">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-2xl font-bold mb-1 flex items-center gap-2">
                <Clock className="w-6 h-6" />
                ציר הזמן של {childName || 'הילד/ה'}
              </h2>
              <p className="text-amber-100">
                אינפוגרפיקה ויזואלית של המסע
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/20 rounded-full transition"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-180px)]">
          {!timeline ? (
            <>
              {/* Style Selection */}
              <div className="mb-6">
                <h3 className="font-semibold text-gray-800 mb-3">בחרי סגנון:</h3>
                <div className="grid grid-cols-3 gap-3">
                  {styles.map((style) => (
                    <button
                      key={style.id}
                      onClick={() => setSelectedStyle(style.id)}
                      className={`p-4 rounded-xl border-2 transition-all ${
                        selectedStyle === style.id
                          ? 'border-amber-500 bg-amber-50'
                          : 'border-gray-200 hover:border-amber-300'
                      }`}
                    >
                      <div className="font-semibold text-gray-800">{style.name}</div>
                      <div className="text-xs text-gray-500 mt-1">{style.description}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Generate Button */}
              <button
                onClick={handleGenerate}
                disabled={isGenerating}
                className="w-full py-4 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white font-bold rounded-xl transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="w-6 h-6 animate-spin" />
                    יוצר ציר זמן...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-6 h-6" />
                    צור ציר זמן
                  </>
                )}
              </button>

              {/* Info */}
              <div className="mt-6 p-4 bg-amber-50 border border-amber-200 rounded-xl">
                <p className="text-amber-800 text-sm">
                  ציר הזמן ייווצר על בסיס המידע שנאסף במהלך השיחות -
                  כולל אירועים מרכזיים, צפייה בסרטונים, ודוחות שנוצרו.
                </p>
              </div>

              {/* Error */}
              {error && (
                <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl">
                  <p className="text-red-800 text-sm">{error}</p>
                </div>
              )}
            </>
          ) : (
            <>
              {/* Generated Timeline */}
              <div className="space-y-4">
                {/* Image */}
                <div className="rounded-xl overflow-hidden border-2 border-amber-200 shadow-lg">
                  <img
                    src={timeline.image_url}
                    alt={`ציר הזמן של ${childName}`}
                    className="w-full h-auto"
                  />
                </div>

                {/* Info */}
                <div className="flex items-center justify-between text-sm text-gray-500">
                  <span>{timeline.event_count} אירועים</span>
                  <span>נוצר עכשיו</span>
                </div>

                {/* Actions */}
                <div className="flex gap-3">
                  <button
                    onClick={handleDownload}
                    className="flex-1 py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold rounded-xl transition flex items-center justify-center gap-2"
                  >
                    <Download className="w-5 h-5" />
                    הורד
                  </button>
                  <button
                    onClick={handleShare}
                    className="flex-1 py-3 bg-amber-100 hover:bg-amber-200 text-amber-700 font-semibold rounded-xl transition flex items-center justify-center gap-2"
                  >
                    <Share2 className="w-5 h-5" />
                    שתף
                  </button>
                </div>

                {/* Regenerate */}
                <button
                  onClick={() => setTimeline(null)}
                  className="w-full py-2 text-gray-500 hover:text-gray-700 text-sm transition"
                >
                  צור מחדש בסגנון אחר
                </button>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 p-4 bg-gray-50">
          <button
            onClick={onClose}
            className="w-full py-2 text-gray-600 hover:text-gray-800 font-medium transition"
          >
            סגור
          </button>
        </div>
      </div>
    </div>
  );
}
