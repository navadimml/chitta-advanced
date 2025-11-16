// UIAdapter.js - Pure function that generates UI from state

class UIAdapter {
  constructor(config) {
    this.config = config;
  }

  // ===== GENERATE UI FROM STATE =====

  generateUI(state) {
    const stage = this.config.stages.find(s => s.id === state.currentStage);

    if (!stage) {
      return {
        cards: [],
        suggestions: [],
        messages: state.ui.messages || [],
        hints: []
      };
    }

    return {
      cards: this.generateCards(stage, state),
      suggestions: this.generateSuggestions(stage, state),
      messages: state.ui.messages || [],
      hints: this.generateHints(stage, state)
    };
  }

  // ===== CARDS =====

  generateCards(stage, state) {
    // Allow stage to define custom card generator
    if (stage.generateCards) {
      return stage.generateCards(state);
    }

    // Default generators by stage type
    const cardGenerators = {
      conversation: (stage, state) => [
        {
          icon: 'MessageCircle',
          title: stage.goal || 'שיחה',
          subtitle: this.getProgressText(stage, state),
          status: 'processing'
        }
      ],

      file_collection: (stage, state) => {
        const uploaded = state.data.uploadedFiles?.length || 0;
        const required = stage.requirements?.count || 3;

        const cards = [
          {
            icon: 'Upload',
            title: 'העלאת קבצים',
            subtitle: `${uploaded}/${required} הועלו`,
            status: uploaded === required ? 'completed' : 'action',
            action: 'upload'
          }
        ];

        if (uploaded > 0) {
          cards.push({
            icon: 'Video',
            title: 'צפייה בקבצים',
            subtitle: `${uploaded} קבצים`,
            status: 'action',
            action: 'videoGallery'
          });
        }

        return cards;
      },

      background_process: (stage, state) => [
        {
          icon: 'Clock',
          title: stage.statusMessages?.inProgress || 'מעבד...',
          subtitle: `זמן משוער: ${stage.estimatedDuration || 'לא ידוע'}`,
          status: 'processing'
        }
      ],

      content_delivery: (stage, state) => {
        const cards = [];

        if (stage.content) {
          Object.entries(stage.content).forEach(([key, config]) => {
            cards.push({
              icon: 'FileText',
              title: config.title || key,
              subtitle: config.description || 'לחץ לצפייה',
              status: 'new',
              action: `view_${key}`
            });
          });
        }

        return cards;
      }
    };

    const generator = cardGenerators[stage.type];
    return generator ? generator(stage, state) : [];
  }

  // ===== SUGGESTIONS =====

  generateSuggestions(stage, state) {
    // Allow stage to define custom suggestion generator
    if (stage.generateSuggestions) {
      return stage.generateSuggestions(state);
    }

    // Default generators by stage type
    if (stage.type === 'conversation') {
      return this.generateConversationSuggestions(stage, state);
    }

    if (stage.type === 'file_collection') {
      return [
        { icon: 'Upload', text: 'להעלות קובץ', color: 'bg-blue-500', action: 'upload' },
        { icon: 'Video', text: 'לצלם סרטון', color: 'bg-purple-500', action: 'record' },
        { icon: 'HelpCircle', text: 'איך להעלות?', color: 'bg-indigo-500', action: 'help' }
      ];
    }

    return [];
  }

  generateConversationSuggestions(stage, state) {
    const base = [
      { icon: 'MessageCircle', text: 'יש לי דאגות', color: 'bg-blue-500' },
      { icon: 'Users', text: 'קשיים חברתיים', color: 'bg-purple-500' },
      { icon: 'Heart', text: 'שאלות כלליות', color: 'bg-pink-500' }
    ];

    // Add dynamic suggestions based on context
    const dynamic = [];

    // If we have name but not age
    if (state.data.childName && !state.data.age) {
      dynamic.push({
        icon: 'User',
        text: `${state.data.childName} בן 3`,
        color: 'bg-indigo-500'
      });
      dynamic.push({
        icon: 'User',
        text: `${state.data.childName} בן 4`,
        color: 'bg-indigo-500'
      });
    }

    // If draft mentions kindergarten
    if (state.ui.draftMessage?.includes('גן')) {
      dynamic.push({
        icon: 'FileUp',
        text: 'יש לי דוח מהגן',
        color: 'bg-orange-500',
        action: 'uploadDoc'
      });
    }

    // If draft mentions report/diagnosis
    if (state.ui.draftMessage?.includes('אבחון') || state.ui.draftMessage?.includes('דוח')) {
      dynamic.push({
        icon: 'FileUp',
        text: 'יש לי אבחון להעלות',
        color: 'bg-orange-500',
        action: 'uploadDoc'
      });
    }

    return [...dynamic, ...base];
  }

  // ===== HINTS (Just-in-time contextual help) =====

  generateHints(stage, state) {
    const hints = [];

    // First interaction hint
    if (state.ui.messages.length === 0 && !state.meta.hasSeenChatHint) {
      hints.push({
        target: 'chat',
        message: "💡 פשוט כתבי את מה שעובר לך בראש",
        position: 'bottom'
      });
    }

    // Draft message hint
    if (state.ui.draftMessage && state.ui.draftMessage.length > 5 && !state.meta.hasSeenSendHint) {
      hints.push({
        target: 'send-button',
        message: "💡 לחצי Enter או על כפתור השליחה",
        position: 'top'
      });
    }

    // Card interaction hint
    if (state.ui.messages.length > 3 && !state.meta.hasSeenCardHint) {
      hints.push({
        target: 'cards',
        message: "💡 הכרטיסים האלה משתנים לפי המצב שלך",
        position: 'top'
      });
    }

    return hints;
  }

  // ===== HELPERS =====

  getProgressText(stage, state) {
    if (stage.completion?.minTopics) {
      const completed = stage.completion.minTopics.filter(topic =>
        state.data[topic] !== undefined && state.data[topic] !== null && state.data[topic] !== ''
      ).length;
      const total = stage.completion.minTopics.length;
      return `התקדמות: ${completed}/${total}`;
    }

    if (stage.completion?.fileCount) {
      const uploaded = state.data.uploadedFiles?.length || 0;
      const required = stage.completion.fileCount;
      return `${uploaded}/${required} קבצים`;
    }

    // Count topics discussed
    const topicsCount = Object.keys(state.data).filter(k => state.data[k]).length;
    return topicsCount > 0 ? `${topicsCount} נושאים נדונו` : 'בתהליך';
  }
}

export default UIAdapter;
