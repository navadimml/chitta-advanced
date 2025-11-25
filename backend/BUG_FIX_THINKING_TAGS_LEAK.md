# Critical Bug Fix: Thinking Tags Leaking to User Chat

**Date**: November 22, 2025
**Severity**: CRITICAL - Cannot publish app with this bug
**Status**: ✅ FIXED

## Problem Description

Users were seeing `<thinking>` tags in the chat with Chitta's internal reasoning exposed:

```
<thinking> The parent has consented to filming ("כן רוצה לצלם").
This confirms the transition to the next stage (Video Filming Guidelines).
I have reached the "knowledge richness threshold"...
Action: Generate the personalized video filming guidelines...
</thinking>
```

Additionally, Chitta was giving instructions in chat instead of responding naturally.

## Root Cause Analysis

### Gemini 3 Pro Preview `thought_signature` Feature

The `STRONG_LLM_MODEL=gemini-3-pro-preview` (used for artifact generation and video analysis) includes an experimental feature called `thought_signature` that contains the model's internal reasoning process.

### The Bug: `response.text` Concatenates ALL Parts

When using `response.text` directly on a Gemini response object, the google-genai SDK concatenates ALL text parts, INCLUDING the `thought_signature` part.

### Warning Message (Previously Ignored)

```
Warning: there are non-text parts in the response: ['thought_signature'],
returning concatenated text result from text parts.
```

This warning was telling us exactly what was happening!

### Locations Where Bug Occurred

1. **`backend/app/services/llm/gemini_provider.py:416`**
   - Fallback code used `response.text` when normal parsing found no content
   - This leaked thinking tags when Gemini returned ONLY thought_signature without text response

2. **`backend/app/services/video_analysis_service.py:254`**
   - Direct use of `response.text` for video analysis JSON parsing
   - Would contaminate structured JSON output with thinking tags

## The Fix

### Fix 1: Removed Bad Fallback in gemini_provider.py

**Before** (Lines 414-420):
```python
# Fallback to simple text if available
if not content and not function_calls:
    if hasattr(response, 'text'):
        content = response.text  # ❌ INCLUDES thought_signature!
    else:
        logger.warning("No content found in response")
        content = str(response) if response else "No response"
```

**After** (Lines 413-424):
```python
# ⚠️ CRITICAL: Do NOT use response.text as fallback!
# response.text concatenates ALL parts including thought_signature from Gemini 3 Pro,
# which leaks internal reasoning (<thinking> tags) to users.
# If there's no text content after parsing parts, it means Gemini returned
# ONLY non-text parts (thought_signature, function_calls, etc.) with no actual text response.
# In this case, returning empty string is correct behavior.
if not content and not function_calls:
    logger.warning(
        f"⚠️ Gemini response has no text content! "
        f"Only non-text parts returned (thought_signature, etc.). "
        f"This indicates the model didn't generate a user-facing response."
    )
```

### Fix 2: Correct thought_signature Handling (UPDATED)

**IMPORTANT DISCOVERY**: thought_signature is NOT a separate part - it's an ATTRIBUTE of the same Part that contains the text!

A single Part can have BOTH:
- `part.text` - User-facing response (what we want)
- `part.thought` - Internal reasoning (what we don't want)

**Original Fix (WRONG)**: Skipped entire part if it had `thought` attribute, which also threw away the text!

**Corrected Fix in gemini_provider.py** (Lines 383-398):
```python
for part in candidate.content.parts:
    # ⚠️ CRITICAL FIX: thought_signature is an ATTRIBUTE of the Part, not a separate part!
    # The same Part can have BOTH part.text (user-facing) and part.thought (internal reasoning).
    # We want the TEXT but not the thought.
    # DO NOT skip the entire part - just extract the text and ignore the thought attribute!

    # Text content (user-facing response)
    if hasattr(part, 'text') and part.text:
        content += part.text
        # Log if this part also has thought_signature (for debugging)
        if hasattr(part, 'thought'):
            logger.debug("🧠 Part has thought_signature (ignored, text extracted)")

    # If part has ONLY thought with NO text, skip it
    elif hasattr(part, 'thought'):
        logger.debug("🧠 Skipping part with ONLY thought_signature (no text)")
        continue
```

**Key Insight**: Extract `part.text` regardless of whether `part.thought` exists. The `response.text` concatenates BOTH, but we only want the text attribute.

### Fix 3: Proper Part Extraction in video_analysis_service.py (UPDATED)

**Before** (Line 254):
```python
content = response.text  # ❌ INCLUDES thought_signature!
```

**Corrected Fix** (Lines 253-280):
```python
# ⚠️ CRITICAL: Extract text from parts, NOT response.text!
# response.text concatenates ALL parts including thought_signature from Gemini 3 Pro,
# which would contaminate our structured JSON output
content = ""
if hasattr(response, 'candidates') and response.candidates:
    candidate = response.candidates[0]
    if hasattr(candidate, 'content') and candidate.content:
        if hasattr(candidate.content, 'parts') and candidate.content.parts:
            for part in candidate.content.parts:
                # ⚠️ CRITICAL FIX: thought_signature is an ATTRIBUTE of the Part, not a separate part!
                # Extract text regardless of whether thought attribute exists

                # Extract text content (the JSON we need)
                if hasattr(part, 'text') and part.text:
                    content += part.text
                    # Log if this part also has thought_signature (for debugging)
                    if hasattr(part, 'thought'):
                        logger.debug("🧠 Part has thought_signature (ignored, text extracted)")

                # If part has ONLY thought with NO text, skip it
                elif hasattr(part, 'thought'):
                    logger.debug("🧠 Skipping part with ONLY thought_signature (no text)")
                    continue

if not content:
    logger.error("❌ No text content in Gemini response!")
    raise ValueError("Gemini returned empty response for video analysis")
```

## Why This Happened

1. **Experimental Feature**: Gemini 3 Pro Preview's `thought_signature` is a relatively new feature
2. **SDK Behavior**: The google-genai SDK's `response.text` shortcut concatenates ALL attributes (both `part.text` and `part.thought`) by design
3. **Insufficient Documentation**: The SDK warning wasn't clear about the implications
4. **Code Pattern**: Using `response.text` is the "easy" way but wrong when thought_signature exists
5. **Misunderstanding Structure**: Initially thought `thought_signature` was a separate Part, but it's actually an attribute of the SAME Part that contains the text

## Critical Discovery (Nov 22, 2025)

**Original Fix Issue**: The initial fix skipped the ENTIRE part when it detected a `thought` attribute, which also threw away the user-facing text!

**Root Cause**: A single `Part` object can have BOTH attributes simultaneously:
- `part.text` - User-facing response (what we want)
- `part.thought` - Internal reasoning (what we don't want)

**Test Results**: Created `test_gemini_empty_response.py` which proved that simple queries return Parts with BOTH text and thought attributes. The fix must extract the text while ignoring the thought attribute, NOT skip the entire part.

This explains why after the initial fix, responses were empty - we were throwing away good text along with the thought_signature!

## What We Learned

1. **NEVER use `response.text` directly** with Gemini 3 Pro or newer models - it concatenates ALL attributes including thought_signature
2. **ALWAYS parse `response.candidates[0].content.parts`** explicitly to extract only `part.text`
3. **EXTRACT part.text, don't skip parts** - thought_signature is an attribute of the Part, not a separate part type
4. **Test assumptions with simple cases** - the test with "שלום" revealed the true structure immediately
5. **Pay attention to SDK warnings** - they're telling us something important!

## Testing

After fix, verify:
- [ ] No `<thinking>` tags appear in chat
- [ ] No internal instructions appear in chat responses
- [ ] Normal conversation flow works correctly
- [ ] Video analysis structured output works correctly
- [ ] Guidelines generation works correctly

## Prevention

Added explicit comments in code with ⚠️ CRITICAL warnings to prevent regression.

## Related Files

- `backend/app/services/llm/gemini_provider.py` - Main LLM provider
- `backend/app/services/video_analysis_service.py` - Video analysis service
- `backend/.env` - LLM model configuration (gemini-3-pro-preview)

---

**Lesson**: When the SDK gives you a warning, INVESTIGATE IT IMMEDIATELY!
