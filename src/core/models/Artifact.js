/**
 * Artifact - Generic artifact (document, media, data) attached to a journey
 *
 * Artifacts represent any type of content collected during a workflow:
 * - Documents (PDFs, Word docs, images)
 * - Media (videos, audio recordings)
 * - Data (structured information, form responses)
 * - External references (URLs, IDs)
 *
 * Examples by domain:
 * - Child Development: diagnostic reports, behavioral videos, assessment data
 * - Healthcare: medical records, lab results, x-rays
 * - Education: transcripts, recommendation letters, essays
 * - Legal: contracts, evidence documents, case files
 */

export class Artifact {
  constructor(config = {}) {
    this.id = config.id || this._generateId();
    this.type = config.type; // 'document', 'video', 'image', 'audio', 'data', 'link'
    this.category = config.category; // Domain-specific categorization
    this.name = config.name;
    this.description = config.description;

    // Content
    this.content = config.content; // File data, URL, or structured data
    this.url = config.url; // URL if stored externally
    this.format = config.format; // File extension or MIME type

    // Size and validation
    this.size = config.size; // Size in bytes
    this.checksum = config.checksum; // For integrity validation

    // Processing status
    this.status = config.status || 'pending'; // 'pending', 'processing', 'ready', 'error'
    this.processingResult = config.processingResult; // Results of analysis/processing

    // Relationships
    this.journeyId = config.journeyId;
    this.stageId = config.stageId; // Stage where artifact was collected
    this.entityId = config.entityId;

    // Metadata
    this.metadata = config.metadata || {};
    this.tags = config.tags || [];

    // Timestamps
    this.uploadedAt = config.uploadedAt || new Date().toISOString();
    this.processedAt = config.processedAt;
    this.updatedAt = config.updatedAt || new Date().toISOString();
  }

  /**
   * Check if artifact is a document
   */
  isDocument() {
    return this.type === 'document';
  }

  /**
   * Check if artifact is media (video/audio/image)
   */
  isMedia() {
    return ['video', 'audio', 'image'].includes(this.type);
  }

  /**
   * Check if artifact is structured data
   */
  isData() {
    return this.type === 'data';
  }

  /**
   * Check if artifact is ready for use
   */
  isReady() {
    return this.status === 'ready';
  }

  /**
   * Mark artifact as processing
   */
  markProcessing() {
    this.status = 'processing';
    this.updatedAt = new Date().toISOString();
    return this;
  }

  /**
   * Mark artifact as ready
   */
  markReady(processingResult = null) {
    this.status = 'ready';
    this.processedAt = new Date().toISOString();
    this.updatedAt = new Date().toISOString();
    if (processingResult) {
      this.processingResult = processingResult;
    }
    return this;
  }

  /**
   * Mark artifact as error
   */
  markError(error) {
    this.status = 'error';
    this.metadata.error = error;
    this.updatedAt = new Date().toISOString();
    return this;
  }

  /**
   * Add tag
   */
  addTag(tag) {
    if (!this.tags.includes(tag)) {
      this.tags.push(tag);
      this.updatedAt = new Date().toISOString();
    }
    return this;
  }

  /**
   * Remove tag
   */
  removeTag(tag) {
    this.tags = this.tags.filter(t => t !== tag);
    this.updatedAt = new Date().toISOString();
    return this;
  }

  /**
   * Check if artifact has tag
   */
  hasTag(tag) {
    return this.tags.includes(tag);
  }

  /**
   * Get file size in human-readable format
   */
  getFormattedSize() {
    if (!this.size) return 'Unknown';

    const units = ['B', 'KB', 'MB', 'GB'];
    let size = this.size;
    let unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }

    return `${size.toFixed(2)} ${units[unitIndex]}`;
  }

  /**
   * Get display name
   */
  getDisplayName() {
    return this.name || `${this.type}_${this.id}`;
  }

  /**
   * Serialize to JSON
   */
  toJSON() {
    return {
      id: this.id,
      type: this.type,
      category: this.category,
      name: this.name,
      description: this.description,
      content: this.content,
      url: this.url,
      format: this.format,
      size: this.size,
      checksum: this.checksum,
      status: this.status,
      processingResult: this.processingResult,
      journeyId: this.journeyId,
      stageId: this.stageId,
      entityId: this.entityId,
      metadata: this.metadata,
      tags: this.tags,
      uploadedAt: this.uploadedAt,
      processedAt: this.processedAt,
      updatedAt: this.updatedAt
    };
  }

  /**
   * Create from JSON
   */
  static fromJSON(json) {
    return new Artifact(json);
  }

  /**
   * Generate unique ID
   */
  _generateId() {
    return `artifact_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
  }
}

export default Artifact;
