# state_derivation.py - DEPRECATED

## ⚠️ This file is deprecated and violates Wu Wei architecture

**Date**: 2025-11-15
**Reason**: Hardcoded card logic bypasses YAML configuration

## What's Wrong

The `derive_active_cards()` function in `state_derivation.py` contains **hardcoded Python logic** for determining which cards to show. This violates the Wu Wei principle of configuration-driven behavior.

### Example of Hardcoded Logic:
```python
def derive_active_cards(state: dict) -> list:
    cards = []

    if not state.get('child'):
        cards.append({
            "id": "welcome",
            "type": "info",
            # ... hardcoded card content
        })

    if state.get('completeness', 0) >= 0.80:
        cards.append({
            "id": "ready_for_videos",
            # ... hardcoded card content
        })

    # ... more hardcoded conditions
    return cards
```

**Problems:**
1. Card logic scattered across Python code instead of centralized in YAML
2. Impossible to configure without code changes
3. Frontend gets these hardcoded cards, ignoring `context_cards.yaml`
4. No single source of truth for UI behavior

## Migration Path

### ✅ CORRECT Approach (Wu Wei Compliant)

Cards should be defined in **`backend/config/workflows/context_cards.yaml`**:

```yaml
welcome_card:
  name: "Welcome"
  card_type: info
  priority: 100

  display_conditions:
    child.name: null  # Show when no child name yet

  content:
    title: "ברוכים הבאים!"
    body: "בואו נתחיל להכיר את הילד/ה שלכם..."
```

Then evaluated by **`CardGenerator.get_visible_cards()`**:
```python
# conversation_service.py
cards = self.card_generator.get_visible_cards(context)  # ✅ YAML-driven
```

### Migration Steps

1. **Identify all cards** in `derive_active_cards()`
2. **Convert each to YAML** in `context_cards.yaml`
3. **Update routes.py** to use `card_generator` instead of `derive_active_cards()`
4. **Delete `state_derivation.py`** entirely

### Current Status

**✅ FIXED** (as of 2025-11-15):
- `routes.py:263` now uses cards from `conversation_service` (YAML-driven)
- `derive_active_cards()` is no longer called
- SSE real-time updates notify frontend of card changes

**⚠️ TODO**:
- Delete `state_derivation.py` file entirely
- Remove import from `routes.py`
- Verify all cards from `derive_active_cards()` exist in `context_cards.yaml`

## Replacement

**Old (Hardcoded)**:
```python
from app.services.state_derivation import derive_active_cards
cards = derive_active_cards(state)
```

**New (YAML-Driven)**:
```python
# In conversation_service.py - cards already evaluated
context_cards = self._generate_context_cards(...)
# Returns cards from context_cards.yaml based on current context

# In routes.py - use cards from conversation response
cards_from_conversation = result.get("context_cards", [])
```

## Why This Matters

The Wu Wei philosophy is about **emergence from configuration**, not hardcoded logic:

- **Configuration** = Single source of truth (YAML)
- **Hardcoded logic** = Scattered, difficult to maintain
- **Wu Wei** = Behavior emerges from prerequisites, no forced stages

`state_derivation.py` represents the **old way** of thinking - staged, hardcoded, imperative.
`context_cards.yaml` + `card_generator.py` represents the **Wu Wei way** - declarative, emergent, configurable.

---

**Do not use this file.** If you see code importing from `state_derivation`, replace it with YAML-driven card evaluation.
