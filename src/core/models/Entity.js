/**
 * Entity - Generic entity being tracked through a workflow
 *
 * This is the core abstraction that replaces domain-specific concepts like:
 * - Child (in child development domain)
 * - Patient (in healthcare domain)
 * - Student (in education domain)
 * - Customer (in customer service domain)
 * - Legal Case (in legal consulting domain)
 *
 * An Entity is anything that goes through a journey/workflow.
 */

export class Entity {
  constructor(config = {}) {
    this.id = config.id || this._generateId();
    this.type = config.type; // Defined by domain (e.g., 'child', 'patient', 'student')
    this.attributes = config.attributes || {}; // Flexible key-value store
    this.metadata = config.metadata || {};
    this.createdAt = config.createdAt || new Date().toISOString();
    this.updatedAt = config.updatedAt || new Date().toISOString();
  }

  /**
   * Get attribute value by key
   */
  getAttribute(key, defaultValue = null) {
    return this.attributes[key] !== undefined ? this.attributes[key] : defaultValue;
  }

  /**
   * Set attribute value
   */
  setAttribute(key, value) {
    this.attributes[key] = value;
    this.updatedAt = new Date().toISOString();
    return this;
  }

  /**
   * Set multiple attributes at once
   */
  setAttributes(attributes) {
    this.attributes = { ...this.attributes, ...attributes };
    this.updatedAt = new Date().toISOString();
    return this;
  }

  /**
   * Check if entity has required attributes
   */
  hasRequiredAttributes(requiredKeys) {
    return requiredKeys.every(key => this.attributes[key] !== undefined);
  }

  /**
   * Get entity display name (uses domain-specific logic)
   */
  getDisplayName() {
    // Common patterns for display names
    if (this.attributes.name) return this.attributes.name;
    if (this.attributes.full_name) return this.attributes.full_name;
    if (this.attributes.title) return this.attributes.title;
    return `${this.type} ${this.id}`;
  }

  /**
   * Serialize to JSON
   */
  toJSON() {
    return {
      id: this.id,
      type: this.type,
      attributes: this.attributes,
      metadata: this.metadata,
      createdAt: this.createdAt,
      updatedAt: this.updatedAt
    };
  }

  /**
   * Create from JSON
   */
  static fromJSON(json) {
    return new Entity(json);
  }

  /**
   * Generate unique ID
   */
  _generateId() {
    return `entity_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
  }
}

export default Entity;
