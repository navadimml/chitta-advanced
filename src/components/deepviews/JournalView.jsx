import React, { useState } from 'react';
import { X, Book, Trash2, CheckCircle } from 'lucide-react';

export default function JournalView({ onClose, journalEntries = [], onCreateJournalEntry, onDeleteJournalEntry }) {
  const [entryText, setEntryText] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('תצפית');
  const [isSaving, setIsSaving] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  const handleSave = async () => {
    if (!entryText.trim()) return;

    setIsSaving(true);
    const response = await onCreateJournalEntry(entryText, selectedStatus);

    if (response.success) {
      setEntryText('');
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 2000);
    }
    setIsSaving(false);
  };

  const handleDelete = async (entryId) => {
    if (window.confirm('האם את בטוחה שאת רוצה למחוק את הרשומה?')) {
      await onDeleteJournalEntry(entryId);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'התקדמות':
        return { bg: 'bg-green-100', text: 'text-green-700' };
      case 'תצפית':
        return { bg: 'bg-blue-100', text: 'text-blue-700' };
      case 'אתגר':
        return { bg: 'bg-orange-100', text: 'text-orange-700' };
      default:
        return { bg: 'bg-gray-100', text: 'text-gray-700' };
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end md:items-center justify-center p-4 animate-backdropIn" onClick={onClose}>
      <div className="absolute inset-0 bg-black/50" />
      <div className="relative bg-white rounded-t-3xl md:rounded-3xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col animate-panelUp" onClick={(e) => e.stopPropagation()}>

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

            {/* Status selector */}
            <div className="mb-3 flex gap-2">
              <button
                onClick={() => setSelectedStatus('התקדמות')}
                className={`px-3 py-1 rounded-full text-xs font-semibold transition ${selectedStatus === 'התקדמות' ? 'bg-green-500 text-white' : 'bg-green-100 text-green-700'}`}
              >
                התקדמות
              </button>
              <button
                onClick={() => setSelectedStatus('תצפית')}
                className={`px-3 py-1 rounded-full text-xs font-semibold transition ${selectedStatus === 'תצפית' ? 'bg-blue-500 text-white' : 'bg-blue-100 text-blue-700'}`}
              >
                תצפית
              </button>
              <button
                onClick={() => setSelectedStatus('אתגר')}
                className={`px-3 py-1 rounded-full text-xs font-semibold transition ${selectedStatus === 'אתגר' ? 'bg-orange-500 text-white' : 'bg-orange-100 text-orange-700'}`}
              >
                אתגר
              </button>
            </div>

            <textarea
              value={entryText}
              onChange={(e) => setEntryText(e.target.value)}
              className="w-full h-32 p-3 border border-amber-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent resize-none text-sm"
              placeholder="למשל: 'היום יוני אמר משפט שלם בפעם הראשונה!' או 'שמתי לב שהוא מתקשה עם מרקמים חדשים באוכל...'"
              dir="rtl"
            ></textarea>

            {showSuccess && (
              <div className="mt-2 bg-green-100 text-green-800 p-2 rounded-lg text-sm flex items-center gap-2">
                <CheckCircle className="w-4 h-4" />
                הרשומה נשמרה בהצלחה!
              </div>
            )}

            <button
              onClick={handleSave}
              disabled={isSaving || !entryText.trim()}
              className="mt-2 w-full bg-gradient-to-r from-amber-500 to-orange-500 text-white py-2 rounded-lg font-bold hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSaving ? 'שומר...' : 'שמירת רשומה'}
            </button>
          </div>

          <div className="space-y-3">
            <h5 className="font-bold text-gray-700 text-sm">רשומות אחרונות ({journalEntries.length})</h5>

            {journalEntries.length === 0 ? (
              <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 text-center">
                <p className="text-gray-500 text-sm">אין רשומות עדיין. הוסיפי את הרשומה הראשונה!</p>
              </div>
            ) : (
              journalEntries.map((entry) => {
                const colors = getStatusColor(entry.status);
                return (
                  <div key={entry.id} className="bg-white border border-gray-200 rounded-xl p-3 hover:shadow-md transition group">
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-xs text-gray-500">{entry.timestamp}</span>
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-1 ${colors.bg} ${colors.text} rounded-full text-xs font-semibold`}>
                          {entry.status}
                        </span>
                        <button
                          onClick={() => handleDelete(entry.id)}
                          className="opacity-0 group-hover:opacity-100 transition p-1 hover:bg-red-100 rounded-full"
                          title="מחיקת רשומה"
                        >
                          <Trash2 className="w-4 h-4 text-red-600" />
                        </button>
                      </div>
                    </div>
                    <p className="text-sm text-gray-800">
                      {entry.text}
                    </p>
                  </div>
                );
              })
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
