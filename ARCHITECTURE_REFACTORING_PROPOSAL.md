# Architecture Refactoring Proposal: Domain-Agnostic Framework

## Executive Summary

Transform **Chitta** from a child development assessment platform into a **domain-agnostic conversational workflow framework** that can be easily adapted to any domain (healthcare, education, customer support, legal consulting, etc.).

---

## 🎯 Vision: Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    DOMAIN LAYER                         │
│  (Child Development / Healthcare / Education / etc.)    │
│  - Domain Models                                        │
│  - Domain Workflows                                     │
│  - Domain Content                                       │
│  - Domain Rules                                         │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                 CONFIGURATION LAYER                     │
│  - Workflow Definitions (JSON/YAML)                     │
│  - Entity Schemas                                       │
│  - Content Templates                                    │
│  - UI Theme Configuration                               │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                     CORE LAYER                          │
│  (Domain-Agnostic Framework)                            │
│  - Conversation Engine                                  │
│  - Status Card System                                   │
│  - Workflow Orchestrator                                │
│  - Media/Document Manager                               │
│  - State Management                                     │
│  - UI Component Library                                 │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 Current State Analysis

### Domain-Specific Concepts Currently Hardcoded

| Current (Child Development) | Generic Abstraction |
|----------------------------|---------------------|
| Child | Entity |
| Journey Stage | Workflow Stage |
| Milestone | Progress Checkpoint |
| Diagnostic Report | Document Artifact |
| Behavioral Video | Media Artifact |
| Interview | Intake Workflow |
| Consultation | Guidance Workflow |
| Expert Profile | Advisor Profile |
| Developmental Assessment | Entity Evaluation |

### Problems with Current Architecture

1. **Tight Coupling**: Domain logic mixed with UI components
2. **Hardcoded Content**: Scenario data embedded in code
3. **Limited Extensibility**: Adding new workflows requires code changes
4. **Domain-Specific Naming**: Makes adaptation to other domains difficult
5. **No Plugin System**: Can't extend functionality without modifying core

---

## 🏗️ Proposed Architecture

### 1. Core Layer (Domain-Agnostic)

#### 1.1 Core Abstractions

```javascript
// src/core/models/Entity.js
/**
 * Generic entity being tracked through a workflow
 * Examples: Child, Patient, Student, Customer, Legal Case
 */
class Entity {
  constructor(config) {
    this.id = config.id;
    this.type = config.type; // Defined in domain config
    this.attributes = config.attributes; // Flexible key-value store
    this.metadata = config.metadata;
  }
}

// src/core/models/Journey.js
/**
 * Generic workflow journey with configurable stages
 */
class Journey {
  constructor(config) {
    this.id = config.id;
    this.entityId = config.entityId;
    this.workflow = config.workflow; // Reference to WorkflowDefinition
    this.currentStage = config.currentStage;
    this.stages = config.stages; // Array of stage instances
    this.progress = config.progress;
    this.artifacts = config.artifacts; // Documents, media, etc.
  }

  advanceStage() { /* ... */ }
  canAdvance() { /* ... */ }
  getNextStage() { /* ... */ }
}

// src/core/models/WorkflowDefinition.js
/**
 * Defines a multi-stage workflow
 */
class WorkflowDefinition {
  constructor(config) {
    this.id = config.id;
    this.name = config.name;
    this.description = config.description;
    this.stages = config.stages; // Array of StageDefinition
    this.transitions = config.transitions; // Rules for moving between stages
  }
}

// src/core/models/StageDefinition.js
/**
 * Defines a single stage in a workflow
 */
class StageDefinition {
  constructor(config) {
    this.id = config.id;
    this.name = config.name;
    this.type = config.type; // 'conversation', 'upload', 'review', 'action'
    this.requiredArtifacts = config.requiredArtifacts;
    this.completionCriteria = config.completionCriteria;
    this.availableActions = config.availableActions;
    this.viewComponent = config.viewComponent; // Which UI to show
  }
}

// src/core/models/Artifact.js
/**
 * Generic artifact (document, media, data) attached to a journey
 */
class Artifact {
  constructor(config) {
    this.id = config.id;
    this.type = config.type; // 'document', 'video', 'image', 'data'
    this.category = config.category; // Domain-specific categorization
    this.content = config.content;
    this.metadata = config.metadata;
    this.uploadedAt = config.uploadedAt;
  }
}

// src/core/models/StatusCard.js
/**
 * Generic status card for contextual surface
 */
class StatusCard {
  constructor(config) {
    this.id = config.id;
    this.type = config.type; // Maps to styling
    this.title = config.title;
    this.subtitle = config.subtitle;
    this.icon = config.icon;
    this.action = config.action; // What happens on click
    this.metadata = config.metadata;
  }
}
```

#### 1.2 Core Services

```javascript
// src/core/services/ConversationEngine.js
/**
 * Manages conversational interactions
 */
class ConversationEngine {
  async processMessage(message, context) {
    // 1. Parse message intent
    // 2. Execute appropriate action
    // 3. Generate response
    // 4. Update journey state
    // 5. Generate new status cards
  }

  async generateResponse(intent, context) { /* ... */ }
  async updateJourneyState(journey, action) { /* ... */ }
  async generateStatusCards(journey) { /* ... */ }
}

// src/core/services/WorkflowOrchestrator.js
/**
 * Manages workflow progression and state transitions
 */
class WorkflowOrchestrator {
  constructor(workflowDefinition) {
    this.workflow = workflowDefinition;
  }

  async startJourney(entity) { /* ... */ }
  async advanceStage(journey, targetStage) { /* ... */ }
  async validateTransition(fromStage, toStage) { /* ... */ }
  async executeStageActions(stage, context) { /* ... */ }
}

// src/core/services/ArtifactManager.js
/**
 * Manages document and media artifacts
 */
class ArtifactManager {
  async uploadArtifact(file, metadata) { /* ... */ }
  async getArtifacts(filters) { /* ... */ }
  async deleteArtifact(id) { /* ... */ }
  async processArtifact(id, processor) { /* ... */ }
}

// src/core/services/StateManager.js
/**
 * Centralized state management
 */
class StateManager {
  constructor() {
    this.state = {
      entities: new Map(),
      journeys: new Map(),
      artifacts: new Map(),
      ui: {}
    };
    this.listeners = [];
  }

  getState() { /* ... */ }
  updateState(updates) { /* ... */ }
  subscribe(listener) { /* ... */ }
}
```

#### 1.3 Core UI Components (Already Good!)

Your existing components are already fairly generic:
- ✅ ConversationTranscript - Works for any conversation
- ✅ ContextualSurface - Generic status cards
- ✅ InputArea - Generic text input
- ✅ SuggestionsPopup - Generic suggestions
- ✅ DeepViewManager - Generic modal router

**Minor Refactoring Needed:**
- Rename to remove domain references
- Make styling configurable via theme
- Extract hardcoded text to content configuration

---

### 2. Configuration Layer

#### 2.1 Workflow Configuration (JSON/YAML)

```yaml
# config/workflows/child-development.yaml
workflow:
  id: "child-development-assessment"
  name: "Child Development Assessment Journey"
  description: "Multi-stage assessment and guidance for child development"

  entity_schema:
    type: "child"
    required_attributes:
      - name
      - age
      - parent_name
    optional_attributes:
      - birth_date
      - medical_history
      - concerns

  stages:
    - id: "interview"
      name: "Initial Interview"
      type: "conversation"
      description: "Gather information about the child"
      completion_criteria:
        required_fields: ["name", "age", "concerns"]
        min_messages: 5
      next_stages: ["consultation", "document_upload"]

    - id: "consultation"
      name: "Ongoing Consultation"
      type: "conversation"
      description: "Provide guidance and answer questions"
      completion_criteria:
        optional: true
      next_stages: ["video_upload", "report_generation"]

    - id: "document_upload"
      name: "Document Upload"
      type: "upload"
      description: "Upload diagnostic reports and medical documents"
      completion_criteria:
        min_artifacts: 1
        artifact_types: ["diagnostic_report", "medical_record"]
      next_stages: ["consultation"]

    - id: "video_upload"
      name: "Video Upload"
      type: "upload"
      description: "Upload videos of child's behavior"
      completion_criteria:
        min_artifacts: 1
        artifact_types: ["behavioral_video"]
      next_stages: ["report_generation"]

    - id: "report_generation"
      name: "Report Generation"
      type: "review"
      description: "Generate comprehensive assessment report"
      completion_criteria:
        dependencies: ["interview", "video_upload"]
      next_stages: ["expert_consultation"]

    - id: "expert_consultation"
      name: "Expert Consultation"
      type: "action"
      description: "Connect with developmental specialists"
      completion_criteria:
        optional: true
      next_stages: []

  artifact_types:
    - id: "diagnostic_report"
      name: "Diagnostic Report"
      category: "medical"
      accepted_formats: [".pdf", ".doc", ".docx"]

    - id: "medical_record"
      name: "Medical Record"
      category: "medical"
      accepted_formats: [".pdf", ".jpg", ".png"]

    - id: "behavioral_video"
      name: "Behavioral Video"
      category: "observation"
      accepted_formats: [".mp4", ".mov", ".avi"]
      max_size_mb: 500

  status_card_templates:
    interview_complete:
      type: "completed"
      title: "Interview Complete"
      subtitle: "Child information gathered"
      icon: "CheckCircle"

    documents_needed:
      type: "action"
      title: "Upload Documents"
      subtitle: "Add diagnostic reports"
      icon: "FileUp"
      action:
        type: "open_deep_view"
        view: "document_upload"

    video_processing:
      type: "processing"
      title: "Processing Video"
      subtitle: "Analyzing behavioral patterns"
      icon: "Video"

  suggestions_templates:
    interview_stage:
      - text: "Tell me about developmental concerns"
        icon: "MessageCircle"
        action: "send_message"
      - text: "Upload diagnostic reports"
        icon: "FileUp"
        action: "open_upload"
      - text: "Record a video"
        icon: "Video"
        action: "open_filming"

    consultation_stage:
      - text: "Ask about speech development"
        icon: "MessageCircle"
        action: "send_message"
      - text: "Connect with an expert"
        icon: "Users"
        action: "open_expert_finder"
```

#### 2.2 Alternative Domain Example: Healthcare

```yaml
# config/workflows/patient-intake.yaml
workflow:
  id: "patient-intake"
  name: "Patient Intake and Care Journey"
  description: "Medical intake, triage, and treatment workflow"

  entity_schema:
    type: "patient"
    required_attributes:
      - full_name
      - date_of_birth
      - insurance_id
    optional_attributes:
      - allergies
      - medications
      - medical_history

  stages:
    - id: "registration"
      name: "Patient Registration"
      type: "conversation"

    - id: "triage"
      name: "Symptom Triage"
      type: "conversation"

    - id: "document_collection"
      name: "Medical Records Collection"
      type: "upload"

    - id: "appointment_scheduling"
      name: "Schedule Appointment"
      type: "action"

    - id: "treatment_plan"
      name: "Treatment Plan Review"
      type: "review"
```

#### 2.3 Theme Configuration

```javascript
// config/themes/child-development.js
export default {
  name: "Child Development",
  colors: {
    primary: {
      start: "#6366f1", // indigo
      end: "#a855f7"    // purple
    },
    statusCards: {
      completed: "bg-green-100 border-green-300",
      pending: "bg-amber-100 border-amber-300",
      action: "bg-blue-100 border-blue-300",
      // ... etc
    }
  },
  typography: {
    direction: "rtl",
    primaryFont: "Inter",
    language: "he"
  },
  branding: {
    appName: "Chitta",
    logo: "/assets/logo-child-dev.svg",
    tagline: "Understanding your child's journey"
  }
};
```

---

### 3. Domain Layer

```
src/domains/
├── child-development/
│   ├── config/
│   │   ├── workflow.yaml
│   │   ├── theme.js
│   │   └── content.json
│   ├── models/
│   │   ├── Child.js          (extends Entity)
│   │   ├── DevelopmentMilestone.js
│   │   └── AssessmentReport.js
│   ├── services/
│   │   ├── AssessmentService.js
│   │   └── MilestoneTracker.js
│   ├── components/
│   │   └── MilestoneChart.jsx (custom visualization)
│   └── index.js
│
├── healthcare/
│   ├── config/
│   ├── models/
│   ├── services/
│   ├── components/
│   └── index.js
│
└── education/
    ├── config/
    ├── models/
    ├── services/
    ├── components/
    └── index.js
```

---

## 🔄 Migration Path

### Phase 1: Extract Core Abstractions
1. Create `src/core/` directory structure
2. Create generic model classes (Entity, Journey, Workflow, etc.)
3. Update existing code to use generic models internally
4. **No UI changes** - everything still works

### Phase 2: Configuration Extraction
1. Create `config/workflows/` directory
2. Extract hardcoded scenario data to YAML files
3. Create configuration loader
4. Update api.js to read from configuration
5. **No UI changes** - everything still works

### Phase 3: Domain Layer Separation
1. Create `src/domains/child-development/` directory
2. Move domain-specific logic to domain layer
3. Register domain as plugin
4. **No UI changes** - everything still works

### Phase 4: Theme System
1. Extract colors, typography to theme config
2. Create theme loader
3. Apply theme dynamically
4. **UI looks identical** but is now configurable

### Phase 5: Alternative Domain Demo
1. Create `src/domains/healthcare/` as proof of concept
2. Implement simple patient intake workflow
3. Demonstrate switching between domains
4. **Shows the power of abstraction**

---

## 🎁 Benefits of This Architecture

### 1. **Adaptability**
- Switch domains by changing configuration file
- No code changes needed for different use cases
- Can run multiple domains simultaneously

### 2. **Maintainability**
- Clear separation of concerns
- Each layer has single responsibility
- Easy to understand and modify

### 3. **Extensibility**
- Plugin system for domains
- Add new workflows without touching core
- Custom components per domain

### 4. **Testability**
- Core logic isolated and unit-testable
- Domain logic tested independently
- UI components tested in isolation

### 5. **Reusability**
- Core framework reusable across projects
- Domain modules can be shared
- UI components are generic

### 6. **Scalability**
- Add new domains easily
- Support multi-tenancy
- Can be packaged as product

---

## 📦 Example: How to Add a New Domain

```javascript
// 1. Create workflow configuration
// config/workflows/legal-consulting.yaml
workflow:
  id: "legal-case-management"
  entity_schema:
    type: "legal_case"
  stages:
    - id: "initial_consultation"
    - id: "document_collection"
    - id: "case_analysis"
    - id: "strategy_recommendation"

// 2. Register domain
// src/domains/legal-consulting/index.js
import workflowConfig from '../../../config/workflows/legal-consulting.yaml';
import theme from './config/theme.js';

export default {
  id: 'legal-consulting',
  name: 'Legal Consulting',
  workflow: workflowConfig,
  theme: theme,
  models: {},
  services: {},
  components: {}
};

// 3. Load in main app
// src/main.jsx
import legalDomain from './domains/legal-consulting';
import framework from './core';

framework.registerDomain(legalDomain);
framework.setActiveDomain('legal-consulting');
```

**That's it!** The entire app now works for legal consulting.

---

## 🚀 Recommended Implementation Order

1. ✅ **Read this proposal** (you are here)
2. Create core abstractions (Entity, Journey, Workflow, Artifact)
3. Extract configuration format and loader
4. Refactor api.js to use configuration
5. Create domain layer structure
6. Move child-development to domain module
7. Implement theme system
8. Create second domain as proof (healthcare or education)
9. Add plugin registration system
10. Documentation and examples

---

## 📊 Before & After Comparison

### Before: Adding a New Workflow Stage

```javascript
// Must modify multiple files:
// 1. src/services/api.js - Add scenario data
// 2. src/components/deepviews/NewView.jsx - Create component
// 3. src/components/DeepViewManager.jsx - Register view
// 4. Update App.jsx if new state needed
// Estimated time: 2-4 hours
```

### After: Adding a New Workflow Stage

```yaml
# Edit single config file:
# config/workflows/child-development.yaml
stages:
  - id: "new_stage"
    name: "New Stage"
    type: "conversation"
    # ... configuration

# Estimated time: 15 minutes
```

---

## 🎯 Success Criteria

This refactoring will be successful when:

1. ✅ Can switch from child development to healthcare by changing config file
2. ✅ No domain-specific code in `src/core/`
3. ✅ Can add new workflow stage via configuration only
4. ✅ All existing functionality preserved
5. ✅ No breaking changes to current UI
6. ✅ Clear documentation for adding domains
7. ✅ Demo showing 2+ different domains running

---

## 🤔 Questions to Consider

1. **Backend Integration**: How will this work with real backend?
   - **Answer**: Backend also adopts workflow model, returns generic Journey objects

2. **Performance**: Will abstraction add overhead?
   - **Answer**: Minimal - configuration loaded once at startup

3. **Learning Curve**: Will this be harder to understand?
   - **Answer**: Initially yes, but clear documentation and examples will help

4. **Migration Risk**: What if refactoring breaks things?
   - **Answer**: Incremental migration with extensive testing at each phase

---

## 📚 Next Steps

Would you like me to:

1. **Start implementing** the core abstractions?
2. **Create detailed examples** of how each layer works?
3. **Build a proof of concept** with an alternative domain?
4. **Write implementation guides** for each phase?

I recommend starting with **Phase 1** (Core Abstractions) while keeping everything working, then iterating from there.

---

*This proposal transforms Chitta from a single-purpose application into a flexible framework that can power conversational workflow applications in any domain, while maintaining all existing functionality and UI quality.*
