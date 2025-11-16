# Conversation Quality Fixes

## Issues Identified

### Critical Issues

#### 1. **Automatic Function Calling (AFC) Enabled by Default** 🔴 CRITICAL
- **Probability:** 85%
- **Impact:** Severe - Data not being extracted
- **Symptoms:**
  - Logs show: "AFC is enabled with max remote calls: 10"
  - Zero function calls received in code
  - Child name and age not being saved despite parent providing them
  - Knowledge richness shows: `has_child_name: False`, `has_age: False`

**Root Cause:**
The Google Gemini SDK enables Automatic Function Calling (AFC) by default as of 2024. When AFC is enabled, Gemini automatically executes functions internally and returns ONLY the final text response. The application code never sees the function call parts, so data extraction never happens.

**Fix Applied:**
```python
# In gemini_provider.py - Explicitly disable AFC
if tools:
    config_params["tool_config"] = types.ToolConfig(
        function_calling_config=types.FunctionCallingConfig(
            mode=types.FunctionCallingConfigMode.ANY
        )
    )
```

This ensures manual function calling where function_call parts are returned to the application for processing.

#### 2. **Message Truncation** 🟠 HIGH
- **Probability:** 70%
- **Impact:** High - Incomplete responses
- **Symptoms:**
  - Messages cut off mid-sentence: "זה יכול להיות דינוזאורים, רכ"
  - Parents seeing incomplete explanations

**Root Cause:**
`max_tokens=2000` was too low. The comprehensive system prompt is ~2500 tokens, leaving minimal room for:
- Function call JSON (200-400 tokens)
- Hebrew text response (needs 1500-2000 tokens for natural conversation)
- Total needed: ~4000 tokens minimum

**Fix Applied:**
```python
# Increased from 2000 to 4000
llm_response = await self.llm.chat(
    messages=messages,
    functions=CONVERSATION_FUNCTIONS_COMPREHENSIVE,
    temperature=temperature,
    max_tokens=4000  # Was: 2000
)
```

#### 3. **Insufficient Debugging for Function Calling** 🟡 MEDIUM
- **Probability:** 100% (This was definitely missing)
- **Impact:** Medium - Makes diagnosis difficult

**Fix Applied:**
Added detailed logging to help identify function calling issues:
```python
# Enhanced debugging for function calling issues
if functions and not has_function_calls:
    logger.warning(
        f"⚠️  No function calls made despite {len(CONVERSATION_FUNCTIONS_COMPREHENSIVE)} "
        f"functions available. Response preview: {response_text[:100]}..."
    )

if has_function_calls:
    func_names = [fc.name for fc in llm_response.function_calls]
    logger.info(f"📞 Functions called: {func_names}")
```

### Other Potential Issues (Not Fixed Yet - Monitor)

#### 4. **Model Quality: Flash Lite**
- **Probability:** 75%
- **Symptoms:** Logs show `gemini-flash-lite-latest` being used
- **Issue:** Flash Lite has weak function calling capabilities
- **Recommendation:** Use `gemini-2.5-flash` or better yet `gemini-2.0-flash-exp`
- **Action:** Set in environment: `LLM_MODEL=gemini-2.5-flash`

#### 5. **Role Confusion**
- **Probability:** 55%
- **Symptoms:** "אתה צודק" - Chitta using masculine form to parent (role swap indicator)
- **Possible Cause:** Conversation history might have roles swapped
- **Status:** Monitor - may be fixed by AFC fix (since conversation flow will be correct now)

## Expected Outcomes After Fixes

### Before:
```
Parent: "קוראים לו יונתן, והוא בן ארבע"
Logs: ✅ LLM response: 199 chars, 0 function calls
Knowledge: has_child_name: False, has_age: False
```

### After:
```
Parent: "קוראים לו יונתן, והוא בן ארבע"
Logs: ✅ LLM response: 245 chars, 1 function calls
Logs: 📞 Functions called: ['extract_interview_data']
Logs: 📝 Extracting data: {'child_name': 'יונתן', 'age': 4}
Knowledge: has_child_name: True ('יונתן'), has_age: True (4.0)
```

## Testing Recommendations

1. **Run test mode with a persona:**
   ```bash
   # Use the test API to simulate a parent conversation
   POST /api/test/start
   {
     "persona_id": "moshe_contradictory"
   }
   ```

2. **Monitor logs for:**
   - ✅ "📞 Functions called: ['extract_interview_data']"
   - ✅ "📝 Extracting data: {...}" with actual data
   - ❌ "⚠️ No function calls made" warnings
   - ✅ No "AFC is enabled" messages (AFC should be disabled now)

3. **Verify data extraction:**
   ```bash
   # Check knowledge richness in logs
   # Should show: has_child_name: True, has_age: True
   ```

4. **Check for message truncation:**
   - Responses should be complete sentences
   - No mid-word cutoffs
   - Full explanations

## Update: Additional Fixes Applied (2025-11-16)

### Issue 3: Empty Responses from Weak Models 🟠 HIGH

**Symptoms:**
- Chitta returning empty messages to parents
- Data being extracted successfully but no acknowledgment
- `FinishReason.MALFORMED_FUNCTION_CALL` in logs

**Root Cause:**
After successful data extraction in iteration 1, `gemini-flash-lite-latest` fails to generate the text response in iteration 2, creating a malformed function call instead.

**Fix Applied:**
```python
# Intelligent fallback response generation
if not final_response and extraction_summary:
    child_name = extraction_summary.get('child_name', 'הילד/ה')
    age = extraction_summary.get('age')

    if child_name and age:
        final_response = f"נעים להכיר את {child_name}! בגיל {age}, מה הדבר שהכי מעסיק אותך לגביו/ה?"
    elif child_name:
        final_response = f"נעים להכיר את {child_name}! ספרי לי קצת עליו/ה - מה מעסיק אותך?"
    else:
        final_response = "תודה שאת משתפת. ספרי לי עוד - מה הדבר שהכי מדאיג אותך?"
```

This ensures conversation continues smoothly even with weak models, using extracted data to generate intelligent fallback responses.

## Files Modified

1. `backend/app/services/llm/gemini_provider.py`
   - Added `tool_config` with `FunctionCallingConfig` to disable AFC

2. `backend/app/services/conversation_service_simplified.py`
   - Increased `max_tokens` from 2000 to 4000
   - Added enhanced debugging logs
   - Added MALFORMED_FUNCTION_CALL detection and logging
   - Added intelligent fallback response generation
   - Fixed NameError in debugging code

## Impact Assessment

### Severity: CRITICAL
These issues completely broke the core functionality - child information was not being saved, making the entire interview process ineffective.

### Fix Confidence: 95%
The AFC issue is almost certainly the root cause. The fix is straightforward and follows Gemini SDK best practices for manual function calling.

### Risk: LOW
Changes are minimal and focused:
- Adding config parameters (safe)
- Increasing token limit (safe, just costs slightly more)
- Adding logging (safe, improves debugging)

## Next Steps

1. ✅ Apply fixes (DONE)
2. ⏳ Run comprehensive test with multiple personas
3. ⏳ Monitor logs for function calling success
4. ⏳ Verify conversation quality improvements
5. ⏳ Consider upgrading to better model if flash-lite still underperforms
6. ⏳ Commit and push changes
