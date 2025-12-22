import React from 'react';
import { ChevronDown, FileText, Video, Film, Loader2, Sparkles } from 'lucide-react';

/**
 * ChildSpaceHeader - Living Dashboard Phase 2
 *
 * Shows child name and artifact badges in the header.
 * Tapping opens the full ChildSpace drawer.
 *
 * 🌟 Living Gestalt: Now receives childSpace prop from App state
 * instead of making separate API calls.
 *
 * Features:
 * - Compact header with child name
 * - Artifact slot badges (pills) showing status
 * - Expands to show full artifact drawer
 */

// Icon mapping for slots
const SLOT_ICONS = {
  current_report: FileText,
  filming_guidelines: Film,
  videos: Video,
  insights: Sparkles,
};

// Status colors
const STATUS_COLORS = {
  ready: 'bg-green-100 text-green-700 border-green-200',
  pending: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  generating: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  error: 'bg-red-100 text-red-700 border-red-200',
  default: 'bg-blue-100 text-blue-700 border-blue-200',
};

function SlotBadge({ badge, onClick }) {
  const Icon = SLOT_ICONS[badge.slot_id] || FileText;
  const colorClass = STATUS_COLORS[badge.status] || STATUS_COLORS.default;
  const isGenerating = badge.status === 'generating';

  const handleClick = (e) => {
    e.stopPropagation(); // Prevent triggering the parent expand click
    onClick(badge);
  };

  return (
    <button
      onClick={handleClick}
      className={`
        flex items-center gap-1.5 px-2.5 py-1 rounded-full border
        text-xs font-medium transition-all duration-200
        hover:scale-105 hover:shadow-sm
        ${colorClass}
      `}
    >
      {isGenerating ? (
        <Loader2 className="w-3.5 h-3.5 animate-spin" />
      ) : (
        <span className="text-sm">{badge.icon}</span>
      )}
      <span>{badge.text}</span>
    </button>
  );
}

export default function ChildSpaceHeader({
  familyId,
  childName,
  childSpace,  // 🌟 Living Gestalt: Receive child space data as prop
  onSlotClick,
  onExpandClick,
  isExpanded = false,  // Controlled from parent
  className = ''
}) {
  // Use badges directly from childSpace prop
  const badges = childSpace?.badges || [];

  // Handle badge click
  const handleBadgeClick = (badge) => {
    if (onSlotClick) {
      onSlotClick(badge.slot_id);
    }
  };

  // Handle expand click
  const handleExpandClick = () => {
    console.log('ChildSpaceHeader: handleExpandClick called, isExpanded:', isExpanded, '-> will pass:', !isExpanded);
    if (onExpandClick) {
      onExpandClick(!isExpanded);
    } else {
      console.warn('ChildSpaceHeader: onExpandClick is not defined');
    }
  };

  // Get display name from props or childSpace
  const displayName = childName || childSpace?.child_name;

  // Don't show if no child name and no badges
  if (!displayName && badges.length === 0) {
    return null;
  }

  return (
    <div className={`bg-white border-b border-gray-100 ${className}`}>
      {/* Main header row */}
      <div
        className="px-4 py-2 flex items-center justify-between cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={handleExpandClick}
      >
        {/* Child name and badges */}
        <div className="flex items-center gap-3 flex-1 min-w-0">
          {/* Child avatar/name */}
          {displayName && (
            <div className="flex items-center gap-2 group">
              <div className="w-8 h-8 bg-gradient-to-br from-purple-400 to-indigo-500 rounded-full flex items-center justify-center text-white font-bold text-sm shadow-sm transition-all duration-200 group-hover:scale-110 group-hover:shadow-md group-hover:ring-2 group-hover:ring-purple-200">
                {displayName.charAt(0)}
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-medium text-gray-700 hidden sm:inline">
                  {displayName}
                </span>
                {badges.length === 0 && (
                  <span className="text-[10px] text-gray-400 hidden sm:inline group-hover:text-purple-500 transition-colors">
                    לחצו לפרטים
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Badges */}
          <div className="flex items-center gap-2 overflow-x-auto hide-scrollbar">
            {badges.length > 0 ? (
              badges.map((badge) => (
                <SlotBadge
                  key={badge.slot_id}
                  badge={badge}
                  onClick={handleBadgeClick}
                />
              ))
            ) : null}
          </div>
        </div>

        {/* Expand indicator */}
        <ChevronDown
          className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${
            isExpanded ? 'rotate-180' : ''
          }`}
        />
      </div>

      {/* Hide scrollbar CSS */}
      <style>{`
        .hide-scrollbar::-webkit-scrollbar {
          display: none;
        }
        .hide-scrollbar {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
      `}</style>
    </div>
  );
}
