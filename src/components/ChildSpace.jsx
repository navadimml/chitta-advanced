import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import {
  X, Sparkles, Lightbulb, Video, Share2,
  ChevronLeft, ChevronDown, ChevronUp, ChevronRight, Heart, Music, Palette, Zap,
  Eye, Play, Clock, Send, Copy, FileText, Printer,
  Users, GraduationCap, Home, MessageCircle, MessageSquare,
  Check, Loader2, ArrowRight, Search, ThumbsUp, ThumbsDown, Minus,
  UserPlus, FileCheck, GitBranch, Link2, Camera, Upload, Brain,
  Maximize2, Trash2, RefreshCw, AlertTriangle, TrendingUp
} from 'lucide-react';
import { api } from '../api/client';
import ProfessionalSummary, { ProfessionalSummaryPrint } from './ProfessionalSummary';

// Backend base URL for static files (videos)
const BACKEND_BASE_URL = import.meta.env.VITE_API_URL?.replace('/api', '') || 'http://localhost:8000';

// Helper to convert relative video paths to full URLs
function getVideoUrl(videoPath) {
  if (!videoPath) return null;
  // If it's already a full URL, return as-is
  if (videoPath.startsWith('http://') || videoPath.startsWith('https://')) {
    return videoPath;
  }
  // Otherwise, prepend the backend base URL
  return `${BACKEND_BASE_URL}/${videoPath}`;
}

/**
 * ChildSpace - The Living Portrait
 *
 * A magical space where understanding lives and breathes.
 * Four tabs: Essence, Discoveries, Observations, Share
 *
 * Design principles:
 * - Delightful animations that feel natural
 * - Warm, inviting colors
 * - Every interaction brings a smile
 * - RTL-first, Hebrew-native
 */

// ============================================
// TAB CONFIGURATION
// ============================================

const TABS = [
  { id: 'essence', icon: Heart, label: 'הדיוקן', color: 'from-rose-400 to-orange-400' },
  { id: 'discoveries', icon: Lightbulb, label: 'המסע', color: 'from-amber-400 to-yellow-400' },
  { id: 'observations', icon: Video, label: 'מה ראינו', color: 'from-teal-400 to-cyan-400' },
  { id: 'share', icon: Share2, label: 'שיתוף', color: 'from-blue-400 to-indigo-400' },
];

// ============================================
// LOADING ANIMATION COMPONENT
// ============================================

function LoadingAnimation({ childName }) {
  return (
    <div className="relative flex flex-col items-center justify-center min-h-[400px] overflow-hidden">
      {/* Massive drifting blobs - varied colors */}
      <div
        className="absolute rounded-full"
        style={{
          width: '500px',
          height: '500px',
          background: 'radial-gradient(circle, rgba(99,182,205,0.2) 0%, transparent 60%)',
          top: '-20%',
          right: '-30%',
          filter: 'blur(60px)',
          animation: 'drift1 30s ease-in-out infinite',
        }}
      />
      <div
        className="absolute rounded-full"
        style={{
          width: '600px',
          height: '600px',
          background: 'radial-gradient(circle, rgba(245,190,160,0.18) 0%, transparent 60%)',
          bottom: '-30%',
          left: '-40%',
          filter: 'blur(70px)',
          animation: 'drift2 35s ease-in-out infinite',
        }}
      />

      {/* Mid layer blobs */}
      <div
        className="absolute rounded-full"
        style={{
          width: '350px',
          height: '350px',
          background: 'radial-gradient(circle, rgba(167,210,170,0.25) 0%, transparent 60%)',
          top: '10%',
          left: '-10%',
          filter: 'blur(50px)',
          animation: 'drift3 25s ease-in-out infinite',
        }}
      />
      <div
        className="absolute rounded-full"
        style={{
          width: '300px',
          height: '300px',
          background: 'radial-gradient(circle, rgba(200,175,215,0.22) 0%, transparent 60%)',
          bottom: '5%',
          right: '-15%',
          filter: 'blur(45px)',
          animation: 'drift4 28s ease-in-out infinite',
        }}
      />

      {/* Near layer - smaller drifters */}
      <div
        className="absolute rounded-full"
        style={{
          width: '200px',
          height: '200px',
          background: 'radial-gradient(circle, rgba(250,215,180,0.3) 0%, transparent 60%)',
          top: '40%',
          right: '10%',
          filter: 'blur(35px)',
          animation: 'drift5 20s ease-in-out infinite',
        }}
      />
      <div
        className="absolute rounded-full"
        style={{
          width: '180px',
          height: '180px',
          background: 'radial-gradient(circle, rgba(180,210,230,0.28) 0%, transparent 60%)',
          bottom: '30%',
          left: '5%',
          filter: 'blur(30px)',
          animation: 'drift6 22s ease-in-out infinite',
        }}
      />

      {/* Three bouncing dots */}
      <div className="relative z-10 flex items-center gap-2">
        <div
          className="w-3 h-3 rounded-full bg-gray-400"
          style={{ animation: 'bounce 1.4s ease-in-out infinite' }}
        />
        <div
          className="w-3 h-3 rounded-full bg-gray-400"
          style={{ animation: 'bounce 1.4s ease-in-out 0.2s infinite' }}
        />
        <div
          className="w-3 h-3 rounded-full bg-gray-400"
          style={{ animation: 'bounce 1.4s ease-in-out 0.4s infinite' }}
        />
      </div>

      {/* Poetic text */}
      <div
        className="relative z-10 mt-6 text-center"
        style={{ animation: 'textFade 3s ease-in-out infinite' }}
      >
        <p className="text-sm text-gray-500 font-medium">
          {childName || 'טוען'}
        </p>
        <p className="text-xs text-gray-400 mt-1">
          אוספים את מה שלמדנו
        </p>
      </div>

      <style>{`
        @keyframes drift1 {
          0%, 100% { transform: translate(0, 0); }
          25% { transform: translate(-80px, 60px); }
          50% { transform: translate(-40px, 120px); }
          75% { transform: translate(60px, 40px); }
        }
        @keyframes drift2 {
          0%, 100% { transform: translate(0, 0); }
          25% { transform: translate(100px, -50px); }
          50% { transform: translate(60px, -100px); }
          75% { transform: translate(-40px, -30px); }
        }
        @keyframes drift3 {
          0%, 100% { transform: translate(0, 0); }
          33% { transform: translate(70px, 50px); }
          66% { transform: translate(30px, -40px); }
        }
        @keyframes drift4 {
          0%, 100% { transform: translate(0, 0); }
          33% { transform: translate(-60px, -40px); }
          66% { transform: translate(-90px, 30px); }
        }
        @keyframes drift5 {
          0%, 100% { transform: translate(0, 0); }
          50% { transform: translate(-50px, 40px); }
        }
        @keyframes drift6 {
          0%, 100% { transform: translate(0, 0); }
          50% { transform: translate(40px, -50px); }
        }
        @keyframes bounce {
          0%, 80%, 100% {
            transform: translateY(0);
          }
          40% {
            transform: translateY(-12px);
          }
        }
        @keyframes textFade {
          0%, 100% {
            opacity: 0;
          }
          50% {
            opacity: 1;
          }
        }
      `}</style>
    </div>
  );
}

// ============================================
// STRENGTH CARD COMPONENT
// ============================================

function StrengthCard({ strength, index }) {
  const gradients = {
    music: 'strength-music',
    creativity: 'strength-creativity',
    persistence: 'strength-persistence',
    social: 'strength-social',
    motor: 'strength-motor',
    default: 'strength-default'
  };

  const icons = {
    music: Music,
    creativity: Palette,
    persistence: Zap,
    default: Heart
  };

  const Icon = icons[strength.domain] || icons.default;
  const gradient = gradients[strength.domain] || gradients.default;

  return (
    <div
      className={`
        ${gradient} rounded-2xl p-4 card-hover
        opacity-0 animate-staggerIn stagger-${index + 1}
      `}
    >
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 bg-white/50 rounded-xl flex items-center justify-center">
          <Icon className="w-5 h-5 text-gray-700" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-bold text-gray-800 text-sm">{strength.title_he}</h4>
          <p className="text-xs text-gray-600 mt-1 line-clamp-2">{strength.evidence}</p>
        </div>
      </div>
    </div>
  );
}

// ============================================
// EXPLORATION CARD - Expandable with Evidence
// ============================================

function ExplorationCard({ exploration, index }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const contentRef = useRef(null);

  const effectIcons = {
    supports: { icon: ThumbsUp, color: 'text-emerald-500', bg: 'bg-emerald-50' },
    contradicts: { icon: ThumbsDown, color: 'text-rose-500', bg: 'bg-rose-50' },
    neutral: { icon: Minus, color: 'text-gray-500', bg: 'bg-gray-50' },
  };

  const hasEvidence = exploration.evidence && exploration.evidence.length > 0;

  return (
    <div
      className={`
        bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden
        transition-all duration-300 card-hover
        opacity-0 animate-staggerIn stagger-${Math.min(index + 1, 6)}
      `}
    >
      {/* Main content - clickable to expand */}
      <button
        onClick={() => hasEvidence && setIsExpanded(!isExpanded)}
        className={`w-full p-4 text-right ${hasEvidence ? 'cursor-pointer' : ''}`}
        disabled={!hasEvidence}
      >
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-indigo-100 to-purple-100 rounded-xl flex items-center justify-center flex-shrink-0">
            <Lightbulb className="w-5 h-5 text-indigo-500" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <h4 className="font-bold text-gray-800">{exploration.question}</h4>
              {hasEvidence && (
                <div className="flex items-center gap-1 text-xs text-gray-400">
                  <span>{exploration.evidence_count} ראיות</span>
                  <ChevronDown
                    className={`w-4 h-4 transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`}
                  />
                </div>
              )}
            </div>
            {exploration.theory && (
              <p className="text-sm text-gray-600 mt-1">{exploration.theory}</p>
            )}
            {/* Confidence bar */}
            <div className="mt-3">
              <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                <span>ביטחון</span>
                <span>{Math.round(exploration.confidence * 100)}%</span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-indigo-400 to-purple-500 rounded-full transition-all duration-500"
                  style={{ width: `${exploration.confidence * 100}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      </button>

      {/* Expanded evidence section with smooth height transition */}
      <div
        className={`
          overflow-hidden transition-all duration-300 ease-out
          ${isExpanded ? 'opacity-100' : 'opacity-0'}
        `}
        style={{
          maxHeight: isExpanded ? `${contentRef.current?.scrollHeight || 500}px` : '0px',
        }}
      >
        <div ref={contentRef} className="px-4 pb-4 pt-0 border-t border-gray-50">
          <h5 className="text-xs font-bold text-gray-500 mb-2 mt-3">ראיות תומכות:</h5>
          <div className="space-y-2">
            {hasEvidence && exploration.evidence.map((ev, idx) => {
              const config = effectIcons[ev.effect] || effectIcons.neutral;
              const EffectIcon = config.icon;
              return (
                <div
                  key={idx}
                  className={`flex items-start gap-2 p-2 rounded-lg ${config.bg}`}
                >
                  <EffectIcon className={`w-4 h-4 mt-0.5 ${config.color} flex-shrink-0`} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-700">{ev.content}</p>
                    <span className="text-xs text-gray-400">
                      {ev.source === 'conversation' ? 'משיחה' : ev.source === 'video' ? 'מסרטון' : ev.source}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Video status badges */}
          <div className="mt-3 flex gap-2">
            {exploration.has_video_analyzed && (
              <span className="inline-flex items-center gap-1 px-2 py-1 bg-emerald-50 text-emerald-700 rounded-full text-xs">
                <Video className="w-3 h-3" />
                סרטון נותח
              </span>
            )}
            {exploration.has_video_pending && (
              <span className="inline-flex items-center gap-1 px-2 py-1 bg-amber-50 text-amber-700 rounded-full text-xs">
                <Clock className="w-3 h-3" />
                סרטון ממתין
              </span>
            )}
            {exploration.video_appropriate && !exploration.has_video_pending && !exploration.has_video_analyzed && (
              <span className="inline-flex items-center gap-1 px-2 py-1 bg-indigo-50 text-indigo-700 rounded-full text-xs">
                <Video className="w-3 h-3" />
                מומלץ לצלם
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================
// EXPERT RECOMMENDATION CARD - Expandable Professional Guidance
// ============================================

function ExpertRecommendationCard({ recommendation, index }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const contentRef = useRef(null);

  const priorityConfig = {
    important: { label: 'מומלץ מאוד', color: 'bg-rose-100 text-rose-700 border-rose-200' },
    soon: { label: 'כדאי בקרוב', color: 'bg-amber-100 text-amber-700 border-amber-200' },
    when_ready: { label: 'כשתהיו מוכנים', color: 'bg-blue-100 text-blue-700 border-blue-200' },
  };

  const priority = priorityConfig[recommendation.priority] || priorityConfig.when_ready;

  return (
    <div
      className={`
        bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl border border-blue-100 shadow-sm overflow-hidden
        transition-all duration-300 card-hover
        opacity-0 animate-staggerIn stagger-${Math.min(index + 1, 6)}
      `}
    >
      {/* Main content - clickable to expand */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-4 text-right cursor-pointer"
      >
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-xl flex items-center justify-center flex-shrink-0">
            <UserPlus className="w-5 h-5 text-blue-600" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-2">
              <h4 className="font-bold text-gray-800">{recommendation.profession}</h4>
              <div className="flex items-center gap-2">
                <span className={`px-2 py-0.5 rounded-full text-xs border ${priority.color}`}>
                  {priority.label}
                </span>
                <ChevronDown
                  className={`w-4 h-4 text-gray-400 transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`}
                />
              </div>
            </div>
            <p className="text-sm text-blue-700 font-medium mt-1">{recommendation.specialization}</p>
            <p className="text-sm text-gray-600 mt-2">{recommendation.why_this_match}</p>
          </div>
        </div>
      </button>

      {/* Expanded details section */}
      <div
        className={`
          overflow-hidden transition-all duration-300 ease-out
          ${isExpanded ? 'opacity-100' : 'opacity-0'}
        `}
        style={{
          maxHeight: isExpanded ? `${contentRef.current?.scrollHeight || 500}px` : '0px',
        }}
      >
        <div ref={contentRef} className="px-4 pb-4 pt-0 border-t border-blue-100/50">
          {/* Recommended Approach */}
          <div className="mt-3">
            <h5 className="text-xs font-bold text-gray-500 mb-2">גישה מומלצת:</h5>
            <p className="text-sm text-gray-700 bg-white/60 p-2 rounded-lg">{recommendation.recommended_approach}</p>
            {recommendation.why_this_approach && (
              <p className="text-xs text-gray-500 mt-1 pr-2">{recommendation.why_this_approach}</p>
            )}
          </div>

          {/* What to Look For */}
          {recommendation.what_to_look_for && recommendation.what_to_look_for.length > 0 && (
            <div className="mt-3">
              <h5 className="text-xs font-bold text-gray-500 mb-2">מה לשאול כשמחפשים:</h5>
              <ul className="space-y-1">
                {recommendation.what_to_look_for.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm text-gray-700">
                    <Check className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Summary for Professional */}
          {recommendation.summary_for_professional && (
            <div className="mt-3">
              <h5 className="text-xs font-bold text-gray-500 mb-2">מה לספר למטפל:</h5>
              <p className="text-sm text-gray-700 bg-white/60 p-3 rounded-lg leading-relaxed">
                {recommendation.summary_for_professional}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================
// ESSENCE TAB - The Living Portrait (Holistic View)
// ============================================

// Premium card color schemes - warm, professional palette
const CARD_SCHEMES = [
  { bg: 'bg-gradient-to-br from-orange-50 to-amber-50', border: 'border-orange-200', accent: 'text-orange-600', icon: 'bg-orange-100' },
  { bg: 'bg-gradient-to-br from-teal-50 to-cyan-50', border: 'border-teal-200', accent: 'text-teal-600', icon: 'bg-teal-100' },
  { bg: 'bg-gradient-to-br from-rose-50 to-pink-50', border: 'border-rose-200', accent: 'text-rose-600', icon: 'bg-rose-100' },
  { bg: 'bg-gradient-to-br from-sky-50 to-blue-50', border: 'border-sky-200', accent: 'text-sky-600', icon: 'bg-sky-100' },
  { bg: 'bg-gradient-to-br from-emerald-50 to-green-50', border: 'border-emerald-200', accent: 'text-emerald-600', icon: 'bg-emerald-100' },
  { bg: 'bg-gradient-to-br from-amber-50 to-yellow-50', border: 'border-amber-200', accent: 'text-amber-600', icon: 'bg-amber-100' },
];

// Icon mapping based on section title keywords
const getIconForSection = (title) => {
  const titleLower = title?.toLowerCase() || '';
  if (titleLower.includes('פנימי') || titleLower.includes('עולם') || titleLower.includes('ניגון') || titleLower.includes('מוזיקה')) return Music;
  if (titleLower.includes('רגיש') || titleLower.includes('סביבה') || titleLower.includes('חושי')) return Eye;
  if (titleLower.includes('מעבר') || titleLower.includes('שינוי') || titleLower.includes('פעילות')) return Clock;
  if (titleLower.includes('חברתי') || titleLower.includes('משחק') || titleLower.includes('ילדים')) return Users;
  if (titleLower.includes('חוזק') || titleLower.includes('יכולת') || titleLower.includes('מיומנות')) return Zap;
  if (titleLower.includes('יצירה') || titleLower.includes('בנייה') || titleLower.includes('אמנות')) return Palette;
  return Heart; // Default
};

function PortraitCard({ section, index = 0 }) {
  const scheme = CARD_SCHEMES[index % CARD_SCHEMES.length];
  const IconComponent = getIconForSection(section.title);

  // Parse bullets if content type is bullets
  const renderContent = () => {
    if (section.content_type === 'bullets') {
      const items = section.content
        .split(/[•\n]/)
        .map(item => item.trim())
        .filter(item => item.length > 0);

      return (
        <ul className="space-y-2.5 mt-3">
          {items.map((item, idx) => (
            <li key={idx} className="flex items-start gap-3">
              <div className={`w-1.5 h-1.5 rounded-full ${scheme.accent.replace('text-', 'bg-')} mt-2 flex-shrink-0`} />
              <span className="text-gray-700 leading-relaxed">{item}</span>
            </li>
          ))}
        </ul>
      );
    }
    return <p className="text-gray-700 leading-relaxed mt-3">{section.content}</p>;
  };

  return (
    <div
      className={`${scheme.bg} rounded-2xl border ${scheme.border} p-6 opacity-0 animate-fadeIn transition-all duration-200 hover:shadow-md`}
      style={{ animationDelay: `${0.1 + index * 0.08}s`, animationFillMode: 'forwards' }}
    >
      <div className="flex items-center gap-4">
        <div className={`w-11 h-11 ${scheme.icon} rounded-xl flex items-center justify-center flex-shrink-0`}>
          <IconComponent className={`w-5 h-5 ${scheme.accent}`} />
        </div>
        <h3 className="text-gray-800 font-semibold text-lg">{section.title}</h3>
      </div>
      {renderContent()}
    </div>
  );
}

/**
 * PatternCard - displays cross-domain insights
 * Clean, professional style with teal accent
 */
function PatternCard({ pattern, index = 0 }) {
  return (
    <div
      className="bg-gradient-to-br from-slate-50 to-gray-50 rounded-2xl border border-slate-200 p-5 opacity-0 animate-fadeIn transition-all duration-200 hover:shadow-md"
      style={{ animationDelay: `${0.1 + index * 0.08}s`, animationFillMode: 'forwards' }}
    >
      <div className="flex items-start gap-4">
        <div className="w-10 h-10 bg-teal-100 rounded-xl flex items-center justify-center flex-shrink-0">
          <Eye className="w-5 h-5 text-teal-600" />
        </div>
        <div className="flex-1">
          <p className="text-gray-700 leading-relaxed">{pattern.description}</p>
        </div>
      </div>
    </div>
  );
}

/**
 * InterventionPathwayCard - displays "what can help" suggestions
 * Vertical layout: hook (strength) as header → concern as context → suggestion as content
 */
function InterventionPathwayCard({ pathway, index = 0 }) {
  return (
    <div
      className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-2xl border border-amber-200 p-5 opacity-0 animate-fadeIn transition-all duration-200 hover:shadow-md"
      style={{ animationDelay: `${0.1 + index * 0.08}s`, animationFillMode: 'forwards' }}
    >
      <div className="flex items-start gap-4">
        <div className="w-10 h-10 bg-amber-100 rounded-xl flex items-center justify-center flex-shrink-0">
          <Zap className="w-5 h-5 text-amber-600" />
        </div>
        <div className="flex-1">
          {/* Strength as header badge */}
          <div className="mb-2">
            <span className="inline-block px-2.5 py-1 bg-amber-100 text-amber-700 text-sm font-medium rounded-lg">
              {pathway.hook}
            </span>
          </div>
          {/* Concern as context */}
          <p className="text-gray-500 text-sm mb-2">{pathway.concern}</p>
          {/* Practical suggestion */}
          <p className="text-gray-700 leading-relaxed">{pathway.suggestion}</p>
        </div>
      </div>
    </div>
  );
}

function EssenceTab({ data, childName }) {
  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center py-16 px-8">
        <div className="w-20 h-20 bg-gradient-to-br from-purple-100 to-indigo-100 rounded-full flex items-center justify-center mb-4 animate-gentleFloat">
          <Sparkles className="w-10 h-10 text-purple-400" />
        </div>
        <p className="text-gray-500 text-center">
          עוד לא הספקנו להכיר מספיק...<br />
          ככל שנשוחח יותר, התמונה תתבהר
        </p>
      </div>
    );
  }

  // Use portrait_sections if available (new format from backend)
  const hasPortraitSections = data.portrait_sections && data.portrait_sections.length > 0;

  return (
    <div className="space-y-4 pb-8">
      {/* Portrait Sections - the main content */}
      {hasPortraitSections ? (
        data.portrait_sections.map((section, idx) => (
          <PortraitCard key={idx} section={section} index={idx} />
        ))
      ) : (
        // Fallback if no portrait sections
        <div className="text-center text-gray-500 py-8">
          ככל שנשוחח יותר, התמונה תתבהר...
        </div>
      )}

      {/* Patterns - cross-domain connections (critical insight) */}
      {data.patterns && data.patterns.length > 0 && (
        <div className="mt-6 pt-6 border-t border-gray-200 opacity-0 animate-fadeIn" style={{ animationDelay: '0.35s', animationFillMode: 'forwards' }}>
          <h3 className="text-gray-600 font-medium mb-4 flex items-center gap-2">
            <Lightbulb className="w-4 h-4" />
            תובנות
          </h3>
          <div className="space-y-3">
            {data.patterns.map((pattern, idx) => (
              <PatternCard key={idx} pattern={pattern} index={idx} />
            ))}
          </div>
        </div>
      )}

      {/* Intervention Pathways - "what can help" sections (very important!) */}
      {data.intervention_pathways && data.intervention_pathways.length > 0 && (
        <div className="mt-6 pt-6 border-t border-gray-200 opacity-0 animate-fadeIn" style={{ animationDelay: '0.4s', animationFillMode: 'forwards' }}>
          <h3 className="text-gray-600 font-medium mb-4 flex items-center gap-2">
            <Lightbulb className="w-4 h-4 text-amber-500" />
            מה יכול לעזור
          </h3>
          <div className="space-y-3">
            {data.intervention_pathways.map((pathway, idx) => (
              <InterventionPathwayCard key={idx} pathway={pathway} index={idx} />
            ))}
          </div>
        </div>
      )}

      {/* Expert recommendations - kept separate, simpler presentation */}
      {data.expert_recommendations && data.expert_recommendations.length > 0 && (
        <div className="mt-8 pt-6 border-t border-gray-200 opacity-0 animate-fadeIn" style={{ animationDelay: '0.5s', animationFillMode: 'forwards' }}>
          <h3 className="text-gray-600 font-medium mb-4 flex items-center gap-2">
            <UserPlus className="w-4 h-4" />
            אנשי מקצוע שיכולים לעזור
          </h3>
          <div className="space-y-3">
            {data.expert_recommendations.map((rec, idx) => (
              <ExpertRecommendationCard key={idx} recommendation={rec} index={idx} />
            ))}
          </div>
        </div>
      )}

      {/* Active explorations - minimal presentation */}
      {data.active_explorations && data.active_explorations.length > 0 && (
        <div className="mt-6 pt-6 border-t border-gray-200 opacity-0 animate-fadeIn" style={{ animationDelay: '0.6s', animationFillMode: 'forwards' }}>
          <h3 className="text-gray-600 font-medium mb-4 flex items-center gap-2">
            <Search className="w-4 h-4" />
            מה אנחנו בודקים עכשיו
          </h3>
          <div className="space-y-3">
            {data.active_explorations.map((exploration, idx) => (
              <ExplorationCard
                key={exploration.id}
                exploration={exploration}
                index={idx}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// Collapsible Facts Section (secondary info)
function FactsSection({ factsData }) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="opacity-0 animate-fadeIn" style={{ animationDelay: '0.45s', animationFillMode: 'forwards' }}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full text-sm font-bold text-gray-400 mb-3 flex items-center gap-2 hover:text-gray-600 transition"
      >
        <FileText className="w-4 h-4" />
        עובדות נוספות
        <ChevronDown className={`w-4 h-4 mr-auto transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
      </button>
      <div
        className={`overflow-hidden transition-all duration-300 ${isExpanded ? 'max-h-[1000px] opacity-100' : 'max-h-0 opacity-0'}`}
      >
        <div className="bg-white rounded-2xl border border-gray-100 divide-y divide-gray-50">
          {Object.entries(factsData).map(([domain, facts]) => (
            <div key={domain} className="p-4">
              <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">
                {getDomainLabel(domain)}
              </span>
              <ul className="mt-2 space-y-1">
                {facts.map((fact, idx) => (
                  <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                    <span className="text-indigo-400 mt-1">•</span>
                    {fact}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ============================================
// DISCOVERIES TAB - Developmental Timeline
// ============================================

/**
 * FUTURE FEATURE: Developmental Timeline
 *
 * This tab will show the child's developmental journey - real milestones
 * that matter to parents and clinicians, organized by age.
 *
 * Examples:
 * - "מילים ראשונות - 12 חודשים"
 * - "התחיל ללכת - 14 חודשים"
 * - "נסיגה בדיבור - גיל שנתיים"
 * - "התחיל טיפול בעיסוק - 3 שנים"
 *
 * Implementation needed:
 * 1. Add developmental_milestones to Gestalt (see models.py skeleton)
 * 2. Create LLM tool to extract milestones from conversation
 * 3. Build age-based timeline UI here
 */
function DiscoveriesTab({ data, onVideoClick }) {
  const [activeView, setActiveView] = useState('discoveries'); // 'discoveries' or 'development'

  const milestones = data?.milestones || [];

  // Split milestones into two types
  const developmentalMilestones = milestones.filter(m => m.type === 'developmental');
  const journeyMilestones = milestones.filter(m => m.type !== 'developmental');

  const hasDevelopmentalMilestones = developmentalMilestones.length > 0;
  const hasJourneyMilestones = journeyMilestones.length > 0;
  const hasAnyContent = hasDevelopmentalMilestones || hasJourneyMilestones;

  // Auto-switch to 'development' view when developmental milestones are present
  // This ensures parents see birth/pregnancy data they shared
  // Prioritize developmental timeline since it contains explicit parent-shared data
  useEffect(() => {
    if (hasDevelopmentalMilestones) {
      setActiveView('development');
    }
  }, [hasDevelopmentalMilestones]);

  // Milestone type configuration for developmental timeline
  const milestoneTypeConfig = {
    birth: {
      color: 'bg-rose-500',
      borderColor: 'border-rose-400',
      bgLight: 'bg-rose-50',
      textColor: 'text-rose-700',
      icon: '◯',
      label: 'לידה'
    },
    achievement: {
      color: 'bg-emerald-500',
      borderColor: 'border-emerald-400',
      bgLight: 'bg-emerald-50',
      textColor: 'text-emerald-700',
      icon: '✓',
      label: 'הישג'
    },
    concern: {
      color: 'bg-amber-500',
      borderColor: 'border-amber-400',
      bgLight: 'bg-amber-50',
      textColor: 'text-amber-700',
      icon: '⚠',
      label: 'תשומת לב'
    },
    regression: {
      color: 'bg-red-500',
      borderColor: 'border-red-400',
      bgLight: 'bg-red-50',
      textColor: 'text-red-700',
      icon: '↓',
      label: 'נסיגה'
    },
    intervention: {
      color: 'bg-blue-500',
      borderColor: 'border-blue-400',
      bgLight: 'bg-blue-50',
      textColor: 'text-blue-700',
      icon: '→',
      label: 'התערבות'
    },
  };

  // Journey milestone type configuration
  const journeyTypeConfig = {
    started: {
      icon: Sparkles,
      color: 'bg-violet-500',
      bgLight: 'bg-violet-50',
      borderColor: 'border-violet-200',
      label: 'התחלנו'
    },
    exploration_began: {
      icon: Search,
      color: 'bg-indigo-500',
      bgLight: 'bg-indigo-50',
      borderColor: 'border-indigo-200',
      label: 'התחלנו לחקור'
    },
    video_analyzed: {
      icon: Video,
      color: 'bg-teal-500',
      bgLight: 'bg-teal-50',
      borderColor: 'border-teal-200',
      label: 'צפינו בסרטון'
    },
    insight: {
      icon: Lightbulb,
      color: 'bg-amber-500',
      bgLight: 'bg-amber-50',
      borderColor: 'border-amber-200',
      label: 'תובנה'
    },
    pattern: {
      icon: Sparkles,
      color: 'bg-purple-500',
      bgLight: 'bg-purple-50',
      borderColor: 'border-purple-200',
      label: 'דפוס'
    },
  };

  // Domain Hebrew labels
  const domainLabels = {
    motor: 'מוטורי',
    language: 'שפה',
    social: 'חברתי',
    cognitive: 'קוגניטיבי',
    regulation: 'ויסות',
    birth_history: 'לידה והריון',
    medical: 'רפואי',
  };

  // Sort developmental milestones by age_months for the timeline
  const sortedDevMilestones = [...developmentalMilestones].sort((a, b) => {
    const ageA = a.age_months ?? 999;
    const ageB = b.age_months ?? 999;
    return ageA - ageB;
  });

  // Sort journey milestones by timestamp (newest first)
  const sortedJourneyMilestones = [...journeyMilestones].sort((a, b) => {
    return new Date(b.timestamp || 0) - new Date(a.timestamp || 0);
  });

  // Calculate timeline bounds for developmental view
  const minAge = Math.min(...sortedDevMilestones.map(m => m.age_months ?? 0), 0);
  const maxAge = Math.max(...sortedDevMilestones.map(m => m.age_months ?? 0), 12);

  // Generate age markers for the developmental timeline
  const generateAgeMarkers = () => {
    const markers = [];
    const endYear = Math.ceil(maxAge / 12);

    if (minAge < 0) {
      markers.push({ months: -1, label: 'הריון' });
    }
    markers.push({ months: 0, label: 'לידה' });
    for (let year = 1; year <= endYear; year++) {
      markers.push({ months: year * 12, label: year === 1 ? 'שנה' : `${year} שנים` });
    }
    return markers;
  };

  const ageMarkers = generateAgeMarkers();

  const getTimelinePosition = (ageMonths) => {
    const range = maxAge - minAge;
    if (range === 0) return 50;
    return ((ageMonths - minAge) / range) * 100;
  };

  // Format date for journey view
  const formatDate = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    const now = new Date();
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'היום';
    if (diffDays === 1) return 'אתמול';
    if (diffDays < 7) return `לפני ${diffDays} ימים`;
    if (diffDays < 30) return `לפני ${Math.floor(diffDays / 7)} שבועות`;
    return date.toLocaleDateString('he-IL', { day: 'numeric', month: 'short' });
  };

  // Empty state
  if (!hasAnyContent) {
    return (
      <div className="flex flex-col items-center justify-center py-16 px-8">
        <div className="w-20 h-20 bg-gradient-to-br from-amber-100 to-orange-100 rounded-full flex items-center justify-center mb-4 animate-gentleFloat">
          <Lightbulb className="w-10 h-10 text-amber-400" />
        </div>
        <h3 className="text-lg font-bold text-gray-700 mb-2">המסע מתחיל</h3>
        <p className="text-gray-500 text-center text-sm">
          כאן יופיע המסע שלנו יחד -<br />
          הגילויים, התובנות, ואבני הדרך
        </p>
        <div className="mt-6 p-4 bg-amber-50 rounded-xl border border-amber-200 max-w-xs">
          <p className="text-xs text-amber-700 text-center">
            💡 ספרו לנו על הילד במהלך השיחה,
            ואנחנו נבנה את המסע יחד
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      {/* Segmented Toggle */}
      <div className="flex justify-center">
        <div className="inline-flex bg-gray-100 rounded-xl p-1 gap-1">
          <button
            onClick={() => setActiveView('discoveries')}
            className={`
              px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
              flex items-center gap-2
              ${activeView === 'discoveries'
                ? 'bg-white text-amber-700 shadow-sm'
                : 'text-gray-600 hover:text-gray-800'
              }
            `}
          >
            <Search className="w-4 h-4" />
            גילויים
          </button>
          <button
            onClick={() => setActiveView('development')}
            className={`
              px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
              flex items-center gap-2
              ${activeView === 'development'
                ? 'bg-white text-amber-700 shadow-sm'
                : 'text-gray-600 hover:text-gray-800'
              }
            `}
          >
            <TrendingUp className="w-4 h-4" />
            התפתחות
          </button>
        </div>
      </div>

      {/* ============ DISCOVERIES VIEW ============ */}
      {activeView === 'discoveries' && (
        <div className="space-y-4">
          {/* Header */}
          <div className="text-center">
            <p className="text-sm text-gray-500">
              מה גילינו יחד במסע שלנו
            </p>
          </div>

          {hasJourneyMilestones ? (
            <div className="space-y-3">
              {sortedJourneyMilestones.map((milestone, index) => {
                const config = journeyTypeConfig[milestone.type] || journeyTypeConfig.insight;
                const Icon = config.icon;

                return (
                  <div
                    key={milestone.id}
                    className={`
                      relative p-4 rounded-xl border transition-all
                      ${config.bgLight} ${config.borderColor}
                      ${milestone.significance === 'major' ? 'ring-1 ring-amber-300' : ''}
                    `}
                  >
                    {/* Date badge */}
                    <div className="absolute top-3 left-3 text-[10px] text-gray-400">
                      {formatDate(milestone.timestamp)}
                    </div>

                    <div className="flex items-start gap-3">
                      {/* Icon */}
                      <div className={`
                        w-10 h-10 rounded-xl ${config.color} flex items-center justify-center
                        text-white shadow-sm flex-shrink-0
                      `}>
                        <Icon className="w-5 h-5" />
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0 pt-1">
                        <div className="text-[10px] font-medium text-gray-500 mb-1">
                          {config.label}
                        </div>
                        <h4 className="font-semibold text-gray-800 text-sm leading-snug">
                          {milestone.title_he}
                        </h4>
                        {milestone.description_he && (
                          <p className="text-xs text-gray-600 mt-1 leading-relaxed">
                            {milestone.description_he}
                          </p>
                        )}

                        {/* Video link if applicable */}
                        {milestone.type === 'video_analyzed' && milestone.video_id && (
                          <button
                            onClick={() => onVideoClick?.(milestone.video_id)}
                            className="mt-2 text-xs text-teal-600 hover:text-teal-700 font-medium flex items-center gap-1"
                          >
                            <Video className="w-3 h-3" />
                            צפה בסרטון
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-8">
              <Search className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500 text-sm">
                עוד לא צברנו גילויים משותפים
              </p>
              <p className="text-gray-400 text-xs mt-1">
                המשיכו לשוחח איתנו ולשתף סרטונים
              </p>
            </div>
          )}
        </div>
      )}

      {/* ============ DEVELOPMENT VIEW ============ */}
      {activeView === 'development' && (
        <div className="space-y-4">
          {/* Header */}
          <div className="text-center">
            <p className="text-sm text-gray-500">
              {hasDevelopmentalMilestones
                ? `${sortedDevMilestones.length} אבני דרך התפתחותיות`
                : 'ציר הזמן ההתפתחותי'
              }
            </p>
          </div>

          {hasDevelopmentalMilestones ? (
            <>
              {/* Legend */}
              <div className="flex flex-wrap justify-center gap-3 px-2">
                {Object.entries(milestoneTypeConfig).map(([type, config]) => (
                  <div key={type} className="flex items-center gap-1.5">
                    <div className={`w-3 h-3 rounded-full ${config.color}`} />
                    <span className="text-xs text-gray-600">{config.label}</span>
                  </div>
                ))}
              </div>

              {/* Timeline Infographic */}
              <div className="relative bg-gradient-to-b from-slate-50 to-white rounded-2xl border border-slate-200 overflow-hidden">
                <div className="absolute inset-0 opacity-5 pointer-events-none">
                  <div className="absolute inset-0" style={{
                    backgroundImage: 'radial-gradient(circle, #6366f1 1px, transparent 1px)',
                    backgroundSize: '20px 20px'
                  }} />
                </div>

                <div className="overflow-x-auto" dir="ltr">
                  <div
                    className="relative py-4 px-16"
                    style={{
                      minHeight: '220px',
                      minWidth: `${Math.max(350, sortedDevMilestones.length * 100)}px`
                    }}
                  >
                    <div className="absolute top-1/2 left-12 right-12 h-1 bg-gradient-to-r from-rose-300 via-amber-300 via-emerald-300 to-blue-300 rounded-full transform -translate-y-1/2" />

                    {ageMarkers.map((marker, idx) => {
                      const position = getTimelinePosition(marker.months);
                      const clampedPosition = Math.max(5, Math.min(95, position));
                      return (
                        <div
                          key={idx}
                          className="absolute top-1/2 transform -translate-x-1/2 -translate-y-1/2"
                          style={{ left: `${clampedPosition}%` }}
                        >
                          <div className="w-0.5 h-4 bg-slate-400 mx-auto" />
                          <div className="absolute top-6 left-1/2 transform -translate-x-1/2 text-[10px] text-slate-500 font-medium whitespace-nowrap">
                            {marker.label}
                          </div>
                        </div>
                      );
                    })}

                    {sortedDevMilestones.map((milestone, index) => {
                      const config = milestoneTypeConfig[milestone.milestone_type] || milestoneTypeConfig.achievement;
                      const rawPosition = getTimelinePosition(milestone.age_months ?? 0);
                      const position = Math.max(8, Math.min(92, rawPosition));
                      const isAbove = index % 2 === 0;
                      const isSignificant = milestone.significance === 'major';

                      return (
                        <div
                          key={milestone.id}
                          className="absolute group"
                          style={{
                            left: `${position}%`,
                            top: isAbove ? '8px' : 'auto',
                            bottom: isAbove ? 'auto' : '8px',
                            transform: 'translateX(-50%)',
                          }}
                        >
                          <div
                            className={`
                              relative w-24 p-2 rounded-lg border shadow-sm bg-white
                              transition-all duration-200 cursor-pointer
                              hover:shadow-md hover:scale-105 hover:z-20
                              ${config.borderColor}
                              ${isSignificant ? 'ring-1 ring-violet-300' : ''}
                            `}
                          >
                            <div className={`
                              absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full flex items-center justify-center
                              text-white text-[10px] font-bold shadow ${config.color}
                            `}>
                              {config.icon}
                            </div>

                            <div className="text-right" dir="rtl">
                              {milestone.description_he && (
                                <div className={`text-[9px] font-semibold ${config.textColor} mb-0.5`}>
                                  {milestone.description_he}
                                </div>
                              )}
                              <p className="text-[10px] text-gray-700 font-medium leading-tight line-clamp-2">
                                {milestone.title_he?.replace(/^[◯✓⚠↓→·]\s*/, '')}
                              </p>
                            </div>
                          </div>

                          <div
                            className={`absolute left-1/2 w-px ${config.color} opacity-50`}
                            style={{
                              transform: 'translateX(-50%)',
                              top: isAbove ? '100%' : 'auto',
                              bottom: isAbove ? 'auto' : '100%',
                              height: '20px',
                            }}
                          />

                          <div
                            className={`
                              absolute left-1/2 transform -translate-x-1/2
                              w-3 h-3 rounded-full border-2 bg-white shadow
                              ${config.borderColor}
                            `}
                            style={{
                              top: isAbove ? 'calc(100% + 20px)' : 'auto',
                              bottom: isAbove ? 'auto' : 'calc(100% + 20px)',
                            }}
                          >
                            <div className={`absolute inset-0.5 rounded-full ${config.color}`} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {sortedDevMilestones.length > 3 && (
                  <div className="py-2 text-center text-[10px] text-slate-400 border-t border-slate-100">
                    ← גלול להצגת ציר הזמן המלא →
                  </div>
                )}
              </div>

              {/* Milestone List */}
              <div className="space-y-2">
                <h4 className="text-sm font-semibold text-gray-700 px-1">רשימת אבני הדרך</h4>
                <div className="space-y-1.5">
                  {sortedDevMilestones.map((milestone) => {
                    const config = milestoneTypeConfig[milestone.milestone_type] || milestoneTypeConfig.achievement;
                    return (
                      <div
                        key={milestone.id}
                        className={`
                          flex items-center gap-3 p-2.5 rounded-lg border
                          ${config.bgLight} ${config.borderColor}
                        `}
                      >
                        <div className={`w-8 h-8 rounded-full ${config.color} flex items-center justify-center text-white text-sm flex-shrink-0`}>
                          {config.icon}
                        </div>
                        <div className="flex-1 min-w-0" dir="rtl">
                          <div className="text-sm font-medium text-gray-800 truncate">
                            {milestone.title_he?.replace(/^[◯✓⚠↓→·]\s*/, '')}
                          </div>
                          <div className="text-xs text-gray-500 flex items-center gap-2">
                            <span>{milestone.description_he}</span>
                            {milestone.domain && (
                              <>
                                <span>•</span>
                                <span>{domainLabels[milestone.domain] || milestone.domain}</span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-8">
              <TrendingUp className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500 text-sm">
                עוד אין אבני דרך התפתחותיות
              </p>
              <p className="text-gray-400 text-xs mt-1">
                ספרו לנו על אבני דרך בהתפתחות הילד
              </p>
            </div>
          )}
        </div>
      )}

      {/* Stats - shown in both views */}
      {data?.days_since_start > 0 && (
        <div className="p-4 bg-gradient-to-r from-slate-50 to-gray-50 rounded-xl border border-slate-200">
          <div className="flex justify-around text-center">
            <div>
              <div className="text-2xl font-bold text-violet-600">{data.days_since_start}</div>
              <div className="text-xs text-gray-500">ימים יחד</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-teal-600">{data.total_videos || 0}</div>
              <div className="text-xs text-gray-500">סרטונים</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-amber-600">{sortedDevMilestones.length}</div>
              <div className="text-xs text-gray-500">אבני דרך</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================
// OBSERVATIONS TAB - Unified Scenario-Centric View
// ============================================

// Status translations for Hebrew
const STATUS_HEBREW = {
  'analyzed': 'נותח',
  'pending': 'ממתין לצילום',
  'uploaded': 'ממתין לניתוח',
  'validation_failed': 'לא תקין',
};

// Status colors
const STATUS_COLORS = {
  analyzed: 'bg-emerald-500',
  uploaded: 'bg-amber-500',
  pending: 'bg-violet-500',
  validation_failed: 'bg-red-500',
};

/**
 * Unified ScenarioCard - Shows the full journey of a scenario:
 * hypothesis context → guidelines → video → analysis results
 */
function ScenarioCard({ scenario, onUpload, onAnalyze, onRemove, uploadProgress, uploadingScenarioId, analyzingScenarioId }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showRemoveConfirm, setShowRemoveConfirm] = useState(false);
  const videoRef = useRef(null);

  // Determine state from scenario data
  const hasVideo = !!scenario.video_path;
  const isAnalyzed = scenario.status === 'analyzed';
  const isPendingAnalysis = scenario.status === 'uploaded';
  const isPendingFilming = scenario.status === 'pending';
  const isValidationFailed = scenario.status === 'validation_failed';
  // Get scenario ID (try different field names, matching handleUpload)
  const scenarioId = scenario.id || scenario.scenario_id || scenario.title;
  const isUploadingThis = uploadingScenarioId === scenarioId;
  const isAnalyzingThis = analyzingScenarioId === scenarioId || analyzingScenarioId === 'all';

  // Get the most relevant date (uploaded_at for videos, created_at for pending)
  const dateToShow = scenario.uploaded_at || scenario.created_at;
  const relativeTime = getRelativeTimeHebrew(dateToShow);
  const formattedDateTime = formatDateTimeHebrew(dateToShow);

  // Fullscreen handler
  const handleFullscreen = useCallback(() => {
    if (videoRef.current) {
      if (videoRef.current.requestFullscreen) {
        videoRef.current.requestFullscreen();
      } else if (videoRef.current.webkitEnterFullscreen) {
        // iOS Safari
        videoRef.current.webkitEnterFullscreen();
      }
    }
  }, []);

  return (
    <div className={`
      bg-white rounded-2xl border-2 overflow-hidden transition-all duration-200
      ${isAnalyzed ? 'border-emerald-200 hover:border-emerald-300' :
        isPendingAnalysis ? 'border-amber-200 hover:border-amber-300' :
        isValidationFailed ? 'border-red-200 hover:border-red-300' :
        'border-violet-200 hover:border-violet-300'}
    `}>
      {/* HEADER - always visible */}
      <div
        className="p-4 cursor-pointer hover:bg-gray-50/50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            {/* Hypothesis context - what we're exploring */}
            {scenario.hypothesis_title && (
              <div className="text-xs text-gray-400 mb-1 flex items-center gap-1 truncate">
                <Lightbulb className="w-3 h-3 flex-shrink-0" />
                <span className="truncate">{scenario.hypothesis_title}</span>
              </div>
            )}

            {/* Scenario title */}
            <h4 className="font-bold text-gray-800">{scenario.title}</h4>

            {/* Status + video indicator */}
            <div className="flex items-center gap-2 mt-2 flex-wrap">
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium text-white ${STATUS_COLORS[scenario.status] || 'bg-gray-500'}`}>
                {STATUS_HEBREW[scenario.status] || scenario.status}
              </span>
              {hasVideo && (
                <span className="text-xs text-gray-400 flex items-center gap-1">
                  <Video className="w-3 h-3" />
                  יש סרטון
                </span>
              )}
              {relativeTime && (
                <span className="text-xs text-gray-400 flex items-center gap-1" title={formattedDateTime}>
                  <Clock className="w-3 h-3" />
                  {relativeTime}
                </span>
              )}
            </div>
          </div>

          <ChevronRight className={`w-5 h-5 text-gray-400 transition-transform duration-200 flex-shrink-0 ${isExpanded ? 'rotate-90' : ''}`} />
        </div>
      </div>

      {/* EXPANDED CONTENT */}
      {isExpanded && (
        <div className="border-t border-gray-100 animate-expandIn" onClick={(e) => e.stopPropagation()}>

          {/* GUIDELINES SECTION - always available */}
          {scenario.what_to_film && (
            <div className="p-4 bg-violet-50/50">
              <h5 className="font-semibold text-violet-900 text-sm mb-2 flex items-center gap-1">
                <FileText className="w-4 h-4" />
                הנחיות צילום
              </h5>
              <p className="text-sm text-violet-800 leading-relaxed">{scenario.what_to_film}</p>
              {scenario.rationale_for_parent && (
                <p className="text-sm text-indigo-700 mt-2">
                  <span className="font-medium">💡 למה זה חשוב: </span>
                  {scenario.rationale_for_parent}
                </p>
              )}
              {scenario.duration_suggestion && (
                <div className="mt-2 flex items-center gap-1 text-xs text-violet-600">
                  <Clock className="w-3 h-3" />
                  {scenario.duration_suggestion}
                </div>
              )}
            </div>
          )}

          {/* VIDEO SECTION - if uploaded */}
          {hasVideo && (
            <div className="p-4 border-t border-gray-100">
              {/* Video wrapper - constrains both video and buttons to same width */}
              <div className="max-w-lg">
                {/* Video container with controls overlay */}
                <div className="relative group overflow-hidden rounded-lg">
                  <video
                    ref={videoRef}
                    src={getVideoUrl(scenario.video_path)}
                    controls
                    playsInline
                    className="w-full h-auto bg-black object-contain"
                    style={{ maxHeight: '400px' }}
                  />
                  {/* Fullscreen button overlay */}
                  <button
                    onClick={handleFullscreen}
                    className="absolute top-2 left-2 p-2 bg-black/50 hover:bg-black/70 rounded-lg text-white opacity-0 group-hover:opacity-100 transition-opacity"
                    title="מסך מלא"
                  >
                    <Maximize2 className="w-5 h-5" />
                  </button>
                </div>

                {/* Video action buttons - same width as video */}
                <div className="mt-3 flex items-center gap-2">
                  {/* Analyze button if pending analysis */}
                  {isPendingAnalysis && onAnalyze && (
                    <button
                      onClick={() => onAnalyze(scenario)}
                      disabled={isAnalyzingThis}
                      className={`flex-1 py-2 rounded-lg font-medium transition-colors flex items-center justify-center gap-2
                        ${isAnalyzingThis
                          ? 'bg-indigo-400 text-white cursor-wait'
                          : 'bg-indigo-600 text-white hover:bg-indigo-700'}`}
                    >
                      {isAnalyzingThis ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          מנתח...
                        </>
                      ) : (
                        <>
                          <Brain className="w-4 h-4" />
                          נתח סרטון
                        </>
                      )}
                    </button>
                  )}

                  {/* Replace video */}
                  <label className="cursor-pointer">
                    <input
                      type="file"
                      accept="video/*"
                      onChange={(e) => {
                        if (e.target.files?.[0]) {
                          onUpload(e.target.files[0], scenario);
                        }
                      }}
                      className="hidden"
                      disabled={isUploadingThis}
                    />
                    <div className={`
                      px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-gray-700
                      transition-colors flex items-center gap-1.5 text-sm
                      ${isUploadingThis ? 'opacity-50 cursor-not-allowed' : ''}
                    `}>
                      <RefreshCw className="w-4 h-4" />
                      החלף
                    </div>
                  </label>

                  {/* Remove video - only if not analyzed */}
                  {!isAnalyzed && onRemove && (
                    <button
                      onClick={() => setShowRemoveConfirm(true)}
                      className="px-3 py-2 bg-red-50 hover:bg-red-100 rounded-lg text-red-600
                        transition-colors flex items-center gap-1.5 text-sm"
                    >
                      <Trash2 className="w-4 h-4" />
                      מחק
                    </button>
                  )}
                </div>

                {/* Remove confirmation */}
                {showRemoveConfirm && (
                  <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-sm text-red-800 mb-2">בטוח שברצונך למחוק את הסרטון?</p>
                    <div className="flex gap-2">
                      <button
                        onClick={() => {
                          onRemove(scenario);
                          setShowRemoveConfirm(false);
                        }}
                        className="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
                      >
                        כן, מחק
                      </button>
                      <button
                        onClick={() => setShowRemoveConfirm(false)}
                        className="px-3 py-1 bg-gray-200 text-gray-700 rounded text-sm hover:bg-gray-300"
                      >
                        ביטול
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Validation failed - comprehensive explanation */}
              {isValidationFailed && (
                <div className="mt-3 space-y-3">
                  {/* What went wrong - clear header */}
                  <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl">
                    <h5 className="font-semibold text-amber-900 text-sm mb-2 flex items-center gap-2">
                      <span className="text-lg">⚠️</span>
                      הסרטון לא תואם לבקשה
                    </h5>

                    {/* What the video actually shows */}
                    {scenario.what_video_shows && (
                      <div className="mb-3">
                        <p className="text-xs text-amber-700 font-medium mb-1">מה הסרטון מראה:</p>
                        <p className="text-sm text-amber-900 bg-white/50 rounded-lg px-3 py-2">
                          {scenario.what_video_shows}
                        </p>
                      </div>
                    )}

                    {/* Specific validation issues */}
                    {scenario.validation_issues?.length > 0 && (
                      <div className="mb-3">
                        <p className="text-xs text-amber-700 font-medium mb-1">מה חסר:</p>
                        <ul className="space-y-1">
                          {scenario.validation_issues.map((issue, idx) => (
                            <li key={idx} className="text-sm text-amber-900 flex items-start gap-2">
                              <span className="text-amber-500 flex-shrink-0">•</span>
                              <span>{issue}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Reminder of what was requested */}
                    {scenario.what_to_film && (
                      <div className="pt-3 border-t border-amber-200">
                        <p className="text-xs text-amber-700 font-medium mb-1">מה ביקשנו לצלם:</p>
                        <p className="text-sm text-amber-900">{scenario.what_to_film}</p>
                      </div>
                    )}
                  </div>

                  {/* Clear call to action */}
                  <div className="text-center text-sm text-gray-600">
                    נסו להעלות סרטון חדש שמתאים להנחיות
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ANALYSIS RESULTS - if analyzed */}
          {isAnalyzed && scenario.observations?.length > 0 && (
            <div className="p-4 bg-emerald-50/50">
              <h5 className="font-semibold text-emerald-900 text-sm mb-2 flex items-center gap-1">
                <Eye className="w-4 h-4" />
                מה ראינו
              </h5>
              <div className="space-y-2">
                {scenario.observations.map((obs, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-sm">
                    <span className="text-emerald-600 font-mono text-xs flex-shrink-0">{obs.timestamp_start}</span>
                    <span className="text-gray-700">{obs.content}</span>
                  </div>
                ))}
              </div>
              {/* Strengths */}
              {scenario.strengths_observed?.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1">
                  {scenario.strengths_observed.map((strength, idx) => (
                    <span key={idx} className="px-2 py-0.5 bg-pink-100 text-pink-700 rounded-full text-xs">
                      {strength}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* UPLOAD SECTION - if pending filming or re-upload */}
          {(isPendingFilming || isValidationFailed) && (
            <div className="p-4">
              <div className="flex gap-2">
                <label className="flex-1 cursor-pointer">
                  <input
                    type="file"
                    accept="video/*"
                    capture="environment"
                    onChange={(e) => {
                      if (e.target.files?.[0]) {
                        onUpload(e.target.files[0], scenario);
                      }
                    }}
                    className="hidden"
                    disabled={isUploadingThis}
                  />
                  <div className={`
                    py-3 bg-gradient-to-r from-violet-500 to-purple-500 text-white font-bold rounded-xl
                    text-center transition-all flex items-center justify-center gap-2
                    ${isUploadingThis ? 'opacity-50 cursor-not-allowed' : 'hover:from-violet-600 hover:to-purple-600'}
                  `}>
                    <Camera className="w-5 h-5" />
                    צלם
                  </div>
                </label>
                <label className="flex-1 cursor-pointer">
                  <input
                    type="file"
                    accept="video/*"
                    onChange={(e) => {
                      if (e.target.files?.[0]) {
                        onUpload(e.target.files[0], scenario);
                      }
                    }}
                    className="hidden"
                    disabled={isUploadingThis}
                  />
                  <div className={`
                    py-3 bg-white border-2 border-violet-300 text-violet-700 font-bold rounded-xl
                    text-center transition-all flex items-center justify-center gap-2
                    ${isUploadingThis ? 'opacity-50 cursor-not-allowed' : 'hover:bg-violet-50'}
                  `}>
                    <Upload className="w-5 h-5" />
                    בחר קובץ
                  </div>
                </label>
              </div>

              {/* Upload progress */}
              {isUploadingThis && (
                <div className="mt-3">
                  <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-violet-500 to-purple-500 transition-all duration-300"
                      style={{ width: `${Math.max(uploadProgress, 5)}%` }}
                    />
                  </div>
                  <p className="text-sm text-gray-500 mt-1 text-center">
                    {uploadProgress > 0 ? `מעלה... ${uploadProgress}%` : 'מתחיל העלאה...'}
                  </p>
                </div>
              )}
            </div>
          )}

        </div>
      )}
    </div>
  );
}

function ObservationsTab({ data, onUpload, onAnalyze, onRemove, uploadProgress, uploadingScenarioId }) {
  // Track which scenario is being analyzed
  const [analyzingScenarioId, setAnalyzingScenarioId] = useState(null);

  // Wrapper for analyze that tracks loading state
  const handleAnalyze = useCallback(async (scenario) => {
    if (!onAnalyze) return;
    const scenarioId = scenario?.id || scenario?.scenario_id || scenario?.title || 'all';
    setAnalyzingScenarioId(scenarioId);
    try {
      await onAnalyze(scenario);
    } finally {
      setAnalyzingScenarioId(null);
    }
  }, [onAnalyze]);

  // Merge videos and pending scenarios into unified list
  const allScenarios = useMemo(() => {
    const scenarios = [];

    // Add videos (which are scenarios with uploaded videos)
    for (const video of (data?.videos || [])) {
      scenarios.push({
        ...video,
        video_path: video.video_path,
        observations: video.observations || [],
      });
    }

    // Add pending scenarios (no video yet)
    for (const pending of (data?.pending_scenarios || [])) {
      scenarios.push({
        ...pending,
        status: pending.status || 'pending',
        video_path: null,
      });
    }

    // Sort: pending first, then by date (newest first)
    return scenarios.sort((a, b) => {
      // Pending filming first
      if (a.status === 'pending' && b.status !== 'pending') return -1;
      if (b.status === 'pending' && a.status !== 'pending') return 1;
      // Then pending analysis
      if (a.status === 'uploaded' && b.status === 'analyzed') return -1;
      if (b.status === 'uploaded' && a.status === 'analyzed') return 1;
      // Then by date (newest first)
      const dateA = new Date(a.uploaded_at || a.created_at || 0);
      const dateB = new Date(b.uploaded_at || b.created_at || 0);
      return dateB - dateA;
    });
  }, [data]);

  // Empty state
  if (allScenarios.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 px-8">
        <div className="w-20 h-20 bg-gradient-to-br from-emerald-100 to-teal-100 rounded-full flex items-center justify-center mb-4 animate-gentleFloat">
          <Video className="w-10 h-10 text-emerald-400" />
        </div>
        <p className="text-gray-500 text-center">
          עוד לא העלינו סרטונים...<br />
          סרטונים עוזרים לנו לראות את מה שמילים לא יכולות לתאר
        </p>
      </div>
    );
  }

  const pendingFilmingCount = data?.pending_scenarios?.length || 0;
  const pendingAnalysisCount = data?.pending_count || 0;
  const analyzedCount = data?.analyzed_count || 0;

  return (
    <div className="space-y-6 pb-8">
      {/* Stats header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-3 flex-wrap">
          {pendingFilmingCount > 0 && (
            <span className="px-3 py-1 bg-violet-100 text-violet-700 rounded-full text-sm flex items-center gap-1">
              <Camera className="w-3.5 h-3.5" />
              {pendingFilmingCount} ממתינים לצילום
            </span>
          )}
          {pendingAnalysisCount > 0 && (
            <span className="px-3 py-1 bg-amber-100 text-amber-700 rounded-full text-sm flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" />
              {pendingAnalysisCount} ממתינים לניתוח
            </span>
          )}
          {analyzedCount > 0 && (
            <span className="px-3 py-1 bg-emerald-100 text-emerald-700 rounded-full text-sm flex items-center gap-1">
              <Check className="w-3.5 h-3.5" />
              {analyzedCount} נותחו
            </span>
          )}
        </div>

        {/* Batch analyze button */}
        {pendingAnalysisCount > 0 && onAnalyze && (
          <button
            onClick={() => handleAnalyze(null)}
            disabled={!!analyzingScenarioId}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2
              ${analyzingScenarioId
                ? 'bg-indigo-400 text-white cursor-wait'
                : 'bg-indigo-600 text-white hover:bg-indigo-700'}`}
          >
            {analyzingScenarioId === 'all' ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                מנתח...
              </>
            ) : (
              <>
                <Brain className="w-4 h-4" />
                נתח הכל
              </>
            )}
          </button>
        )}
      </div>

      {/* Unified scenario cards */}
      <div className="space-y-4 max-w-2xl">
        {allScenarios.map((scenario, idx) => (
          <div
            key={scenario.id || idx}
            className="opacity-0 animate-staggerIn"
            style={{ animationDelay: `${idx * 0.05}s`, animationFillMode: 'forwards' }}
          >
            <ScenarioCard
              scenario={scenario}
              onUpload={onUpload}
              onAnalyze={handleAnalyze}
              onRemove={onRemove}
              uploadProgress={uploadProgress}
              uploadingScenarioId={uploadingScenarioId}
              analyzingScenarioId={analyzingScenarioId}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

// Helper function for Hebrew relative time
function getRelativeTimeHebrew(dateString) {
  if (!dateString) return null;
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));

  if (diffDays === 0) {
    if (diffHours < 1) return 'עכשיו';
    if (diffHours === 1) return 'לפני שעה';
    return `לפני ${diffHours} שעות`;
  }
  if (diffDays === 1) return 'אתמול';
  if (diffDays === 2) return 'שלשום';
  if (diffDays < 7) return `לפני ${diffDays} ימים`;
  if (diffDays < 14) return 'לפני שבוע';
  return `לפני ${Math.floor(diffDays / 7)} שבועות`;
}

// Helper function for formatted datetime in Hebrew locale
function formatDateTimeHebrew(dateString) {
  if (!dateString) return null;
  const date = new Date(dateString);
  // Format: DD/MM/YY HH:MM
  const day = date.getDate().toString().padStart(2, '0');
  const month = (date.getMonth() + 1).toString().padStart(2, '0');
  const year = date.getFullYear().toString().slice(-2);
  const hours = date.getHours().toString().padStart(2, '0');
  const minutes = date.getMinutes().toString().padStart(2, '0');
  return `${day}/${month}/${year} ${hours}:${minutes}`;
}

// ============================================
// STYLED SUMMARY RENDERER - Beautiful HTML
// ============================================

function StyledSummary({ content, recipientType }) {
  // Parse markdown-like content into styled HTML
  const renderContent = () => {
    if (!content) return null;

    const lines = content.split('\n');
    const elements = [];
    let bulletList = [];

    // Helper to format inline bold text
    const formatInlineText = (text) => {
      if (!text) return null;
      // Match **bold** patterns
      const parts = text.split(/\*\*(.*?)\*\*/);
      return parts.map((part, i) =>
        i % 2 === 1 ? <strong key={i} className="font-semibold text-gray-900">{part}</strong> : part
      );
    };

    const flushBulletList = () => {
      if (bulletList.length > 0) {
        elements.push(
          <ul key={`bullets-${elements.length}`} className="space-y-3 my-4">
            {bulletList.map((item, idx) => (
              <li key={idx} className="flex items-start gap-3">
                <span className="w-2 h-2 mt-2 rounded-full bg-gradient-to-r from-indigo-400 to-purple-400 flex-shrink-0" />
                <span className="text-gray-700 leading-relaxed">{item}</span>
              </li>
            ))}
          </ul>
        );
        bulletList = [];
      }
    };

    lines.forEach((line, idx) => {
      const trimmed = line.trim();

      // Skip empty lines
      if (!trimmed) {
        flushBulletList();
        return;
      }

      // Headers: ### or ## or standalone **Header**
      const headerMatch = trimmed.match(/^(#{1,3})\s*(\d+\.)?\s*(.+)$/);
      if (headerMatch) {
        flushBulletList();
        const level = headerMatch[1].length;
        const number = headerMatch[2] || '';
        const headerText = headerMatch[3].replace(/\*\*/g, ''); // Remove any bold markers

        elements.push(
          <div key={`header-${idx}`} className={`${level <= 2 ? 'mt-6' : 'mt-5'} mb-3`}>
            <h4 className={`font-bold ${level <= 2 ? 'text-lg' : 'text-base'} text-gray-800 flex items-center gap-2`}>
              <span className={`w-1 ${level <= 2 ? 'h-6' : 'h-5'} bg-gradient-to-b from-indigo-500 to-purple-500 rounded-full`} />
              {number && <span className="text-indigo-600">{number}</span>}
              {headerText}
            </h4>
          </div>
        );
        return;
      }

      // Standalone bold line as subheader: **Text**
      if (trimmed.startsWith('**') && trimmed.endsWith('**') && !trimmed.includes(':')) {
        flushBulletList();
        const headerText = trimmed.slice(2, -2);
        elements.push(
          <h5 key={`subheader-${idx}`} className="font-bold text-gray-800 mt-4 mb-2 flex items-center gap-2">
            <span className="w-1 h-4 bg-gradient-to-b from-indigo-400 to-purple-400 rounded-full" />
            {headerText}
          </h5>
        );
        return;
      }

      // Definition-style line: **Term**: Description or **Term (English)**: Description
      const definitionMatch = trimmed.match(/^\*\*(.+?)\*\*:\s*(.+)$/);
      if (definitionMatch) {
        const term = definitionMatch[1];
        const description = definitionMatch[2];
        bulletList.push(
          <span key={idx}>
            <strong className="font-semibold text-gray-900">{term}:</strong>{' '}
            {formatInlineText(description)}
          </span>
        );
        return;
      }

      // Bullet points: • or - or *
      if (trimmed.startsWith('• ') || trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
        const bulletText = trimmed.replace(/^[•\-\*]\s*/, '');
        bulletList.push(formatInlineText(bulletText));
        return;
      }

      // Regular paragraph
      flushBulletList();
      elements.push(
        <p key={`para-${idx}`} className="text-gray-700 leading-relaxed my-3">
          {formatInlineText(trimmed)}
        </p>
      );
    });

    flushBulletList();
    return elements;
  };

  // Get color scheme based on recipient type
  const colorSchemes = {
    professional: { gradient: 'from-blue-50 to-indigo-50', border: 'border-indigo-200', accent: 'text-indigo-600', headerBg: 'bg-indigo-100' },
    educational: { gradient: 'from-emerald-50 to-teal-50', border: 'border-emerald-200', accent: 'text-emerald-600', headerBg: 'bg-emerald-100' },
    family: { gradient: 'from-pink-50 to-rose-50', border: 'border-rose-200', accent: 'text-rose-600', headerBg: 'bg-rose-100' },
    peer: { gradient: 'from-purple-50 to-violet-50', border: 'border-purple-200', accent: 'text-purple-600', headerBg: 'bg-purple-100' },
  };

  const scheme = colorSchemes[recipientType] || colorSchemes.professional;

  return (
    <div className={`bg-gradient-to-br ${scheme.gradient} rounded-2xl border ${scheme.border} shadow-sm overflow-hidden`}>
      {/* Decorative header bar */}
      <div className={`h-1.5 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500`} />

      {/* Content */}
      <div className="p-6 text-base">
        {renderContent()}
      </div>

      {/* Decorative footer */}
      <div className="px-6 py-4 border-t border-gray-200/50 bg-white/30">
        <p className={`text-xs ${scheme.accent} flex items-center gap-1.5`}>
          <Sparkles className="w-3.5 h-3.5" />
          נוצר על ידי צ'יטה
        </p>
      </div>
    </div>
  );
}

// ============================================
// SHARE TAB - Crystal-Driven Sharing
// ============================================

// Fallback expert suggestions for when crystal doesn't have recommendations
const FALLBACK_EXPERT_OPTIONS = [
  { id: 'ot', label: 'מרפא/ת בעיסוק', profession: 'מרפא בעיסוק' },
  { id: 'psychologist', label: 'פסיכולוג/ית', profession: 'פסיכולוג' },
  { id: 'speech', label: 'קלינאי/ת תקשורת', profession: 'קלינאי תקשורת' },
  { id: 'neurologist', label: 'נוירולוג/ית', profession: 'נוירולוג' },
  { id: 'kindergarten', label: 'גננת', profession: 'גננת' },
  { id: 'teacher', label: 'מורה', profession: 'מורה' },
  { id: 'grandparent', label: 'סבא/סבתא', profession: 'סבא או סבתא' },
  { id: 'family', label: 'בן/בת משפחה', profession: 'בן משפחה' },
];

function ShareTab({ data, familyId, onGenerateSummary, onStartGuidedCollection }) {
  const [selectedExpert, setSelectedExpert] = useState(null);
  const [customExpert, setCustomExpert] = useState('');
  const [showCustomInput, setShowCustomInput] = useState(false);
  const [additionalContext, setAdditionalContext] = useState('');
  const [isComprehensive, setIsComprehensive] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedContent, setGeneratedContent] = useState(null);  // Legacy text
  const [structuredSummary, setStructuredSummary] = useState(null);  // New structured data
  const [copied, setCopied] = useState(false);
  const [viewingSavedSummary, setViewingSavedSummary] = useState(null);
  const [loadingSavedSummary, setLoadingSavedSummary] = useState(false);
  // Track newly generated summaries in this session (prepended to the list)
  const [newSummaries, setNewSummaries] = useState([]);
  // Gap detection state
  const [showGapWarning, setShowGapWarning] = useState(false);
  const [gapData, setGapData] = useState(null);
  const [isCheckingReadiness, setIsCheckingReadiness] = useState(false);
  const [isStartingChat, setIsStartingChat] = useState(false);

  const canGenerate = data?.can_generate !== false;
  // Combine new summaries (most recent first) with existing ones from server
  const previousSummaries = [...newSummaries, ...(data?.previous_summaries || [])];
  const hasPreviousSummaries = previousSummaries.length > 0;

  // Expert recommendations flow from Crystal → Share (unified experience)
  // Same experts shown in Crystal's "מי צריך לראות את הילד הזה" appear here
  const recommendedExperts = data?.expert_recommendations || [];
  const hasRecommendedExperts = recommendedExperts.length > 0;

  const handleViewSavedSummary = async (summaryId) => {
    setLoadingSavedSummary(true);
    try {
      const response = await fetch(`/api/family/${familyId}/child-space/share/summaries/${summaryId}`);
      if (response.ok) {
        const summary = await response.json();
        setViewingSavedSummary(summary);
      }
    } catch (error) {
      console.error('Error loading saved summary:', error);
    } finally {
      setLoadingSavedSummary(false);
    }
  };

  // Map expert types to backend recipient_type for readiness check
  const getRecipientType = (expert) => {
    if (!expert) return 'default';
    const id = expert.id || '';
    // Map to backend-expected types
    if (id === 'neurologist' || expert.profession?.includes('נוירולוג')) return 'neurologist';
    if (id === 'speech' || expert.profession?.includes('תקשורת')) return 'speech_therapist';
    if (id === 'ot' || expert.profession?.includes('עיסוק')) return 'ot';
    if (id === 'pediatrician' || expert.profession?.includes('ילדים')) return 'pediatrician';
    return 'default';
  };

  const handleGenerate = async (skipReadinessCheck = false, overrideGaps = null) => {
    const expertDescription = selectedExpert
      ? (selectedExpert.profession + (selectedExpert.specialization ? ` (${selectedExpert.specialization})` : ''))
      : customExpert;

    if (!expertDescription) return;

    // Step 1: Check readiness (unless we're skipping because user chose "generate anyway")
    if (!skipReadinessCheck) {
      const recipientType = getRecipientType(selectedExpert);

      // Only check readiness for clinical professionals
      if (recipientType !== 'default') {
        setIsCheckingReadiness(true);
        try {
          const readiness = await api.checkSummaryReadiness(familyId, recipientType);

          // Show warning if there are missing critical OR important items
          const hasMissingItems =
            (readiness.missing_critical?.length > 0) ||
            (readiness.missing_important?.length > 0);

          if (hasMissingItems) {
            // Combine critical and important for display, critical first
            const allMissing = [
              ...(readiness.missing_critical || []),
              ...(readiness.missing_important || [])
            ];
            setGapData({
              ...readiness,
              missing_critical: allMissing, // Use combined list for display
            });
            setShowGapWarning(true);
            setIsCheckingReadiness(false);
            return; // Don't proceed - wait for user decision
          }
        } catch (error) {
          console.error('Error checking readiness:', error);
          // Continue with generation even if readiness check fails
        } finally {
          setIsCheckingReadiness(false);
        }
      }
    }

    // Step 2: Generate the summary
    setIsGenerating(true);
    try {
      // Pass the full expert info and let backend determine appropriate style
      const result = await onGenerateSummary({
        expert: selectedExpert || { customDescription: customExpert },
        expertDescription,
        context: additionalContext,
        comprehensive: isComprehensive,
        // Pass crystal insights for context
        crystalInsights: selectedExpert ? {
          why_this_match: selectedExpert.why_this_match,
          recommended_approach: selectedExpert.recommended_approach,
          summary_for_professional: selectedExpert.summary_for_professional,
        } : null,
        // Pass gaps if user chose "generate anyway" - LLM will note what's missing
        missingGaps: overrideGaps || null,
      });
      // Store both structured and legacy formats
      setStructuredSummary(result.structured || null);
      setGeneratedContent(result.content);

      // Add the new summary to the list for immediate UI update
      if (result.saved_summary) {
        setNewSummaries(prev => [result.saved_summary, ...prev]);
      }
    } catch (error) {
      console.error('Error generating summary:', error);
    } finally {
      setIsGenerating(false);
      setShowGapWarning(false);
      setGapData(null);
    }
  };

  const handleGenerateAnyway = () => {
    // User chose to generate despite gaps - pass the gaps so LLM can note them
    handleGenerate(true, gapData?.missing_critical);
  };

  const handleAddInChat = async () => {
    // User chose to add missing info in chat - start guided collection mode
    const recipientType = getRecipientType(selectedExpert);
    setIsStartingChat(true);
    try {
      // Call API to set the guided collection session flag and get greeting
      const response = await api.startGuidedCollection(familyId, recipientType);

      // If callback provided, pass the greeting so Chitta speaks first
      if (onStartGuidedCollection) {
        onStartGuidedCollection(response.greeting);
      } else {
        // Otherwise, show message and close the warning
        alert('עברו לשיחה כדי להשלים את המידע החסר. כשתסיימו, תוכלו לחזור לכאן ליצור את הסיכום.');
      }
      setShowGapWarning(false);
      setGapData(null);
    } catch (error) {
      console.error('Error starting guided collection:', error);
      alert('אירעה שגיאה. נסו שוב.');
    } finally {
      setIsStartingChat(false);
    }
  };

  const handleCopy = () => {
    if (generatedContent) {
      navigator.clipboard.writeText(generatedContent);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handlePrint = () => {
    if (!generatedContent && !structuredSummary) return;
    const printWindow = window.open('', '_blank');

    // Use professional print format if we have structured data
    if (structuredSummary) {
      printWindow.document.write(ProfessionalSummaryPrint({ data: structuredSummary }));
    } else {
      // Fallback to legacy format
      const expertName = selectedExpert?.profession || customExpert || 'איש מקצוע';
      printWindow.document.write(`
        <!DOCTYPE html>
        <html dir="rtl" lang="he">
        <head>
          <meta charset="UTF-8">
          <title>סיכום ל${expertName}</title>
          <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; line-height: 1.8; }
            h1 { font-size: 1.5em; border-bottom: 2px solid #333; padding-bottom: 10px; }
            p { margin: 0.5em 0; white-space: pre-wrap; }
          </style>
        </head>
        <body>
          <h1>סיכום ל${expertName}</h1>
          <p>${generatedContent}</p>
        </body>
        </html>
      `);
    }
    printWindow.document.close();
    printWindow.print();
  };

  const handleBack = () => {
    if (viewingSavedSummary) {
      setViewingSavedSummary(null);
    } else if (generatedContent || structuredSummary) {
      // Reset all the way to expert list - don't stop at intermediate state
      setGeneratedContent(null);
      setStructuredSummary(null);
      setSelectedExpert(null);
      setCustomExpert('');
      setShowCustomInput(false);
    } else if (selectedExpert || customExpert) {
      setSelectedExpert(null);
      setCustomExpert('');
      setShowCustomInput(false);
    }
  };

  // View saved summary
  if (viewingSavedSummary) {
    return (
      <div className="pb-8 opacity-0 animate-fadeIn" style={{ animationFillMode: 'forwards' }}>
        <div className="flex items-center justify-between mb-4">
          <button
            onClick={handleBack}
            className="flex items-center gap-1 text-gray-500 hover:text-gray-700 transition"
          >
            <ChevronRight className="w-4 h-4" />
            חזרה
          </button>
          <button
            onClick={() => {
              navigator.clipboard.writeText(viewingSavedSummary.content);
              setCopied(true);
              setTimeout(() => setCopied(false), 2000);
            }}
            className={`
              flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition
              ${copied ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}
            `}
          >
            {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
            {copied ? 'הועתק!' : 'העתק'}
          </button>
        </div>

        <h3 className="font-bold text-xl text-gray-800 mb-2 flex items-center gap-2">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center">
            <FileText className="w-5 h-5 text-white" />
          </div>
          סיכום ל{viewingSavedSummary.recipient}
        </h3>
        <p className="text-sm text-gray-500 mb-4">
          {formatDate(viewingSavedSummary.created_at)}
          {viewingSavedSummary.comprehensive && ' • מקיף'}
        </p>

        <StyledSummary content={viewingSavedSummary.content} recipientType="professional" />

        <div className="flex gap-2 mt-6">
          <button
            onClick={() => {
              navigator.clipboard.writeText(viewingSavedSummary.content);
              setCopied(true);
              setTimeout(() => setCopied(false), 2000);
            }}
            className="flex-1 flex items-center justify-center gap-2 py-3 bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 rounded-xl font-medium transition shadow-sm"
          >
            <Copy className="w-4 h-4" />
            העתק
          </button>
          <button
            onClick={() => {
              const text = encodeURIComponent(viewingSavedSummary.content);
              window.open(`https://wa.me/?text=${text}`, '_blank');
            }}
            className="flex-1 flex items-center justify-center gap-2 py-3 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white rounded-xl font-medium transition shadow-lg shadow-emerald-500/25"
          >
            <Send className="w-4 h-4" />
            וואטסאפ
          </button>
        </div>
      </div>
    );
  }

  // Not ready state
  if (!canGenerate) {
    return (
      <div className="flex flex-col items-center justify-center py-16 px-8">
        <div className="w-20 h-20 bg-gradient-to-br from-pink-100 to-rose-100 rounded-full flex items-center justify-center mb-4 animate-gentleFloat">
          <Share2 className="w-10 h-10 text-pink-400" />
        </div>
        <p className="text-gray-500 text-center">
          {data?.not_ready_reason || 'עוד לא צברנו מספיק הבנה לשיתוף...'}
        </p>
      </div>
    );
  }

  // Gap warning modal - shown when clinical data is missing
  if (showGapWarning && gapData) {
    const expertName = selectedExpert?.profession || customExpert || 'איש מקצוע';
    return (
      <div className="pb-8 opacity-0 animate-fadeIn" style={{ animationFillMode: 'forwards' }}>
        <button
          onClick={() => {
            setShowGapWarning(false);
            setGapData(null);
          }}
          className="flex items-center gap-1 text-gray-500 hover:text-gray-700 mb-4 transition"
        >
          <ChevronRight className="w-4 h-4" />
          חזרה
        </button>

        {/* Warning card */}
        <div className="bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200 rounded-2xl p-6 mb-6">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-400 to-orange-400 flex items-center justify-center flex-shrink-0">
              <AlertTriangle className="w-6 h-6 text-white" />
            </div>
            <div className="flex-1">
              <h3 className="font-bold text-lg text-gray-800 mb-2">
                יש מידע שיכול לעזור
              </h3>
              <p className="text-gray-600 text-sm mb-4">
                כדי שהסיכום ל{expertName} יהיה שימושי יותר, היה עוזר אם נדע גם על:
              </p>

              {/* Missing items list */}
              <ul className="space-y-2 mb-4">
                {gapData.missing_critical?.map((gap, idx) => (
                  <li key={idx} className="flex items-center gap-2 text-sm">
                    <span className="w-2 h-2 rounded-full bg-amber-400 flex-shrink-0" />
                    <span className="text-gray-700">{gap.description || gap.parent_description}</span>
                  </li>
                ))}
              </ul>

              {gapData.guidance_message && (
                <p className="text-xs text-amber-700 italic">
                  {gapData.guidance_message}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Action buttons */}
        <div className="space-y-3">
          <button
            onClick={handleAddInChat}
            disabled={isStartingChat}
            className="w-full py-4 bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600 disabled:from-indigo-400 disabled:to-purple-400 text-white rounded-xl font-bold transition shadow-lg hover:shadow-xl flex items-center justify-center gap-2"
          >
            {isStartingChat ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                מכין שאלה...
              </>
            ) : (
              <>
                <MessageSquare className="w-5 h-5" />
                הוסף פרטים בשיחה
              </>
            )}
          </button>

          <button
            onClick={handleGenerateAnyway}
            disabled={isGenerating}
            className="w-full py-3 bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 rounded-xl font-medium transition flex items-center justify-center gap-2"
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                יוצר סיכום...
              </>
            ) : (
              <>
                <Share2 className="w-4 h-4" />
                צור סיכום עם מה שיש
              </>
            )}
          </button>

          <p className="text-xs text-gray-500 text-center">
            הסיכום יציין מה עדיין לא ידוע לנו
          </p>
        </div>
      </div>
    );
  }

  // Generated content view
  if (generatedContent || structuredSummary) {
    const expertName = selectedExpert?.profession || customExpert || 'איש מקצוע';
    return (
      <div className="pb-8 opacity-0 animate-fadeIn" style={{ animationFillMode: 'forwards' }}>
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <button
            onClick={handleBack}
            className="flex items-center gap-1 text-gray-500 hover:text-gray-700 transition"
          >
            <ChevronRight className="w-4 h-4" />
            חזרה
          </button>
          <div className="flex gap-2">
            <button
              onClick={handleCopy}
              className={`
                flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition
                ${copied ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}
              `}
            >
              {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              {copied ? 'הועתק!' : 'העתק'}
            </button>
          </div>
        </div>

        {/* Professional Summary - Use structured if available, fallback to legacy */}
        {structuredSummary ? (
          <ProfessionalSummary data={structuredSummary} copied={copied} />
        ) : (
          <div className="prose prose-gray max-w-none" dir="rtl">
            <pre className="whitespace-pre-wrap font-sans text-gray-700 leading-relaxed bg-gray-50 rounded-xl p-6">
              {generatedContent}
            </pre>
          </div>
        )}

        {/* Share buttons */}
        <div className="flex gap-2 mt-8">
          <button
            onClick={handleCopy}
            className="flex-1 flex items-center justify-center gap-2 py-3 bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 rounded-xl font-medium transition shadow-sm"
          >
            <Copy className="w-4 h-4" />
            העתק
          </button>
          <button
            onClick={handlePrint}
            className="flex-1 flex items-center justify-center gap-2 py-3 bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 rounded-xl font-medium transition shadow-sm"
          >
            <Printer className="w-4 h-4" />
            הדפס
          </button>
          <button
            onClick={() => {
              const text = encodeURIComponent(generatedContent || '');
              window.open(`https://wa.me/?text=${text}`, '_blank');
            }}
            className="flex-1 flex items-center justify-center gap-2 py-3 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white rounded-xl font-medium transition shadow-lg shadow-emerald-500/25"
          >
            <Send className="w-4 h-4" />
            וואטסאפ
          </button>
        </div>

        <button
          onClick={() => {
            setGeneratedContent(null);
            setStructuredSummary(null);
          }}
          className="w-full mt-3 py-2 text-sm text-gray-500 hover:text-gray-700 transition"
        >
          צור סיכום חדש
        </button>
      </div>
    );
  }

  // Expert selected - show context form
  if (selectedExpert || customExpert) {
    const expertName = selectedExpert?.profession || customExpert;
    return (
      <div className="pb-8 opacity-0 animate-fadeIn" style={{ animationFillMode: 'forwards' }}>
        <button
          onClick={handleBack}
          className="flex items-center gap-1 text-gray-500 hover:text-gray-700 mb-4 transition"
        >
          <ChevronRight className="w-4 h-4" />
          חזרה
        </button>

        {/* Selected expert card */}
        <div className="bg-gradient-to-br from-indigo-50 to-purple-50 border border-indigo-200 rounded-2xl p-4 mb-5">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center">
              <GraduationCap className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="font-bold text-gray-800">{expertName}</div>
              {selectedExpert?.specialization && (
                <div className="text-sm text-indigo-600">{selectedExpert.specialization}</div>
              )}
              {selectedExpert?.why_this_match && (
                <div className="text-xs text-gray-500 mt-1">{selectedExpert.why_this_match}</div>
              )}
            </div>
          </div>
        </div>

        {/* Context input */}
        <div className="space-y-5">
          <div>
            <label className="text-sm font-medium text-gray-700 mb-2 block">
              יש משהו ספציפי שחשוב להדגיש? (אופציונלי)
            </label>
            <textarea
              value={additionalContext}
              onChange={(e) => setAdditionalContext(e.target.value)}
              placeholder="למשל: הפגישה היא בעקבות אירוע ספציפי, או יש משהו שמטריד במיוחד..."
              className="w-full p-3 border border-gray-200 rounded-xl resize-none h-24 focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-300 transition"
            />
          </div>

          {/* Comprehensive toggle */}
          <label className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl cursor-pointer hover:bg-gray-100 transition">
            <input
              type="checkbox"
              checked={isComprehensive}
              onChange={(e) => setIsComprehensive(e.target.checked)}
              className="w-5 h-5 rounded border-gray-300 text-indigo-500 focus:ring-indigo-200"
            />
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <FileCheck className="w-4 h-4 text-indigo-500" />
                <span className="font-medium text-gray-700">סיכום מקיף</span>
              </div>
              <p className="text-xs text-gray-500 mt-0.5">
                כולל יותר פירוט ועומק - מתאים לפגישות ראשונות או להערכות מקיפות
              </p>
            </div>
          </label>

          <button
            onClick={() => handleGenerate()}
            disabled={isGenerating}
            className={`
              w-full py-4 rounded-xl font-bold text-white transition
              flex items-center justify-center gap-2
              ${isGenerating
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600 shadow-lg hover:shadow-xl'}
            `}
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                כותב סיכום מותאם...
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                צור סיכום
              </>
            )}
          </button>
        </div>
      </div>
    );
  }

  // Main view - Expert selection
  return (
    <div className="pb-8">
      <p className="text-gray-600 mb-6">
        בחרו למי לשתף - הסיכום ייכתב בסגנון ובאורך המתאימים לאיש המקצוע
      </p>

      {/* Recommended experts from crystal */}
      {hasRecommendedExperts && (
        <div className="mb-6">
          <h4 className="text-sm font-bold text-gray-700 mb-3 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-amber-500" />
            מומחים שהמלצנו עליהם
          </h4>
          <div className="space-y-2">
            {recommendedExperts.map((expert, idx) => (
              <button
                key={idx}
                onClick={() => setSelectedExpert(expert)}
                className={`
                  w-full p-4 bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200 rounded-2xl
                  flex items-center gap-4 text-right
                  hover:border-amber-300 hover:shadow-md transition card-hover
                  opacity-0 animate-staggerIn stagger-${idx + 1}
                `}
              >
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center flex-shrink-0">
                  <GraduationCap className="w-6 h-6 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-bold text-gray-800">{expert.profession}</div>
                  {expert.specialization && (
                    <div className="text-sm text-amber-700 truncate">{expert.specialization}</div>
                  )}
                  {expert.why_this_match && (
                    <div className="text-xs text-gray-500 mt-1 line-clamp-2">{expert.why_this_match}</div>
                  )}
                </div>
                <ArrowRight className="w-5 h-5 text-amber-400 flex-shrink-0" />
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Divider */}
      {hasRecommendedExperts && (
        <div className="flex items-center gap-3 mb-4">
          <div className="flex-1 h-px bg-gray-200" />
          <span className="text-sm text-gray-400">או בחרו מומחה אחר</span>
          <div className="flex-1 h-px bg-gray-200" />
        </div>
      )}

      {/* Custom input or quick options */}
      {showCustomInput ? (
        <div className="space-y-3">
          <input
            type="text"
            value={customExpert}
            onChange={(e) => setCustomExpert(e.target.value)}
            placeholder="כתבו את סוג איש המקצוע..."
            className="w-full p-4 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-300 transition text-right"
            autoFocus
          />
          <div className="flex gap-2">
            <button
              onClick={() => {
                setShowCustomInput(false);
                setCustomExpert('');
              }}
              className="px-4 py-2 text-gray-600 hover:text-gray-800 transition"
            >
              ביטול
            </button>
            <button
              onClick={() => customExpert && handleGenerate()}
              disabled={!customExpert}
              className={`
                flex-1 py-2 rounded-xl font-medium transition
                ${customExpert
                  ? 'bg-indigo-500 text-white hover:bg-indigo-600'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'}
              `}
            >
              המשך
            </button>
          </div>
        </div>
      ) : (
        <>
          {/* Quick options grid */}
          <div className="grid grid-cols-2 gap-2 mb-4">
            {FALLBACK_EXPERT_OPTIONS.slice(0, 6).map((option) => (
              <button
                key={option.id}
                onClick={() => setSelectedExpert({ profession: option.profession })}
                className="p-3 bg-white border border-gray-200 rounded-xl text-sm font-medium text-gray-700 hover:border-indigo-300 hover:bg-indigo-50 transition"
              >
                {option.label}
              </button>
            ))}
          </div>

          {/* Custom option */}
          <button
            onClick={() => setShowCustomInput(true)}
            className="w-full p-4 border-2 border-dashed border-gray-300 rounded-xl text-gray-500 hover:border-indigo-300 hover:text-indigo-600 transition flex items-center justify-center gap-2"
          >
            <span className="text-xl">+</span>
            איש מקצוע אחר
          </button>

          {/* Previous summaries */}
          {hasPreviousSummaries && (
            <div className="mt-8 pt-6 border-t border-gray-200">
              <h4 className="text-sm font-bold text-gray-700 mb-3 flex items-center gap-2">
                <Clock className="w-4 h-4 text-gray-400" />
                סיכומים קודמים
              </h4>
              <div className="space-y-2">
                {previousSummaries.map((summary, idx) => (
                  <button
                    key={summary.id}
                    onClick={() => handleViewSavedSummary(summary.id)}
                    disabled={loadingSavedSummary}
                    className="w-full p-3 bg-gray-50 border border-gray-200 rounded-xl text-right hover:bg-gray-100 transition"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-800">
                        ל{summary.recipient}
                      </span>
                      <span className="text-xs text-gray-400">
                        {formatDate(summary.created_at)}
                      </span>
                    </div>
                    {summary.comprehensive && (
                      <span className="text-xs text-indigo-600 mt-1 inline-block">מקיף</span>
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ============================================
// HELPER FUNCTIONS
// ============================================

function getDomainLabel(domain) {
  const labels = {
    identity: 'זהות',
    behavioral: 'התנהגות',
    sensory: 'חושי',
    motor: 'מוטורי',
    social: 'חברתי',
    emotional: 'רגשי',
    cognitive: 'קוגניטיבי',
    family: 'משפחה',
    strengths: 'חוזקות',
  };
  return labels[domain] || domain;
}

function formatDate(timestamp) {
  if (!timestamp) return '';
  const date = new Date(timestamp);
  const now = new Date();
  const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return 'היום';
  if (diffDays === 1) return 'אתמול';
  if (diffDays < 7) return `לפני ${diffDays} ימים`;

  return date.toLocaleDateString('he-IL', {
    day: 'numeric',
    month: 'long'
  });
}

function formatDuration(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// ============================================
// MAIN COMPONENT
// ============================================

export default function ChildSpace({
  familyId,
  isOpen,
  onClose,
  childName,
  childSpaceData,
  onVideoClick,
  onGenerateSummary,
  initialTab = 'essence',  // Allow opening to specific tab
  onUploadVideo,  // Callback for video upload
  onAddChittaMessage,  // Callback to add Chitta message to chat
}) {
  const [activeTab, setActiveTab] = useState(initialTab);
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadingScenarioId, setUploadingScenarioId] = useState(null);
  const tabIndicatorRef = useRef(null);
  const tabsRef = useRef({});

  // Update active tab when initialTab prop changes (e.g., opening to specific tab)
  useEffect(() => {
    if (isOpen && initialTab) {
      setActiveTab(initialTab);
    }
  }, [isOpen, initialTab]);

  // Use provided data or fetch from API
  useEffect(() => {
    if (childSpaceData) {
      setData(childSpaceData);
      setIsLoading(false);
    } else if (familyId && isOpen) {
      // Fetch data from API
      setIsLoading(true);
      api.getChildSpaceFull(familyId)
        .then((result) => {
          console.log('🌟 ChildSpace data loaded:', result);
          setData(result);
        })
        .catch((error) => {
          console.error('Error loading ChildSpace data:', error);
        })
        .finally(() => {
          setIsLoading(false);
        });
    }
  }, [familyId, isOpen, childSpaceData]);

  // Update tab indicator position (supports both RTL and LTR)
  // Note: depends on isOpen to trigger when panel opens (refs become available)
  useEffect(() => {
    if (!isOpen) return;

    // Small delay to ensure DOM is ready after panel animation starts
    const timer = setTimeout(() => {
      const activeTabEl = tabsRef.current[activeTab];
      const indicator = tabIndicatorRef.current;
      const container = activeTabEl?.parentElement;
      if (activeTabEl && indicator && container) {
        const isRTL = getComputedStyle(container).direction === 'rtl';
        indicator.style.width = `${activeTabEl.offsetWidth}px`;

        if (isRTL) {
          // RTL: position from right edge
          const containerWidth = container.offsetWidth;
          const tabRight = containerWidth - activeTabEl.offsetLeft - activeTabEl.offsetWidth;
          indicator.style.right = `${tabRight}px`;
          indicator.style.left = 'auto';
        } else {
          // LTR: position from left edge
          indicator.style.left = `${activeTabEl.offsetLeft}px`;
          indicator.style.right = 'auto';
        }
      }
    }, 50);

    return () => clearTimeout(timer);
  }, [activeTab, isOpen]);

  // Inline upload handler
  const handleUpload = async (file, scenario) => {
    console.log('📹 handleUpload called:', { file: file?.name, scenario });
    if (!file || !familyId) {
      console.error('❌ Upload blocked: missing file or familyId', { file: !!file, familyId });
      return;
    }

    // Get scenario ID (try different field names)
    const scenarioId = scenario.id || scenario.scenario_id || scenario.title;
    const cycleId = scenario.target_hypothesis_id || scenario.hypothesis_id || scenario.cycle_id;

    console.log('📹 Starting upload:', { familyId, cycleId, scenarioId, fileName: file.name });
    setUploadingScenarioId(scenarioId);
    setUploadProgress(0);

    try {
      // uploadVideoV2 expects: familyId, cycleId, scenarioId, file, onProgress
      await api.uploadVideoV2(familyId, cycleId, scenarioId, file, (progress) => {
        console.log('📹 Upload progress:', progress);
        setUploadProgress(progress);
      });
      console.log('✅ Upload complete');
      // Refresh data after upload
      const result = await api.getChildSpaceFull(familyId);
      setData(result);
    } catch (error) {
      console.error('❌ Upload failed:', error);
    } finally {
      setUploadProgress(0);
      setUploadingScenarioId(null);
    }
  };

  // Analyze video handler
  const handleAnalyze = async (scenario) => {
    if (!familyId) return;

    try {
      if (scenario) {
        // Analyze single video - analyzeVideos expects familyId, cycleId
        const cycleId = scenario.target_hypothesis_id || scenario.hypothesis_id || scenario.cycle_id;
        await api.analyzeVideos(familyId, cycleId);
      } else {
        // Analyze all pending videos
        await api.analyzeVideos(familyId, true);
      }
      // Refresh data after analysis
      const result = await api.getChildSpaceFull(familyId);
      setData(result);
    } catch (error) {
      console.error('Analysis failed:', error);
    }
  };

  // Remove video handler (placeholder - needs backend API)
  const handleRemove = async (scenario) => {
    if (!familyId) return;

    try {
      // TODO: Implement when backend API is ready
      // const cycleId = scenario.target_hypothesis_id || scenario.hypothesis_id || scenario.cycle_id;
      // await api.removeVideoScenario(familyId, cycleId, scenario.id);
      console.log('Remove video requested for scenario:', scenario.id);
      // For now, show a message that this feature is coming
      alert('מחיקת סרטון תתאפשר בקרוב');
    } catch (error) {
      console.error('Remove failed:', error);
    }
  };

  if (!isOpen) return null;

  const displayName = data?.child_name || childName || 'הילד';

  return (
    <div className="fixed inset-0 z-50 animate-backdropIn" dir="rtl">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="absolute inset-x-0 bottom-0 top-12 bg-gradient-to-br from-slate-50 via-white to-indigo-50 rounded-t-[2rem] shadow-2xl animate-panelUp overflow-hidden flex flex-col">

        {/* Header */}
        <div className="glass-strong border-b border-white/50 px-5 pt-4 pb-2 flex-shrink-0">
          {/* Close button and avatar */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              {/* Avatar with gradient */}
              <div className="relative">
                <div className="w-14 h-14 bg-gradient-to-br from-purple-400 via-indigo-500 to-blue-500 rounded-2xl flex items-center justify-center text-white font-bold text-2xl shadow-lg animate-scaleSpring">
                  {displayName.charAt(0)}
                </div>
                <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-emerald-400 rounded-full border-2 border-white flex items-center justify-center">
                  <Sparkles className="w-3 h-3 text-white" />
                </div>
              </div>
              <div>
                <h2 className="text-xl font-bold gradient-text">
                  המרחב של {displayName}
                </h2>
                <p className="text-sm text-gray-500">מסע ההבנה שלנו</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-full transition"
            >
              <X className="w-6 h-6 text-gray-400" />
            </button>
          </div>

          {/* Tabs */}
          <div className="relative">
            <div className="flex gap-1 relative">
              {TABS.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    ref={(el) => tabsRef.current[tab.id] = el}
                    onClick={() => setActiveTab(tab.id)}
                    className={`
                      flex-1 flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-xl
                      font-medium text-sm transition-all duration-300
                      ${isActive
                        ? 'text-white'
                        : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'}
                    `}
                  >
                    <Icon className={`w-4 h-4 ${isActive ? 'animate-gentleFloat' : ''}`} />
                    <span className="text-xs sm:text-sm">{tab.label}</span>
                  </button>
                );
              })}
            </div>
            {/* Animated indicator - direction-aware positioning */}
            <div
              ref={tabIndicatorRef}
              className={`
                absolute top-0 h-full rounded-xl
                bg-gradient-to-r ${TABS.find(t => t.id === activeTab)?.color}
                shadow-lg -z-10 transition-all duration-300 ease-out
              `}
            />
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-5 pt-4 hide-scrollbar">
          {isLoading ? (
            <LoadingAnimation childName={displayName} />
          ) : (
            <>
              {/* Tab Title Header - Shows current section */}
              {(() => {
                const currentTab = TABS.find(t => t.id === activeTab);
                const Icon = currentTab?.icon;
                return (
                  <div className="flex items-center gap-3 mb-5 pb-4 border-b border-gray-100">
                    <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${currentTab?.color} flex items-center justify-center shadow-lg`}>
                      {Icon && <Icon className="w-5 h-5 text-white" />}
                    </div>
                    <div>
                      <h3 className="font-bold text-lg text-gray-800">{currentTab?.label}</h3>
                      <p className="text-xs text-gray-500">
                        {activeTab === 'essence' && `הדיוקן של ${displayName}`}
                        {activeTab === 'discoveries' && 'מסע ההבנה שלנו'}
                        {activeTab === 'observations' && 'הסרטונים וההתבוננות'}
                        {activeTab === 'share' && 'שתפו את ההבנה'}
                      </p>
                    </div>
                  </div>
                );
              })()}

              {activeTab === 'essence' && (
                <EssenceTab data={data?.essence} childName={displayName} />
              )}
              {activeTab === 'discoveries' && (
                <DiscoveriesTab data={data?.discoveries} onVideoClick={onVideoClick} />
              )}
              {activeTab === 'observations' && (
                <ObservationsTab
                  data={data?.observations}
                  onUpload={handleUpload}
                  onAnalyze={handleAnalyze}
                  onRemove={handleRemove}
                  uploadProgress={uploadProgress}
                  uploadingScenarioId={uploadingScenarioId}
                />
              )}
              {activeTab === 'share' && (
                <ShareTab
                  data={data?.share}
                  familyId={familyId}
                  onGenerateSummary={onGenerateSummary}
                  onStartGuidedCollection={(greeting) => {
                    // Add Chitta's greeting to chat and close ChildSpace
                    if (greeting && onAddChittaMessage) {
                      onAddChittaMessage(greeting);
                    }
                    onClose();
                  }}
                />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
