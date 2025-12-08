# Chitta Refactor: Implementation Plan

**Based on**: REFACTOR_PLAN.md v4.0
**Branch**: `refactor/living-gestalt-architecture`
**Goal**: 7 files, ~1800 lines - minimum NECESSARY complexity

---

## Executive Summary

### Current State
| File | Lines | Notes |
|------|-------|-------|
| gestalt.py | 1,303 | 18 dataclasses, completeness calculation |
| service.py | 2,380 | Two-phase works, but mixed concerns |
| tools.py | 1,283 | 16 tools, overly complex |
| reflection.py | 637 | Background async (to be removed) |
| prompt.py | 796 | Builds system prompts |
| cards.py | 380 | Card derivation |
| api_transform.py | 300 | API response formatting |
| **Total** | **7,079** | |

### Target State
| File | Lines | Purpose |
|------|-------|---------|
| gestalt.py | ~400 | Living Gestalt with 3 public methods |
| curiosity.py | ~200 | Unified curiosity model + engine |
| models.py | ~300 | All data models |
| tools.py | ~150 | 5 tool definitions |
| service.py | ~150 | API orchestration |
| reflection.py | ~200 | Synthesis + memory (no background async) |
| formatting.py | ~100 | Prompt formatting utilities |
| **Total** | **~1500** | |

---

## Phase 1: Foundation Models (Day 1-2)

### 1.1 Create `curiosity.py` - Unified Curiosity Model

**New file**: `backend/app/chitta/curiosity.py`

**Contains**:
1. `Curiosity` dataclass - unified model with explicit `type` field
2. `CuriosityEngine` class - activation management

**Key Design Decisions**:
- Type and certainty are **INDEPENDENT**
- Four types: discovery, question, hypothesis, pattern
- 5 perpetual curiosities (always present)
- Dynamic curiosities spawn from conversation

**Implementation Steps**:
```
1. Create curiosity.py with Curiosity dataclass
2. Implement CuriosityEngine with:
   - PERPETUAL class constant (5 curiosities)
   - get_active(understanding) -> List[Curiosity]
   - _calculate_activation(curiosity, understanding) -> float
   - add_curiosity(curiosity)
   - on_fact_learned(fact)
   - on_evidence_added(focus, effect)
   - get_gaps() -> List[str]
3. Write unit tests for activation math
```

**Migration from current code**:
- Replace `GestaltHypotheses` → `Curiosity(type="hypothesis")`
- Replace `GestaltOpenQuestions` → `Curiosity(type="question")`
- Replace `GestaltPatterns` → `Curiosity(type="pattern")`
- Current `exploration.py:Hypothesis` stays for cycle-owned hypotheses

### 1.2 Create `models.py` - Lean Data Models

**New file**: `backend/app/chitta/models.py`

**Contains**:
```python
@dataclass JournalEntry        # 4 fields (was 15)
@dataclass Story               # summary, reveals, domains, significance, timestamp
@dataclass Evidence            # content, effect, source, timestamp
@dataclass ExplorationCycle    # unified with type-specific optional fields
@dataclass ToolCall            # name, args
@dataclass ExtractionResult    # tool_calls, perceived_intent
@dataclass TurnContext         # understanding, curiosities, recent_history, this_message
@dataclass Response            # text, curiosities, open_questions
@dataclass ConversationMemory  # summary, distilled_at, turn_count
@dataclass SynthesisReport     # essence_narrative, patterns, confidence_by_domain, open_questions
```

**Implementation Steps**:
```
1. Create models.py with all dataclasses
2. Ensure backward compatibility with existing exploration.py
3. Add type hints and docstrings
```

**Key Changes**:
- `JournalEntry`: Reduce from 15 fields to 4 (timestamp, summary, learned, significance)
- `ExplorationCycle`: Add `curiosity_type` field, support all 4 types via optional fields
- Remove all completeness-related models

---

## Phase 2: Core Gestalt (Day 3-4)

### 2.1 Rewrite `gestalt.py` - Living Gestalt

**Replace**: `backend/app/chitta/gestalt.py` (1,303 lines → ~400 lines)

**Three Public Methods**:
1. `process_message(message) -> Response`
2. `get_active_curiosities() -> List[Curiosity]`
3. `synthesize() -> Optional[SynthesisReport]`

**Implementation Steps**:
```
1. Create new LivingGestalt class structure
2. Implement _build_turn_context()
3. Implement _phase1_extract() with critical LLM config
4. Implement _phase2_respond() without tools
5. Implement _apply_learnings() - tool call handlers
6. Move prompt building to _build_extraction_prompt() and _build_response_prompt()
7. Implement turn guidance computation
```

**Critical Preservation** (from current code):
```python
# Phase 1 config - DO NOT CHANGE
tool_config=types.ToolConfig(
    function_calling_config=types.FunctionCallingConfig(
        mode=types.FunctionCallingConfigMode.ANY
    )
)
automatic_function_calling=types.AutomaticFunctionCallingConfig(
    disable=True,
    maximum_remote_calls=0  # CRITICAL
)
temperature=0.0

# Phase 2 config
functions=None  # Forces text response
temperature=0.7
```

### 2.2 Create `formatting.py` - Prompt Utilities

**New file**: `backend/app/chitta/formatting.py`

**Contains**:
- `format_understanding(understanding) -> str`
- `format_curiosities(curiosities) -> str`
- `format_cycles(cycles) -> str`
- `format_extraction_summary(extraction) -> str`

**Implementation Steps**:
```
1. Extract formatting logic from current prompt.py
2. Create visual activation bars for curiosities
3. Add type icons (discovery=🔍, question=❓, hypothesis=💡, pattern=🔗)
```

---

## Phase 3: Tools & Service (Day 5-6)

### 3.1 Simplify `tools.py`

**Reduce**: 16 tools → 5 tools

**New Tool Set**:
1. `notice` - Record observation about child
2. `wonder` - Spawn new curiosity (4 types)
3. `capture_story` - Capture meaningful story
4. `add_evidence` - Add evidence to active cycle
5. `spawn_exploration` - Start focused exploration

**Implementation Steps**:
```
1. Create new tools.py with 5 tool definitions
2. Ensure Gemini schema compatibility (required fields)
3. Add detailed tool descriptions guiding LLM usage
```

**Key Migrations**:
| Old Tool | New Tool |
|----------|----------|
| update_child_understanding | notice |
| form_hypothesis | wonder(type="hypothesis") |
| note_pattern | wonder(type="pattern") |
| capture_story | capture_story (simplified) |
| update_hypothesis_evidence | add_evidence |
| start_exploration | spawn_exploration |
| **REMOVE** | ask_about_child, ask_about_app, generate_synthesis, complete_exploration, etc. |

### 3.2 Simplify `service.py`

**Reduce**: 2,380 lines → ~150 lines

**New Structure**:
```python
class ChittaService:
    def __init__(llm_provider)
    async def process_message(family_id, message) -> Dict
    async def _get_gestalt_with_transition_check(family_id) -> LivingGestalt
    def _is_session_transition(session) -> bool
    def _persist_gestalt(family_id, gestalt)
    def _derive_cards(gestalt) -> List[Dict]
    async def request_synthesis(family_id) -> SynthesisReport
```

**Implementation Steps**:
```
1. Move two-phase logic INTO gestalt.py
2. Keep service as thin orchestration layer
3. Implement session transition detection (>4 hour gap)
4. Implement card derivation (video suggestion, synthesis available)
```

**Key Removal**:
- All 20 tool handlers → Move into gestalt.py `_apply_learnings()`
- Background reflection spawning → Remove entirely
- Completeness calculation → Remove entirely

---

## Phase 4: Reflection & Memory (Day 7)

### 4.1 Rewrite `reflection.py`

**Replace**: Background async → Synchronous on-demand

**New Structure**:
```python
class SynthesisService:
    def __init__(llm_provider)
    async def synthesize(child) -> SynthesisReport  # Strongest model
    async def distill_memory_on_transition(session, child) -> ConversationMemory  # Regular model
    def should_synthesize(child) -> bool
```

**Implementation Steps**:
```
1. Remove ReflectionQueue and ReflectionTask
2. Remove all async background processing
3. Implement synchronous synthesize() with strongest model
4. Implement distill_memory_on_transition() for session gaps
5. Implement should_synthesize() conditions
```

**When Things Happen**:
| Action | Trigger |
|--------|---------|
| Memory distillation | Session transition (>4 hour gap) |
| Pattern detection | Part of synthesize() |
| Synthesis report | User request OR conditions ripe |

---

## Phase 5: Delete Old Code (Day 8)

### Files to Delete/Replace

```bash
# Replace entirely
backend/app/chitta/gestalt.py     # Replace with new ~400 line version
backend/app/chitta/tools.py       # Replace with new ~150 line version
backend/app/chitta/service.py     # Replace with new ~150 line version
backend/app/chitta/reflection.py  # Replace with new ~200 line version

# Delete entirely
backend/app/chitta/prompt.py      # Logic moves into gestalt.py
backend/app/chitta/cards.py       # Logic moves into service.py
backend/app/chitta/api_transform.py  # Simplify into service.py

# Keep but update
backend/app/models/exploration.py  # Keep ExplorationCycle, update for curiosity types
backend/app/models/child.py        # Keep, remove completeness references
```

### Code to Remove from Existing Files

**service.py**:
- Lines 1096, 1201: Remove completeness threshold checks
- Lines 658-661: Remove completeness recalculation
- Lines 230-247: Remove background reflection spawning
- All 20 `_handle_*` methods → consolidate into gestalt.py

**gestalt.py**:
- `GestaltCompleteness` class (lines 413-451)
- `_calculate_completeness_from_child()` (lines 982-1081)
- `get_conversation_priority()` that uses completeness (lines 1239-1308)

**prompt.py**:
- Line 396: Remove completeness in system prompt
- Entire file moves into gestalt.py prompt building methods

---

## Phase 6: Frontend Updates (Day 9-10)

### API Response Changes

**Before**:
```json
{
  "response": "...",
  "completeness": { "score": 0.65, "sections": {...} }
}
```

**After**:
```json
{
  "response": "...",
  "curiosity_state": {
    "active_curiosities": [...],
    "open_questions": [...]
  },
  "cards": [...]
}
```

### Frontend Files to Update

```
src/App.jsx                    # Remove completeness, add curiosityState
src/api/client.js             # Update response parsing
src/components/ProgressBar.jsx # DELETE
src/components/CuriosityPanel.jsx  # NEW
src/components/ActionCard.jsx # Update for new card types
src/components/DeepView.jsx   # Add synthesis request
src/styles/curiosity.css      # NEW
```

---

## Phase 7: Testing & Polish (Day 11-12)

### Unit Tests (No LLM)

```python
# backend/tests/test_curiosity.py
- test_activation_decay_over_time
- test_evidence_boosts_activation
- test_high_certainty_dampens_activation
- test_four_curiosity_types_supported

# backend/tests/test_exploration_cycle.py
- test_evidence_supports_increases_confidence
- test_evidence_contradicts_decreases_confidence

# backend/tests/test_session_transition.py
- test_four_hour_gap_triggers_transition
- test_short_gap_no_transition
```

### Integration Tests (With LLM)

```python
# backend/tests/test_gestalt_integration.py
- test_phase1_returns_tool_calls_only
- test_phase2_returns_text_only
- test_story_triggers_capture_story_tool

# backend/tests/test_turn_guidance.py
- test_story_extraction_gives_story_guidance
- test_no_extraction_gives_natural_guidance
```

### Conversation Quality Tests

```python
# backend/tests/test_conversation_quality.py
- GOLDEN_CONVERSATIONS with expectations
- test_story_reception
- test_direct_question
- test_emotional_expression
```

---

## Implementation Order Summary

| Day | Task | Output |
|-----|------|--------|
| 1 | Create curiosity.py | Unified curiosity model |
| 2 | Create models.py | Lean data models |
| 3 | Rewrite gestalt.py (Part 1) | LivingGestalt shell + phase1 |
| 4 | Rewrite gestalt.py (Part 2) | phase2 + tool handlers |
| 5 | Simplify tools.py | 5 tools |
| 6 | Simplify service.py | Thin orchestration |
| 7 | Rewrite reflection.py | Sync synthesis service |
| 8 | Delete old code | Clean codebase |
| 9 | Frontend changes | New components |
| 10 | Frontend polish | Styling, UX |
| 11 | Unit tests | Test coverage |
| 12 | Integration tests | End-to-end validation |

---

## Success Criteria

- [ ] 7 files in backend/app/chitta/
- [ ] ~1800 lines total (with two-phase, slightly more than 1500)
- [ ] One `Curiosity` model with explicit type field
- [ ] Certainty independent of type
- [ ] 4-field JournalEntry
- [ ] **No completeness anywhere**
- [ ] **Two-phase architecture preserved**
- [ ] **Intent detection by LLM, not keywords**
- [ ] Turn guidance from extraction results
- [ ] Active cycles in prompt with type indicator
- [ ] Session transition triggers memory distillation
- [ ] Pattern detection in synthesis (on demand)
- [ ] **No background async processing**

---

## Risk Mitigation

### High Risk: Breaking Two-Phase Architecture
**Mitigation**:
- Copy exact LLM config from current service.py
- Test with X-Ray framework before/after
- Keep critical comments in code

### Medium Risk: Data Migration
**Mitigation**:
- Add backward-compat properties to ExplorationCycle
- Run both systems in parallel during transition
- Gradual migration of existing Child data

### Medium Risk: Frontend Breaking
**Mitigation**:
- Add feature flag for new curiosity_state
- Keep completeness in response during transition
- Coordinate frontend/backend deployment

---

## Files Created by This Plan

### New Files
```
backend/app/chitta/curiosity.py      # NEW
backend/app/chitta/models.py         # NEW
backend/app/chitta/formatting.py     # NEW
src/components/CuriosityPanel.jsx    # NEW
src/styles/curiosity.css             # NEW
backend/tests/test_curiosity.py      # NEW
backend/tests/test_session_transition.py  # NEW
```

### Replaced Files
```
backend/app/chitta/gestalt.py        # 1303 → ~400 lines
backend/app/chitta/tools.py          # 1283 → ~150 lines
backend/app/chitta/service.py        # 2380 → ~150 lines
backend/app/chitta/reflection.py     # 637 → ~200 lines
```

### Deleted Files
```
backend/app/chitta/prompt.py         # Merged into gestalt.py
backend/app/chitta/cards.py          # Merged into service.py
backend/app/chitta/api_transform.py  # Merged into service.py
```

---

*Version 1.0 - Implementation Plan*
*December 2025*
