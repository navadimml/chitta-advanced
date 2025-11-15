# Extraction & Intent Detection Robustness Analysis

## 🔍 Root Causes Discovered

### Issue 1: Extracted Data Not Prominent in System Prompt

**Location**: `backend/app/prompts/dynamic_interview_prompt.py:82-84`

```python
## CURRENT STATE

Child: {child_name} | Age: {age} | Gender: {gender}
Concerns mentioned: {concerns_str}
```

**Problems**:
1. ❌ Buried in massive 177-line system prompt
2. ❌ Shows "unknown" without emphasis if not extracted
3. ❌ No explicit instruction to USE these facts
4. ❌ Easily overlooked by LLM among hundreds of other instructions

**Result**: LLM generates responses ignoring extracted data because it's not prominent.

---

### Issue 2: Extraction Function Has No Required Fields

**Location**: `backend/app/prompts/interview_functions.py:100`

```python
"required": []  # Nothing is required - extract whatever is available
```

**Problems**:
1. ❌ LLM can return completely empty extraction
2. ❌ No validation that critical fields (name, age) were actually extracted
3. ❌ No error handling when extraction fails
4. ❌ No retry mechanism for failed extractions

**Result**: Silent extraction failures - data simply not captured.

---

### Issue 3: Extraction Timing Issue

**Location**: `backend/app/services/conversation_service.py:604-694`

**Flow**:
```
1. Build system prompt with OLD extracted data
2. Generate conversational response
3. THEN extract data from conversation
4. Save for NEXT turn
```

**Problems**:
1. ❌ When parent says "מיכל, בת 4.5", response in THAT turn won't use the name
2. ❌ Only NEXT response will have the data
3. ❌ Creates 1-turn lag in using extracted information

**Example Bug**:
```
Parent: "שמה מיכל והיא בת 4.5"
Chitta: "תודה! ספרי לי עוד על הילדה שלך" ← doesn't use name!
Parent: [next message]
Chitta: "איך מיכל עם..." ← NOW uses name (too late)
```

---

### Issue 4: Weak Intent Detection

**Current**: Multiple systems checking for intents:
- Sage/Hand architecture (complex, not rock solid)
- Intent detection service (LLM-based, can hallucinate)
- Prerequisite checking (after intent detected)
- Strategic guidance (separate LLM call)

**Problems**:
1. ❌ Too many moving parts - failure in any breaks the chain
2. ❌ LLM-based intent detection unreliable
3. ❌ No validation of detected intents
4. ❌ Conflicting signals from different services

---

## 🎯 Wu Wei Solution: Make It Rock Solid

### Principle: Simplicity + Validation = Robustness

The Dao says: "The rigid tree breaks in the storm. The flexible reed bends and survives."

Don't fight complexity with more complexity. **Simplify and validate.**

---

## 🛠️ Fixes Required

### Fix 1: Make Extracted Facts PROMINENT and MANDATORY

**File**: `backend/app/prompts/dynamic_interview_prompt.py`

**Change**: Add CRITICAL FACTS section at top of prompt:

```python
prompt = f"""You are Chitta (צ'יטה) - a warm, empathetic developmental specialist.

## 🚨 CRITICAL FACTS - USE THESE IN EVERY RESPONSE 🚨

**Child Information (FACTS - DO NOT ASK AGAIN):**
{build_facts_section(child_name, age, gender, concerns)}

**RULES:**
- If child name is known: USE IT in every response! Say "מיכל" not "הילד שלך"
- If age is known: Reference it naturally: "בגיל 4.5..."
- If concerns mentioned: Build on them, don't re-ask
- NEVER ask for information shown above!

{rest_of_prompt}
```

Where `build_facts_section` returns:
- ✅ "• Child's name: **מיכל** ← USE THIS NAME!"
- ❌ "• Child's name: (not mentioned yet) ← ASK GENTLY if needed"

---

### Fix 2: Add Schema Validation to Extraction

**File**: `backend/app/prompts/interview_functions.py`

**Change**: Add Pydantic validation:

```python
from pydantic import BaseModel, Field, validator

class ExtractedInterviewData(BaseModel):
    """Validated extraction schema"""
    child_name: Optional[str] = Field(None, min_length=2)
    age: Optional[float] = Field(None, ge=0, le=18)
    gender: Optional[str] = Field(None, pattern="^(male|female|unknown)$")

    @validator('child_name')
    def validate_name(cls, v):
        if v and v.lower() in ['unknown', 'not mentioned', 'null']:
            return None  # Reject placeholder values
        return v

    @validator('age')
    def validate_age(cls, v):
        if v and (v < 0 or v > 18):
            raise ValueError("Age must be between 0 and 18")
        return v
```

**Result**: Invalid extractions rejected before saving.

---

### Fix 3: Add Extraction Verification

**File**: `backend/app/services/conversation_service.py`

**Change**: After extraction, verify critical data:

```python
# After extraction call
extracted = extraction_response.function_calls[0]['arguments']

# Verify critical fields if conversation progressed enough
if session.conversation_history > 3:  # After initial exchanges
    if not extracted.get('child_name'):
        logger.warning("⚠️ Child name not extracted after 3 turns!")
        # Add to system prompt: "Gently ask for child's name"

    if not extracted.get('age'):
        logger.warning("⚠️ Child age not extracted after 3 turns!")
        # Add to system prompt: "Gently ask for child's age"
```

---

### Fix 4: Simplify Intent Detection

**Remove**: Complex Sage/Hand architecture for basic cases

**Use**: Simple pattern matching + LLM validation

```python
def detect_intent_robust(message: str, extracted_data: dict) -> Intent:
    """Rock-solid intent detection with validation"""

    # 1. Simple keyword matching for common intents
    keywords = {
        'view_report': ['דוח', 'תוצאות', 'לראות את'],
        'upload_video': ['וידאו', 'סרטון', 'להעלות'],
        'consultation': ['שאלה', 'להתייעץ', 'לדבר'],
    }

    for intent, words in keywords.items():
        if any(word in message for word in words):
            # Found keyword match
            # 2. Verify with prerequisite check
            if prerequisite_met(intent, extracted_data):
                return Intent(type=intent, confidence=0.9)

    # 3. Fall back to LLM for ambiguous cases
    llm_intent = await llm_detect_intent(message)

    # 4. Validate LLM result
    if validate_intent(llm_intent, extracted_data):
        return llm_intent

    # 5. Default: conversation mode
    return Intent(type='conversation', confidence=1.0)
```

---

### Fix 5: Add Extraction Quality Metrics

**File**: `backend/app/services/session_service.py`

**Add**:

```python
def get_extraction_quality(self, family_id: str) -> dict:
    """Check extraction quality and completeness"""
    session = self.get_or_create_session(family_id)
    data = session.extracted_data
    turns = len(session.conversation_history)

    quality = {
        'has_name': bool(data.child_name),
        'has_age': bool(data.age),
        'has_concerns': len(data.primary_concerns) > 0,
        'turns_count': turns,
        'completeness': session.completeness
    }

    # Quality warnings
    if turns > 3 and not quality['has_name']:
        quality['warning'] = "Child name not extracted after 3 turns"
    if turns > 3 and not quality['has_age']:
        quality['warning'] = "Child age not extracted after 3 turns"

    return quality
```

---

## 📊 Validation Checklist

For extraction to be "rock solid":

- [ ] ✅ Name extracted within first 3 turns (if mentioned)
- [ ] ✅ Age extracted within first 3 turns (if mentioned)
- [ ] ✅ Extracted data validated with Pydantic schemas
- [ ] ✅ Extracted data PROMINENTLY shown in system prompt
- [ ] ✅ Extraction failures logged and handled
- [ ] ✅ Intent detection has fallback mechanisms
- [ ] ✅ No placeholder values ("unknown") stored as real data

---

## 🧪 Testing Strategy

1. **Extraction Test**:
   ```python
   parent_says("מיכל, בת 4.5")
   assert session.extracted_data.child_name == "מיכל"
   assert session.extracted_data.age == 4.5
   assert "מיכל" in next_chitta_response  # Uses name immediately
   ```

2. **Invalid Data Test**:
   ```python
   # LLM returns garbage
   extraction = {"child_name": "unknown", "age": -1}
   validated = validate_extraction(extraction)
   assert validated.child_name is None  # Rejected
   assert validated.age is None  # Rejected
   ```

3. **Missing Data Test**:
   ```python
   # After 5 turns, no name extracted
   session.conversation_history = [...]  # 5 turns
   quality = get_extraction_quality(family_id)
   assert quality['warning'] == "Child name not extracted after 3 turns"
   ```

---

## 📝 Implementation Priority

1. **HIGH**: Fix 1 - Prominent facts in system prompt (fixes immediate UX)
2. **HIGH**: Fix 2 - Schema validation (prevents garbage data)
3. **MEDIUM**: Fix 3 - Extraction verification (alerts to failures)
4. **MEDIUM**: Fix 5 - Quality metrics (monitoring)
5. **LOW**: Fix 4 - Simplify intent (can do later)

---

## 🎯 Success Metrics

After fixes:
- ✅ 95%+ extraction accuracy for name/age within 3 turns
- ✅ 0% invalid data in database (validated and rejected)
- ✅ 100% of responses use child's name once extracted
- ✅ <1% of conversations require name re-asking

**Wu Wei**: Make the natural path (extraction and usage) so clear and simple that failures become impossible.
