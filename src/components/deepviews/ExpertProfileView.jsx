import React from 'react';
import { X, Star, MapPin, Phone, Mail } from 'lucide-react';

export default function ExpertProfileView({ viewKey, onClose }) {
  const experts = {
    expert1: {
      name: 'ד״ר רחל כהן',
      role: 'קלינאית תקשורת מוסמכת',
      rating: 4.8,
      reviews: 127,
      location: 'רח׳ ויצמן 25, תל אביב',
      phone: '03-1234567',
      email: 'rachel.cohen@clinic.co.il',
      specialties: ['איחור שפה', 'גיל 2-6', 'ליקויי תקשורת', 'דו-לשוניות'],
      whyMatch: 'ד״ר כהן מתמחה בדיוק בטווח הגילאים והקשיים שזיהיתי אצל יוני. היא עובדת עם ילדים עם איחור בדיבור ומיומנויות תקשורת, ויש לה ניסיון רב בגישה רגישה ומעצימה להורים.',
      initials: 'RK',
      color: 'from-teal-400 to-cyan-400'
    },
    expert2: {
      name: 'יעל לוי',
      role: 'מרפאה בעיסוק מוסמכת, M.OT',
      rating: 4.9,
      reviews: 93,
      location: 'רח׳ ביאליק 18, רמת גן',
      phone: '03-7654321',
      email: 'yael.levy@ot-clinic.co.il',
      specialties: ['אינטגרציה חושית', 'ויסות עצמי', 'מוטוריקה עדינה', 'גילאים 2-8'],
      whyMatch: 'יעל מתמחה בדיוק בתחום הויסות החושי שזיהיתי אצל יוני. היא עובדת עם גישה של אינטגרציה חושית ועוזרת לילדים להתמודד עם רגישויות למרקמים, רעשים ועוד.',
      initials: 'YL',
      color: 'from-rose-400 to-pink-400'
    }
  };

  const expert = experts[viewKey] || experts.expert1;

  return (
    <div className="fixed inset-0 z-50 flex items-end md:items-center justify-center p-4 animate-backdropIn" onClick={onClose}>
      <div className="absolute inset-0 bg-black/50" />
      <div className="relative bg-white rounded-t-3xl md:rounded-3xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col animate-panelUp" onClick={(e) => e.stopPropagation()}>
        
        <div className="bg-gradient-to-r from-indigo-500 to-purple-500 text-white p-5 flex items-center justify-between">
          <h3 className="text-lg font-bold">פרופיל מומחה</h3>
          <button onClick={onClose} className="p-2 hover:bg-white hover:bg-opacity-20 rounded-full transition">
            <X className="w-6 h-6" />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          <div className="flex items-start gap-4 bg-gradient-to-r from-teal-50 to-cyan-50 border border-teal-200 rounded-xl p-5">
            <div className={`w-20 h-20 bg-gradient-to-br ${expert.color} rounded-full flex items-center justify-center text-white text-2xl font-bold flex-shrink-0`}>
              {expert.initials}
            </div>
            <div className="flex-1">
              <h4 className="text-xl font-bold text-teal-900">{expert.name}</h4>
              <p className="text-teal-700 text-sm mb-2">{expert.role}</p>
              <div className="flex items-center gap-3 text-sm">
                <div className="flex items-center gap-1 text-amber-600">
                  <Star className="w-4 h-4 fill-current" />
                  <span className="font-bold">{expert.rating}</span>
                  <span className="text-gray-600">({expert.reviews} ביקורות)</span>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-purple-50 border border-purple-200 rounded-xl p-4">
            <h5 className="font-bold text-purple-900 mb-2">התמחות</h5>
            <div className="flex flex-wrap gap-2">
              {expert.specialties.map((specialty, idx) => (
                <span key={idx} className="px-3 py-1 bg-purple-200 text-purple-800 rounded-full text-xs font-semibold">
                  {specialty}
                </span>
              ))}
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
            <h5 className="font-bold text-blue-900 mb-2">למה מתאימה ליוני?</h5>
            <p className="text-blue-800 text-sm leading-relaxed">
              {expert.whyMatch}
            </p>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <MapPin className="w-5 h-5 text-gray-600" />
              <span className="text-sm text-gray-800">{expert.location}</span>
            </div>
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <Phone className="w-5 h-5 text-gray-600" />
              <span className="text-sm text-gray-800" dir="ltr">{expert.phone}</span>
            </div>
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <Mail className="w-5 h-5 text-gray-600" />
              <span className="text-sm text-gray-800">{expert.email}</span>
            </div>
          </div>

          <div className="bg-green-50 border border-green-200 rounded-xl p-4">
            <h5 className="font-bold text-green-900 mb-2">זמינות</h5>
            <p className="text-green-800 text-sm">
              תורים פנויים בשבועיים הקרובים • מקבלת כרטיס כללית ומכבי
            </p>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <button className="bg-gradient-to-r from-teal-500 to-cyan-500 text-white py-3 px-4 rounded-xl font-bold hover:shadow-lg transition">
              קביעת תור
            </button>
            <button className="bg-white border-2 border-teal-500 text-teal-600 py-3 px-4 rounded-xl font-bold hover:bg-teal-50 transition">
              שליחת הדוח
            </button>
          </div>
        </div>
        
      </div>
    </div>
  );
}
