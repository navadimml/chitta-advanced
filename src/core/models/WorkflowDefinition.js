/**
 * WorkflowDefinition - Defines the structure of a multi-stage workflow
 *
 * A workflow consists of:
 * - Stages that entities progress through
 * - Transitions rules between stages
 * - Completion criteria for each stage
 * - Required artifacts and data
 *
 * Examples:
 * - Child Development: interview → consultation → video upload → report
 * - Patient Intake: registration → triage → scheduling → treatment
 * - Student Onboarding: application → interview → enrollment → orientation
 */

export class WorkflowDefinition {
  constructor(config = {}) {
    this.id = config.id;
    this.name = config.name;
    this.description = config.description;
    this.version = config.version || '1.0.0';

    // Entity configuration
    this.entitySchema = config.entitySchema || {
      type: 'entity',
      requiredAttributes: [],
      optionalAttributes: []
    };

    // Stages
    this.stages = config.stages || [];
    this.initialStageId = config.initialStageId || (this.stages[0]?.id);

    // Transitions
    this.transitions = config.transitions || this._inferTransitions();

    // Artifact types allowed in this workflow
    this.artifactTypes = config.artifactTypes || [];

    // Status card templates
    this.statusCardTemplates = config.statusCardTemplates || {};

    // Suggestion templates
    this.suggestionTemplates = config.suggestionTemplates || {};

    // Metadata
    this.metadata = config.metadata || {};
  }

  /**
   * Get stage by ID
   */
  getStage(stageId) {
    return this.stages.find(stage => stage.id === stageId);
  }

  /**
   * Get initial stage
   */
  getInitialStage() {
    return this.getStage(this.initialStageId);
  }

  /**
   * Get stages that can follow the given stage
   */
  getNextStages(stageId) {
    const stage = this.getStage(stageId);
    return stage?.nextStages || [];
  }

  /**
   * Check if transition from one stage to another is valid
   */
  canTransition(fromStageId, toStageId) {
    const nextStages = this.getNextStages(fromStageId);
    return nextStages.includes(toStageId);
  }

  /**
   * Get all stages that must be completed before a given stage
   */
  getPrerequisiteStages(stageId) {
    const stage = this.getStage(stageId);
    return stage?.prerequisites || [];
  }

  /**
   * Check if all prerequisites are met for a stage
   */
  arePrerequisitesMet(stageId, completedStages) {
    const prerequisites = this.getPrerequisiteStages(stageId);
    return prerequisites.every(prereqId => completedStages.includes(prereqId));
  }

  /**
   * Get artifact type definition
   */
  getArtifactType(artifactTypeId) {
    return this.artifactTypes.find(type => type.id === artifactTypeId);
  }

  /**
   * Get status card template
   */
  getStatusCardTemplate(templateId) {
    return this.statusCardTemplates[templateId];
  }

  /**
   * Get suggestion templates for a stage
   */
  getSuggestionTemplates(stageId) {
    return this.suggestionTemplates[stageId] || [];
  }

  /**
   * Validate entity against schema
   */
  validateEntity(entity) {
    const errors = [];

    // Check type
    if (entity.type !== this.entitySchema.type) {
      errors.push(`Entity type must be '${this.entitySchema.type}', got '${entity.type}'`);
    }

    // Check required attributes
    this.entitySchema.requiredAttributes?.forEach(attr => {
      if (!entity.attributes[attr]) {
        errors.push(`Missing required attribute: ${attr}`);
      }
    });

    return {
      valid: errors.length === 0,
      errors
    };
  }

  /**
   * Infer transitions from stages' nextStages arrays
   */
  _inferTransitions() {
    const transitions = [];
    this.stages.forEach(stage => {
      if (stage.nextStages) {
        stage.nextStages.forEach(nextStageId => {
          transitions.push({
            from: stage.id,
            to: nextStageId,
            condition: null
          });
        });
      }
    });
    return transitions;
  }

  /**
   * Serialize to JSON
   */
  toJSON() {
    return {
      id: this.id,
      name: this.name,
      description: this.description,
      version: this.version,
      entitySchema: this.entitySchema,
      stages: this.stages,
      initialStageId: this.initialStageId,
      transitions: this.transitions,
      artifactTypes: this.artifactTypes,
      statusCardTemplates: this.statusCardTemplates,
      suggestionTemplates: this.suggestionTemplates,
      metadata: this.metadata
    };
  }

  /**
   * Create from JSON (used when loading from configuration files)
   */
  static fromJSON(json) {
    return new WorkflowDefinition(json);
  }
}

export default WorkflowDefinition;
