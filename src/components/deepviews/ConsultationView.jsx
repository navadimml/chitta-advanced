import React from 'react';
import { X, Brain, HelpCircle, Users, Lightbulb, CheckCircle } from 'lucide-react';

export default function ConsultationView({ onClose }) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-end md:items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-t-3xl md:rounded-3xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col animate-slideUp" onClick={(e) => e.stopPropagation()}>
        
        <div className="bg-gradient-to-r from-indigo-500 to-purple-500 text-white p-5 flex items-center justify-between">
          <h3 className="text-lg font-bold">התייעצות עם Chitta</h3>
          <button onClick={onClose} className="p-2 hover:bg-white hover:bg-opacity-20 rounded-full transition">
            <X className="w-6 h-6" />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-xl p-5">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-indigo-500 rounded-full flex items-center justify-center">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
                <h4 className="font-bold text-purple-900">מצב התייעצות</h4>
                <p className="text-sm text-purple-700">שאלי כל שאלה שעולה לך</p>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <h5 className="font-bold text-gray-700 text-sm">שאלות נפוצות:</h5>

            <button className="w-full text-right bg-blue-50 border border-blue-200 rounded-xl p-4 hover:bg-blue-100 transition">
              <div className="flex items-start gap-3">
                <HelpCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-blue-900 text-sm mb-1">איך אני יודעת אם הקושי חמור?</p>
                  <p className="text-xs text-blue-700">לחצי לקבל תשובה מפורטת</p>
                </div>
              </div>
            </button>

            <button className="w-full text-right bg-teal-50 border border-teal-200 rounded-xl p-4 hover:bg-teal-100 transition">
              <div className="flex items-start gap-3">
                <Users className="w-5 h-5 text-teal-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-teal-900 text-sm mb-1">באיזה סדר לפנות לאנשי מקצוע?</p>
                  <p className="text-xs text-teal-700">המלצות על תהליך הטיפול</p>
                </div>
              </div>
            </button>

            <button className="w-full text-right bg-amber-50 border border-amber-200 rounded-xl p-4 hover:bg-amber-100 transition">
              <div className="flex items-start gap-3">
                <Lightbulb className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-amber-900 text-sm mb-1">מה אני יכולה לעשות בבית?</p>
                  <p className="text-xs text-amber-700">פעילויות והמלצות יומיומיות</p>
                </div>
              </div>
            </button>
          </div>

          <div className="bg-purple-50 border border-purple-200 rounded-xl p-4">
            <h5 className="font-bold text-purple-900 mb-3">או שאלי שאלה חופשית:</h5>
            <textarea
              className="w-full h-24 p-3 border border-purple-300 rounded-lg focus:ring-2 focus:ring-purple-500 resize-none text-sm"
              placeholder="למשל: 'האם זה רגיל שילד בגיל 3.5 עדיין לא מדבר במשפטים?'"
              dir="rtl"
            ></textarea>
            <button className="mt-2 w-full bg-gradient-to-r from-purple-500 to-indigo-500 text-white py-2 rounded-lg font-bold hover:shadow-lg transition">
              שליחת שאלה
            </button>
          </div>
        </div>
        
      </div>
    </div>
  );
}
