import React, { useState } from 'react';
import { X, Play, Pause, Shield, CheckCircle } from 'lucide-react';

export default function VideoGalleryView({ onClose }) {
  const [isPlaying, setIsPlaying] = useState(false);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-end md:items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-t-3xl md:rounded-3xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col animate-slideUp" onClick={(e) => e.stopPropagation()}>
        
        <div className="bg-gradient-to-r from-indigo-500 to-purple-500 text-white p-5 flex items-center justify-between">
          <h3 className="text-lg font-bold">הסרטונים של יוני</h3>
          <button onClick={onClose} className="p-2 hover:bg-white hover:bg-opacity-20 rounded-full transition">
            <X className="w-6 h-6" />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-xl p-4">
            <h4 className="font-bold text-purple-900 mb-2">3 סרטונים הועלו</h4>
            <p className="text-sm text-purple-800">
              הסרטונים נשמרים בצורה מאובטחת ומוצפנת
            </p>
          </div>

          <div className="bg-black rounded-xl overflow-hidden">
            <div className="aspect-video bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center relative">
              <div className="text-center text-white">
                <Play className="w-16 h-16 mx-auto mb-2 opacity-80" />
                <p className="text-sm opacity-70">משחק חופשי - גן הילדים</p>
              </div>
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black to-transparent p-4">
                <div className="flex items-center gap-3">
                  <button 
                    onClick={() => setIsPlaying(!isPlaying)}
                    className="w-10 h-10 bg-white bg-opacity-20 hover:bg-opacity-30 rounded-full flex items-center justify-center transition"
                  >
                    {isPlaying ? <Pause className="w-5 h-5 text-white" /> : <Play className="w-5 h-5 text-white" />}
                  </button>
                  <div className="flex-1 h-1 bg-white bg-opacity-30 rounded-full overflow-hidden">
                    <div className="h-full bg-white rounded-full" style={{width: '35%'}}></div>
                  </div>
                  <span className="text-white text-sm" dir="ltr">1:35 / 4:32</span>
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <div className="bg-indigo-50 border-2 border-indigo-300 rounded-xl p-3 flex items-center gap-3">
              <div className="w-20 h-14 bg-indigo-200 rounded-lg flex items-center justify-center flex-shrink-0">
                <Play className="w-6 h-6 text-indigo-600" />
              </div>
              <div className="flex-1">
                <h5 className="font-bold text-indigo-900 text-sm">משחק חופשי</h5>
                <p className="text-xs text-indigo-700">10 אוקטובר 2024 • 4:32 דקות</p>
              </div>
              <CheckCircle className="w-5 h-5 text-indigo-600" />
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-xl p-3">
            <p className="text-sm text-blue-800 flex items-start gap-2">
              <Shield className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <span>הסרטונים מוצפנים ומאוחסנים בצורה מאובטחת</span>
            </p>
          </div>
        </div>
        
      </div>
    </div>
  );
}
