import React from 'react';
import { X, FileText, Calendar, Share2, CheckCircle } from 'lucide-react';

export default function MeetingSummaryView({ onClose }) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-end md:items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-t-3xl md:rounded-3xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col animate-slideUp" onClick={(e) => e.stopPropagation()}>
        
        <div className="bg-gradient-to-r from-indigo-500 to-purple-500 text-white p-5 flex items-center justify-between">
          <h3 className="text-lg font-bold">סיכום לפגישה</h3>
          <button onClick={onClose} className="p-2 hover:bg-white hover:bg-opacity-20 rounded-full transition">
            <X className="w-6 h-6" />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-xl p-5">
            <div className="flex items-center gap-3 mb-3">
              <Calendar className="w-6 h-6 text-indigo-600" />
              <div>
                <h4 className="font-bold text-indigo-900">פגישה עם יעל לוי</h4>
                <p className="text-sm text-indigo-700">מחר, 15 באוקטובר, 10:00</p>
              </div>
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-xl p-4">
            <h5 className="font-bold text-gray-900 mb-3">מידע רקע על יוני</h5>
            <div className="space-y-2 text-sm text-gray-700">
              <p><strong>גיל:</strong> 3.5 שנים</p>
              <p><strong>נושא מרכזי:</strong> איחור בדיבור, קושי ויסות חושי</p>
              <p><strong>מטפלים נוכחיים:</strong> ד״ר רחל כהן (קלינאית תקשורת)</p>
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
            <h5 className="font-bold text-blue-900 mb-3">ממצאים עיקריים מהערכת Chitta</h5>
            <ul className="space-y-2 text-sm text-blue-800">
              <li className="flex items-start gap-2">
                <div className="w-1.5 h-1.5 bg-blue-600 rounded-full mt-1.5 flex-shrink-0"></div>
                <span>שפה והבנה - משתמש במילים בודדות ומשפטים קצרים (2-3 מילים)</span>
              </li>
              <li className="flex items-start gap-2">
                <div className="w-1.5 h-1.5 bg-blue-600 rounded-full mt-1.5 flex-shrink-0"></div>
                <span>ויסות חושי - רגישות יתר לרעשים ומרקמים מסוימים באוכל</span>
              </li>
              <li className="flex items-start gap-2">
                <div className="w-1.5 h-1.5 bg-blue-600 rounded-full mt-1.5 flex-shrink-0"></div>
                <span>אינטראקציה חברתית - נוטה למשחק מקבילי, מתקשה לפעמים ביוזמה חברתית</span>
              </li>
            </ul>
          </div>

          <div className="bg-green-50 border border-green-200 rounded-xl p-4">
            <h5 className="font-bold text-green-900 mb-3">התקדמות בחודש האחרון</h5>
            <ul className="space-y-2 text-sm text-green-800">
              <li className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0 text-green-600" />
                <span>התחיל להשתמש ב"בבקשה" ו"תודה" באופן עצמאי יותר</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0 text-green-600" />
                <span>משתלב טוב יותר במעגל בגן (דיווח הגננת)</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0 text-green-600" />
                <span>מראה התקדמות בטיפול התקשורת עם ד״ר כהן</span>
              </li>
            </ul>
          </div>

          <div className="bg-purple-50 border border-purple-200 rounded-xl p-4">
            <h5 className="font-bold text-purple-900 mb-2">שאלות לפגישה</h5>
            <ul className="space-y-1 text-sm text-purple-800">
              <li>• איך נוכל לעזור ביוני להתמודד עם רגישות לרעשים?</li>
              <li>• האם יש תרגילים שנוכל לעשות בבית?</li>
              <li>• כמה זמן לוקח בדרך כלל לראות שיפור?</li>
            </ul>
          </div>

          <button className="w-full bg-gradient-to-r from-indigo-500 to-purple-500 text-white py-3 rounded-xl font-bold hover:shadow-lg transition flex items-center justify-center gap-2">
            <Share2 className="w-5 h-5" />
            שליחה ליעל לוי
          </button>
        </div>
        
      </div>
    </div>
  );
}
