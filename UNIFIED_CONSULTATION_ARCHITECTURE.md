# Unified Consultation Architecture: Graphiti-Powered

**Status:** Design Document
**Date:** 2025-11-11
**Philosophy:** Wu Wei - Leverage existing power, don't reinvent

---

## Core Insight

Instead of creating special handlers for different types of knowledge (artifacts, documents, conversations), **use Graphiti's search as the universal retrieval mechanism**.

### The Simplification

**Before (Complex):**
```
Question about artifact? → artifact_handler() → retrieve artifact
Question about diagnosis? → diagnosis_handler() → retrieve document
Question about child? → context_handler() → retrieve structured data
General question? → consultation_handler() → retrieve conversation
```

**After (Simple - Wu Wei):**
```
ANY question → graphiti.search(question, child_node, family_id) → relevant context
```

Graphiti automatically retrieves relevant information from ALL sources:
- Generated artifacts (reports, guidelines, analysis)
- Uploaded documents (diagnosis reports, evaluations)
- Conversation history (all discussions)
- Journal entries (observations over time)
- Structured data (milestones, concerns, professionals)

---

## How Uploaded Documents Work

### Document as Episode

When a parent uploads a diagnosis report (איבחון):

```python
# backend/app/services/document_service.py
from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
from datetime import datetime
import PyPDF2  # or other document parser

async def upload_diagnosis_document(
    family_id: str,
    child_id: str,
    file_path: str,
    document_metadata: dict
):
    """
    Upload an external diagnosis report (איבחון) to Graphiti.

    The document becomes searchable alongside all other knowledge.
    """

    # Extract text from PDF/DOC
    document_text = extract_text_from_document(file_path)

    # Create episode with structured metadata
    episode_body = f"""
    External Diagnosis Report

    Document Type: {document_metadata.get('type', 'Diagnosis Report')}
    Professional: {document_metadata.get('professional_name')}
    Specialty: {document_metadata.get('specialty')}
    Date: {document_metadata.get('report_date')}

    Full Content:
    {document_text}

    Key Findings:
    {document_metadata.get('key_findings', 'See full content above')}
    """

    # Add to Graphiti as episode
    await graphiti.add_episode(
        name=f"diagnosis_report_{child_id}_{document_metadata.get('report_date')}",
        episode_body=episode_body,
        source=EpisodeType.text,
        reference_time=datetime.fromisoformat(document_metadata['report_date']),
        group_id=f"family_{family_id}",
        entity_types=entity_types,
        edge_types=edge_types,
        edge_type_map=edge_type_map
    )

    # Graphiti automatically:
    # 1. Extracts entities (diagnoses, observations, recommendations)
    # 2. Creates relationships (Child -> HasDiagnosis -> Diagnosis entity)
    # 3. Makes it searchable with all other knowledge

    return {
        "status": "uploaded",
        "searchable": True,
        "message": "Document indexed and ready for consultation"
    }
```

### Document Entity Type

Add new entity type for external documents:

```python
# In entity schema (from GRAPHITI_INTEGRATION_GUIDE.md)

class ExternalDocument(BaseModel):
    """An uploaded external document (diagnosis report, evaluation, etc.)"""
    document_type: str = Field(..., description="Diagnosis, Evaluation, Assessment, etc.")
    professional_name: Optional[str] = None
    specialty: Optional[str] = None
    report_date: datetime
    key_findings: Optional[list[str]] = None

class Diagnosis(BaseModel):
    """A clinical diagnosis from external document or assessment"""
    diagnosis_name: str = Field(..., description="e.g., Autism Spectrum Disorder, Speech Delay")
    icd_code: Optional[str] = None
    severity: Optional[str] = Field(None, description="mild, moderate, severe")
    notes: Optional[str] = None
```

### Edge Types for Documents

```python
class ReceivedDiagnosis(BaseModel):
    """Child received a diagnosis from a professional"""
    diagnosis_date: datetime
    diagnosing_professional: Optional[str] = None
    confidence_level: Optional[str] = Field(None, description="confirmed, suspected, ruled out")

class DocumentedIn(BaseModel):
    """Finding or diagnosis is documented in an external document"""
    page_number: Optional[int] = None
    section: Optional[str] = None

# Update edge type map
edge_type_map = {
    # ... existing mappings
    ("Child", "Diagnosis"): ["ReceivedDiagnosis"],
    ("Child", "ExternalDocument"): ["HasDocument"],
    ("Diagnosis", "ExternalDocument"): ["DocumentedIn"],
    ("Observation", "ExternalDocument"): ["DocumentedIn"],
}
```

---

## Universal Consultation Service

### The Single Handler

```python
# backend/app/services/consultation_service.py
from graphiti_core import Graphiti
from services.llm.factory import LLMFactory
from services.llm.base import Message
from datetime import datetime
import json

class ConsultationService:
    """
    Universal consultation service powered by Graphiti.

    Works for ANY question:
    - "What did the psychologist write about attention?" → searches diagnosis docs
    - "What did you mean by 'sensory seeking' in the report?" → searches our artifacts
    - "How has speech improved over time?" → searches all observations
    - "What strategies worked for meltdowns?" → searches journal + conversations
    """

    def __init__(self, graphiti: Graphiti, llm_provider: str = "gemini"):
        self.graphiti = graphiti
        self.llm = LLMFactory.create(
            provider=llm_provider,
            api_key=settings.LLM_API_KEY,
            model=settings.LM_MODEL
        )

    async def handle_consultation(
        self,
        family_id: str,
        child_id: str,
        question: str,
        conversation_history: list[dict] = None
    ) -> dict:
        """
        Universal consultation handler.

        1. Use Graphiti to retrieve relevant context
        2. Generate response with full context
        3. Save consultation as episode for future reference
        """

        # Get child's node for centered search
        child_node = await self._get_child_node(child_id, family_id)

        # Retrieve relevant context using Graphiti's semantic search
        context_results = await self.graphiti.search(
            query=question,
            center_node_uuid=child_node.uuid if child_node else None,
            group_id=f"family_{family_id}",
            num_results=20  # Get rich context
        )

        # Format context for LLM
        formatted_context = self._format_context_for_llm(context_results)

        # Build system prompt with context
        system_prompt = f"""
        אתה Chitta, מדריכה להתפתחות ילדים בישראל.

        ההורה שואל שאלה. יש לך גישה להיסטוריה מלאה של הילד/ה:
        - שיחות שקיימתם
        - דוחות שיצרת (הנחיות, ניתוחים, סיכומים)
        - מסמכים שההורה העלה (איבחונים, הערכות מקצועיות)
        - רישומי יומן (תצפיות לאורך זמן)
        - אבני דרך והתקדמות

        הקשר רלוונטי מה-Knowledge Graph:
        {formatted_context}

        הנחיות למענה:
        1. השתמשי בקשר המלא - התייחסי לתצפיות ספציפיות, תאריכים, דפוסים
        2. אם השאלה על מסמך חיצוני (איבחון), ציטטי ממנו ישירות
        3. אם השאלה על דוח שכתבת, הסבירי מה התכוונת ולמה
        4. אם השאלה על דפוסים לאורך זמן, הראי את המגמה
        5. תני עצות מעשיות מבוססות על מה שעבד בעבר
        6. אם אין לך מידע מספיק, תגידי זאת בכנות

        דברי בעברית טבעית, חמה ותומכת.
        """

        # Generate consultation response
        messages = [
            Message(role="system", content=system_prompt),
            *[Message(role=h["role"], content=h["content"])
              for h in (conversation_history or [])],
            Message(role="user", content=question)
        ]

        llm_response = await self.llm.generate(
            messages=messages,
            temperature=0.7,
            max_tokens=2048
        )

        response_text = llm_response.content

        # Save this consultation as an episode for future context
        await self.graphiti.add_episode(
            name=f"consultation_{child_id}_{datetime.now().isoformat()}",
            episode_body=f"Parent Question: {question}\n\nChitta Response: {response_text}",
            source=EpisodeType.message,
            reference_time=datetime.now(),
            group_id=f"family_{family_id}",
            entity_types=entity_types,
            edge_types=edge_types,
            edge_type_map=edge_type_map
        )

        return {
            "response": response_text,
            "context_sources": self._summarize_sources(context_results),
            "timestamp": datetime.now().isoformat()
        }

    def _format_context_for_llm(self, context_results: list) -> str:
        """Format Graphiti search results for LLM consumption"""

        if not context_results:
            return "אין מידע זמין עדיין."

        formatted = []

        for i, result in enumerate(context_results, 1):
            # Each result has: fact, reference_time, episode_name, etc.
            timestamp = result.reference_time.strftime("%Y-%m-%d") if result.reference_time else "Unknown date"
            source_type = self._identify_source_type(result.episode_name)

            formatted.append(f"""
            [{i}] [{source_type}] ({timestamp})
            {result.fact}
            """)

        return "\n".join(formatted)

    def _identify_source_type(self, episode_name: str) -> str:
        """Identify the source type from episode name"""
        if "diagnosis_report" in episode_name:
            return "📄 איבחון חיצוני"
        elif "baseline_parent_report" in episode_name:
            return "📋 דוח שיצרה Chitta"
        elif "journal" in episode_name:
            return "📔 יומן"
        elif "interview" in episode_name:
            return "💬 שיחה"
        elif "video_analysis" in episode_name:
            return "🎥 ניתוח וידאו"
        else:
            return "📝 מידע"

    def _summarize_sources(self, context_results: list) -> dict:
        """Summarize which sources were used in consultation"""
        sources = {
            "external_documents": 0,
            "generated_reports": 0,
            "conversations": 0,
            "journal_entries": 0,
            "video_analyses": 0
        }

        for result in context_results:
            if "diagnosis_report" in result.episode_name:
                sources["external_documents"] += 1
            elif "report" in result.episode_name:
                sources["generated_reports"] += 1
            elif "journal" in result.episode_name:
                sources["journal_entries"] += 1
            elif "interview" in result.episode_name or "consultation" in result.episode_name:
                sources["conversations"] += 1
            elif "video" in result.episode_name:
                sources["video_analyses"] += 1

        return sources

    async def _get_child_node(self, child_id: str, family_id: str):
        """Get the child's node UUID for centered search"""
        # Search for the child entity
        results = await self.graphiti.search(
            query=f"child with id {child_id}",
            group_id=f"family_{family_id}",
            num_results=1
        )

        if results and len(results) > 0:
            return results[0]
        return None
```

---

## Example Usage Scenarios

### Scenario 1: Question About External Diagnosis

```python
# Parent uploaded a diagnosis report from a psychologist
# Report mentioned "executive function difficulties"

# Parent asks:
question = "מה המשמעות של 'קשיי תפקודים ניהוליים' שהפסיכולוגית כתבה?"

response = await consultation_service.handle_consultation(
    family_id="family_123",
    child_id="child_456",
    question=question
)

# Graphiti automatically finds:
# 1. The external diagnosis document episode
# 2. Relevant observations from conversations about attention/planning
# 3. Strategies tried from journal entries
# 4. Related information from generated reports

# Chitta responds:
"""
הפסיכולוגית התייחסה ל'תפקודים ניהוליים' (Executive Functions) - אלו הכישורים
שעוזרים לילד לתכנן, להתארגן, ולעצור ולחשוב לפני פעולה.

מהאיבחון שהעלית (15.10.2024), היא כתבה:
"נצפו קשיים בתפקודים ניהוליים, במיוחד בתכנון רצף פעולות ובעיכוב תגובה"

זה מתחבר למה שסיפרת לי בשיחה שלנו ב-20.10:
"קשה לו לעצור לפני שהוא עושה משהו, הוא פשוט קופץ"

דפוס זה חזר גם ביומן שלך - 3 מתוך 4 רישומים באוקטובר דיווחו על התנהגות
אימפולסיבית (למשל: קופץ מהמיטה לפני שהפעוטון מוכן).

מה שאפשר לעשות:
1. פירוק משימות לשלבים קטנים ("קודם נלביש גרביים, אחר כך נעליים")
2. תמונות רצף פעולות על הקיר
3. משחקי 'עצור-המשך' (כמו 'אור ירוק-אור אדום')

הטיפולית התעסוקתית שלכם גם המליצה על משהו דומה בפגישה הראשונה.
"""
```

### Scenario 2: Question About Generated Report

```python
question = "למה כתבת בדוח שיש לו 'חיפוש חושי'? מה זה אומר?"

# Graphiti finds:
# 1. The baseline_parent_report artifact episode
# 2. Original interview where parent described behaviors
# 3. Video analysis that identified sensory-seeking patterns
# 4. Professional diagnosis that mentioned sensory processing

# Chitta responds:
"""
כתבתי 'חיפוש חושי' (Sensory Seeking) בדוח כי שמתי לב לדפוס של התנהגויות
שכולן קשורות לחיפוש גירוי חושי חזק.

במה דיברנו על זה:
- בשיחה שלנו (8.9.2024) סיפרת: "הוא אוהב לקפוץ על הספה בלי הפסקה"
- בסרטון הראשון (12.9) ראיתי אותו מסתובב במעגלים 7 פעמים
- ביומן (15.9) רשמת: "היום הוא ביקש שאני אלחץ אותו חזק בשמיכה"

כל אלו הן דרכים שהגוף שלו מחפש תחושות תנועה ולחץ.

זה לא דבר רע! זה סוג של ויסות חושי. הילדים האלו פשוט צריכים יותר
קלט חושי כדי להרגיש מאורגנים.

גם הטיפולית התעסוקתית שלכם כתבה משהו דומה באיבחון שלה (20.9):
"מראה דפוסי Sensory Seeking במערכת הווסטיבולרית והפרופריוצפטיבית"

הדבר החשוב: לתת לו הזדמנויות בטוחות לחיפוש החושי הזה - טרמפולינה,
משחקי דחיפה/משיכה, שמיכות כבדות.
"""
```

### Scenario 3: Pattern Over Time

```python
question = "האם הדיבור שלו השתפר בחודשיים האחרונים?"

# Graphiti searches across time:
# - Conversations from September, October, November
# - Journal entries documenting speech milestones
# - Video analysis comparing early vs recent videos
# - Professional notes from speech therapist

# Chitta responds:
"""
כן! אני רואה שיפור ברור בדיבור של יוני בחודשיים האחרונים. בואי אראה לך:

ספטמבר (נקודת התחלה):
- "יש לו כמה מילים בודדות אבל לא משפטים" (שיחה, 8.9)
- בסרטון הראשון: זיהיתי 4 מילים ברורות

אוקטובר (שיפור ניכר):
- "היום הוא אמר 'אבא בוא' - שתי מילים ביחד!" (יומן, 15.10)
- גם הקלינאית התקשורת ציינה בפגישה (22.10): "מתחיל לשלב שתי מילים"

נובמבר (המשך התקדמות):
- "אמר לי היום 'רוצה מים' - אני בהלם!" (יומן, 3.11)
- בשיחה שלנו (7.11) סיפרת שהוא אמר 4 משפטים שונים באותו יום

זה שיפור משמעותי! מ-4 מילים בודדות לעשרות מילים ומשפטים בני 2-3 מילים.

קצב הדיבור שלו עלה פי 3 בחודשיים - זה מעולה! ממשיכים בדיוק את מה שאת עושה. 💙
"""
```

---

## Integration with Conversation Service

```python
# backend/app/services/conversation_service.py

async def process_message(family_id: str, child_id: str, user_message: str):
    """
    Process incoming message - detect if it's a consultation question
    """

    # Detect intent (existing logic)
    intent = await detect_intent(user_message, conversation_history)

    if intent == "SEEKING_CONSULTATION":
        # Use universal consultation service
        result = await consultation_service.handle_consultation(
            family_id=family_id,
            child_id=child_id,
            question=user_message,
            conversation_history=get_recent_history(family_id)
        )

        return {
            "response": result["response"],
            "sources_used": result["context_sources"],
            "type": "consultation"
        }

    elif intent == "SHARING_INFORMATION":
        # Extract data and continue conversation
        # ... existing logic
        pass

    elif intent == "ACTION_REQUEST":
        # Handle action (view report, generate summary, etc.)
        # ... existing logic
        pass

    # ... other intents
```

---

## Benefits of Unified Approach

### 1. **Simplicity (פשוט)**
- ONE service for all consultation types
- NO special handlers for different knowledge types
- Graphiti handles complexity internally

### 2. **Generality (כללי)**
- Works for existing knowledge: conversations, reports, journal
- Works for NEW knowledge types: uploaded documents, video analysis, professional notes
- Future-proof: any new knowledge type just becomes an episode

### 3. **Accuracy (מדויק)**
- Semantic search finds relevant context automatically
- Temporal awareness (recent vs old information)
- Relationship awareness (connected facts surface together)

### 4. **Context-Rich (עשיר בהקשר)**
- LLM gets full context from all sources
- Can reference specific observations, dates, patterns
- Creates natural, informed responses

### 5. **Privacy (פרטיות)**
- `group_id=family_X` ensures complete isolation
- Each family's knowledge is separate
- No cross-family leakage

---

## Implementation Steps

### Step 1: Extend Entity Schema (Week 1)

```python
# Add to backend/app/services/graphiti_service.py

# New entity types
class ExternalDocument(BaseModel):
    document_type: str
    professional_name: Optional[str] = None
    specialty: Optional[str] = None
    report_date: datetime
    key_findings: Optional[list[str]] = None

class Diagnosis(BaseModel):
    diagnosis_name: str
    icd_code: Optional[str] = None
    severity: Optional[str] = None
    notes: Optional[str] = None

# New edge types
class ReceivedDiagnosis(BaseModel):
    diagnosis_date: datetime
    diagnosing_professional: Optional[str] = None

class DocumentedIn(BaseModel):
    page_number: Optional[int] = None
    section: Optional[str] = None

# Update edge_type_map
edge_type_map.update({
    ("Child", "Diagnosis"): ["ReceivedDiagnosis"],
    ("Child", "ExternalDocument"): ["HasDocument"],
    ("Diagnosis", "ExternalDocument"): ["DocumentedIn"],
})
```

### Step 2: Implement Document Upload Service (Week 1-2)

```python
# backend/app/services/document_service.py
# (See code example above)
```

### Step 3: Implement Universal Consultation Service (Week 2)

```python
# backend/app/services/consultation_service.py
# (See code example above)
```

### Step 4: Integrate with Conversation Flow (Week 2-3)

- Update conversation_service.py to route consultation questions
- Add UI for document upload
- Display source attribution in responses

### Step 5: Test with Real Data (Week 3)

- Upload sample diagnosis reports
- Test consultation across all knowledge types
- Verify context relevance and quality

---

## Example API Endpoints

### Upload Document

```python
@router.post("/families/{family_id}/documents/upload")
async def upload_document(
    family_id: str,
    child_id: str,
    file: UploadFile,
    metadata: DocumentMetadata
):
    """Upload external document (diagnosis, evaluation, etc.)"""

    # Save file
    file_path = await save_uploaded_file(file, family_id)

    # Ingest into Graphiti
    result = await document_service.upload_diagnosis_document(
        family_id=family_id,
        child_id=child_id,
        file_path=file_path,
        document_metadata=metadata.dict()
    )

    return result
```

### Ask Consultation Question

```python
@router.post("/families/{family_id}/consultation")
async def ask_consultation_question(
    family_id: str,
    child_id: str,
    question: ConsultationRequest
):
    """Ask any consultation question - universal handler"""

    result = await consultation_service.handle_consultation(
        family_id=family_id,
        child_id=child_id,
        question=question.text,
        conversation_history=question.context
    )

    return {
        "answer": result["response"],
        "sources": result["context_sources"],
        "timestamp": result["timestamp"]
    }
```

---

## Wu Wei Achievement

**Before:**
- Multiple special handlers
- Complex routing logic
- Duplicate code for different knowledge types
- Fragile (breaks when new types added)

**After:**
- Single consultation service
- Graphiti handles routing via semantic search
- Universal mechanism for all knowledge
- Extensible (new types just become episodes)

**Wu Wei:** פשוט - נטול חלקים עודפים (Simple - without excess parts)

The power was already there in Graphiti. We just needed to use it fully instead of building redundant handlers on top.

---

## Next Steps

1. ✅ **Design complete** (this document)
2. 🔧 **Extend entity schema** with ExternalDocument and Diagnosis
3. 🔧 **Implement document upload service**
4. 🔧 **Implement universal consultation service**
5. 🔧 **Add UI for document upload**
6. 🔧 **Test with real diagnosis reports**
7. 🔧 **Validate consultation quality**

---

**Status:** Ready for implementation
**Complexity:** Simple (Wu Wei)
**Extensibility:** Infinite (any new knowledge type works automatically)
