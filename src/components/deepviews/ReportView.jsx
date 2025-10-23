import React from 'react';
import { X, Heart, TrendingUp, Eye, Award, MessageCircle, Star } from 'lucide-react';

export default function ReportView({ viewKey, onClose }) {
  const isParentReport = viewKey === 'parentReport';

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-end md:items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-t-3xl md:rounded-3xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col animate-slideUp" onClick={(e) => e.stopPropagation()}>
        
        <div className="bg-gradient-to-r from-indigo-500 to-purple-500 text-white p-5 flex items-center justify-between">
          <h3 className="text-lg font-bold">מדריך להורים - יוני</h3>
          <button onClick={onClose} className="p-2 hover:bg-white hover:bg-opacity-20 rounded-full transition">
            <X className="w-6 h-6" />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-xl p-5">
            <h4 className="font-bold text-lg text-purple-900 mb-3 flex items-center gap-2">
              <Heart className="w-6 h-6" />
              שלום שרה,
            </h4>
            <p className="text-purple-800 leading-relaxed">
              סיימתי לנתח את השיחה שלנו ואת הסרטונים של יוני. זה היה כיף "להכיר" אותו! להלן התובנות העיקריות בשפה פשוטה.
            </p>
          </div>

          <div className="bg-green-50 border-l-4 border-green-400 rounded-lg p-4">
            <h4 className="font-bold text-green-900 mb-2 flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              נקודות חוזק
            </h4>
            <ul className="space-y-2 text-sm text-green-800">
              <li className="flex items-start gap-2">
                <Star className="w-4 h-4 mt-1 flex-shrink-0" />
                <span><strong>סקרנות ויצירתיות:</strong> יוני מראה עניין גדול בדברים חדשים ויכולת הדמיון מפותחת במשחק</span>
              </li>
              <li className="flex items-start gap-2">
                <Star className="w-4 h-4 mt-1 flex-shrink-0" />
                <span><strong>קשר רגשי:</strong> נראה קשר חם עם בני המשפחה ותגובתי</span>
              </li>
              <li className="flex items-start gap-2">
                <Star className="w-4 h-4 mt-1 flex-shrink-0" />
                <span><strong>התמדה:</strong> כשמתעניין במשהו, יוני מסוגל להתמקד לזמן סביר</span>
              </li>
            </ul>
          </div>

          <div className="bg-orange-50 border-l-4 border-orange-400 rounded-lg p-4">
            <h4 className="font-bold text-orange-900 mb-2 flex items-center gap-2">
              <Eye className="w-5 h-5" />
              תחומים שכדאי לתת עליהם את הדעת
            </h4>
            <div className="space-y-3 text-sm text-orange-800">
              <div>
                <p className="font-semibold mb-1">תקשורת ושפה:</p>
                <p>יוני משתמש במילים בודדות ומשפטים של 2-3 מילים, בעוד שבגילו (3.5) רוב הילדים כבר בונים משפטים מורכבים יותר. הוא גם מתקשה לפעמים להביע רצונות בצורה ברורה.</p>
              </div>
              <div>
                <p className="font-semibold mb-1">אינטראקציה חברתית:</p>
                <p>יוני נוטה למשחק מקבילי (לצד ילדים אחרים) יותר מאשר למשחק משותף. לפעמים נראה שהוא מתקשה "לקרוא רמזים חברתיים מילדים אחרים.</p>
              </div>
              <div>
                <p className="font-semibold mb-1">ויסות חושי:</p>
                <p>צפיתי בכמה רגעים של רגישות יתר לרעשים חזקים ולמרקמים מסוימים באוכל. זה יכול להשפיע על הנוחות שלו בסיטואציות מסוימות.</p>
              </div>
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
            <h4 className="font-bold text-blue-900 mb-3 flex items-center gap-2">
              <Award className="w-5 h-5" />
              אינדיקטורים כמותיים
            </h4>
            <div className="space-y-2">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-blue-800">תקשורת והבעה</span>
                  <span className="font-bold text-blue-900">65/100</span>
                </div>
                <div className="bg-blue-200 h-2 rounded-full overflow-hidden">
                  <div className="bg-blue-600 h-full rounded-full" style={{width: '65%'}}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-blue-800">אינטראקציה חברתית</span>
                  <span className="font-bold text-blue-900">58/100</span>
                </div>
                <div className="bg-blue-200 h-2 rounded-full overflow-hidden">
                  <div className="bg-blue-600 h-full rounded-full" style={{width: '58%'}}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-blue-800">ויסות והתנהלות</span>
                  <span className="font-bold text-blue-900">62/100</span>
                </div>
                <div className="bg-blue-200 h-2 rounded-full overflow-hidden">
                  <div className="bg-blue-600 h-full rounded-full" style={{width: '62%'}}></div>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-xl p-5">
            <h4 className="font-bold text-indigo-900 mb-3 flex items-center gap-2">
              <MessageCircle className="w-5 h-5" />
              חשוב להדגיש
            </h4>
            <p className="text-indigo-800 text-sm leading-relaxed">
              <strong>זהו לא אבחון קליני.</strong> התצפיות שלי מבוססות על הסרטונים והראיון, אך אבחנה רשמית דורשת מפגש עם איש מקצוע מוסמך. המטרה שלי היא לעזור לך להבין מה כדאי לבדוק ולאן כדאי לפנות.
            </p>
          </div>
        </div>
        
      </div>
    </div>
  );
}
