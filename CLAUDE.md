# CLAUDE.md

This file provides the Constitution and Technical Guidance for Claude Code when working on **Chitta**.

## 1. Core Philosophy: The "Why"

**Chitta exists to help parents and clinicians see child development clearly.**

Chitta is an **expert developmental psychologist** (0.5-18 years) - not just a conversationalist.
We are a "Conversation-First" platform with a "Wu Wei" architecture.

*   **Identity**: An expert guide with deep developmental psychology knowledge. We point; we do not replace.
*   **Voice**: "שמתי לב ש..." not "המערכת זיהתה..." (Simple words, deep understanding).
*   **Goal**: Create space for understanding through **curiosity**, not checklists.

### Darshan (The Observing Intelligence)

**Darshan** (Sanskrit: दर्शन) means "mutual seeing" - to see and be seen.

Darshan is the **observing intelligence** - it HOLDS, NOTICES, and ACTS.
- Child and Session are its memory
- Darshan is the mind
- Understanding emerges through conversation, not assessment

See `backend/docs/METAPHOR_ARCHITECTURE.md` for the complete naming philosophy.

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
Phase 1: Perception (with tools)
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
# Phase 1: Perception
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

### Gemini Structured Output (JSON Schema)

When you need guaranteed JSON structure from LLM responses (e.g., portraits, reports), use **structured output** instead of asking the LLM to produce JSON.

**How Gemini Structured Output Works:**
1. Define schema using **Pydantic** models
2. Call `chat_with_structured_output()` with the schema
3. Gemini returns **syntactically valid JSON** matching your schema
4. Validate and convert to your dataclass/model

**Key Configuration (from Gemini docs):**
```python
config = types.GenerateContentConfig(
    response_mime_type="application/json",   # REQUIRED: Request JSON output
    response_schema=YourSchema.model_json_schema(),  # Your Pydantic schema
    # ... other config
)
```

**Our Abstraction - Use the LLM Provider:**
```python
from app.services.llm.factory import create_llm_provider
from app.services.llm.base import Message as LLMMessage
from your_module import YourPydanticSchema

llm = create_llm_provider(provider_type="gemini", model="gemini-2.5-pro")

# Get structured output
response_data = await llm.chat_with_structured_output(
    messages=[
        LLMMessage(role="system", content="Your prompt here"),
        LLMMessage(role="user", content="Generate the output"),
    ],
    response_schema=YourPydanticSchema.model_json_schema(),
    temperature=0.7,
)

# response_data is already a dict - validate with Pydantic
result = YourPydanticSchema.model_validate(response_data)
```

**Schema Best Practices:**
- Use `Field(description="...")` to guide the LLM on each field
- Use `enum` for constrained choices
- Keep schemas relatively flat (1-2 levels) for reliability
- Schema descriptions are part of the prompt - be explicit about what you want

**Example Schema (Portrait):**
```python
from pydantic import BaseModel, Field
from typing import List

class PatternSchema(BaseModel):
    description: str = Field(description="Pattern in situational language")
    domains: List[str] = Field(description="Domains involved: behavioral, emotional, sensory")

class PortraitOutput(BaseModel):
    narrative: str = Field(description="2-3 sentences about who this child IS")
    patterns: List[PatternSchema] = Field(default_factory=list)
```

**IMPORTANT Limitations:**
- Structured output guarantees **syntactically correct JSON**, NOT semantically correct values
- Always validate the output in your application code
- Use `max_output_tokens=8000+` to prevent truncation on complex schemas

**Where We Use Structured Output:**
- `synthesis.py` → Portrait generation via `chat_with_structured_output()`
- Schema defined in `portrait_schema.py`

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
- Curiosity pull math (`base + boost - decay`)
- Session transition detection (`hours >= 4`)
- Evidence effect on confidence (`+0.1 supports, -0.15 contradicts`)
- Formatting data for prompts

## 5. Architecture Overview

### Core Flow
```
Message arrives
    ↓
Phase 1: Perception (with tools, temp=0)
    - Darshan perceives and understands
    - Intent detected by comprehension, not keywords
    - Tool calls: notice, wonder, capture_story, add_evidence
    ↓
Apply Learnings (update Child state)
    ↓
Phase 2: Response (without tools, temp=0.7)
    - Turn guidance based on what was perceived
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
| **Chitta Core** | `backend/app/chitta/gestalt.py` | Darshan - the observing intelligence |
| **Chitta Core** | `backend/app/chitta/curiosity.py` | Curiosity model and Curiosities manager |
| **Chitta Core** | `backend/app/chitta/service.py` | Thin orchestrator, public API |
| **Chitta Core** | `backend/app/chitta/models.py` | Data models |
| **Chitta Core** | `backend/app/chitta/tools.py` | Tool definitions for LLM |
| **Chitta Core** | `backend/app/chitta/formatting.py` | Prompt formatting utilities |
| **Chitta Core** | `backend/app/chitta/synthesis.py` | Portrait/crystal generation |
| **Chitta Core** | `backend/app/chitta/portrait_schema.py` | Pydantic schema for structured output |
| **Specialized Services** | `backend/app/chitta/gestalt_manager.py` | Darshan lifecycle & persistence |
| **Specialized Services** | `backend/app/chitta/video_service.py` | Video consent → guidelines → upload → analysis |
| **Specialized Services** | `backend/app/chitta/child_space.py` | Living Portrait derivation (read-only) |
| **Specialized Services** | `backend/app/chitta/sharing.py` | Shareable summary generation |
| **Specialized Services** | `backend/app/chitta/cards.py` | Context card derivation |
| **Specialized Services** | `backend/app/chitta/journal_service.py` | Parent journal processing |
| **LLM Layer** | `backend/app/services/llm/base.py` | LLM provider interface |
| **LLM Layer** | `backend/app/services/llm/gemini_provider.py` | Gemini implementation |
| **LLM Layer** | `backend/app/services/llm/factory.py` | Provider factory |
| **Domain Config** | `backend/config/workflows/lifecycle_events.yaml` | Lifecycle events |
| **Domain Config** | `backend/config/workflows/context_cards.yaml` | Card logic definition |
| **Frontend** | `src/App.jsx` | Main state orchestrator |
| **Frontend** | `src/components/CuriosityPanel.jsx` | Curiosity display |
| **Docs** | `backend/docs/METAPHOR_ARCHITECTURE.md` | Darshan naming philosophy |

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
*   **String Matching for Content Detection**: `if 'לידה' in observation.content` - NEVER use string/keyword matching to determine if we have data about something. The LLM extracts observations WITH domains via tools. Check domains, not content strings. If you need semantic understanding of content, use an LLM.
*   **Combined Tool+Text**: Trying to get tool calls and text in one LLM call
*   **Completeness Score**: We use curiosity pull, not completion percentage
*   **Background Reflection**: Pattern detection is part of synthesis, not async
*   **Simplistic vs פשוט**: Minimum NECESSARY, not minimum possible

### The Right Way to Check for Data

```python
# ❌ WRONG - String matching
if any('לידה' in obs.content for obs in observations):
    has_birth_history = True

# ✅ RIGHT - Domain-based (LLM already classified during perception)
has_birth_history = any(obs.domain == 'birth_history' for obs in observations)

# ✅ RIGHT - If you need semantic understanding, use LLM
# But usually domain-based is sufficient because LLM already extracted with domain
```

---
**Version**: 3.0 (Darshan Architecture)
**Last Updated**: December 2025
