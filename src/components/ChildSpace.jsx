import React, { useState, useEffect } from 'react';
import {
  X, FileText, Video, BookOpen, Film, Clock, ChevronRight,
  Loader2, Download, Eye, Plus, History, ArrowLeft
} from 'lucide-react';
import { api } from '../api/client';

/**
 * History Modal - Shows version history for a slot
 */
function HistoryModal({ slot, onClose, onSelectVersion }) {
  if (!slot || !slot.history || slot.history.length === 0) return null;

  return (
    <div className="fixed inset-0 z-60 flex items-center justify-center p-4 animate-backdropIn">
      <div className="absolute inset-0 bg-black/50" />
      <div className="relative bg-white rounded-2xl shadow-2xl max-w-md w-full max-h-[80vh] overflow-hidden animate-panelUp">
        {/* Header */}
        <div className="bg-gradient-to-r from-indigo-500 to-purple-500 text-white p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <History className="w-5 h-5" />
              <h3 className="font-bold text-lg">היסטוריית גרסאות</h3>
            </div>
            <button
              onClick={onClose}
              className="p-1 hover:bg-white/20 rounded-full transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          <p className="text-sm text-indigo-100 mt-1">{slot.slot_name}</p>
        </div>

        {/* Current Version */}
        <div className="p-4 border-b border-gray-200">
          <div className="text-xs text-gray-500 mb-2">גרסה נוכחית</div>
          <div
            className="p-3 bg-green-50 border-2 border-green-300 rounded-lg cursor-pointer hover:bg-green-100 transition"
            onClick={() => {
              onSelectVersion(slot.current);
              onClose();
            }}
          >
            <div className="flex items-center justify-between">
              <span className="font-medium text-green-800">
                {slot.current?.name || 'דוח נוכחי'}
              </span>
              <span className="text-xs text-green-600 bg-green-200 px-2 py-0.5 rounded-full">
                פעיל
              </span>
            </div>
            {slot.current?.created_at && (
              <div className="text-xs text-green-600 mt-1">
                {new Date(slot.current.created_at).toLocaleDateString('he-IL', {
                  day: 'numeric',
                  month: 'long',
                  year: 'numeric'
                })}
              </div>
            )}
            {slot.current?.preview && (
              <p className="text-sm text-gray-600 mt-2 line-clamp-2">{slot.current.preview}</p>
            )}
          </div>
        </div>

        {/* History */}
        <div className="p-4 max-h-60 overflow-y-auto">
          <div className="text-xs text-gray-500 mb-2">גרסאות קודמות</div>
          <div className="space-y-2">
            {slot.history.map((item, idx) => (
              <div
                key={item.artifact_id || idx}
                className="p-3 bg-gray-50 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-100 hover:border-gray-300 transition"
                onClick={() => {
                  onSelectVersion(item);
                  onClose();
                }}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium text-gray-700">
                    {item.name || `גרסה ${slot.history.length - idx}`}
                  </span>
                  <ArrowLeft className="w-4 h-4 text-gray-400" />
                </div>
                {item.created_at && (
                  <div className="text-xs text-gray-500 mt-1">
                    {new Date(item.created_at).toLocaleDateString('he-IL', {
                      day: 'numeric',
                      month: 'long',
                      year: 'numeric'
                    })}
                  </div>
                )}
                {item.preview && (
                  <p className="text-sm text-gray-500 mt-2 line-clamp-2">{item.preview}</p>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 bg-gray-50 border-t border-gray-200">
          <button
            onClick={onClose}
            className="w-full py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 font-medium rounded-lg transition"
          >
            סגור
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * ChildSpace - Living Dashboard Phase 2
 *
 * Full-screen drawer showing all artifact slots.
 * "Daniel's Space" - quick access to all child artifacts.
 *
 * Features:
 * - Grid of slot cards
 * - Each slot shows current artifact or collection summary
 * - Actions: view, download, history
 * - Collection slots show item count
 */

// Icon mapping for slots
const SLOT_ICONS = {
  current_report: FileText,
  filming_guidelines: Film,
  videos: Video,
  journal: BookOpen,
};

// Action handlers
const SLOT_ACTIONS = {
  current_report: { primary: 'view_report', secondary: 'download_report' },
  filming_guidelines: { primary: 'view_guidelines' },
  videos: { primary: 'view_videos', secondary: 'upload_video' },
  journal: { primary: 'view_journal', secondary: 'add_journal_entry' },
};

function SlotCard({ slot, onAction, onHistoryClick }) {
  const Icon = SLOT_ICONS[slot.slot_id] || FileText;
  const actions = SLOT_ACTIONS[slot.slot_id] || {};

  const hasContent = slot.has_content;
  const isGenerating = slot.is_generating;
  const hasError = slot.has_error;

  // Determine card state styling
  let cardStyle = 'bg-white border-gray-200';
  let statusBadge = null;

  if (isGenerating) {
    cardStyle = 'bg-yellow-50 border-yellow-200';
    statusBadge = (
      <span className="flex items-center gap-1 text-xs text-yellow-600 bg-yellow-100 px-2 py-0.5 rounded-full">
        <Loader2 className="w-3 h-3 animate-spin" />
        מכין...
      </span>
    );
  } else if (hasError) {
    cardStyle = 'bg-red-50 border-red-200';
    statusBadge = (
      <span className="text-xs text-red-600 bg-red-100 px-2 py-0.5 rounded-full">
        שגיאה
      </span>
    );
  } else if (hasContent) {
    cardStyle = 'bg-green-50 border-green-200';
    statusBadge = (
      <span className="text-xs text-green-600 bg-green-100 px-2 py-0.5 rounded-full">
        מוכן
      </span>
    );
  }

  // Handle primary action
  const handlePrimaryAction = () => {
    if (actions.primary && onAction) {
      onAction(actions.primary, slot);
    }
  };

  return (
    <div
      className={`
        rounded-xl border-2 p-4 transition-all duration-200
        hover:shadow-md cursor-pointer
        ${cardStyle}
      `}
      onClick={handlePrimaryAction}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{slot.icon}</span>
          <div>
            <h3 className="font-semibold text-gray-800">{slot.slot_name}</h3>
            {slot.slot_name_en && (
              <p className="text-xs text-gray-500">{slot.slot_name_en}</p>
            )}
          </div>
        </div>
        {statusBadge}
      </div>

      {/* Content preview */}
      <div className="mb-3">
        {slot.is_collection ? (
          // Collection slot
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <span className="font-medium text-lg">{slot.item_count}</span>
            <span>{slot.item_count === 1 ? 'פריט' : 'פריטים'}</span>
          </div>
        ) : slot.current ? (
          // Single item slot
          <div className="text-sm text-gray-600">
            {slot.current.preview ? (
              <p className="line-clamp-2">{slot.current.preview}</p>
            ) : (
              <p className="italic">לחץ לצפייה</p>
            )}
          </div>
        ) : (
          // Empty slot
          <p className="text-sm text-gray-400 italic">ריק</p>
        )}
      </div>

      {/* Footer with actions */}
      <div className="flex items-center justify-between">
        {/* Last updated */}
        {slot.last_updated && (
          <div className="flex items-center gap-1 text-xs text-gray-400">
            <Clock className="w-3 h-3" />
            <span>
              {new Date(slot.last_updated).toLocaleDateString('he-IL')}
            </span>
          </div>
        )}

        {/* Action buttons */}
        <div className="flex items-center gap-2">
          {/* History button for versioned slots */}
          {slot.history && slot.history.length > 0 && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onHistoryClick && onHistoryClick(slot);
              }}
              className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition"
              title="היסטוריית גרסאות"
            >
              <History className="w-4 h-4" />
            </button>
          )}

          {/* Secondary action */}
          {actions.secondary && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onAction && onAction(actions.secondary, slot);
              }}
              className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition"
            >
              {actions.secondary.includes('download') ? (
                <Download className="w-4 h-4" />
              ) : actions.secondary.includes('upload') || actions.secondary.includes('add') ? (
                <Plus className="w-4 h-4" />
              ) : (
                <Eye className="w-4 h-4" />
              )}
            </button>
          )}

          <ChevronRight className="w-4 h-4 text-gray-400" />
        </div>
      </div>
    </div>
  );
}

export default function ChildSpace({
  familyId,
  isOpen,
  onClose,
  onSlotAction,
  childName
}) {
  const [space, setSpace] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [historySlot, setHistorySlot] = useState(null); // Slot to show history for

  // Fetch full child space
  useEffect(() => {
    async function fetchSpace() {
      if (!familyId || !isOpen) return;

      try {
        setIsLoading(true);
        setError(null);
        const response = await api.getChildSpace(familyId);
        setSpace(response);
      } catch (err) {
        console.error('Error fetching child space:', err);
        setError('שגיאה בטעינת המרחב');
      } finally {
        setIsLoading(false);
      }
    }

    fetchSpace();
  }, [familyId, isOpen]);

  // Handle slot action
  const handleAction = (action, slot) => {
    if (onSlotAction) {
      onSlotAction(action, slot);
    }
  };

  // Handle history click
  const handleHistoryClick = (slot) => {
    setHistorySlot(slot);
  };

  // Handle version selection from history
  const handleSelectVersion = (item) => {
    // Open the artifact in LivingDocument view
    if (onSlotAction && item?.artifact_id) {
      onSlotAction('view_artifact', { artifact_id: item.artifact_id, slot: historySlot });
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 animate-backdropIn">
      <div className="absolute inset-0 bg-black/50" />
      <div
        className="absolute inset-x-0 bottom-0 top-16 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-t-3xl shadow-2xl animate-panelUp overflow-hidden"
      >
        {/* Header */}
        <div className="sticky top-0 bg-white/90 backdrop-blur-sm border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-purple-400 to-indigo-500 rounded-full flex items-center justify-center text-white font-bold text-xl shadow-md">
              {(space?.child_name || childName || 'ד').charAt(0)}
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-800">
                המרחב של {space?.child_name || childName || 'הילד'}
              </h2>
              <p className="text-sm text-gray-500">כל המסמכים והפעילויות</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-full transition"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto h-full pb-24">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <p className="text-red-500">{error}</p>
              <button
                onClick={() => window.location.reload()}
                className="mt-4 px-4 py-2 bg-indigo-500 text-white rounded-lg hover:bg-indigo-600 transition"
              >
                נסה שוב
              </button>
            </div>
          ) : space?.slots ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {space.slots.map((slot) => (
                <SlotCard
                  key={slot.slot_id}
                  slot={slot}
                  onAction={handleAction}
                  onHistoryClick={handleHistoryClick}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              <p>אין עדיין מסמכים במרחב</p>
            </div>
          )}
        </div>
      </div>

      {/* History Modal */}
      {historySlot && (
        <HistoryModal
          slot={historySlot}
          onClose={() => setHistorySlot(null)}
          onSelectVersion={handleSelectVersion}
        />
      )}
    </div>
  );
}
