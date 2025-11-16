// JourneyEngine.js - Single source of truth for state management and persistence

class JourneyEngine {
  constructor(config) {
    this.config = config;
    this.state = this.loadState() || this.getInitialState();
    this.listeners = [];

    // Auto-save on every change
    this.subscribe(() => this.saveState());
  }

  // ===== STATE MANAGEMENT =====

  getInitialState() {
    return {
      // Journey position
      currentStage: this.config.stages[0].id,
      completedStages: [],

      // Collected data (grows over time)
      data: {},

      // UI state
      ui: {
        draftMessage: '',
        messages: [],
        lastActivity: Date.now()
      },

      // Metadata
      meta: {
        sessionId: this.generateId(),
        firstVisit: Date.now(),
        lastSeen: Date.now(),
        isReturning: false,
        hasSeenOnboarding: false
      }
    };
  }

  getState() {
    return this.state;
  }

  setState(newState) {
    this.state = newState;
    this.notifyListeners();
  }

  updateState(updates) {
    this.state = { ...this.state, ...updates };
    this.state.meta.lastSeen = Date.now();
    this.state.ui.lastActivity = Date.now();
    this.notifyListeners();
  }

  // Update nested properties
  updateNested(path, value) {
    const keys = path.split('.');
    const newState = JSON.parse(JSON.stringify(this.state)); // Deep clone
    let current = newState;

    for (let i = 0; i < keys.length - 1; i++) {
      if (!current[keys[i]]) {
        current[keys[i]] = {};
      }
      current = current[keys[i]];
    }

    current[keys[keys.length - 1]] = value;
    this.state = newState;
    this.state.meta.lastSeen = Date.now();
    this.state.ui.lastActivity = Date.now();
    this.notifyListeners();
  }

  // ===== STAGE MANAGEMENT =====

  getCurrentStage() {
    return this.config.stages.find(s => s.id === this.state.currentStage);
  }

  canTransitionTo(stageId) {
    const currentStage = this.getCurrentStage();
    if (!currentStage) return false;

    // Allow transition if it's the nextStage or in validTransitions array
    return currentStage.nextStage === stageId ||
           (currentStage.validTransitions && currentStage.validTransitions.includes(stageId));
  }

  async transitionTo(stageId) {
    if (!this.canTransitionTo(stageId)) {
      console.warn(`Invalid transition from ${this.state.currentStage} to ${stageId}`);
      return false;
    }

    const oldStage = this.getCurrentStage();

    // Exit current stage
    if (oldStage && oldStage.onExit) {
      await oldStage.onExit(this);
    }

    // Update state
    this.updateState({
      currentStage: stageId,
      completedStages: [...this.state.completedStages, oldStage.id]
    });

    // Enter new stage
    const newStage = this.getCurrentStage();
    if (newStage && newStage.onEnter) {
      await newStage.onEnter(this);
    }

    return true;
  }

  // Check if current stage is complete
  isStageComplete() {
    const stage = this.getCurrentStage();

    if (!stage || !stage.completion) {
      return false;
    }

    return this.checkCompletion(stage.completion);
  }

  checkCompletion(criteria) {
    // Generic completion checking
    if (criteria.minTopics) {
      const topics = criteria.minTopics.filter(topic => {
        const value = this.state.data[topic];
        return value !== undefined && value !== null && value !== '';
      });
      return topics.length >= criteria.minTopics.length;
    }

    if (criteria.fileCount) {
      return (this.state.data.uploadedFiles?.length || 0) >= criteria.fileCount;
    }

    if (criteria.custom) {
      return criteria.custom(this.state);
    }

    return false;
  }

  // ===== DATA MANAGEMENT =====

  updateData(key, value) {
    this.updateState({
      data: {
        ...this.state.data,
        [key]: value
      }
    });
  }

  getData(key) {
    return this.state.data[key];
  }

  // ===== PERSISTENCE =====

  saveState() {
    try {
      localStorage.setItem('journey_state', JSON.stringify(this.state));
    } catch (error) {
      console.error('Failed to save state:', error);
    }
  }

  loadState() {
    try {
      const saved = localStorage.getItem('journey_state');
      if (saved) {
        const state = JSON.parse(saved);

        // Mark as returning user if away for more than 30 minutes
        const timeAway = Date.now() - state.meta.lastSeen;
        state.meta.isReturning = timeAway > 30 * 60 * 1000; // 30 min
        state.meta.timeAway = timeAway;
        state.meta.lastSeen = Date.now();

        return state;
      }
    } catch (error) {
      console.error('Failed to load state:', error);
    }
    return null;
  }

  // ===== SUBSCRIPTION =====

  subscribe(listener) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  notifyListeners() {
    this.listeners.forEach(listener => {
      try {
        listener(this.state);
      } catch (error) {
        console.error('Listener error:', error);
      }
    });
  }

  // ===== RESET =====

  reset() {
    localStorage.removeItem('journey_state');
    this.state = this.getInitialState();
    this.notifyListeners();
  }

  // ===== UTILITIES =====

  generateId() {
    return `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}

export default JourneyEngine;
