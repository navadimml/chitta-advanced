import React from 'react';
import { X, FileUp, Brain, CheckCircle, Shield } from 'lucide-react';

export default function DocumentUploadView({ onClose }) {
  return (
    <div className="fixed inset-0 z-50 flex items-end md:items-center justify-center p-4 animate-backdropIn" onClick={onClose}>
      <div className="absolute inset-0 bg-black/50" />
      <div className="relative bg-white rounded-t-3xl md:rounded-3xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col animate-panelUp" onClick={(e) => e.stopPropagation()}>
        
        <div className="bg-gradient-to-r from-indigo-500 to-purple-500 text-white p-5 flex items-center justify-between">
          <h3 className="text-lg font-bold">העלאת מסמך</h3>
          <button onClick={onClose} className="p-2 hover:bg-white hover:bg-opacity-20 rounded-full transition">
            <X className="w-6 h-6" />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          <div className="bg-gradient-to-r from-blue-50 to-cyan-50 border border-blue-200 rounded-xl p-5 text-center">
            <FileUp className="w-12 h-12 text-blue-600 mx-auto mb-3" />
            <h4 className="font-bold text-blue-900 mb-2">העלאת מסמך רפואי או אבחון</h4>
            <p className="text-sm text-blue-800 mb-4">גררי קובץ או לחצי לבחירה</p>
            <button className="bg-gradient-to-r from-blue-500 to-cyan-500 text-white py-3 px-6 rounded-xl font-bold hover:shadow-lg transition">
              בחירת מסמך
            </button>
          </div>

          <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4">
            <h5 className="font-bold text-indigo-900 mb-2 flex items-center gap-2">
              <Brain className="w-5 h-5" />
              מה אני אעשה עם המסמך?
            </h5>
            <div className="space-y-2 text-sm text-indigo-800">
              <div className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <span>אקרא ואנתח את המסמך</span>
              </div>
              <div className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <span>אסכם את הממצאים בשפה פשוטה</span>
              </div>
              <div className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <span>אשלב עם המידע על יוני</span>
              </div>
            </div>
          </div>

          <div className="bg-green-50 border border-green-200 rounded-xl p-4">
            <div className="flex items-start gap-3">
              <Shield className="w-5 h-5 text-green-700 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-green-800">
                <p className="font-semibold mb-1">מוצפן ומאובטח</p>
                <p>כל המסמכים מוצפנים והמידע שלך מאובטח.</p>
              </div>
            </div>
          </div>
        </div>
        
      </div>
    </div>
  );
}
