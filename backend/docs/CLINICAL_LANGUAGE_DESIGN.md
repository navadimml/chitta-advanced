# Clinical Language & Observation Design

## The Problem

Chitta has two audiences with different language needs:

1. **Parents** - Need everyday language they understand
2. **Professionals** - Need clinical precision for useful summaries

Currently, the system uses clinical terms everywhere:
- "תשומת לב משותפת" (joint attention)
- "קשר עין" (eye contact)
- "אבני דרך התפתחותיות" (developmental milestones)

Parents may not understand these terms, yet professionals NEED them.

---

## Design Principle: Two Languages, One Concept

Every clinical concept has:
- **Internal ID** - Used in code (e.g., `joint_attention`)
- **Clinical Term** - For professional summaries (e.g., "תשומת לב משותפת")
- **Parent Language** - For conversation/UI (e.g., "כשמסתכל על משהו ביחד איתך")
- **Observable Behavior** - What to actually look for (e.g., "Child looks at object, then at parent, then back at object")

---

## Layer 1: Clinical Vocabulary Dictionary

```yaml
# config/clinical_vocabulary.yaml

clinical_markers:
  joint_attention:
    id: joint_attention
    clinical_term: "תשומת לב משותפת"
    parent_term: "להסתכל על דברים ביחד"
    parent_question: "כשאת מראה לו משהו מעניין, האם הוא מביט בזה ואז מסתכל עליך?"
    observable:
      - "Child looks at object"
      - "Child looks at parent's face"
      - "Child looks back at object"
      - "Cycle repeats (shared attention loop)"
    video_observable: true
    natural_situations:
      - "הראי לו משהו חדש ומעניין"
      - "קראי לו לבוא לראות משהו"
      - "צפו ביחד בסרטון או ספר"

  eye_contact:
    id: eye_contact
    clinical_term: "קשר עין"
    parent_term: "להסתכל בעיניים"
    parent_question: "האם הוא מסתכל לך בעיניים כשאת מדברת איתו?"
    observable:
      - "Child's gaze meets adult's gaze"
      - "Duration of gaze (brief/sustained)"
      - "Context (spontaneous vs. prompted)"
      - "Quality (fleeting, avoiding, comfortable)"
    video_observable: true
    natural_situations:
      - "שיחה רגילה"
      - "קריאה לילד"
      - "מתן הוראה"

  pointing_declarative:
    id: pointing_declarative
    clinical_term: "הצבעה דקלרטיבית"
    parent_term: "להצביע כדי להראות"
    parent_question: "האם הוא מצביע על דברים כדי להראות לך - לא רק כי הוא רוצה משהו?"
    observable:
      - "Child points at object of interest"
      - "Child looks at parent to share interest (not request)"
      - "Different from pointing to request (pointing imperative)"
    video_observable: true
    natural_situations:
      - "טיול בחוץ"
      - "הסתכלות על ספר"
      - "ראיית משהו מפתיע"

  social_referencing:
    id: social_referencing
    clinical_term: "התייחסות חברתית"
    parent_term: "להסתכל עליך כשלא בטוח"
    parent_question: "כשהוא לא בטוח לגבי משהו, האם הוא מסתכל עליך?"
    observable:
      - "Child encounters uncertain situation"
      - "Child looks at parent's face"
      - "Child modifies behavior based on parent's expression"
    video_observable: true
    natural_situations:
      - "מפגש עם אדם זר"
      - "צעצוע חדש"
      - "רעש לא מוכר"

  reciprocal_play:
    id: reciprocal_play
    clinical_term: "משחק הדדי"
    parent_term: "לשחק הלוך-חזור"
    parent_question: "האם הוא משחק איתך משחקים של 'תורי-תורך'?"
    observable:
      - "Turn-taking in play"
      - "Awareness of other player"
      - "Enjoyment of interaction (not just object)"
    video_observable: true
    natural_situations:
      - "משחק כדור"
      - "בניית מגדל ביחד"
      - "משחק מחבואים"

  symbolic_play:
    id: symbolic_play
    clinical_term: "משחק סמלי"
    parent_term: "משחקי דמיון"
    parent_question: "האם הוא משחק משחקי דמיון - מאכיל בובה, עושה שהדבר הזה משהו אחר?"
    observable:
      - "Object substitution (banana as phone)"
      - "Pretend actions (feeding doll)"
      - "Role play elements"
    video_observable: true
    natural_situations:
      - "משחק חופשי עם צעצועים"
      - "משחק עם בובות"
      - "משחק מטבח"

developmental_history:
  birth_history:
    id: birth_history
    clinical_term: "היסטוריית לידה"
    parent_term: "איך עברה הלידה"
    parent_question: "איך הייתה הלידה? האם היו קשיים או סיבוכים?"
    subtopics:
      - pregnancy: "האם ההריון עבר בסדר?"
      - birth_week: "באיזה שבוע נולד?"
      - complications: "האם היו סיבוכים בלידה?"
      - nicu: "האם היה צורך בפגייה?"
    video_observable: false

  milestones:
    id: milestones
    clinical_term: "אבני דרך התפתחותיות"
    parent_term: "מתי התחיל..."
    parent_question: "מתי בערך התחיל ללכת? ומתי אמר מילים ראשונות?"
    subtopics:
      - walking: "מתי התחיל ללכת?"
      - first_words: "מתי אמר מילים ראשונות?"
      - sentences: "מתי התחיל לדבר במשפטים?"
      - toilet: "מתי הפסיק לחיתולים?"
    video_observable: false

  regression:
    id: regression
    clinical_term: "נסיגה התפתחותית"
    parent_term: "דברים שהפסיק לעשות"
    parent_question: "האם יש דברים שפעם עשה וכבר לא?"
    red_flag: true
    subtopics:
      - language_loss: "האם היו מילים שהפסיק להשתמש?"
      - skill_loss: "האם יש כישורים אחרים שנעלמו?"
    video_observable: false

daily_function:
  sleep:
    id: sleep
    clinical_term: "דפוסי שינה"
    parent_term: "איך השינה"
    parent_question: "איך הוא ישן בלילה? קל לו להירדם?"
    subtopics:
      - falling_asleep: "האם קל לו להירדם?"
      - staying_asleep: "האם הוא ישן רציף?"
      - waking: "איך ההתעוררות בבוקר?"
    video_observable: false

  feeding:
    id: feeding
    clinical_term: "דפוסי אכילה"
    parent_term: "איך האוכל"
    parent_question: "איך הוא אוכל? יש קשיים עם אוכל מסוים?"
    subtopics:
      - variety: "האם הוא אוכל מגוון?"
      - textures: "יש בעיה עם מרקמים מסוימים?"
      - independence: "האם הוא אוכל לבד?"
    video_observable: true  # Mealtime video can be valuable
    natural_situations:
      - "ארוחה רגילה"
```

---

## Layer 2: Clinical Observation Scenarios

Different from hypothesis-testing scenarios. Purpose: **Baseline observation** of natural behavior.

### Scenario Types

| Type | Purpose | When to Suggest |
|------|---------|-----------------|
| `baseline_play` | See natural play patterns | Always valuable |
| `social_interaction` | Observe social markers | When social curiosity is active |
| `transition` | See regulation patterns | When regulation curiosity is active |
| `communication` | See language/communication | When language curiosity is active |
| `daily_routine` | See daily function | When sleep/feeding curiosity is active |

### Scenario Structure

```python
@dataclass
class ClinicalObservationScenario:
    """
    A scenario designed to observe clinical markers naturally.

    Different from VideoScenario which tests a hypothesis.
    This is for BASELINE observation - seeing how the child naturally behaves.
    """
    id: str
    scenario_type: str  # baseline_play, social_interaction, etc.

    # What parent sees
    title: str  # "שחק חופשי"
    parent_instruction: str  # "שחקי איתו 3-5 דקות במשחק שהוא אוהב"
    why_helpful: str  # "זה עוזר לנו לראות איך הוא כשהוא בנוח"

    # What analyst looks for (NOT shown to parent)
    clinical_markers_to_observe: List[str]  # ["joint_attention", "eye_contact", "reciprocal_play"]
    observation_guide: str  # Instructions for video analyst

    # Metadata
    duration_minutes: int  # 3-5
    domains_covered: List[str]  # ["social", "play", "communication"]
```

### Pre-Defined Clinical Scenarios

```yaml
# config/clinical_observation_scenarios.yaml

scenarios:
  - id: baseline_free_play
    type: baseline_play
    title: "משחק חופשי"
    parent_instruction: |
      שחקי איתו 3-5 דקות במשחק שהוא הכי אוהב.
      פשוט תהני איתו, בלי לנסות ללמד או להדריך.
    why_helpful: "זה עוזר לנו לראות אותו כשהוא בנוח ונהנה"
    clinical_markers:
      - joint_attention
      - eye_contact
      - reciprocal_play
      - symbolic_play
    observation_guide: |
      Look for:
      - Does child share enjoyment with parent?
      - Turn-taking patterns
      - Eye contact frequency and quality
      - Level of play complexity
    duration_minutes: 5
    domains: [social, play, emotional]

  - id: show_something_new
    type: social_interaction
    title: "להראות משהו חדש"
    parent_instruction: |
      הביאי משהו חדש ומעניין (צעצוע, ספר, חפץ).
      תגידי "בוא תראה מה יש לי!" ותסתכלי מה קורה.
    why_helpful: "זה עוזר לנו להבין איך הוא מגיב לדברים חדשים ואיך הוא משתף אותך"
    clinical_markers:
      - joint_attention
      - social_referencing
      - pointing_declarative
    observation_guide: |
      Look for:
      - Does child look at object then at parent?
      - Does child point to share (not request)?
      - Does child check parent's reaction?
    duration_minutes: 3
    domains: [social, communication]

  - id: transition_moment
    type: transition
    title: "רגע של מעבר"
    parent_instruction: |
      תצלמי רגע שבו צריך לעבור מפעילות אחת לאחרת.
      למשל: לסיים משחק ללכת לאכול, או להתלבש לצאת מהבית.
    why_helpful: "זה עוזר לנו להבין איך הוא מתמודד עם שינויים"
    clinical_markers:
      - flexibility
      - regulation
      - compliance
    observation_guide: |
      Look for:
      - Warning given before transition?
      - Child's initial reaction
      - Escalation pattern (if any)
      - What helped (or didn't)
    duration_minutes: 5
    domains: [regulation, emotional, behavioral]

  - id: call_for_attention
    type: social_interaction
    title: "לקרוא לו"
    parent_instruction: |
      כשהוא עסוק במשהו, קראי לו בשמו וראי אם הוא מגיב.
      נסי פעם אחת רגילה, ופעם אחת יותר בהתלהבות.
    why_helpful: "זה עוזר לנו להבין איך הוא מגיב לפניות אליו"
    clinical_markers:
      - response_to_name
      - joint_attention
      - eye_contact
    observation_guide: |
      Look for:
      - Response to name (first call)
      - Response latency
      - Eye contact when responding
      - Difference between normal and enthusiastic call
    duration_minutes: 2
    domains: [social, communication]

  - id: mealtime_observation
    type: daily_routine
    title: "רגע של אוכל"
    parent_instruction: |
      תצלמי כמה דקות מארוחה רגילה.
      לא צריך לעשות שום דבר מיוחד, פשוט ארוחה כרגיל.
    why_helpful: "זה עוזר לנו להבין את דפוסי האכילה וההתנהגות בשגרה"
    clinical_markers:
      - feeding_patterns
      - sensory_sensitivities
      - independence
      - communication_during_meal
    observation_guide: |
      Look for:
      - Food textures accepted/rejected
      - Utensil use
      - Sitting behavior
      - Communication during meal
    duration_minutes: 5
    domains: [feeding, sensory, motor]
```

---

## Layer 3: Curiosity → Clinical Observation Trigger

When should we suggest a clinical observation scenario?

### Trigger Conditions

```python
def should_suggest_clinical_observation(
    curiosity: Curiosity,
    understanding: Understanding,
    has_video_consent: bool,
) -> Optional[ClinicalObservationScenario]:
    """
    Determine if we should suggest a clinical observation scenario.

    Conditions:
    1. Parent has consented to video
    2. Curiosity is active (activation > 0.6) but uncertain (certainty < 0.4)
    3. Curiosity domain maps to a clinical observation type
    4. We don't already have analyzed video for this domain
    """

    if not has_video_consent:
        return None

    if curiosity.activation < 0.6 or curiosity.certainty > 0.4:
        return None

    # Domain → Scenario mapping
    domain_scenarios = {
        "social": ["baseline_free_play", "show_something_new", "call_for_attention"],
        "communication": ["show_something_new", "call_for_attention"],
        "regulation": ["transition_moment"],
        "feeding": ["mealtime_observation"],
        "play": ["baseline_free_play"],
    }

    scenarios = domain_scenarios.get(curiosity.domain, [])
    if not scenarios:
        return None

    # Return first scenario not yet done
    for scenario_id in scenarios:
        if not has_scenario_been_done(scenario_id, understanding):
            return get_scenario(scenario_id)

    return None
```

### Integration with Existing Video System

```
Current Flow:
  Hypothesis (video_appropriate=true)
    → Parent consents
    → VideoScenario generated (for hypothesis testing)
    → Video analyzed

New Flow (parallel):
  Clinical Curiosity (social, regulation, etc.)
    + Parent has already consented to video
    + High activation + Low certainty
    → ClinicalObservationScenario suggested
    → Video analyzed with clinical markers lens
```

---

## Usage in ClinicalGapDetector

The ClinicalGapDetector should use parent language for UI, clinical terms for summaries:

```python
class ClinicalGap:
    field: str                    # "joint_attention"
    priority: GapPriority

    # For parent-facing UI
    parent_question: str          # "כשאת מראה לו משהו, האם הוא מביט ואז מסתכל עליך?"

    # For professional summary
    clinical_term: str            # "תשומת לב משותפת"

    # For LLM collection
    collection_approach: str      # How to naturally gather this in conversation

    # Can video help?
    video_scenario_ids: List[str] # ["show_something_new", "baseline_free_play"]
```

---

## Summary: What Gets Shown Where

| Context | Language Used |
|---------|---------------|
| Chat conversation | Parent language ("כשהוא רואה משהו מעניין, האם הוא מביט עליך?") |
| UI gap display | Parent language ("עוד לא שמענו על איך הוא משתף אותך בדברים") |
| Video instruction to parent | Simple, behavioral ("הראי לו משהו חדש ותראי מה קורה") |
| Video analysis (internal) | Clinical precision ("joint_attention: initiating=yes, responding=partial") |
| Professional summary | Clinical terms ("תשומת לב משותפת: יוזם קשר עין אך קושי בתיאום מבטים") |
| Summary "unknown" section | Clinical terms ("לא נצפה: תשומת לב משותפת") |

---

## Implementation Priority

1. **Clinical Vocabulary YAML** - Foundation for everything
2. **ClinicalObservationScenario model** - New model for baseline observations
3. **Trigger logic in Gestalt** - When to suggest clinical observation
4. **ClinicalGapDetector with dual language** - Gap detection with both languages
5. **Video analysis enhancement** - Ensure clinical markers are extracted from baseline videos

---

---

## The Deeper Value of Video: Beyond Clinical Markers

The previous sections focused on video for **clinical marker quality assessment** - making sure we see joint attention, eye contact, etc. with professional precision.

But this is too narrow. Video's true value goes far beyond this.

### What Video Uniquely Provides

#### 1. **The Unknown Unknowns**

This is video's most powerful gift.

A parent describes: "הוא מתעצבן בגן משחקים"

In conversation, we follow their interpretation. But video might reveal:
- He gets upset *before* the other child approaches (anticipatory anxiety, not social rejection)
- His body posture shows hypervigilance throughout (sensory overwhelm, not social difficulty)
- There's a pattern in what catches his attention that the parent never noticed

**Video shows us what the parent didn't think to mention because they didn't notice it.**

This is why even a "boring" video of regular play is gold - we might see something neither we nor the parent would have thought to ask about.

#### 2. **Cross-Domain Chain Revelation**

Parent reports two separate things:
- "הוא רגיש לרעשים" (sensory)
- "הוא לא משחק עם ילדים אחרים" (social)

Video of a birthday party might reveal the CHAIN:
```
Noise triggers sensory overwhelm
  → He withdraws to recover (self-regulation attempt)
  → This looks like social avoidance
  → But when noise drops, he actually glances at other kids
  → He WANTS connection but can't access it under sensory load
```

**The chain is invisible in conversation because the parent experiences these as separate issues.**

This is the Gestalt's superpower - seeing patterns that emerge from watching, not asking.

#### 3. **Calibration of Parent Perception**

Parent says: "הוא אף פעם לא מסתכל בעיניים"
Video shows: Brief eye contact that parent misses because they're looking for sustained gaze.

Parent says: "הוא משחק יפה עם אחרים"
Video shows: Parallel play, not interactive play - parent's expectations are calibrated differently.

**Video calibrates the baseline - what "אף פעם" and "תמיד" actually mean for this family.**

This isn't about proving the parent wrong - it's about understanding their reference frame.

#### 4. **Temporal Micropatterns**

Things that happen too fast to narrate:
- How long does he look before looking away? (0.5 seconds vs 3 seconds matters)
- What's the sequence: regulate first then approach, or approach then struggle?
- Is there a "tell" 30 seconds before a meltdown? (subtle signs)
- The rhythm of interaction - who leads, who follows, tempo changes

**These are measured in fractions of seconds - outside human narrative capacity.**

Parents can't report what they can't perceive consciously.

#### 5. **The Strength-in-Disguise**

A "problem behavior" on video might reveal competence:

| Parent reports | Video might reveal |
|----------------|-------------------|
| "הוא מתנדנד כל הזמן" (stimming) | Effective self-regulation in action |
| "הוא מתעלם ממני" | Deep focus - actually a strength |
| "הוא דוחף ילדים" | Communication attempt (doesn't have words) |
| "הוא מתפרץ פתאום" | Actually there were 10 warning signs we can learn |

**Video can reframe deficit narratives into strength narratives.**

This is therapeutic for parents AND provides accurate professional data.

#### 6. **The Relational Dance (Dyadic Patterns)**

Parent-child interaction patterns that neither party is aware of:

- Parent speaks faster when anxious → child withdraws → parent speaks even faster
- Child's subtle bids for connection that get missed consistently
- Moments of beautiful attunement that happen naturally (strength evidence!)
- Co-regulation: does parent help regulate, or does parent escalate?

**Video captures the DYAD, not just the child.**

This matters because:
- Intervention recommendations often involve the parent-child relationship
- Strengths in the relationship are therapeutic resources
- Patterns repeat - seeing one helps predict others

#### 7. **Context Details We'd Never Think to Ask**

Video shows the environment:
- How stimulating is the home? (visual clutter, noise level)
- Where does the child position themselves?
- What objects do they gravitate toward?
- How is space organized?

**Environmental factors that affect behavior are visible but not narratable.**

---

### A New Taxonomy: Video's Six Gifts

| Gift | What It Reveals | Example |
|------|-----------------|---------|
| **Unknown unknowns** | What parent didn't notice | Sensory seeking behavior they see as "just playing" |
| **Chain revelation** | Cross-domain patterns | Sensory → regulatory → social cascade |
| **Calibration** | What "always/never" actually means | Brief eye contact vs. no eye contact |
| **Micropatterns** | Sub-second timing | Regulation sequence, attention duration |
| **Reframing** | Strengths hidden in concerns | Self-regulation, not "stimming" |
| **Relational** | Dyadic patterns | Attunement, bids, co-regulation |

---

### When to Ask for Video: The New Criteria

Not just "is this video-appropriate?" but "would video provide value we can't get otherwise?"

**Video is HIGH VALUE when:**

1. **We're uncertain AND curious** - We have active curiosity but low certainty
2. **Cross-domain pattern suspected** - Multiple domains might be connected
3. **Parent perception needs calibration** - "Always/never" language suggests possible gap
4. **Quality matters** - We know something happens, need to see HOW it happens
5. **Discovery mode active** - We're still forming hypotheses, not just testing them
6. **Relationship is the question** - Parent-child interaction is the curiosity focus
7. **Baseline unknown** - We've never seen this child in ANY context

**Video is LOW VALUE when:**

1. **Conversation answered it** - Parent gave detailed, consistent account
2. **Historical data** - "When did he start walking?" (video won't help)
3. **Parent reports objectively verifiable fact** - "He's in speech therapy twice a week"
4. **Already have video of this type** - Unless significant time has passed

---

### The "Baseline Video" Insight

Even without specific hypotheses, ONE video of natural play can provide:
- Unknown unknowns (we don't know what we'll see)
- Calibration of everything else parent says
- Cross-domain pattern detection opportunity
- Strength identification
- Dyadic rhythm baseline

**Consider: Early in relationship, suggest ONE baseline video regardless of specific curiosities.**

This isn't hypothesis testing - it's opening our eyes.

---

## Open Questions

1. Should clinical observation scenarios be separate from hypothesis-testing VideoScenarios, or just a special category?
2. How to handle "already done" - if parent filmed baseline_play, do we need it again?
3. Should we proactively suggest baseline observation even without specific curiosity?
4. **NEW**: How do we communicate video's value to parents without making them feel scrutinized?
5. **NEW**: Should we have different video "intentions" - hypothesis testing vs. discovery vs. calibration?
