import React, { useState } from 'react';
import { X, Video, CheckCircle, Camera, Upload } from 'lucide-react';
import VideoUploadView from './VideoUploadView';

export default function FilmingInstructionView({ viewKey, onClose }) {
  const [showVideoUpload, setShowVideoUpload] = useState(false);
  const instructions = {
    view1: {
      title: 'תרחיש 1: משחק חופשי',
      subtitle: 'מה לצלם?',
      description: 'צלמי את יוני במשחק חופשי עם ילדים אחרים (2-3 ילדים). זה יכול להיות בגן, בגינה הציבורית, או בבית חבר.',
      why: 'משחק חופשי מאפשר לראות איך יוני מתקשר עם ילדים אחרים, יוזם משחק, מגיב לשינויים, ומשתף פעולה - כל אלה מספרים הרבה על התפתחות חברתית ורגשית.',
      tips: [
        'צלמי מרחק של 2-3 מטרים כדי לראות את כל הילדים',
        'אורך מומלץ: 3-5 דקות',
        'אל תתערבי - תני להם לשחק בחופשיות',
        'ודאי שהסאונד ברור (שומעים שיחות)'
      ],
      timing: 'בכל זמן שנוח לך ושיוני יהיה במצב טבעי ונינוח. זה לא צריך להיות "הופעה" - רק הצצה לחיי היומיום שלו.'
    },
    view2: {
      title: 'תרחיש 2: זמן ארוחה',
      subtitle: 'מה לצלם?',
      description: 'ארוחה משפחתית רגילה - ארוחת צהריים או ערב. המטרה היא לראות איך יוני מתנהל בסיטואציה חברתית מובנית עם משפחה.',
      why: 'ארוחה משפחתית מגלה הפוסי תקשורת, יכולת ויסות (להמתין, לשבת), תגובה לגירויים חושיים (טעמים, מרקמים), ויכולת להיות חלק מקבוצה.',
      tips: [
        'צלמי ארוחה רגילה - לא מיוחדת',
        'תפסי את כל השולחן כולל יוני ואחרים',
        '3-5 דקות מספיקות',
        'השאירי את המצלמה במקום קבוע'
      ],
      timing: 'מתי לצלם? בזמן ארוחה שנוח לך'
    },
    view3: {
      title: 'תרחיש 3: פעילות ממוקדת',
      subtitle: 'מה לצלם?',
      description: 'פעילות שדורשת ריכוז - ציור, פאזל, בניית משהו, או למידה. משהו שיוני צריך להתמקד בו לכמה דקות.',
      why: 'פעילות ממוקדת מאפשרת לראות ריכוז, התמדה, תגובה לתסכול, יכולת לעקוב אחר הוראות, ומיומנויות מוטוריקה עדינה.',
      tips: [
        'בחרי פעילות שיוני אוהב ויודע לעשות',
        'צלמי מזווית שרואה את הפנים והידיים',
        'אפשר להיות נוכחת ולעזור קצת אם צריך',
        '3-5 דקות של הפעילות'
      ],
      timing: 'מתי לצלם? כשנוח לך'
    }
  };

  const instruction = instructions[viewKey] || instructions.view1;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-end md:items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-t-3xl md:rounded-3xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col animate-slideUp" onClick={(e) => e.stopPropagation()}>
        
        <div className="bg-gradient-to-r from-indigo-500 to-purple-500 text-white p-5 flex items-center justify-between">
          <h3 className="text-lg font-bold">{instruction.title}</h3>
          <button onClick={onClose} className="p-2 hover:bg-white hover:bg-opacity-20 rounded-full transition">
            <X className="w-6 h-6" />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4">
            <h4 className="font-bold text-indigo-900 mb-2 flex items-center gap-2">
              <Video className="w-5 h-5" />
              {instruction.subtitle}
            </h4>
            <p className="text-indigo-800 text-sm leading-relaxed">
              {instruction.description}
            </p>
          </div>

          <div className="bg-purple-50 border border-purple-200 rounded-xl p-4">
            <h4 className="font-bold text-purple-900 mb-2">למה זה חשוב?</h4>
            <p className="text-purple-800 text-sm leading-relaxed">
              {instruction.why}
            </p>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
            <h4 className="font-bold text-blue-900 mb-3">טיפים לצילום:</h4>
            <div className="space-y-2 text-sm text-blue-800">
              {instruction.tips.map((tip, idx) => (
                <div key={idx} className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  <span>{tip}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-green-50 border border-green-200 rounded-xl p-4">
            <h4 className="font-bold text-green-900 mb-2">מתי לצלם?</h4>
            <p className="text-green-800 text-sm">
              {instruction.timing}
            </p>
          </div>

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
          onClose={() => setShowVideoUpload(false)}
          scenarioData={{ title: instruction.title }}
        />
      )}
    </div>
  );
}
