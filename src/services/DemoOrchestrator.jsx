/**
 * 🎭 Demo Orchestrator - Clean Architecture
 *
 * Manages demo mode completely separately from the app.
 * The app doesn't know it's in demo - we inject data as if it were real.
 *
 * Inspired by Puppeteer's approach: control from outside.
 */

import ReactDOM from 'react-dom';
import React from 'react';
import DemoBannerPortal from '../components/DemoBannerPortal';

class DemoOrchestrator {
  constructor() {
    this.active = false;
    this.scenario = null;
    this.currentStep = -1;
    this.speed = 1.0; // 1x = normal speed
    this.paused = false;
    this.bannerContainer = null;
    this.messageInjector = null; // Callback to inject messages into app
    this.cardInjector = null; // Callback to inject cards into app
    this.guidelinesInjector = null; // Callback to inject guidelines into app
    this.timeoutId = null;
  }

  /**
   * Check if demo is active
   */
  isActive() {
    return this.active;
  }

  /**
   * Start demo with scenario
   */
  async start(scenario, messageInjector, cardInjector) {
    console.log('🎭 DemoOrchestrator: Starting demo...');

    this.active = true;
    this.scenario = scenario;
    this.currentStep = -1;
    this.messageInjector = messageInjector;
    this.cardInjector = cardInjector;

    // Create banner portal
    this.createBanner();

    // Start auto-play
    this.playNext();
  }

  /**
   * Play next message in scenario
   */
  async playNext() {
    if (!this.active || this.paused) {
      console.log('🎭 Paused or inactive, skipping');
      return;
    }

    this.currentStep++;

    if (this.currentStep >= this.scenario.messages.length) {
      this.complete();
      return;
    }

    const message = this.scenario.messages[this.currentStep];
    const adjustedDelay = message.delay_ms / this.speed; // Speed adjustment!

    console.log(`🎭 Step ${this.currentStep + 1}/${this.scenario.messages.length} - Delay: ${adjustedDelay}ms (${this.speed}x speed)`);

    // Update banner
    this.updateBanner();

    // Wait for delay
    if (adjustedDelay > 0) {
      await new Promise(resolve => {
        this.timeoutId = setTimeout(resolve, adjustedDelay);
      });
    }

    // Inject message into app (app doesn't know it's demo!)
    this.injectMessage(message);

    // Handle special actions
    if (message.trigger_artifact) {
      this.injectArtifactCard();
    }

    if (message.card_hint) {
      // Inject contextual cards based on hints
      this.injectContextCard(message.card_hint);
    }

    // Schedule next
    setTimeout(() => this.playNext(), 100);
  }

  /**
   * Inject message into app
   */
  injectMessage(message) {
    if (this.messageInjector) {
      const formattedMessage = {
        sender: message.role === 'user' ? 'user' : 'chitta',
        text: message.content,
        timestamp: new Date().toISOString()
      };

      this.messageInjector(formattedMessage);
    }
  }

  /**
   * Inject artifact card and guidelines
   */
  injectArtifactCard() {
    // Inject guidelines data
    if (this.guidelinesInjector) {
      const demoGuidelines = {
        introduction: "הסרטונים יעזרו לי להבין את ההתפתחות של דניאל בצורה מעמיקה ומדויקת. זה כמו שאלך איתך הביתה ואראה אותו בפעולה - רק שאת קובעת מתי ואיך.",
        estimated_duration: "2-3 דקות לסרטון",
        scenarios: [
          {
            title: "משחק חופשי",
            context: "דניאל משחק עם הצעצועים האהובים עליו",
            duration: "2-3 דקות",
            what_to_film: "צלמי את דניאל משחק בחופשיות עם הצעצועים שלו. אל תכווני אותו - רק תתבונני. האם הוא מדבר לעצמו? איך הוא מבטא רצונות? האם הוא מזמין אותך להצטרף?",
            what_to_look_for: [
              "האם הוא משתמש במילים במהלך המשחק?",
              "איך הוא מבקש עזרה אם צריך?",
              "האם יש תקשורת לא מילולית (מחוות, הצבעה)?",
              "מה קורה כשהוא רוצה משהו שלא בהישג יד?"
            ],
            why_matters: "המשחק החופשי חושף את דפוסי התקשורת הטבעיים של דניאל כשהוא נינוח ומרוכז."
          },
          {
            title: "אוכל משותף",
            context: "ארוחה או חטיף עם דניאל",
            duration: "2-3 דקות",
            what_to_film: "צלמי את דניאל בזמן ארוחה. איך הוא מבקש דברים? האם הוא משתף מה הוא אוהב/לא אוהב? תגיבי באופן טבעי ותראי איך הוא מגיב.",
            what_to_look_for: [
              "איך הוא מבקש עוד אוכל?",
              "מה קורה כשמציעים לו משהו שהוא לא רוצה?",
              "האם יש שיחה קטנה על האוכל?",
              "איך הוא מבטא העדפות?"
            ],
            why_matters: "מצבים יומיומיים כמו אוכל מראים תקשורת פונקציונלית - איך דניאל מבטא צרכים ורצונות בסיטואציה אמיתית."
          },
          {
            title: "משחק עם ילד אחר",
            context: "אם אפשר - דניאל עם אח, חבר או בן משפחה",
            duration: "2-3 דקות",
            what_to_film: "אם יש אפשרות, צלמי את דניאל משחק עם ילד אחר (אח, חבר, בן דוד). איך הם מתקשרים? מי מוביל? האם יש שיתוף פעולה?",
            what_to_look_for: [
              "איך דניאל פונה לילד האחר?",
              "האם יש עין-קשר או תקשורת גופנית?",
              "מה קורה בקונפליקט (כמו רצון באותו צעצוע)?",
              "האם יש משחק משותף או משחק מקביל?"
            ],
            why_matters: "המשחק החברתי מראה את התקשורת של דניאל עם בני גילו - זה שונה מאינטראקציה עם מבוגרים."
          }
        ],
        general_tips: [
          "צלמי בגובה עיניים של דניאל - לא מלמעלה",
          "תנועה טבעית עדיפה על 'פוזה' - תראי את דניאל כמו שהוא",
          "אורך משוער: 2-3 דקות לכל תרחיש, לא יותר מ-5 דקות",
          "אין צורך באיכות מושלמת - תוכן חשוב יותר מטכניקה",
          "אפשר לצלם במשך כמה ימים - לא הכל באותו היום",
          "אם דניאל לא משתף פעולה ביום מסוים - אין בעיה לנסות מחר"
        ]
      };

      this.guidelinesInjector(demoGuidelines);
    }

    // Inject artifact card
    if (this.cardInjector) {
      const artifactCard = {
        card_type: 'artifact',
        status: 'new',
        icon: 'FileText',
        title: 'הנחיות צילום מוכנות! 📋',
        subtitle: 'לחץ לצפייה בהנחיות מותאמות אישית',
        action: 'view_guidelines',
        color: 'green'
      };

      this.cardInjector(artifactCard);
    }
  }

  /**
   * Inject context card based on hint
   */
  injectContextCard(hint) {
    if (!this.cardInjector) return;

    const cardMap = {
      conversation_depth_card: {
        card_type: 'progress',
        status: 'processing',
        icon: 'MessageCircle',
        title: 'השיחה מתעמקת',
        subtitle: 'נושאים: שפה, חוזקות, דאגות',
        color: 'cyan'
      },
      guidelines_offer_card: {
        card_type: 'instruction',
        status: 'instruction',
        icon: 'Lightbulb',
        title: 'הנחיות צילום זמינות',
        subtitle: 'מותאם אישית עבור דניאל',
        color: 'indigo'
      }
    };

    const card = cardMap[hint];
    if (card) {
      this.cardInjector(card);
    }
  }

  /**
   * Complete demo
   */
  complete() {
    console.log('🎭 Demo completed!');
    this.paused = true;
    this.updateBanner();

    // Show completion message
    if (this.messageInjector) {
      this.messageInjector({
        sender: 'chitta',
        text: 'זה היה הדמו! ראית את כל התהליך - מראיון ועד להנחיות מותאמות. רוצה להתחיל שיחה אמיתית? 💙',
        timestamp: new Date().toISOString()
      });
    }
  }

  /**
   * Speed control
   */
  setSpeed(multiplier) {
    console.log(`🎭 Speed changed: ${this.speed}x -> ${multiplier}x`);
    this.speed = multiplier;
    this.updateBanner();
  }

  /**
   * Pause demo
   */
  pause() {
    console.log('🎭 Paused');
    this.paused = true;
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
    }
    this.updateBanner();
  }

  /**
   * Resume demo
   */
  resume() {
    console.log('🎭 Resumed');
    this.paused = false;
    this.updateBanner();
    this.playNext();
  }

  /**
   * Skip to next step immediately
   */
  skip() {
    console.log('🎭 Skipping to next step');
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
    }
    this.playNext();
  }

  /**
   * Stop demo completely
   */
  stop() {
    console.log('🎭 Stopping demo');
    this.active = false;
    this.paused = false;
    this.currentStep = -1;

    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
    }

    this.removeBanner();

    // Notify app
    if (this.messageInjector) {
      this.messageInjector({
        sender: 'chitta',
        text: 'הדמו הופסק. מוכנה להתחיל את השיחה האמיתית שלך! 💙',
        timestamp: new Date().toISOString()
      });
    }
  }

  /**
   * Create banner portal
   */
  createBanner() {
    // Create portal container if it doesn't exist
    if (!document.getElementById('demo-banner-root')) {
      const portal = document.createElement('div');
      portal.id = 'demo-banner-root';
      document.body.appendChild(portal);
    }

    this.bannerContainer = document.getElementById('demo-banner-root');
    this.updateBanner();
  }

  /**
   * Update banner with current state
   */
  updateBanner() {
    if (!this.bannerContainer || !this.scenario) return;

    const progress = Math.round((this.currentStep / this.scenario.messages.length) * 100);
    const isComplete = this.currentStep >= this.scenario.messages.length;

    ReactDOM.render(
      <DemoBannerPortal
        step={this.currentStep + 1}
        total={this.scenario.messages.length}
        progress={progress}
        speed={this.speed}
        paused={this.paused}
        isComplete={isComplete}
        scenarioName={this.scenario.name}
        onSpeedChange={(s) => this.setSpeed(s)}
        onPause={() => this.pause()}
        onResume={() => this.resume()}
        onSkip={() => this.skip()}
        onStop={() => this.stop()}
      />,
      this.bannerContainer
    );
  }

  /**
   * Remove banner
   */
  removeBanner() {
    if (this.bannerContainer) {
      ReactDOM.unmountComponentAtNode(this.bannerContainer);
      this.bannerContainer.remove();
      this.bannerContainer = null;
    }
  }

  /**
   * Get demo scenario data
   */
  getScenario() {
    return {
      scenario_id: 'language_concerns',
      name: 'דאגות שפה',
      name_en: 'Language Development Concerns',
      description: 'הדגמה של שיחה עם הורה לילד עם דאגות שפה',
      duration_estimate: '2-3 דקות',
      child_profile: {
        child_name: 'דניאל',
        age: 3.5,
        gender: 'male',
        primary_concerns: ['שפה', 'תקשורת'],
        strengths: 'ממוקד, יצירתי, משחק יפה אחד על אחד'
      },
      messages: [
        // Message 0: Chitta greets (already shown in app)
        {
          role: 'assistant',
          content: 'שלום! אני צ\'יטה 💙\n\nנעים להכיר אותך! אני כאן כדי להכיר את הילד/ה שלך ולהבין איך אפשר לעזור. נשוחח קצת יחד, ואז נמשיך לשלבים הבאים.\n\nבואי נתחיל - מה שם הילד/ה שלך ובן/בת כמה?',
          delay_ms: 0
        },
        // Message 1: Parent shares name and age
        {
          role: 'user',
          content: 'שמו דניאל, הוא בן 3 וחצי',
          delay_ms: 3000
        },
        // Message 2: Chitta starts with STRENGTHS
        {
          role: 'assistant',
          content: 'נעים להכיר את דניאל! לפני שנדבר על אתגרים, בואי נתחיל מהדברים הטובים. במה דניאל אוהב לעסוק? מה הוא עושה טוב?',
          delay_ms: 2500
        },
        // Message 3: Parent shares strengths
        {
          role: 'user',
          content: 'הוא מאוד אוהב לשחק עם קוביות ולבנות מגדלים. הוא ממוקד ויצירתי. וגם משחק יפה עם ילד אחד.',
          delay_ms: 3500
        },
        // Message 4: Chitta acknowledges and asks about concerns
        {
          role: 'assistant',
          content: 'נשמע שדניאל יצירתי וממוקד - זה נפלא! עכשיו ספרי לי, מה הביא אותך אלינו? מה מדאיג אותך לגבי דניאל?',
          delay_ms: 2500,
          card_hint: 'conversation_depth_card'
        },
        // Message 5: Parent shares main concern
        {
          role: 'user',
          content: 'יש לי דאגות לגבי הדיבור שלו. הוא מדבר הרבה פחות מילדים אחרים בגיל שלו.',
          delay_ms: 4000
        },
        // Message 6: Chitta asks for specific example
        {
          role: 'assistant',
          content: 'אני שומעת. תני לי דוגמה ספציפית - מה קורה בדיוק? איך הוא מתקשר איתך?',
          delay_ms: 2500
        },
        // Message 7: Parent gives specific details
        {
          role: 'user',
          content: 'הוא משתמש במילים בודדות, קשה לו לבנות משפטים. למשל אומר "מים" במקום "אני רוצה מים". ובגן הוא שקט, לא משתתף בפעילויות.',
          delay_ms: 4500
        },
        // Message 8: Chitta explores context
        {
          role: 'assistant',
          content: 'אני מבינה. ואיך זה משפיע על היום יום שלכם? איך אתם מתמודדים עם זה?',
          delay_ms: 2500
        },
        // Message 9: Parent shares family context
        {
          role: 'user',
          content: 'זה מתסכל לפעמים. יש לו אח קטן שנולד לפני שנה, ולפעמים קשה לי לדעת מה דניאל צריך.',
          delay_ms: 4000
        },
        // Message 10: Chitta asks about goals
        {
          role: 'assistant',
          content: 'זה מאתגר. ספרי לי - מה הייתם רוצים לראות מתקדם? מה חשוב לכם?',
          delay_ms: 2500
        },
        // Message 11: Parent shares goals - TRIGGERS ARTIFACT
        {
          role: 'user',
          content: 'אני רוצה לעזור לו להרגיש בטוח בתקשורת. שיוכל להתבטא טוב יותר ולהצליח בגן.',
          delay_ms: 3500,
          trigger_artifact: 'baseline_video_guidelines'
        },
        // Message 12: Chitta acknowledges and offers guidelines
        {
          role: 'assistant',
          content: 'תודה שספרת לי על דניאל. אני מרגישה שיש לי תמונה עשירה שלו - החוזקות שלו, האתגרים, והמטרות שלכם. אני יכולה להכין עבורך הנחיות צילום מותאמות אישית שיעזרו לי להבין את דניאל טוב יותר. רוצה לראות אותן?',
          delay_ms: 3000,
          card_hint: 'guidelines_offer_card'
        },
        // Message 13: Parent accepts
        {
          role: 'user',
          content: 'כן, בטח!',
          delay_ms: 2000
        },
        // Message 14: Chitta confirms guidelines are ready
        {
          role: 'assistant',
          content: 'מעולה! ההנחיות מוכנות 📋 תראי אותן בכרטיס למטה. הן מותאמות במיוחד לדניאל - 3 מצבים שיעזרו לי לראות את התקשורת שלו. קחי את הזמן שצריך, אין לחץ 💙',
          delay_ms: 2500
        }
      ]
    };
  }
}

// Singleton instance
export const demoOrchestrator = new DemoOrchestrator();
