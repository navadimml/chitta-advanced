import React, { useState } from 'react';
import { X, Play, Pause, Shield, CheckCircle, Trash2 } from 'lucide-react';

export default function VideoGalleryView({ onClose, videos = [], onDeleteVideo }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [selectedVideo, setSelectedVideo] = useState(videos[0] || null);

  const handleDelete = async (videoId) => {
    if (window.confirm('האם את בטוחה שאת רוצה למחוק את הסרטון?')) {
      await onDeleteVideo(videoId);
      // If the deleted video was selected, select another one
      if (selectedVideo && selectedVideo.id === videoId) {
        const remainingVideos = videos.filter(v => v.id !== videoId);
        setSelectedVideo(remainingVideos[0] || null);
      }
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end md:items-center justify-center p-4 animate-backdropIn" onClick={onClose}>
      <div className="absolute inset-0 bg-black/50" />
      <div className="relative bg-white rounded-t-3xl md:rounded-3xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col animate-panelUp" onClick={(e) => e.stopPropagation()}>

        <div className="bg-gradient-to-r from-indigo-500 to-purple-500 text-white p-5 flex items-center justify-between">
          <h3 className="text-lg font-bold">הסרטונים של יוני</h3>
          <button onClick={onClose} className="p-2 hover:bg-white hover:bg-opacity-20 rounded-full transition">
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-xl p-4">
            <h4 className="font-bold text-purple-900 mb-2">{videos.length} סרטונים הועלו</h4>
            <p className="text-sm text-purple-800">
              הסרטונים נשמרים בצורה מאובטחת ומוצפנת
            </p>
          </div>

          {videos.length === 0 ? (
            <div className="bg-gray-50 border border-gray-200 rounded-xl p-8 text-center">
              <Play className="w-16 h-16 mx-auto mb-3 text-gray-400" />
              <p className="text-gray-500 font-bold mb-1">אין סרטונים עדיין</p>
              <p className="text-gray-400 text-sm">העלאת סרטונים תעזור לנתח את התנהגות יוני</p>
            </div>
          ) : (
            <>
            {selectedVideo && (
              <div className="bg-black rounded-xl overflow-hidden">
                <div className="aspect-video bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center relative">
                  <div className="text-center text-white">
                    <Play className="w-16 h-16 mx-auto mb-2 opacity-80" />
                    <p className="text-sm opacity-70">{selectedVideo.title}</p>
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
                      <span className="text-white text-sm" dir="ltr">{selectedVideo.duration}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div className="space-y-2">
              <h5 className="font-bold text-gray-700 text-sm">כל הסרטונים</h5>
              {videos.map((video) => {
                const isSelected = selectedVideo && selectedVideo.id === video.id;
                return (
                  <div
                    key={video.id}
                    className={`${isSelected ? 'bg-indigo-50 border-2 border-indigo-300' : 'bg-white border border-gray-200'} rounded-xl p-3 flex items-center gap-3 hover:shadow-md transition group cursor-pointer`}
                    onClick={() => setSelectedVideo(video)}
                  >
                    <div className={`w-20 h-14 ${isSelected ? 'bg-indigo-200' : 'bg-gray-200'} rounded-lg flex items-center justify-center flex-shrink-0`}>
                      <Play className={`w-6 h-6 ${isSelected ? 'text-indigo-600' : 'text-gray-600'}`} />
                    </div>
                    <div className="flex-1">
                      <h5 className={`font-bold ${isSelected ? 'text-indigo-900' : 'text-gray-900'} text-sm`}>{video.title}</h5>
                      <p className={`text-xs ${isSelected ? 'text-indigo-700' : 'text-gray-600'}`}>
                        {video.date} • {video.duration}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {isSelected && <CheckCircle className="w-5 h-5 text-indigo-600" />}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(video.id);
                        }}
                        className="opacity-0 group-hover:opacity-100 transition p-2 hover:bg-red-100 rounded-full"
                        title="מחיקת סרטון"
                      >
                        <Trash2 className="w-4 h-4 text-red-600" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </>
          )}

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
