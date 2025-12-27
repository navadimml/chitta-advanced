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
    v2architecture: true,  // V2: New section explaining architecture changes
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

          {/* Fullness - V2 */}
          <TermCard
            icon={<TrendingUp className="w-6 h-6 text-emerald-600" />}
            term="מלאות"
            english="Fullness"
            definition="עד כמה למדנו על שאלה או גילוי. משמש עבור סקרנויות קולטות (גילוי ושאלה). מספר בין 0% ל-100%."
            example="מלאות של 60% אומרת שיש לנו כבר תמונה סבירה, אבל עדיין יש מה לגלות"
            scale={[
              { value: '0-30%', label: 'התחלתי', color: 'red' },
              { value: '31-60%', label: 'בתהליך', color: 'amber' },
              { value: '61-85%', label: 'מתמלא', color: 'blue' },
              { value: '86-100%', label: 'מלא', color: 'emerald' },
            ]}
          />

          {/* Confidence - V2 */}
          <TermCard
            icon={<Target className="w-6 h-6 text-purple-600" />}
            term="ביטחון"
            english="Confidence"
            definition="עד כמה אנחנו בטוחים בהשערה או דפוס. משמש עבור סקרנויות קובעות (השערה ודפוס). מספר בין 0% ל-100%."
            example="ביטחון של 75% אומר שיש בסיס חזק להשערה, אבל עדיין יש מקום לספק"
            scale={[
              { value: '0-30%', label: 'חלש', color: 'red' },
              { value: '31-60%', label: 'בינוני', color: 'amber' },
              { value: '61-85%', label: 'טוב', color: 'blue' },
              { value: '86-100%', label: 'גבוה', color: 'emerald' },
            ]}
          />

          {/* Hypothesis - V2 */}
          <TermCard
            icon={<Lightbulb className="w-6 h-6 text-purple-600" />}
            term="השערה"
            english="Hypothesis"
            definition="סקרנות קובעת עם תיאוריה ספציפית לבדיקה. יש לה 'ביטחון' שעולה/יורד לפי ראיות, וסטטוס (חלשה → נבדקת → נתמכת/אושרה/נדחתה)."
            example="השערה: 'הקושי בהרכבת פאזלים קשור לתכנון מוטורי' — ביטחון 55%, סטטוס: נבדקת"
            note="השערות יכולות להתחיל חקירה (Investigation) שמנהלת את תהליך בדיקת הסרטון"
          />

          {/* Pattern - V2 */}
          <TermCard
            icon={<Sparkles className="w-6 h-6 text-violet-600" />}
            term="דפוס"
            english="Pattern"
            definition="סקרנות קובעת שמחברת בין מספר תחומים או השערות. יש לו 'ביטחון' וסטטוס (זמני → נתמך → אושר/נדחה). דפוס יכול להיות תלוי בהשערות שממנו הוא צמח."
            example="דפוס: 'רגישות חושית + צורך בשליטה = קושי במעברים' — ביטחון 60%, נתמך"
            note="כשהשערה שתמכה בדפוס נדחית, הדפוס מתעדכן או מתפרק (cascade)"
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
          <p className="mb-4">
            לא כל סקרנות היא אותו דבר. יש הבדל בין "מי הילד הזה?" לבין "בוא נבדוק אם X נכון".
          </p>

          {/* V2: Two Natures */}
          <div className="bg-gradient-to-l from-emerald-50 to-purple-50 rounded-xl p-5 border border-gray-200 mb-6">
            <h4 className="font-semibold text-gray-800 mb-3">שני סוגי סקרנות</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-white rounded-lg p-4 border border-emerald-200">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xl">🌊</span>
                  <span className="font-medium text-emerald-800">קולטות (Receptive)</span>
                </div>
                <p className="text-sm text-emerald-700 mb-2">גילוי ושאלה — פתוחות לקליטת מידע</p>
                <div className="bg-emerald-50 rounded-lg p-2 text-xs">
                  <span className="font-medium">מדד: מלאות (Fullness)</span>
                  <p className="text-emerald-600">כמה למדנו? 0% = ריק, 100% = מלא</p>
                </div>
              </div>
              <div className="bg-white rounded-lg p-4 border border-purple-200">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xl">🎯</span>
                  <span className="font-medium text-purple-800">קובעות (Assertive)</span>
                </div>
                <p className="text-sm text-purple-700 mb-2">השערה ודפוס — יש להן טענה לבדיקה</p>
                <div className="bg-purple-50 rounded-lg p-2 text-xs">
                  <span className="font-medium">מדד: ביטחון (Confidence)</span>
                  <p className="text-purple-600">כמה בטוחים? 0% = חלש, 100% = מאושר</p>
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <CuriosityTypeCard
              type="גילוי"
              english="Discovery"
              color="emerald"
              icon="🔍"
              description="קליטה פתוחה, ללא הנחות מוקדמות"
              question="מי הילד הזה? מה מאפיין אותו?"
              example="'איך הוא ניגש לפעילויות חדשות?' — מלאות 30%"
            />

            <CuriosityTypeCard
              type="שאלה"
              english="Question"
              color="blue"
              icon="❓"
              description="העמקה בנושא שעלה"
              question="רוצים לדעת עוד על משהו שעלה"
              example="'מה קורה כשהוא צריך לחכות?' — מלאות 45%"
            />

            <CuriosityTypeCard
              type="השערה"
              english="Hypothesis"
              color="purple"
              icon="🎯"
              description="תיאוריה לבדיקה עם סטטוס: חלשה → נבדקת → נתמכת/אושרה/נדחתה"
              question="יש לנו רעיון מה קורה — בוא נבדוק"
              example="'הקושי החברתי נובע מקושי בקריאת רמזים' — ביטחון 55%, נבדקת"
            />

            <CuriosityTypeCard
              type="דפוס"
              english="Pattern"
              color="violet"
              icon="🧩"
              description="חיבור נקודות בין תחומים, יכול להיות תלוי בהשערות"
              question="האם יש קשר בין X ל-Y?"
              example="'הרגישות החושית והויסות הרגשי קשורים' — ביטחון 60%, נתמך"
            />
          </div>

          <div className="bg-purple-50 border border-purple-100 rounded-xl p-4 mt-6">
            <p className="text-purple-800">
              <strong>שימו לב:</strong> סוג הסקרנות והמדד שלה (מלאות/ביטחון) הם עצמאיים.
              אפשר שתהיה השערה עם ביטחון נמוך (30%) — כי היא חדשה ועדיין לא נבדקה,
              או גילוי עם מלאות גבוהה (80%) — כי למדנו הרבה.
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
          <p className="mb-4">
            ראיות הן מידע חדש שמשפיע על הביטחון של השערה או דפוס.
            יש שלושה סוגים של השפעה:
          </p>

          {/* V2: Evidence Provenance */}
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 mb-6">
            <h4 className="font-medium text-slate-800 mb-2 flex items-center gap-2">
              <FileText className="w-4 h-4" />
              מקור הראיה (Provenance)
            </h4>
            <p className="text-sm text-slate-600 mb-3">
              ב-V2, כל ראיה חייבת לכלול:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
              <div className="bg-white rounded-lg p-2 border border-slate-100">
                <span className="font-medium text-slate-700">source_observation</span>
                <p className="text-slate-500">מה בהודעה הוביל לראיה הזו</p>
              </div>
              <div className="bg-white rounded-lg p-2 border border-slate-100">
                <span className="font-medium text-slate-700">effect_reasoning</span>
                <p className="text-slate-500">למה זה תומך/סותר/משנה</p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <EvidenceCard
              type="תומך"
              english="Supports"
              color="emerald"
              icon={<CheckCircle className="w-6 h-6" />}
              effect="מעלה את הביטחון"
              description="הראיה מחזקת את ההשערה — ה-LLM מעריך את ההשפעה"
              example="'שמענו שגם בגן הוא מכסה אוזניים ברעש' — תומך בהשערת הרגישות השמיעתית"
            />

            <EvidenceCard
              type="סותר"
              english="Contradicts"
              color="red"
              icon={<XCircle className="w-6 h-6" />}
              effect="מוריד את הביטחון"
              description="הראיה מערערת על ההשערה — ה-LLM מעריך את ההשפעה"
              example="'בהופעה של הגן הוא ישב בשקט למרות הרעש' — סותר חלקית את הרגישות"
            />

            <EvidenceCard
              type="משנה"
              english="Transforms"
              color="amber"
              icon={<RefreshCw className="w-6 h-6" />}
              effect="משנה את ההבנה"
              description="הראיה מחדדת או משנה את התיאוריה לכיוון חדש"
              example="'הבעיה היא לא רעש אלא רעש בלתי צפוי' — מחדד את ההשערה"
            />
          </div>

          {/* V2: Video Evidence */}
          <div className="bg-violet-50 border border-violet-100 rounded-xl p-4 mt-4">
            <h4 className="font-medium text-violet-800 mb-2 flex items-center gap-2">
              <Video className="w-4 h-4" />
              ראיות מסרטון (Video Evidence)
            </h4>
            <p className="text-violet-700 text-sm mb-2">
              ראיות מסרטון מבוססות על צפייה ישירה ולכן ה-LLM נותן להן משקל גבוה יותר
              בהערכת הביטחון. הסרטון מספק מידע אובייקטיבי שלא תלוי בדיווח בלבד.
            </p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-emerald-100 rounded-lg p-2 text-center">
                <span className="text-emerald-700">תומך מסרטון</span>
                <div className="font-bold text-emerald-800">השפעה חזקה יותר</div>
              </div>
              <div className="bg-red-100 rounded-lg p-2 text-center">
                <span className="text-red-700">סותר מסרטון</span>
                <div className="font-bold text-red-800">השפעה חזקה יותר</div>
              </div>
            </div>
          </div>

          <div className="bg-gray-50 border border-gray-100 rounded-xl p-4 mt-4">
            <p className="text-gray-700">
              <strong>איך זה עובד (V2):</strong> ה-LLM מעריך את ההשפעה של כל ראיה
              ומחליט ישירות מה הביטחון החדש. הוא מביא בחשבון את כל ההקשר —
              לא רק הראיה הבודדת, אלא את מכלול הראיות והסיפור הרחב.
              כל החלטה מלווה בהסבר (reasoning) למה הביטחון השתנה.
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
        title="איך ראיות משפיעות על הביטחון"
        expanded={expandedSections.evidenceDeep}
        onToggle={() => toggleSection('evidenceDeep')}
      >
        <div className="space-y-6">
          <p>
            ב-V2, ה-LLM מעריך את ההשפעה של כל ראיה ומחליט ישירות מה הביטחון החדש.
            הוא מביא בחשבון את ההקשר המלא — לא רק הראיה הבודדת, אלא את כל מה שנלמד עד כה.
          </p>

          {/* The Logic */}
          <div className="bg-gray-50 rounded-xl p-5 border border-gray-200">
            <h4 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-blue-600" />
              הלוגיקה (V2) — LLM מחליט
            </h4>

            <div className="space-y-4">
              <div className="flex items-center gap-4 p-3 bg-emerald-50 rounded-lg border border-emerald-100">
                <div className="text-2xl">➕</div>
                <div>
                  <div className="font-medium text-emerald-800">ראיה תומכת (supports)</div>
                  <div className="text-emerald-600 text-sm">ה-LLM מעלה את הביטחון לפי עוצמת הראיה והקשר</div>
                </div>
              </div>

              <div className="flex items-center gap-4 p-3 bg-red-50 rounded-lg border border-red-100">
                <div className="text-2xl">➖</div>
                <div>
                  <div className="font-medium text-red-800">ראיה סותרת (contradicts)</div>
                  <div className="text-red-600 text-sm">ה-LLM מוריד את הביטחון לפי חומרת הסתירה</div>
                </div>
              </div>

              <div className="flex items-center gap-4 p-3 bg-amber-50 rounded-lg border border-amber-100">
                <div className="text-2xl">🔄</div>
                <div>
                  <div className="font-medium text-amber-800">ראיה משנה (transforms)</div>
                  <div className="text-amber-600 text-sm">ה-LLM מחדד את התיאוריה — יכול ליצור השערה חדשה ומדויקת יותר</div>
                </div>
              </div>
            </div>

            <div className="mt-4 bg-blue-50 rounded-lg p-3 border border-blue-100">
              <p className="text-blue-700 text-sm">
                <strong>חשוב:</strong> כל עדכון ביטחון מלווה ב-<code className="bg-blue-100 px-1 rounded">effect_reasoning</code> —
                הסבר למה ה-LLM החליט כך. זה מאפשר שקיפות וביקורת.
              </p>
            </div>
          </div>

          {/* V2: Status Transitions */}
          <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-5">
            <h4 className="font-medium text-indigo-800 mb-3">מעברי סטטוס (V2)</h4>
            <p className="text-indigo-700 text-sm mb-3">
              הביטחון משפיע על הסטטוס של השערות ודפוסים:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              <div className="bg-white rounded-lg p-3 border border-indigo-100">
                <div className="font-medium text-indigo-800 mb-2">השערה (Hypothesis)</div>
                <div className="space-y-1 text-indigo-600">
                  <p>• חלשה (weak): ביטחון {'<'} 25%</p>
                  <p>• נבדקת (testing): ביטחון 25-55%</p>
                  <p>• נתמכת (supported): ביטחון 55-75%</p>
                  <p>• אושרה (confirmed): ביטחון {'>'} 75%</p>
                  <p>• נדחתה (refuted): נסתרה עם ביטחון נמוך</p>
                  <p>• השתנתה (transformed): הבנה שינתה כיוון</p>
                </div>
              </div>
              <div className="bg-white rounded-lg p-3 border border-indigo-100">
                <div className="font-medium text-indigo-800 mb-2">דפוס (Pattern)</div>
                <div className="space-y-1 text-indigo-600">
                  <p>• מתהווה (emerging): ביטחון {'<'} 45%</p>
                  <p>• יציב (solid): ביטחון 45-70%</p>
                  <p>• יסודי (foundational): ביטחון {'>'} 70%</p>
                  <p>• מוטל בספק (questioned): מקורות נחלשו</p>
                  <p>• התפרק (dissolved): הדפוס כבר לא מחזיק</p>
                </div>
              </div>
            </div>
          </div>

          {/* LLM Judgment Principles */}
          <div className="bg-purple-50 border border-purple-100 rounded-xl p-5">
            <h4 className="font-medium text-purple-800 mb-2">עקרונות שיקול הדעת של ה-LLM</h4>
            <p className="text-purple-700 leading-relaxed">
              ה-LLM נוטה לתת משקל גבוה יותר לראיות סותרות — ראיה אחת שמערערת על השערה
              משמעותית יותר ממספר ראיות תומכות קטנות. זה מונע "אישור הטיה" (confirmation bias).
              בנוסף, ראיות מסרטון מקבלות משקל גבוה יותר מדיווחים בשיחה כי הן אובייקטיביות.
            </p>
          </div>

          {/* Example */}
          <div className="bg-blue-50 rounded-xl p-5 border border-blue-100">
            <h4 className="font-medium text-blue-800 mb-3">דוגמה מעשית</h4>
            <div className="space-y-2 text-sm">
              <p className="text-blue-700">השערה: "רגישות שמיעתית גבוהה משפיעה על ויסות"</p>
              <p className="text-blue-700">ביטחון התחלתי: <strong>35%</strong> (סטטוס: נבדקת)</p>
              <div className="border-r-2 border-blue-300 pr-3 mr-2 space-y-1">
                <p className="text-blue-600">• ההורה: "גם בגן הוא מכסה אוזניים" (תומך)</p>
                <p className="text-blue-500 text-xs mr-4">→ LLM: "ראיה נוספת מסביבה אחרת — מעלה ביטחון ל-50%"</p>
                <p className="text-blue-600">• ההורה: "אבל בהופעה ישב בשקט" (סותר)</p>
                <p className="text-blue-500 text-xs mr-4">→ LLM: "סותר את הכלליות — מוריד ל-35%"</p>
                <p className="text-blue-600">• ההורה: "אה, זה רק ברעש פתאומי!" (משנה)</p>
                <p className="text-blue-500 text-xs mr-4">→ LLM: "התיאוריה צריכה לחדד — יוצר השערה חדשה: רגישות לרעשים בלתי צפויים"</p>
              </div>
              <p className="text-blue-700 mt-2">ה-LLM מסביר כל החלטה ב-reasoning — שקיפות מלאה.</p>
            </div>
          </div>

          {/* Video vs Conversation */}
          <div className="bg-violet-50 border border-violet-100 rounded-xl p-4">
            <p className="text-violet-800">
              <strong>סרטונים משפיעים יותר:</strong> ה-LLM נותן משקל גבוה יותר לראיות מסרטון
              כי הן מבוססות על צפייה ישירה ולא רק על דיווח. ראיה מסרטון יכולה לשנות
              את הביטחון יותר מראיה מדיווח — ולכל כיוון.
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

          {/* LLM-driven transitions (V2) */}
          <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-5">
            <h4 className="font-medium text-indigo-800 mb-3">מעברים (V2 — LLM מחליט)</h4>
            <ul className="space-y-2 text-indigo-700">
              <li className="flex items-start gap-2">
                <span className="text-indigo-500 mt-1">•</span>
                <span><strong>שאלה → השערה:</strong> LLM משתמש ב-wonder עם type=hypothesis כשמזהה תיאוריה</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-indigo-500 mt-1">•</span>
                <span><strong>תצפיות → דפוס:</strong> LLM משתמש ב-see_pattern כשמזהה קשר חוצה-סקרנויות</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-indigo-500 mt-1">•</span>
                <span><strong>דעיכה:</strong> רק משיכה (pull) דועכת אוטומטית בזמן — fullness/confidence לא משתנים לבד</span>
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
              מערכת ה"משיכה" (Pull) — V2
            </h4>
            <p className="text-amber-700 mb-4">
              לכל סקרנות יש "משיכה" (pull) — עד כמה היא דורשת תשומת לב כרגע.
              ב-V2, ה-LLM קובע את המשיכה הראשונית, והמערכת רק מחילה דעיכה בזמן.
            </p>

            <div className="space-y-2">
              <div className="flex items-center gap-3 p-2 bg-white/60 rounded-lg">
                <span className="text-lg">🎯</span>
                <div className="text-sm text-amber-700">
                  <strong>LLM קובע:</strong> כשנוצרת סקרנות, ה-LLM מעריך את המשיכה הראשונית (0-1)
                </div>
              </div>
              <div className="flex items-center gap-3 p-2 bg-white/60 rounded-lg">
                <span className="text-lg">⬇️</span>
                <div className="text-sm text-amber-700">
                  <strong>דעיכה בזמן:</strong> המערכת מורידה משיכה אוטומטית עם הזמן בלי פעילות
                </div>
              </div>
              <div className="flex items-center gap-3 p-2 bg-white/60 rounded-lg">
                <span className="text-lg">🔄</span>
                <div className="text-sm text-amber-700">
                  <strong>עדכון:</strong> LLM יכול לעדכן משיכה דרך <code className="bg-amber-100 px-1 rounded text-xs">update_curiosity</code>
                </div>
              </div>
            </div>

            <div className="mt-3 bg-amber-100/50 rounded-lg p-2 text-xs text-amber-700">
              <strong>חשוב:</strong> מלאות/ביטחון לא משפיעים אוטומטית על משיכה.
              רק דעיכה בזמן היא אוטומטית — כל שינוי אחר הוא החלטת LLM.
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
            קודם נבין מה המספרים אומרים, ואז נראה דוגמה חיה.
          </p>

          {/* What Pull Actually Is */}
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-5">
            <h4 className="font-bold text-amber-900 mb-3 flex items-center gap-2">
              <span>🔥</span>
              <span>מה זה בעצם "משיכה" (Pull)? — V2</span>
            </h4>
            <p className="text-amber-800 mb-4">
              משיכה = כמה הסקרנות "דוחקת" לתשומת לב. ב-V2, ה-LLM קובע את הערך הראשוני,
              והמערכת רק מחילה דעיכה בזמן.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div className="bg-white rounded-lg p-3 border border-amber-100">
                <div className="font-medium text-amber-900 mb-2">איך משיכה עובדת ב-V2</div>
                <ul className="space-y-1 text-amber-700">
                  <li>• <strong>LLM קובע:</strong> ערך ראשוני (0-1) כשנוצרת סקרנות</li>
                  <li>• <strong>דעיכה בזמן:</strong> יורדת אוטומטית (~0.01 ליום)</li>
                  <li>• <strong>עדכון:</strong> LLM יכול לשנות דרך update_curiosity</li>
                </ul>
              </div>
              <div className="bg-white rounded-lg p-3 border border-amber-100">
                <div className="font-medium text-amber-900 mb-2">איפה משיכה משפיעה?</div>
                <ul className="space-y-1 text-amber-700">
                  <li>• <strong>פרומפט:</strong> מופיעה כערך ליד כל סקרנות</li>
                  <li>• <strong>סדר:</strong> סקרנויות ממוינות לפי משיכה</li>
                  <li>• <strong>הקשר:</strong> עוזרת ל-LLM להבין מה דורש תשומת לב</li>
                </ul>
              </div>
            </div>
            <div className="mt-4 bg-green-50 rounded-lg p-3 border border-green-200">
              <p className="text-green-800 text-sm">
                <strong>חשוב:</strong> צ'יטה עוקבת אחרי ההורה, לא בוחרת מכנית לפי משיכה.
                משיכה היא הקשר — לא כלל החלטה אוטומטי.
              </p>
            </div>
          </div>

          {/* What Chitta Actually Sees */}
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-5">
            <h4 className="font-bold text-slate-800 mb-3">מה צ'יטה באמת רואה בפרומפט? (V2)</h4>
            <p className="text-slate-600 text-sm mb-3">זה הפורמט האמיתי שה-LLM מקבל:</p>
            <div className="bg-slate-900 text-green-400 font-mono text-xs p-4 rounded-lg overflow-x-auto" dir="ltr">
              <div className="text-slate-400">## WHAT I'M CURIOUS ABOUT</div>
              <br />
              <div className="text-emerald-400">- 🔍 מי הילד הזה? (Discovery) pull=0.6</div>
              <div className="text-slate-500 mr-4">  fullness: 25% | status: growing</div>
              <br />
              <div className="text-blue-400">- ❓ איך יואב מתמודד עם מעברים? (Question) pull=0.7</div>
              <div className="text-slate-500 mr-4">  fullness: 40% | status: partial</div>
              <br />
              <div className="text-purple-400">- 🎯 רגישות חושית משפיעה על ויסות (Hypothesis) pull=0.65</div>
              <div className="text-slate-500 mr-4">  confidence: 55% | status: testing</div>
              <div className="text-slate-500 mr-4">  theory: רגישות חושית גורמת לקושי בוויסות</div>
              <br />
              <div className="text-violet-400">- 🧩 רגישות + שליטה = מעברים קשים (Pattern) pull=0.5</div>
              <div className="text-slate-500 mr-4">  confidence: 45% | status: emerging</div>
            </div>
            <p className="text-slate-500 text-xs mt-2">
              שימו לב: סקרנויות קולטות מציגות fullness, קובעות מציגות confidence.
            </p>
          </div>

          {/* Setup - Enhanced Visual */}
          <div className="bg-gradient-to-l from-slate-100 to-gray-50 rounded-2xl p-5 border border-gray-200 shadow-sm">
            {/* Child Info Header */}
            <div className="flex items-center gap-4 mb-5 pb-4 border-b border-gray-200">
              <div className="w-14 h-14 bg-gradient-to-br from-blue-400 to-indigo-500 rounded-full flex items-center justify-center text-white text-2xl shadow-md">
                👦
              </div>
              <div>
                <h4 className="text-xl font-bold text-gray-800">יואב</h4>
                <p className="text-gray-500">בן 4 | תחילת היכרות</p>
              </div>
              <div className="mr-auto bg-white rounded-lg px-3 py-1.5 border border-gray-200 shadow-sm">
                <span className="text-xs text-gray-400">סקרנויות פתוחות</span>
                <span className="text-lg font-bold text-indigo-600 mr-2">3</span>
              </div>
            </div>

            {/* Curiosities Grid */}
            <div className="space-y-3">
              {/* Curiosity 1 - Question (highest pull) */}
              <div className="bg-white rounded-xl p-4 border-r-4 border-blue-400 shadow-sm">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">❓</span>
                    <span className="text-xs font-medium text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full">שאלה</span>
                  </div>
                  <div className="flex items-center gap-1 text-orange-500">
                    <span className="text-xs">משיכה</span>
                    <span className="font-bold">0.7</span>
                    <span className="text-orange-400">🔥</span>
                  </div>
                </div>
                <p className="text-gray-800 font-medium mb-2">"איך יואב מתמודד עם מעברים?"</p>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-400">מלאות:</span>
                  <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-400 rounded-full" style={{width: '35%'}}></div>
                  </div>
                  <span className="text-xs font-medium text-gray-600">35%</span>
                </div>
              </div>

              {/* Curiosity 2 - Hypothesis */}
              <div className="bg-white rounded-xl p-4 border-r-4 border-purple-400 shadow-sm">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">🎯</span>
                    <span className="text-xs font-medium text-purple-600 bg-purple-50 px-2 py-0.5 rounded-full">השערה</span>
                  </div>
                  <div className="flex items-center gap-1 text-orange-400">
                    <span className="text-xs">משיכה</span>
                    <span className="font-bold">0.6</span>
                  </div>
                </div>
                <p className="text-gray-800 font-medium mb-2">"רגישות חושית משפיעה על ויסות"</p>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-400">ביטחון:</span>
                  <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div className="h-full bg-purple-400 rounded-full" style={{width: '55%'}}></div>
                  </div>
                  <span className="text-xs font-medium text-gray-600">55%</span>
                </div>
              </div>

              {/* Curiosity 3 - Discovery */}
              <div className="bg-white rounded-xl p-4 border-r-4 border-emerald-400 shadow-sm opacity-75">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">🔍</span>
                    <span className="text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">גילוי</span>
                  </div>
                  <div className="flex items-center gap-1 text-gray-400">
                    <span className="text-xs">משיכה</span>
                    <span className="font-bold">0.5</span>
                  </div>
                </div>
                <p className="text-gray-800 font-medium mb-2">"עולם המשחק שלו"</p>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-400">מלאות:</span>
                  <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-400 rounded-full" style={{width: '20%'}}></div>
                  </div>
                  <span className="text-xs font-medium text-gray-600">20%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Turn 1 */}
          <ConversationTurnExample
            turnNumber={1}
            parentMessage="היום היה לנו בוקר קשה. יואב לא רצה להתלבש בשום אופן, צרח שהחולצה 'עוקצת'"
            chittaThinking={[
              "הממ, 'עוקצת'... זה נשמע כמו רגישות טקטילית. זה מחזק את ההשערה שלי על רגישות חושית!",
              "אוסיף את זה כראיה תומכת עם הסבר למה זה תומך.",
              "אני רוצה להבין יותר — האם זה כל הבגדים או ספציפיים? זה יעזור להבין את הדפוס.",
            ]}
            responseThinking="האמא סיפרה על הבוקר הקשה. אעקוב אחרי מה שהיא הביאה — הרגישות לבגדים. אשאל שאלה ממוקדת שתעזור להבין את ההיקף."
            chittaResponse="זה נשמע כמו בוקר מאתגר. כשהוא אומר שהחולצה 'עוקצת' — זה קורה עם בגדים מסוימים? או שזה משתנה?"
            toolCalls={[
              { tool: "notice", content: "תגובה שלילית לטקסטורת בד — מתאר תחושת 'עקיצה'" },
              { tool: "add_evidence", content: "effect=supports, new_confidence=0.65, reasoning: 'ראיה נוספת לרגישות'" },
            ]}
            stateChanges={[
              { entity: "רגישות חושית", field: "ביטחון", from: "55%", to: "65%", direction: "up" },
            ]}
            chittaNote="שימו לב: ה-LLM מחליט על הביטחון החדש (65%) עם reasoning. לא נוסחה קבועה."
          />

          {/* Turn 2 */}
          <ConversationTurnExample
            turnNumber={2}
            parentMessage="כן, יש חולצות שהוא בכלל לא מוכן ללבוש. רק כותנה רכה. ואסור שיהיו תוויות."
            chittaThinking={[
              "עוד אישור חזק! תוויות וטקסטורות — זה קלאסי לרגישות טקטילית.",
              "זו ראיה משמעותית — אעלה את הביטחון משמעותית.",
              "יש לי כבר הבנה טובה על הרגישות. עכשיו אני יכולה לחפש קשרים לתחומים אחרים.",
              "ההתלבשות היא גם סוג של מעבר...",
            ]}
            responseThinking="יש לי כבר הבנה טובה על הרגישות החושית. עכשיו אני יכולה לראות איך זה מתחבר לתחומים אחרים. ההתלבשות היא מעבר — אשאל על מעברים נוספים."
            chittaResponse="כותנה רכה ובלי תוויות — הוא יודע בדיוק מה מתאים לו. ספרי לי, מלבד ההתלבשות — איך הוא עם מעברים אחרים במהלך היום?"
            toolCalls={[
              { tool: "notice", content: "העדפה ברורה לכותנה רכה, רגישות לתוויות" },
              { tool: "add_evidence", content: "effect=supports, new_confidence=0.75, reasoning: 'ראיה חזקה נוספת'" },
            ]}
            stateChanges={[
              { entity: "רגישות חושית", field: "ביטחון", from: "65%", to: "75%", direction: "up" },
              { entity: "רגישות חושית", field: "סטטוס", from: "testing", to: "supported", direction: "up" },
            ]}
            chittaNote="שימו לב: ה-LLM מחליט שביטחון 75% = סטטוס 'supported'. אין נוסחה אוטומטית — ה-LLM שוקל את כל ההקשר."
          />

          {/* Turn 3 */}
          <ConversationTurnExample
            turnNumber={3}
            parentMessage="מעברים? תראי, יציאה מהבית זה תמיד דרמה. אבל דווקא כשאנחנו בגן, הוא נפרד ממני בקלות!"
            chittaThinking={[
              "רגע רגע! זה מעניין מאוד!",
              "הנחתי שהבעיה היא 'מעברים בכלל', אבל המידע הזה משנה את ההבנה.",
              "הבעיה היא ביציאה מהבית, לא בפרידה. זה יותר ספציפי!",
              "המידע הזה מחדד את השאלה — אני צריכה לפתוח סקרנות יותר מדויקת.",
            ]}
            responseThinking="זו תובנה חשובה של האמא. אחזור על ההבחנה שלה (לוודא שהבנתי נכון) ואשאל מה היא חושבת שקורה — היא מכירה את יואב הכי טוב."
            chittaResponse="זה ממש מעניין! אז בגן, כשהוא כבר שם, הפרידה קלה. הקושי הוא דווקא ברגע היציאה מהבית. מה את חושבת שקורה ברגע הזה?"
            toolCalls={[
              { tool: "notice", content: "פרידה קלה בגן, קושי ביציאה מהבית — הבחנה חשובה" },
              { tool: "wonder", content: "type=question, focus='יציאה מסביבה מוכרת', pull=0.8" },
            ]}
            stateChanges={[
              { entity: "מעברים (כללי)", field: "מלאות", from: "35%", to: "50%", direction: "up", note: "למדנו יותר" },
              { entity: "סקרנות חדשה", field: "focus", from: "", to: "יציאה מסביבה מוכרת", direction: "new" },
            ]}
            chittaNote="הנה רגע קריטי: כשמידע חדש מחדד את ההבנה, צ'יטה פותחת סקרנות חדשה ומדויקת יותר. הישנה נשארת עם מלאות גבוהה יותר."
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
            ]}
            responseThinking="האמא הגיעה לתובנה בעצמה! אני אחזק את זה — עכשיו אני רואה דפוס שמחבר בין ההשערות."
            chittaResponse="את מתארת משהו חשוב מאוד. יואב צריך לדעת מה לצפות — גם בבגדים וגם בסביבה. כשהוא מרגיש בשליטה, הוא מסתדר יפה."
            toolCalls={[
              { tool: "notice", content: "צורך בשליטה ובציפיות ברורות — חוצה תחומים" },
              { tool: "see_pattern", content: "connects: [רגישות חושית, יציאה מבית], confidence=0.45" },
            ]}
            stateChanges={[
              { entity: "דפוס חדש!", field: "סוג", from: "", to: "pattern", direction: "pattern" },
              { entity: "דפוס", field: "ביטחון", from: "", to: "45% (emerging)", direction: "new" },
              { entity: "דפוס", field: "connects", from: "", to: "חושי + רגשי + התנהגותי", direction: "new" },
            ]}
            chittaNote="כאן נוצר דפוס עם see_pattern! ה-LLM מחבר בין סקרנויות קיימות ליצירת תובנה חדשה."
          />

          {/* Summary */}
          <div className="bg-gradient-to-l from-indigo-50 to-purple-50 rounded-xl p-5 border border-indigo-100">
            <h4 className="font-medium text-indigo-800 mb-3">מה למדנו מהדוגמה? (V2)</h4>
            <ul className="space-y-2 text-indigo-700">
              <li className="flex items-start gap-2">
                <span className="text-indigo-400 mt-1">✓</span>
                <span><strong>עקיבה אחרי ההורה:</strong> צ'יטה עוקבת אחרי מה שההורה מביא, לא בוחרת מכנית</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-indigo-400 mt-1">✓</span>
                <span><strong>LLM מעריך ראיות:</strong> ה-LLM מחליט על הביטחון החדש עם reasoning — לא נוסחה קבועה</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-indigo-400 mt-1">✓</span>
                <span><strong>שני סוגים:</strong> שאלות/גילויים משתמשות במלאות, השערות/דפוסים משתמשים בביטחון</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-indigo-400 mt-1">✓</span>
                <span><strong>כלים ייעודיים:</strong> notice, wonder, add_evidence, see_pattern — כל אחד עם תפקיד</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-indigo-400 mt-1">✓</span>
                <span><strong>דפוסים מתגלים:</strong> כשמספיק נקודות מתחברות, ה-LLM משתמש ב-see_pattern</span>
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
                description="התאמה לאיש מקצוע עם התמחות ספציפית שמתאימה לילד"
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

      {/* Section: V2 Architecture */}
      <GuideSection
        id="v2architecture"
        icon={<Layers className="w-6 h-6" />}
        title="ארכיטקטורת V2 — מה חדש"
        expanded={expandedSections.v2architecture}
        onToggle={() => toggleSection('v2architecture')}
      >
        <div className="space-y-6">
          <p>
            גרסה 2 של מערכת הסקרנות מביאה שינויים משמעותיים באופן שבו צ'יטה
            עוקבת אחרי מידע, בונה הבנה, ומתקנת את עצמה.
          </p>

          {/* V2 Tools */}
          <div className="bg-violet-50 border border-violet-100 rounded-xl p-5">
            <h4 className="font-medium text-violet-800 mb-3 flex items-center gap-2">
              <Search className="w-5 h-5" />
              הכלים של ה-LLM (V2 Tools)
            </h4>
            <p className="text-violet-700 text-sm mb-3">
              ב-V2, ל-LLM יש כלים ייעודיים לכל פעולה:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
              <div className="bg-white rounded-lg p-2 border border-violet-100">
                <span className="font-medium text-violet-700">notice</span>
                <p className="text-violet-500">רישום תצפית עם תחום</p>
              </div>
              <div className="bg-white rounded-lg p-2 border border-violet-100">
                <span className="font-medium text-violet-700">wonder</span>
                <p className="text-violet-500">יצירת/עדכון סקרנות</p>
              </div>
              <div className="bg-white rounded-lg p-2 border border-violet-100">
                <span className="font-medium text-violet-700">add_evidence</span>
                <p className="text-violet-500">הוספת ראיה להשערה</p>
              </div>
              <div className="bg-white rounded-lg p-2 border border-violet-100">
                <span className="font-medium text-violet-700">see_pattern</span>
                <p className="text-violet-500">זיהוי דפוס חוצה-סקרנויות</p>
              </div>
              <div className="bg-white rounded-lg p-2 border border-violet-100">
                <span className="font-medium text-violet-700">update_curiosity</span>
                <p className="text-violet-500">הערכה מחדש של סקרנות</p>
              </div>
            </div>
          </div>

          {/* Event Sourcing */}
          <div className="bg-blue-50 border border-blue-100 rounded-xl p-5">
            <h4 className="font-medium text-blue-800 mb-3 flex items-center gap-2">
              <Clock className="w-5 h-5" />
              מעקב אירועים (Event Sourcing)
            </h4>
            <p className="text-blue-700 text-sm mb-3">
              כל שינוי בסקרנות נשמר כאירוע — אפשר לעקוב אחרי ההיסטוריה המלאה.
            </p>
            <div className="bg-white rounded-lg p-3 border border-blue-100 text-xs font-mono">
              <div className="text-blue-600">CuriosityEvent:</div>
              <div className="text-blue-400 mr-4">• created_at: 2024-01-15 10:30</div>
              <div className="text-blue-400 mr-4">• event_type: confidence_changed</div>
              <div className="text-blue-400 mr-4">• changes: [{'{'}field: confidence, old: 0.5, new: 0.6{'}'}]</div>
              <div className="text-blue-400 mr-4">• trigger: evidence_added</div>
            </div>
          </div>

          {/* Provenance */}
          <div className="bg-amber-50 border border-amber-100 rounded-xl p-5">
            <h4 className="font-medium text-amber-800 mb-3 flex items-center gap-2">
              <FileText className="w-5 h-5" />
              מקור (Provenance)
            </h4>
            <p className="text-amber-700 text-sm mb-3">
              כל פעולה חייבת לכלול הסבר למה היא נעשתה — לשקיפות ותיקון.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
              <div className="bg-white rounded-lg p-2 border border-amber-100">
                <span className="font-medium text-amber-700">assessment_reasoning</span>
                <p className="text-amber-500">למה ה-LLM החליט כך</p>
              </div>
              <div className="bg-white rounded-lg p-2 border border-amber-100">
                <span className="font-medium text-amber-700">source_observation</span>
                <p className="text-amber-500">מה בהודעה הוביל לזה</p>
              </div>
            </div>
          </div>

          {/* Cascades */}
          <div className="bg-red-50 border border-red-100 rounded-xl p-5">
            <h4 className="font-medium text-red-800 mb-3 flex items-center gap-2">
              <GitBranch className="w-5 h-5" />
              מפלים (Cascades)
            </h4>
            <p className="text-red-700 text-sm mb-3">
              כשהשערה נדחית או אושרה, זה משפיע על דפוסים שתלויים בה.
            </p>
            <div className="space-y-2 text-xs">
              <div className="flex items-center gap-2 bg-white rounded-lg p-2 border border-red-100">
                <span className="text-red-500">🔴</span>
                <span className="text-red-700">השערה נדחתה → דפוסים שתלויים בה מתפרקים או מתעדכנים</span>
              </div>
              <div className="flex items-center gap-2 bg-white rounded-lg p-2 border border-emerald-100">
                <span className="text-emerald-500">🟢</span>
                <span className="text-emerald-700">השערה אושרה → דפוסים שתלויים בה מתחזקים</span>
              </div>
              <div className="flex items-center gap-2 bg-white rounded-lg p-2 border border-blue-100">
                <span className="text-blue-500">🔵</span>
                <span className="text-blue-700">דפוס אושר/נדחה → קריסטל מתעדכן אוטומטית</span>
              </div>
            </div>
          </div>

          {/* Lineage */}
          <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-5">
            <h4 className="font-medium text-emerald-800 mb-3 flex items-center gap-2">
              <GitBranch className="w-5 h-5" />
              שושלת (Lineage)
            </h4>
            <p className="text-emerald-700 text-sm mb-3">
              סקרנויות יכולות לצמוח אחת מהשנייה — שאלה הופכת להשערה, השערות מתחברות לדפוס.
            </p>
            <div className="bg-white rounded-lg p-3 border border-emerald-100">
              <div className="flex items-center gap-2 text-sm">
                <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded">שאלה</span>
                <span className="text-emerald-400">→</span>
                <span className="bg-purple-100 text-purple-700 px-2 py-1 rounded">השערה</span>
                <span className="text-emerald-400">→</span>
                <span className="bg-violet-100 text-violet-700 px-2 py-1 rounded">דפוס</span>
              </div>
              <p className="text-xs text-emerald-600 mt-2">
                כל צעד שומר את ה-emerges_from וה-source_hypotheses לתיעוד מלא
              </p>
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
            howDetected="LLM מפעיל כלי 'see_pattern' כשמזהה קשר חוצה-סקרנויות"
            criteria={[
              "קשר בין שתיים או יותר סקרנויות/השערות קיימות",
              "LLM מספק reasoning למה זה דפוס",
              "יש לו confidence ו-status משלו (emerging/solid/foundational)",
            ]}
            notThis="'הוא רגיש' — תחום יחיד, לא חיבור בין סקרנויות"
            thisIs="'רגישות שמיעתית → קושי בוויסות → הימנעות חברתית' — חיבור בין השערות"
          />

          {/* Evidence */}
          <GlossaryItem
            term="ראיה (Evidence)"
            color="purple"
            belongsTo="שייכת להשערה (Hypothesis) קיימת"
            howDetected="LLM מפעיל כלי 'add_evidence' עם effect ו-new_confidence"
            criteria={[
              "מקושרת להשערה קיימת (curiosity_id)",
              "יש effect: supports/contradicts/transforms",
              "LLM קובע new_confidence עם effect_reasoning",
            ]}
            notThis="כל מידע חדש (רק מידע שנוגע להשערה)"
            thisIs="מידע שה-LLM מעריך שמשנה את הביטחון בהשערה"
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
            belongsTo="תכונה של סקרנות"
            howDetected="LLM קובע ערך ראשוני, המערכת רק מחילה דעיכה בזמן"
            criteria={[
              "LLM קובע pull ראשוני (0-1) כשנוצרת סקרנות",
              "המערכת מחילה דעיכה בזמן (~0.01 ליום)",
              "LLM יכול לעדכן דרך update_curiosity",
              "אין שינוי אוטומטי לפי fullness/confidence",
            ]}
            notThis="נוסחה אוטומטית עם gap boost וכו'"
            thisIs="ערך ש-LLM קובע ורק דעיכה בזמן משנה אוטומטית"
          />

          {/* Fullness - V2 */}
          <GlossaryItem
            term="מלאות (Fullness)"
            color="emerald"
            belongsTo="תכונה של סקרנויות קולטות (גילוי, שאלה)"
            howDetected="LLM קובע עם wonder או update_curiosity"
            criteria={[
              "0-100% — כמה למדנו על הנושא",
              "משמשת עבור Discovery ו-Question בלבד",
              "LLM מעריך כמה מלאה התמונה ומעדכן עם reasoning",
            ]}
            notThis="כמה בטוחים (זה ביטחון, לא מלאות)"
            thisIs="הערכת LLM לגבי כמה מידע יש לנו — 0% = ריק, 100% = תמונה מלאה"
          />

          {/* Confidence - V2 */}
          <GlossaryItem
            term="ביטחון (Confidence)"
            color="purple"
            belongsTo="תכונה של סקרנויות קובעות (השערה, דפוס)"
            howDetected="LLM קובע עם add_evidence או update_curiosity"
            criteria={[
              "0-100% — כמה בטוחים בהשערה/דפוס",
              "משמש עבור Hypothesis ו-Pattern בלבד",
              "LLM קובע את הערך החדש עם reasoning — לא נוסחה קבועה",
              "משפיע על סטטוס: weak → testing → supported → confirmed",
            ]}
            notThis="כמה מידע יש (זה מלאות, לא ביטחון)"
            thisIs="הערכת LLM לגבי חוזק ההשערה לאור כל הראיות"
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

function GlossaryItem({ term, color, belongsTo, howDetected, criteria, notThis, thisIs }) {
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
      <h4 className={`font-semibold ${headerColors[color]} mb-1`}>{term}</h4>
      {belongsTo && (
        <div className="text-xs text-gray-500 mb-3 italic">📎 {belongsTo}</div>
      )}

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

function ConversationTurnExample({ turnNumber, parentMessage, chittaThinking, responseThinking, chittaResponse, toolCalls, stateChanges, chittaNote }) {
  return (
    <div className="border border-gray-200 rounded-xl overflow-hidden shadow-sm">
      {/* Turn header */}
      <div className="bg-gradient-to-l from-gray-100 to-gray-50 px-4 py-2 border-b border-gray-200">
        <span className="text-sm font-bold text-gray-700">תור {turnNumber}</span>
      </div>

      {/* Parent message */}
      <div className="p-4 bg-blue-50 border-b border-gray-200">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-300 to-blue-400 rounded-full flex items-center justify-center text-white text-lg shadow-sm">
            👩
          </div>
          <div className="flex-1">
            <div className="text-xs font-medium text-blue-600 mb-1">ההורה:</div>
            <p className="text-blue-900 leading-relaxed">{parentMessage}</p>
          </div>
        </div>
      </div>

      {/* Chitta's thinking - the inner voice */}
      <div className="p-4 bg-amber-50 border-b border-gray-200">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-amber-300 to-orange-400 rounded-full flex items-center justify-center text-white text-lg shadow-sm">
            🧠
          </div>
          <div className="flex-1">
            <div className="text-xs font-medium text-amber-700 mb-3">מה צ'יטה חושבת:</div>
            <div className="space-y-2">
              {chittaThinking.map((thought, i) => (
                <p key={i} className="text-amber-900 text-sm italic bg-white/60 rounded-lg px-3 py-2 border-r-2 border-amber-300">
                  "{thought}"
                </p>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Tool calls */}
      <div className="p-4 bg-gray-50 border-b border-gray-200">
        <div className="text-xs font-medium text-gray-600 mb-2">🔧 כלים שהופעלו:</div>
        <div className="flex flex-wrap gap-2">
          {toolCalls.map((tc, i) => (
            <div key={i} className="bg-white rounded-lg px-3 py-1.5 border border-gray-200 text-xs shadow-sm">
              <span className="font-mono font-medium text-purple-600">{tc.tool}</span>
              <span className="text-gray-300 mx-1">|</span>
              <span className="text-gray-600">{tc.content}</span>
            </div>
          ))}
        </div>
      </div>

      {/* State Changes - Visual */}
      {stateChanges && stateChanges.length > 0 && (
        <div className="p-4 bg-gradient-to-l from-indigo-50 to-purple-50 border-b border-gray-200">
          <div className="text-xs font-medium text-indigo-700 mb-3">📊 שינויים במצב:</div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {stateChanges.map((change, i) => (
              <div key={i} className={`rounded-lg px-3 py-2 text-xs flex items-center gap-2 ${
                change.direction === 'up' ? 'bg-emerald-100 border border-emerald-200' :
                change.direction === 'down' ? 'bg-orange-100 border border-orange-200' :
                change.direction === 'reset' ? 'bg-amber-100 border border-amber-200' :
                change.direction === 'transform' ? 'bg-purple-100 border border-purple-200' :
                change.direction === 'new' ? 'bg-blue-100 border border-blue-200' :
                change.direction === 'pattern' ? 'bg-violet-100 border border-violet-200' :
                change.direction === 'video' ? 'bg-pink-100 border border-pink-200' :
                'bg-gray-100 border border-gray-200'
              }`}>
                <span className={`text-lg ${
                  change.direction === 'up' ? '' :
                  change.direction === 'down' ? '' :
                  change.direction === 'reset' ? '' :
                  change.direction === 'transform' ? '' :
                  change.direction === 'new' ? '' :
                  change.direction === 'pattern' ? '' :
                  change.direction === 'video' ? '' : ''
                }`}>
                  {change.direction === 'up' ? '📈' :
                   change.direction === 'down' ? '📉' :
                   change.direction === 'reset' ? '🔄' :
                   change.direction === 'transform' ? '✨' :
                   change.direction === 'new' ? '➕' :
                   change.direction === 'pattern' ? '🧩' :
                   change.direction === 'video' ? '🎬' : '•'}
                </span>
                <div className="flex-1">
                  <span className="font-medium text-gray-800">{change.entity}</span>
                  {change.field && <span className="text-gray-500"> • {change.field}</span>}
                  {change.from && (
                    <span className="text-gray-400 mx-1">
                      {change.from} ←
                    </span>
                  )}
                  <span className={`font-bold ${
                    change.direction === 'up' ? 'text-emerald-700' :
                    change.direction === 'down' ? 'text-orange-700' :
                    change.direction === 'reset' ? 'text-amber-700' :
                    change.direction === 'transform' ? 'text-purple-700' :
                    change.direction === 'new' ? 'text-blue-700' :
                    change.direction === 'pattern' ? 'text-violet-700' :
                    change.direction === 'video' ? 'text-pink-700' :
                    'text-gray-700'
                  }`}>{change.to}</span>
                  {change.note && <span className="text-gray-400 mr-1">({change.note})</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Response thinking - bridge to response */}
      {responseThinking && (
        <div className="p-4 bg-teal-50 border-b border-gray-200">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-teal-200 rounded-full flex items-center justify-center text-teal-700 text-sm">
              💭
            </div>
            <div className="flex-1">
              <div className="text-xs font-medium text-teal-700 mb-1">איך להגיב:</div>
              <p className="text-teal-800 text-sm italic">"{responseThinking}"</p>
            </div>
          </div>
        </div>
      )}

      {/* Chitta's response */}
      <div className="p-4 bg-emerald-50">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-emerald-300 to-green-400 rounded-full flex items-center justify-center text-white text-lg shadow-sm">
            🌱
          </div>
          <div className="flex-1">
            <div className="text-xs font-medium text-emerald-700 mb-1">תגובת צ'יטה:</div>
            <p className="text-emerald-900 leading-relaxed">{chittaResponse}</p>
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
