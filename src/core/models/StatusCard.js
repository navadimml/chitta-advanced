/**
 * StatusCard - Represents a status card in the contextual surface
 *
 * Status cards provide quick visual feedback about the journey state
 * and allow users to take actions via click handlers.
 *
 * Card types represent different states:
 * - completed: Something was finished
 * - pending: Waiting for action
 * - action: User action needed
 * - processing: System is working
 * - info: Informational status
 * - warning: Needs attention
 * - error: Something went wrong
 * - success: Positive outcome
 * - milestone: Important achievement
 * - metric: Progress or statistic
 */

export class StatusCard {
  constructor(config = {}) {
    this.id = config.id || this._generateId();
    this.type = config.type || 'info'; // Maps to styling
    this.title = config.title;
    this.subtitle = config.subtitle;
    this.icon = config.icon; // Lucide icon name
    this.badge = config.badge; // Optional badge text

    // Action configuration
    this.action = config.action; // What happens on click
    this.clickable = config.clickable !== undefined ? config.clickable : !!config.action;

    // Visual options
    this.variant = config.variant || 'default'; // 'default', 'compact', 'detailed'
    this.priority = config.priority || 0; // Higher = more important, shown first

    // Context
    this.journeyId = config.journeyId;
    this.stageId = config.stageId;
    this.entityId = config.entityId;

    // Metadata
    this.metadata = config.metadata || {};
    this.createdAt = config.createdAt || new Date().toISOString();
    this.expiresAt = config.expiresAt; // Optional expiration time
  }

  /**
   * Check if card is expired
   */
  isExpired() {
    if (!this.expiresAt) return false;
    return new Date(this.expiresAt) < new Date();
  }

  /**
   * Get Tailwind CSS classes for styling based on type
   */
  getStyleClasses() {
    const typeClasses = {
      completed: 'bg-green-100 border-green-300 text-green-800',
      pending: 'bg-amber-100 border-amber-300 text-amber-800',
      action: 'bg-blue-100 border-blue-300 text-blue-800',
      processing: 'bg-purple-100 border-purple-300 text-purple-800',
      info: 'bg-gray-100 border-gray-300 text-gray-800',
      warning: 'bg-orange-100 border-orange-300 text-orange-800',
      error: 'bg-red-100 border-red-300 text-red-800',
      success: 'bg-emerald-100 border-emerald-300 text-emerald-800',
      milestone: 'bg-indigo-100 border-indigo-300 text-indigo-800',
      metric: 'bg-cyan-100 border-cyan-300 text-cyan-800'
    };

    return typeClasses[this.type] || typeClasses.info;
  }

  /**
   * Get icon color class
   */
  getIconColorClass() {
    const iconColors = {
      completed: 'text-green-600',
      pending: 'text-amber-600',
      action: 'text-blue-600',
      processing: 'text-purple-600',
      info: 'text-gray-600',
      warning: 'text-orange-600',
      error: 'text-red-600',
      success: 'text-emerald-600',
      milestone: 'text-indigo-600',
      metric: 'text-cyan-600'
    };

    return iconColors[this.type] || iconColors.info;
  }

  /**
   * Execute the card's action
   */
  executeAction() {
    if (!this.action) return null;

    return {
      type: this.action.type,
      payload: this.action.payload || {},
      cardId: this.id
    };
  }

  /**
   * Create action for opening a deep view
   */
  static createDeepViewAction(viewName, params = {}) {
    return {
      type: 'open_deep_view',
      payload: { view: viewName, params }
    };
  }

  /**
   * Create action for sending a message
   */
  static createMessageAction(message) {
    return {
      type: 'send_message',
      payload: { message }
    };
  }

  /**
   * Create action for navigation
   */
  static createNavigationAction(target, params = {}) {
    return {
      type: 'navigate',
      payload: { target, params }
    };
  }

  /**
   * Create action for triggering a workflow step
   */
  static createWorkflowAction(stepId, params = {}) {
    return {
      type: 'workflow_action',
      payload: { stepId, params }
    };
  }

  /**
   * Serialize to JSON
   */
  toJSON() {
    return {
      id: this.id,
      type: this.type,
      title: this.title,
      subtitle: this.subtitle,
      icon: this.icon,
      badge: this.badge,
      action: this.action,
      clickable: this.clickable,
      variant: this.variant,
      priority: this.priority,
      journeyId: this.journeyId,
      stageId: this.stageId,
      entityId: this.entityId,
      metadata: this.metadata,
      createdAt: this.createdAt,
      expiresAt: this.expiresAt
    };
  }

  /**
   * Create from JSON
   */
  static fromJSON(json) {
    return new StatusCard(json);
  }

  /**
   * Generate unique ID
   */
  _generateId() {
    return `card_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
  }
}

export default StatusCard;
