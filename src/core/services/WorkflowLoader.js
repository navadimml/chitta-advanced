/**
 * WorkflowLoader - Loads workflow definitions from configuration files
 *
 * This service reads workflow configuration files (JSON/YAML) and creates
 * WorkflowDefinition objects that can be used by the framework.
 *
 * Configuration files should be placed in: config/workflows/
 */

import { WorkflowDefinition } from '../models/WorkflowDefinition.js';

export class WorkflowLoader {
  constructor() {
    this.workflows = new Map();
    this.activeWorkflowId = null;
  }

  /**
   * Load workflow from configuration object
   */
  loadWorkflow(config) {
    const workflow = WorkflowDefinition.fromJSON(config);
    this.workflows.set(workflow.id, workflow);
    return workflow;
  }

  /**
   * Load workflow from JSON file
   */
  async loadWorkflowFromFile(filePath) {
    try {
      const response = await fetch(filePath);
      if (!response.ok) {
        throw new Error(`Failed to load workflow from ${filePath}: ${response.statusText}`);
      }
      const config = await response.json();
      return this.loadWorkflow(config);
    } catch (error) {
      console.error(`Error loading workflow from ${filePath}:`, error);
      throw error;
    }
  }

  /**
   * Load multiple workflows from a directory
   */
  async loadWorkflowsFromDirectory(directoryPath, workflowFiles) {
    const workflows = [];
    for (const file of workflowFiles) {
      const filePath = `${directoryPath}/${file}`;
      try {
        const workflow = await this.loadWorkflowFromFile(filePath);
        workflows.push(workflow);
      } catch (error) {
        console.error(`Failed to load workflow from ${file}:`, error);
      }
    }
    return workflows;
  }

  /**
   * Get workflow by ID
   */
  getWorkflow(workflowId) {
    return this.workflows.get(workflowId);
  }

  /**
   * Get all loaded workflows
   */
  getAllWorkflows() {
    return Array.from(this.workflows.values());
  }

  /**
   * Set active workflow
   */
  setActiveWorkflow(workflowId) {
    if (!this.workflows.has(workflowId)) {
      throw new Error(`Workflow not found: ${workflowId}`);
    }
    this.activeWorkflowId = workflowId;
    return this.getActiveWorkflow();
  }

  /**
   * Get active workflow
   */
  getActiveWorkflow() {
    if (!this.activeWorkflowId) {
      // Return first workflow if none is active
      const workflows = this.getAllWorkflows();
      return workflows.length > 0 ? workflows[0] : null;
    }
    return this.getWorkflow(this.activeWorkflowId);
  }

  /**
   * Check if workflow is loaded
   */
  hasWorkflow(workflowId) {
    return this.workflows.has(workflowId);
  }

  /**
   * Unload workflow
   */
  unloadWorkflow(workflowId) {
    const removed = this.workflows.delete(workflowId);
    if (removed && this.activeWorkflowId === workflowId) {
      this.activeWorkflowId = null;
    }
    return removed;
  }

  /**
   * Reload workflow (useful for development)
   */
  async reloadWorkflow(workflowId) {
    const workflow = this.getWorkflow(workflowId);
    if (!workflow) {
      throw new Error(`Workflow not found: ${workflowId}`);
    }

    // You would need to store the original file path for this to work
    // This is a simplified version
    const filePath = workflow.metadata?.filePath;
    if (filePath) {
      this.unloadWorkflow(workflowId);
      return await this.loadWorkflowFromFile(filePath);
    }

    throw new Error('Cannot reload workflow: original file path not stored');
  }

  /**
   * Validate workflow configuration
   */
  validateWorkflow(workflow) {
    const errors = [];

    // Check required fields
    if (!workflow.id) errors.push('Workflow ID is required');
    if (!workflow.name) errors.push('Workflow name is required');
    if (!workflow.stages || workflow.stages.length === 0) {
      errors.push('Workflow must have at least one stage');
    }

    // Check entity schema
    if (!workflow.entitySchema?.type) {
      errors.push('Entity schema must specify a type');
    }

    // Check stage references
    workflow.stages?.forEach(stage => {
      if (!stage.id) {
        errors.push(`Stage at position ${stage.order} is missing an ID`);
      }

      // Check that nextStages references exist
      stage.nextStages?.forEach(nextStageId => {
        const stageExists = workflow.stages.some(s => s.id === nextStageId);
        if (!stageExists) {
          errors.push(`Stage '${stage.id}' references non-existent next stage: ${nextStageId}`);
        }
      });

      // Check that prerequisites exist
      stage.prerequisites?.forEach(prereqId => {
        const stageExists = workflow.stages.some(s => s.id === prereqId);
        if (!stageExists) {
          errors.push(`Stage '${stage.id}' references non-existent prerequisite: ${prereqId}`);
        }
      });
    });

    // Check artifact type references
    workflow.stages?.forEach(stage => {
      stage.completionCriteria?.artifactTypes?.forEach(artifactTypeId => {
        const typeExists = workflow.artifactTypes?.some(t => t.id === artifactTypeId);
        if (!typeExists) {
          errors.push(`Stage '${stage.id}' references non-existent artifact type: ${artifactTypeId}`);
        }
      });
    });

    return {
      valid: errors.length === 0,
      errors
    };
  }

  /**
   * Get workflow statistics
   */
  getWorkflowStats(workflowId) {
    const workflow = this.getWorkflow(workflowId);
    if (!workflow) return null;

    return {
      id: workflow.id,
      name: workflow.name,
      version: workflow.version,
      totalStages: workflow.stages.length,
      artifactTypes: workflow.artifactTypes.length,
      statusCardTemplates: Object.keys(workflow.statusCardTemplates).length,
      domain: workflow.metadata?.domain,
      language: workflow.metadata?.language
    };
  }
}

// Singleton instance
let instance = null;

export function getWorkflowLoader() {
  if (!instance) {
    instance = new WorkflowLoader();
  }
  return instance;
}

export default WorkflowLoader;
