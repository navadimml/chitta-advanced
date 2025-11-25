# Gemini Function Calling - Complete Implementation Guide

**Source**: [Google AI Gemini API Documentation](https://ai.google.dev/gemini-api/docs/function-calling)
**Date**: November 22, 2025

## Table of Contents
1. [Overview](#overview)
2. [How Function Calling Works](#how-function-calling-works)
3. [Defining Functions](#defining-functions)
4. [Enabling Function Calling](#enabling-function-calling)
5. [Response Structure](#response-structure)
6. [Handling Function Results](#handling-function-results)
7. [Function Calling Modes](#function-calling-modes)
8. [Advanced Features](#advanced-features)
9. [Best Practices](#best-practices)
10. [Common Pitfalls & Solutions](#common-pitfalls--solutions)

---

## Overview

Function calling allows Gemini models to:
1. **Augment Knowledge**: Connect to external data sources
2. **Extend Capabilities**: Access real-time information
3. **Take Actions**: Trigger external operations

**Key Concept**: The model doesn't execute functions - it **requests** them with structured parameters. Your code executes them and returns results.

---

## How Function Calling Works

```
User Message
    ↓
Model analyzes with function definitions
    ↓
Model decides: Call function OR respond naturally
    ↓
If function call:
    - Returns function name + arguments
    - NO text response (this is expected!)
    ↓
Your code executes the function
    ↓
Send results back to model
    ↓
Model generates natural language response using results
```

**CRITICAL**: When model calls a function, `response.text` will be **empty or minimal**. This is **correct behavior**, not an error!

---

## Defining Functions

Functions use **OpenAPI-compatible JSON Schema**:

```python
function_declaration = {
    "name": "extract_interview_data",  # Use snake_case or camelCase (no spaces!)
    "description": "Extract structured child development information from conversation",
    "parameters": {
        "type": "object",
        "properties": {
            "child_name": {
                "type": "string",
                "description": "Child's first name"
            },
            "age": {
                "type": "number",
                "description": "Child's age in years (can be decimal like 3.5)"
            },
            "primary_concerns": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of parent's main concerns"
            },
            "filming_preference": {
                "type": "string",
                "enum": ["wants_videos", "report_only"],
                "description": "Whether parent wants video analysis or report only"
            }
        },
        "required": ["child_name"]  # Only truly required fields
    }
}
```

**Best Practices for Definitions**:
- ✅ **Clear descriptions**: Include examples and context
- ✅ **Specific types**: Use `enum` when possible for validation
- ✅ **Optional parameters**: Only mark truly required fields
- ❌ **Avoid vague descriptions**: "Gets data" → "Gets current temperature in Celsius for a specific city"

---

## Enabling Function Calling

### Python (google-genai SDK)

```python
from google import genai
from google.genai import types

client = genai.Client(api_key="your_key")

# Define functions
tools = [types.Tool(function_declarations=[
    extract_interview_data,
    ask_developmental_question,
    request_action
])]

# Configure with functions
config = types.GenerateContentConfig(
    tools=tools,
    temperature=0.0,  # Low temp for reliable function calling
    max_output_tokens=2000
)

# Generate with functions enabled
response = await client.aio.models.generate_content(
    model="gemini-2.5-flash",
    contents=[
        types.Content(role="user", parts=[types.Part(text="My son Danny is 3 years old")])
    ],
    config=config
)
```

**CRITICAL for Chitta**: Disable Automatic Function Calling (AFC):

```python
config = types.GenerateContentConfig(
    tools=tools,
    tool_config=types.ToolConfig(
        function_calling_config=types.FunctionCallingConfig(
            mode=types.FunctionCallingConfigMode.ANY  # Manual control
        )
    )
)
```

**Why disable AFC?** We need to save function results to our database before sending them back to the model. AFC auto-executes and we lose control.

---

## Response Structure

### When Model Calls a Function

```python
response = await client.aio.models.generate_content(...)

# Check for function calls
if response.candidates[0].content.parts:
    for part in response.candidates[0].content.parts:
        # Check for function call
        if hasattr(part, 'function_call') and part.function_call:
            fc = part.function_call
            print(f"Function: {fc.name}")
            print(f"Arguments: {dict(fc.args)}")

        # Check for text (might be empty!)
        if hasattr(part, 'text') and part.text:
            print(f"Text: {part.text}")
```

**Example Output**:
```
Function: extract_interview_data
Arguments: {'child_name': 'Danny', 'age': 3.0}
Text: (empty string or None)
```

**IMPORTANT**:
- ✅ Empty text when function called = **EXPECTED**
- ✅ The model is doing its job correctly
- ❌ Don't treat this as an error!

### Response with Multiple Parts

A single response can have:
- Multiple function calls (parallel calling)
- Function call + text
- Just text (no function call)
- Just function calls (no text) ← **Most common with mode=ANY**

---

## Handling Function Results

### Step 1: Execute the Function

```python
# Extract function call from response
fc = response.candidates[0].content.parts[0].function_call

# Execute function
if fc.name == "extract_interview_data":
    # Save to database
    session_service.update_extracted_data(family_id, dict(fc.args))
    result = {"status": "saved", "fields": list(fc.args.keys())}
```

### Step 2: Build Conversation History

**CRITICAL**: You must add the assistant's function call to history BEFORE sending results!

```python
conversation_history = []

# 1. Original user message
conversation_history.append(types.Content(
    role="user",
    parts=[types.Part(text="My son Danny is 3")]
))

# 2. Assistant's function call (from response)
conversation_history.append(response.candidates[0].content)

# 3. Function results (as user role!)
conversation_history.append(types.Content(
    role="user",  # ← Results are sent as "user" role
    parts=[types.Part.from_function_response(
        name=fc.name,
        response={"result": result}
    )]
))
```

### Step 3: Get Final Response

```python
# Now ask model to generate user-facing response
final_response = await client.aio.models.generate_content(
    model="gemini-2.5-flash",
    contents=conversation_history,
    config=config  # Can include functions again or set to None
)

# This time we should get text!
print(final_response.text)  # "Great! Tell me about Danny..."
```

---

## Function Calling Modes

Control when/how model uses functions:

```python
tool_config = types.ToolConfig(
    function_calling_config=types.FunctionCallingConfig(
        mode=types.FunctionCallingConfigMode.AUTO,  # or ANY, NONE
        allowed_function_names=["extract_interview_data"]  # Optional filter
    )
)
```

### Mode Comparison

| Mode | Behavior | Use Case |
|------|----------|----------|
| **AUTO** (default) | Model chooses: function OR text | Conversational apps |
| **ANY** | Model MUST call a function | Structured extraction only |
| **NONE** | Model CANNOT call functions | Pure conversation |

**For Chitta**:
- Phase 1 (Extraction): Use `ANY` - force extraction
- Phase 2 (Response): Use `NONE` or no functions - get natural text

---

## Advanced Features

### Parallel Function Calling

Model can call multiple independent functions in one response:

```python
# User: "What's the weather in London and Paris?"
# Model response parts:
parts = [
    FunctionCall(name="get_weather", args={"city": "London"}),
    FunctionCall(name="get_weather", args={"city": "Paris"})
]
```

**Handling**:
```python
results = []
for part in response.candidates[0].content.parts:
    if hasattr(part, 'function_call'):
        result = execute_function(part.function_call.name, part.function_call.args)
        results.append(types.Part.from_function_response(
            name=part.function_call.name,
            response={"result": result}
        ))
```

### Automatic Function Calling (Python Only)

Pass Python functions directly:

```python
def get_temperature(location: str) -> dict:
    """Gets current temperature for a location."""
    return {"temp": 25, "unit": "C"}

# SDK auto-converts to declaration
config = types.GenerateContentConfig(tools=[get_temperature])

# SDK auto-executes when model requests it
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="What's the weather in London?",
    config=config
)
```

**Chitta doesn't use this** because we need database access between call and result.

---

## Best Practices

### 1. Clear Descriptions

❌ **Bad**:
```python
"description": "Gets data"
```

✅ **Good**:
```python
"description": "Extracts structured child development data from parent's message. Call this when parent shares: child's name, age, gender, concerns, strengths, or developmental details."
```

### 2. Use Enums for Validation

❌ **Bad**:
```python
"filming_preference": {
    "type": "string",
    "description": "Whether parent wants videos"
}
```

✅ **Good**:
```python
"filming_preference": {
    "type": "string",
    "enum": ["wants_videos", "report_only"],
    "description": "Parent's choice: 'wants_videos' if they agree to film, 'report_only' if they prefer report without videos"
}
```

### 3. Temperature Settings

- **Function calling**: Use 0.0-0.1 for reliability
- **Natural responses**: Use 0.7-1.0 for variety
- **Gemini 3 models**: Keep at 1.0 (Google recommendation)

### 4. Validate Before Executing

```python
if fc.name == "delete_all_data":
    # Critical action - confirm with user first!
    return {"confirmation_needed": True, "action": "delete_all_data"}
```

### 5. Token Management

- Function descriptions count toward input tokens
- Keep descriptions concise but clear
- Limit to 10-20 most relevant functions per call

---

## Common Pitfalls & Solutions

### Pitfall 1: Empty Response After Function Call

**Symptom**: Model returns function call but `response.text` is empty

**Cause**: This is **expected behavior**! Model returns structured call, not text.

**Solution**:
```python
# Don't expect text when function is called
if function_calls:
    # Execute functions, send results back
    # THEN get text response
else:
    # Only use response.text when NO functions called
    text = response.text
```

### Pitfall 2: Automatic Function Calling (AFC) Enabled

**Symptom**: No function calls received, or SDK executes them automatically

**Cause**: SDK enables AFC by default (as of 2024)

**Solution**:
```python
tool_config = types.ToolConfig(
    function_calling_config=types.FunctionCallingConfig(
        mode=types.FunctionCallingConfigMode.ANY  # Disables AFC
    )
)
```

### Pitfall 3: Model Writes About Functions Instead of Calling

**Symptom**: Model responds with text like "I'll call extract_interview_data with..." or XML tags like `<start_action>view_guidelines</start_action>`

**Cause**:
1. Functions not properly enabled in config
2. Model doesn't understand when to call functions
3. Function descriptions are unclear

**Solution**:
```python
# 1. Verify functions are in config
config = types.GenerateContentConfig(tools=tools)  # ✅

# 2. Use clearer function descriptions
"description": "CALL THIS FUNCTION when parent shares child information"

# 3. Use mode=ANY to force function calling in Phase 1
```

**Cleanup**: Remove text-based function syntax:
```python
# In clean_response()
text = re.sub(r'<start_action>.*?</start_action>', '', text, flags=re.DOTALL)
```

### Pitfall 4: Missing Function Call History

**Symptom**: Model doesn't have context about previous function calls

**Cause**: Forgot to add assistant's function call to conversation history

**Solution**:
```python
# MUST include assistant's response in history
conversation.append(response.candidates[0].content)  # ← Critical!
conversation.append(function_results)
```

### Pitfall 5: thought_signature Contamination

**Symptom**: Internal reasoning or thinking tags appear in responses

**Cause**: Modern Gemini models include `part.thought` attribute with internal reasoning

**Solution**:
```python
# Extract ONLY text, ignore thought attribute
for part in candidate.content.parts:
    if hasattr(part, 'text') and part.text:
        content += part.text  # ✅ Get text
        # Ignore part.thought if it exists
```

**Don't use**: `response.text` - it concatenates ALL attributes including `thought`

---

## Chitta-Specific Implementation

### Two-Phase Architecture

**Phase 1: Extraction (with functions)**
```python
# Enable functions, mode=ANY (force function calling)
extraction_config = types.GenerateContentConfig(
    tools=extraction_tools,
    tool_config=types.ToolConfig(
        function_calling_config=types.FunctionCallingConfig(
            mode=types.FunctionCallingConfigMode.ANY
        )
    ),
    temperature=0.0
)

response1 = await llm.chat(messages, config=extraction_config)
# Expect: function_calls, minimal/no text
```

**Phase 2: Response (without functions)**
```python
# No functions = forces natural text response
response_config = types.GenerateContentConfig(
    tools=None,  # ← No functions!
    temperature=0.7
)

response2 = await llm.chat(updated_messages, config=response_config)
# Expect: natural Hebrew text, NO function calls
```

### Why Two Phases?

1. **Separation of concerns**: Extraction vs conversation
2. **Reliable extraction**: Phase 1 forces function calling
3. **Natural responses**: Phase 2 can't call functions, must generate text
4. **Database control**: Save extractions between phases

---

## Debugging Function Calling

### Check if Functions are Being Offered

```python
logger.info(f"Tools: {config.tools}")
logger.info(f"Tool config: {config.tool_config}")
```

### Log Function Calls

```python
for part in response.candidates[0].content.parts:
    if hasattr(part, 'function_call'):
        logger.info(f"✅ Function called: {part.function_call.name}")
        logger.info(f"   Args: {dict(part.function_call.args)}")
    elif hasattr(part, 'text'):
        logger.info(f"📝 Text: {part.text[:100]}")
```

### Check Finish Reason

```python
finish_reason = response.candidates[0].finish_reason
if finish_reason != "STOP":
    logger.warning(f"Unusual finish reason: {finish_reason}")
    # Could be: MAX_TOKENS, SAFETY, RECITATION, etc.
```

---

## Summary

**Function calling is NOT a bug, it's a feature!**

✅ **Expected**:
- Empty text when function called
- Structured arguments in function_call
- Need to send results back for final response

❌ **NOT Expected**:
- Model writing about functions in text
- AFC auto-executing functions
- thought_signature leaking to users
- `<start_action>` tags in text

**Golden Rule**: If you see function-related text or XML tags in the response, **functions are not properly configured** and the model is improvising.
