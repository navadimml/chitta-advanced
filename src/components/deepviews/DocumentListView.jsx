import React from 'react';
import { X, FileText, FileUp, ChevronRight } from 'lucide-react';

export default function DocumentListView({ onClose }) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-end md:items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-t-3xl md:rounded-3xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col animate-slideUp" onClick={(e) => e.stopPropagation()}>
        
        <div className="bg-gradient-to-r from-indigo-500 to-purple-500 text-white p-5 flex items-center justify-between">
          <h3 className="text-lg font-bold">המסמכים של יוני</h3>
          <button onClick={onClose} className="p-2 hover:bg-white hover:bg-opacity-20 rounded-full transition">
            <X className="w-6 h-6" />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-xl p-4">
            <h4 className="font-bold text-purple-900 mb-2">3 מסמכים נשמרו</h4>
            <p className="text-sm text-purple-800">
              כל המסמכים מנותחים ומשולבים בתמונה המלאה של יוני
            </p>
          </div>

          <div className="space-y-3">
            <div className="bg-white border border-gray-200 rounded-xl p-4 hover:shadow-md transition cursor-pointer">
              <div className="flex items-start gap-3">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <FileText className="w-6 h-6 text-blue-600" />
                </div>
                <div className="flex-1">
                  <h5 className="font-bold text-gray-900 text-sm mb-1">אבחון התפתחותי</h5>
                  <p className="text-xs text-gray-600 mb-2">הועלה ב-5 ספטמבר 2024 • PDF • 4 עמודים</p>
                  <div className="flex gap-2">
                    <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-semibold">נותח</span>
                    <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-semibold">משולב</span>
                  </div>
                </div>
                <ChevronRight className="w-5 h-5 text-gray-400" />
              </div>
              <div className="mt-3 pt-3 border-t border-gray-100">
                <p className="text-xs text-gray-700">
                  <strong>סיכום:</strong> אבחון מלפני שנה, זיהה איחור קל בשפה ומיומנויות תקשורת.
                </p>
              </div>
            </div>
          </div>

          <button className="w-full bg-gradient-to-r from-blue-500 to-cyan-500 text-white py-3 rounded-xl font-bold hover:shadow-lg transition flex items-center justify-center gap-2">
            <FileUp className="w-5 h-5" />
            העלאת מסמך נוסף
          </button>
        </div>
        
      </div>
    </div>
  );
}
