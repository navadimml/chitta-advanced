# Gemini 2.5 Function Calling Reference

**Date**: 2025-11-16
**Purpose**: Reference documentation for proper Gemini 2.5 function calling implementation

## Key Principles

### The Natural Flow (Wu Wei)

Gemini 2.5 function calling follows a **multi-turn conversation loop**, NOT a single-turn operation:

1. **Turn 1**: Model analyzes prompt → Returns function calls ONLY (no text)
2. **Turn 2**: You execute functions → Send results back as user message
3. **Turn 3**: Model incorporates results → Returns final text response

**Do NOT expect text and function calls in the same turn!** While Gemini CAN sometimes return both, this is:
- Unpredictable and unreliable
- Not the recommended pattern
- Considered unexpected behavior

### Conversation Loop Pattern

```python
while iteration < max_iterations:
    # 1. Call Gemini with conversation history + function declarations
    response = client.models.generate_content(
        model=model,
        contents=conversation_history,
        config=types.GenerateContentConfig(
            tools=[types.Tool(function_declarations=FUNCTION_DECLARATIONS)],
            temperature=0.0
        )
    )

    # 2. Add model's response to history
    conversation_history.append(response.candidates[0].content)

    # 3. Check if response contains function calls
    has_function_calls = any(part.function_call for part in response.candidates[0].content.parts)

    if not has_function_calls:
        # Final text response - return it
        return response.candidates[0].content.parts[0].text

    # 4. Execute all function calls (parallel execution possible)
    function_response_parts = []
    for part in response.candidates[0].content.parts:
        if part.function_call:
            result = execute_function(part.function_call)
            function_response_parts.append(
                types.Part.from_function_response(
                    name=part.function_call.name,
                    response={"result": result}
                )
            )

    # 5. Add function results to conversation as user message
    conversation_history.append(
        types.Content(
            role="user",
            parts=function_response_parts
        )
    )

    # Loop continues - next iteration Gemini will see function results
```

## Response Structure

### When Function Calls Are Made

```python
response.candidates[0].content.parts = [
    Part(function_call=FunctionCall(name="get_weather", args={"location": "Boston"})),
    Part(function_call=FunctionCall(name="get_weather", args={"location": "Tokyo"}))
]

# Note: parts[0].text will be None or empty
```

### When Final Text Response Is Returned

```python
response.candidates[0].content.parts = [
    Part(text="The weather in Boston is 15°C and partly cloudy...")
]

# Note: No function_call parts present
```

## Parallel vs Sequential Function Calls

### Parallel Execution
Gemini can call multiple independent functions in ONE turn:

```python
# User: "Compare weather in Boston, Tokyo, and London"

# Gemini Turn 1: Returns 3 function calls simultaneously
[
    FunctionCall(name="get_weather", args={"location": "Boston"}),
    FunctionCall(name="get_weather", args={"location": "Tokyo"}),
    FunctionCall(name="get_weather", args={"location": "London"})
]

# You execute all 3, send results back

# Gemini Turn 2: Returns text response with comparison
```

### Sequential Execution
When functions depend on each other, Gemini calls them across multiple iterations:

```python
# User: "Check weather in Tokyo, if it's sunny book a hotel"

# Iteration 1:
# - Gemini calls get_weather("Tokyo")
# - You execute, send result: {"temp": 22, "condition": "Clear"}

# Iteration 2:
# - Gemini sees sunny weather, calls book_hotel("Tokyo", ...)
# - You execute, send confirmation

# Iteration 3:
# - Gemini returns final text: "Great! I've booked the hotel because..."
```

## Warning Signs of Fighting The Flow

If you see these, you're fighting Gemini's natural behavior:

1. **Trying to force text + function calls in same response** ❌
   - Adding prompts like "You must respond with text AND call functions"
   - This fights against Gemini's default flow

2. **Expecting conversation_history to contain final response immediately** ❌
   - After function calls, you need another iteration

3. **Not implementing the loop** ❌
   - Function calling requires iteration until final text response

## Best Practices

### 1. Temperature Setting
```python
temperature=0.0  # More deterministic for function calling
```

### 2. Error Handling
```python
try:
    result = FUNCTION_MAP[function_name](**function_args)
    return result
except Exception as e:
    return {"error": f"Error executing {function_name}: {str(e)}"}
```

### 3. Max Iterations
```python
max_iterations=5  # Prevent infinite loops
```

### 4. Function Response Format
```python
# Send function results back in this exact format
types.Part.from_function_response(
    name=function_call.name,
    response={"result": actual_result_dict}
)
```

## Example: Our Use Case (Chitta)

For conversation with data extraction, the flow should be:

```python
# Turn 1: Parent message
user: "הוא בן 4, שמו דניאל, והוא לא משחק עם ילדים"

# Iteration 1:
# - Gemini analyzes → calls extract_interview_data(child_name="דניאל", age=4, ...)
# - Backend executes extraction, saves to session
# - Backend sends function result back

# Iteration 2:
# - Gemini sees extraction succeeded
# - Gemini returns conversation response: "נעים להכיר את דניאל! ספרי לי..."

# Final response to user: "נעים להכיר את דניאל! ספרי לי..."
```

## Anti-Pattern: What We Were Doing Wrong

```python
# ❌ WRONG: Expecting both in same turn
response = llm.generate_content(prompt)
text = response.content  # Expecting text
function_calls = response.function_calls  # Expecting functions
# This fights Gemini's natural flow!

# ✅ RIGHT: Loop until text response
while True:
    response = llm.generate_content(conversation_history)
    if has_function_calls(response):
        results = execute_functions(response)
        conversation_history.append(function_results)
        continue  # Loop again
    else:
        return response.text  # Final answer
```

## References

- Google Gemini API Documentation: Function Calling
- Gemini 2.5 supports parallel function calling
- Function calls and text responses happen in SEPARATE turns
- This is by design, not a limitation

## Wu Wei Principle Applied

**Flow with Gemini's natural design:**
- Accept that function calling is multi-turn
- Embrace the iteration loop
- Don't force both responses in one turn
- Trust the natural conversation flow

**The water finds its way around the rock, it doesn't push through it.**
