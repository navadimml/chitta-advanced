/**
 * CuriosityPanel - Display active curiosities
 *
 * Living Gestalt Architecture: Shows what Chitta is curious about.
 * Replaces the old "progress" / "completeness" indicators.
 *
 * Curiosity Types:
 * - discovery: Open exploration (blue)
 * - question: Following a thread (yellow)
 * - hypothesis: Testing a theory (purple)
 * - pattern: Connecting dots (green)
 */

import React from 'react';
import { Sparkles, HelpCircle, Lightbulb, GitBranch, ChevronDown, ChevronUp } from 'lucide-react';

// Map curiosity types to icons and colors
const CURIOSITY_CONFIG = {
  discovery: {
    icon: Sparkles,
    color: 'blue',
    bgClass: 'bg-blue-50',
    borderClass: 'border-blue-200',
    textClass: 'text-blue-700',
    iconClass: 'text-blue-500',
    label: 'גילוי'
  },
  question: {
    icon: HelpCircle,
    color: 'yellow',
    bgClass: 'bg-yellow-50',
    borderClass: 'border-yellow-200',
    textClass: 'text-yellow-700',
    iconClass: 'text-yellow-500',
    label: 'שאלה'
  },
  hypothesis: {
    icon: Lightbulb,
    color: 'purple',
    bgClass: 'bg-purple-50',
    borderClass: 'border-purple-200',
    textClass: 'text-purple-700',
    iconClass: 'text-purple-500',
    label: 'השערה'
  },
  pattern: {
    icon: GitBranch,
    color: 'green',
    bgClass: 'bg-green-50',
    borderClass: 'border-green-200',
    textClass: 'text-green-700',
    iconClass: 'text-green-500',
    label: 'תבנית'
  }
};

/**
 * Single curiosity item
 */
function CuriosityItem({ curiosity }) {
  const config = CURIOSITY_CONFIG[curiosity.type] || CURIOSITY_CONFIG.discovery;
  const Icon = config.icon;

  // Activation as percentage for visual indicator
  const activationPct = Math.round((curiosity.activation || 0) * 100);

  return (
    <div
      className={`
        p-3 rounded-lg border ${config.bgClass} ${config.borderClass}
        transition-all duration-200 hover:shadow-sm
      `}
    >
      <div className="flex items-start gap-2">
        <Icon className={`w-4 h-4 mt-0.5 ${config.iconClass}`} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs font-medium ${config.textClass}`}>
              {config.label}
            </span>
            {/* Activation indicator */}
            <div className="flex-1 h-1 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full ${config.bgClass} transition-all duration-300`}
                style={{ width: `${activationPct}%`, backgroundColor: `var(--${config.color}-400, #93c5fd)` }}
              />
            </div>
          </div>
          <p className="text-sm text-gray-700 leading-relaxed">
            {curiosity.focus}
          </p>
          {/* Show theory for hypotheses */}
          {curiosity.type === 'hypothesis' && curiosity.theory && (
            <p className="text-xs text-gray-500 mt-1 italic">
              {curiosity.theory}
            </p>
          )}
          {/* Show question for question type */}
          {curiosity.type === 'question' && curiosity.question && (
            <p className="text-xs text-gray-600 mt-1">
              {curiosity.question}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Open questions section
 */
function OpenQuestions({ questions }) {
  if (!questions || questions.length === 0) return null;

  return (
    <div className="mt-3 pt-3 border-t border-gray-100">
      <h4 className="text-xs font-medium text-gray-500 mb-2">
        שאלות פתוחות
      </h4>
      <ul className="space-y-1">
        {questions.slice(0, 3).map((q, i) => (
          <li key={i} className="text-xs text-gray-600 flex items-start gap-1">
            <span className="text-gray-400">•</span>
            <span>{q}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

/**
 * Main CuriosityPanel component
 */
export default function CuriosityPanel({
  curiosityState,
  collapsed = false,
  onToggle
}) {
  const [isExpanded, setIsExpanded] = React.useState(!collapsed);

  const curiosities = curiosityState?.active_curiosities || [];
  const openQuestions = curiosityState?.open_questions || [];

  // Don't render if no curiosities
  if (curiosities.length === 0 && openQuestions.length === 0) {
    return null;
  }

  const handleToggle = () => {
    const newExpanded = !isExpanded;
    setIsExpanded(newExpanded);
    onToggle?.(newExpanded);
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      {/* Header */}
      <button
        onClick={handleToggle}
        className="w-full px-4 py-3 flex items-center justify-between bg-gradient-to-r from-indigo-50 to-purple-50 hover:from-indigo-100 hover:to-purple-100 transition"
      >
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-indigo-500" />
          <span className="text-sm font-medium text-gray-700">
            מה אני סקרנית לגביו
          </span>
          <span className="text-xs bg-indigo-100 text-indigo-600 px-2 py-0.5 rounded-full">
            {curiosities.length}
          </span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-400" />
        )}
      </button>

      {/* Content */}
      {isExpanded && (
        <div className="p-4">
          {/* Curiosities list */}
          <div className="space-y-2">
            {curiosities.map((curiosity, index) => (
              <CuriosityItem key={index} curiosity={curiosity} />
            ))}
          </div>

          {/* Open questions */}
          <OpenQuestions questions={openQuestions} />
        </div>
      )}
    </div>
  );
}
