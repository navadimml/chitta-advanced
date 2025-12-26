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
  Zap,
  ArrowUpRight,
  Clock,
  FileText,
  Play,
  Camera,
  Search,
  Activity,
  BarChart3,
  BookMarked,
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
    evidenceDeep: false,
    understanding: false,
    conversation: false,
    conversationExample: false,
    crystal: false,
    videos: true,
    videoAnalysis: false,
    dashboard: true,
    glossary: false,
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
        <div className="space-y-5">
          {/* Main definition */}
          <p className="text-gray-700 leading-relaxed">
            <strong>צ'יטה היא מלווה התבוננות התפתחותית</strong>, המסייעת להורים ולאנשי מקצוע
            להבין את עולמו של הילד דרך סקרנות, הקשבה ושאלות מכוונות.
          </p>

          <p className="text-gray-700 leading-relaxed">
            היא נשענת על ידע התפתחותי מבוסס כדי לכוון את תשומת הלב: להציע נקודות מבט רלוונטיות,
            לעורר שאלות מקצועיות, ולהדגיש היבטים שכדאי לבחון לעומק.
            צ'יטה <strong>אינה כלי אבחוני</strong> ואינה מסיקה מסקנות קליניות — היא יוצרת מסגרת של גילוי משותף,
            שבה האחריות לפרשנות, לאינטגרציה מקצועית ולמתן פידבק נשארת בידי אנשי המקצוע.
          </p>

          {/* Ethical principle */}
          <div className="bg-amber-50 border border-amber-100 rounded-xl p-5">
            <p className="text-amber-800 font-medium mb-2">
              עיקרון אתי מנחה: צ'יטה פועלת מתוך סקרנות, זהירות וכבוד.
            </p>
            <p className="text-amber-700 leading-relaxed">
              היא מציגה ניסוחים תצפיתיים ופתוחים (כגון "שמתי לב ש…", "ייתכן שכדאי להתבונן ב…")
              ונמנעת משפה אבחנתית, שיפוטית או קובעת. מטרתה היא לאפשר הבנה עמוקה ומדויקת יותר —
              מבלי לצמצם את הילד לכדי תוצאה, ציון או אבחנה.
            </p>
          </div>

          {/* Professional support */}
          <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-5">
            <p className="text-indigo-800 leading-relaxed">
              צ'יטה נועדה <strong>לתמוך בעבודה מקצועית</strong>, להעמיק שיח בין-מקצועי,
              ולחזק תהליכי קבלת החלטות אחראיים סביב הילד —
              מבלי להחליף אחריות, סמכות או שיקול דעת אנושי.
            </p>
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
            example="'בזמן משחק בקוביות, בונה מגדלים גבוהים ומביע תסכול כשהם נופלים'"
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
            example="'יוסי הוא ילד סקרן עם רגישות חושית גבוהה. הוא חווה את העולם בעוצמה - מה שנראה כחוסר תשומת לב הוא למעשה התבוננות פנימית עשירה...'"
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
              description="העמקה בנושא שעלה"
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

      {/* Section: Evidence Deep Dive */}
      <GuideSection
        id="evidenceDeep"
        icon={<Zap className="w-6 h-6" />}
        title="איך ראיות משפיעות על הודאות"
        expanded={expandedSections.evidenceDeep}
        onToggle={() => toggleSection('evidenceDeep')}
      >
        <div className="space-y-6">
          <p>
            המערכת משתמשת בחישוב מתמטי פשוט אך מדויק כדי לעדכן את רמת הודאות
            בכל פעם שמתווספת ראיה חדשה.
          </p>

          {/* The Math */}
          <div className="bg-gray-50 rounded-xl p-5 border border-gray-200">
            <h4 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-blue-600" />
              החישוב
            </h4>

            <div className="space-y-4">
              <div className="flex items-center gap-4 p-3 bg-emerald-50 rounded-lg border border-emerald-100">
                <div className="text-2xl">➕</div>
                <div>
                  <div className="font-medium text-emerald-800">ראיה תומכת</div>
                  <div className="text-emerald-600 text-sm">+10% לודאות (עד מקסימום 100%)</div>
                </div>
              </div>

              <div className="flex items-center gap-4 p-3 bg-red-50 rounded-lg border border-red-100">
                <div className="text-2xl">➖</div>
                <div>
                  <div className="font-medium text-red-800">ראיה סותרת</div>
                  <div className="text-red-600 text-sm">-15% מהודאות (עד מינימום 0%)</div>
                </div>
              </div>

              <div className="flex items-center gap-4 p-3 bg-amber-50 rounded-lg border border-amber-100">
                <div className="text-2xl">🔄</div>
                <div>
                  <div className="font-medium text-amber-800">ראיה משנה (transforms)</div>
                  <div className="text-amber-600 text-sm">איפוס ל-40% — התחלה מחדש עם הבנה חדשה</div>
                </div>
              </div>
            </div>
          </div>

          {/* Asymmetry explanation */}
          <div className="bg-purple-50 border border-purple-100 rounded-xl p-5">
            <h4 className="font-medium text-purple-800 mb-2">למה האסימטריה?</h4>
            <p className="text-purple-700 leading-relaxed">
              שימו לב: ראיה סותרת מורידה יותר (-15%) מאשר ראיה תומכת מעלה (+10%).
              זה מכוון — קל יותר לצבור ראיות תומכות בהדרגה, אבל ראיה סותרת אחת
              צריכה לשקול יותר בשקילה מחודשת. זה מונע "אישור הטיה" (confirmation bias).
            </p>
          </div>

          {/* Example */}
          <div className="bg-blue-50 rounded-xl p-5 border border-blue-100">
            <h4 className="font-medium text-blue-800 mb-3">דוגמה מעשית</h4>
            <div className="space-y-2 text-sm">
              <p className="text-blue-700">השערה: "רגישות שמיעתית גבוהה משפיעה על ויסות"</p>
              <p className="text-blue-700">ודאות התחלתית: <strong>50%</strong></p>
              <div className="border-r-2 border-blue-300 pr-3 mr-2 space-y-1">
                <p className="text-blue-600">• ההורה: "גם בגן הוא מכסה אוזניים" (תומך) — ודאות: <strong>60%</strong></p>
                <p className="text-blue-600">• ההורה: "אבל בהופעה ישב בשקט" (סותר) — ודאות: <strong>45%</strong></p>
                <p className="text-blue-600">• ההורה: "אבל זה רק ברעש פתאומי" (משנה) — ודאות: <strong>40%</strong> (איפוס)</p>
              </div>
              <p className="text-blue-700 mt-2">עכשיו ההשערה מתחדדת: לא רגישות כללית, אלא לרעשים בלתי צפויים.</p>
            </div>
          </div>

          {/* Video vs Conversation */}
          <div className="bg-violet-50 border border-violet-100 rounded-xl p-4">
            <p className="text-violet-800">
              <strong>סרטונים משפיעים יותר:</strong> ראיות מסרטון מקבלות משקל גבוה יותר
              (עד +15% או -20%) כי הן מבוססות על צפייה ישירה ולא רק על דיווח.
            </p>
          </div>
        </div>
      </GuideSection>

      {/* Section: Understanding Evolution */}
      <GuideSection
        id="understanding"
        icon={<ArrowUpRight className="w-6 h-6" />}
        title="איך ההבנה מתפתחת"
        expanded={expandedSections.understanding}
        onToggle={() => toggleSection('understanding')}
      >
        <div className="space-y-6">
          <p>
            ההבנה על הילד לא קופאת במקום — היא מתפתחת דרך שלבים.
            הנה המסלול הטיפוסי מגילוי ראשוני ועד תמונה מגובשת:
          </p>

          {/* Evolution Flow */}
          <div className="relative">
            <div className="absolute right-6 top-8 bottom-8 w-0.5 bg-gradient-to-b from-emerald-300 via-blue-300 via-purple-300 to-violet-300" />

            <EvolutionStep
              number={1}
              color="emerald"
              title="גילוי (Discovery)"
              description="שאלות פתוחות, קליטה ללא הנחות מוקדמות"
              trigger="מתחילות אוטומטית עם פתיחת הפרופיל"
              example="'מי הילד הזה?' — תמיד פעילה ברקע"
            />

            <EvolutionStep
              number={2}
              color="blue"
              title="שאלה (Question)"
              description="כשמשהו עולה מהשיחה ורוצים לדעת עוד"
              trigger="LLM מזהה נושא שדורש העמקה"
              example="'מה קורה כשהוא צריך לחכות?' — נולדת מתוך סיפור על תסכול"
            />

            <EvolutionStep
              number={3}
              color="purple"
              title="השערה (Hypothesis)"
              description="תיאוריה ספציפית שאפשר לבדוק"
              trigger="כשיש מספיק מידע לנסח רעיון + אפשרות לבדוק בסרטון"
              example="'הקושי בהרכבת פאזלים קשור לתכנון מוטורי' — ניתן לבדיקה בסרטון"
            />

            <EvolutionStep
              number={4}
              color="violet"
              title="דפוס (Pattern)"
              description="קשר בין תחומים שונים — תובנה רחבה יותר"
              trigger="סיפור שנוגע ב-2+ תחומים עם משמעות גבוהה"
              example="'רגישות חושית → קושי בוויסות → הימנעות חברתית'"
              isLast
            />
          </div>

          {/* Automatic transitions */}
          <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-5">
            <h4 className="font-medium text-indigo-800 mb-3">מעברים אוטומטיים</h4>
            <ul className="space-y-2 text-indigo-700">
              <li className="flex items-start gap-2">
                <span className="text-indigo-500 mt-1">•</span>
                <span><strong>שאלה → השערה:</strong> כש-LLM מזהה תיאוריה ברת-בדיקה ומציע סרטון</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-indigo-500 mt-1">•</span>
                <span><strong>תצפיות → דפוס:</strong> כשסיפור מחבר 2+ תחומים עם significance ≥ 0.5</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-indigo-500 mt-1">•</span>
                <span><strong>ודאות גבוהה → דעיכה:</strong> סקרנות שהגיעה ל-70%+ ודאות יורדת ב"משיכה" שלה</span>
              </li>
            </ul>
          </div>

          {/* Crystallization triggers */}
          <div className="bg-gradient-to-l from-cyan-50 to-blue-50 rounded-xl p-5 border border-cyan-100">
            <h4 className="font-medium text-cyan-800 mb-3 flex items-center gap-2">
              <Gem className="w-5 h-5" />
              מתי נוצר קריסטל?
            </h4>
            <p className="text-cyan-700 mb-3">
              המערכת מזהה שהגיע הזמן ליצור תמונה מגובשת כשמתקיים אחד מאלה:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="bg-white/60 rounded-lg p-3 text-center">
                <div className="text-2xl mb-1">2+</div>
                <div className="text-sm text-cyan-600">השערות שנחקרו</div>
              </div>
              <div className="bg-white/60 rounded-lg p-3 text-center">
                <div className="text-2xl mb-1">5+</div>
                <div className="text-sm text-cyan-600">סיפורים נאספו</div>
              </div>
              <div className="bg-white/60 rounded-lg p-3 text-center">
                <div className="text-2xl mb-1">10+</div>
                <div className="text-sm text-cyan-600">תצפיות נרשמו</div>
              </div>
            </div>
          </div>
        </div>
      </GuideSection>

      {/* Section: Conversation Flow */}
      <GuideSection
        id="conversation"
        icon={<MessageSquare className="w-6 h-6" />}
        title="איך השיחה מנווטת"
        expanded={expandedSections.conversation}
        onToggle={() => toggleSection('conversation')}
      >
        <div className="space-y-6">
          <p>
            צ'יטה לא עוקבת אחרי סקריפט קבוע. במקום זה, היא מגיבה לכל מה שההורה משתף
            ומכוונת את השיחה בהתאם. הנה איך זה עובד מאחורי הקלעים:
          </p>

          {/* Two-Phase Architecture */}
          <div className="bg-gray-50 rounded-xl p-5 border border-gray-200">
            <h4 className="font-semibold text-gray-800 mb-4">ארכיטקטורת שני שלבים</h4>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-blue-50 rounded-lg p-4 border border-blue-100">
                <div className="flex items-center gap-2 mb-2">
                  <Search className="w-5 h-5 text-blue-600" />
                  <span className="font-medium text-blue-800">שלב 1: תפיסה</span>
                </div>
                <p className="text-sm text-blue-700 mb-2">
                  צ'יטה "קוראת" את ההודעה ומזהה:
                </p>
                <ul className="text-xs text-blue-600 space-y-1">
                  <li>• האם יש כאן סיפור משמעותי?</li>
                  <li>• האם זה מוסיף ראיה להשערה?</li>
                  <li>• איזה תחום התפתחותי מוזכר?</li>
                  <li>• מה הכוונה של ההורה?</li>
                </ul>
              </div>

              <div className="bg-emerald-50 rounded-lg p-4 border border-emerald-100">
                <div className="flex items-center gap-2 mb-2">
                  <MessageSquare className="w-5 h-5 text-emerald-600" />
                  <span className="font-medium text-emerald-800">שלב 2: תגובה</span>
                </div>
                <p className="text-sm text-emerald-700 mb-2">
                  צ'יטה מגיבה בהתאם למה שזוהה:
                </p>
                <ul className="text-xs text-emerald-600 space-y-1">
                  <li>• סיפור → הכרה במשמעות</li>
                  <li>• שאלה → מענה ישיר + גשר</li>
                  <li>• רגש → מתן מקום</li>
                  <li>• מידע → העמקה טבעית</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Pull System */}
          <div className="bg-amber-50 border border-amber-100 rounded-xl p-5">
            <h4 className="font-medium text-amber-800 mb-3 flex items-center gap-2">
              <Activity className="w-5 h-5" />
              מערכת ה"משיכה" (Pull)
            </h4>
            <p className="text-amber-700 mb-4">
              לכל סקרנות יש "משיכה" — עד כמה היא דורשת תשומת לב כרגע.
              המשיכה מחושבת מחדש בכל תור:
            </p>

            <div className="space-y-2">
              <div className="flex items-center gap-3 p-2 bg-white/60 rounded-lg">
                <span className="text-lg">⬆️</span>
                <div className="text-sm text-amber-700">
                  <strong>עולה:</strong> כשיש פערים בתחום (אין מספיק מידע)
                </div>
              </div>
              <div className="flex items-center gap-3 p-2 bg-white/60 rounded-lg">
                <span className="text-lg">⬇️</span>
                <div className="text-sm text-amber-700">
                  <strong>יורדת:</strong> כשהודאות גבוהה (כבר מבינים) או שעבר זמן בלי פעילות
                </div>
              </div>
              <div className="flex items-center gap-3 p-2 bg-white/60 rounded-lg">
                <span className="text-lg">🎯</span>
                <div className="text-sm text-amber-700">
                  <strong>תחומים קליניים:</strong> מקבלים boost נוסף כי נדרשים למכתבים
                </div>
              </div>
            </div>
          </div>

          {/* Natural Flow */}
          <div className="bg-green-50 border border-green-100 rounded-xl p-4">
            <p className="text-green-800">
              <strong>העיקרון המנחה:</strong> צ'יטה לא "דוחפת" נושאים אלא "עוקבת אחרי הזרם".
              הסקרנויות מציעות כיוונים, אבל ההורה מוביל את השיחה.
              רק כשיש רגע טבעי, צ'יטה עשויה לשזור שאלה רלוונטית.
            </p>
          </div>
        </div>
      </GuideSection>

      {/* Section: Conversation Example - Chitta's Inner Voice */}
      <GuideSection
        id="conversationExample"
        icon={<Sparkles className="w-6 h-6" />}
        title="בתוך הראש של צ'יטה — דוגמה חיה"
        expanded={expandedSections.conversationExample}
        onToggle={() => toggleSection('conversationExample')}
      >
        <div className="space-y-6">
          <p>
            בואו נציץ לתוך "הראש" של צ'יטה במהלך שיחה אמיתית.
            מה היא חושבת? איך היא מחליטה מה לשאול? הנה דוגמה:
          </p>

          {/* Setup */}
          <div className="bg-gray-100 rounded-xl p-4 border border-gray-200">
            <div className="text-sm text-gray-500 mb-2">📋 מצב התחלתי:</div>
            <div className="text-gray-700">
              <strong>ילד:</strong> יואב, בן 4
              <br />
              <strong>סקרנויות פתוחות:</strong>
              <ul className="mr-4 mt-1 space-y-1">
                <li>• "איך יואב מתמודד עם מעברים?" (שאלה, ודאות 35%, משיכה 0.7)</li>
                <li>• "מה מאפיין את המשחק שלו?" (גילוי, ודאות 20%, משיכה 0.5)</li>
                <li>• "רגישות חושית משפיעה על ויסות" (השערה, ודאות 55%, משיכה 0.6)</li>
              </ul>
            </div>
          </div>

          {/* Turn 1 */}
          <ConversationTurnExample
            turnNumber={1}
            parentMessage="היום היה לנו בוקר קשה. יואב לא רצה להתלבש בשום אופן, צרח שהחולצה 'עוקצת'"
            chittaThinking={[
              "הממ, 'עוקצת'... זה נשמע כמו רגישות טקסטילית. זה מחזק את ההשערה שלי על רגישות חושית!",
              "אני אוסיפה את זה כראיה תומכת. ודאות עולה מ-55% ל-65%.",
              "רגע, זה גם קשור למעברים — הוא התקשה במעבר מפיג'מה לבגדים. שתי סקרנויות מתחברות!",
              "המשיכה של 'מעברים' עכשיו הכי גבוהה (0.8). אבל לא אלחץ — אעקוב אחרי מה שהאמא רוצה לספר.",
            ]}
            chittaResponse="זה נשמע כמו בוקר מאתגר. כשהוא אומר שהחולצה 'עוקצת' — זה קורה עם בגדים מסוימים? או שזה משתנה?"
            toolCalls={[
              { tool: "notice", content: "תגובה שלילית לטקסטורת בד — מתאר תחושת 'עקיצה'" },
              { tool: "add_evidence", content: "תומך בהשערת רגישות חושית (מקור: שיחה)" },
            ]}
          />

          {/* Turn 2 */}
          <ConversationTurnExample
            turnNumber={2}
            parentMessage="כן, יש חולצות שהוא בכלל לא מוכן ללבוש. רק כותנה רכה. ואסור שיהיו תוויות."
            chittaThinking={[
              "וואו, עוד אישור! תוויות וטקסטורות — זה ממש קלאסי לרגישות טקטילית.",
              "הודאות קופצת ל-75%! זו כבר רמה גבוהה.",
              "אבל רגע — אני לא רוצה להתקבע. בוא נראה אם זה מתחבר לתחומים אחרים.",
              "יש לי רעיון: אולי אציע סרטון? לצלם את הבוקר כדי לראות את הרצף המלא...",
              "לא, עדיין מוקדם. קודם אבין יותר על המעברים בכלל.",
            ]}
            chittaResponse="כותנה רכה ובלי תוויות — הוא יודע בדיוק מה מתאים לו. ספרי לי, מלבד ההתלבשות — איך הוא עם מעברים אחרים במהלך היום?"
            toolCalls={[
              { tool: "notice", content: "העדפה ברורה לכותנה רכה, רגישות לתוויות" },
              { tool: "add_evidence", content: "תומך בהשערת רגישות חושית — ודאות 75%" },
            ]}
            chittaNote="שימו לב: צ'יטה בחרה לעקוב אחרי הסקרנות עם המשיכה הגבוהה ביותר (מעברים), אבל עשתה את זה בצורה טבעית שמתחברת למה שהאמא סיפרה."
          />

          {/* Turn 3 */}
          <ConversationTurnExample
            turnNumber={3}
            parentMessage="מעברים? תראי, יציאה מהבית זה תמיד דרמה. אבל דווקא כשאנחנו בגן, הוא נפרד ממני בקלות!"
            chittaThinking={[
              "רגע רגע! זה מעניין מאוד!",
              "הנחתי שהבעיה היא במעברים בכלל, אבל זה לא מדויק.",
              "הבעיה היא ביציאה מהבית, לא בפרידה. אלה שני דברים שונים!",
              "זו ראיה שמשנה את ההבנה שלי. לא 'סותרת' — 'משנה' (transforms).",
              "ההשערה על מעברים צריכה להתחדד: לא 'מעברים' אלא 'מעברים מסביבה מוכרת לבלתי מוכרת'.",
              "אני אעדכן את הסקרנות. ודאות יורדת ל-40% (איפוס) כי ההבנה השתנתה.",
            ]}
            chittaResponse="זה ממש מעניין! אז בגן, כשהוא כבר שם, הפרידה קלה. הקושי הוא דווקא ברגע היציאה מהבית. מה את חושבת שקורה ברגע הזה?"
            toolCalls={[
              { tool: "notice", content: "פרידה קלה בגן, קושי ביציאה מהבית — הבחנה חשובה" },
              { tool: "add_evidence", content: "משנה את הבנת 'מעברים' — ודאות 40% (איפוס)" },
              { tool: "wonder", content: "שאלה חדשה: מה בסביבה הביתית מקשה על היציאה?" },
            ]}
            chittaNote="הנה רגע קריטי: צ'יטה לא נצמדת להשערה הישנה. היא מוכנה 'לאפס' ולהתחיל מחדש עם הבנה מדויקת יותר."
          />

          {/* Turn 4 - Pattern Emerging */}
          <ConversationTurnExample
            turnNumber={4}
            parentMessage="אני חושבת שזה העומס. בבית הוא יודע בדיוק איפה הכל, מרגיש בשליטה. ברגע שיוצאים — הכל פתוח ולא צפוי."
            chittaThinking={[
              "💡 רגע של תובנה!",
              "הנה הקשר: רגישות חושית + צורך בשליטה + קושי עם חוסר ודאות.",
              "זה מסביר גם את הבגדים — הוא יודע בדיוק איזה בד 'בטוח'.",
              "וגם את היציאה — בחוץ הוא לא יודע מה לצפות.",
              "זה לא שלוש בעיות נפרדות. זה דפוס אחד!",
              "אני רואה דפוס חוצה-תחומים: חושי + רגשי + התנהגותי.",
              "עכשיו זה הזמן להציע סרטון — לראות את הרצף ביציאה מהבית.",
            ]}
            chittaResponse="את מתארת משהו חשוב מאוד. יואב צריך לדעת מה לצפות — גם בבגדים וגם בסביבה. כשהוא מרגיש בשליטה, הוא מסתדר יפה. האם תרצי שנצלם את רגע היציאה מהבית? זה יכול לעזור לנו להבין בדיוק מה עוזר לו ומה מקשה."
            toolCalls={[
              { tool: "notice", content: "צורך בשליטה ובציפיות ברורות — חוצה תחומים" },
              { tool: "wonder", content: "דפוס: רגישות חושית + צורך בשליטה + חוסר ודאות = קושי" },
              { tool: "suggest_video", content: "בקשת סרטון — רגע היציאה מהבית" },
            ]}
            chittaNote="כאן נוצר דפוס! שלושה תחומים התחברו לתובנה אחת. זה הרגע שבו ההבנה 'מתגבשת'."
          />

          {/* Summary */}
          <div className="bg-gradient-to-l from-indigo-50 to-purple-50 rounded-xl p-5 border border-indigo-100">
            <h4 className="font-medium text-indigo-800 mb-3">מה למדנו מהדוגמה?</h4>
            <ul className="space-y-2 text-indigo-700">
              <li className="flex items-start gap-2">
                <span className="text-indigo-400 mt-1">✓</span>
                <span><strong>עקיבה אחרי משיכה:</strong> צ'יטה עקבה אחרי הסקרנות עם המשיכה הגבוהה, אבל בצורה טבעית</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-indigo-400 mt-1">✓</span>
                <span><strong>ראיות משנות הבנה:</strong> כשהמידע סתר את ההנחה, צ'יטה איפסה ולא התעקשה</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-indigo-400 mt-1">✓</span>
                <span><strong>דפוס מתגלה:</strong> כשמספיק נקודות התחברו, נוצרה תובנה חוצת-תחומים</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-indigo-400 mt-1">✓</span>
                <span><strong>סרטון בזמן הנכון:</strong> ההצעה לצלם באה רק כשהיה ברור מה לבדוק</span>
              </li>
            </ul>
          </div>
        </div>
      </GuideSection>

      {/* Section: Crystal Deep Dive */}
      <GuideSection
        id="crystal"
        icon={<Gem className="w-6 h-6" />}
        title="הקריסטל — הפורטרט החי"
        expanded={expandedSections.crystal}
        onToggle={() => toggleSection('crystal')}
      >
        <div className="space-y-6">
          <p>
            הקריסטל הוא סינתזה מגובשת של כל מה שצ'יטה למדה על הילד.
            זה לא דו"ח או רשימת ממצאים — זה <strong>פורטרט</strong> שמציג מי הילד הזה באמת.
          </p>

          {/* Two Gifts */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-gradient-to-bl from-rose-50 to-pink-50 rounded-xl p-5 border border-rose-100">
              <h4 className="font-medium text-rose-800 mb-2">🎁 מתנה ראשונה: הכרה</h4>
              <p className="text-rose-700 text-sm leading-relaxed">
                "כן! זה בדיוק הוא!" — ההורים מרגישים שמישהו באמת רואה את הילד שלהם.
                לא תיאור קליני, אלא הכרה אמיתית במי שהוא.
              </p>
            </div>

            <div className="bg-gradient-to-bl from-sky-50 to-blue-50 rounded-xl p-5 border border-sky-100">
              <h4 className="font-medium text-sky-800 mb-2">🎁 מתנה שנייה: תובנה קלינית</h4>
              <p className="text-sky-700 text-sm leading-relaxed">
                "לא ראיתי את זה ככה קודם!" — חיבור נקודות שמפתיע ומאיר.
                ההורים מגלים קשרים שלא היו ברורים להם.
              </p>
            </div>
          </div>

          {/* Crystal Components */}
          <div className="bg-gray-50 rounded-xl p-5 border border-gray-200">
            <h4 className="font-semibold text-gray-800 mb-4">מה יש בקריסטל?</h4>

            <div className="space-y-3">
              <CrystalComponent
                icon="✨"
                name="נרטיב מהות"
                description="2-3 משפטים על מי הילד הזה — לא מה הבעיות, אלא מי הוא"
              />
              <CrystalComponent
                icon="🌡️"
                name="טמפרמנט"
                description="תכונות ליבה בשפה יומיומית — 'סקרן', 'רגיש', 'אנרגטי'"
              />
              <CrystalComponent
                icon="🧩"
                name="דפוסים"
                description="קשרים בין תחומים — איך דבר אחד משפיע על השני"
              />
              <CrystalComponent
                icon="🌉"
                name="נתיבי התערבות"
                description="גשרים מחוזקות לאתגרים — איך להשתמש במה שהוא אוהב"
              />
              <CrystalComponent
                icon="🔮"
                name="שאלות פתוחות"
                description="מה עוד תוהים — לא פערים אלא סקרנות"
              />
              <CrystalComponent
                icon="👩‍⚕️"
                name="המלצות למומחים"
                description="התאמה לא-מובנת לאנשי מקצוע ספציפיים"
              />
            </div>
          </div>

          {/* Three Layers */}
          <div className="bg-violet-50 border border-violet-100 rounded-xl p-5">
            <h4 className="font-medium text-violet-800 mb-3">שלושה רבדים נפרדים</h4>
            <p className="text-violet-700 mb-3">
              במכתב למומחים, המידע מופרד לשלושה רבדים ברורים:
            </p>
            <div className="space-y-2">
              <div className="bg-white/60 rounded-lg p-3 flex items-start gap-3">
                <span className="text-violet-500 font-bold">1</span>
                <div>
                  <div className="font-medium text-violet-800">מה ההורים שיתפו</div>
                  <div className="text-sm text-violet-600">התצפיות שלהם, במילים שלהם</div>
                </div>
              </div>
              <div className="bg-white/60 rounded-lg p-3 flex items-start gap-3">
                <span className="text-violet-500 font-bold">2</span>
                <div>
                  <div className="font-medium text-violet-800">מה צ'יטה שמה לב</div>
                  <div className="text-sm text-violet-600">דפוסים ותהיות — מוצעים, לא נקבעים</div>
                </div>
              </div>
              <div className="bg-white/60 rounded-lg p-3 flex items-start gap-3">
                <span className="text-violet-500 font-bold">3</span>
                <div>
                  <div className="font-medium text-violet-800">מה נשאר פתוח</div>
                  <div className="text-sm text-violet-600">שאלות לחקירה משותפת</div>
                </div>
              </div>
            </div>
          </div>

          {/* Staleness */}
          <div className="bg-amber-50 border border-amber-100 rounded-xl p-4">
            <p className="text-amber-800">
              <strong>עדכניות:</strong> הקריסטל יודע מתי הוא "מיושן" — אם נוספו תצפיות חדשות
              מאז שנוצר, המערכת תעדכן אותו בצורה הדרגתית במקום לייצר מחדש.
            </p>
          </div>
        </div>
      </GuideSection>

      {/* Section: Video Analysis Deep Dive */}
      <GuideSection
        id="videoAnalysis"
        icon={<Camera className="w-6 h-6" />}
        title="ניתוח סרטונים — מאחורי הקלעים"
        expanded={expandedSections.videoAnalysis}
        onToggle={() => toggleSection('videoAnalysis')}
      >
        <div className="space-y-6">
          <p>
            סרטונים הם כלי רב-עוצמה לבדיקת השערות. הנה איך התהליך עובד מקבלת ההסכמה
            ועד ניתוח התוצאות:
          </p>

          {/* Guidelines Generation */}
          <div className="bg-blue-50 rounded-xl p-5 border border-blue-100">
            <h4 className="font-medium text-blue-800 mb-3 flex items-center gap-2">
              <FileText className="w-5 h-5" />
              שלב 1: יצירת הנחיות צילום
            </h4>
            <p className="text-blue-700 mb-3">
              ההנחיות נוצרות באופן אישי להורה, תוך שימוש באוצר המילים שלו:
            </p>
            <ul className="space-y-2 text-sm text-blue-600">
              <li className="flex items-start gap-2">
                <span className="text-blue-400">•</span>
                <span>משתמשים בשמות של צעצועים/מקומות שההורה הזכיר</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-400">•</span>
                <span>ההשערה נשארת פנימית — ההורה לא יודע מה בודקים</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-400">•</span>
                <span>ההנחיות חמות וספציפיות: "שבו ליד השולחן עם הדינוזאורים..."</span>
              </li>
            </ul>
          </div>

          {/* Video Validation */}
          <div className="bg-amber-50 rounded-xl p-5 border border-amber-100">
            <h4 className="font-medium text-amber-800 mb-3 flex items-center gap-2">
              <CheckCircle className="w-5 h-5" />
              שלב 2: תיקוף הסרטון (שער כניסה)
            </h4>
            <p className="text-amber-700 mb-3">
              לפני שמנתחים, המערכת בודקת:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="bg-white/60 rounded-lg p-3">
                <div className="font-medium text-amber-800">התאמה לתרחיש</div>
                <div className="text-sm text-amber-600">האם הסרטון מראה מה שביקשנו?</div>
              </div>
              <div className="bg-white/60 rounded-lg p-3">
                <div className="font-medium text-amber-800">זיהוי הילד</div>
                <div className="text-sm text-amber-600">האם הילד בסרטון תואם לפרופיל?</div>
              </div>
            </div>
            <p className="text-amber-600 text-sm mt-3 italic">
              אם התיקוף נכשל, הסרטון לא ינותח והשערות לא יעודכנו.
            </p>
          </div>

          {/* Analysis */}
          <div className="bg-emerald-50 rounded-xl p-5 border border-emerald-100">
            <h4 className="font-medium text-emerald-800 mb-3 flex items-center gap-2">
              <Play className="w-5 h-5" />
              שלב 3: ניתוח תוכן
            </h4>
            <p className="text-emerald-700 mb-3">
              הניתוח מונחה על ידי ההשערה אבל לא מוטה:
            </p>
            <ul className="space-y-2 text-sm text-emerald-600">
              <li className="flex items-start gap-2">
                <span className="text-emerald-400">•</span>
                <span><strong>תצפיות אובייקטיביות:</strong> התנהגויות ספציפיות עם חותמות זמן</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-emerald-400">•</span>
                <span><strong>חוזקות (חובה!):</strong> תמיד מחפשים מה הילד עושה טוב</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-emerald-400">•</span>
                <span><strong>ראיות להשערה:</strong> תומך / סותר / מעורב / לא ברור</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-emerald-400">•</span>
                <span><strong>שאלות חדשות:</strong> מה הסרטון מעלה לחקירה נוספת</span>
              </li>
            </ul>
          </div>

          {/* Confidence Updates */}
          <div className="bg-purple-50 rounded-xl p-5 border border-purple-100">
            <h4 className="font-medium text-purple-800 mb-3 flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              עדכון ודאות מסרטון
            </h4>
            <p className="text-purple-700 mb-3">
              סרטונים משפיעים יותר משיחה רגילה:
            </p>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="bg-emerald-100 rounded-lg p-2 text-center">
                <div className="font-medium text-emerald-700">תומך + ביטחון גבוה</div>
                <div className="text-emerald-600">+15%</div>
              </div>
              <div className="bg-red-100 rounded-lg p-2 text-center">
                <div className="font-medium text-red-700">סותר + ביטחון גבוה</div>
                <div className="text-red-600">-20%</div>
              </div>
            </div>
          </div>

          {/* Video Values */}
          <div className="bg-gray-50 border border-gray-200 rounded-xl p-5">
            <h4 className="font-medium text-gray-800 mb-3">סוגי ערך סרטון</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
              <VideoValueCard
                value="כיול (calibration)"
                description="ההורה אמר 'תמיד' או 'אף פעם' — הסרטון יראה את המציאות"
              />
              <VideoValueCard
                value="שרשרת (chain)"
                description="לראות את הרצף: טריגר → תגובה → תוצאה"
              />
              <VideoValueCard
                value="גילוי (discovery)"
                description="צילום ראשוני להכרות — בסיס ללא השערה ספציפית"
              />
              <VideoValueCard
                value="מסגור מחדש (reframe)"
                description="דאגה של ההורה שעשויה להיות חוזקה במסגור אחר"
              />
            </div>
          </div>
        </div>
      </GuideSection>

      {/* Section: Algorithmic Glossary */}
      <GuideSection
        id="glossary"
        icon={<BookMarked className="w-6 h-6" />}
        title="מילון אלגוריתמי"
        expanded={expandedSections.glossary}
        onToggle={() => toggleSection('glossary')}
      >
        <div className="space-y-6">
          <p>
            איך המערכת "יודעת" להבחין בין סוגי מידע שונים? הנה ההגדרות האלגוריתמיות:
          </p>

          {/* Observation */}
          <GlossaryItem
            term="תצפית (Observation)"
            color="emerald"
            howDetected="LLM קורא את ההודעה ומפעיל כלי 'notice' עם פרטים ספציפיים"
            criteria={[
              "תיאור התנהגות ספציפית (לא הכללה)",
              "יש תחום התפתחותי (מוטורי, רגשי, חושי...)",
              "יש הקשר זמני (מתי זה קורה)",
            ]}
            notThis="'הוא ילד קשה' (הכללה, לא תצפית)"
            thisIs="'כשמגיעים לגן, הוא נצמד לרגל של אמא ולא נכנס לבד' (התנהגות ספציפית עם הקשר)"
          />

          {/* Curiosity */}
          <GlossaryItem
            term="סקרנות (Curiosity)"
            color="amber"
            howDetected="LLM מפעיל כלי 'wonder' עם סוג (גילוי/שאלה/השערה/דפוס)"
            criteria={[
              "יש נושא לחקירה (focus)",
              "יש סוג: discovery/question/hypothesis/pattern",
              "יש 'משיכה' (pull) ראשונית",
            ]}
            notThis="כל שאלה ששואלים (לא כל שאלה היא סקרנות במערכת)"
            thisIs="שאלה או תהייה שהמערכת רוצה לעקוב אחריה לאורך זמן"
          />

          {/* Question vs Hypothesis */}
          <GlossaryItem
            term="שאלה מול השערה"
            color="blue"
            howDetected="ההבדל בפרמטר 'type' של כלי wonder"
            criteria={[
              "שאלה (question): רוצים לדעת עוד — אין תיאוריה",
              "השערה (hypothesis): יש תיאוריה ספציפית לבדיקה",
              "השערה חייבת שדה 'theory' מלא",
              "השערה עם video_appropriate=true מתחילה חקירה אוטומטית",
            ]}
            notThis="שאלה: 'מה עם השינה?' — כללי מדי"
            thisIs="השערה: 'הקושי בשינה קשור לעוררות יתר חושית בסוף היום' — תיאוריה בדיקה"
          />

          {/* Pattern */}
          <GlossaryItem
            term="דפוס (Pattern)"
            color="violet"
            howDetected="נוצר אוטומטית כשסיפור נוגע ב-2+ תחומים"
            criteria={[
              "קשר בין שני תחומים התפתחותיים או יותר",
              "significance של הסיפור ≥ 0.5",
              "לא קיים דפוס דומה כבר",
            ]}
            notThis="'הוא רגיש' — תחום יחיד"
            thisIs="'רגישות שמיעתית → קושי בוויסות → הימנעות חברתית' — שלושה תחומים מחוברים"
          />

          {/* Evidence */}
          <GlossaryItem
            term="ראיה (Evidence)"
            color="purple"
            howDetected="LLM מפעיל כלי 'add_evidence' עם effect"
            criteria={[
              "מקושרת לחקירה פעילה (investigation_id)",
              "יש effect: supports/contradicts/transforms",
              "יש source: conversation או video",
            ]}
            notThis="כל מידע חדש (רק מידע שנוגע לחקירה פעילה)"
            thisIs="מידע שמשנה את הודאות בהשערה שנחקרת כרגע"
          />

          {/* Crystal */}
          <GlossaryItem
            term="קריסטל (Crystal)"
            color="cyan"
            howDetected="נוצר כשמתקיימים תנאי סף (2+ חקירות / 5+ סיפורים / 10+ תצפיות)"
            criteria={[
              "סינתזה של כל ההבנה הנוכחית",
              "נוצר ע״י המודל החזק ביותר",
              "כולל: מהות, דפוסים, המלצות, שאלות פתוחות",
              "יודע מתי הוא מיושן ודורש עדכון",
            ]}
            notThis="דוח או רשימת ממצאים"
            thisIs="פורטרט חי של הילד — מי הוא, לא רק מה הבעיות"
          />

          {/* Pull */}
          <GlossaryItem
            term="משיכה (Pull)"
            color="orange"
            howDetected="מחושבת מחדש בכל תור לפי נוסחה"
            criteria={[
              "base_pull — ערך התחלתי (0-1)",
              "- 0.02 ליום בלי פעילות (דעיכה)",
              "+ עד 0.3 לפערים בתחום (gap boost)",
              "- 0.2 אם ודאות > 70% (דעיכת שביעות רצון)",
            ]}
            notThis="מספר קבוע"
            thisIs="ערך דינמי שמשתנה — סקרנויות ׳רעבות׳ עולות, ׳שבעות׳ יורדות"
          />

          {/* Certainty */}
          <GlossaryItem
            term="ודאות (Certainty)"
            color="indigo"
            howDetected="מתעדכנת עם כל ראיה"
            criteria={[
              "0-100% — כמה בטוחים בסקרנות/השערה",
              "עצמאית מסוג הסקרנות (אפשר גילוי בודאות גבוהה!)",
              "מושפעת מראיות: +10% תומך, -15% סותר, 40% משנה",
            ]}
            notThis="ציון איכות או חשיבות"
            thisIs="כמה ראיות תומכות יש — לא כמה חשוב הנושא"
          />
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

function EvolutionStep({ number, color, title, description, trigger, example, isLast }) {
  const colors = {
    emerald: 'bg-emerald-500',
    blue: 'bg-blue-500',
    purple: 'bg-purple-500',
    violet: 'bg-violet-500',
  };

  const bgColors = {
    emerald: 'bg-emerald-50 border-emerald-100',
    blue: 'bg-blue-50 border-blue-100',
    purple: 'bg-purple-50 border-purple-100',
    violet: 'bg-violet-50 border-violet-100',
  };

  const textColors = {
    emerald: 'text-emerald-700',
    blue: 'text-blue-700',
    purple: 'text-purple-700',
    violet: 'text-violet-700',
  };

  return (
    <div className={`relative pr-16 ${isLast ? '' : 'pb-6'}`}>
      <div className={`absolute right-4 w-6 h-6 rounded-full ${colors[color]} flex items-center justify-center text-white text-xs font-bold`}>
        {number}
      </div>
      <div className={`border rounded-xl p-4 ${bgColors[color]}`}>
        <h4 className={`font-medium ${textColors[color]} mb-1`}>{title}</h4>
        <p className="text-sm text-gray-600 mb-2">{description}</p>
        <div className="bg-white/60 rounded-lg p-2 text-sm mb-2">
          <span className="text-gray-500">🔄 טריגר:</span>
          <span className="text-gray-700 mr-1">{trigger}</span>
        </div>
        <div className="bg-white/60 rounded-lg p-2 text-sm text-gray-600 italic">
          💡 {example}
        </div>
      </div>
    </div>
  );
}

function CrystalComponent({ icon, name, description }) {
  return (
    <div className="flex items-start gap-3 bg-white/60 rounded-lg p-3">
      <span className="text-xl">{icon}</span>
      <div>
        <div className="font-medium text-gray-800">{name}</div>
        <div className="text-sm text-gray-600">{description}</div>
      </div>
    </div>
  );
}

function VideoValueCard({ value, description }) {
  return (
    <div className="bg-white rounded-lg p-3 border border-gray-100">
      <div className="font-medium text-gray-800 mb-1">{value}</div>
      <div className="text-gray-600">{description}</div>
    </div>
  );
}

function GlossaryItem({ term, color, howDetected, criteria, notThis, thisIs }) {
  const colors = {
    emerald: 'border-emerald-200 bg-emerald-50',
    amber: 'border-amber-200 bg-amber-50',
    blue: 'border-blue-200 bg-blue-50',
    violet: 'border-violet-200 bg-violet-50',
    purple: 'border-purple-200 bg-purple-50',
    cyan: 'border-cyan-200 bg-cyan-50',
    orange: 'border-orange-200 bg-orange-50',
    indigo: 'border-indigo-200 bg-indigo-50',
  };

  const headerColors = {
    emerald: 'text-emerald-800',
    amber: 'text-amber-800',
    blue: 'text-blue-800',
    violet: 'text-violet-800',
    purple: 'text-purple-800',
    cyan: 'text-cyan-800',
    orange: 'text-orange-800',
    indigo: 'text-indigo-800',
  };

  const textColors = {
    emerald: 'text-emerald-700',
    amber: 'text-amber-700',
    blue: 'text-blue-700',
    violet: 'text-violet-700',
    purple: 'text-purple-700',
    cyan: 'text-cyan-700',
    orange: 'text-orange-700',
    indigo: 'text-indigo-700',
  };

  return (
    <div className={`rounded-xl p-5 border ${colors[color]}`}>
      <h4 className={`font-semibold ${headerColors[color]} mb-3`}>{term}</h4>

      <div className="mb-3">
        <div className={`text-sm font-medium ${textColors[color]} mb-1`}>איך המערכת מזהה:</div>
        <p className="text-sm text-gray-700">{howDetected}</p>
      </div>

      <div className="mb-3">
        <div className={`text-sm font-medium ${textColors[color]} mb-1`}>קריטריונים:</div>
        <ul className="text-sm text-gray-700 space-y-1">
          {criteria.map((c, i) => (
            <li key={i} className="flex items-start gap-2">
              <span className="text-gray-400 mt-0.5">•</span>
              <span>{c}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
        <div className="bg-red-50 rounded-lg p-2 border border-red-100">
          <div className="text-red-600 font-medium text-xs mb-1">❌ זה לא:</div>
          <p className="text-red-700">{notThis}</p>
        </div>
        <div className="bg-emerald-50 rounded-lg p-2 border border-emerald-100">
          <div className="text-emerald-600 font-medium text-xs mb-1">✓ זה כן:</div>
          <p className="text-emerald-700">{thisIs}</p>
        </div>
      </div>
    </div>
  );
}

function ConversationTurnExample({ turnNumber, parentMessage, chittaThinking, chittaResponse, toolCalls, chittaNote }) {
  return (
    <div className="border border-gray-200 rounded-xl overflow-hidden">
      {/* Turn header */}
      <div className="bg-gray-100 px-4 py-2 border-b border-gray-200">
        <span className="text-sm font-medium text-gray-600">תור {turnNumber}</span>
      </div>

      {/* Parent message */}
      <div className="p-4 bg-blue-50 border-b border-gray-200">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 bg-blue-200 rounded-full flex items-center justify-center text-blue-700 text-sm font-medium">
            👩
          </div>
          <div>
            <div className="text-xs text-blue-600 mb-1">ההורה:</div>
            <p className="text-blue-800">{parentMessage}</p>
          </div>
        </div>
      </div>

      {/* Chitta's thinking - the inner voice */}
      <div className="p-4 bg-amber-50 border-b border-gray-200">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 bg-amber-200 rounded-full flex items-center justify-center text-amber-700 text-sm">
            🧠
          </div>
          <div className="flex-1">
            <div className="text-xs text-amber-600 mb-2">מה צ'יטה חושבת:</div>
            <div className="space-y-2">
              {chittaThinking.map((thought, i) => (
                <p key={i} className="text-amber-800 text-sm italic bg-white/50 rounded-lg px-3 py-2">
                  "{thought}"
                </p>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Tool calls */}
      <div className="p-4 bg-gray-50 border-b border-gray-200">
        <div className="text-xs text-gray-500 mb-2">🔧 כלים שהופעלו:</div>
        <div className="flex flex-wrap gap-2">
          {toolCalls.map((tc, i) => (
            <div key={i} className="bg-white rounded-lg px-3 py-1.5 border border-gray-200 text-xs">
              <span className="font-mono text-purple-600">{tc.tool}</span>
              <span className="text-gray-400 mx-1">:</span>
              <span className="text-gray-600">{tc.content}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Chitta's response */}
      <div className="p-4 bg-emerald-50">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 bg-emerald-200 rounded-full flex items-center justify-center text-emerald-700 text-sm">
            🌱
          </div>
          <div>
            <div className="text-xs text-emerald-600 mb-1">תגובת צ'יטה:</div>
            <p className="text-emerald-800">{chittaResponse}</p>
          </div>
        </div>
      </div>

      {/* Expert note */}
      {chittaNote && (
        <div className="px-4 py-3 bg-violet-50 border-t border-violet-100">
          <p className="text-sm text-violet-700">
            <span className="font-medium">💡 הערה למומחה:</span> {chittaNote}
          </p>
        </div>
      )}
    </div>
  );
}
