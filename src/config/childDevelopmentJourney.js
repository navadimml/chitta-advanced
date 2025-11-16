// childDevelopmentJourney.js - Domain-specific configuration for child development assessment

const childDevelopmentJourney = {
  meta: {
    name: "הערכת התפתחות הילד",
    welcomeMessage: "שלום! אני Chitta 💙\n\nאני כאן כדי לעזור לך להבין את המסע ההתפתחותי של הילד שלך."
  },

  stages: [
    // ===== STAGE 1: WELCOME =====
    {
      id: "welcome",
      type: "conversation",
      goal: "התחלה",

      onEnter: async (engine) => {
        const state = engine.getState();

        // Only show welcome on first visit
        if (!state.meta.hasSeenWelcome) {
          engine.updateNested('ui.messages', [
            {
              sender: 'chitta',
              text: 'שלום! אני Chitta 💙\n\nאני כאן כדי לעזור לך להבין את המסע ההתפתחותי של הילד שלך.\n\nבואי נתחיל בשיחה קצרה.',
              timestamp: Date.now(),
              id: engine.generateId()
            }
          ]);
          engine.updateNested('meta.hasSeenWelcome', true);
        }
      },

      completion: {
        custom: (state) => state.ui.messages.length > 2 // User sent at least one message
      },

      nextStage: "interview",
      validTransitions: ["interview"]
    },

    // ===== STAGE 2: INTERVIEW =====
    {
      id: "interview",
      type: "conversation",
      goal: "ריאיון התפתחותי",

      onEnter: async (engine) => {
        const state = engine.getState();

        if (!state.meta.hasStartedInterview) {
          // First time entering interview
          setTimeout(() => {
            engine.updateNested('ui.messages', [
              ...state.ui.messages,
              {
                sender: 'chitta',
                text: 'מעולה! בואי נתחיל בהכרות.\n\nמה שמו של הילד שלך?',
                timestamp: Date.now(),
                id: engine.generateId()
              }
            ]);
          }, 500);
          engine.updateNested('meta.hasStartedInterview', true);
        }
      },

      completion: {
        minTopics: ["childName", "age", "concerns"]
      },

      prompts: {
        completion: `תודה רבה! יש לי תמונה טובה של ${(state) => state.data.childName || 'הילד שלך'}.\n\nעכשיו אני אכין עבורך הוראות צילום פשוטות. 🎬`
      },

      generateCards: (state) => {
        const topics = Object.keys(state.data).filter(k => state.data[k]).length;
        const progress = Math.min(100, (topics / 3) * 100);

        return [
          {
            icon: 'MessageCircle',
            title: 'מתנהל ראיון',
            subtitle: `התקדמות: ${Math.round(progress)}%`,
            status: 'processing'
          },
          {
            icon: 'CheckCircle',
            title: 'מידע שנאסף',
            subtitle: topics > 0 ? `${topics} פרטים` : 'טרם התחלנו',
            status: topics > 0 ? 'progress' : 'pending'
          },
          {
            icon: 'Book',
            title: 'יומן יוני',
            subtitle: 'הערות והתבוננויות',
            status: 'action',
            action: 'journal'
          }
        ];
      },

      generateSuggestions: (state) => {
        const base = [
          { icon: 'MessageCircle', text: 'אני מודאגת מהדיבור שלו', color: 'bg-blue-500' },
          { icon: 'Users', text: 'הוא מתקשה עם ילדים אחרים', color: 'bg-purple-500' },
          { icon: 'Heart', text: 'יש לי שאלות כלליות', color: 'bg-pink-500' }
        ];

        const dynamic = [];

        // Name-based suggestions
        if (state.data.childName && !state.data.age) {
          dynamic.push(
            { icon: 'User', text: `${state.data.childName} בן 3`, color: 'bg-indigo-500' },
            { icon: 'User', text: `${state.data.childName} בן 4`, color: 'bg-indigo-500' }
          );
        }

        return [...dynamic, ...base];
      },

      nextStage: "video_instructions",
      validTransitions: ["video_instructions", "consultation"]
    },

    // ===== STAGE 3: VIDEO INSTRUCTIONS =====
    {
      id: "video_instructions",
      type: "conversation",
      goal: "קבלת הוראות צילום",

      onEnter: async (engine) => {
        const state = engine.getState();
        const childName = state.data.childName || 'הילד שלך';

        // Generate video instructions
        const instructions = [
          {
            id: 'video_1',
            title: 'משחק חופשי',
            description: 'עם ילדים אחרים, 3-5 דקות',
            scenario: 'free_play'
          },
          {
            id: 'video_2',
            title: 'זמן ארוחה',
            description: 'ארוחה משפחתית רגילה',
            scenario: 'mealtime'
          },
          {
            id: 'video_3',
            title: 'פעילות ממוקדת',
            description: 'ציור, משחק או למידה',
            scenario: 'focused_activity'
          }
        ];

        engine.updateData('videoInstructions', instructions);
        engine.updateData('requiredVideos', 3);

        setTimeout(() => {
          engine.updateNested('ui.messages', [
            ...state.ui.messages,
            {
              sender: 'chitta',
              text: `הכנתי עבורך 3 תרחישי צילום של ${childName}.\n\nכל סרטון יעזור לי להבין טוב יותר את ההתנהגות שלו במצבים שונים.\n\nאת יכולה לצלם בקצב שלך - אין צורך לעשות הכל היום. 📱`,
              timestamp: Date.now(),
              id: engine.generateId()
            }
          ]);
        }, 1000);
      },

      generateCards: (state) => {
        const instructions = state.data.videoInstructions || [];

        return instructions.map(inst => ({
          icon: 'Video',
          title: inst.title,
          subtitle: inst.description,
          status: 'instruction',
          action: `view_instruction_${inst.id}`
        }));
      },

      generateSuggestions: (state) => [
        { icon: 'Video', text: 'הבנתי, בואי נמשיך', color: 'bg-indigo-500' },
        { icon: 'Upload', text: 'להעלות סרטון', color: 'bg-blue-500', action: 'upload' },
        { icon: 'HelpCircle', text: 'איך לצלם?', color: 'bg-purple-500', action: 'help' }
      ],

      completion: {
        custom: (state) => state.meta.acknowledgedInstructions === true
      },

      nextStage: "video_upload",
      validTransitions: ["video_upload"]
    },

    // ===== STAGE 4: VIDEO UPLOAD =====
    {
      id: "video_upload",
      type: "file_collection",
      goal: "העלאת סרטונים",

      requirements: {
        fileType: "video",
        count: 3,
        maxSize: "100MB"
      },

      onEnter: async (engine) => {
        const state = engine.getState();

        setTimeout(() => {
          engine.updateNested('ui.messages', [
            ...state.ui.messages,
            {
              sender: 'chitta',
              text: 'מוכנה להעלות סרטונים?\n\nאת יכולה להעלות מהגלריה או לצלם ישירות מהאפליקציה. 📹',
              timestamp: Date.now(),
              id: engine.generateId()
            }
          ]);
        }, 500);
      },

      generateCards: (state) => {
        const videos = state.data.videos || [];
        const required = state.data.requiredVideos || 3;

        const cards = [
          {
            icon: 'Upload',
            title: 'העלאת סרטון',
            subtitle: `${videos.length}/${required} הועלו`,
            status: videos.length === required ? 'completed' : 'action',
            action: 'upload'
          }
        ];

        if (videos.length > 0) {
          cards.push({
            icon: 'Video',
            title: 'צפייה בסרטונים',
            subtitle: `${videos.length} סרטונים`,
            status: 'action',
            action: 'videoGallery'
          });
        }

        return cards;
      },

      generateSuggestions: (state) => {
        const videos = state.data.videos || [];
        const required = state.data.requiredVideos || 3;

        if (videos.length === 0) {
          return [
            { icon: 'Upload', text: 'להעלות סרטון', color: 'bg-blue-500', action: 'upload' },
            { icon: 'Video', text: 'לראות הוראות', color: 'bg-indigo-500' }
          ];
        } else if (videos.length < required) {
          return [
            { icon: 'Upload', text: 'להעלות עוד סרטון', color: 'bg-blue-500', action: 'upload' },
            { icon: 'Video', text: 'לצפות בסרטונים', color: 'bg-purple-500', action: 'videoGallery' },
            { icon: 'Clock', text: 'אמשיך מאוחר יותר', color: 'bg-gray-500' }
          ];
        } else {
          return [
            { icon: 'CheckCircle', text: 'סיימתי! בואי נמשיך', color: 'bg-green-500' }
          ];
        }
      },

      completion: {
        custom: (state) => {
          const videos = state.data.videos || [];
          const required = state.data.requiredVideos || 3;
          return videos.length >= required;
        }
      },

      prompts: {
        completion: 'מעולה! קיבלתי את כל הסרטונים! 🎉\n\nאני מתחילה לנתח. זה ייקח בערך 24 שעות.\n\nאני אעדכן אותך ברגע שהדוח יהיה מוכן.'
      },

      nextStage: "analyzing",
      validTransitions: ["analyzing"]
    },

    // ===== STAGE 5: ANALYZING =====
    {
      id: "analyzing",
      type: "background_process",
      estimatedDuration: "24 שעות",

      statusMessages: {
        inProgress: "מנתח סרטונים...",
        complete: "הניתוח הושלם!"
      },

      onEnter: async (engine) => {
        const state = engine.getState();
        const childName = state.data.childName || 'הילד שלך';

        // Simulate analysis (in real app, this would trigger backend process)
        engine.updateData('analysisStatus', 'in_progress');
        engine.updateData('analysisStartTime', Date.now());

        // Auto-complete after 5 seconds (for demo purposes)
        // In real app, this would be triggered by backend
        setTimeout(() => {
          engine.updateData('analysisStatus', 'complete');
          engine.transitionTo('report_ready');
        }, 5000);
      },

      generateCards: (state) => [
        {
          icon: 'Clock',
          title: 'ניתוח בתהליך',
          subtitle: 'משוער: 24 שעות',
          status: 'processing'
        },
        {
          icon: 'Video',
          title: 'צפייה בסרטונים',
          subtitle: `${state.data.videos?.length || 0} סרטונים`,
          status: 'action',
          action: 'videoGallery'
        },
        {
          icon: 'Book',
          title: 'יומן',
          subtitle: 'הוסיפי הערות בינתיים',
          status: 'action',
          action: 'journal'
        }
      ],

      generateSuggestions: (state) => [
        { icon: 'Book', text: 'להוסיף הערה ליומן', color: 'bg-amber-500', action: 'journal' },
        { icon: 'Video', text: 'לראות את הסרטונים', color: 'bg-blue-500', action: 'videoGallery' }
      ],

      nextStage: "report_ready",
      validTransitions: ["report_ready"]
    },

    // ===== STAGE 6: REPORT READY =====
    {
      id: "report_ready",
      type: "content_delivery",

      content: {
        parent: {
          title: "מדריך להורים",
          description: "הסברים ברורים עבורך"
        },
        professional: {
          title: "דוח מקצועי",
          description: "לשיתוף עם מומחים"
        }
      },

      onEnter: async (engine) => {
        const state = engine.getState();
        const childName = state.data.childName || 'הילד שלך';

        setTimeout(() => {
          engine.updateNested('ui.messages', [
            ...state.ui.messages,
            {
              sender: 'chitta',
              text: `הדוח של ${childName} מוכן! 📊\n\nהכנתי עבורך שני דוחות:\n• מדריך להורים - הסברים ברורים\n• דוח מקצועי - לשיתוף עם מומחים\n\nאני גם יכולה לעזור לך למצוא אנשי מקצוע מתאימים.`,
              timestamp: Date.now(),
              id: engine.generateId()
            }
          ]);
        }, 1000);
      },

      generateCards: (state) => [
        {
          icon: 'FileText',
          title: 'מדריך להורים',
          subtitle: 'הסברים ברורים עבורך',
          status: 'new',
          action: 'parentReport'
        },
        {
          icon: 'FileText',
          title: 'דוח מקצועי',
          subtitle: 'לשיתוף עם מומחים',
          status: 'new',
          action: 'proReport'
        },
        {
          icon: 'Search',
          title: 'מציאת מומחים',
          subtitle: 'מבוסס על הממצאים',
          status: 'action',
          action: 'experts'
        }
      ],

      generateSuggestions: (state) => [
        { icon: 'Eye', text: 'לקרוא את המדריך להורים', color: 'bg-purple-500', action: 'parentReport' },
        { icon: 'Search', text: 'למצוא מומחים מתאימים', color: 'bg-teal-500', action: 'experts' },
        { icon: 'Share2', text: 'לשתף את הדוח', color: 'bg-blue-500', action: 'shareExpert' }
      ],

      validTransitions: []
    }
  ]
};

export default childDevelopmentJourney;
