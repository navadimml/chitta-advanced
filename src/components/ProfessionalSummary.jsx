import React, { useRef } from 'react';
import {
  User, Heart, MessageCircle, Eye, Clock, HelpCircle,
  AlertCircle, Sparkles, ChevronLeft, Copy, Printer, Send, Check, Lightbulb
} from 'lucide-react';

/**
 * ProfessionalSummary - A beautifully designed summary renderer
 *
 * Design principles:
 * - Clean, professional typography
 * - Clear visual hierarchy
 * - Print-friendly
 * - Credibility through restraint
 */

// Section component with consistent styling
function Section({ icon: Icon, title, children, accentColor = 'indigo' }) {
  if (!children || (Array.isArray(children) && children.length === 0)) return null;

  const colors = {
    indigo: 'from-indigo-500 to-indigo-600',
    emerald: 'from-emerald-500 to-emerald-600',
    amber: 'from-amber-500 to-amber-600',
    rose: 'from-rose-500 to-rose-600',
    slate: 'from-slate-500 to-slate-600',
    purple: 'from-purple-500 to-purple-600',
    teal: 'from-teal-500 to-teal-600',
  };

  return (
    <div className="mb-8">
      <div className="flex items-center gap-3 mb-4">
        <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${colors[accentColor]} flex items-center justify-center shadow-sm`}>
          <Icon className="w-4 h-4 text-white" />
        </div>
        <h3 className="text-lg font-semibold text-gray-800 tracking-tight">{title}</h3>
      </div>
      <div className="pr-11">
        {children}
      </div>
    </div>
  );
}

// Pill/Tag component
function Tag({ children, variant = 'default' }) {
  const variants = {
    default: 'bg-gray-100 text-gray-700',
    parent: 'bg-blue-50 text-blue-700 border border-blue-200',
    chitta: 'bg-purple-50 text-purple-700 border border-purple-200',
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${variants[variant]}`}>
      {children}
    </span>
  );
}

// Scene card component
function SceneCard({ scene }) {
  return (
    <div className="bg-gradient-to-br from-slate-50 to-gray-50 rounded-xl p-5 border border-gray-100 shadow-sm">
      <h4 className="font-semibold text-gray-900 mb-2 text-base">{scene.title}</h4>
      <p className="text-gray-700 leading-relaxed mb-3">{scene.description}</p>
      {(scene.what_helps || scene.what_doesnt_help) && (
        <div className="flex flex-wrap gap-4 mt-3 pt-3 border-t border-gray-200">
          {scene.what_helps && (
            <div className="flex items-start gap-2">
              <div className="w-5 h-5 rounded-full bg-emerald-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                <Check className="w-3 h-3 text-emerald-600" />
              </div>
              <span className="text-sm text-gray-600">{scene.what_helps}</span>
            </div>
          )}
          {scene.what_doesnt_help && (
            <div className="flex items-start gap-2">
              <div className="w-5 h-5 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-red-600 text-xs font-bold">×</span>
              </div>
              <span className="text-sm text-gray-600">{scene.what_doesnt_help}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Practical tip card component - מה יכול לעזור
function TipCard({ tip }) {
  return (
    <div className="bg-gradient-to-br from-teal-50 to-emerald-50 rounded-xl p-5 border border-teal-100 shadow-sm">
      <div className="flex items-start gap-3 mb-3">
        <div className="w-6 h-6 rounded-full bg-teal-100 flex items-center justify-center flex-shrink-0 mt-0.5">
          <Lightbulb className="w-3.5 h-3.5 text-teal-600" />
        </div>
        <div className="flex-1">
          <p className="text-gray-800 font-medium">{tip.suggestion}</p>
        </div>
      </div>
      <div className="pr-9 space-y-1.5">
        <div className="flex items-start gap-2 text-sm">
          <span className="text-teal-600 font-medium whitespace-nowrap">מה עובד:</span>
          <span className="text-gray-600">{tip.what_works}</span>
        </div>
        <div className="flex items-start gap-2 text-sm">
          <span className="text-amber-600 font-medium whitespace-nowrap">מאתגר:</span>
          <span className="text-gray-600">{tip.challenge}</span>
        </div>
      </div>
    </div>
  );
}

// Main component
export default function ProfessionalSummary({
  data,
  onCopy,
  onPrint,
  onWhatsApp,
  copied = false
}) {
  const summaryRef = useRef(null);

  if (!data) return null;

  // Handle both structured data and legacy format detection
  const isStructured = data.essence_paragraph !== undefined;

  if (!isStructured) {
    // Fallback to legacy text rendering
    return (
      <div className="prose prose-gray max-w-none" dir="rtl">
        <pre className="whitespace-pre-wrap font-sans text-gray-700 leading-relaxed">
          {typeof data === 'string' ? data : JSON.stringify(data, null, 2)}
        </pre>
      </div>
    );
  }

  return (
    <div ref={summaryRef} className="font-sans" dir="rtl">
      {/* Header */}
      <div className="bg-gradient-to-br from-slate-800 via-slate-900 to-gray-900 text-white rounded-2xl p-6 mb-8 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-white/10 backdrop-blur flex items-center justify-center">
              <User className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight">{data.child_first_name}</h1>
              <p className="text-slate-300 text-sm">{data.child_age_description}</p>
            </div>
          </div>
          <div className="text-left">
            <p className="text-slate-400 text-xs">סיכום עבור</p>
            <p className="text-white font-medium">{data.recipient_title}</p>
          </div>
        </div>
        <div className="text-slate-400 text-xs flex items-center gap-2">
          <Clock className="w-3.5 h-3.5" />
          {data.summary_date}
        </div>
      </div>

      {/* Essence - The most important part */}
      {data.essence_paragraph && (
        <div className="bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 rounded-2xl p-6 mb-8 border border-indigo-100">
          <p className="text-gray-800 text-lg leading-relaxed font-medium">
            {data.essence_paragraph}
          </p>
        </div>
      )}

      {/* Strengths as Bridges */}
      {data.strengths && data.strengths.length > 0 && (
        <Section icon={Sparkles} title="חוזקות כגשרים" accentColor="emerald">
          <div className="space-y-3">
            {data.strengths.map((strength, idx) => (
              <div key={idx} className="flex items-start gap-3 bg-emerald-50/50 rounded-xl p-4 border border-emerald-100">
                <div className="w-2 h-2 rounded-full bg-emerald-500 mt-2 flex-shrink-0" />
                <div>
                  <span className="font-semibold text-gray-900">{strength.strength}</span>
                  <span className="text-gray-600"> — {strength.how_to_use}</span>
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* What Parents Shared */}
      {data.parent_observations && data.parent_observations.length > 0 && (
        <Section icon={MessageCircle} title="מה ההורים סיפרו" accentColor="indigo">
          <div className="space-y-2">
            {data.parent_observations.map((obs, idx) => (
              <div key={idx} className="flex items-start gap-3 py-2">
                <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-2 flex-shrink-0" />
                <p className="text-gray-700 leading-relaxed">{obs.text}</p>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Concrete Scenes */}
      {data.scenes && data.scenes.length > 0 && (
        <Section icon={Eye} title="תמונות מהשטח" accentColor="amber">
          <div className="space-y-4">
            {data.scenes.map((scene, idx) => (
              <SceneCard key={idx} scene={scene} />
            ))}
          </div>
        </Section>
      )}

      {/* Practical Tips - מה יכול לעזור */}
      {data.practical_tips && data.practical_tips.length > 0 && (
        <Section icon={Lightbulb} title="מה יכול לעזור" accentColor="teal">
          <div className="space-y-4">
            {data.practical_tips.map((tip, idx) => (
              <TipCard key={idx} tip={tip} />
            ))}
          </div>
        </Section>
      )}

      {/* Patterns from conversations and videos */}
      {data.patterns && data.patterns.length > 0 && (
        <Section icon={Eye} title="דפוסים שעלו מהשיחות והסרטונים" accentColor="purple">
          <div className="bg-purple-50/50 rounded-xl p-5 border border-purple-100">
            <div className="space-y-3">
              {data.patterns.map((pattern, idx) => (
                <div key={idx} className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-lg bg-purple-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-purple-600 text-xs font-bold">{idx + 1}</span>
                  </div>
                  <div>
                    <p className="text-gray-800 leading-relaxed">{pattern.observation}</p>
                    {pattern.domains_involved && pattern.domains_involved.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mt-2">
                        {pattern.domains_involved.map((domain, i) => (
                          <Tag key={i}>{domain}</Tag>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-3 italic">
            * תצפיות ראשוניות — מומלץ לבחון בהערכה מקצועית
          </p>
        </Section>
      )}

      {/* Developmental Timeline */}
      {data.developmental_notes && data.developmental_notes.length > 0 && (
        <Section icon={Clock} title="ציר זמן התפתחותי" accentColor="slate">
          <div className="relative">
            <div className="absolute right-3 top-0 bottom-0 w-0.5 bg-gray-200" />
            <div className="space-y-4">
              {data.developmental_notes.map((note, idx) => (
                <div key={idx} className="flex items-start gap-4 relative">
                  <div className="w-6 h-6 rounded-full bg-white border-2 border-gray-300 flex items-center justify-center z-10 flex-shrink-0">
                    <div className="w-2 h-2 rounded-full bg-gray-400" />
                  </div>
                  <div className="flex-1 pb-2">
                    <p className="text-sm font-medium text-gray-500">{note.timing}</p>
                    <p className="text-gray-800">{note.event}</p>
                    {note.significance && (
                      <p className="text-sm text-gray-500 mt-1">{note.significance}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Section>
      )}

      {/* Open Questions */}
      {data.open_questions && data.open_questions.length > 0 && (
        <Section icon={HelpCircle} title="שאלות לבדיקה" accentColor="amber">
          <div className="bg-amber-50/50 rounded-xl p-5 border border-amber-100">
            <div className="space-y-3">
              {data.open_questions.map((q, idx) => (
                <div key={idx} className="flex items-start gap-3">
                  <div className="w-5 h-5 rounded-full bg-amber-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-amber-600 text-sm">?</span>
                  </div>
                  <div>
                    <p className="text-gray-800">{q.question}</p>
                    {q.why_relevant && (
                      <p className="text-sm text-gray-500 mt-1">{q.why_relevant}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Section>
      )}

      {/* Missing Information */}
      {data.missing_info && data.missing_info.length > 0 && (
        <Section icon={AlertCircle} title="מידע שטרם נאסף" accentColor="rose">
          <div className="bg-rose-50/50 rounded-xl p-5 border border-rose-100">
            <div className="space-y-2">
              {data.missing_info.map((item, idx) => (
                <div key={idx} className="flex items-start gap-3">
                  <div className="w-1.5 h-1.5 rounded-full bg-rose-400 mt-2 flex-shrink-0" />
                  <div>
                    <span className="text-gray-800">{item.item}</span>
                    {item.why_relevant && (
                      <span className="text-gray-500 text-sm"> — {item.why_relevant}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Section>
      )}

      {/* Closing Note */}
      {data.closing_note && (
        <div className="mt-8 pt-6 border-t border-gray-200">
          <p className="text-gray-600 text-sm leading-relaxed">{data.closing_note}</p>
        </div>
      )}

      {/* Footer */}
      <div className="mt-8 pt-6 border-t border-gray-100">
        <div className="flex items-center justify-between text-xs text-gray-400">
          <span>נוצר על ידי Chitta</span>
          <span>{data.summary_date}</span>
        </div>
      </div>
    </div>
  );
}

// Print-friendly version
export function ProfessionalSummaryPrint({ data }) {
  if (!data || !data.essence_paragraph) return null;

  return `
<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
  <meta charset="UTF-8">
  <title>סיכום עבור ${data.recipient_title} - ${data.child_first_name}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700&display=swap');

    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
      font-family: 'Heebo', Arial, sans-serif;
      line-height: 1.5;
      color: #1f2937;
      max-width: 800px;
      margin: 0 auto;
      padding: 24px;
      background: white;
      font-size: 13px;
    }

    .header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      padding-bottom: 12px;
      border-bottom: 2px solid #e5e7eb;
      margin-bottom: 16px;
    }

    .header h1 {
      font-size: 22px;
      font-weight: 700;
      color: #111827;
      margin-bottom: 2px;
    }

    .header .meta {
      color: #6b7280;
      font-size: 13px;
    }

    .header .recipient {
      text-align: left;
      color: #6b7280;
      font-size: 12px;
    }

    .header .recipient strong {
      display: block;
      color: #111827;
      font-size: 14px;
    }

    .essence {
      background: linear-gradient(135deg, #eef2ff 0%, #faf5ff 100%);
      padding: 14px 16px;
      border-radius: 8px;
      margin-bottom: 16px;
      font-size: 14px;
      font-weight: 500;
      color: #374151;
    }

    .section {
      margin-bottom: 14px;
    }

    .section-title {
      font-size: 14px;
      font-weight: 600;
      color: #111827;
      margin-bottom: 8px;
      padding-bottom: 4px;
      border-bottom: 1px solid #e5e7eb;
    }

    .item {
      display: flex;
      gap: 8px;
      margin-bottom: 4px;
      font-size: 13px;
    }

    .item::before {
      content: "•";
      color: #9ca3af;
      flex-shrink: 0;
    }

    .scene-card {
      background: #f9fafb;
      padding: 10px 12px;
      border-radius: 6px;
      margin-bottom: 8px;
      border: 1px solid #e5e7eb;
    }

    .scene-card h4 {
      font-size: 13px;
      font-weight: 600;
      margin-bottom: 4px;
      color: #111827;
    }

    .scene-card p {
      color: #4b5563;
      font-size: 12px;
    }

    .scene-meta {
      display: flex;
      gap: 12px;
      margin-top: 8px;
      padding-top: 8px;
      border-top: 1px dashed #e5e7eb;
      font-size: 11px;
      color: #6b7280;
    }

    .timeline-item {
      display: flex;
      gap: 12px;
      margin-bottom: 8px;
      padding-right: 12px;
      border-right: 2px solid #e5e7eb;
      font-size: 13px;
    }

    .timeline-item .time {
      font-size: 12px;
      color: #6b7280;
      min-width: 70px;
    }

    .note-box {
      background: #fffbeb;
      border: 1px solid #fcd34d;
      padding: 10px 12px;
      border-radius: 6px;
      margin-top: 4px;
    }

    .missing-box {
      background: #fef2f2;
      border: 1px solid #fecaca;
      padding: 10px 12px;
      border-radius: 6px;
    }

    .footer {
      margin-top: 20px;
      padding-top: 12px;
      border-top: 1px solid #e5e7eb;
      display: flex;
      justify-content: space-between;
      font-size: 11px;
      color: #9ca3af;
    }

    .intro-note {
      font-size: 12px;
      color: #6b7280;
      margin-bottom: 16px;
      padding: 10px 14px;
      background: #f9fafb;
      border-radius: 6px;
      border-right: 3px solid #6366f1;
    }

    @media print {
      body { padding: 16px; font-size: 12px; }
      .header { page-break-after: avoid; }
      .section { page-break-inside: avoid; }
      .essence { padding: 12px 14px; }
    }
  </style>
</head>
<body>
  <div class="header">
    <div>
      <h1>${data.child_first_name}</h1>
      <div class="meta">${data.child_age_description}</div>
    </div>
    <div class="recipient">
      סיכום עבור
      <strong>${data.recipient_title}</strong>
    </div>
  </div>

  <div class="intro-note">
    ${(() => {
      const type = (data.recipient_type || '').toLowerCase();
      const base = 'הסיכום הזה נבנה באמצעות Chitta, מתוך שיחות עם ההורים וצפייה בסרטונים שהם שיתפו.';
      const isEducator = type.includes('גן') || type.includes('גננת') || type.includes('מורה') || type.includes('חינוך') || type.includes('סייעת');

      if (isEducator) {
        return base + ' המטרה היא לעזור לך להכיר את הילד טוב יותר ולתת תמונה מהבית — כך שתוכל/י ליצור המשכיות בינו לבין המסגרת.';
      } else {
        return base + ' המטרה היא לחסוך לך זמן ולתת תמונה עשירה יותר מהבית — כך שתוכל/י להתמקד במה שחשוב באמת.';
      }
    })()}
  </div>

  ${data.essence_paragraph ? `<div class="essence">${data.essence_paragraph}</div>` : ''}

  ${data.strengths && data.strengths.length > 0 ? `
    <div class="section">
      <div class="section-title">חוזקות כגשרים</div>
      ${data.strengths.map(s => `
        <div class="item"><strong>${s.strength || ''}</strong>${s.how_to_use ? ` — ${s.how_to_use}` : ''}</div>
      `).join('')}
    </div>
  ` : ''}

  ${data.parent_observations && data.parent_observations.length > 0 ? `
    <div class="section">
      <div class="section-title">מה ההורים סיפרו</div>
      ${data.parent_observations.map(o => `<div class="item">${o.text || ''}</div>`).join('')}
    </div>
  ` : ''}

  ${data.scenes && data.scenes.length > 0 ? `
    <div class="section">
      <div class="section-title">תמונות מהשטח</div>
      ${data.scenes.map(scene => `
        <div class="scene-card">
          <h4>${scene.title || ''}</h4>
          <p>${scene.description || ''}</p>
          ${scene.what_helps || scene.what_doesnt_help ? `
            <div class="scene-meta">
              ${scene.what_helps ? `<span>✓ מה עוזר: ${scene.what_helps}</span>` : ''}
              ${scene.what_doesnt_help ? `<span>✗ מה לא עוזר: ${scene.what_doesnt_help}</span>` : ''}
            </div>
          ` : ''}
        </div>
      `).join('')}
    </div>
  ` : ''}

  ${data.practical_tips && data.practical_tips.length > 0 ? `
    <div class="section">
      <div class="section-title">💡 מה יכול לעזור</div>
      ${data.practical_tips.map(tip => `
        <div class="scene-card" style="background: linear-gradient(135deg, #f0fdfa 0%, #ecfdf5 100%); border-color: #99f6e4;">
          <p style="font-weight: 600; color: #0f766e; margin-bottom: 8px;">${tip.suggestion || ''}</p>
          <div style="font-size: 12px; color: #4b5563;">
            <span style="color: #0d9488; font-weight: 500;">מה עובד:</span> ${tip.what_works || ''}
          </div>
          <div style="font-size: 12px; color: #4b5563; margin-top: 4px;">
            <span style="color: #d97706; font-weight: 500;">מאתגר:</span> ${tip.challenge || ''}
          </div>
        </div>
      `).join('')}
    </div>
  ` : ''}

  ${data.patterns && data.patterns.length > 0 ? `
    <div class="section">
      <div class="section-title">דפוסים שעלו מהשיחות והסרטונים</div>
      <div class="note-box">
        ${data.patterns.map((p, i) => `
          <div class="item">
            ${p.observation || ''}
            ${p.domains_involved && p.domains_involved.length > 0 ? `
              <span style="font-size: 11px; color: #6b7280; margin-right: 8px;">(${p.domains_involved.join(', ')})</span>
            ` : ''}
          </div>
        `).join('')}
        <p style="font-size: 11px; color: #92400e; margin-top: 8px; font-style: italic;">
          * תצפיות ראשוניות — מומלץ לבחון בהערכה מקצועית
        </p>
      </div>
    </div>
  ` : ''}

  ${data.developmental_notes && data.developmental_notes.length > 0 ? `
    <div class="section">
      <div class="section-title">ציר זמן התפתחותי</div>
      ${data.developmental_notes.map(note => `
        <div class="timeline-item">
          <span class="time">${note.timing || ''}</span>
          <div>
            <span>${note.event || ''}</span>
            ${note.significance ? `<div style="font-size: 11px; color: #6b7280; margin-top: 2px;">${note.significance}</div>` : ''}
          </div>
        </div>
      `).join('')}
    </div>
  ` : ''}

  ${data.open_questions && data.open_questions.length > 0 ? `
    <div class="section">
      <div class="section-title">שאלות לבדיקה</div>
      <div class="note-box">
        ${data.open_questions.map(q => `
          <div class="item">
            ${q.question || ''}
            ${q.why_relevant ? `<span style="color: #6b7280; font-size: 12px;"> — ${q.why_relevant}</span>` : ''}
          </div>
        `).join('')}
      </div>
    </div>
  ` : ''}

  ${data.missing_info && data.missing_info.length > 0 ? `
    <div class="section">
      <div class="section-title">מידע שטרם נאסף</div>
      <div class="missing-box">
        ${data.missing_info.map(m => `
          <div class="item">
            ${m.item || ''}
            ${m.why_relevant ? `<span style="color: #6b7280; font-size: 12px;"> — ${m.why_relevant}</span>` : ''}
          </div>
        `).join('')}
      </div>
    </div>
  ` : ''}

  ${data.closing_note ? `<div class="section"><p>${data.closing_note}</p></div>` : ''}

  <div class="footer">
    <span>נוצר על ידי Chitta</span>
    <span>${data.summary_date}</span>
  </div>
</body>
</html>
  `;
}
