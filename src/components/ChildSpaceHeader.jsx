import React, { useState, useEffect } from 'react';
import { ChevronDown, FileText, Video, BookOpen, Film, Loader2 } from 'lucide-react';
import { api } from '../api/client';

/**
 * ChildSpaceHeader - Living Dashboard Phase 2
 *
 * Shows child name and artifact badges in the header.
 * Tapping opens the full ChildSpace drawer.
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
  journal: BookOpen,
};

// Status colors
const STATUS_COLORS = {
  ready: 'bg-green-100 text-green-700 border-green-200',
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
  onSlotClick,
  onExpandClick,
  className = ''
}) {
  const [badges, setBadges] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isExpanded, setIsExpanded] = useState(false);

  // Fetch header badges
  useEffect(() => {
    async function fetchBadges() {
      if (!familyId) return;

      try {
        setIsLoading(true);
        const response = await api.getChildSpaceHeader(familyId);
        setBadges(response.badges || []);
      } catch (error) {
        console.error('Error fetching child space header:', error);
        setBadges([]);
      } finally {
        setIsLoading(false);
      }
    }

    fetchBadges();
  }, [familyId]);

  // Handle badge click
  const handleBadgeClick = (badge) => {
    if (onSlotClick) {
      onSlotClick(badge.slot_id);
    }
  };

  // Handle expand click
  const handleExpandClick = () => {
    setIsExpanded(!isExpanded);
    if (onExpandClick) {
      onExpandClick(!isExpanded);
    }
  };

  // Don't show if no child name yet
  if (!childName && badges.length === 0) {
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
          {childName && (
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-purple-400 to-indigo-500 rounded-full flex items-center justify-center text-white font-bold text-sm shadow-sm">
                {childName.charAt(0)}
              </div>
              <span className="text-sm font-medium text-gray-700 hidden sm:inline">
                {childName}
              </span>
            </div>
          )}

          {/* Badges */}
          <div className="flex items-center gap-2 overflow-x-auto hide-scrollbar">
            {isLoading ? (
              <div className="flex items-center gap-1 text-gray-400 text-xs">
                <Loader2 className="w-3 h-3 animate-spin" />
                <span>טוען...</span>
              </div>
            ) : badges.length > 0 ? (
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
