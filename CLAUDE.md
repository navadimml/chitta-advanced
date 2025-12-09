# CLAUDE.md

This file provides the Constitution and Technical Guidance for Claude Code when working on **Chitta**.

## 1. Core Philosophy: The "Why"

**Chitta exists to help parents and clinicians see child development clearly.**

Chitta is an **expert developmental psychologist** (0.5-18 years) - not just a conversationalist.
We are a "Conversation-First" platform with a "Wu Wei" architecture.

*   **Identity**: An expert guide with deep developmental psychology knowledge. We point; we do not replace.
*   **Voice**: "שמתי לב ש..." not "המערכת זיהתה..." (Simple words, deep understanding).
*   **Goal**: Create space for understanding through **curiosity**, not checklists.

### The Living Gestalt

The Gestalt is the **observing intelligence** - it HOLDS, NOTICES, and ACTS.
- Child and Session are its memory
- The Gestalt is the mind
- Understanding emerges through conversation, not assessment

## 2. The 10 Golden Rules (Coding Constitution)

**Strictly adhere to these principles when generating code or logic:**

1.  **Follow the Current (Logic)**:
    *   ❌ No rigid state machines (`if step == 3`).
    *   ✅ Use context-driven logic (`if parent_concerned_about_motor`).
    *   Allow the user to redirect; the system follows.

2.  **Start Fresh (Data)**:
    *   Do not hard-code reliance on past conclusions.
    *   Functions must accept a `context` object to allow for a "fresh look" at new data.

3.  **Adapt Like Water (Polymorphism)**:
    *   ❌ Do not build separate code paths for "Parent" vs "Clinician."
    *   ✅ Build single, adaptive functions that infer tone/depth from context.

4.  **Show, Don't Conclude (Data Model)**:
    *   ❌ `diagnosis: "delayed"` (Interpretive labels are forbidden in raw data).
    *   ✅ `observation: { event: "looked at face", timestamp: "0:03" }` (Descriptive data).

5.  **Be Invisible (UX)**:
    *   Proactive ≠ Pushy. Only trigger logic when `value > interruption_cost`.
    *   Prerequisites determine what is *available/recommended*, never what is *blocked*.

6.  **Simplicity (פשוט)**:
    *   Beauty is the **minimum NECESSARY complexity** - not minimum possible.
    *   מינימום המורכבות הנדרשת - the right amount, not less.

7.  **Honest Uncertainty**:
    *   If confidence is low, return structured data indicating ambiguity.
    *   Never hallucinate certainty or generic errors.

8.  **Emergence**:
    *   Prefer small, composable functions over monolithic "Intelligent Managers."
    *   Intelligence emerges from the interaction of simple parts.

9.  **Naming Convention**:
    *   Use `notice`, `wonder`, `capture_story`, `explore`.
    *   Avoid `diagnose`, `assess`, `decide`, `completeness`.

10. **Natural Language**:
    *   Hebrew output must be natural, warm, and non-robotic.
    *   Preserve `dir="rtl"` in all UI components.

## 3. The Four Curiosity Types

Understanding emerges through **curiosity**, not checklists. Four types:

| Type | Purpose | Example |
|------|---------|---------|
| **discovery** | Open receiving | "Who is this child?" |
| **question** | Following a thread | "What triggers meltdowns?" |
| **hypothesis** | Testing a theory | "Music helps him regulate" |
| **pattern** | Connecting dots | "Sensory input is key across domains" |

**Type and certainty are INDEPENDENT**:
- Type = what kind of exploration activity
- Certainty = how confident within that type

You can have a weak hypothesis (certainty=0.3) or a strong discovery (certainty=0.8).

## 4. Technical Constraints & Critical Implementation

### Two-Phase LLM Architecture (CRITICAL)

**Tool calls and text responses CANNOT be combined reliably.**

We use TWO separate LLM calls per message:

```
Phase 1: Extraction (with tools)
  - temperature=0.0
  - FunctionCallingConfigMode.ANY
  - Returns: tool calls only

Phase 2: Response (without tools)
  - temperature=0.7
  - functions=None
  - Returns: text only
```

### LLM Configuration (Gemini)

**Provider**: Gemini 2.5 Flash (conversation), Gemini 3 Pro Preview (synthesis)

**CRITICAL Configuration** - DO NOT CHANGE:
```python
# Phase 1: Extraction
config_params["tool_config"] = types.ToolConfig(
    function_calling_config=types.FunctionCallingConfig(
        mode=types.FunctionCallingConfigMode.ANY  # Forces tool calls
    )
)
config_params["automatic_function_calling"] = types.AutomaticFunctionCallingConfig(
    disable=True,
    maximum_remote_calls=0  # CRITICAL: Must be 0 to fully disable AFC
)
temperature = 0.0

# Phase 2: Response
functions = None  # NO TOOLS - forces text response
temperature = 0.7
```

**Token Limits**: `max_output_tokens` must be **4000+** to prevent Hebrew truncation.

### Model Tiers

| Tier | Models | Use For |
|------|--------|---------|
| **Strongest** | gemini-3-pro-preview, claude-opus-4-5 | Pattern detection, synthesis |
| **Standard** | gemini-2.5-flash | Conversation, memory distillation |

### What Needs LLM vs What Doesn't

**Needs LLM** (minimum NECESSARY complexity):
- Intent detection (understanding parent's meaning)
- Story analysis (extracting developmental signals)
- Pattern detection (cross-domain connections)
- Response generation (natural Hebrew)

**Simple Code Sufficient**:
- Curiosity activation math (`base + boost - decay`)
- Session transition detection (`hours >= 4`)
- Evidence effect on confidence (`+0.1 supports, -0.15 contradicts`)
- Formatting data for prompts

## 5. Architecture Overview

### Core Flow
```
Message arrives
    ↓
Phase 1: Extraction (with tools, temp=0)
    - LLM perceives and understands
    - Intent detected by comprehension, not keywords
    - Tool calls: notice, wonder, capture_story, add_evidence
    ↓
Apply Learnings (update Child state)
    ↓
Phase 2: Response (without tools, temp=0.7)
    - Turn guidance based on what was extracted
    - Natural Hebrew response
    ↓
Persist + Return curiosity_state
```

### Session Management
- **Session transition**: >4 hours gap triggers memory distillation
- **Memory distillation**: Summarizes previous session (standard model)
- **No background async**: Everything is synchronous, on-demand

### Synthesis (On Demand)
- Called when user requests or conditions are ripe
- Uses **strongest model** for pattern detection
- Creates essence narrative when understanding crystallizes

## 6. Key Files Map

| Category | File | Purpose |
| :--- | :--- | :--- |
| **Chitta Core** | `backend/app/chitta/gestalt.py` | Living Gestalt - the observing intelligence |
| **Chitta Core** | `backend/app/chitta/curiosity.py` | Curiosity model and engine |
| **Chitta Core** | `backend/app/chitta/service.py` | Service orchestration |
| **Chitta Core** | `backend/app/chitta/models.py` | Data models |
| **Chitta Core** | `backend/app/chitta/tools.py` | Tool definitions for LLM |
| **Chitta Core** | `backend/app/chitta/formatting.py` | Prompt formatting utilities |
| **Chitta Core** | `backend/app/chitta/reflection.py` | Synthesis and memory services |
| **Domain Config** | `backend/config/workflows/lifecycle_events.yaml` | Lifecycle events |
| **Domain Config** | `backend/config/workflows/context_cards.yaml` | Card logic definition |
| **Frontend** | `src/App.jsx` | Main state orchestrator |
| **Frontend** | `src/components/CuriosityPanel.jsx` | Curiosity display |
| **Docs** | `backend/docs/REFACTOR_PLAN.md` | Architecture plan |
| **Docs** | `backend/docs/architecture/LIVING_GESTALT.md` | Gestalt principles |

## 7. Quick Start & Environment

### Commands
```bash
# Full Startup
./start.sh

# Backend (Manual)
cd backend && source venv/bin/activate
python -m app.main

# Frontend (Manual)
npm run dev

# Testing
pytest backend/tests/test_curiosity.py      # Unit tests
pytest backend/tests/test_gestalt_integration.py  # Integration tests
```

## 8. Development Checklist

Before submitting code, verify:

1.  [ ] Did I preserve the **two-phase architecture**? (tools separate from response)
2.  [ ] Is intent detection done by **LLM understanding**, not keyword matching?
3.  [ ] Is `FunctionCallingConfigMode.ANY` active with `maximum_remote_calls=0`?
4.  [ ] Is the language warm Hebrew ("שמתי לב") not robotic ("המערכת זיהתה")?
5.  [ ] Am I using **curiosity** (4 types) not completeness?
6.  [ ] Is certainty **independent** of curiosity type?
7.  [ ] Is pattern detection using **strongest model**?
8.  [ ] Is there **no background async** processing?
9.  [ ] Does the feature embody **פשוט** - minimum NECESSARY complexity?

## 9. Anti-Patterns to Reject

*   **Keyword Intent Detection**: `if 'אתמול' in message` - LLM understands intent, not keywords
*   **Combined Tool+Text**: Trying to get tool calls and text in one LLM call
*   **Completeness Score**: We use curiosity activation, not completion percentage
*   **Background Reflection**: Pattern detection is part of synthesis, not async
*   **Simplistic vs פשוט**: Minimum NECESSARY, not minimum possible

---
**Version**: 3.0 (Living Gestalt Architecture)
**Last Updated**: December 2025
