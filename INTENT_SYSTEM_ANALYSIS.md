# Intent System Analysis & Improvement Proposal

## Current Architecture (Beautiful Design! ✅)

### Layer 1: Intent Classification (GENERAL)
**File:** `backend/app/prompts/intent_types.py`

```python
class IntentCategory(Enum):
    DATA_COLLECTION = "data_collection"      # Continue interview
    ACTION_REQUEST = "action_request"        # Do something specific
    INFORMATION_REQUEST = "information_request"  # Learn about app
    TANGENT = "tangent"                      # Off-topic question
    PAUSE_EXIT = "pause_exit"                # Stop/leave

class InformationRequestType(Enum):
    APP_FEATURES = "app_features"
    PROCESS_EXPLANATION = "process_explanation"
    CURRENT_STATE = "current_state"
    PREREQUISITE_EXPLANATION = "prerequisite_explanation"
    NEXT_STEPS = "next_steps"
    DOMAIN_QUESTION = "domain_question"

@dataclass
class DetectedIntent:
    category: IntentCategory
    specific_action: Optional[str] = None
    information_type: Optional[InformationRequestType] = None
    confidence: float = 1.0  # ← NOT USED currently!
```

**This is GENERAL - works for any domain ✅**

---

### Layer 2: Domain Knowledge (SPECIFIC)
**File:** `backend/app/prompts/domain_knowledge.py`

```python
FAQ = {
    "what_is_chitta": {
        "question_patterns": [
            "מה זה צ'יטה", "what is chitta", "who are you"
        ],
        "answer_hebrew": "..."
    },
    "creative_writing_about_chitta": {
        "question_patterns": [
            "תכתבי לי שיר", "write me a poem", "איך עבר לך היום"
        ],
        "answer_hebrew": "..."
    },
    # ... more FAQs
}
```

**This is SPECIFIC to Chitta domain ✅**

---

### Layer 3: Knowledge Service (GENERAL mechanism)
**File:** `backend/app/services/knowledge_service.py`

**This should be GENERAL - works for any domain by using Layer 2 content**

---

## Current Problems (Primitive Implementation ❌)

### Problem 1: String Matching in `detect_information_request()`

```python
def detect_information_request(self, user_message: str) -> Optional[InformationRequestType]:
    message_lower = user_message.lower()

    # Check for app features questions
    if any(phrase in message_lower for phrase in [
        "מה אני יכול", "מה יש", "איזה אפשרויות", "מה זמין",
        "what can i do", "what features", "what's available"
    ]):
        return InformationRequestType.APP_FEATURES
```

**Issues:**
- ❌ Too rigid: "מה אני יכול לעשות?" ✅ matches, but "אני רוצה לדעת מה האפשרויות" ❌ doesn't
- ❌ No semantic understanding: "תספרי לי על התכונות" (tell me about features) won't match
- ❌ No confidence scores
- ❌ Can't handle variations/morphology
- ❌ Hebrew is complex - different word forms not handled

### Problem 2: String Matching in `match_faq_question()`

```python
def match_faq_question(user_message: str) -> Optional[str]:
    user_message_lower = user_message.lower()

    for faq_key, faq_data in FAQ.items():
        for pattern in faq_data["question_patterns"]:
            if pattern.lower() in user_message_lower:
                return faq_key
```

**Issues:**
- ❌ Substring matching: "תכתבי שיר" in message → matches, but "שירה" (a name) → false positive!
- ❌ No semantic similarity
- ❌ Miss close matches: "כתבי לי שיר" vs "תכתבי לי שיר" (minor difference)
- ❌ Order matters: "שיר תכתבי לי?" might not match

### Problem 3: Not Using `DetectedIntent` Properly

The beautiful `DetectedIntent` dataclass with confidence scores **is not being used**!

```python
@dataclass
class DetectedIntent:
    confidence: float = 1.0  # ← Always 1.0, never actually computed
```

---

## Proposed Solution: Two-Tier Intent System

### Architecture Overview

```
User Message
    ↓
┌─────────────────────────────────────┐
│ Tier 1: Fast Path (Pattern Match)  │
│ - Exact FAQ pattern matching        │
│ - No LLM call                       │
│ - Instant response                  │
└─────────────────────────────────────┘
    ↓ if no exact match
┌─────────────────────────────────────┐
│ Tier 2: Accurate Path (LLM)        │
│ - LLM-based intent classification   │
│ - Semantic understanding            │
│ - Confidence scores                 │
│ - Returns DetectedIntent            │
└─────────────────────────────────────┘
    ↓
Response with proper intent handling
```

---

## Detailed Implementation

### Tier 1: Fast Path (Keep but Improve)

**When to use:** Exact matches for common FAQs

**How it works:**
```python
def check_faq_exact_match(user_message: str) -> Optional[Tuple[str, str]]:
    """
    Check if message matches FAQ patterns EXACTLY

    Returns:
        (faq_key, direct_answer) if matched, None otherwise
    """
    # Use the existing FAQ patterns from domain_knowledge
    faq_key = domain_knowledge.match_faq_question(user_message)

    if faq_key and faq_key in self.faq:
        answer = self.faq[faq_key]["answer_hebrew"]
        return (faq_key, answer)

    return None
```

**Improvements needed:**
- Better pattern matching (not just substring)
- Handle word boundaries
- Maybe use regex for patterns

---

### Tier 2: Accurate Path (NEW - LLM-based)

**When to use:** When Tier 1 doesn't match

**How it works:**
```python
async def detect_intent_llm(
    self,
    user_message: str,
    llm_provider: BaseLLMProvider,
    context: Dict
) -> DetectedIntent:
    """
    Use LLM to classify intent with semantic understanding

    Returns:
        DetectedIntent with proper category, type, and confidence
    """

    # Build classification prompt using Layer 1 enums
    classification_prompt = f"""Classify this user message into intent categories.

User message: "{user_message}"

Intent Categories:
1. DATA_COLLECTION - User wants to continue the main conversation/interview
2. ACTION_REQUEST - User wants to perform a specific action
3. INFORMATION_REQUEST - User wants to learn about app/process
4. TANGENT - Off-topic or tangential request
5. PAUSE_EXIT - User wants to stop/leave

If INFORMATION_REQUEST, specify type:
- APP_FEATURES: What can I do?
- PROCESS_EXPLANATION: How does it work?
- CURRENT_STATE: Where am I?
- DOMAIN_QUESTION: Question about the domain topic
- PREREQUISITE_EXPLANATION: Why can't I do X?

If ACTION_REQUEST, specify which action from: {list(Action)}

If TANGENT, specify if it's:
- Creative writing request (poems, stories)
- Personal questions about system
- Philosophical discussions
- Off-topic conversation

Respond in JSON:
{{
    "category": "...",
    "information_type": "..." or null,
    "specific_action": "..." or null,
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
}}"""

    # Call LLM with small temperature for consistency
    response = await llm_provider.chat(
        messages=[
            Message(role="system", content=classification_prompt),
            Message(role="user", content=user_message)
        ],
        temperature=0.1,
        max_tokens=200
    )

    # Parse JSON response
    intent_data = json.loads(response.content)

    # Build DetectedIntent properly
    return DetectedIntent(
        category=IntentCategory(intent_data["category"]),
        information_type=InformationRequestType(intent_data["information_type"]) if intent_data["information_type"] else None,
        specific_action=intent_data["specific_action"],
        confidence=intent_data["confidence"],
        user_message=user_message,
        context={"reasoning": intent_data["reasoning"]}
    )
```

---

## Benefits of Two-Tier System

### ✅ Fast for Common Cases
- FAQ exact matches → instant response (Tier 1)
- No LLM call needed
- Saves tokens and latency

### ✅ Accurate for Complex Cases
- Semantic understanding (Tier 2)
- Handles variations: "תכתבי שיר" vs "כתבי לי שיר אחד"
- Confidence scores
- Better Hebrew handling (LLM understands morphology)

### ✅ Maintains Beautiful Architecture
- Layer 1 (intent_types.py) still GENERAL ✅
- Layer 2 (domain_knowledge.py) still SPECIFIC ✅
- Layer 3 (knowledge_service.py) uses both layers properly ✅

### ✅ Fixes All Current Problems
- ❌ String matching → ✅ Semantic understanding
- ❌ No confidence → ✅ Confidence scores
- ❌ Misses variations → ✅ Handles variations
- ❌ DetectedIntent unused → ✅ DetectedIntent fully utilized

---

## Implementation Plan

### Step 1: Improve Tier 1 (Fast Path)
**File:** `knowledge_service.py`

```python
def match_faq_with_confidence(self, user_message: str) -> Optional[Tuple[str, str, float]]:
    """
    Match FAQ patterns with confidence score

    Returns:
        (faq_key, answer, confidence) if matched, None otherwise
    """
    # Better pattern matching
    # Maybe use fuzzy matching for close matches
    # Return confidence score
```

### Step 2: Add Tier 2 (LLM Intent Classification)
**File:** `knowledge_service.py`

```python
async def detect_intent_llm(
    self,
    user_message: str,
    llm_provider: BaseLLMProvider,
    context: Dict
) -> DetectedIntent:
    """Use LLM for accurate intent classification"""
    # Implementation as shown above
```

### Step 3: Update ConversationService to Use Both Tiers
**File:** `conversation_service.py`

```python
async def process_message(self, family_id: str, user_message: str):
    # 1. Try Tier 1 (fast) - FAQ exact match
    faq_match = self.knowledge_service.match_faq_with_confidence(user_message)

    if faq_match and faq_match[2] >= 0.9:  # High confidence
        return direct_answer_response(faq_match)

    # 2. Try Tier 2 (accurate) - LLM classification
    detected_intent = await self.knowledge_service.detect_intent_llm(
        user_message,
        self.llm,
        context
    )

    # 3. Handle intent based on category
    if detected_intent.category == IntentCategory.TANGENT:
        # Handle tangent
        pass
    elif detected_intent.category == IntentCategory.ACTION_REQUEST:
        # Check prerequisites
        pass
    elif detected_intent.category == IntentCategory.INFORMATION_REQUEST:
        # Inject knowledge
        pass
    else:
        # Continue conversation
        pass
```

---

## Summary

### Current State
- ✅ Beautiful architecture (3 layers)
- ❌ Primitive implementation (string matching)
- ❌ `DetectedIntent` not fully used
- ❌ No confidence scores
- ❌ Misses variations

### Proposed State
- ✅ Beautiful architecture (maintained)
- ✅ Intelligent implementation (two-tier)
- ✅ `DetectedIntent` fully utilized
- ✅ Confidence scores computed
- ✅ Handles variations with LLM
- ✅ Fast for common cases (Tier 1)
- ✅ Accurate for complex cases (Tier 2)

---

## Questions for Discussion

1. Should we use embeddings for FAQ matching (even faster than LLM)?
2. What confidence threshold for Tier 1 → Tier 2 fallback?
3. Cache LLM intent classification results?
4. Add intent classification training examples to improve accuracy?

---

**Date:** November 5, 2025
**Author:** Claude Code Assistant
**Status:** Proposal for Discussion
