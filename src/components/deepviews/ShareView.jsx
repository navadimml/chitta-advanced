import React, { useState } from 'react';
import { X, Share2, Shield, FileText, Video, Lock, ExternalLink, ToggleLeft, ToggleRight } from 'lucide-react';

export default function ShareView({ onClose }) {
  const [shareToggles, setShareToggles] = useState({
    parentReport: true,
    professionalReport: true,
    videos: false,
    journal: true,
    assessmentData: false
  });

  return (
    <div className="fixed inset-0 z-50 flex items-end md:items-center justify-center p-4 animate-backdropIn" onClick={onClose}>
      <div className="absolute inset-0 bg-black/50" />
      <div className="relative bg-white rounded-t-3xl md:rounded-3xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col animate-panelUp" onClick={(e) => e.stopPropagation()}>
        
        <div className="bg-gradient-to-r from-indigo-500 to-purple-500 text-white p-5 flex items-center justify-between">
          <h3 className="text-lg font-bold">שיתוף עם איש מקצוע</h3>
          <button onClick={onClose} className="p-2 hover:bg-white hover:bg-opacity-20 rounded-full transition">
            <X className="w-6 h-6" />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-xl p-5">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full flex items-center justify-center">
                <Share2 className="w-6 h-6 text-white" />
              </div>
              <div>
                <h4 className="font-bold text-indigo-900">שיתוף מאובטח</h4>
                <p className="text-sm text-indigo-700">בחרי בדיוק מה לשתף</p>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <h5 className="font-bold text-gray-700 text-sm">מה לשתף?</h5>
            
            <div 
              onClick={() => setShareToggles({...shareToggles, parentReport: !shareToggles.parentReport})}
              className={`border rounded-xl p-4 flex items-center justify-between cursor-pointer transition ${
                shareToggles.parentReport ? 'bg-indigo-50 border-indigo-300' : 'bg-white border-gray-200 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center gap-3">
                <FileText className={`w-5 h-5 ${shareToggles.parentReport ? 'text-indigo-600' : 'text-gray-500'}`} />
                <div>
                  <div className="font-semibold text-sm text-gray-900">מדריך להורים</div>
                  <div className="text-xs text-gray-600">סיכום מפורט עם ממצאים</div>
                </div>
              </div>
              {shareToggles.parentReport ? 
                <ToggleRight className="w-8 h-8 text-indigo-600" /> : 
                <ToggleLeft className="w-8 h-8 text-gray-400" />
              }
            </div>

            <div 
              onClick={() => setShareToggles({...shareToggles, videos: !shareToggles.videos})}
              className={`border rounded-xl p-4 flex items-center justify-between cursor-pointer transition ${
                shareToggles.videos ? 'bg-indigo-50 border-indigo-300' : 'bg-white border-gray-200 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center gap-3">
                <Video className={`w-5 h-5 ${shareToggles.videos ? 'text-indigo-600' : 'text-gray-500'}`} />
                <div>
                  <div className="font-semibold text-sm text-gray-900">סרטונים</div>
                  <div className="text-xs text-gray-600">3 סרטונים של יוני</div>
                </div>
              </div>
              {shareToggles.videos ? 
                <ToggleRight className="w-8 h-8 text-indigo-600" /> : 
                <ToggleLeft className="w-8 h-8 text-gray-400" />
              }
            </div>
          </div>

          <div className="bg-green-50 border border-green-200 rounded-xl p-4">
            <div className="flex items-start gap-3">
              <Shield className="w-5 h-5 text-green-700 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-green-800">
                <p className="font-semibold mb-1">קישור מאובטח</p>
                <p>הקישור מוצפן. את יכולה לבטל את הגישה בכל רגע.</p>
              </div>
            </div>
          </div>

          <button className="w-full bg-gradient-to-r from-indigo-500 to-purple-500 text-white py-4 rounded-xl font-bold hover:shadow-lg transition flex items-center justify-center gap-2">
            <ExternalLink className="w-5 h-5" />
            יצירת קישור ושליחה
          </button>
        </div>
        
      </div>
    </div>
  );
}
