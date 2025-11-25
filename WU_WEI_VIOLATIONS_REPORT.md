# Wu Wei Architecture Violations Report
**Date**: 2025-11-24
**Analysis**: Code polluted with domain-specific terms where configuration should be used

---

## Executive Summary

After analyzing the codebase against the Wu Wei Developer Guide principles, I found **several categories of violations** where domain-specific concepts have leaked into the framework layer. These violations make the system less flexible and harder to extend with new features.

**Key Principle Violated:**
> "Domain concepts go in YAML. Framework stays generic in Python."

---

## Category 1: Hardcoded Domain-Specific Artifact IDs

### ❌ Problem: Framework code references specific artifact names

**Wu Wei Guide Says:**
> "Don't hardcode responses in Python. Instead, use existing mechanisms and configure in YAML."

**Locations Found:**

#### 1.1 `lifecycle_manager.py` - Special Case Handling

**Lines 132-154:**
```python
# ❌ VIOLATION: Hardcoded artifact-specific validation
if artifact_id and session.has_artifact(artifact_id):
    if artifact and artifact_id == "baseline_video_guidelines":  # 🚩 Domain-specific!
        # Parse content to check if scenarios exist
        try:
            import json
            if isinstance(artifact.content, str):
                content = json.loads(artifact.content)
            else:
                content = artifact.content

            scenarios = content.get("scenarios", [])
            if len(scenarios) == 0:
                logger.info(f"  ↳ Artifact {artifact_id} exists but has 0 scenarios - forcing regeneration")
```

**Why This is Wrong:**
- Framework code knows about `"baseline_video_guidelines"` (domain concept)
- Framework code knows about `"scenarios"` field (domain structure)
- Adding new artifact types requires modifying framework code

**Wu Wei Fix:**
```yaml
# artifacts.yaml
artifacts:
  baseline_video_guidelines:
    validation:
      type: "json_field_check"
      field: "scenarios"
      min_length: 1
      on_invalid: "force_regeneration"
```

#### 1.2 `lifecycle_manager.py` - Artifact Generation Logic

**Lines 577-605:**
```python
# ❌ VIOLATION: Hardcoded artifact-specific generation logic
if artifact_id == "baseline_video_guidelines":  # 🚩 Domain-specific!
    return await self.artifact_service.generate_video_guidelines(context)

# Get video_analysis artifact from context
video_analysis_artifact = context.get("artifacts", {}).get("baseline_video_analysis")  # 🚩 Domain-specific!
if not video_analysis_artifact or not video_analysis_artifact.get("exists"):
    logger.error(f"Cannot generate parent report: video_analysis not ready")
    raise ValueError("Video analysis not ready")

video_analysis = json.loads(video_analysis_artifact.get("content", "{}"))
return await self.artifact_service.generate_parent_report(context, video_analysis)

elif artifact_id == "baseline_parent_report":  # 🚩 Domain-specific!
    # Get video_analysis artifact from context
    video_analysis_artifact = context.get("artifacts", {}).get("baseline_video_analysis")  # 🚩 Domain-specific!
```

**Why This is Wrong:**
- Framework knows about specific artifact IDs: `baseline_video_guidelines`, `baseline_parent_report`, `baseline_video_analysis`
- Framework knows about dependencies between artifacts (parent_report needs video_analysis)
- Adding new artifacts requires modifying this switch statement

**Wu Wei Fix:**
```yaml
# artifacts.yaml (with dependencies)
artifacts:
  baseline_video_guidelines:
    generator: "generate_video_guidelines"
    requires: []

  baseline_parent_report:
    generator: "generate_parent_report"
    requires:
      - baseline_video_analysis  # Dependency declared in config
    generator_params:
      video_analysis_source: "baseline_video_analysis"
```

#### 1.3 `artifact_generation_service.py` - Hardcoded Method Names

**Lines 61-142:**
```python
async def generate_video_guidelines(  # 🚩 Domain-specific method name!
    self,
    session_data: Dict[str, Any]
) -> Artifact:
    """
    Generate personalized video recording guidelines using two-stage LLM approach.

    Wu Wei: This is triggered when knowledge is rich (qualitative check).
    """
    artifact_id = "baseline_video_guidelines"  # 🚩 Domain-specific!
```

**Why This is Wrong:**
- Service has domain-specific method: `generate_video_guidelines()`
- Method name is about child development domain, not framework concept
- Cannot add new artifact types without adding new methods

**Wu Wei Fix:**
```python
async def generate_artifact(
    self,
    artifact_id: str,
    session_data: Dict[str, Any]
) -> Artifact:
    """Generic artifact generator - uses config to determine how to generate."""

    # Get artifact config from YAML
    artifact_config = self.artifact_manager.get_config(artifact_id)

    # Get prompt template from config
    prompt_template = artifact_config.get("prompt_template")

    # Generate using LLM with config-driven prompt
    content = await self._generate_with_template(prompt_template, session_data)
```

#### 1.4 `state_derivation.py` - Domain-Specific Checks

**Lines 18, 126, 182:**
```python
# ❌ VIOLATION: Framework code checks for specific artifact
if "baseline_video_guidelines" in state.artifacts:  # 🚩 Domain-specific!
```

**Wu Wei Fix:**
```python
# Generic check using artifact capabilities
def has_capability(state, capability_name: str) -> bool:
    """Check if state has capability (from config)"""
    required_artifacts = capability_config.get(capability_name, {}).get("requires", [])
    return all(artifact in state.artifacts for artifact in required_artifacts)
```

---

## Category 2: Domain-Specific Status Fields in Framework Models

### ❌ Problem: FamilyState/SessionState polluted with domain concepts

**Wu Wei Guide Says:**
> "If it's about the child/family (domain), it goes in `ExtractedData`. If it's about the system (framework), it goes in state."

**Locations Found:**

#### 2.1 `session_service.py` - Domain Status Field

**Line 176:**
```python
class SessionState(BaseModel):
    # ... framework fields ...

    video_analysis_status: Optional[str] = None  # 🚩 Domain-specific!
    # "pending", "analyzing", "complete"
```

**Why This is Wrong:**
- `video_analysis_status` is about a specific domain feature (video analysis)
- Framework model should not know about "video analysis" concept
- What about other analysis types? (photo analysis, audio analysis, etc.)

**Wu Wei Fix:**
```python
# Move to artifact status (generic framework concept)
class Artifact(BaseModel):
    status: str  # "pending", "generating", "ready", "error"

# Or move to extracted_data if it's user preference
class ExtractedData(BaseModel):
    analysis_preferences: Optional[Dict[str, str]] = None
    # {"video": "wants_analysis", "photo": "skip"}
```

#### 2.2 `prerequisite_service.py` - Domain Field Mapping

**Lines 231-232:**
```python
# ❌ VIOLATION: Framework knows about video_analysis domain concept
"video_analysis_status": session_data.get("video_analysis_status", "pending"),  # 🚩 Domain-specific!

# videos_analyzed: true when video_analysis_status == "complete"
"videos_analyzed": session_data.get("video_analysis_status") == "complete",  # 🚩 Domain-specific!
```

**Wu Wei Fix:**
```yaml
# lifecycle_events.yaml - Define what "videos_analyzed" means in config
prerequisites:
  videos_analyzed:
    type: "artifact_status_check"
    artifact: "baseline_video_analysis"
    status: "ready"
```

---

## Category 3: Hardcoded Hebrew Text in Python Code

### ❌ Problem: Domain messages hardcoded in routes and services

**Wu Wei Guide Says:**
> "Don't hardcode Hebrew text in Python. Put it in YAML."

**Locations Found:**

#### 3.1 `routes.py` - Hardcoded Demo/Test Mode Messages

**Lines 186-227:**
```python
# ❌ VIOLATION: Hebrew text hardcoded in Python
if action == "start_demo":
    # ...
    return SendMessageResponse(
        response=demo_result["first_message"]["content"],  # From config ✅
        stage="demo",
        ui_data={
            "demo_mode": True,
            # ...
            "suggestions": ["המשך דמו", "עצור דמו", "דלג לשלב הבא"],  # 🚩 Hardcoded Hebrew!
            "progress": 0
        }
    )

elif action == "start_test_mode":
    # ...
    return SendMessageResponse(
        response=f"🧪 מצב בדיקה\n\nהבנתי שאת רוצה לבדוק את המערכת! יש לי {len(personas)} פרסונות הורים מוכנות:\n\n{persona_list}\n\nכדי להתחיל, השתמשי ב-API של מצב הבדיקה (/test/start) או בממשק המיוחד למפתחים.",  # 🚩 Hardcoded Hebrew!
        stage="interview",
        ui_data={
            "test_mode_available": True,
            "personas": personas,
            "suggestions": ["המשך שיחה רגילה"],  # 🚩 Hardcoded Hebrew!
            # ...
        }
    )
```

**Why This is Wrong:**
- Hebrew text embedded in Python routes
- Cannot change messages without modifying code
- Translation/localization impossible

**Wu Wei Fix:**
```yaml
# app_information.yaml
system_messages:
  demo_mode_start:
    suggestions:
      - "המשך דמו"
      - "עצור דמו"
      - "דלג לשלב הבא"

  test_mode_start:
    response: "🧪 מצב בדיקה\n\nהבנתי שאת רוצה לבדוק את המערכת! יש לי {persona_count} פרסונות הורים מוכנות:\n\n{persona_list}\n\nכדי להתחיל, השתמשי ב-API של מצב הבדיקה."
    suggestions:
      - "המשך שיחה רגילה"
```

#### 3.2 `routes.py` - Hardcoded Keyword Detection

**Lines 159-180:**
```python
# ❌ VIOLATION: Hardcoded domain keywords for system actions
message_lower = request.message.lower()
action = None

# Check for demo mode triggers
import re
if any(re.search(r'\b' + re.escape(trigger) + r'\b', message_lower) for trigger in ['demo', 'start demo', 'start_demo']):  # 🚩 Hardcoded keywords!
    action = "start_demo"
elif any(re.search(r'(?:^|[\s])' + re.escape(trigger) + r'(?:[\s]|$)', message_lower) for trigger in ['דמו', 'התחל דמו']):  # 🚩 Hardcoded keywords!
    action = "start_demo"

# Check for test mode triggers
elif not is_in_test_mode and (
    any(re.search(r'\b' + re.escape(trigger) + r'\b', message_lower) for trigger in ['test', 'start test', 'start_test']) or  # 🚩 Hardcoded keywords!
    any(re.search(r'(?:^|[\s])' + re.escape(trigger) + r'(?:[\s]|$)', message_lower) for trigger in ['טסט', 'מצב בדיקה'])  # 🚩 Hardcoded keywords!
):
    action = "start_test_mode"
```

**Why This is Wrong:**
- Keywords hardcoded in routes (not configuration)
- Cannot add new triggers without code changes
- Hebrew and English mixed in code

**Wu Wei Fix:**
```yaml
# app_information.yaml
system_triggers:
  start_demo:
    keywords:
      en: ["demo", "start demo", "start_demo"]
      he: ["דמו", "התחל דמו"]
    pattern: "word_boundary"

  start_test_mode:
    keywords:
      en: ["test", "start test", "start_test"]
      he: ["טסט", "מצב בדיקה"]
    pattern: "word_boundary"
```

#### 3.3 `routes.py` - Hardcoded Error Messages

**Lines 308, 241:**
```python
# ❌ VIOLATION: Hardcoded Hebrew error message
return SendMessageResponse(
    response="מצטערת, נתקלתי בבעיה טכנית. בואי ננסה שוב.",  # 🚩 Hardcoded Hebrew!
    ui_data={
        "suggestions": ["נסה שוב", "דבר עם תמיכה"],  # 🚩 Hardcoded Hebrew!
        # ...
    }
)

# Line 241
action_validation = {
    "action": action_requested,
    "feasible": False,
    "explanation": f"פעולה לא מוכרת: {action_requested}"  # 🚩 Hardcoded Hebrew!
}
```

**Wu Wei Fix:**
```yaml
# app_information.yaml
error_messages:
  technical_error:
    response: "מצטערת, נתקלתי בבעיה טכנית. בואי ننסה שוב."
    suggestions:
      - "נסה שוב"
      - "דבר עם תמיכה"

  unknown_action:
    explanation: "פעולה לא מוכרת: {action_id}"
```

---

## Category 4: Business Logic in Routes

### ❌ Problem: Domain logic embedded in API layer

**Wu Wei Guide Says (Anti-Pattern #3):**
> "Business logic in routes is bad. Domain logic hardcoded in API layer. Fix: Let lifecycle system handle it."

**Locations Found:**

#### 4.1 `routes.py` - Demo/Test Mode Logic

**Lines 157-227:**
```python
# ❌ VIOLATION: Business logic in routes
# 🎯 Simple Keyword Detection: Check for system actions (test/demo mode)
message_lower = request.message.lower()
action = None

# 🚨 Check if already in test mode (prevents recursive triggering)
simulator = get_parent_simulator()
is_in_test_mode = request.family_id in simulator.active_simulations

# Check for demo mode triggers - use word boundaries to avoid false matches
import re
if any(re.search(r'\b' + re.escape(trigger) + r'\b', message_lower) for trigger in ['demo', 'start demo', 'start_demo']):
    action = "start_demo"
# ... 60+ lines of domain logic in routes ...

# Handle system/developer actions
if action:
    # 🎬 Demo Mode
    if action == "start_demo":
        demo_orchestrator = get_demo_orchestrator()
        scenario_id = "language_concerns"  # Default scenario
        demo_result = await demo_orchestrator.start_demo(scenario_id)

        return SendMessageResponse(
            response=demo_result["first_message"]["content"],
            stage="demo",
            ui_data={
                "demo_mode": True,
                # ... build UI data here ...
            }
        )
```

**Why This is Wrong:**
- Routes contain 70+ lines of domain logic
- Keyword detection logic mixed with API handling
- Response construction in routes (should be in service)
- Cannot reuse this logic from other entry points

**Wu Wei Fix:**
```python
# routes.py - Thin API layer
@router.post("/chat/send")
async def send_message(request: SendMessageRequest):
    """Thin route - delegates to service"""
    conversation_service = get_simplified_conversation_service()

    result = await conversation_service.process_message(
        family_id=request.family_id,
        user_message=request.message
    )

    return SendMessageResponse(
        response=result["response"],
        ui_data=result["ui_data"]
    )

# conversation_service.py - Business logic
async def process_message(self, family_id: str, user_message: str):
    # Check for system triggers (from config)
    system_action = self.detect_system_action(user_message)

    if system_action:
        return await self.handle_system_action(system_action, family_id)

    # Normal conversation flow
    return await self.process_normal_message(family_id, user_message)
```

#### 4.2 `routes.py` - Artifact Syncing Logic

**Lines 259-277:**
```python
# ❌ VIOLATION: Data synchronization logic in routes
# Sync artifacts to graphiti state (CRITICAL FIX!)
# The state derivation checks state.artifacts, so we must sync them
for artifact_id, artifact in interview_session.artifacts.items():
    if artifact.is_ready:  # Only sync ready artifacts
        await graphiti.add_artifact(
            family_id=request.family_id,
            artifact_type=artifact_id,
            content={"status": "ready", "content": artifact.content}
        )

# Convert artifacts to simplified format for UI
artifacts_for_ui = {}
for artifact_id, artifact in interview_session.artifacts.items():
    artifacts_for_ui[artifact_id] = {
        "exists": artifact.exists,
        "status": artifact.status,
        "artifact_type": artifact.artifact_type,
        "ready_at": artifact.ready_at.isoformat() if artifact.ready_at else None
    }
```

**Why This is Wrong:**
- Routes responsible for data synchronization between systems
- Format conversion logic in API layer
- Violates single responsibility principle

**Wu Wei Fix:**
```python
# Move to session_service.py
class SessionService:
    async def sync_artifacts_to_graphiti(self, family_id: str):
        """Sync artifacts from session to graphiti (internal service method)"""
        session = self.get_or_create_session(family_id)

        for artifact_id, artifact in session.artifacts.items():
            if artifact.is_ready:
                await self.graphiti.add_artifact(
                    family_id=family_id,
                    artifact_type=artifact_id,
                    content={"status": "ready", "content": artifact.content}
                )
```

---

## Category 5: Special Case Anti-Pattern

### ❌ Problem: Artifact-specific handling in generic code

**Wu Wei Guide Anti-Pattern #1:**
> "Every new artifact needs code changes. Fix: Make artifact behavior configurable."

**Locations Found:**

#### 5.1 `lifecycle_manager.py` - Special Scenario Validation

**Lines 652-665:**
```python
# ❌ VIOLATION: Special case for specific artifact
if artifact_id == "baseline_video_guidelines":  # 🚩 Special case!
    # Verify generated scenarios match guideline count
    try:
        import json
        content = json.loads(artifact.content) if isinstance(artifact.content, str) else artifact.content
        scenarios = content.get("scenarios", [])

        if len(scenarios) == 0:
            logger.error(f"❌ Video guidelines generated with 0 scenarios!")
            artifact.mark_error("No scenarios generated")
        else:
            logger.info(f"✅ Video guidelines has {len(scenarios)} scenarios")
    except Exception as e:
        logger.warning(f"⚠️ Could not validate guideline scenarios: {e}")
```

**Why This is Wrong:**
- Framework code has special validation logic for one specific artifact
- What about other artifacts that need validation? Add more if statements?
- Cannot extend validation logic without modifying framework

**Wu Wei Fix:**
```yaml
# artifacts.yaml
artifacts:
  baseline_video_guidelines:
    validation:
      type: "json_structure"
      checks:
        - path: "scenarios"
          type: "array"
          min_length: 1
          error_message: "No scenarios generated"
```

---

## Category 6: Domain-Specific Prompt Content

### ❌ Problem: Clinical domain knowledge embedded in prompts

**Wu Wei Guide Says:**
> "Domain concepts go in YAML. Framework stays generic in Python."

**Locations Found:**

#### 6.1 `artifact_generation_service.py` - Hardcoded Prompt

**Lines 156-200:**
```python
# ❌ VIOLATION: Domain-specific prompt structure hardcoded
def _build_guidelines_prompt(
    self,
    child_name: str,
    age_str: str,
    concerns: list,
    concern_details: str,
    strengths: str
) -> str:
    """Build LLM prompt for generating video guidelines."""

    concerns_text = "\n".join(f"- {c}" for c in concerns) if concerns else "לא צוינו דאגות ספציפיות"

    return f"""
אתה מומחה בהערכה התפתחותית של ילדים. תפקידך ליצור הנחיות צילום מותאמות אישית להורה.  # 🚩 Domain-specific!

**מידע על הילד/ה:**
- שם: {child_name}
- גיל: {age_str}

**דאגות עיקריות:**
{concerns_text}

**פרטים נוספים על הדאגות:**
{concern_details if concern_details else "לא צוינו"}

**חוזקות:**
{strengths if strengths else "לא צוינו"}

**המשימה:**
צור הנחיות צילום מותאמות אישית בעברית שיעזרו להורה לצלם סרטונים שיסייעו בהערכה התפתחותית.  # 🚩 Domain-specific!

**מבנה ההנחיות:**

# הנחיות צילום מותאמות אישית עבור {child_name}

## למה חשוב לצלם?
[הסבר קצר ואישי למה הסרטונים יעזרו - בהקשר לדאגות שהועלו]

## מה לצלם? 3 מצבים מומלצים  # 🚩 Domain-specific structure!
"""
```

**Why This is Wrong:**
- Entire clinical domain structure embedded in Python code
- Prompt talks about "developmental assessment", "child concerns", "filming scenarios"
- Cannot adapt to different domains without rewriting code
- Hebrew template hardcoded

**Wu Wei Fix:**
```yaml
# prompts/video_guidelines.yaml
system_role: "אתה מומחה בהערכה התפתחותית של ילדים"

task: "צור הנחיות צילום מותאמות אישית בעברית"

input_structure:
  - field: child_name
    label: "שם"
  - field: age
    label: "גיל"
  - field: primary_concerns
    label: "דאגות עיקריות"
    format: "bullet_list"
  - field: concern_details
    label: "פרטים נוספים"
  - field: strengths
    label: "חוזקות"

output_structure:
  title: "הנחיות צילום מותאמות אישית עבור {child_name}"
  sections:
    - heading: "למה חשוב לצלם?"
      instruction: "הסבר קצר ואישי בהקשר לדאגות"
    - heading: "מה לצלם? 3 מצבים מומלצים"
      instruction: "3 תרחישי צילום רלוונטיים"
      subsections:
        - "מה לצלם"
        - "למה חשוב"
        - "דוגמה"
```

---

## Summary Table

| Category | Violations Found | Files Affected | Severity |
|----------|-----------------|----------------|----------|
| Hardcoded Artifact IDs | 15+ instances | lifecycle_manager.py, state_derivation.py, artifact_generation_service.py, prerequisite_service.py | 🔴 HIGH |
| Domain Status Fields | 3 instances | session_service.py, prerequisite_service.py | 🟡 MEDIUM |
| Hardcoded Hebrew Text | 10+ instances | routes.py | 🟡 MEDIUM |
| Business Logic in Routes | 70+ lines | routes.py | 🔴 HIGH |
| Special Case Anti-Pattern | 5+ instances | lifecycle_manager.py | 🟡 MEDIUM |
| Domain Prompts in Code | 2 major prompts | artifact_generation_service.py, comprehensive_prompt_builder.py | 🟠 MEDIUM-HIGH |

---

## Impact Assessment

### Development Velocity
- ❌ Adding new artifact types requires changing 5+ files
- ❌ Adding new domain features touches framework code
- ❌ Cannot A/B test different prompts without deployments

### Maintainability
- ❌ Domain logic scattered across framework
- ❌ Difficult to understand what's framework vs domain
- ❌ Hard to test framework independently

### Extensibility
- ❌ Cannot reuse framework for different domains
- ❌ Cannot configure different workflows without code
- ❌ Translation/localization blocked by hardcoded text

---

## Recommended Refactoring Priority

### Phase 1 (High Priority) 🔴
1. **Extract artifact-specific logic from lifecycle_manager.py**
   - Move artifact validation to configuration
   - Make artifact generation dispatch config-driven

2. **Remove business logic from routes.py**
   - Move demo/test mode logic to services
   - Extract keyword detection to configuration
   - Move Hebrew text to YAML

### Phase 2 (Medium Priority) 🟡
3. **Remove domain status fields from SessionState**
   - Move `video_analysis_status` to artifact status
   - Or move to ExtractedData if it's user preference

4. **Extract prompts to configuration**
   - Create prompt templates in YAML
   - Use placeholder substitution system
   - Make prompt structure configurable

### Phase 3 (Lower Priority) 🟢
5. **Refactor special case handling**
   - Create generic validation system
   - Move artifact-specific logic to config
   - Remove hardcoded artifact ID checks

---

## Example: Complete Wu Wei Refactoring

### Before (Current State)
```python
# lifecycle_manager.py - 50+ lines of hardcoded logic
if artifact_id == "baseline_video_guidelines":
    return await self.artifact_service.generate_video_guidelines(context)
elif artifact_id == "baseline_parent_report":
    video_analysis_artifact = context.get("artifacts", {}).get("baseline_video_analysis")
    if not video_analysis_artifact:
        raise ValueError("Video analysis not ready")
    return await self.artifact_service.generate_parent_report(context, video_analysis)
```

### After (Wu Wei)
```yaml
# artifacts.yaml
artifacts:
  baseline_video_guidelines:
    generator: "generate_with_template"
    template: "prompts/video_guidelines.yaml"
    requires: []

  baseline_parent_report:
    generator: "generate_with_template"
    template: "prompts/parent_report.yaml"
    requires:
      - baseline_video_analysis
    generator_params:
      input_artifacts:
        - baseline_video_analysis
```

```python
# lifecycle_manager.py - Generic, config-driven
async def generate_artifact(self, artifact_id: str, context: Dict[str, Any]):
    """Generic artifact generation - all config-driven"""

    # Get artifact config
    config = self.artifact_manager.get_config(artifact_id)

    # Check dependencies
    for required in config.get("requires", []):
        if not context.get("artifacts", {}).get(required, {}).get("exists"):
            raise ValueError(f"Artifact {artifact_id} requires {required}")

    # Get generator method from config
    generator_name = config.get("generator")
    generator = getattr(self.artifact_service, generator_name)

    # Call generator with config params
    return await generator(
        artifact_id=artifact_id,
        template=config.get("template"),
        context=context,
        params=config.get("generator_params", {})
    )
```

---

## Conclusion

The codebase has **significant Wu Wei violations** where domain-specific concepts (child development, video analysis, filming guidelines) have leaked into the framework layer. This makes the system less flexible and harder to extend.

**Key Fix:** Extract all domain-specific artifact IDs, status fields, Hebrew text, and business logic into YAML configuration. Keep the framework generic and domain-agnostic.

**Benefit:** New features can be added by editing YAML files instead of modifying Python code. The system becomes truly configuration-driven as intended.

---

**Generated by**: Wu Wei Architecture Analysis
**Review**: Recommended for architecture team discussion
