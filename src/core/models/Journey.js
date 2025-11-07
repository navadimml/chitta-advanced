/**
 * Journey - Represents an entity's progress through a workflow
 *
 * A Journey tracks:
 * - Which entity is going through the workflow
 * - What workflow they're following
 * - Current stage in the workflow
 * - Progress metrics
 * - Collected artifacts (documents, media, data)
 * - History of interactions
 */

export class Journey {
  constructor(config = {}) {
    this.id = config.id || this._generateId();
    this.entityId = config.entityId;
    this.workflowId = config.workflowId;
    this.currentStageId = config.currentStageId || null;
    this.status = config.status || 'active'; // 'active', 'completed', 'paused', 'cancelled'

    // Stage progress tracking
    this.completedStages = config.completedStages || [];
    this.stageData = config.stageData || {}; // Data collected at each stage

    // Progress metrics
    this.progress = config.progress || {
      percentage: 0,
      completedSteps: 0,
      totalSteps: 0
    };

    // Artifacts collected during journey
    this.artifacts = config.artifacts || [];

    // Interaction history
    this.messages = config.messages || [];
    this.actions = config.actions || [];

    // Metadata
    this.metadata = config.metadata || {};
    this.startedAt = config.startedAt || new Date().toISOString();
    this.completedAt = config.completedAt || null;
    this.updatedAt = config.updatedAt || new Date().toISOString();
  }

  /**
   * Check if journey is at a specific stage
   */
  isAtStage(stageId) {
    return this.currentStageId === stageId;
  }

  /**
   * Check if stage has been completed
   */
  hasCompletedStage(stageId) {
    return this.completedStages.includes(stageId);
  }

  /**
   * Mark current stage as complete and advance
   */
  completeCurrentStage(nextStageId) {
    if (this.currentStageId && !this.hasCompletedStage(this.currentStageId)) {
      this.completedStages.push(this.currentStageId);
    }
    this.currentStageId = nextStageId;
    this.updatedAt = new Date().toISOString();
    return this;
  }

  /**
   * Add artifact to journey
   */
  addArtifact(artifact) {
    this.artifacts.push(artifact);
    this.updatedAt = new Date().toISOString();
    return this;
  }

  /**
   * Get artifacts by type
   */
  getArtifactsByType(type) {
    return this.artifacts.filter(artifact => artifact.type === type);
  }

  /**
   * Get artifacts by category
   */
  getArtifactsByCategory(category) {
    return this.artifacts.filter(artifact => artifact.category === category);
  }

  /**
   * Add message to history
   */
  addMessage(message) {
    this.messages.push({
      ...message,
      timestamp: message.timestamp || new Date().toISOString()
    });
    this.updatedAt = new Date().toISOString();
    return this;
  }

  /**
   * Add action to history
   */
  addAction(action) {
    this.actions.push({
      ...action,
      timestamp: action.timestamp || new Date().toISOString()
    });
    this.updatedAt = new Date().toISOString();
    return this;
  }

  /**
   * Update progress metrics
   */
  updateProgress(progress) {
    this.progress = { ...this.progress, ...progress };
    this.updatedAt = new Date().toISOString();
    return this;
  }

  /**
   * Store data for a specific stage
   */
  setStageData(stageId, data) {
    this.stageData[stageId] = {
      ...(this.stageData[stageId] || {}),
      ...data
    };
    this.updatedAt = new Date().toISOString();
    return this;
  }

  /**
   * Get data for a specific stage
   */
  getStageData(stageId) {
    return this.stageData[stageId] || {};
  }

  /**
   * Mark journey as complete
   */
  complete() {
    this.status = 'completed';
    this.completedAt = new Date().toISOString();
    this.updatedAt = new Date().toISOString();
    return this;
  }

  /**
   * Calculate overall progress percentage
   */
  calculateProgress(totalStages) {
    const completed = this.completedStages.length;
    const percentage = totalStages > 0 ? (completed / totalStages) * 100 : 0;
    return Math.round(percentage);
  }

  /**
   * Serialize to JSON
   */
  toJSON() {
    return {
      id: this.id,
      entityId: this.entityId,
      workflowId: this.workflowId,
      currentStageId: this.currentStageId,
      status: this.status,
      completedStages: this.completedStages,
      stageData: this.stageData,
      progress: this.progress,
      artifacts: this.artifacts,
      messages: this.messages,
      actions: this.actions,
      metadata: this.metadata,
      startedAt: this.startedAt,
      completedAt: this.completedAt,
      updatedAt: this.updatedAt
    };
  }

  /**
   * Create from JSON
   */
  static fromJSON(json) {
    return new Journey(json);
  }

  /**
   * Generate unique ID
   */
  _generateId() {
    return `journey_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
  }
}

export default Journey;
