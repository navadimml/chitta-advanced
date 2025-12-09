import React, { useState, useEffect, useRef } from 'react';
import {
  X, Sparkles, Lightbulb, Video, Share2,
  ChevronLeft, ChevronDown, ChevronUp, Heart, Music, Palette, Zap,
  Eye, Play, Clock, Send, Copy, FileText,
  Users, GraduationCap, Home, MessageCircle,
  Check, Loader2, ArrowRight, Search, ThumbsUp, ThumbsDown, Minus,
  UserPlus
} from 'lucide-react';
import { api } from '../api/client';

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
  { id: 'essence', icon: Sparkles, label: 'מי זה', color: 'from-purple-500 to-indigo-500' },
  { id: 'discoveries', icon: Lightbulb, label: 'מה גילינו', color: 'from-amber-500 to-orange-500' },
  { id: 'observations', icon: Video, label: 'מה ראינו', color: 'from-emerald-500 to-teal-500' },
  { id: 'share', icon: Share2, label: 'שיתוף', color: 'from-pink-500 to-rose-500' },
];

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

  const hasPatterns = data.patterns && data.patterns.length > 0;
  const hasPathways = data.intervention_pathways && data.intervention_pathways.length > 0;
  const hasInterests = data.interests && data.interests.length > 0;
  const hasOpenQuestions = data.open_questions && data.open_questions.length > 0;
  const hasExpertRecommendations = data.expert_recommendations && data.expert_recommendations.length > 0;

  return (
    <div className="space-y-6 pb-8">

      {/* === 1. ESSENCE NARRATIVE - Who Is This Child === */}
      {data.narrative ? (
        <div className="opacity-0 animate-fadeIn" style={{ animationDelay: '0.1s', animationFillMode: 'forwards' }}>
          <div className="bg-gradient-to-br from-purple-50 via-indigo-50 to-blue-50 rounded-3xl p-6 border border-purple-100 shadow-sm">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="w-5 h-5 text-purple-500" />
              <h3 className="font-bold text-purple-700">מי זה {childName}</h3>
            </div>
            <p className="text-gray-700 text-lg leading-relaxed">
              {data.narrative}
            </p>
            {/* Temperament & Core Qualities */}
            {(data.temperament?.length > 0 || data.core_qualities?.length > 0) && (
              <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-purple-100/50">
                {data.temperament?.map((t, idx) => (
                  <span key={`temp-${idx}`} className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm">
                    {t}
                  </span>
                ))}
                {data.core_qualities?.map((q, idx) => (
                  <span key={`qual-${idx}`} className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm">
                    {q}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="opacity-0 animate-fadeIn bg-gradient-to-br from-gray-50 to-slate-50 rounded-3xl p-6 border border-gray-100" style={{ animationDelay: '0.1s', animationFillMode: 'forwards' }}>
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="w-5 h-5 text-gray-400" />
            <h3 className="font-bold text-gray-500">מי זה {childName}</h3>
          </div>
          <p className="text-gray-500 text-sm">
            ככל שנשוחח יותר, התמונה המלאה תתגבש...
          </p>
        </div>
      )}

      {/* === 2. CROSS-DOMAIN PATTERNS - What We Noticed === */}
      {hasPatterns && (
        <div className="opacity-0 animate-fadeIn" style={{ animationDelay: '0.15s', animationFillMode: 'forwards' }}>
          <h3 className="text-sm font-bold text-gray-600 mb-3 flex items-center gap-2">
            <Zap className="w-4 h-4 text-amber-500" />
            מה שמנו לב
          </h3>
          <div className="space-y-3">
            {data.patterns.map((pattern, idx) => (
              <div
                key={idx}
                className="bg-gradient-to-r from-amber-50 to-orange-50 rounded-2xl p-4 border border-amber-100"
              >
                <p className="text-gray-800 font-medium">{pattern.description}</p>
                {pattern.domains && pattern.domains.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {pattern.domains.map((domain, dIdx) => (
                      <span
                        key={dIdx}
                        className="px-2 py-0.5 bg-amber-100 text-amber-700 rounded-full text-xs"
                      >
                        {getDomainLabel(domain)}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* === 3. INTERVENTION PATHWAYS - What Helps === */}
      {hasPathways && (
        <div className="opacity-0 animate-fadeIn" style={{ animationDelay: '0.2s', animationFillMode: 'forwards' }}>
          <h3 className="text-sm font-bold text-gray-600 mb-3 flex items-center gap-2">
            <Lightbulb className="w-4 h-4 text-emerald-500" />
            מה עוזר לו
          </h3>
          <div className="bg-gradient-to-br from-emerald-50 to-teal-50 rounded-2xl border border-emerald-100 overflow-hidden">
            {data.intervention_pathways.map((pathway, idx) => (
              <div
                key={idx}
                className={`p-4 ${idx > 0 ? 'border-t border-emerald-100/50' : ''}`}
              >
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-emerald-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Heart className="w-4 h-4 text-emerald-600" />
                  </div>
                  <div>
                    <p className="text-gray-800 font-medium">{pathway.suggestion}</p>
                    <p className="text-sm text-gray-600 mt-1">
                      כי הוא אוהב {pathway.hook}
                    </p>
                    {pathway.concern && (
                      <p className="text-xs text-emerald-600 mt-1">
                        עוזר כש: {pathway.concern}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* === 3.5 EXPERT RECOMMENDATIONS - Professional Help Tailored to This Child === */}
      {hasExpertRecommendations && (
        <div className="opacity-0 animate-fadeIn" style={{ animationDelay: '0.22s', animationFillMode: 'forwards' }}>
          <h3 className="text-sm font-bold text-gray-600 mb-3 flex items-center gap-2">
            <UserPlus className="w-4 h-4 text-blue-500" />
            אנשי מקצוע שיכולים לעזור
          </h3>
          <div className="space-y-3">
            {data.expert_recommendations.map((rec, idx) => (
              <ExpertRecommendationCard key={idx} recommendation={rec} index={idx} />
            ))}
          </div>
        </div>
      )}

      {/* === 4. INTERESTS - What They Love === */}
      {hasInterests && (
        <div className="opacity-0 animate-fadeIn" style={{ animationDelay: '0.25s', animationFillMode: 'forwards' }}>
          <h3 className="text-sm font-bold text-gray-600 mb-3 flex items-center gap-2">
            <Heart className="w-4 h-4 text-pink-500" />
            מה הוא אוהב
          </h3>
          <div className="flex flex-wrap gap-2">
            {data.interests.map((interest, idx) => (
              <span
                key={idx}
                className="px-4 py-2 bg-gradient-to-r from-pink-50 to-rose-50 text-pink-700 rounded-full text-sm border border-pink-100"
              >
                {interest.content}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* === 5. STRENGTHS - What They're Good At === */}
      {data.strengths && data.strengths.length > 0 && (
        <div className="opacity-0 animate-fadeIn" style={{ animationDelay: '0.3s', animationFillMode: 'forwards' }}>
          <h3 className="text-sm font-bold text-gray-600 mb-3 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-amber-500" />
            במה הוא מצטיין
          </h3>
          <div className="grid grid-cols-2 gap-3">
            {data.strengths.map((strength, idx) => (
              <StrengthCard key={idx} strength={strength} index={idx} />
            ))}
          </div>
        </div>
      )}

      {/* === 6. ACTIVE EXPLORATIONS - What We're Still Learning === */}
      {data.active_explorations && data.active_explorations.length > 0 && (
        <div className="opacity-0 animate-fadeIn" style={{ animationDelay: '0.35s', animationFillMode: 'forwards' }}>
          <h3 className="text-sm font-bold text-gray-600 mb-3 flex items-center gap-2">
            <Search className="w-4 h-4 text-indigo-500" />
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

      {/* === 7. OPEN QUESTIONS - What We Still Want to Understand === */}
      {hasOpenQuestions && (
        <div className="opacity-0 animate-fadeIn" style={{ animationDelay: '0.4s', animationFillMode: 'forwards' }}>
          <h3 className="text-sm font-bold text-gray-600 mb-3 flex items-center gap-2">
            <MessageCircle className="w-4 h-4 text-blue-500" />
            מה עוד רוצים להבין
          </h3>
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-4 border border-blue-100">
            <ul className="space-y-2">
              {data.open_questions.map((question, idx) => (
                <li key={idx} className="flex items-start gap-2 text-gray-700">
                  <span className="text-blue-400 mt-1">?</span>
                  <span>{question}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* === 8. FACTS BY DOMAIN (Secondary - Collapsed by Default) === */}
      {data.facts_by_domain && Object.keys(data.facts_by_domain).length > 0 && (
        <FactsSection factsData={data.facts_by_domain} />
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
// DISCOVERIES TAB - Journey Timeline
// ============================================

function DiscoveriesTab({ data, onVideoClick }) {
  if (!data || !data.milestones || data.milestones.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 px-8">
        <div className="w-20 h-20 bg-gradient-to-br from-amber-100 to-orange-100 rounded-full flex items-center justify-center mb-4 animate-gentleFloat">
          <Lightbulb className="w-10 h-10 text-amber-400" />
        </div>
        <p className="text-gray-500 text-center">
          מסע הגילוי רק מתחיל...<br />
          כל שיחה מוסיפה עוד נדבך
        </p>
      </div>
    );
  }

  return (
    <div className="pb-8">
      {/* Stats bar */}
      {data.days_since_start !== undefined && (
        <div className="flex items-center justify-around py-4 mb-6 bg-gradient-to-r from-amber-50 to-orange-50 rounded-2xl opacity-0 animate-fadeIn">
          <div className="text-center">
            <div className="text-2xl font-bold text-amber-600">{data.days_since_start}</div>
            <div className="text-xs text-gray-500">ימים</div>
          </div>
          <div className="w-px h-8 bg-amber-200" />
          <div className="text-center">
            <div className="text-2xl font-bold text-amber-600">{data.total_videos || 0}</div>
            <div className="text-xs text-gray-500">סרטונים</div>
          </div>
          <div className="w-px h-8 bg-amber-200" />
          <div className="text-center">
            <div className="text-2xl font-bold text-amber-600">{data.insights_discovered || 0}</div>
            <div className="text-xs text-gray-500">תובנות</div>
          </div>
        </div>
      )}

      {/* Timeline */}
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute right-5 top-0 bottom-0 w-0.5 bg-gradient-to-b from-amber-300 via-orange-300 to-transparent" />

        {/* Milestones - clickable for videos */}
        <div className="space-y-4">
          {data.milestones.map((milestone, idx) => (
            <TimelineMilestone
              key={milestone.id}
              milestone={milestone}
              index={idx}
              onVideoClick={onVideoClick}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function TimelineMilestone({ milestone, index, onVideoClick }) {
  const typeConfig = {
    started: { icon: Heart, color: 'bg-pink-500', bg: 'bg-pink-50' },
    exploration_began: { icon: Search, color: 'bg-indigo-500', bg: 'bg-indigo-50' },
    video_analyzed: { icon: Video, color: 'bg-emerald-500', bg: 'bg-emerald-50' },
    insight: { icon: Lightbulb, color: 'bg-amber-500', bg: 'bg-amber-50' },
    pattern: { icon: Sparkles, color: 'bg-purple-500', bg: 'bg-purple-50' },
    synthesis: { icon: FileText, color: 'bg-blue-500', bg: 'bg-blue-50' },
  };

  const config = typeConfig[milestone.type] || typeConfig.insight;
  const Icon = config.icon;
  const hasVideo = milestone.video_id;

  const handleVideoClick = () => {
    if (hasVideo && onVideoClick) {
      onVideoClick({
        id: milestone.video_id,
        exploration_id: milestone.exploration_id,
      });
    }
  };

  return (
    <div
      className={`
        relative pr-12 opacity-0 animate-staggerIn stagger-${Math.min(index + 1, 6)}
      `}
    >
      {/* Timeline dot */}
      <div className={`
        absolute right-3 w-5 h-5 rounded-full ${config.color}
        flex items-center justify-center shadow-lg
        ${milestone.significance === 'major' ? 'ring-4 ring-white' : ''}
      `}>
        <Icon className="w-3 h-3 text-white" />
      </div>

      {/* Content - clickable if has video */}
      <div
        className={`
          ${config.bg} rounded-2xl p-4 card-hover
          ${hasVideo ? 'cursor-pointer' : ''}
        `}
        onClick={hasVideo ? handleVideoClick : undefined}
      >
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1">
            <h4 className="font-bold text-gray-800">{milestone.title_he}</h4>
            <p className="text-sm text-gray-600 mt-1">{milestone.description_he}</p>
          </div>
          {hasVideo && (
            <button
              onClick={(e) => { e.stopPropagation(); handleVideoClick(); }}
              className="p-2 bg-white rounded-full shadow-sm hover:shadow-md transition hover:scale-110"
            >
              <Play className="w-4 h-4 text-emerald-500" />
            </button>
          )}
        </div>
        {milestone.timestamp && (
          <div className="flex items-center gap-1 mt-2 text-xs text-gray-400">
            <Clock className="w-3 h-3" />
            {formatDate(milestone.timestamp)}
          </div>
        )}
        {/* Video indicator */}
        {hasVideo && (
          <div className="flex items-center gap-1 mt-2 text-xs text-emerald-600 font-medium">
            <Video className="w-3 h-3" />
            לחץ לצפייה בסרטון
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================
// OBSERVATIONS TAB - Video Gallery
// ============================================

function ObservationsTab({ data, onVideoClick }) {
  if (!data || !data.videos || data.videos.length === 0) {
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

  return (
    <div className="space-y-4 pb-8">
      {/* Stats */}
      <div className="flex items-center gap-4 opacity-0 animate-fadeIn">
        <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-50 text-emerald-700 rounded-full text-sm">
          <Check className="w-4 h-4" />
          {data.analyzed_count} נותחו
        </div>
        {data.pending_count > 0 && (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-amber-50 text-amber-700 rounded-full text-sm">
            <Clock className="w-4 h-4" />
            {data.pending_count} ממתינים
          </div>
        )}
      </div>

      {/* Video cards */}
      <div className="space-y-4">
        {data.videos.map((video, idx) => (
          <VideoCard
            key={video.id}
            video={video}
            index={idx}
            onClick={() => onVideoClick && onVideoClick(video)}
          />
        ))}
      </div>
    </div>
  );
}

function VideoCard({ video, index, onClick }) {
  const isAnalyzed = video.status === 'analyzed';
  const isPending = video.status === 'pending' || video.status === 'uploaded';

  return (
    <div
      className={`
        bg-white rounded-2xl border overflow-hidden card-hover cursor-pointer
        opacity-0 animate-staggerIn stagger-${Math.min(index + 1, 6)}
        ${isAnalyzed ? 'border-emerald-200' : isPending ? 'border-amber-200' : 'border-gray-200'}
      `}
      onClick={onClick}
    >
      {/* Video thumbnail area */}
      <div className="relative h-32 bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center">
        <div className="w-14 h-14 bg-white/20 rounded-full flex items-center justify-center backdrop-blur-sm">
          <Play className="w-6 h-6 text-white mr-[-2px]" />
        </div>
        {/* Duration badge */}
        {video.duration_seconds > 0 && (
          <div className="absolute bottom-2 left-2 px-2 py-0.5 bg-black/60 text-white text-xs rounded">
            {formatDuration(video.duration_seconds)}
          </div>
        )}
        {/* Status badge */}
        <div className={`
          absolute top-2 left-2 px-2 py-0.5 rounded-full text-xs font-medium
          ${isAnalyzed ? 'bg-emerald-500 text-white' : isPending ? 'bg-amber-500 text-white' : 'bg-gray-500 text-white'}
        `}>
          {isAnalyzed ? 'נותח' : isPending ? 'ממתין' : video.status}
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        <h4 className="font-bold text-gray-800">{video.title}</h4>
        <p className="text-sm text-gray-500 mt-1">{video.hypothesis_title}</p>

        {/* Observations preview */}
        {isAnalyzed && video.observations && video.observations.length > 0 && (
          <div className="mt-3 space-y-2">
            <div className="text-xs font-medium text-gray-400">תצפיות:</div>
            {video.observations.slice(0, 2).map((obs, idx) => (
              <div key={idx} className="flex items-start gap-2 text-sm">
                <span className="text-emerald-500 font-mono text-xs mt-0.5">
                  {obs.timestamp_start}
                </span>
                <span className="text-gray-600 line-clamp-1">{obs.content}</span>
              </div>
            ))}
            {video.observations.length > 2 && (
              <div className="text-xs text-indigo-500">
                +{video.observations.length - 2} תצפיות נוספות
              </div>
            )}
          </div>
        )}

        {/* Strengths observed */}
        {isAnalyzed && video.strengths_observed && video.strengths_observed.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1">
            {video.strengths_observed.map((strength, idx) => (
              <span
                key={idx}
                className="px-2 py-0.5 bg-pink-50 text-pink-600 rounded-full text-xs"
              >
                {strength}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
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
// SHARE TAB - Adaptive Sharing
// ============================================

const RECIPIENT_TYPES = [
  {
    id: 'professional',
    icon: GraduationCap,
    label: 'איש מקצוע',
    description: 'רופא, מטפל, פסיכולוג',
    color: 'from-blue-500 to-indigo-500',
    subtypes: [
      { id: 'neurologist', label: 'נוירולוג' },
      { id: 'psychologist', label: 'פסיכולוג' },
      { id: 'ot', label: 'מטפלת בעיסוק' },
      { id: 'speech_therapist', label: 'קלינאית תקשורת' },
      { id: 'pediatrician', label: 'רופא ילדים' },
    ]
  },
  {
    id: 'educational',
    icon: Users,
    label: 'מסגרת חינוכית',
    description: 'גננת, מורה, מטפלת',
    color: 'from-emerald-500 to-teal-500',
    subtypes: [
      { id: 'kindergarten', label: 'גננת' },
      { id: 'teacher', label: 'מורה' },
      { id: 'daycare', label: 'מטפלת במעון' },
    ]
  },
  {
    id: 'family',
    icon: Home,
    label: 'משפחה',
    description: 'סבים, דודים, בן זוג',
    color: 'from-pink-500 to-rose-500',
    subtypes: [
      { id: 'grandparent', label: 'סבא/סבתא' },
      { id: 'family', label: 'משפחה רחבה' },
    ]
  },
  {
    id: 'peer',
    icon: MessageCircle,
    label: 'הורה אחר',
    description: 'קבוצת תמיכה, חברים',
    color: 'from-purple-500 to-violet-500',
    subtypes: [
      { id: 'parent_peer', label: 'הורה אחר' },
    ]
  },
];

function ShareTab({ data, familyId, onGenerateSummary }) {
  const [selectedType, setSelectedType] = useState(null);
  const [selectedSubtype, setSelectedSubtype] = useState(null);
  const [timeAvailable, setTimeAvailable] = useState('standard');
  const [additionalContext, setAdditionalContext] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedContent, setGeneratedContent] = useState(null);
  const [copied, setCopied] = useState(false);

  const canGenerate = data?.can_generate !== false;

  const handleGenerate = async () => {
    if (!selectedSubtype) return;

    setIsGenerating(true);
    try {
      const result = await onGenerateSummary({
        recipientType: selectedType.id,
        recipientSubtype: selectedSubtype.id,
        timeAvailable,
        context: additionalContext
      });
      setGeneratedContent(result.content);
    } catch (error) {
      console.error('Error generating summary:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopy = () => {
    if (generatedContent) {
      navigator.clipboard.writeText(generatedContent);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleBack = () => {
    if (generatedContent) {
      setGeneratedContent(null);
    } else if (selectedSubtype) {
      setSelectedSubtype(null);
    } else if (selectedType) {
      setSelectedType(null);
    }
  };

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

  // Generated content view - Beautiful styled display
  if (generatedContent) {
    return (
      <div className="pb-8 opacity-0 animate-fadeIn" style={{ animationFillMode: 'forwards' }}>
        {/* Header with back button */}
        <div className="flex items-center justify-between mb-4">
          <button
            onClick={handleBack}
            className="flex items-center gap-1 text-gray-500 hover:text-gray-700 transition"
          >
            <ChevronLeft className="w-4 h-4" />
            חזרה
          </button>
          <button
            onClick={handleCopy}
            className={`
              flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition
              ${copied
                ? 'bg-emerald-100 text-emerald-700'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}
            `}
          >
            {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
            {copied ? 'הועתק!' : 'העתק'}
          </button>
        </div>

        {/* Title */}
        <h3 className="font-bold text-xl text-gray-800 mb-4 flex items-center gap-2">
          <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${selectedType?.color || 'from-indigo-500 to-purple-500'} flex items-center justify-center`}>
            {selectedType?.icon && <selectedType.icon className="w-5 h-5 text-white" />}
          </div>
          סיכום ל{selectedSubtype?.label}
        </h3>

        {/* Styled content */}
        <StyledSummary content={generatedContent} recipientType={selectedType?.id} />

        {/* Share buttons */}
        <div className="flex gap-3 mt-6">
          <button
            onClick={handleCopy}
            className="flex-1 flex items-center justify-center gap-2 py-3.5 bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 rounded-xl font-medium transition shadow-sm"
          >
            <Copy className="w-5 h-5" />
            העתק טקסט
          </button>
          <button
            onClick={() => {
              const text = encodeURIComponent(generatedContent);
              window.open(`https://wa.me/?text=${text}`, '_blank');
            }}
            className="flex-1 flex items-center justify-center gap-2 py-3.5 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white rounded-xl font-medium transition shadow-lg shadow-emerald-500/25"
          >
            <Send className="w-5 h-5" />
            שלח בוואטסאפ
          </button>
        </div>

        {/* Regenerate option */}
        <button
          onClick={() => {
            setGeneratedContent(null);
          }}
          className="w-full mt-3 py-2 text-sm text-gray-500 hover:text-gray-700 transition"
        >
          צור סיכום חדש עם הגדרות שונות
        </button>
      </div>
    );
  }

  // Subtype selection + options
  if (selectedType) {
    return (
      <div className="pb-8 opacity-0 animate-fadeIn" style={{ animationFillMode: 'forwards' }}>
        <button
          onClick={handleBack}
          className="flex items-center gap-1 text-gray-500 hover:text-gray-700 mb-4 transition"
        >
          <ChevronLeft className="w-4 h-4" />
          חזרה
        </button>

        <h3 className="font-bold text-gray-800 mb-4">
          {selectedSubtype ? 'התאמה אישית' : `בחרו סוג ${selectedType.label}`}
        </h3>

        {!selectedSubtype ? (
          // Subtype selection
          <div className="grid grid-cols-2 gap-3">
            {selectedType.subtypes.map((subtype) => (
              <button
                key={subtype.id}
                onClick={() => setSelectedSubtype(subtype)}
                className="p-4 bg-white border border-gray-200 rounded-xl text-right hover:border-indigo-300 hover:bg-indigo-50 transition card-hover"
              >
                <span className="font-medium text-gray-800">{subtype.label}</span>
              </button>
            ))}
          </div>
        ) : (
          // Options form
          <div className="space-y-5">
            {/* Time available */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                כמה זמן יש ל{selectedSubtype.label}?
              </label>
              <div className="flex gap-2">
                {[
                  { id: 'brief', label: 'קצר', desc: '2-3 דקות' },
                  { id: 'standard', label: 'רגיל', desc: '5-10 דקות' },
                  { id: 'comprehensive', label: 'מלא', desc: '15+ דקות' },
                ].map((option) => (
                  <button
                    key={option.id}
                    onClick={() => setTimeAvailable(option.id)}
                    className={`
                      flex-1 py-3 px-2 rounded-xl border-2 transition text-center
                      ${timeAvailable === option.id
                        ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                        : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300'}
                    `}
                  >
                    <div className="font-medium">{option.label}</div>
                    <div className="text-xs opacity-70">{option.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Additional context */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                יש משהו ספציפי שחשוב להדגיש? (אופציונלי)
              </label>
              <textarea
                value={additionalContext}
                onChange={(e) => setAdditionalContext(e.target.value)}
                placeholder="למשל: הפגישה היא בעקבות התקף חרדה שהיה לו בגן..."
                className="w-full p-3 border border-gray-200 rounded-xl resize-none h-24 focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-300 transition"
              />
            </div>

            {/* Generate button */}
            <button
              onClick={handleGenerate}
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
                  מכין סיכום...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  צור סיכום
                </>
              )}
            </button>
          </div>
        )}
      </div>
    );
  }

  // Main recipient type selection
  return (
    <div className="pb-8">
      <p className="text-gray-600 mb-6">
        שתפו את ההבנה על הילד עם מי שחשוב - בשפה שמתאימה להם
      </p>

      <div className="space-y-3">
        {RECIPIENT_TYPES.map((type, idx) => {
          const Icon = type.icon;
          return (
            <button
              key={type.id}
              onClick={() => setSelectedType(type)}
              className={`
                w-full p-4 bg-white border border-gray-200 rounded-2xl
                flex items-center gap-4 text-right
                hover:border-indigo-300 hover:shadow-md transition card-hover
                opacity-0 animate-staggerIn stagger-${idx + 1}
              `}
            >
              <div className={`
                w-12 h-12 rounded-xl bg-gradient-to-br ${type.color}
                flex items-center justify-center flex-shrink-0
              `}>
                <Icon className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1">
                <div className="font-bold text-gray-800">{type.label}</div>
                <div className="text-sm text-gray-500">{type.description}</div>
              </div>
              <ArrowRight className="w-5 h-5 text-gray-400" />
            </button>
          );
        })}
      </div>
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
}) {
  const [activeTab, setActiveTab] = useState('essence');
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const tabIndicatorRef = useRef(null);
  const tabsRef = useRef({});

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
  useEffect(() => {
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
  }, [activeTab]);

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
            <div className="flex items-center justify-center py-16">
              <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
            </div>
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
                        {activeTab === 'essence' && `מי זה ${displayName}`}
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
                <ObservationsTab data={data?.observations} onVideoClick={onVideoClick} />
              )}
              {activeTab === 'share' && (
                <ShareTab
                  data={data?.share}
                  familyId={familyId}
                  onGenerateSummary={onGenerateSummary}
                />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
