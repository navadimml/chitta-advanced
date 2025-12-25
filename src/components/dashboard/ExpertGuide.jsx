import React, { useState } from 'react';
import {
  BookOpen,
  Brain,
  Eye,
  Lightbulb,
  Sparkles,
  Video,
  MessageSquare,
  TrendingUp,
  CheckCircle,
  XCircle,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Target,
  Compass,
  HelpCircle,
  Layers,
  GitBranch,
  Gem,
  Flag,
  Edit3,
} from 'lucide-react';

/**
 * Expert Guide - Comprehensive explanation of Chitta for expert reviewers
 *
 * Written in Hebrew for child development specialists.
 * Explains all terms, processes, and how to use the dashboard effectively.
 */
export default function ExpertGuide() {
  const [expandedSections, setExpandedSections] = useState({
    intro: true,
    process: true,
    terms: true,
    curiosityTypes: true,
    evidence: true,
    videos: true,
    dashboard: true,
  });

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  return (
    <div className="p-8 max-w-4xl mx-auto" dir="rtl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 bg-indigo-100 rounded-2xl">
            <BookOpen className="w-8 h-8 text-indigo-600" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">מדריך למומחה</h1>
            <p className="text-gray-500">הכל על איך צ'יטה עובדת ומה כל מונח אומר</p>
          </div>
        </div>

        <div className="bg-gradient-to-l from-indigo-50 to-purple-50 rounded-2xl p-6 border border-indigo-100">
          <p className="text-lg text-gray-700 leading-relaxed">
            ברוכים הבאים לדשבורד המומחים של צ'יטה.
            כאן תוכלו לראות כיצד המערכת בונה הבנה על כל ילד,
            לבחון את התהליכים הפנימיים, ולתת משוב שמשפר את הדיוק.
          </p>
        </div>
      </div>

      {/* Section: What is Chitta */}
      <GuideSection
        id="intro"
        icon={<Brain className="w-6 h-6" />}
        title="מה זה צ'יטה?"
        expanded={expandedSections.intro}
        onToggle={() => toggleSection('intro')}
      >
        <div className="space-y-4">
          <p>
            <strong>צ'יטה היא פסיכולוגית התפתחותית דיגיטלית</strong> שעוזרת להורים ומומחים
            להבין ילדים בצורה עמוקה יותר. היא לא מאבחנת ולא מחליפה מומחה - היא
            <em> מצביעה על מה שכדאי לשים לב אליו</em>.
          </p>

          <div className="bg-amber-50 border border-amber-100 rounded-xl p-4">
            <p className="text-amber-800">
              <strong>עיקרון מנחה:</strong> צ'יטה מתבוננת בסקרנות, לא בביקורתיות.
              היא אומרת "שמתי לב ש..." ולא "המערכת זיהתה ש...".
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            <FeatureCard
              icon={<Compass className="w-5 h-5 text-indigo-600" />}
              title="מכוונת, לא מחליטה"
              description="מציגה תובנות ושאלות, לא מסקנות סופיות"
            />
            <FeatureCard
              icon={<Target className="w-5 h-5 text-emerald-600" />}
              title="סקרנות, לא רשימות"
              description="בונה הבנה דרך שאלות פתוחות, לא צ'קליסטים"
            />
          </div>
        </div>
      </GuideSection>

      {/* Section: The Process */}
      <GuideSection
        id="process"
        icon={<GitBranch className="w-6 h-6" />}
        title="איך צ'יטה לומדת על ילד?"
        expanded={expandedSections.process}
        onToggle={() => toggleSection('process')}
      >
        <div className="space-y-6">
          <p>
            הלמידה מתרחשת באופן טבעי דרך שיחה. ככל שההורה משתף יותר,
            ההבנה מתעמקת. הנה התהליך:
          </p>

          {/* Process Flow */}
          <div className="relative">
            <div className="absolute right-6 top-8 bottom-8 w-0.5 bg-gradient-to-b from-blue-200 via-purple-200 to-emerald-200" />

            <ProcessStep
              number={1}
              color="blue"
              title="שיחה עם ההורה"
              description="ההורה מספר על הילד - מה קורה בבית, מה מרגיש, מה מאתגר"
              example="'הוא מאוד רגיש לרעשים חזקים, מיד מכסה את האוזניים'"
            />

            <ProcessStep
              number={2}
              color="indigo"
              title="זיהוי תצפיות"
              description="צ'יטה מזהה פרטים משמעותיים מההתנהגות של הילד"
              example="תצפית: 'מגיב לגירויים שמיעתיים בכיסוי אוזניים'"
            />

            <ProcessStep
              number={3}
              color="purple"
              title="יצירת סקרנויות"
              description="נוצרות שאלות ותהיות לגבי מה שנצפה"
              example="סקרנות: 'מה טווח הרגישות השמיעתית שלו?'"
            />

            <ProcessStep
              number={4}
              color="violet"
              title="בניית השערות"
              description="כשיש מספיק מידע, נוצרת תיאוריה לבדיקה"
              example="השערה: 'רגישות שמיעתית גבוהה משפיעה על יכולת הויסות שלו'"
            />

            <ProcessStep
              number={5}
              color="emerald"
              title="זיהוי דפוסים"
              description="חיבור בין תחומים שונים לתמונה רחבה יותר"
              example="דפוס: 'רגישות חושית קשורה לקשיים בוויסות רגשי'"
              isLast
            />
          </div>

          <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-4 mt-6">
            <p className="text-indigo-800">
              <strong>חשוב להבין:</strong> התהליך לא לינארי. צ'יטה יכולה לחזור אחורה,
              לעדכן תצפיות קודמות, או לגלות שהשערה לא מתאימה.
              <em> זו למידה חיה ודינמית.</em>
            </p>
          </div>
        </div>
      </GuideSection>

      {/* Section: Key Terms */}
      <GuideSection
        id="terms"
        icon={<Layers className="w-6 h-6" />}
        title="מונחים מרכזיים"
        expanded={expandedSections.terms}
        onToggle={() => toggleSection('terms')}
      >
        <div className="space-y-6">
          {/* Observation */}
          <TermCard
            icon={<Eye className="w-6 h-6 text-emerald-600" />}
            term="תצפית"
            english="Observation"
            definition="פרט ספציפי שצ'יטה שמה לב אליו מתוך מה שההורה סיפר. תצפית היא עובדתית ותיאורית - לא פרשנית."
            example="'בזמן משחק בקוביות, בונה מגדלים גבוהים ומתסכל כשהם נופלים'"
            note="התחום (domain) של התצפית נקבע אוטומטית: מוטורי, חושי, רגשי, חברתי וכו'"
          />

          {/* Curiosity */}
          <TermCard
            icon={<Lightbulb className="w-6 h-6 text-amber-500" />}
            term="סקרנות"
            english="Curiosity"
            definition="שאלה או תהייה שצ'יטה רוצה לחקור לגבי הילד. זה המנוע של הלמידה - מה עוד רוצים לדעת?"
            example="'איך הוא מתמודד עם תסכול במצבים אחרים?'"
            note="יש 4 סוגים של סקרנות - ראו בהמשך"
          />

          {/* Certainty */}
          <TermCard
            icon={<TrendingUp className="w-6 h-6 text-blue-600" />}
            term="ודאות"
            english="Certainty"
            definition="עד כמה צ'יטה בטוחה במסקנה או בהשערה. מספר בין 0% ל-100%."
            example="ודאות של 75% אומרת שיש בסיס חזק להשערה, אבל עדיין יש מקום לספק"
            scale={[
              { value: '0-30%', label: 'חלשה', color: 'red' },
              { value: '31-60%', label: 'בינונית', color: 'amber' },
              { value: '61-85%', label: 'טובה', color: 'blue' },
              { value: '86-100%', label: 'גבוהה', color: 'emerald' },
            ]}
          />

          {/* Hypothesis */}
          <TermCard
            icon={<Target className="w-6 h-6 text-purple-600" />}
            term="השערה"
            english="Hypothesis"
            definition="סקרנות שהתגבשה לתיאוריה ספציפית שאפשר לבדוק. יש לה 'תיאוריה' - מה אנחנו חושבים שקורה."
            example="השערה: 'הקושי בהרכבת פאזלים קשור לתכנון מוטורי ולא לתפיסה חזותית' (תיאוריה)"
            note="השערות הן המועמדות לבדיקה באמצעות סרטון או שאלות נוספות"
          />

          {/* Pattern */}
          <TermCard
            icon={<Sparkles className="w-6 h-6 text-violet-600" />}
            term="דפוס"
            english="Pattern"
            definition="תובנה שמחברת בין מספר תחומים או תצפיות. דפוס הוא יותר מסכום חלקיו - הוא מראה קשר עמוק."
            example="דפוס: 'רגישות חושית (שמיעה+מגע) קשורה לקושי בויסות רגשי ולהימנעות ממצבים חברתיים'"
            note="דפוסים מתגלים רק אחרי שנצברו מספיק תצפיות בתחומים שונים"
          />

          {/* Crystal */}
          <TermCard
            icon={<Gem className="w-6 h-6 text-cyan-600" />}
            term="קריסטל"
            english="Crystal"
            definition="סיכום מגובש של ההבנה על הילד. נוצר כשיש מספיק מידע לתמונה ברורה. זה 'מי הילד הזה' במילים פשוטות."
            example="'יוסי הוא ילד סקרן עם רגישות חושית גבוהה. הוא מעבד את העולם בעומק - מה שנראה כחוסר תשומת לב הוא למעשה עיבוד פנימי עשיר...'"
            note="הקריסטל מתעדכן ככל שנלמד יותר על הילד"
          />
        </div>
      </GuideSection>

      {/* Section: Curiosity Types */}
      <GuideSection
        id="curiosityTypes"
        icon={<HelpCircle className="w-6 h-6" />}
        title="ארבעת סוגי הסקרנות"
        expanded={expandedSections.curiosityTypes}
        onToggle={() => toggleSection('curiosityTypes')}
      >
        <div className="space-y-4">
          <p className="mb-6">
            לא כל סקרנות היא אותו דבר. יש הבדל בין "מי הילד הזה?" לבין "בוא נבדוק אם X נכון".
            ארבעת הסוגים מייצגים שלבים שונים בתהליך ההבנה:
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <CuriosityTypeCard
              type="גילוי"
              english="Discovery"
              color="emerald"
              icon="🔍"
              description="קליטה פתוחה, ללא הנחות מוקדמות"
              question="מי הילד הזה? מה מאפיין אותו?"
              example="'איך הוא ניגש לפעילויות חדשות?'"
            />

            <CuriosityTypeCard
              type="שאלה"
              english="Question"
              color="blue"
              icon="❓"
              description="מעקב אחרי חוט ספציפי"
              question="רוצים לדעת עוד על משהו שעלה"
              example="'מה קורה כשהוא צריך לחכות?'"
            />

            <CuriosityTypeCard
              type="השערה"
              english="Hypothesis"
              color="purple"
              icon="🎯"
              description="תיאוריה לבדיקה"
              question="יש לנו רעיון מה קורה - בוא נבדוק"
              example="'הקושי החברתי נובע מקושי בקריאת רמזים לא-מילוליים'"
            />

            <CuriosityTypeCard
              type="דפוס"
              english="Pattern"
              color="violet"
              icon="🧩"
              description="חיבור נקודות בין תחומים"
              question="האם יש קשר בין X ל-Y?"
              example="'הרגישות החושית והויסות הרגשי קשורים'"
            />
          </div>

          <div className="bg-purple-50 border border-purple-100 rounded-xl p-4 mt-6">
            <p className="text-purple-800">
              <strong>שימו לב:</strong> סוג הסקרנות ורמת הודאות הם עצמאיים.
              אפשר שתהיה השערה עם ודאות נמוכה (30%) - כי היא חדשה ועדיין לא נבדקה,
              או גילוי עם ודאות גבוהה (80%) - כי יש הרבה ראיות תומכות.
            </p>
          </div>
        </div>
      </GuideSection>

      {/* Section: Evidence */}
      <GuideSection
        id="evidence"
        icon={<CheckCircle className="w-6 h-6" />}
        title="סוגי ראיות"
        expanded={expandedSections.evidence}
        onToggle={() => toggleSection('evidence')}
      >
        <div className="space-y-4">
          <p className="mb-6">
            ראיות הן מידע חדש שמשפיע על הודאות של סקרנות או השערה.
            יש שלושה סוגים של השפעה:
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <EvidenceCard
              type="תומך"
              english="Supports"
              color="emerald"
              icon={<CheckCircle className="w-6 h-6" />}
              effect="+10% לודאות"
              description="הראיה מחזקת את ההשערה"
              example="'שמענו שגם בגן הוא מכסה אוזניים ברעש' - תומך בהשערת הרגישות השמיעתית"
            />

            <EvidenceCard
              type="סותר"
              english="Contradicts"
              color="red"
              icon={<XCircle className="w-6 h-6" />}
              effect="-15% מהודאות"
              description="הראיה מערערת על ההשערה"
              example="'בהופעה של הגן הוא ישב בשקט למרות הרעש' - סותר חלקית את הרגישות"
            />

            <EvidenceCard
              type="משנה"
              english="Transforms"
              color="amber"
              icon={<RefreshCw className="w-6 h-6" />}
              effect="מעדכן את ההשערה"
              description="הראיה משנה את ההבנה לכיוון חדש"
              example="'הבעיה היא לא רעש אלא רעש בלתי צפוי' - מחדד את ההשערה"
            />
          </div>

          <div className="bg-gray-50 border border-gray-100 rounded-xl p-4 mt-6">
            <p className="text-gray-700">
              <strong>איך זה עובד:</strong> ראיות מצטברות לאורך זמן.
              ראיות תומכות מעלות את הודאות, ראיות סותרות מורידות אותה.
              ראיות משנות יכולות לשנות את נוסח ההשערה עצמה.
            </p>
          </div>
        </div>
      </GuideSection>

      {/* Section: Videos */}
      <GuideSection
        id="videos"
        icon={<Video className="w-6 h-6" />}
        title="סרטונים וסוגיהם"
        expanded={expandedSections.videos}
        onToggle={() => toggleSection('videos')}
      >
        <div className="space-y-6">
          <p>
            סרטונים הם כלי חשוב לבדיקת השערות. ההורה מצלם מצב ספציפי,
            וצ'יטה מנתחת את הסרטון לחיפוש ראיות.
          </p>

          {/* Video Categories */}
          <div>
            <h4 className="font-semibold text-gray-800 mb-3">קטגוריות סרטון</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <VideoTypeCard
                type="בדיקת השערה"
                english="hypothesis_test"
                description="סרטון שמטרתו לבדוק השערה ספציפית"
              />
              <VideoTypeCard
                type="חקירת דפוס"
                english="pattern_exploration"
                description="סרטון לחקירת קשר בין תחומים"
              />
              <VideoTypeCard
                type="בסיס חוזקות"
                english="strength_baseline"
                description="סרטון שמתעד חוזקות וכישורים"
              />
              <VideoTypeCard
                type="בסיס"
                english="baseline"
                description="סרטון ראשוני להכרות עם הילד"
              />
              <VideoTypeCard
                type="היעדרות ארוכה"
                english="long_absence"
                description="סרטון אחרי הפסקה ארוכה בשיחות"
              />
              <VideoTypeCard
                type="חזרה"
                english="returning"
                description="סרטון לבדיקת התקדמות לאחר זמן"
              />
            </div>
          </div>

          {/* Video Values */}
          <div>
            <h4 className="font-semibold text-gray-800 mb-3">ערך הסרטון</h4>
            <p className="text-gray-600 mb-3">מה הסרטון יכול לתרום להבנה:</p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="bg-violet-50 border border-violet-100 rounded-xl p-3">
                <span className="font-medium text-violet-700">כיול</span>
                <p className="text-sm text-violet-600">אימות השערה קיימת</p>
              </div>
              <div className="bg-blue-50 border border-blue-100 rounded-xl p-3">
                <span className="font-medium text-blue-700">גילוי</span>
                <p className="text-sm text-blue-600">חשיפת מידע חדש</p>
              </div>
              <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-3">
                <span className="font-medium text-emerald-700">שרשרת</span>
                <p className="text-sm text-emerald-600">חיבור בין התנהגויות</p>
              </div>
            </div>
          </div>

          {/* Video Status */}
          <div>
            <h4 className="font-semibold text-gray-800 mb-3">סטטוס סרטון</h4>
            <div className="flex flex-wrap gap-2">
              <StatusBadge status="ממתין" color="gray" />
              <StatusBadge status="הועלה" color="violet" />
              <StatusBadge status="נותח" color="emerald" />
              <StatusBadge status="ממתין לאישור" color="amber" />
              <StatusBadge status="אושר" color="green" />
              <StatusBadge status="נדחה" color="red" />
              <StatusBadge status="נכשל" color="red" />
            </div>
          </div>
        </div>
      </GuideSection>

      {/* Section: Dashboard Actions */}
      <GuideSection
        id="dashboard"
        icon={<Edit3 className="w-6 h-6" />}
        title="מה אתם יכולים לעשות בדשבורד"
        expanded={expandedSections.dashboard}
        onToggle={() => toggleSection('dashboard')}
      >
        <div className="space-y-6">
          <p>
            הדשבורד נועד לאפשר לכם, המומחים, לבחון את עבודת צ'יטה
            ולספק משוב שמשפר את הדיוק. הנה הפעולות העיקריות:
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <ActionCard
              icon={<Eye className="w-5 h-5 text-blue-600" />}
              title="צפייה בשיחה"
              description="צפו בכל השיחה בין ההורה לצ'יטה, כולל הכלים שהופעלו בכל הודעה"
            />
            <ActionCard
              icon={<Lightbulb className="w-5 h-5 text-amber-600" />}
              title="בחינת השערות"
              description="ראו את כל ההשערות, הראיות שלהן, ואיך הודאות התפתחה לאורך זמן"
            />
            <ActionCard
              icon={<TrendingUp className="w-5 h-5 text-purple-600" />}
              title="התאמת ודאות"
              description="אם לדעתכם הודאות צריכה להיות שונה, תוכלו לשנות ולציין למה"
            />
            <ActionCard
              icon={<Flag className="w-5 h-5 text-red-600" />}
              title="סימון טעות"
              description="סמנו מסקנה שגויה או מידע לא נכון לתיקון"
            />
            <ActionCard
              icon={<MessageSquare className="w-5 h-5 text-emerald-600" />}
              title="הוספת הערות"
              description="הוסיפו הערות קליניות לכל אלמנט - תצפית, סקרנות, או דפוס"
            />
            <ActionCard
              icon={<Video className="w-5 h-5 text-violet-600" />}
              title="צפייה בסרטונים"
              description="צפו בסרטונים שהועלו וראו את הניתוח שצ'יטה ביצעה"
            />
          </div>

          <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-4 mt-6">
            <p className="text-emerald-800">
              <strong>המשוב שלכם חיוני:</strong> כל תיקון ודאות, סימון טעות, או הערה
              שאתם מוסיפים עוזר לנו לשפר את צ'יטה ולהפוך אותה למדויקת יותר.
            </p>
          </div>
        </div>
      </GuideSection>

      {/* Footer */}
      <div className="mt-8 text-center text-gray-400 text-sm">
        <p>שאלות? פנו לצוות התמיכה</p>
      </div>
    </div>
  );
}

// =============================================================================
// HELPER COMPONENTS
// =============================================================================

function GuideSection({ id, icon, title, expanded, onToggle, children }) {
  return (
    <div className="mb-6 bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-5 hover:bg-gray-50 transition"
      >
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gray-50 rounded-xl text-gray-600">
            {icon}
          </div>
          <h2 className="text-xl font-semibold text-gray-800">{title}</h2>
        </div>
        {expanded ? (
          <ChevronUp className="w-5 h-5 text-gray-400" />
        ) : (
          <ChevronDown className="w-5 h-5 text-gray-400" />
        )}
      </button>
      {expanded && (
        <div className="px-5 pb-5 pt-2 text-gray-600 leading-relaxed">
          {children}
        </div>
      )}
    </div>
  );
}

function FeatureCard({ icon, title, description }) {
  return (
    <div className="bg-white border border-gray-100 rounded-xl p-4">
      <div className="flex items-start gap-3">
        {icon}
        <div>
          <h4 className="font-medium text-gray-800">{title}</h4>
          <p className="text-sm text-gray-500">{description}</p>
        </div>
      </div>
    </div>
  );
}

function ProcessStep({ number, color, title, description, example, isLast }) {
  const colors = {
    blue: 'bg-blue-500',
    indigo: 'bg-indigo-500',
    purple: 'bg-purple-500',
    violet: 'bg-violet-500',
    emerald: 'bg-emerald-500',
  };

  return (
    <div className={`relative pr-16 ${isLast ? '' : 'pb-8'}`}>
      <div className={`absolute right-4 w-5 h-5 rounded-full ${colors[color]} flex items-center justify-center text-white text-xs font-bold`}>
        {number}
      </div>
      <div className="bg-white border border-gray-100 rounded-xl p-4">
        <h4 className="font-medium text-gray-800 mb-1">{title}</h4>
        <p className="text-sm text-gray-600 mb-2">{description}</p>
        <div className="bg-gray-50 rounded-lg p-2 text-sm text-gray-500 italic">
          {example}
        </div>
      </div>
    </div>
  );
}

function TermCard({ icon, term, english, definition, example, note, scale }) {
  return (
    <div className="bg-gray-50 rounded-xl p-5 border border-gray-100">
      <div className="flex items-start gap-4">
        <div className="p-2 bg-white rounded-xl shadow-sm">
          {icon}
        </div>
        <div className="flex-1">
          <div className="flex items-baseline gap-2 mb-2">
            <h4 className="text-lg font-semibold text-gray-800">{term}</h4>
            <span className="text-sm text-gray-400">({english})</span>
          </div>
          <p className="text-gray-600 mb-3">{definition}</p>

          {example && (
            <div className="bg-white rounded-lg p-3 border border-gray-100 mb-3">
              <span className="text-xs text-gray-400 block mb-1">דוגמה:</span>
              <p className="text-sm text-gray-700 italic">{example}</p>
            </div>
          )}

          {scale && (
            <div className="flex gap-2 mb-3">
              {scale.map((item, i) => (
                <div
                  key={i}
                  className={`flex-1 text-center text-xs py-1.5 rounded-lg ${
                    item.color === 'red' ? 'bg-red-50 text-red-600' :
                    item.color === 'amber' ? 'bg-amber-50 text-amber-600' :
                    item.color === 'blue' ? 'bg-blue-50 text-blue-600' :
                    'bg-emerald-50 text-emerald-600'
                  }`}
                >
                  <div className="font-medium">{item.value}</div>
                  <div>{item.label}</div>
                </div>
              ))}
            </div>
          )}

          {note && (
            <p className="text-sm text-gray-500 italic">
              💡 {note}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

function CuriosityTypeCard({ type, english, color, icon, description, question, example }) {
  const colors = {
    emerald: 'border-emerald-200 bg-emerald-50',
    blue: 'border-blue-200 bg-blue-50',
    purple: 'border-purple-200 bg-purple-50',
    violet: 'border-violet-200 bg-violet-50',
  };

  const textColors = {
    emerald: 'text-emerald-700',
    blue: 'text-blue-700',
    purple: 'text-purple-700',
    violet: 'text-violet-700',
  };

  return (
    <div className={`rounded-xl p-4 border ${colors[color]}`}>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-2xl">{icon}</span>
        <div>
          <h4 className={`font-semibold ${textColors[color]}`}>{type}</h4>
          <span className="text-xs text-gray-400">{english}</span>
        </div>
      </div>
      <p className="text-sm text-gray-600 mb-2">{description}</p>
      <p className="text-sm text-gray-500 mb-2">
        <strong>השאלה:</strong> {question}
      </p>
      <div className="bg-white/60 rounded-lg p-2 text-sm text-gray-600 italic">
        {example}
      </div>
    </div>
  );
}

function EvidenceCard({ type, english, color, icon, effect, description, example }) {
  const colors = {
    emerald: 'border-emerald-200 bg-emerald-50',
    red: 'border-red-200 bg-red-50',
    amber: 'border-amber-200 bg-amber-50',
  };

  const iconColors = {
    emerald: 'text-emerald-600',
    red: 'text-red-600',
    amber: 'text-amber-600',
  };

  return (
    <div className={`rounded-xl p-4 border ${colors[color]}`}>
      <div className="flex items-center gap-2 mb-3">
        <span className={iconColors[color]}>{icon}</span>
        <div>
          <h4 className="font-semibold text-gray-800">{type}</h4>
          <span className="text-xs text-gray-400">{english}</span>
        </div>
      </div>
      <div className="bg-white/60 rounded-lg px-2 py-1 text-sm font-medium text-gray-700 inline-block mb-2">
        {effect}
      </div>
      <p className="text-sm text-gray-600 mb-2">{description}</p>
      <div className="bg-white/60 rounded-lg p-2 text-xs text-gray-500 italic">
        {example}
      </div>
    </div>
  );
}

function VideoTypeCard({ type, english, description }) {
  return (
    <div className="bg-violet-50 border border-violet-100 rounded-xl p-3">
      <div className="flex items-baseline gap-2 mb-1">
        <span className="font-medium text-violet-700">{type}</span>
        <span className="text-xs text-violet-400">{english}</span>
      </div>
      <p className="text-sm text-violet-600">{description}</p>
    </div>
  );
}

function StatusBadge({ status, color }) {
  const colors = {
    gray: 'bg-gray-100 text-gray-600',
    violet: 'bg-violet-100 text-violet-600',
    emerald: 'bg-emerald-100 text-emerald-600',
    amber: 'bg-amber-100 text-amber-600',
    green: 'bg-green-100 text-green-600',
    red: 'bg-red-100 text-red-600',
  };

  return (
    <span className={`px-3 py-1 rounded-lg text-sm ${colors[color]}`}>
      {status}
    </span>
  );
}

function ActionCard({ icon, title, description }) {
  return (
    <div className="bg-gray-50 border border-gray-100 rounded-xl p-4">
      <div className="flex items-start gap-3">
        <div className="p-2 bg-white rounded-lg shadow-sm">
          {icon}
        </div>
        <div>
          <h4 className="font-medium text-gray-800 mb-1">{title}</h4>
          <p className="text-sm text-gray-500">{description}</p>
        </div>
      </div>
    </div>
  );
}
