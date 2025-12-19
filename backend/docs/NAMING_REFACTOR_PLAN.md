# Naming Refactor Plan

Apply the metaphor architecture from `METAPHOR_ARCHITECTURE.md`.

---

## Overview of Changes

| Before | After | Type |
|--------|-------|------|
| `LivingGestalt` | `Darshan` | Class rename |
| `Extraction` / `extract` | `Perception` / `perceive` | Phase 1 rename |
| `ExplorationCycle` | `Exploration` | Class rename |
| `CuriosityEngine` | `Curiosities` | Class rename |
| `activation` | `pull` | Property rename |
| `facts` | `observations` | Property rename |
| `ClinicalGapDetector` | `ClinicalGaps` | Class rename |
| Professional Summary | Letter | Concept rename |

---

## Phase 1: Core Models (`models.py`)

**File:** `backend/app/chitta/models.py`

### Changes:
1. Rename `ExplorationCycle` class → `Exploration`
2. Rename `facts` field in `Understanding` → `observations`
3. Update all references within the file
4. Update docstrings to use new terminology

### Find & Replace:
```
ExplorationCycle → Exploration
.facts → .observations
facts: → observations:
```

---

## Phase 2: Curiosity (`curiosity.py`)

**File:** `backend/app/chitta/curiosity.py`

### Changes:
1. Rename `CuriosityEngine` class → `Curiosities`
2. Rename `activation` property → `pull` in `Curiosity` class
3. Update all references within the file
4. Update docstrings

### Find & Replace:
```
CuriosityEngine → Curiosities
activation → pull
.activation → .pull
```

---

## Phase 3: Clinical Gaps (`clinical_gaps.py`)

**File:** `backend/app/chitta/clinical_gaps.py`

### Changes:
1. Rename `ClinicalGapDetector` class → `ClinicalGaps`
2. Update docstrings

### Find & Replace:
```
ClinicalGapDetector → ClinicalGaps
```

---

## Phase 4: The Observer (`gestalt.py`)

**File:** `backend/app/chitta/gestalt.py`

### Changes:
1. Rename `LivingGestalt` class → `Darshan`
2. Rename `_build_extraction_prompt` → `_build_perception_prompt`
3. Rename any `extract` methods → `perceive`
4. Update all internal references to renamed classes
5. Update docstrings and comments

### Find & Replace:
```
LivingGestalt → Darshan
_build_extraction_prompt → _build_perception_prompt
extraction → perception
ExplorationCycle → Exploration
CuriosityEngine → Curiosities
ClinicalGapDetector → ClinicalGaps
.facts → .observations
.activation → .pull
```

---

## Phase 5: Service Layer (`service.py`)

**File:** `backend/app/chitta/service.py`

### Changes:
1. Update all references to renamed classes
2. Update method names if any use old terminology
3. Rename "professional summary" references → "letter" where appropriate
4. Update docstrings

### Find & Replace:
```
LivingGestalt → Darshan
ExplorationCycle → Exploration
CuriosityEngine → Curiosities
ClinicalGapDetector → ClinicalGaps
.facts → .observations
.activation → .pull
professional_summary → letter (where appropriate)
```

---

## Phase 6: Formatting (`formatting.py`)

**File:** `backend/app/chitta/formatting.py`

### Changes:
1. Rename `format_extraction_summary` → `format_perception_summary`
2. Update references to renamed properties
3. Update docstrings

### Find & Replace:
```
extraction → perception
.facts → .observations
.activation → .pull
ExplorationCycle → Exploration
```

---

## Phase 7: Tools (`tools.py`)

**File:** `backend/app/chitta/tools.py`

### Changes:
1. Update any references to old terminology in tool descriptions
2. Ensure tool names stay: `notice`, `wonder`, `capture_story` (these are correct)

---

## Phase 8: Synthesis (`synthesis.py`)

**File:** `backend/app/chitta/synthesis.py`

### Changes:
1. Update references to renamed classes/properties
2. Update docstrings

---

## Phase 9: API Routes (`routes.py`)

**File:** `backend/app/api/routes.py`

### Changes:
1. Update all references to renamed classes
2. Consider renaming endpoints if they use old terminology
3. Update docstrings and comments

### Potential endpoint renames:
```
/generate-summary → /write-letter (optional, consider API stability)
```

---

## Phase 10: Tests

**Files:** `backend/tests/*.py`

### Changes:
1. Update all test files to use new names
2. Update test docstrings
3. Run tests to verify nothing broke

---

## Phase 11: Frontend

**Files:** `src/**/*.jsx`, `src/**/*.js`

### Changes:
1. Update any references to old terminology in comments
2. Update variable names if they mirror backend concepts
3. Update UI text if needed:
   - "Professional Summary" → "Letter" (where user-facing)

---

## Phase 12: Documentation

**Files:**
- `CLAUDE.md`
- `backend/docs/*.md`
- Any other documentation

### Changes:
1. Update all references to renamed concepts
2. Ensure consistency with `METAPHOR_ARCHITECTURE.md`

---

## Execution Order

Execute in this order to minimize breakage:

```
1. models.py          (foundation - other files depend on this)
2. curiosity.py       (Curiosity class, Curiosities manager)
3. clinical_gaps.py   (ClinicalGaps)
4. gestalt.py         (Darshan - the big one)
5. formatting.py      (prompt formatting)
6. tools.py           (tool definitions)
7. synthesis.py       (synthesis service)
8. service.py         (orchestration)
9. routes.py          (API layer)
10. tests             (verify everything works)
11. frontend          (UI layer)
12. documentation     (CLAUDE.md, other docs)
```

---

## Verification Steps

After each phase:
1. Run `python -c "from app.chitta import *"` to check imports
2. Run relevant tests
3. Check for any remaining references to old names

After all phases:
1. Run full test suite: `pytest backend/tests/`
2. Start the app and test manually
3. Search codebase for any remaining old terminology:
   ```bash
   grep -r "LivingGestalt" backend/
   grep -r "ExplorationCycle" backend/
   grep -r "CuriosityEngine" backend/
   grep -r "ClinicalGapDetector" backend/
   grep -r "\.activation" backend/
   grep -r "\.facts" backend/
   grep -r "extraction" backend/
   ```

---

## Rollback Plan

Before starting:
1. Commit current state: `git commit -am "Pre-naming-refactor checkpoint"`
2. Create branch: `git checkout -b refactor/metaphor-naming`

If issues arise:
1. `git checkout main` to return to stable state

---

## Notes

- **API Stability**: Consider whether to rename API endpoints or keep them for backwards compatibility
- **Database**: If any field names are persisted in JSON files, those will need migration
- **Gradual vs Big Bang**: Can do all at once (recommended for consistency) or phase by phase

---

## Estimated Scope

| Area | Files | Complexity |
|------|-------|------------|
| Core models | 1 | Medium |
| Curiosity | 1 | Medium |
| Clinical gaps | 1 | Low |
| Gestalt → Darshan | 1 | High |
| Formatting | 1 | Low |
| Tools | 1 | Low |
| Synthesis | 1 | Low |
| Service | 1 | High |
| Routes | 1 | Medium |
| Tests | ~5 | Medium |
| Frontend | ~10 | Low |
| Docs | ~5 | Low |

**Total: ~30 files**

---

*Plan created: December 2025*
