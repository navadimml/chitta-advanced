import React from 'react';
import { X, Book } from 'lucide-react';

export default function JournalView({ onClose }) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-end md:items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-t-3xl md:rounded-3xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col animate-slideUp" onClick={(e) => e.stopPropagation()}>
        
        <div className="bg-gradient-to-r from-indigo-500 to-purple-500 text-white p-5 flex items-center justify-between">
          <h3 className="text-lg font-bold">יומן יוני</h3>
          <button onClick={onClose} className="p-2 hover:bg-white hover:bg-opacity-20 rounded-full transition">
            <X className="w-6 h-6" />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-xl p-4">
            <h4 className="font-bold text-amber-900 mb-2 flex items-center gap-2">
              <Book className="w-5 h-5" />
              הוסיפי רשומה חדשה
            </h4>
            <p className="text-amber-800 text-sm mb-3">
              תעדי רגעים, התקדמויות קטנות, או דברים שמעניינים אותך
            </p>
            <textarea
              className="w-full h-32 p-3 border border-amber-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent resize-none text-sm"
              placeholder="למשל: 'היום יוני אמר משפט שלם בפעם הראשונה!' או 'שמתי לב שהוא מתקשה עם מרקמים חדשים באוכל...'"
              dir="rtl"
            ></textarea>
            <button className="mt-2 w-full bg-gradient-to-r from-amber-500 to-orange-500 text-white py-2 rounded-lg font-bold hover:shadow-lg transition-all">
              שמירת רשומה
            </button>
          </div>

          <div className="space-y-3">
            <h5 className="font-bold text-gray-700 text-sm">רשומות אחרונות</h5>
            
            <div className="bg-white border border-gray-200 rounded-xl p-3">
              <div className="flex justify-between items-start mb-2">
                <span className="text-xs text-gray-500">לפני 3 ימים</span>
                <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-semibold">התקדמות</span>
              </div>
              <p className="text-sm text-gray-800">
                יוני התחיל להשתמש ב"בבקשה" ו"תודה" יותר לבד! אני כל כך גאה בו 💚
              </p>
            </div>

            <div className="bg-white border border-gray-200 rounded-xl p-3">
              <div className="flex justify-between items-start mb-2">
                <span className="text-xs text-gray-500">לפני שבוע</span>
                <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-semibold">תצפית</span>
              </div>
              <p className="text-sm text-gray-800">
                בגן הגננת אמרה שהוא משתלב יותר טוב במעגל. נראה שהטיפולים עוזרים.
              </p>
            </div>

            <div className="bg-white border border-gray-200 rounded-xl p-3">
              <div className="flex justify-between items-start mb-2">
                <span className="text-xs text-gray-500">לפני שבועיים</span>
                <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded-full text-xs font-semibold">אתגר</span>
              </div>
              <p className="text-sm text-gray-800">
                היום היה קשה בקניון - הרעש היה חזק מדי בשבילו. עזבנו מוקדם.
              </p>
            </div>
          </div>
        </div>
        
      </div>
    </div>
  );
}
