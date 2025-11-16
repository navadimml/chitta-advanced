# Comprehensive Intent Handling via Functions - Wu Wei Simplification

## 🎯 Current Modes (from Hand Service)

1. **CONVERSATION** - Continue natural dialogue (data collection)
2. **CONSULTATION** - Expert developmental guidance
   - **general**: "What is sensory seeking?"
   - **specific**: "Why did you say my child has sensory seeking?"
3. **DELIVER_ARTIFACT** - Show specific report/document
4. **EXPLAIN_PROCESS** - Help about the app itself
5. **EXECUTE_ACTION** - Do something specific

## 🔍 Current Functions

From `interview_functions.py`:
1. `extract_interview_data` - Extracts structured data
2. `user_wants_action` - Detects actions like view_report, upload_video, **consultation_mode**
3. `check_interview_completeness` - Checks if enough info collected

**Problem**: `user_wants_action` has "consultation_mode" but doesn't distinguish:
- General developmental questions
- Questions about Chitta's specific analysis
- Questions about the app

**Missing**: Help/explanation about the app itself

---

## ✨ Proposed: Comprehensive Function Schema

### Function 1: extract_interview_data ✅ (Keep as is)
Extracts: child_name, age, concerns, strengths, history, etc.

### Function 2: ask_developmental_question (NEW - replaces consultation detection)
```python
{
    "name": "ask_developmental_question",
    "description": """Call when parent asks a developmental/professional question.

    Examples:
    - "מה זה חיפוש חושי?" (What is sensory seeking?)
    - "האם זה נורמלי שהוא לא מדבר בגיל 3?" (Is it normal he doesn't talk at age 3?)
    - "למה ילדים עם ADHD מתקשים בקשב?" (Why do ADHD kids struggle with attention?)
    - "איזה סוג טיפול יעזור?" (What type of therapy would help?)

    Don't call for:
    - Questions about Chitta's specific analysis (use ask_about_analysis)
    - Questions about the app (use ask_about_app)""",
    "parameters": {
        "type": "object",
        "properties": {
            "question_topic": {
                "type": "string",
                "enum": [
                    "developmental_milestone",  # אבני דרך התפתחותיות
                    "diagnosis_explanation",     # הסבר על אבחון
                    "therapy_options",           # אפשרויות טיפול
                    "behavior_understanding",    # הבנת התנהגות
                    "parenting_strategy",        # אסטרטגיית הורות
                    "educational_approach",      # גישה חינוכית
                    "general_developmental"      # כללי התפתחותי
                ]
            },
            "question_text": {
                "type": "string",
                "description": "The actual question (for context)"
            },
            "relates_to_child": {
                "type": "boolean",
                "description": "True if asking specifically about their child's situation"
            }
        },
        "required": ["question_topic", "question_text"]
    }
}
```

### Function 3: ask_about_analysis (NEW - specific consultation)
```python
{
    "name": "ask_about_analysis",
    "description": """Call when parent asks about Chitta's specific analysis/conclusions.

    Examples:
    - "למה אמרת שיש לו חיפוש חושי?" (Why did you say he has sensory seeking?)
    - "איך הגעת למסקנה הזאת?" (How did you reach this conclusion?)
    - "מה ראית בסרטונים?" (What did you see in the videos?)
    - "למה המלצת על הדבר הזה?" (Why did you recommend this?)""",
    "parameters": {
        "type": "object",
        "properties": {
            "analysis_element": {
                "type": "string",
                "enum": [
                    "video_observation",      # שאלה על מה שראית בסרטון
                    "concern_identification", # למה זיהית את הדאגה הזאת
                    "strength_identification",# למה אמרת שזה חוזקה
                    "recommendation",         # למה המלצת על זה
                    "general_conclusion"      # שאלה כללית על המסקנה
                ]
            },
            "question_text": {
                "type": "string",
                "description": "What they're asking about"
            }
        },
        "required": ["analysis_element", "question_text"]
    }
}
```

### Function 4: ask_about_app (NEW - app help)
```python
{
    "name": "ask_about_app",
    "description": """Call when parent asks about the app itself, features, or process.

    Examples:
    - "איך מעלים סרטון?" (How do I upload a video?)
    - "מה קורה אחרי שאעלה את הסרטונים?" (What happens after I upload videos?)
    - "איפה אני רואה את הדוח?" (Where do I see the report?)
    - "איך זה עובד?" (How does this work?)
    - "מה הצעד הבא?" (What's the next step?)""",
    "parameters": {
        "type": "object",
        "properties": {
            "help_topic": {
                "type": "string",
                "enum": [
                    "how_to_upload_video",
                    "where_to_find_report",
                    "process_explanation",
                    "next_steps",
                    "app_features",
                    "technical_issue",
                    "general_help"
                ]
            },
            "question_text": {
                "type": "string",
                "description": "What they're asking"
            }
        },
        "required": ["help_topic", "question_text"]
    }
}
```

### Function 5: request_action (ENHANCED - was user_wants_action)
```python
{
    "name": "request_action",
    "description": """Call when parent explicitly requests to DO something.

    Examples:
    - "תראי לי את הדוח" (Show me the report)
    - "אני רוצה להעלות סרטון" (I want to upload a video)
    - "תיצרי לי את ההנחיות" (Generate the guidelines)
    - "רוצה לדבר עם מומחה" (Want to talk to an expert)""",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "generate_guidelines",       # תכיני הנחיות צילום
                    "view_guidelines",           # תראי לי את ההנחיות
                    "upload_video",              # רוצה להעלות סרטון
                    "view_report",               # רוצה לראות דוח
                    "schedule_consultation",     # קביעת פגישה עם מומחה
                    "find_experts",              # מציאת מומחים
                    "share_report",              # שיתוף דוח
                    "add_journal_entry",         # כתיבת יומן
                    "view_journal"               # צפייה ביומן
                ]
            },
            "details": {
                "type": "string",
                "description": "Additional context"
            }
        },
        "required": ["action"]
    }
}
```

---

## 📊 Mode Detection Logic (in System Prompt)

Instead of Sage + Hand LLM calls, the system prompt tells the LLM when to call which function:

```
## 🔧 פונקציות זמינות

אתה יכולה לקרוא לפונקציות הבאות:

### 1. extract_interview_data()
קראי כשההורה משתף מידע על הילד/ה - שם, גיל, דאגות, חוזקות, וכו'.

### 2. ask_developmental_question()
קראי כשההורה שואל שאלה התפתחותית כללית:
- "מה זה ADHD?"
- "האם זה נורמלי?"
- "איזה טיפול מומלץ?"

### 3. ask_about_analysis()
קראי כשההורה שואל על הניתוח/מסקנות שלך:
- "למה אמרת שיש לו חיפוש חושי?"
- "מה ראית בסרטונים?"

### 4. ask_about_app()
קראי כשההורה שואל על האפליקציה עצמה:
- "איך מעלים סרטון?"
- "מה הצעד הבא?"

### 5. request_action()
קראי כשההורה מבקש לעשות משהו ספציפי:
- "תכיני הנחיות צילום"
- "תראי לי את הדוח"

## 📝 איך להחליט?

**רוב הזמן**: רק extract_interview_data() - שיחה טבעית
**שאלה התפתחותית**: גם ask_developmental_question()
**שאלה על הניתוח שלך**: גם ask_about_analysis()
**שאלה על האפליקציה**: גם ask_about_app()
**בקשה לפעולה**: גם request_action()

**אפשר לקרוא למספר פונקציות באותו תור!**
```

---

## 🎯 Response Handling

```python
for func_call in response.function_calls:
    if func_call.name == "extract_interview_data":
        update_extracted_data(family_id, func_call.arguments)

    elif func_call.name == "ask_developmental_question":
        # Inject developmental knowledge into response
        knowledge = get_developmental_knowledge(func_call.arguments['question_topic'])
        # Can add to context or respond directly

    elif func_call.name == "ask_about_analysis":
        # Explain Chitta's reasoning from artifacts
        analysis_context = get_analysis_context(
            family_id,
            func_call.arguments['analysis_element']
        )
        # LLM response uses this context

    elif func_call.name == "ask_about_app":
        # Provide app help
        help_content = get_app_help(func_call.arguments['help_topic'])
        # Can show card or inline help

    elif func_call.name == "request_action":
        # Execute requested action
        execute_action(family_id, func_call.arguments['action'])
```

---

## 🎨 Making it Configurable (YAML)

```yaml
# config/conversation_intents.yaml

intents:
  developmental_question:
    function: ask_developmental_question
    topics:
      - developmental_milestone
      - diagnosis_explanation
      - therapy_options
      - behavior_understanding
      - parenting_strategy
      - educational_approach
      - general_developmental
    response_strategy: inject_knowledge

  analysis_question:
    function: ask_about_analysis
    elements:
      - video_observation
      - concern_identification
      - strength_identification
      - recommendation
      - general_conclusion
    response_strategy: explain_reasoning

  app_help:
    function: ask_about_app
    topics:
      - how_to_upload_video
      - where_to_find_report
      - process_explanation
      - next_steps
      - app_features
      - technical_issue
      - general_help
    response_strategy: provide_help

  action_request:
    function: request_action
    actions:
      - generate_guidelines
      - view_guidelines
      - upload_video
      - view_report
      - schedule_consultation
      - find_experts
      - share_report
      - add_journal_entry
      - view_journal
    response_strategy: execute_action
```

**Benefits**:
- ✅ Easy to add new intents (just add to YAML)
- ✅ Easy to add new actions (just add to enum + handler)
- ✅ Easy to modify topics/categories
- ✅ Clear documentation in one place
- ✅ Can load different configs for different contexts

---

## 📈 Comparison

| Aspect | Current (Sage+Hand) | Proposed (Functions) |
|--------|-------------------|---------------------|
| **Intent Detection** | 2 LLM calls | 0 LLM calls (function calling) |
| **Extensibility** | Add code | Add to YAML |
| **Latency** | High | Low |
| **Accuracy** | Good | Same or better |
| **Configurability** | Hard-coded | YAML-driven |

---

## ✅ Final Simplified Architecture

```
Parent sends message
    ↓
1. Main LLM (with comprehensive functions)
   - Generates conversation response
   - Calls extract_interview_data() if info shared
   - Calls ask_developmental_question() if question
   - Calls ask_about_analysis() if asking about Chitta
   - Calls ask_about_app() if asking about app
   - Calls request_action() if wants to do something
    ↓
2. Process function calls
   - Update extracted data
   - Inject knowledge if needed
   - Execute actions if requested
    ↓
3. Semantic Check (every 3 turns until guidelines ready)
    ↓
Response returned
```

**Total**: 1-2 LLM calls instead of 5-6!

---

## 🎯 Answer to Your Question

**"What about other intents?"**
→ Handled via function calling! 5 comprehensive functions cover ALL modes.

**"Seeking help on the app?"**
→ `ask_about_app()` function with help topics.

**"Consultation about child development?"**
→ `ask_developmental_question()` for general + `ask_about_analysis()` for specific.

**"Maybe add more in future?"**
→ YES! Easy to add:
1. Add new function definition
2. Add to YAML config (optional)
3. Add handler in process_function_calls()
4. Done!

**"Should we configure it?"**
→ YES! YAML config for:
- Intent topics/categories (easy to extend)
- Action types (easy to add new actions)
- Response strategies (how to handle each intent)

**No string patterns!** All via function calling = robust + LLM-native!
