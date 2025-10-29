import React, { useState, useRef } from 'react';
import { X, Video, Upload, Camera, Play, Pause, CheckCircle, AlertCircle, Loader } from 'lucide-react';

export default function VideoUploadView({ onClose, scenarioData, videoGuidelines, onCreateVideo }) {
  const [uploadStatus, setUploadStatus] = useState('idle'); // idle, uploading, success, error
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [videoPreview, setVideoPreview] = useState(null);
  const [selectedGuideline, setSelectedGuideline] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [videoTitle, setVideoTitle] = useState('');
  const [videoDescription, setVideoDescription] = useState('');
  const fileInputRef = useRef(null);
  const videoRef = useRef(null);

  // Simulate file upload
  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file && file.type.startsWith('video/')) {
      setVideoPreview(URL.createObjectURL(file));
      setVideoTitle(file.name.replace(/\.[^/.]+$/, '')); // Remove file extension
      simulateUpload(file);
    }
  };

  // Simulate upload progress
  const simulateUpload = async (file) => {
    setUploadStatus('uploading');
    setUploadProgress(0);

    const interval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        return prev + 10;
      });
    }, 300);

    // Wait for upload to complete
    await new Promise(resolve => setTimeout(resolve, 3000));

    // Save the video to the app state
    if (onCreateVideo) {
      const videoData = {
        title: videoTitle || 'סרטון חדש',
        description: videoDescription || 'סרטון שהועלה',
        duration: '0:00', // In a real app, would get this from the video file
        url: videoPreview
      };
      await onCreateVideo(videoData);
    }

    setUploadStatus('success');
  };

  // Handle recording start/stop (simplified simulation)
  const toggleRecording = async () => {
    if (!isRecording) {
      setIsRecording(true);
      setRecordingTime(0);

      // Simulate recording timer
      const timer = setInterval(() => {
        setRecordingTime(prev => {
          if (prev >= 300) { // Max 5 minutes
            clearInterval(timer);
            setIsRecording(false);
            return prev;
          }
          return prev + 1;
        });
      }, 1000);
    } else {
      setIsRecording(false);

      // Save the recorded video
      if (onCreateVideo) {
        const mins = Math.floor(recordingTime / 60);
        const secs = recordingTime % 60;
        const duration = `${mins}:${secs.toString().padStart(2, '0')}`;

        const videoData = {
          title: videoTitle || 'סרטון מוקלט',
          description: videoDescription || 'סרטון שצולם',
          duration,
          url: null
        };
        await onCreateVideo(videoData);
      }

      setUploadStatus('success');
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Handler to select a guideline and auto-fill form
  const handleSelectGuideline = (scenario) => {
    setSelectedGuideline(scenario);
    setVideoTitle(scenario.title);
    setVideoDescription(scenario.description);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-end md:items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-t-3xl md:rounded-3xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col animate-slideUp" onClick={(e) => e.stopPropagation()}>
        
        <div className="bg-gradient-to-r from-indigo-500 to-purple-500 text-white p-5 flex items-center justify-between">
          <h3 className="text-lg font-bold">צילום והעלאת וידאו</h3>
          <button onClick={onClose} className="p-2 hover:bg-white hover:bg-opacity-20 rounded-full transition">
            <X className="w-6 h-6" />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-5 space-y-4">

          {/* Video Guidelines Section - Brief Summary with Click for Details */}
          {videoGuidelines && videoGuidelines.scenarios && videoGuidelines.scenarios.length > 0 && !selectedGuideline && (
            <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-xl p-4">
              <h5 className="font-bold text-purple-900 mb-3 flex items-center gap-2">
                <Video className="w-5 h-5" />
                הוראות צילום מותאמות אישית
              </h5>

              {/* Why These Scenarios */}
              {videoGuidelines.why_these_scenarios && (
                <div className="bg-white/70 rounded-lg p-3 mb-4 border border-purple-200">
                  <p className="text-sm text-purple-900 leading-relaxed">
                    {videoGuidelines.why_these_scenarios}
                  </p>
                </div>
              )}

              <div className="space-y-2">
                {videoGuidelines.scenarios.map((scenario, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSelectGuideline(scenario)}
                    className="w-full bg-white border-2 border-purple-200 hover:border-purple-400 rounded-lg p-3 text-right transition-all hover:shadow-md"
                  >
                    <div className="flex items-start gap-3">
                      <span className="w-7 h-7 bg-purple-500 text-white rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0">
                        {idx + 1}
                      </span>
                      <div className="flex-1">
                        <h6 className="font-bold text-purple-900 text-sm mb-1">{scenario.title}</h6>
                        <p className="text-xs text-purple-700 leading-relaxed">{scenario.description}</p>
                        <div className="flex items-center gap-2 mt-2">
                          {scenario.priority === 'essential' && (
                            <span className="px-2 py-0.5 bg-orange-100 text-orange-700 rounded-full text-xs font-semibold">
                              חיוני
                            </span>
                          )}
                          <span className="text-xs text-purple-600 font-semibold">
                            לחץ לפרטים מלאים →
                          </span>
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Detailed Guideline View */}
          {selectedGuideline && (
            <div className="bg-white border-2 border-purple-300 rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between mb-4">
                <h5 className="font-bold text-purple-900 text-lg">{selectedGuideline.title}</h5>
                <button
                  onClick={() => setSelectedGuideline(null)}
                  className="text-purple-600 hover:text-purple-800 text-sm font-semibold"
                >
                  ← חזרה לרשימה
                </button>
              </div>

              {/* Why I Chose This - New Section */}
              {selectedGuideline.why_i_chose_this && (
                <div className="bg-gradient-to-r from-pink-50 to-purple-50 border-2 border-pink-200 rounded-lg p-4">
                  <h6 className="font-bold text-pink-900 mb-2 flex items-center gap-2">
                    <CheckCircle className="w-5 h-5" />
                    למה בחרתי את התרחיש הזה בשבילך?
                  </h6>
                  <p className="text-sm text-pink-900 leading-relaxed">
                    {selectedGuideline.why_i_chose_this}
                  </p>
                </div>
              )}

              {/* Detailed Description */}
              {selectedGuideline.detailed_description && (
                <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
                  <h6 className="font-bold text-indigo-900 mb-2 flex items-center gap-2">
                    <Video className="w-4 h-4" />
                    מה לצלם?
                  </h6>
                  <p className="text-sm text-indigo-800 whitespace-pre-line leading-relaxed">
                    {selectedGuideline.detailed_description}
                  </p>
                </div>
              )}

              {/* Detailed Rationale */}
              {selectedGuideline.detailed_rationale && (
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                  <h6 className="font-bold text-purple-900 mb-2">למה זה חשוב?</h6>
                  <p className="text-sm text-purple-800 whitespace-pre-line leading-relaxed">
                    {selectedGuideline.detailed_rationale}
                  </p>
                </div>
              )}

              {/* Example Situations */}
              {selectedGuideline.example_situations && selectedGuideline.example_situations.length > 0 && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h6 className="font-bold text-blue-900 mb-2">דוגמאות לסיטואציות:</h6>
                  <ul className="space-y-2">
                    {selectedGuideline.example_situations.map((example, idx) => (
                      <li key={idx} className="text-sm text-blue-800 flex items-start gap-2">
                        <span className="text-blue-500 font-bold">•</span>
                        <span>{example}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Filming Tips */}
              {selectedGuideline.filming_tips && selectedGuideline.filming_tips.length > 0 && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <h6 className="font-bold text-green-900 mb-2">טיפים לצילום:</h6>
                  <ul className="space-y-2">
                    {selectedGuideline.filming_tips.map((tip, idx) => (
                      <li key={idx} className="text-sm text-green-800 flex items-start gap-2">
                        <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                        <span>{tip}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* What to Look For */}
              {selectedGuideline.what_to_look_for && selectedGuideline.what_to_look_for.length > 0 && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                  <h6 className="font-bold text-amber-900 mb-2">על מה לשים לב?</h6>
                  <ul className="space-y-2">
                    {selectedGuideline.what_to_look_for.map((item, idx) => (
                      <li key={idx} className="text-sm text-amber-800 flex items-start gap-2">
                        <span className="text-amber-600 font-bold">▸</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Confirmation Message */}
              <div className="bg-gradient-to-r from-green-50 to-teal-50 border-2 border-green-300 rounded-lg p-4">
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-6 h-6 text-green-600" />
                  <div>
                    <h6 className="font-bold text-green-900">פרטי הטופס מולאו אוטומטית</h6>
                    <p className="text-sm text-green-700">כותרת ותיאור הסרטון הוגדרו לפי ההוראה הזו. גללי למטה להעלות את הסרטון!</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Video Preview Area */}
          {(videoPreview || isRecording) && (
            <div className="bg-black rounded-xl overflow-hidden">
              <div className="aspect-video relative">
                {videoPreview ? (
                  <video 
                    ref={videoRef}
                    src={videoPreview} 
                    controls 
                    className="w-full h-full"
                  />
                ) : (
                  <div className="w-full h-full bg-gradient-to-br from-red-900 to-red-700 flex items-center justify-center">
                    <div className="text-center text-white">
                      <div className="w-16 h-16 mx-auto mb-3 bg-red-500 rounded-full animate-pulse flex items-center justify-center">
                        <Video className="w-8 h-8" />
                      </div>
                      <p className="text-2xl font-bold">{formatTime(recordingTime)}</p>
                      <p className="text-sm opacity-80">מצלם...</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Upload Status */}
          {uploadStatus === 'uploading' && (
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
              <div className="flex items-center gap-3 mb-3">
                <Loader className="w-5 h-5 text-blue-600 animate-spin" />
                <div className="flex-1">
                  <h5 className="font-bold text-blue-900 text-sm">מעלה וידאו...</h5>
                  <p className="text-xs text-blue-700">{uploadProgress}% הושלם</p>
                </div>
              </div>
              <div className="w-full bg-blue-200 h-2 rounded-full overflow-hidden">
                <div 
                  className="bg-blue-600 h-full rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          {uploadStatus === 'success' && (
            <div className="bg-green-50 border border-green-200 rounded-xl p-4 space-y-3">
              <div className="flex items-center gap-3">
                <CheckCircle className="w-6 h-6 text-green-600" />
                <div>
                  <h5 className="font-bold text-green-900">הוידאו הועלה בהצלחה! 🎉</h5>
                  <p className="text-sm text-green-700">הוידאו נשמר ומוכן לניתוח</p>
                </div>
              </div>

              {/* What happens next */}
              <div className="bg-white border-l-4 border-green-400 rounded-lg p-3">
                <h6 className="font-bold text-green-900 text-sm mb-2">מה קורה עכשיו?</h6>
                <div className="text-xs text-green-800 space-y-1.5 leading-relaxed">
                  <p>✓ הסרטון נשמר במערכת</p>
                  <p>✓ תוכלי להעלות עוד סרטונים או לסגור את החלון</p>
                  <p>✓ כשתסיימי להעלות את כל הסרטונים, אנתח אותם (לוקח כ-24 שעות)</p>
                  <p>✓ תקבלי התראה כשהניתוח מוכן ואוכל ליצור עבורך דוחות מפורטים</p>
                </div>
              </div>
            </div>
          )}

          {uploadStatus === 'error' && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4">
              <div className="flex items-center gap-3">
                <AlertCircle className="w-6 h-6 text-red-600" />
                <div>
                  <h5 className="font-bold text-red-900">שגיאה בהעלאה</h5>
                  <p className="text-sm text-red-700">נסי שוב או בחרי קובץ אחר</p>
                </div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          {uploadStatus === 'idle' && (
            <>
              {/* Video metadata inputs */}
              <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 space-y-3">
                <h5 className="font-bold text-gray-900 text-sm">פרטי הסרטון (אופציונלי)</h5>
                <div>
                  <label className="text-xs text-gray-600 block mb-1">כותרת</label>
                  <input
                    type="text"
                    value={videoTitle}
                    onChange={(e) => setVideoTitle(e.target.value)}
                    placeholder="למשל: משחק חופשי, זמן ארוחה..."
                    className="w-full p-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    dir="rtl"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-600 block mb-1">תיאור</label>
                  <input
                    type="text"
                    value={videoDescription}
                    onChange={(e) => setVideoDescription(e.target.value)}
                    placeholder="תיאור קצר של הסרטון"
                    className="w-full p-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    dir="rtl"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                {/* Record Button */}
                <button
                  onClick={toggleRecording}
                  className="bg-gradient-to-r from-red-500 to-pink-500 text-white p-4 rounded-xl font-bold hover:shadow-lg transition flex flex-col items-center gap-2"
                >
                  <Camera className="w-8 h-8" />
                  <span>צילום וידאו</span>
                </button>

                {/* Upload Button */}
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="bg-gradient-to-r from-blue-500 to-cyan-500 text-white p-4 rounded-xl font-bold hover:shadow-lg transition flex flex-col items-center gap-2"
                >
                  <Upload className="w-8 h-8" />
                  <span>העלאת קובץ</span>
                </button>
              </div>

              <input
                ref={fileInputRef}
                type="file"
                accept="video/*"
                onChange={handleFileSelect}
                className="hidden"
              />
            </>
          )}

          {/* Recording Controls */}
          {isRecording && (
            <button
              onClick={toggleRecording}
              className="w-full bg-red-600 text-white py-4 rounded-xl font-bold hover:bg-red-700 transition flex items-center justify-center gap-2"
            >
              <Pause className="w-5 h-5" />
              עצור צילום
            </button>
          )}

          {/* Tips Section */}
          <div className="bg-purple-50 border border-purple-200 rounded-xl p-4">
            <h5 className="font-bold text-purple-900 mb-2 flex items-center gap-2">
              <Video className="w-5 h-5" />
              טיפים לצילום איכותי
            </h5>
            <div className="space-y-2 text-sm text-purple-800">
              <div className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <span>ודאי שהתאורה טובה - לא נגד האור</span>
              </div>
              <div className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <span>השמע צריך להיות ברור</span>
              </div>
              <div className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <span>צלמי 3-5 דקות - לא צריך יותר</span>
              </div>
              <div className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <span>השאירי את המצלמה יציבה ככל האפשר</span>
              </div>
            </div>
          </div>

          {/* Privacy Note */}
          <div className="bg-green-50 border border-green-200 rounded-xl p-3">
            <p className="text-sm text-green-800 flex items-start gap-2">
              <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <span>הוידאו מוצפן ומאוחסן בצורה מאובטחת לחלוטין</span>
            </p>
          </div>

          {/* Success Actions */}
          {uploadStatus === 'success' && (
            <div className="grid grid-cols-2 gap-2">
              <button 
                onClick={onClose}
                className="bg-gradient-to-r from-indigo-500 to-purple-500 text-white py-3 px-4 rounded-xl font-bold hover:shadow-lg transition"
              >
                סגור
              </button>
              <button 
                onClick={() => {
                  setUploadStatus('idle');
                  setVideoPreview(null);
                }}
                className="bg-white border-2 border-indigo-500 text-indigo-600 py-3 px-4 rounded-xl font-bold hover:bg-indigo-50 transition"
              >
                העלה עוד
              </button>
            </div>
          )}
        </div>
        
      </div>
    </div>
  );
}
