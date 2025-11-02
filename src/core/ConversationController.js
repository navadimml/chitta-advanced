// ConversationController.js - Handles messages and proactive behavior (smart, not annoying)

class ConversationController {
  constructor(journeyEngine) {
    this.engine = journeyEngine;
    this.proactiveTimeout = null;
  }

  // ===== USER MESSAGES =====

  async sendMessage(text) {
    const state = this.engine.state;

    // Add user message
    this.addMessage({ sender: 'user', text });

    // Clear draft
    this.engine.updateNested('ui.draftMessage', '');

    // Extract information from message
    const extracted = await this.extractInformation(text);

    // Update data
    Object.entries(extracted).forEach(([key, value]) => {
      const currentValue = this.engine.getData(key);

      if (Array.isArray(value)) {
        // Merge arrays
        const merged = [...(currentValue || []), ...value];
        this.engine.updateData(key, [...new Set(merged)]); // Remove duplicates
      } else {
        this.engine.updateData(key, value);
      }
    });

    // Generate response
    const response = await this.generateResponse(text, extracted);

    // Small delay for natural feel
    setTimeout(() => {
      this.addMessage({ sender: 'chitta', text: response });

      // Check if stage is complete
      if (this.engine.isStageComplete()) {
        this.handleStageCompletion();
      }
    }, 800);
  }

  // ===== PROACTIVE MESSAGES (Smart!) =====

  getProactiveMessage() {
    const state = this.engine.state;
    const stage = this.engine.getCurrentStage();

    // Only send proactive messages in specific situations:

    // 1. User just returned after being away
    if (state.meta.isReturning && !state.meta.hasSeenWelcomeBack) {
      this.engine.updateNested('meta.hasSeenWelcomeBack', true);
      return this.getWelcomeBackMessage();
    }

    // 2. User is clearly stuck (no activity for 5+ min) and has interacted before
    const idleTime = Date.now() - state.ui.lastActivity;
    if (idleTime > 5 * 60 * 1000 && state.ui.messages.length > 0 && !state.meta.hasSeenIdleHelp) {
      this.engine.updateNested('meta.hasSeenIdleHelp', true);
      return {
        text: "עדיין כאן? אם משהו לא ברור, אני כאן לעזור 💙",
        suggestions: [
          { text: 'איך זה עובד?', action: 'help' },
          { text: 'מה אני צריכה לעשות?', action: 'explain' }
        ]
      };
    }

    return null; // Don't be annoying!
  }

  getWelcomeBackMessage() {
    const state = this.engine.state;
    const context = this.generateContextSummary();

    const hours = Math.floor(state.meta.timeAway / (1000 * 60 * 60));
    let greeting = 'ברוכה השבה!';

    if (hours > 24) {
      greeting = 'היי! שמחה לראות אותך שוב 👋';
    } else if (hours > 1) {
      greeting = 'היי! ברוכה השבה 😊';
    }

    return {
      text: `${greeting}\n\n${context.summary}`,
      suggestions: context.nextActions
    };
  }

  generateContextSummary() {
    const state = this.engine.state;
    const stage = this.engine.getCurrentStage();

    // Generate smart summary based on what's been done
    const data = state.data;

    // No progress yet
    if (Object.keys(data).length === 0) {
      return {
        summary: 'בואי נתחיל!',
        nextActions: [{ text: 'בואי נתחיל', action: 'continue' }]
      };
    }

    // Has child info
    if (data.childName) {
      const topics = Object.keys(data).filter(k => data[k]).length;
      return {
        summary: `דיברנו על ${data.childName}. אספנו ${topics} פרטים.`,
        nextActions: [{ text: 'בואי נמשיך', action: 'continue' }]
      };
    }

    return {
      summary: 'התחלנו לדבר.',
      nextActions: [{ text: 'המשך שיחה', action: 'continue' }]
    };
  }

  // ===== INFORMATION EXTRACTION (Simulated) =====

  async extractInformation(text) {
    // In real app: call LLM with function calling
    // For now: simple pattern matching

    const extracted = {};

    // Extract name (Hebrew)
    const nameMatch = text.match(/שמו ([\u0590-\u05FF]+)/);
    if (nameMatch) extracted.childName = nameMatch[1];

    // Extract age
    const ageMatch = text.match(/בן (\d+)/);
    if (ageMatch) extracted.age = parseInt(ageMatch[1]);

    const ageMatch2 = text.match(/(\d+) שנים/);
    if (ageMatch2) extracted.age = parseInt(ageMatch2[1]);

    // Extract concerns
    const concerns = [];
    if (text.includes('דיבור') || text.includes('לדבר')) concerns.push('speech');
    if (text.includes('חברים') || text.includes('חברתי')) concerns.push('social');
    if (text.includes('קשב') || text.includes('ריכוז')) concerns.push('attention');
    if (text.includes('רגשות') || text.includes('רגשי')) concerns.push('emotional');
    if (concerns.length > 0) extracted.concerns = concerns;

    // Topics discussed (for tracking)
    if (extracted.childName) extracted.topics = ['name'];
    if (extracted.age) extracted.topics = ['age'];
    if (extracted.concerns) extracted.topics = ['concerns'];

    return extracted;
  }

  // ===== RESPONSE GENERATION (Simulated) =====

  async generateResponse(userMessage, extracted) {
    const state = this.engine.state;
    const stage = this.engine.getCurrentStage();
    const data = state.data;

    // In real app: call LLM with context
    // For now: simple rules based on what we have

    // First interaction - ask for name
    if (!data.childName) {
      if (extracted.childName) {
        return `נעים להכיר את ${extracted.childName}! 😊 בן כמה הוא?`;
      }
      return 'מה שמו של הילד שלך?';
    }

    // Have name, need age
    if (!data.age) {
      if (extracted.age) {
        return `${data.childName} בן ${extracted.age}, גיל נפלא! 💙\n\nמה גרם לך לפנות אליי? מה מעסיק אותך לגבי ${data.childName}?`;
      }
      return `בן כמה ${data.childName}?`;
    }

    // Have name and age, need concerns
    if (!data.concerns || data.concerns.length === 0) {
      if (extracted.concerns) {
        const concernText = this.getConcernText(extracted.concerns);
        return `אני שומעת שיש דאגות ב${concernText}. ספרי לי עוד על זה.`;
      }
      return `ספרי לי, מה מעסיק אותך לגבי ${data.childName}?`;
    }

    // Have basic info, encourage more details
    return stage.prompts?.followUp || 'ספרי לי עוד...';
  }

  getConcernText(concerns) {
    const concernMap = {
      speech: 'דיבור',
      social: 'תקשורת חברתית',
      attention: 'קשב וריכוז',
      emotional: 'ויסות רגשי'
    };

    return concerns.map(c => concernMap[c] || c).join(', ');
  }

  // ===== STAGE COMPLETION =====

  async handleStageCompletion() {
    const stage = this.engine.getCurrentStage();

    // Send completion message
    if (stage.prompts?.completion) {
      setTimeout(() => {
        this.addMessage({ sender: 'chitta', text: stage.prompts.completion });

        // Transition to next stage after a delay
        if (stage.nextStage) {
          setTimeout(() => {
            this.engine.transitionTo(stage.nextStage);
          }, 1500);
        }
      }, 1000);
    } else {
      // Transition immediately if no completion message
      if (stage.nextStage) {
        setTimeout(() => {
          this.engine.transitionTo(stage.nextStage);
        }, 500);
      }
    }
  }

  // ===== HELPERS =====

  addMessage(message) {
    const state = this.engine.state;
    this.engine.updateNested('ui.messages', [
      ...state.ui.messages,
      { ...message, timestamp: Date.now(), id: this.engine.generateId() }
    ]);
  }

  // Update draft message
  updateDraft(text) {
    this.engine.updateNested('ui.draftMessage', text);
  }

  // Start proactive message monitoring
  startProactiveMonitoring() {
    // Check every 60 seconds
    this.proactiveTimeout = setInterval(() => {
      const proactiveMsg = this.getProactiveMessage();
      if (proactiveMsg) {
        this.addMessage({ sender: 'chitta', text: proactiveMsg.text });
      }
    }, 60000);
  }

  stopProactiveMonitoring() {
    if (this.proactiveTimeout) {
      clearInterval(this.proactiveTimeout);
    }
  }
}

export default ConversationController;
