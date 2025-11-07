# Usage Examples: Domain-Agnostic Framework

This document demonstrates how to use the new domain-agnostic architecture to build workflow-based applications.

---

## Table of Contents

1. [Basic Concepts](#basic-concepts)
2. [Loading a Workflow](#loading-a-workflow)
3. [Creating an Entity](#creating-an-entity)
4. [Starting a Journey](#starting-a-journey)
5. [Adding Artifacts](#adding-artifacts)
6. [Generating Status Cards](#generating-status-cards)
7. [Switching Domains](#switching-domains)
8. [Creating a Custom Domain](#creating-a-custom-domain)

---

## Basic Concepts

The framework is built around five core abstractions:

1. **Entity** - The subject going through a workflow (child, patient, student, etc.)
2. **Journey** - An entity's progress through a workflow
3. **WorkflowDefinition** - The structure and rules of a workflow
4. **Artifact** - Documents, media, or data collected during a journey
5. **StatusCard** - UI cards showing current status and available actions

---

## Loading a Workflow

```javascript
import { getWorkflowLoader } from './src/core/services/WorkflowLoader.js';

// Get the singleton loader
const loader = getWorkflowLoader();

// Load child development workflow
const childDevWorkflow = await loader.loadWorkflowFromFile(
  '/config/workflows/child-development.json'
);

// Load healthcare workflow
const healthcareWorkflow = await loader.loadWorkflowFromFile(
  '/config/workflows/healthcare-intake.json'
);

// Set active workflow
loader.setActiveWorkflow('child-development-assessment');

// Get active workflow
const workflow = loader.getActiveWorkflow();
console.log(`Active workflow: ${workflow.name}`);
// Output: Active workflow: Child Development Assessment Journey
```

---

## Creating an Entity

```javascript
import { Entity } from './src/core/models/Entity.js';

// Example 1: Child Development Domain
const child = new Entity({
  type: 'child',
  attributes: {
    name: 'יוסי כהן',
    age: 3,
    parentName: 'שרה כהן',
    concerns: 'Speech development delay'
  },
  metadata: {
    referralSource: 'pediatrician'
  }
});

console.log(child.getDisplayName()); // Output: יוסי כהן
console.log(child.getAttribute('age')); // Output: 3

// Example 2: Healthcare Domain
const patient = new Entity({
  type: 'patient',
  attributes: {
    fullName: 'John Smith',
    dateOfBirth: '1985-06-15',
    insuranceId: 'INS-123456',
    allergies: ['Penicillin'],
    primaryConcern: 'Chronic back pain'
  }
});

// Validate entity against workflow schema
const validation = workflow.validateEntity(child);
if (!validation.valid) {
  console.error('Validation errors:', validation.errors);
}
```

---

## Starting a Journey

```javascript
import { Journey } from './src/core/models/Journey.js';

// Create a new journey
const journey = new Journey({
  entityId: child.id,
  workflowId: workflow.id,
  currentStageId: workflow.initialStageId // 'interview'
});

console.log(`Journey started at stage: ${journey.currentStageId}`);
// Output: Journey started at stage: interview

// Add a message to the journey
journey.addMessage({
  sender: 'user',
  text: 'שלום, אני רוצה לדבר על התפתחות הילד שלי',
  timestamp: new Date().toISOString()
});

journey.addMessage({
  sender: 'assistant',
  text: 'שלום! אשמח לעזור לך להבין את המסע ההתפתחותי של ילדך. ספר לי בבקשה על הדברים שמדאיגים אותך.',
  timestamp: new Date().toISOString()
});

// Store stage-specific data
journey.setStageData('interview', {
  concerns: ['speech', 'motor_skills'],
  completedQuestions: 5,
  totalQuestions: 10
});

// Check if we can advance to next stage
const currentStage = workflow.getStage(journey.currentStageId);
const canAdvance = journey.hasRequiredAttributes(
  currentStage.completionCriteria?.requiredFields || []
);

if (canAdvance) {
  journey.completeCurrentStage('consultation');
  console.log(`Advanced to: ${journey.currentStageId}`);
}
```

---

## Adding Artifacts

```javascript
import { Artifact } from './src/core/models/Artifact.js';

// Example 1: Diagnostic Report
const diagnosticReport = new Artifact({
  type: 'document',
  category: 'diagnostic_report',
  name: 'התפתחות שפה - אבחון.pdf',
  format: 'pdf',
  size: 1024000, // 1MB
  url: 'https://storage.example.com/reports/abc123.pdf',
  journeyId: journey.id,
  stageId: 'document_upload',
  entityId: child.id,
  metadata: {
    diagnostician: 'ד"ר מרים לוי',
    date: '2024-01-15'
  }
});

// Add to journey
journey.addArtifact(diagnosticReport.toJSON());

console.log(`Total artifacts: ${journey.artifacts.length}`);

// Example 2: Behavioral Video
const video = new Artifact({
  type: 'video',
  category: 'behavioral_video',
  name: 'playing_with_toys.mp4',
  format: 'mp4',
  size: 50000000, // 50MB
  url: 'https://storage.example.com/videos/xyz789.mp4',
  journeyId: journey.id,
  stageId: 'video_upload',
  entityId: child.id,
  tags: ['play', 'motor_skills', 'social_interaction']
});

// Mark as processing
video.markProcessing();

// Simulate video analysis
setTimeout(() => {
  video.markReady({
    duration: 180, // seconds
    analysis: {
      motor_skills: 'age-appropriate',
      social_interaction: 'needs_attention',
      confidence: 0.87
    }
  });
  console.log('Video processing complete:', video.processingResult);
}, 2000);

// Get artifacts by type
const videos = journey.getArtifactsByType('video');
console.log(`Video count: ${videos.length}`);

// Get artifacts by category
const medicalDocs = journey.getArtifactsByCategory('diagnostic_report');
console.log(`Medical documents: ${medicalDocs.length}`);
```

---

## Generating Status Cards

```javascript
import { StatusCard } from './src/core/models/StatusCard.js';

// Function to generate status cards based on journey state
function generateStatusCards(journey, workflow) {
  const cards = [];

  // Card 1: Current stage progress
  if (journey.currentStageId === 'interview') {
    const template = workflow.getStatusCardTemplate('interview_in_progress');
    cards.push(new StatusCard({
      ...template,
      journeyId: journey.id,
      stageId: journey.currentStageId,
      entityId: journey.entityId
    }));
  }

  // Card 2: Completed stages
  if (journey.hasCompletedStage('interview')) {
    const template = workflow.getStatusCardTemplate('interview_complete');
    cards.push(new StatusCard({
      ...template,
      journeyId: journey.id,
      priority: 5
    }));
  }

  // Card 3: Action needed
  const currentStage = workflow.getStage(journey.currentStageId);
  if (currentStage?.id === 'consultation') {
    const documentsCount = journey.getArtifactsByCategory('diagnostic_report').length;

    if (documentsCount === 0) {
      const template = workflow.getStatusCardTemplate('documents_needed');
      cards.push(new StatusCard({
        ...template,
        journeyId: journey.id,
        stageId: journey.currentStageId
      }));
    }
  }

  // Card 4: Artifact processing
  const processingVideos = journey.artifacts.filter(
    a => a.type === 'video' && a.status === 'processing'
  );

  if (processingVideos.length > 0) {
    const template = workflow.getStatusCardTemplate('video_processing');
    cards.push(new StatusCard({
      ...template,
      journeyId: journey.id
    }));
  }

  // Card 5: Progress metric
  const progress = journey.calculateProgress(workflow.stages.length);
  cards.push(new StatusCard({
    type: 'metric',
    title: 'מסע התפתחותי',
    subtitle: `${progress}% הושלם`,
    icon: 'TrendingUp',
    journeyId: journey.id,
    priority: 3
  }));

  // Sort by priority (higher first)
  cards.sort((a, b) => b.priority - a.priority);

  return cards;
}

// Generate cards
const statusCards = generateStatusCards(journey, workflow);

// Render in UI
statusCards.forEach(card => {
  console.log(`[${card.type}] ${card.title} - ${card.subtitle}`);

  if (card.clickable) {
    console.log(`  Action: ${card.action.type}`);
  }
});

/* Output:
[processing] Interview in Progress - Gathering child information
  Action: undefined
[info] מסע התפתחותי - 20% הושלם
  Action: undefined
*/
```

---

## Switching Domains

```javascript
// Start with child development
loader.setActiveWorkflow('child-development-assessment');
let workflow = loader.getActiveWorkflow();

console.log(`Domain: ${workflow.metadata.domain}`);
console.log(`Language: ${workflow.metadata.language}`);
console.log(`Direction: ${workflow.metadata.direction}`);
// Output:
// Domain: child_development
// Language: he
// Direction: rtl

// Switch to healthcare
loader.setActiveWorkflow('healthcare-patient-intake');
workflow = loader.getActiveWorkflow();

console.log(`Domain: ${workflow.metadata.domain}`);
console.log(`Language: ${workflow.metadata.language}`);
console.log(`Direction: ${workflow.metadata.direction}`);
// Output:
// Domain: healthcare
// Language: en
// Direction: ltr

// All the same code works! Just different configuration
```

---

## Creating a Custom Domain

Let's create a completely new domain: **Student Enrollment**

### Step 1: Create workflow configuration

```json
// config/workflows/student-enrollment.json
{
  "id": "student-enrollment",
  "name": "Student Enrollment Journey",
  "description": "University student application and enrollment workflow",
  "version": "1.0.0",

  "entitySchema": {
    "type": "student",
    "requiredAttributes": ["fullName", "email", "phoneNumber"],
    "optionalAttributes": ["previousSchool", "gpa", "interests"]
  },

  "stages": [
    {
      "id": "application",
      "name": "Application Submission",
      "type": "conversation",
      "order": 1,
      "nextStages": ["document_submission"]
    },
    {
      "id": "document_submission",
      "name": "Document Submission",
      "type": "upload",
      "order": 2,
      "nextStages": ["interview"]
    },
    {
      "id": "interview",
      "name": "Admissions Interview",
      "type": "conversation",
      "order": 3,
      "nextStages": ["decision"]
    },
    {
      "id": "decision",
      "name": "Admissions Decision",
      "type": "review",
      "order": 4,
      "nextStages": ["enrollment"]
    },
    {
      "id": "enrollment",
      "name": "Course Enrollment",
      "type": "action",
      "order": 5,
      "nextStages": []
    }
  ],

  "artifactTypes": [
    {
      "id": "transcript",
      "name": "Academic Transcript",
      "category": "academic",
      "acceptedFormats": [".pdf"],
      "icon": "FileText"
    },
    {
      "id": "recommendation",
      "name": "Letter of Recommendation",
      "category": "academic",
      "acceptedFormats": [".pdf"],
      "icon": "Mail"
    },
    {
      "id": "essay",
      "name": "Personal Essay",
      "category": "application",
      "acceptedFormats": [".pdf", ".doc", ".docx"],
      "icon": "FileEdit"
    }
  ],

  "metadata": {
    "domain": "education",
    "language": "en",
    "direction": "ltr"
  }
}
```

### Step 2: Load and use

```javascript
// Load the new workflow
const enrollmentWorkflow = await loader.loadWorkflowFromFile(
  '/config/workflows/student-enrollment.json'
);

loader.setActiveWorkflow('student-enrollment');

// Create a student entity
const student = new Entity({
  type: 'student',
  attributes: {
    fullName: 'Emily Chen',
    email: 'emily.chen@example.com',
    phoneNumber: '+1-555-0123',
    previousSchool: 'Lincoln High School',
    gpa: 3.8,
    interests: ['Computer Science', 'Mathematics']
  }
});

// Start enrollment journey
const enrollmentJourney = new Journey({
  entityId: student.id,
  workflowId: enrollmentWorkflow.id,
  currentStageId: 'application'
});

// Add transcript
const transcript = new Artifact({
  type: 'document',
  category: 'transcript',
  name: 'high_school_transcript.pdf',
  journeyId: enrollmentJourney.id,
  stageId: 'document_submission',
  entityId: student.id
});

enrollmentJourney.addArtifact(transcript.toJSON());

console.log('Student enrollment journey started!');
console.log(`Current stage: ${enrollmentJourney.currentStageId}`);
console.log(`Artifacts: ${enrollmentJourney.artifacts.length}`);
```

**That's it!** The entire framework now works for student enrollment, using exactly the same code as child development and healthcare. Only the configuration changed.

---

## Advanced: Programmatic Workflow Creation

You can also create workflows programmatically instead of loading from JSON:

```javascript
import { WorkflowDefinition } from './src/core/models/WorkflowDefinition.js';

const customWorkflow = new WorkflowDefinition({
  id: 'custom-workflow',
  name: 'My Custom Workflow',
  entitySchema: {
    type: 'custom_entity',
    requiredAttributes: ['name']
  },
  stages: [
    {
      id: 'stage1',
      name: 'First Stage',
      type: 'conversation',
      nextStages: ['stage2']
    },
    {
      id: 'stage2',
      name: 'Second Stage',
      type: 'action',
      nextStages: []
    }
  ],
  initialStageId: 'stage1',
  artifactTypes: [],
  statusCardTemplates: {},
  suggestionTemplates: {}
});

// Validate
const validation = loader.validateWorkflow(customWorkflow);
if (validation.valid) {
  loader.loadWorkflow(customWorkflow);
  console.log('Custom workflow loaded!');
}
```

---

## Key Takeaways

1. **Same Code, Different Domains** - Write once, configure for any domain
2. **Configuration Over Code** - Add workflows via JSON, not code changes
3. **Type Safety** - Models enforce structure and validation
4. **Extensible** - Easy to add new stages, artifacts, and actions
5. **Testable** - Each model can be tested independently

---

## Next Steps

- Review the [Architecture Refactoring Proposal](./ARCHITECTURE_REFACTORING_PROPOSAL.md)
- Explore the core models in `src/core/models/`
- Create your own workflow configuration
- Extend with custom domain logic in `src/domains/`

---

*This framework transforms workflow-based applications from domain-specific code into flexible, configuration-driven systems that can be adapted to any use case.*
