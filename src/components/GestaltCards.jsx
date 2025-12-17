import React, { useState } from 'react';
import {
  Video,
  FileText,
  Eye,
  CheckCircle2,
  Loader2,
  Lightbulb,
  Camera,
  X,
  Brain,
  Wand2,
  AlertTriangle,
  Upload,
  BellOff,
  XCircle,
  HelpCircle,
} from 'lucide-react';

/**
 * Living Gestalt Cards - Context cards for the video workflow
 *
 * CARD PHILOSOPHY: Two Categories
 * ================================
 * Context cards are for CYCLE-BOUND artifacts - things that emerge from
 * exploration cycles and need parent action or acknowledgment.
 *
 * HOLISTIC artifacts (synthesis, summaries, essence) are NOT cards -
 * they're pulled by the user from ChildSpace when ready.
 *
 * ACTION CARDS (need parent decision/action):
 * - video_suggestion: Hypothesis formed, video would help, needs consent
 * - video_guidelines_generating: Guidelines being created
 * - video_guidelines_ready: Guidelines ready, needs upload
 * - video_uploaded: Video ready for analysis
 * - video_analyzing: Analysis in progress
 * - video_validation_failed: Video didn't match request
 *
 * FEEDBACK CARDS (just acknowledge, dismiss only):
 * - video_analyzed: Analysis complete, insights integrated into understanding
 */

// Card type configurations with icons, colors, and styling
const CARD_CONFIGS = {
  video_suggestion: {
    icon: Video,
    accentColor: 'violet',
    borderColor: 'border-violet-200',
    bgColor: 'bg-violet-50/50',
    iconBg: 'bg-violet-100',
    iconColor: 'text-violet-600',
    buttonBg: 'bg-violet-600 hover:bg-violet-700',
  },
  baseline_video_suggestion: {
    icon: Eye,  // Discovery/seeing the child
    accentColor: 'sky',
    borderColor: 'border-sky-200',
    bgColor: 'bg-sky-50/50',
    iconBg: 'bg-sky-100',
    iconColor: 'text-sky-600',
    buttonBg: 'bg-sky-600 hover:bg-sky-700',
  },
  video_guidelines_generating: {
    icon: Wand2,
    accentColor: 'amber',
    borderColor: 'border-amber-200',
    bgColor: 'bg-amber-50/50',
    iconBg: 'bg-amber-100',
    iconColor: 'text-amber-600',
    buttonBg: 'bg-amber-600 hover:bg-amber-700',
    isLoading: true,
  },
  video_guidelines_ready: {
    icon: FileText,
    accentColor: 'emerald',
    borderColor: 'border-emerald-200',
    bgColor: 'bg-emerald-50/50',
    iconBg: 'bg-emerald-100',
    iconColor: 'text-emerald-600',
    buttonBg: 'bg-emerald-600 hover:bg-emerald-700',
  },
  video_uploaded: {
    icon: Camera,
    accentColor: 'blue',
    borderColor: 'border-blue-200',
    bgColor: 'bg-blue-50/50',
    iconBg: 'bg-blue-100',
    iconColor: 'text-blue-600',
    buttonBg: 'bg-blue-600 hover:bg-blue-700',
  },
  video_analyzing: {
    icon: Brain,
    accentColor: 'indigo',
    borderColor: 'border-indigo-200',
    bgColor: 'bg-indigo-50/50',
    iconBg: 'bg-indigo-100',
    iconColor: 'text-indigo-600',
    buttonBg: 'bg-indigo-600 hover:bg-indigo-700',
    isLoading: true,
  },
  video_validation_failed: {
    icon: AlertTriangle,
    accentColor: 'amber',
    borderColor: 'border-amber-300',
    bgColor: 'bg-amber-50/70',
    iconBg: 'bg-amber-100',
    iconColor: 'text-amber-600',
    buttonBg: 'bg-amber-600 hover:bg-amber-700',
  },
  video_needs_confirmation: {
    icon: HelpCircle,
    accentColor: 'orange',
    borderColor: 'border-orange-300',
    bgColor: 'bg-orange-50/70',
    iconBg: 'bg-orange-100',
    iconColor: 'text-orange-600',
    buttonBg: 'bg-orange-600 hover:bg-orange-700',
  },
  // FEEDBACK CARD - not action card. Analysis complete, insights woven into understanding.
  video_analyzed: {
    icon: CheckCircle2,  // Check icon - acknowledgment, not action
    accentColor: 'teal',
    borderColor: 'border-teal-200',
    bgColor: 'bg-teal-50/50',
    iconBg: 'bg-teal-100',
    iconColor: 'text-teal-600',
    buttonBg: 'bg-teal-600 hover:bg-teal-700',
    isFeedback: true,  // Marks as feedback card (dismiss only)
  },
  // NOTE: synthesis_available removed - synthesis is HOLISTIC, not cycle-bound.
  // Users pull it from ChildSpace (Essence/Share tabs), not via cards.
};

// Default config for unknown types
const DEFAULT_CONFIG = {
  icon: Lightbulb,
  accentColor: 'gray',
  borderColor: 'border-gray-200',
  bgColor: 'bg-gray-50/50',
  iconBg: 'bg-gray-100',
  iconColor: 'text-gray-600',
  buttonBg: 'bg-gray-600 hover:bg-gray-700',
};

function GestaltCard({ card, onAction, isActionLoading, loadingAction }) {
  const config = CARD_CONFIGS[card.type] || DEFAULT_CONFIG;
  const Icon = config.icon;

  // Check if this specific card's action is loading
  const isThisCardLoading = loadingAction && card.actions?.some(a => a.action === loadingAction);

  // Show loading state if: card type is loading, or card.loading flag, or this card's action is running
  const isLoading = config.isLoading || card.loading || isThisCardLoading;

  return (
    <div
      className={`
        relative overflow-hidden rounded-xl border ${config.borderColor}
        ${config.bgColor} bg-white
        shadow-sm hover:shadow-md
        transition-all duration-200
      `}
    >
      {/* Subtle top accent line */}
      <div className={`h-0.5 bg-${config.accentColor}-400`} />

      {/* Loading shimmer overlay */}
      {isLoading && (
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="loading-shimmer" />
        </div>
      )}

      <div className="p-4">
        {/* Header with icon */}
        <div className="flex items-start gap-3">
          <div className={`
            p-2 rounded-lg ${config.iconBg}
            ${isLoading ? 'animate-pulse' : ''}
          `}>
            {isLoading ? (
              <Loader2 className={`w-5 h-5 ${config.iconColor} animate-spin`} />
            ) : (
              <Icon className={`w-5 h-5 ${config.iconColor}`} />
            )}
          </div>

          <div className="flex-1 min-w-0">
            <h3 className="text-base font-semibold text-gray-800 leading-tight flex items-center gap-2">
              {card.title}
              {isLoading && (
                <span className="loading-dots">
                  <span className="dot" />
                  <span className="dot" />
                  <span className="dot" />
                </span>
              )}
            </h3>
            <p className="text-sm text-gray-600 mt-0.5 leading-relaxed">
              {card.description}
            </p>
          </div>

          {/* Dismiss button for dismissible cards */}
          {card.dismissible && !isLoading && (
            <button
              onClick={() => onAction('dismiss', card)}
              className="p-1 rounded-md hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Action buttons */}
        {card.actions && card.actions.length > 0 && (
          <div className="flex gap-2 mt-3 justify-end">
            {card.actions.map((action, idx) => {
              const isThisActionLoading = loadingAction === action.action;

              return (
                <button
                  key={idx}
                  type="button"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    onAction(action.action, card);
                  }}
                  disabled={isActionLoading}
                  className={`
                    py-2 px-4 rounded-lg font-medium text-sm
                    transition-all duration-150
                    flex items-center justify-center gap-2
                    disabled:opacity-50 disabled:cursor-not-allowed
                    ${action.primary
                      ? `${config.buttonBg} text-white shadow-sm`
                      : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50'
                    }
                  `}
                >
                  {isThisActionLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>מעבד...</span>
                    </>
                  ) : (
                    <>
                      {action.primary && getActionIcon(action.action)}
                      <span>{action.label}</span>
                    </>
                  )}
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

// Get icon for action type
function getActionIcon(actionType) {
  const icons = {
    accept_video: <CheckCircle2 className="w-4 h-4" />,
    view_guidelines: <Eye className="w-4 h-4" />,
    analyze_videos: <Brain className="w-4 h-4" />,
    upload_video: <Upload className="w-4 h-4" />,
    dismiss: <CheckCircle2 className="w-4 h-4" />,  // For feedback cards
    dismiss_reminder: <BellOff className="w-4 h-4" />,  // Don't remind me
    reject_guidelines: <XCircle className="w-4 h-4" />,  // Not relevant
  };
  return icons[actionType] || null;
}

export default function GestaltCards({ cards, onCardAction }) {
  const [loadingAction, setLoadingAction] = useState(null);

  const handleAction = async (action, card) => {
    // Set loading for actions that take time
    const longRunningActions = ['accept_video', 'analyze_videos'];
    if (longRunningActions.includes(action)) {
      setLoadingAction(action);
    }

    try {
      await onCardAction(action, card);
    } finally {
      setLoadingAction(null);
    }
  };

  if (!cards || cards.length === 0) {
    return null;
  }

  return (
    <div className="px-4 py-3">
      {/* Section header - subtle */}
      <div className="flex items-center gap-2 mb-3">
        <Lightbulb className="w-4 h-4 text-violet-500" />
        <span className="text-sm font-medium text-gray-600">מה עכשיו?</span>
        <div className="flex-1 h-px bg-gray-200" />
      </div>

      {/* Cards list - max width for readability */}
      <div className="space-y-3 max-w-2xl">
        {cards.map((card, idx) => (
          <div
            key={card.cycle_id || idx}
            className="animate-cardEnter"
            style={{ animationDelay: `${idx * 0.1}s` }}
          >
            <GestaltCard
              card={card}
              onAction={handleAction}
              isActionLoading={!!loadingAction}
              loadingAction={loadingAction}
            />
          </div>
        ))}
      </div>

      <style>{`
        /* Card entry animation */
        @keyframes cardEnter {
          from {
            opacity: 0;
            transform: translateY(16px) scale(0.96);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }

        .animate-cardEnter {
          animation: cardEnter 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
          opacity: 0;
        }

        /* Loading shimmer */
        .loading-shimmer {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: linear-gradient(
            90deg,
            transparent 0%,
            rgba(255, 255, 255, 0.4) 50%,
            transparent 100%
          );
          animation: shimmer 2s ease-in-out infinite;
        }

        @keyframes shimmer {
          0% {
            transform: translateX(-100%);
          }
          100% {
            transform: translateX(100%);
          }
        }

        /* Loading dots */
        .loading-dots {
          display: inline-flex;
          gap: 2px;
          align-items: center;
          margin-right: 4px;
        }

        .loading-dots .dot {
          width: 4px;
          height: 4px;
          background: currentColor;
          border-radius: 50%;
          opacity: 0.5;
          animation: dotPulse 1.4s ease-in-out infinite;
        }

        .loading-dots .dot:nth-child(1) { animation-delay: 0s; }
        .loading-dots .dot:nth-child(2) { animation-delay: 0.2s; }
        .loading-dots .dot:nth-child(3) { animation-delay: 0.4s; }

        @keyframes dotPulse {
          0%, 80%, 100% {
            opacity: 0.3;
            transform: scale(0.8);
          }
          40% {
            opacity: 1;
            transform: scale(1);
          }
        }
      `}</style>
    </div>
  );
}
