// Mock API Service - Simulates backend communication
// In production, this would make real API calls to the backend

const SCENARIOS = {
  interview: {
    name: 'ריאיון התחלתי',
    masterState: {
      journey_stage: 'interview',
      child: { name: 'יוני', age: 3.5 },
      progress: { interview: 45, videos: 0 },
      active_artifacts: [],
      completed_milestones: []
    },
    messages: [
      { sender: 'chitta', text: 'היי! אני צ\'יטה 💙\n\nכיף שהגעת! אשמח להכיר את הילד שלך ולהבין איך אפשר לעזור.\n\nמה השם והגיל?', delay: 0 },
      { sender: 'user', text: 'השם שלו יוני', delay: 3000 },
      { sender: 'chitta', text: 'נעים להכיר את יוני! 😊 בן כמה הוא?', delay: 4000 },
      { sender: 'user', text: 'הוא בן 3 וחצי', delay: 5500 },
      { sender: 'chitta', text: 'תודה! יוני בגיל נפלא של גילויים. מה גרם לך לפנות אליי? מה עובר לך בראש לגבי יוני?', delay: 6500 },
    ],
    contextCards: [
      { icon: 'MessageCircle', title: 'מתנהל ראיון', subtitle: 'התקדמות: מידע בסיסי', status: 'processing' },
      { icon: 'CheckCircle', title: 'נושאים שנדונו', subtitle: 'גיל, דיבור, תקשורת', status: 'progress' },
      { icon: 'Clock', title: 'זמן משוער', subtitle: 'עוד 10-15 דקות', status: 'pending' },
    ],
    suggestions: [
      { icon: 'MessageCircle', text: 'אני מודאגת מהדיבור שלו', color: 'bg-blue-500' },
      { icon: 'Users', text: 'הוא מתקשה עם ילדים אחרים', color: 'bg-purple-500' },
      { icon: 'Heart', text: 'יש לי שאלות כלליות', color: 'bg-pink-500' },
      { icon: 'FileUp', text: 'יש לי אבחון קודם להעלות', color: 'bg-orange-500' },
    ]
  },
  
  consultation: {
    name: 'התייעצות',
    masterState: {
      journey_stage: 'consultation',
      child: { name: 'יוני', age: 3.5 },
      progress: { interview: 100, videos: 0 },
      active_artifacts: [],
      completed_milestones: ['interview']
    },
    messages: [
      { sender: 'user', text: 'אני רוצה להתייעץ איתך', delay: 0 },
      { sender: 'chitta', text: 'בטח! אני כאן בשבילך 💙', delay: 800 },
      { sender: 'chitta', text: 'ספרי לי, מה מעסיק אותך? אני כאן כדי לעזור לך להבין, לתמוך, ולהכווין.', delay: 1800 },
    ],
    contextCards: [
      { icon: 'Brain', title: 'מצב התייעצות', subtitle: 'שאלי כל שאלה', status: 'processing', action: 'consultDoc' },
      { icon: 'FileText', title: 'העלאת מסמכים', subtitle: 'אבחונים, סיכומים, דוחות', status: 'action', action: 'uploadDoc' },
      { icon: 'Book', title: 'יומן יוני', subtitle: 'הערות והתבוננויות', status: 'action', action: 'journal' },
    ],
    suggestions: [
      { icon: 'HelpCircle', text: 'איך אני יודעת אם זה חמור?', color: 'bg-indigo-500' },
      { icon: 'Users', text: 'מתי כדאי לפנות למומחה?', color: 'bg-teal-500' },
      { icon: 'Heart', text: 'איך אני מסבירה זאת למשפחה?', color: 'bg-rose-500' },
      { icon: 'Lightbulb', text: 'מה אני יכולה לעשות בבית?', color: 'bg-amber-500' },
    ]
  },

  documentUpload: {
    name: 'העלאת מסמך',
    masterState: {
      journey_stage: 'document_upload',
      child: { name: 'יוני', age: 3.5 },
      progress: { interview: 100, videos: 0, documents: 0 },
      active_artifacts: [],
      completed_milestones: ['interview']
    },
    messages: [
      { sender: 'user', text: 'יש לי סיכום אבחון מלפני שנה', delay: 0 },
      { sender: 'chitta', text: 'מעולה! זה יעזור לי להבין את התמונה המלאה 📄', delay: 800 },
      { sender: 'chitta', text: 'את יכולה להעלות את המסמך, ואני אקרא ואנתח אותו. המידע יישמר בצורה מאובטחת ומוצפנת.', delay: 2000 },
      { sender: 'chitta', text: 'אני אסכם את העיקר ואשלב את הממצאים עם המידע שכבר יש לי על יוני.', delay: 3500 },
    ],
    contextCards: [
      { icon: 'FileUp', title: 'העלאת מסמך', subtitle: 'PDF, תמונה, או וורד', status: 'action', action: 'uploadDoc' },
      { icon: 'FileText', title: 'מסמכים קיימים', subtitle: 'צפייה במסמכים שהועלו', status: 'action', action: 'viewDocs' },
      { icon: 'Shield', title: 'אבטחה מלאה', subtitle: 'כל המסמכים מוצפנים', status: 'completed' },
    ],
    suggestions: [
      { icon: 'FileText', text: 'להעלות סיכום אבחון', color: 'bg-blue-500' },
      { icon: 'FileText', text: 'להעלות דוח מהגן', color: 'bg-purple-500' },
      { icon: 'FileText', text: 'להעלות דוח רפואי', color: 'bg-teal-500' },
      { icon: 'Eye', text: 'לראות מסמכים קיימים', color: 'bg-orange-500' },
    ]
  },

  returning: {
    name: 'חזרה לאפליקציה',
    masterState: {
      journey_stage: 'video_upload',
      child: { name: 'יוני', age: 3.5 },
      progress: { interview: 100, videos: 0 },
      active_artifacts: [
        { type: 'instructions', count: 3, viewed: [] }
      ],
      completed_milestones: ['interview']
    },
    messages: [
      { sender: 'chitta', text: 'היי שרה, ברוכה השבה! 👋', delay: 0 },
      { sender: 'chitta', text: 'את באמצע הכנת סרטונים של יוני. נתתי לך 3 תרחישי צילום ביום שלישי שעבר.', delay: 1000 },
      { sender: 'chitta', text: 'מה תרצי לעשות עכשיו?', delay: 2000 },
    ],
    contextCards: [
      { icon: 'Video', title: 'הוראות צילום', subtitle: '3 תרחישים', status: 'pending', action: 'instructions' },
      { icon: 'CheckCircle', title: 'ההתקדמות שלך', subtitle: 'ראיון ✓ | סרטונים (0/3)', status: 'progress' },
      { icon: 'Upload', title: 'העלאת סרטון', subtitle: 'לחצי כדי להעלות', status: 'action', action: 'upload' },
    ],
    suggestions: [
      { icon: 'Video', text: 'לראות הוראות צילום', color: 'bg-indigo-500' },
      { icon: 'Upload', text: 'להעלות סרטון', color: 'bg-blue-500' },
      { icon: 'Brain', text: 'להתייעץ איתך', color: 'bg-purple-500' },
      { icon: 'FileUp', text: 'להעלות מסמך', color: 'bg-orange-500' },
    ]
  },

  instructions: {
    name: 'הצגת הוראות',
    masterState: {
      journey_stage: 'video_instructions',
      child: { name: 'יוני', age: 3.5 },
      progress: { interview: 100, videos: 0 },
      active_artifacts: [
        { type: 'instructions', count: 3, viewed: [] }
      ],
      completed_milestones: ['interview']
    },
    messages: [
      { sender: 'user', text: 'אני רוצה לראות את הוראות הצילום', delay: 0 },
      { sender: 'chitta', text: 'בטח! הנה 3 התרחישים שאני ממליצה לצלם:', delay: 800 },
      { sender: 'chitta', text: 'כל סרטון יעזור לי להבין טוב יותר את ההתנהגויות של יוני במצבים שונים.', delay: 1600 },
    ],
    contextCards: [
      { icon: 'Video', title: 'משחק חופשי', subtitle: 'עם ילדים אחרים, 3-5 דקות', status: 'instruction', action: 'view1' },
      { icon: 'Video', title: 'זמן ארוחה', subtitle: 'ארוחה משפחתית רגילה', status: 'instruction', action: 'view2' },
      { icon: 'Video', title: 'פעילות ממוקדת', subtitle: 'ציור, משחק או למידה', status: 'instruction', action: 'view3' },
    ],
    suggestions: [
      { icon: 'Eye', text: 'לקרוא את ההוראות הראשונות', color: 'bg-indigo-500' },
      { icon: 'HelpCircle', text: 'מה אם אני לא יכולה לצלם עכשיו?', color: 'bg-purple-500' },
      { icon: 'Upload', text: 'להעלות סרטון שכבר יש לי', color: 'bg-blue-500' },
    ]
  },

  videoUploaded: {
    name: 'סרטונים שהועלו',
    masterState: {
      journey_stage: 'video_upload',
      child: { name: 'יוני', age: 3.5 },
      progress: { interview: 100, videos: 33 },
      active_artifacts: [
        { type: 'video', count: 1, total: 3 }
      ],
      completed_milestones: ['interview', 'video_1']
    },
    messages: [
      { sender: 'user', text: 'העליתי את הסרטון הראשון', delay: 0 },
      { sender: 'chitta', text: 'מעולה שרה! קיבלתי את הסרטון של יוני במשחק 🎉', delay: 800 },
      { sender: 'chitta', text: 'נשארו עוד 2 סרטונים. זה ממש עוזר לקבל תמונה מלאה.', delay: 2000 },
      { sender: 'chitta', text: 'את יכולה להמשיך כשנוח לך, אין צורך לעשות הכל היום.', delay: 3200 },
    ],
    contextCards: [
      { icon: 'Video', title: 'צפייה בסרטונים', subtitle: '1 סרטון הועלה', status: 'action', action: 'videoGallery' },
      { icon: 'Upload', title: 'זמן ארוחה', subtitle: 'ממתינה לסרטון', status: 'pending', action: 'upload' },
      { icon: 'Upload', title: 'פעילות ממוקדת', subtitle: 'ממתינה לסרטון', status: 'pending', action: 'upload' },
    ],
    suggestions: [
      { icon: 'Video', text: 'לראות את הסרטון שהעליתי', color: 'bg-blue-500' },
      { icon: 'Upload', text: 'להעלות עוד סרטון', color: 'bg-indigo-500' },
      { icon: 'Clock', text: 'אני אמשיך מאוחר יותר', color: 'bg-purple-500' },
    ]
  },

  analyzing: {
    name: 'בניתוח',
    masterState: {
      journey_stage: 'analysis',
      child: { name: 'יוני', age: 3.5 },
      progress: { interview: 100, videos: 100, analysis: 20 },
      active_artifacts: [
        { type: 'video', count: 3, total: 3 },
        { type: 'analysis', status: 'processing', eta: '24h' }
      ],
      completed_milestones: ['interview', 'video_1', 'video_2', 'video_3']
    },
    messages: [
      { sender: 'chitta', text: 'שרה, קיבלתי את כל 3 הסרטונים! 🎬', delay: 0 },
      { sender: 'chitta', text: 'אני מנתחת את הסרטונים ומשלבת עם המידע מהראיון. זה ייקח כ-24 שעות.', delay: 1500 },
      { sender: 'chitta', text: 'אני אעדכן אותך ברגע שהממצאים יהיו מוכנים.', delay: 3000 },
    ],
    contextCards: [
      { icon: 'Clock', title: 'ניתוח בתהליך', subtitle: 'משוער: 24 שעות', status: 'processing' },
      { icon: 'Video', title: 'צפייה בסרטונים', subtitle: '3 סרטונים', status: 'action', action: 'videoGallery' },
      { icon: 'MessageCircle', title: 'יומן יוני', subtitle: 'הוסיפי הערות מהימים האחרונים', status: 'action', action: 'journal' },
    ],
    suggestions: [
      { icon: 'Book', text: 'להוסיף הערה ליומן', color: 'bg-amber-500' },
      { icon: 'Brain', text: 'להתייעץ איתך בינתיים', color: 'bg-purple-500' },
      { icon: 'Video', text: 'לראות את הסרטונים', color: 'bg-blue-500' },
    ]
  },

  reportReady: {
    name: 'דוח מוכן',
    masterState: {
      journey_stage: 'report_ready',
      child: { name: 'יוני', age: 3.5 },
      progress: { interview: 100, videos: 100, analysis: 100 },
      active_artifacts: [
        { type: 'report', variant: 'parent', status: 'new' },
        { type: 'report', variant: 'professional', status: 'new' }
      ],
      completed_milestones: ['interview', 'video_1', 'video_2', 'video_3', 'analysis']
    },
    messages: [
      { sender: 'chitta', text: 'שרה, סיימתי לנתח את הכל! 📊', delay: 0 },
      { sender: 'chitta', text: 'הכנתי עבורך שני דוחות:', delay: 1200 },
      { sender: 'chitta', text: '• מדריך להורים - הסברים ברורים על מה שצפיתי\n• דוח מקצועי - לשיתוף עם מומחים', delay: 2000 },
      { sender: 'chitta', text: 'אני גם יכולה לעזור לך למצוא אנשי מקצוע מתאימים באזורך על סמך הממצאים.', delay: 3500 },
      { sender: 'chitta', text: 'במה תרצי להתחיל?', delay: 4800 },
    ],
    contextCards: [
      { icon: 'FileText', title: 'מדריך להורים', subtitle: 'הסברים ברורים עבורך', status: 'new', action: 'parentReport' },
      { icon: 'FileText', title: 'דוח מקצועי', subtitle: 'לשיתוף עם מומחים', status: 'new', action: 'proReport' },
      { icon: 'Search', title: 'מציאת מומחים', subtitle: 'מבוסס על הממצאים', status: 'action', action: 'experts' },
    ],
    suggestions: [
      { icon: 'Eye', text: 'לקרוא את המדריך להורים', color: 'bg-purple-500' },
      { icon: 'Search', text: 'למצוא מומחים מתאימים', color: 'bg-teal-500' },
      { icon: 'Brain', text: 'להתייעץ איתך על הממצאים', color: 'bg-indigo-500' },
      { icon: 'Share2', text: 'לשתף את הדוח עם מישהו', color: 'bg-blue-500' },
    ]
  },

  viewReport: {
    name: 'צפייה בדוח',
    masterState: {
      journey_stage: 'report_ready',
      child: { name: 'יוני', age: 3.5 },
      progress: { interview: 100, videos: 100, analysis: 100 },
      active_artifacts: [
        { type: 'report', variant: 'parent', status: 'viewing' }
      ],
      completed_milestones: ['interview', 'video_1', 'video_2', 'video_3', 'analysis']
    },
    messages: [
      { sender: 'user', text: 'אני רוצה לראות את המדריך להורים', delay: 0 },
      { sender: 'chitta', text: 'פותחת את המדריך עבורך...', delay: 600 },
    ],
    contextCards: [
      { icon: 'Eye', title: 'צפייה במדריך', subtitle: 'גלילה לקריאת הדוח המלא', status: 'active', action: 'parentReport' },
      { icon: 'Share2', title: 'שיתוף הדוח', subtitle: 'שלחי למשפחה או מומחים', status: 'action', action: 'shareExpert' },
      { icon: 'Search', title: 'מציאת מומחים', subtitle: 'על סמך הממצאים', status: 'action', action: 'experts' },
    ],
    suggestions: [
      { icon: 'Brain', text: 'יש לי שאלות על הדוח', color: 'bg-purple-500' },
      { icon: 'Search', text: 'למצוא מומחים', color: 'bg-teal-500' },
      { icon: 'Share2', text: 'לשתף עם מישהו', color: 'bg-blue-500' },
    ]
  },

  experts: {
    name: 'מציאת מומחים',
    masterState: {
      journey_stage: 'expert_search',
      child: { name: 'יוני', age: 3.5 },
      progress: { interview: 100, videos: 100, analysis: 100 },
      active_artifacts: [
        { type: 'expert_list', count: 12 }
      ],
      completed_milestones: ['interview', 'video_1', 'video_2', 'video_3', 'analysis']
    },
    messages: [
      { sender: 'user', text: 'עזרי לי למצוא מומחים', delay: 0 },
      { sender: 'chitta', text: 'על סמך הממצאים, אני ממליצה על:', delay: 800 },
      { sender: 'chitta', text: '• קלינאית תקשורת - לתמיכה בתחום השפה\n• מרפאה בעיסוק - לקושי ויסות חושי', delay: 1800 },
      { sender: 'chitta', text: 'מצאתי 12 מומחים באזור תל אביב והסביבה המתמחים בגיל של יוני.', delay: 3200 },
    ],
    contextCards: [
      { icon: 'Users', title: 'ד״ר רחל כהן', subtitle: 'קלינאית תקשורת | 4.8★ | ת״א', status: 'expert', action: 'expert1' },
      { icon: 'Users', title: 'יעל לוי', subtitle: 'מרפאה בעיסוק | 4.9★ | רמת גן', status: 'expert', action: 'expert2' },
      { icon: 'Search', title: 'עוד 10 מומחים', subtitle: 'לחצי לראות את כולם', status: 'action', action: 'moreExperts' },
    ],
    suggestions: [
      { icon: 'Eye', text: 'לראות את הפרופיל הראשון', color: 'bg-teal-500' },
      { icon: 'Brain', text: 'איך אני בוחרת מומחה?', color: 'bg-purple-500' },
      { icon: 'HelpCircle', text: 'מה ההבדל בין המומחים?', color: 'bg-indigo-500' },
    ]
  },

  meetingPrep: {
    name: 'הכנה לפגישה',
    masterState: {
      journey_stage: 'meeting_prep',
      child: { name: 'יוני', age: 3.5 },
      progress: { interview: 100, videos: 100, analysis: 100 },
      active_artifacts: [
        { type: 'meeting_summary', expert: 'יעל לוי', date: '2024-10-16' }
      ],
      completed_milestones: ['interview', 'video_1', 'video_2', 'video_3', 'analysis']
    },
    messages: [
      { sender: 'user', text: 'יש לי פגישה מחר עם המרפאה בעיסוק', delay: 0 },
      { sender: 'chitta', text: 'אני מכינה עבורך סיכום של עמוד אחד...', delay: 800 },
      { sender: 'chitta', text: 'הסיכום כולל:\n• נקודות מפתח מהראיון\n• תובנות מהסרטונים\n• התקדמות מחודש שעבר', delay: 2000 },
      { sender: 'chitta', text: 'האם לכלול גם את ההערות מהגננת?', delay: 3500 },
    ],
    contextCards: [
      { icon: 'FileText', title: 'סיכום לפגישה', subtitle: 'מוכן לשיתוף', status: 'new', action: 'summary' },
      { icon: 'Calendar', title: 'מחר, 10:00', subtitle: 'פגישה עם יעל לוי', status: 'upcoming' },
      { icon: 'Share2', title: 'שיתוף עם המרפאה', subtitle: 'גישה מאובטחת למידע', status: 'action', action: 'shareExpert' },
    ],
    suggestions: [
      { icon: 'CheckCircle', text: 'כן, לכלול הכל', color: 'bg-green-500' },
      { icon: 'Eye', text: 'לראות את הסיכום', color: 'bg-blue-500' },
      { icon: 'Brain', text: 'מה כדאי לשאול בפגישה?', color: 'bg-purple-500' },
    ]
  },

  sharing: {
    name: 'שיתוף עם מומחה',
    masterState: {
      journey_stage: 'sharing',
      child: { name: 'יוני', age: 3.5 },
      progress: { interview: 100, videos: 100, analysis: 100 },
      active_artifacts: [
        { type: 'share_link', expert: 'ד״ר רחל כהן', expires: '30d' }
      ],
      completed_milestones: ['interview', 'video_1', 'video_2', 'video_3', 'analysis']
    },
    messages: [
      { sender: 'user', text: 'אני רוצה לשתף את הדוח עם ד״ר כהן', delay: 0 },
      { sender: 'chitta', text: 'בטח! אני יוצרת קישור מאובטח לשיתוף עם ד״ר רחל כהן.', delay: 800 },
      { sender: 'chitta', text: 'את יכולה לבחור בדיוק מה לשתף ולכמה זמן הקישור יהיה פעיל.', delay: 2200 },
    ],
    contextCards: [
      { icon: 'Shield', title: 'הגדרות שיתוף', subtitle: 'בחרי מה לשתף', status: 'action', action: 'shareExpert' },
      { icon: 'Lock', title: 'קישור מאובטח', subtitle: 'תוקף: 30 יום', status: 'new' },
      { icon: 'Users', title: 'ד״ר רחל כהן', subtitle: 'תקבל גישה למידע שנבחר', status: 'expert' },
    ],
    suggestions: [
      { icon: 'CheckCircle', text: 'לשתף הכל מלבד סרטונים', color: 'bg-blue-500' },
      { icon: 'Eye', text: 'לבחור בדיוק מה לשתף', color: 'bg-purple-500' },
      { icon: 'HelpCircle', text: 'האם זה מאובטח?', color: 'bg-teal-500' },
    ]
  }
};

// Mock API class
class ChittaAPI {
  constructor() {
    this.currentScenario = 'interview';
    // In-memory storage for videos and journal entries
    this.videos = [
      {
        id: 'video_1',
        title: 'משחק חופשי',
        description: 'עם ילדים אחרים, 3-5 דקות',
        date: '10 אוקטובר 2024',
        duration: '4:32',
        thumbnail: null,
        url: null
      }
    ];
    this.journalEntries = [
      {
        id: 'entry_1',
        text: 'יוני התחיל להשתמש ב"בבקשה" ו"תודה" יותר לבד! אני כל כך גאה בו 💚',
        status: 'התקדמות',
        timestamp: 'לפני 3 ימים',
        date: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000)
      },
      {
        id: 'entry_2',
        text: 'בגן הגננת אמרה שהוא משתלב יותר טוב במעגל. נראה שהטיפולים עוזרים.',
        status: 'תצפית',
        timestamp: 'לפני שבוע',
        date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
      },
      {
        id: 'entry_3',
        text: 'היום היה קשה בקניון - הרעש היה חזק מדי בשבילו. עזבנו מוקדם.',
        status: 'אתגר',
        timestamp: 'לפני שבועיים',
        date: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000)
      }
    ];
  }

  // Get scenario data
  async getScenario(scenarioKey) {
    return new Promise((resolve) => {
      setTimeout(() => {
        this.currentScenario = scenarioKey;
        resolve(SCENARIOS[scenarioKey]);
      }, 100);
    });
  }

  // Get all available scenarios for demo controls
  async getAllScenarios() {
    return Object.keys(SCENARIOS).map(key => ({
      key,
      name: SCENARIOS[key].name
    }));
  }

  // Send a message (simulated)
  async sendMessage(message) {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          success: true,
          response: {
            sender: 'chitta',
            text: 'תגובה מהמערכת...'
          }
        });
      }, 800);
    });
  }

  // Trigger an action (like opening a deep view)
  async triggerAction(actionKey) {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          success: true,
          deepView: actionKey
        });
      }, 300);
    });
  }

  // Upload file (simulated)
  async uploadFile(file) {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          success: true,
          fileId: 'file_' + Date.now(),
          message: 'הקובץ הועלה בהצלחה'
        });
      }, 1500);
    });
  }

  // === JOURNAL CRUD OPERATIONS ===

  // Get all journal entries
  async getJournalEntries() {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          success: true,
          entries: [...this.journalEntries].sort((a, b) => b.date - a.date)
        });
      }, 200);
    });
  }

  // Create a new journal entry
  async createJournalEntry(text, status = 'תצפית') {
    return new Promise((resolve) => {
      setTimeout(() => {
        const newEntry = {
          id: 'entry_' + Date.now(),
          text,
          status,
          timestamp: 'עכשיו',
          date: new Date()
        };
        this.journalEntries.unshift(newEntry);
        resolve({
          success: true,
          entry: newEntry,
          message: 'הרשומה נשמרה בהצלחה'
        });
      }, 300);
    });
  }

  // Delete a journal entry
  async deleteJournalEntry(entryId) {
    return new Promise((resolve) => {
      setTimeout(() => {
        const index = this.journalEntries.findIndex(e => e.id === entryId);
        if (index !== -1) {
          this.journalEntries.splice(index, 1);
          resolve({
            success: true,
            message: 'הרשומה נמחקה'
          });
        } else {
          resolve({
            success: false,
            message: 'רשומה לא נמצאה'
          });
        }
      }, 200);
    });
  }

  // === VIDEO CRUD OPERATIONS ===

  // Get all videos
  async getVideos() {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          success: true,
          videos: [...this.videos]
        });
      }, 200);
    });
  }

  // Create/Upload a new video
  async createVideo(videoData) {
    return new Promise((resolve) => {
      setTimeout(() => {
        const newVideo = {
          id: 'video_' + Date.now(),
          title: videoData.title || 'סרטון חדש',
          description: videoData.description || '',
          date: new Date().toLocaleDateString('he-IL'),
          duration: videoData.duration || '0:00',
          thumbnail: videoData.thumbnail || null,
          url: videoData.url || null
        };
        this.videos.push(newVideo);
        resolve({
          success: true,
          video: newVideo,
          message: 'הסרטון הועלה בהצלחה'
        });
      }, 1500);
    });
  }

  // Delete a video
  async deleteVideo(videoId) {
    return new Promise((resolve) => {
      setTimeout(() => {
        const index = this.videos.findIndex(v => v.id === videoId);
        if (index !== -1) {
          this.videos.splice(index, 1);
          resolve({
            success: true,
            message: 'הסרטון נמחק'
          });
        } else {
          resolve({
            success: false,
            message: 'סרטון לא נמצא'
          });
        }
      }, 300);
    });
  }
}

export default new ChittaAPI();
