/**
 * Core Models - Domain-agnostic abstractions
 *
 * These models form the foundation of the framework and can be used
 * across any domain without modification.
 */

export { Entity } from './Entity.js';
export { Journey } from './Journey.js';
export { WorkflowDefinition } from './WorkflowDefinition.js';
export { Artifact } from './Artifact.js';
export { StatusCard } from './StatusCard.js';

export default {
  Entity,
  Journey,
  WorkflowDefinition,
  Artifact,
  StatusCard
};
