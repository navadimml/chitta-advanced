# Domain Abstraction Proposal: Making Chitta Domain-Agnostic

**Author**: Architecture Analysis
**Date**: 2025-11-07
**Status**: Proposal for Discussion

---

## Executive Summary

After deep analysis of the Chitta backend architecture (based on `conversation_service.py`, `IMPLEMENTATION_DEEP_DIVE.md`, and prerequisite system), I've identified a clean path to make the system domain-agnostic **without adding significant complexity**.

**Key Insight**: The current architecture already has excellent separation between **process** (how we extract information, check prerequisites, manage state) and **domain** (what we extract, what actions mean, what prerequisites exist). We just need to make this separation explicit and configurable.

**Result**: The same codebase could power:
- Child development assessment (current)
- Medical patient intake
- Legal case management
- Job interview screening
- Customer support qualification
- Real estate property assessment
- ... any domain requiring conversational information extraction with gated workflows

---

## Current Architecture Analysis

### What Works Brilliantly (Keep As-Is)

The current architecture has these domain-agnostic patterns:

```python
# 1. CONVERSATIONAL EXTRACTION PATTERN
# - Works for ANY domain where you extract structured data from conversation
# - Child dev: extract child_name, concerns, developmental_history
# - Medical: extract patient_name, symptoms, medical_history
# - Legal: extract case_type, parties, incident_details

async def process_message(family_id, message):
    # Load context → Call LLM → Extract data → Check completeness → Generate cards
    # THIS PATTERN IS UNIVERSAL
```

```python
# 2. PREREQUISITE-BASED ACTION GATING
# - Works for ANY workflow with sequential dependencies
# - Child dev: interview_complete → video_guidelines → upload → analysis → report
# - Medical: intake_complete → tests_ordered → results → diagnosis → treatment
# - Legal: case_filed → discovery → depositions → trial_prep → settlement

PREREQUISITES = {
    Action.VIEW_REPORT: {
        "requires": [PrerequisiteType.ANALYSIS_COMPLETE]
    }
}
# THIS PATTERN IS UNIVERSAL
```

```python
# 3. COMPLETENESS CALCULATION
# - Works for ANY domain where you need "enough information"
# - NOT a rigid checklist, but richness/depth scoring
# - Child dev: concerns (50%), context (20%), history (15%)
# - Medical: symptoms (50%), history (20%), medications (15%)

def calculate_completeness(data):
    score = weighted_sum_of_fields(data)
    # THIS PATTERN IS UNIVERSAL
```

### What's Domain-Specific (Make Configurable)

Only THREE things are domain-specific:

1. **Data Schema** - What fields to extract
2. **Action/Prerequisite Definitions** - What users can do and when
3. **Domain Knowledge & Prompts** - How to talk about the domain

**That's it.** Everything else is generic.

---

## Proposed Abstraction: 3-Layer Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     DOMAIN LAYER                             │
│  (Specific to child development, medical, legal, etc.)       │
│                                                               │
│  📁 /domains/child_development/                              │
│     ├── schema.py          ← What data to extract            │
│     ├── actions.py         ← Available actions & prerequisites│
│     ├── completeness.py    ← How to calculate completeness   │
│     ├── prompts/           ← Domain-specific prompts         │
│     └── knowledge.py       ← Domain knowledge base           │
└──────────────────────────────────────────────────────────────┘
                            ↓ uses
┌──────────────────────────────────────────────────────────────┐
│                   WORKFLOW ENGINE LAYER                       │
│  (Domain-agnostic interview/extraction engine)               │
│                                                               │
│  📁 /engine/                                                 │
│     ├── extraction_service.py  ← Extract data from conversation│
│     ├── prerequisite_service.py ← Check action feasibility   │
│     ├── completeness_service.py ← Calculate readiness        │
│     ├── state_service.py       ← Manage session state        │
│     └── prompt_builder.py      ← Build contextual prompts    │
└──────────────────────────────────────────────────────────────┘
                            ↓ uses
┌──────────────────────────────────────────────────────────────┐
│                      CORE LAYER                              │
│  (Universal LLM conversation infrastructure)                 │
│                                                               │
│  📁 /core/                                                   │
│     ├── conversation_service.py ← Main orchestrator          │
│     ├── llm/                   ← LLM providers (Gemini, Claude)│
│     └── models.py              ← Base models (Message, etc.)  │
└──────────────────────────────────────────────────────────────┘
```

---

## Implementation: Minimal Changes, Maximum Impact

### Step 1: Extract Domain Definitions

**Current** (hardcoded in `/backend/app/services/interview_service.py`):
```python
class ExtractedData(BaseModel):
    child_name: Optional[str] = None
    age: Optional[float] = None
    gender: Optional[str] = None
    primary_concerns: List[str] = []
    concern_details: Optional[str] = None
    strengths: Optional[str] = None
    developmental_history: Optional[str] = None
    family_context: Optional[str] = None
    daily_routines: Optional[str] = None
    parent_goals: Optional[str] = None
    urgent_flags: List[str] = []
```

**Proposed** (`/backend/domains/child_development/schema.py`):
```python
from engine.base_schema import BaseDomainSchema, FieldDefinition

class ChildDevelopmentSchema(BaseDomainSchema):
    """Domain schema for child development assessment"""

    @property
    def entity_name(self) -> str:
        return "child"  # "child", "patient", "case", "candidate", etc.

    @property
    def entity_identifier_field(self) -> str:
        return "child_name"  # Primary identifier field

    @property
    def fields(self) -> Dict[str, FieldDefinition]:
        return {
            # Core identifiers (small weight in completeness)
            "child_name": FieldDefinition(
                type="string",
                description="שם הילד/ה",
                weight=0.01,
                category="identifier"
            ),
            "age": FieldDefinition(
                type="number",
                description="גיל בשנים",
                weight=0.03,
                category="identifier"
            ),
            "gender": FieldDefinition(
                type="enum",
                description="מגדר",
                options=["male", "female", "unknown"],
                weight=0.01,
                category="identifier"
            ),

            # Primary content (large weight in completeness)
            "primary_concerns": FieldDefinition(
                type="array",
                description="תחומי דאגה עיקריים",
                options=["speech", "social", "attention", "motor", "sensory", "emotional"],
                weight=0.10,
                category="core"
            ),
            "concern_details": FieldDefinition(
                type="longtext",
                description="פירוט הדאגות והדוגמאות",
                weight=0.40,  # THIS is the main content
                category="core"
            ),

            # Supporting context (medium weight)
            "strengths": FieldDefinition(
                type="text",
                description="חוזקות והתנהגויות חיוביות",
                weight=0.10,
                category="context"
            ),
            "developmental_history": FieldDefinition(
                type="text",
                description="אבני דרך התפתחותיות",
                weight=0.15,
                category="context"
            ),

            # Additional context (smaller weight)
            "family_context": FieldDefinition(
                type="text",
                description="הקשר משפחתי",
                weight=0.07,
                category="context"
            ),
            "daily_routines": FieldDefinition(
                type="text",
                description="שגרת יום",
                weight=0.07,
                category="context"
            ),
            "parent_goals": FieldDefinition(
                type="text",
                description="מטרות ההורים",
                weight=0.06,
                category="context"
            ),

            # Flags
            "urgent_flags": FieldDefinition(
                type="array",
                description="דגלים דחופים",
                weight=0.0,
                category="meta"
            )
        }
```

**Alternative Domain** (`/backend/domains/medical_intake/schema.py`):
```python
class MedicalIntakeSchema(BaseDomainSchema):
    """Domain schema for medical patient intake"""

    @property
    def entity_name(self) -> str:
        return "patient"

    @property
    def entity_identifier_field(self) -> str:
        return "patient_name"

    @property
    def fields(self) -> Dict[str, FieldDefinition]:
        return {
            # Identifiers
            "patient_name": FieldDefinition(type="string", weight=0.01),
            "date_of_birth": FieldDefinition(type="date", weight=0.02),
            "insurance_id": FieldDefinition(type="string", weight=0.02),

            # Primary symptoms (main content)
            "chief_complaint": FieldDefinition(type="text", weight=0.10),
            "symptom_details": FieldDefinition(type="longtext", weight=0.40),
            "symptom_duration": FieldDefinition(type="text", weight=0.05),

            # Medical history
            "current_medications": FieldDefinition(type="array", weight=0.10),
            "allergies": FieldDefinition(type="array", weight=0.08),
            "past_medical_history": FieldDefinition(type="text", weight=0.15),
            "family_medical_history": FieldDefinition(type="text", weight=0.07),

            # Flags
            "urgent_symptoms": FieldDefinition(type="array", weight=0.0)
        }
```

**Key Benefits**:
1. ✅ **Same extraction engine** - works for both domains
2. ✅ **Completeness auto-calculated** - from field weights
3. ✅ **No code changes** - just different config
4. ✅ **Type-safe** - Pydantic validates everything

---

### Step 2: Extract Action/Prerequisite Definitions

**Current** (hardcoded in `/backend/app/prompts/prerequisites.py`):
```python
PREREQUISITES: Dict[Action, Dict[str, Any]] = {
    Action.VIEW_VIDEO_GUIDELINES: {
        "requires": [PrerequisiteType.INTERVIEW_COMPLETE],
        "explanation_to_user": "כדי ליצור הנחיות צילום..."
    },
    # ... 15 more actions
}
```

**Proposed** (`/backend/domains/child_development/actions.py`):
```python
from engine.base_actions import BaseDomainActions, ActionDefinition, PrerequisiteType

class ChildDevelopmentActions(BaseDomainActions):
    """Actions and prerequisites for child development domain"""

    @property
    def actions(self) -> Dict[str, ActionDefinition]:
        return {
            "view_video_guidelines": ActionDefinition(
                name="view_video_guidelines",
                description="View personalized video filming guidelines",
                requires=[PrerequisiteType.INTAKE_COMPLETE],
                explanation_template="כדי ליצור הנחיות צילום מותאמות אישית, אני צריכה קודם לסיים את הראיון. בואי נמשיך בשיחה - נשארו עוד כמה דברים שחשוב לי לדעת.",
                category="workflow"
            ),

            "upload_video": ActionDefinition(
                name="upload_video",
                description="Upload behavioral observation video",
                requires=[PrerequisiteType.INTAKE_COMPLETE],
                explanation_template="נהדר שאת מוכנה להעלות סרטונים! בואי נסיים קודם את הראיון, ואז אוכל ליצור עבורך הנחיות צילום מדויקות שמתאימות ל{entity_name}.",
                category="workflow"
            ),

            "view_report": ActionDefinition(
                name="view_report",
                description="View comprehensive assessment report",
                requires=[PrerequisiteType.ANALYSIS_COMPLETE],
                explanation_template="הדוח עדיין בהכנה. אני מנתחת את הסרטונים של {entity_name} ומכינה עבורך סיכום מקיף.",
                category="output"
            ),

            # Always available actions
            "consultation": ActionDefinition(
                name="consultation",
                description="Ask questions about child development",
                requires=[],
                category="support"
            ),
            "journal": ActionDefinition(
                name="journal",
                description="Add journal entry about observations",
                requires=[],
                category="support"
            )
        }
```

**Alternative Domain** (`/backend/domains/medical_intake/actions.py`):
```python
class MedicalIntakeActions(BaseDomainActions):
    @property
    def actions(self) -> Dict[str, ActionDefinition]:
        return {
            "schedule_appointment": ActionDefinition(
                name="schedule_appointment",
                description="Schedule appointment with provider",
                requires=[PrerequisiteType.INTAKE_COMPLETE, PrerequisiteType.TRIAGE_COMPLETE],
                explanation_template="Before scheduling, we need to complete your intake and assess the urgency of your symptoms.",
                category="workflow"
            ),

            "upload_medical_records": ActionDefinition(
                name="upload_medical_records",
                description="Upload previous medical records",
                requires=[],  # Can upload anytime
                category="data"
            ),

            "view_care_plan": ActionDefinition(
                name="view_care_plan",
                description="View personalized care recommendations",
                requires=[PrerequisiteType.PROVIDER_REVIEW_COMPLETE],
                explanation_template="Your care plan will be ready after the provider reviews your information.",
                category="output"
            )
        }
```

---

### Step 3: Domain-Aware Prompt Builder

**Current** (hardcoded in `/backend/app/prompts/dynamic_interview_prompt.py`):
```python
def build_dynamic_interview_prompt(child_name, age, gender, concerns, ...):
    return f"""You are Chitta - a warm AI assistant for child development...

    Current state:
    - Child: {child_name}, age {age}
    - Concerns: {concerns}
    ...
    """
```

**Proposed** (`/backend/engine/prompt_builder.py`):
```python
class DomainPromptBuilder:
    """Builds contextual prompts using domain configuration"""

    def __init__(self, domain_config: BaseDomainConfig):
        self.domain = domain_config

    def build_intake_prompt(self, session_state: SessionState) -> str:
        """Build prompt for intake/interview phase"""

        data = session_state.extracted_data
        completeness = session_state.completeness

        # Load domain-specific base prompt
        base_prompt = self.domain.prompts.get_base_prompt()

        # Inject current state
        entity_ref = data.get(self.domain.schema.entity_identifier_field, "unknown")

        prompt = f"""{base_prompt}

## Current State

**{self.domain.schema.entity_name.title()}**: {entity_ref}
**Intake Completeness**: {completeness:.0%}

**Extracted So Far**:
{self._format_extracted_data(data)}

**What's Still Missing**:
{self._identify_gaps(data, completeness)}

**Strategic Guidance**:
{session_state.strategic_guidance}

Remember: Extract data continuously and opportunistically from natural conversation.
"""
        return prompt

    def _format_extracted_data(self, data: Dict) -> str:
        """Format extracted data for prompt context"""
        lines = []
        for field_name, definition in self.domain.schema.fields.items():
            value = data.get(field_name)
            if value:
                if isinstance(value, list):
                    lines.append(f"- {definition.description}: {', '.join(value)}")
                elif isinstance(value, str) and len(value) > 100:
                    lines.append(f"- {definition.description}: {len(value)} characters of detail")
                else:
                    lines.append(f"- {definition.description}: {value}")

        return "\n".join(lines) if lines else "(No data collected yet)"
```

---

## Example: How It Works End-to-End

### Child Development Domain
```python
# Load domain
from domains.child_development.config import ChildDevelopmentDomain
domain = ChildDevelopmentDomain()

# User message
message = "הבן שלי יוני בן 3 וחצי, והוא לא ממש מדבר"

# Engine extracts based on domain schema
extracted = {
    "child_name": "יוני",
    "age": 3.5,
    "primary_concerns": ["speech"],
    "concern_details": "לא ממש מדבר"
}

# Calculate completeness (based on field weights)
completeness = 0.14  # Just getting started

# Check if actions available
can_view_report = prerequisite_service.check(
    action="view_report",
    state={
        "completeness": 0.14,
        "analysis_complete": False
    }
)
# Returns: False, missing [ANALYSIS_COMPLETE]

# Generate prompt (domain-aware)
prompt = prompt_builder.build(domain, session_state)
# Includes: child dev terminology, Hebrew, empathetic tone
```

### Medical Intake Domain (SAME ENGINE!)
```python
# Load different domain
from domains.medical_intake.config import MedicalIntakeDomain
domain = MedicalIntakeDomain()

# User message
message = "I'm John Smith, 45 years old, having severe chest pain for 2 hours"

# SAME engine extracts based on THIS domain's schema
extracted = {
    "patient_name": "John Smith",
    "age": 45,
    "chief_complaint": "chest pain",
    "symptom_details": "severe chest pain for 2 hours",
    "urgent_symptoms": ["chest_pain"]
}

# SAME completeness calculation (different field weights)
completeness = 0.18

# SAME prerequisite check (different action definitions)
can_schedule = prerequisite_service.check(
    action="schedule_appointment",
    state={
        "completeness": 0.18,
        "triage_complete": False
    }
)
# Returns: False, missing [INTAKE_COMPLETE, TRIAGE_COMPLETE]

# SAME prompt builder (different domain config)
prompt = prompt_builder.build(domain, session_state)
# Includes: medical terminology, English, professional tone
```

---

## Migration Path: Zero Disruption

### Phase 1: Refactor Without Changing Behavior (1 week)
1. Create `/backend/engine/` directory
2. Move generic logic from `interview_service.py` → `extraction_service.py`
3. Move prerequisite checking → stays as-is but uses domain config
4. **NO CHANGES to behavior** - just reorganization

### Phase 2: Extract Current Domain (3 days)
1. Create `/backend/domains/child_development/`
2. Move schema, actions, prompts to domain config
3. Update services to load from domain config
4. **Test that everything still works identically**

### Phase 3: Prove It Works - Add Second Domain (1 week)
1. Create `/backend/domains/medical_intake/`
2. Define medical schema, actions, prompts
3. **Same engine, different domain** - prove the abstraction
4. Demo switching between domains

### Phase 4: Polish & Document (3 days)
1. Add domain registry/factory
2. Document how to add new domains
3. Create domain template

**Total time**: ~2-3 weeks for complete abstraction

**Risk**: LOW - incremental refactoring with testing at each step

---

## Key Benefits

### 1. Simplicity
- **No new concepts** - just explicit configuration
- **Same patterns** - extraction, prerequisites, completeness still work the same way
- **Minimal code changes** - mostly moving files, not rewriting logic

### 2. Clarity
- **Clear separation**: Domain config vs. generic engine
- **Easy to understand**: "Want a new domain? Create a schema, actions, and prompts"
- **No magic**: Simple Python classes, no complex frameworks

### 3. Extensibility
- **New domain in 1-2 days**: Just configuration, no code changes
- **Domain-specific features**: Easy to add custom logic per domain
- **Reusable engine**: Write once, use everywhere

### 4. Maintainability
- **Testability**: Engine tested once, domains tested independently
- **Debugging**: Clear boundaries between layers
- **Evolution**: Can improve engine without touching domains

---

## Comparison: Alternative Approaches (and Why Not)

### ❌ Multi-Tenant with Database Schema
```
Problems:
- Runtime schema is complex
- Hard to version control domain definitions
- Mixing code and data
- Difficult to test
```

### ❌ Plugin Architecture with Dynamic Loading
```
Problems:
- Over-engineered for this use case
- Adds deployment complexity
- Harder to debug
- Unnecessary indirection
```

### ❌ Microservices per Domain
```
Problems:
- Massive infrastructure overhead
- Duplicated engine code
- Network latency
- Operational complexity
```

### ✅ Our Approach: Domain Configs as Code
```
Benefits:
- Version controlled (Git)
- Type-safe (Pydantic)
- Testable (unit tests per domain)
- Simple (just Python modules)
- Fast (no runtime overhead)
```

---

## Code Organization

```
backend/
├── core/                      # Universal infrastructure
│   ├── conversation_service.py   # Main orchestrator (no domain logic)
│   ├── llm/                      # LLM providers
│   └── models.py                 # Base models
│
├── engine/                    # Domain-agnostic workflow engine
│   ├── extraction_service.py     # Extract data based on schema
│   ├── prerequisite_service.py   # Check action feasibility
│   ├── completeness_service.py   # Calculate readiness
│   ├── state_service.py          # Manage session state
│   ├── prompt_builder.py         # Build contextual prompts
│   └── base_schema.py            # Base classes for domains
│
├── domains/                   # Domain-specific configurations
│   ├── child_development/
│   │   ├── schema.py             # What to extract
│   │   ├── actions.py            # Available actions & prerequisites
│   │   ├── completeness.py       # How to calculate readiness
│   │   ├── prompts/
│   │   │   ├── base_prompt.txt   # Core personality/role
│   │   │   ├── strategic.txt     # Strategic guidance templates
│   │   │   └── examples.txt      # Few-shot examples
│   │   ├── knowledge.py          # Domain knowledge base
│   │   └── config.py             # Domain configuration object
│   │
│   ├── medical_intake/
│   │   └── ... same structure
│   │
│   └── legal_case_management/
│       └── ... same structure
│
└── app/
    ├── main.py                   # FastAPI app
    └── api/
        └── routes.py             # API endpoints
```

---

## Real-World Example: Adding Legal Case Management

**Time**: ~2 days for complete working domain

```python
# 1. Create schema (30 minutes)
# domains/legal_case_management/schema.py
class LegalCaseSchema(BaseDomainSchema):
    @property
    def entity_name(self) -> str:
        return "case"

    @property
    def fields(self) -> Dict[str, FieldDefinition]:
        return {
            "case_type": FieldDefinition(type="enum", options=["personal_injury", "contract", "family", "criminal"]),
            "parties_involved": FieldDefinition(type="array"),
            "incident_description": FieldDefinition(type="longtext", weight=0.40),
            "damages_claimed": FieldDefinition(type="text"),
            "timeline": FieldDefinition(type="text"),
            # ... etc
        }

# 2. Define actions (30 minutes)
# domains/legal_case_management/actions.py
class LegalActions(BaseDomainActions):
    @property
    def actions(self) -> Dict[str, ActionDefinition]:
        return {
            "generate_intake_summary": ActionDefinition(
                requires=[PrerequisiteType.INTAKE_COMPLETE]
            ),
            "draft_demand_letter": ActionDefinition(
                requires=[PrerequisiteType.DOCUMENTS_UPLOADED]
            ),
            # ... etc
        }

# 3. Write prompts (4 hours)
# domains/legal_case_management/prompts/base_prompt.txt
"""
You are a legal intake assistant helping attorneys gather case information...
"""

# 4. Configure completeness (1 hour)
# domains/legal_case_management/completeness.py
class LegalCompletenessCalculator(BaseCompletenessCalculator):
    def calculate(self, data: Dict) -> float:
        # Case type + incident_description = 60% of completeness
        # Timeline + parties + damages = 40%
        ...

# 5. Add domain knowledge (2-4 hours)
# domains/legal_case_management/knowledge.py
LEGAL_KNOWLEDGE = {
    "statute_of_limitations": "...",
    "evidence_requirements": "...",
    # ...
}

# 6. Register domain (5 minutes)
# domains/__init__.py
from .legal_case_management.config import LegalCaseManagementDomain

AVAILABLE_DOMAINS = {
    "child_development": ChildDevelopmentDomain(),
    "medical_intake": MedicalIntakeDomain(),
    "legal_case_management": LegalCaseManagementDomain()
}
```

**That's it!** The engine handles everything else:
- ✅ Extraction from conversation
- ✅ Completeness calculation
- ✅ Prerequisite checking
- ✅ Prompt building
- ✅ State management
- ✅ Function calling

---

## Questions & Answers

**Q: Is this over-engineered?**
A: No - we're just making explicit what's already implicit. Current code mixes domain and engine. This separates them cleanly.

**Q: Will this slow down development?**
A: No - faster! Once engine is solid, new domains are just configuration. No code changes needed.

**Q: What about domain-specific features?**
A: Domains can add custom logic via hooks:
```python
class ChildDevelopmentDomain(BaseDomain):
    async def post_extraction_hook(self, data):
        # Custom logic for video guideline generation
        if self.should_generate_guidelines(data):
            await self.generate_video_guidelines(data)
```

**Q: How do we test this?**
A:
- **Engine**: Unit tests once, works for all domains
- **Domains**: Test schema, actions, completeness separately
- **Integration**: Test each domain end-to-end

**Q: Can we mix domains?**
A: Not in same session, but easy to switch domains per user/session

**Q: What about shared functionality?**
A: Create base classes or mixins:
```python
class VideoBasedDomain(BaseDomain):
    # Shared video handling logic

class ChildDevelopmentDomain(VideoBasedDomain):
    # Inherits video capabilities
```

---

## Success Metrics

This abstraction is successful when:

1. ✅ **Adding new domain takes 1-2 days** (vs. weeks of code changes)
2. ✅ **Zero code changes to engine** when adding domains
3. ✅ **Same tests work** for all domains (just different fixtures)
4. ✅ **Clear documentation** of how to add a domain
5. ✅ **Production ready** - child development domain works identically to current

---

## Recommendation

**DO THIS REFACTORING** because:

1. **Low risk** - incremental migration, test at each step
2. **High value** - future domains are 10x faster to build
3. **No complexity** - just explicit configuration
4. **Better code** - clear separation of concerns
5. **Future-proof** - easy to extend and maintain

**Start with Phase 1** (refactor to engine layer) and validate that everything still works. Then proceed to Phase 2 (extract domain config).

---

**Next Steps**: Get feedback on this approach, then start with Phase 1 (creating `/backend/engine/` and moving generic logic).
