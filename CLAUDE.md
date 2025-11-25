
# CLAUDE.md

This file provides the Constitution and Technical Guidance for Claude Code when working on **Chitta**.

## 1. Core Philosophy: The "Why"

**Chitta exists to help parents and clinicians see child development clearly.**
We are a "Conversation-First" platform with a "Wu Wei" (dependency-based) architecture.

*   **Identity**: A helpful guide, not an autonomous expert. We point; we do not replace.
*   **Voice**: "We noticed..." not "System detected..." (Simple words, deep understanding).
*   **Goal**: Create space for understanding. Do not fill silence with unnecessary prompts.

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
    *   Example: `generate_report(data, audience="clinician")` vs `generate_report(data, audience="parent")`.

4.  **Show, Don't Conclude (Data Model)**:
    *   ❌ `diagnosis: "delayed"` (Interpretive labels are forbidden in raw data).
    *   ✅ `observation: { event: "looked at face", timestamp: "0:03" }` (Descriptive data).

5.  **Be Invisible (UX)**:
    *   Proactive $\neq$ Pushy. Only trigger logic when `value > interruption_cost`.
    *   Prerequisites determine what is *available/recommended*, never what is *blocked*.

6.  **Simplicity (Wu Wei)**:
    *   Beauty is the minimum necessary complexity.
    *   Prefer configuration (YAML) over code (Python) whenever possible.

7.  **Honest Uncertainty**:
    *   If confidence is low, return structured data indicating ambiguity (`readiness: "need_more_info"`).
    *   Never hallucinate certainty or generic errors.

8.  **Emergence**:
    *   Prefer small, composable functions over monolithic "Intelligent Managers." Intelligence emerges from the interaction of simple parts.

9.  **Naming Convention**:
    *   Use `organize`, `highlight`, `suggest`.
    *   Avoid `diagnose`, `assess`, `decide`.

10. **Natural Language**:
    *   Hebrew output must be natural, warm, and non-robotic.
    *   Preserve `dir="rtl"` in all UI components.

## 3. The Wu Wei Development Protocol

**CRITICAL: Before writing Python code, consult this decision tree.**

We distinguish between the **Domain Layer** (Configuration) and the **Framework Layer** (Code).

### The Decision Tree
1.  **Is this a domain feature?** (e.g., "Filming decision", "New therapy type")
    *   **STOP.** Do not write Python logic.
    *   **Action:**
        1.  Add field to `ExtractedData` schema (`backend/app/core/models.py`).
        2.  Configure "Moment" in `lifecycle_events.yaml`.
        3.  Configure "Card" in `context_cards.yaml`.
2.  **Is this a general mechanism?** (e.g., "Status-based card content")
    *   **Proceed.** Modify Framework code (`backend/app/services/`).
    *   **Rule:** Only if 3+ domain features will use it.

### Anti-Patterns to Reject
*   **The Premature Enum**: Creating `class ActionType(Enum)` for a specific domain choice. (Use strings in YAML instead).
*   **The Hardcoded Response**: Writing Hebrew text inside Python functions. (Put it in YAML).
*   **The Special Case**: `if artifact == "video": do_x()`. (Make artifact behavior configurable).

## 4. Technical Constraints & Critical Implementation

### LLM Configuration (Gemini)
*   **Provider**: Gemini 2.5 Pro (Primary) or 2.0 Flash Exp.
*   **CRITICAL: Disable Automatic Function Calling (AFC)**.
    *   Gemini SDK defaults break our flow. You MUST use:
    ```python
    tool_config=types.ToolConfig(
        function_calling_config=types.FunctionCallingConfig(
            mode=types.FunctionCallingConfigMode.ANY  # Disables AFC
        )
    )
    ```
*   **Token Limits**: `max_output_tokens` must be **4000+** to prevent Hebrew truncation.

### Architecture Mode
*   **Default**: `simplified` (1-2 LLM calls per message).
*   **Logic File**: `backend/app/services/conversation_service_simplified.py` (Do not edit the legacy full service).
*   **Core Flow**:
    1.  Main LLM call (Intent + Extraction).
    2.  Local function processing (No extra LLM calls).
    3.  Semantic verification (every 3 turns).

## 5. Quick Start & Environment

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
python test_conversation_service.py       # Simplified flow
python test_gemini_interview_enhanced.py  # Gemini integration
```

### Key Files Map
| Category | File | Purpose |
| :--- | :--- | :--- |
| **Domain Config** | `backend/config/workflows/lifecycle_events.yaml` | **Start here for new features.** |
| **Domain Config** | `backend/config/workflows/context_cards.yaml` | Card logic definition. |
| **Data Model** | `backend/app/core/models.py` | `ExtractedData` schema. |
| **Logic** | `backend/app/services/conversation_service_simplified.py` | Primary business logic. |
| **Logic** | `backend/app/services/prerequisite_service.py` | Dependency checker. |
| **LLM** | `backend/app/services/llm/gemini_provider_enhanced.py` | Gemini config (AFC disabled). |
| **Prompts** | `backend/app/prompts/comprehensive_prompt_builder.py` | System prompt construction. |
| **Frontend** | `src/App.jsx` | Main state orchestrator. |

## 6. Development Checklist

Before submitting code, verify:
1.  [ ] Did I avoid adding a new Enum?
2.  [ ] Did I use `lifecycle_events.yaml` instead of `if/else` logic?
3.  [ ] Is `FunctionCallingConfigMode.ANY` active?
4.  [ ] Is the language simple ("We noticed") and not diagnostic ("Delayed")?
5.  [ ] Does the feature "adapt like water" (polymorphic) or is it rigid?

---
**Version**: 2.0 (Wu Wei & Principles Integrated)
**Last Updated**: November 2025