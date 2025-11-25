# YAML Configuration Consolidation Plan
## Wu Wei Architecture Simplification

> **פשוט - נטול חלקים עודפים**
> *Simple - devoid of excess parts*

---

## Executive Summary

The current configuration system has **8 YAML files** when **3-4 would suffice**. This plan consolidates them while preserving the domain/framework separation that makes the architecture robust.

### Current State: 8 Files (~4,500 lines)

| File | Lines | Purpose | Verdict |
|------|-------|---------|---------|
| lifecycle_events.yaml | 578 | Moments, prerequisites, messages, some cards | ✅ KEEP (enhance) |
| context_cards.yaml | 750 | UI cards with display conditions | ⚠️ MERGE |
| action_graph.yaml | 295 | Action prerequisites | ⚠️ SIMPLIFY |
| artifacts.yaml | 700 | Artifact metadata & lifecycle | ⚠️ SIMPLIFY |
| artifact_generators.yaml | 123 | Generation method config | ⚠️ MERGE |
| phases.yaml | 241 | Phase definitions | ❌ DELETE |
| deep_views.yaml | 893 | View layouts & behavior | ✅ KEEP |
| app_information.yaml | 357 | FAQ & app info | ✅ KEEP |

### Target State: 4 Files (~2,500 lines)

| File | Purpose |
|------|---------|
| **workflow.yaml** | Moments, cards, prerequisites, artifact triggers |
| **artifacts.yaml** | Artifact metadata, generators, storage |
| **views.yaml** | Deep view layouts (renamed from deep_views) |
| **app_information.yaml** | FAQ, about, privacy info |

---

## Phase 1: Delete phases.yaml (SAFE - Low Risk)

### Rationale
- `lifecycle_events.yaml:551` explicitly states: "No phases. No gates."
- `prerequisite_service.py:247` derives phase from artifacts (`_infer_emergent_state`)
- Phase is only used for backwards compatibility in card display conditions

### Changes Required

**1. Delete file:**
```bash
rm backend/config/workflows/phases.yaml
```

**2. Update config_loader.py:**
```python
# Remove these lines:
# @lru_cache(maxsize=1)
# def load_phases(self) -> Dict[str, Any]:
#     ...

# Remove from load_all():
# "phases": self.load_phases(),

# Remove clear_cache line:
# self.load_phases.cache_clear()
```

**3. Update context_cards.yaml** - Replace phase conditions with artifact conditions:
```yaml
# BEFORE:
display_conditions:
  phase: [ongoing, re_assessment]

# AFTER:
display_conditions:
  artifacts.baseline_parent_report.exists: true  # ongoing = report exists
  # OR for re_assessment:
  re_assessment.active: true
```

**4. Verify no Python imports:**
```bash
grep -r "load_phases" backend/
# Should only find config_loader.py after removal
```

---

## Phase 2: Merge context_cards.yaml into lifecycle_events.yaml

### Rationale
- lifecycle_events.yaml already supports inline `card:` definitions (see `first_message`, `analysis_done`, `report_ready`)
- context_cards.yaml duplicates prerequisite logic
- Having cards in two places is confusing

### Migration Strategy

**A. Event-triggered cards (one-time)** → Already in lifecycle_events.yaml
- `first_message.card` ✅
- `analysis_done.card` ✅
- `report_ready.card` ✅

**B. State-persistent cards** → Move to lifecycle_events.yaml

Each persistent card becomes a "state moment":

```yaml
# BEFORE (context_cards.yaml):
video_guidelines_card:
  name: "הנחיות צילום"
  card_type: action_needed
  priority: 90
  display_conditions:
    filming_preference: "wants_videos"
    artifacts.baseline_video_guidelines.exists: true
    artifacts.baseline_video_guidelines.status: "ready"
    artifacts.baseline_parent_report.exists: false
  content:
    title: "הנחיות הצילום מוכנות! 📹"
    ...

# AFTER (lifecycle_events.yaml):
video_guidelines_available:
  when:
    filming_preference: "wants_videos"
    artifacts.baseline_video_guidelines.status: "ready"
    artifacts.baseline_parent_report.exists: false
  # No artifact, no message - just card display
  card:
    card_type: action_needed
    priority: 90
    title: "הנחיות הצילום מוכנות! 📹"
    body: |
      הכנתי עבורך הנחיות מותאמות אישית...
    actions:
      - view_video_guidelines
      - consultation
    persistent: true  # NEW: Card stays while conditions true
```

**C. Move card_types to lifecycle_events.yaml:**

```yaml
# At top of lifecycle_events.yaml
card_types:
  progress:
    icon: "progress-bar"
    color: "blue"
  action_needed:
    icon: "alert-circle"
    color: "orange"
  success:
    icon: "check-circle"
    color: "green"
  guidance:
    icon: "lightbulb"
    color: "purple"
```

### Cards to Migrate

| Card | Type | Migration |
|------|------|-----------|
| conversation_depth_card | State | → `conversation_deepening` moment |
| child_profile_card | State | → `child_profile_known` moment |
| guidelines_offer_card | Event | → Already handled by `knowledge_rich` moment |
| guidelines_preparing_card | State | → `guidelines_generating` moment |
| video_guidelines_card | State | → `video_guidelines_available` moment |
| generate_report_card | State | → `report_generation_available` moment |
| video_analysis_card | State | → `video_analysis_pending` / `video_analysis_running` |
| ongoing_welcome_card | Event | → `entered_ongoing_phase` moment |
| journal_card | State | → `journal_available` moment |
| follow_up_summary_ready_card | Event | → `follow_up_summary_ready` moment |
| expert_finder_card | State | → `experts_available` moment |
| re_assessment_welcome_card | Event | → `re_assessment_started` moment |
| re_assessment_progress_card | State | → `re_assessment_in_progress` moment |
| updated_report_ready_card | Event | → `re_assessment_complete` moment |

### Code Changes for card_generator.py

```python
def get_visible_cards(self, context: Dict[str, Any], max_cards: int = 4):
    """
    🌟 Wu Wei: Cards now come from moments in lifecycle_events.yaml
    """
    visible = []

    # Load moments from lifecycle config
    lifecycle_config = load_lifecycle_events()
    moments = lifecycle_config.get("moments", {})
    card_types = lifecycle_config.get("card_types", {})

    for moment_id, moment_config in moments.items():
        card_config = moment_config.get("card")
        if not card_config:
            continue

        # Evaluate prerequisites (when clause)
        prerequisites = moment_config.get("when", {})
        if not self._evaluate_prerequisites(prerequisites, context):
            continue

        # Card should be visible
        visible.append(self._build_card(moment_id, card_config, card_types, context))

    return sorted(visible, key=lambda c: c.get("priority", 0), reverse=True)[:max_cards]
```

---

## Phase 3: Simplify action_graph.yaml

### Rationale
- Actions are already gated by artifact existence
- action_graph.yaml mostly duplicates prerequisite logic from lifecycle_events.yaml

### Strategy: Derive actions from artifacts

**Insight:** If `baseline_video_guidelines` artifact exists → `view_video_guidelines` action available

```yaml
# SIMPLIFIED action_graph.yaml:
version: "2.0"

# Always available actions (no prerequisites)
always_available:
  - consultation
  - add_journal_entry
  - view_journal
  - continue_interview

# Actions derived from artifacts
artifact_actions:
  baseline_video_guidelines:
    enables: [view_video_guidelines, upload_video]
    explanation_when_locked: "ההנחיות עדיין לא מוכנות. אני צריכה עוד קצת מידע על {child_name}."

  baseline_parent_report:
    enables: [view_report, download_report, share_report, find_experts, contact_expert]
    explanation_when_locked: "הדוח עדיין לא מוכן. הוא יהיה זמין אחרי שנסיים את הניתוח."

# Categories for UI grouping only
categories:
  interview: { icon: "message-circle" }
  video: { icon: "video" }
  reports: { icon: "file-text" }
  experts: { icon: "users" }
  support: { icon: "help-circle" }
```

### Code Change: action_registry.py

```python
def get_available_actions(self, context: Dict[str, Any]) -> List[str]:
    """Derive available actions from artifacts."""
    available = set(self.config.get("always_available", []))

    artifacts = context.get("artifacts", {})
    artifact_actions = self.config.get("artifact_actions", {})

    for artifact_id, action_config in artifact_actions.items():
        artifact = artifacts.get(artifact_id)
        if artifact and artifact.get("exists") and artifact.get("status") == "ready":
            available.update(action_config.get("enables", []))

    return list(available)
```

---

## Phase 4: Merge artifact_generators.yaml into artifacts.yaml

### Rationale
- Two files defining the same artifacts with different naming (`video_guidelines` vs `baseline_video_guidelines`)
- Generation config belongs with artifact definition

### Target Structure

```yaml
# artifacts.yaml (simplified)
version: "2.0"

artifacts:
  baseline_interview_summary:
    name: "סיכום ראיון"
    type: analysis
    generator:
      method: "generate_interview_summary"
      requires_artifacts: []  # Uses session data
    storage: "sessions/{session_id}/artifacts/interview_summary.json"

  baseline_video_guidelines:
    name: "הנחיות צילום"
    type: guidelines
    generator:
      method: "generate_video_guidelines"
      requires_artifacts: [baseline_interview_summary]
      validation:
        type: json_structure
        checks:
          - path: scenarios
            type: array
            min_length: 1
    storage: "sessions/{session_id}/artifacts/video_guidelines.json"

  baseline_professional_report:
    name: "דוח מקצועי"
    type: report
    generator:
      method: "generate_professional_report"
      requires_artifacts: [baseline_interview_summary]
      optional_artifacts: [baseline_video_analysis]
    storage: "sessions/{session_id}/artifacts/professional_report.md"

  baseline_parent_report:
    name: "דוח הורים"
    type: report
    generator:
      method: "generate_parent_report"
      requires_artifacts: [baseline_professional_report]
    storage: "sessions/{session_id}/artifacts/parent_report.md"

# Artifact types for metadata
artifact_types:
  report:
    format: "markdown/pdf"
    can_download: true
    can_share: true
  guidelines:
    format: "json"
    can_download: true
  analysis:
    format: "json"
    can_download: false
```

### Code Changes

```python
# artifact_manager.py
def get_generator_config(self, artifact_id: str) -> Optional[Dict]:
    """Get generator config from artifacts.yaml"""
    artifact = self.config.get("artifacts", {}).get(artifact_id)
    if artifact:
        return artifact.get("generator")
    return None
```

---

## Phase 5: Rename Files

```bash
# After all migrations complete
mv backend/config/workflows/lifecycle_events.yaml backend/config/workflows/workflow.yaml
mv backend/config/workflows/deep_views.yaml backend/config/workflows/views.yaml

# Delete merged files
rm backend/config/workflows/context_cards.yaml
rm backend/config/workflows/artifact_generators.yaml
rm backend/config/workflows/phases.yaml
```

Update config_loader.py to match new names.

---

## Migration Order (Safest First)

### Wave 1: Low Risk (No Breaking Changes)
1. ✅ Delete phases.yaml + remove loader
2. ✅ Update card conditions to use artifacts instead of phase

### Wave 2: Medium Risk (Careful Testing Required)
3. ⚠️ Merge context_cards.yaml into lifecycle_events.yaml
4. ⚠️ Update card_generator.py to read from moments

### Wave 3: Higher Risk (Refactoring)
5. ⚠️ Simplify action_graph.yaml
6. ⚠️ Merge artifact_generators into artifacts.yaml
7. ⚠️ Rename files

---

## Verification Checklist

### After Each Phase:
- [ ] Run existing tests: `python -m pytest backend/tests/`
- [ ] Test conversation flow manually
- [ ] Verify cards appear correctly
- [ ] Check artifact generation triggers
- [ ] Verify actions unlock properly

### Specific Tests:
- [ ] New family → first_message card appears
- [ ] Knowledge rich → guidelines offer appears
- [ ] Filming preference set → guidelines generate
- [ ] Guidelines ready → video_guidelines_card appears
- [ ] Report ready → success card + view_report action available

---

## Rollback Plan

Each phase is independently reversible:
1. Git revert the commit
2. Clear config cache: `get_workflow_config_loader().clear_cache()`
3. Restart backend

---

## Benefits After Migration

### Reduced Complexity
- **Before:** 8 files, ~4,500 lines, duplicate prerequisite logic
- **After:** 4 files, ~2,500 lines, single source of truth

### Clearer Mental Model
- **Before:** "Is this card in context_cards or lifecycle_events?"
- **After:** "Everything is in workflow.yaml - moments with optional cards"

### Easier Feature Addition
- **Before:** Add to lifecycle_events + context_cards + maybe action_graph
- **After:** Add one moment to workflow.yaml

### Better Wu Wei Alignment
- Domain logic in YAML (workflow, artifacts)
- UI presentation in YAML (views, app_info)
- Framework code stays generic (Python)

---

## Questions to Consider Before Starting

1. **Should we keep backwards compatibility for existing sessions?**
   - Current sessions have artifact IDs like `baseline_video_guidelines`
   - Migration shouldn't break existing data

2. **Do we want to run parallel configs during migration?**
   - Could load both old and new configs, prefer new
   - Adds complexity but reduces risk

3. **Should card_generator.py be renamed to moment_card_resolver.py?**
   - More accurate name after migration
   - Would require import updates

---

*Written following Wu Wei principle: מינימום המורכבות הנדרשת - Minimum necessary complexity*
