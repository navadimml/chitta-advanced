"""
Sharing Service - Professional summary generation

Generates shareable summaries for professionals using structured LLM output.
This service is independent of ChittaService - it receives Darshan state
and a persist callback.

Features:
- Structured output for consistent professional summaries
- Recipient-type detection (teacher, medical, therapist)
- Temporal insight extraction
- Backwards-compatible text format generation
"""

from datetime import datetime, date
from typing import Dict, Any, List, Optional, Callable, Awaitable
import logging

from .gestalt import Darshan


def _format_age_hebrew(birth_date: Optional[date], gender: Optional[str] = None) -> Optional[str]:
    """Format child's age in Hebrew from birth date."""
    if not birth_date:
        return None

    today = date.today()
    years = today.year - birth_date.year
    months = today.month - birth_date.month

    # Adjust for birthday not yet reached this year
    if today.day < birth_date.day:
        months -= 1
    if months < 0:
        years -= 1
        months += 12

    # Gender-aware prefix
    if gender == "female":
        prefix = "בת"
    elif gender == "male":
        prefix = "בן"
    else:
        prefix = "בן/בת"

    if years == 0:
        return f"{prefix} {months} חודשים"
    elif months == 0:
        if years == 1:
            return f"{prefix} שנה"
        return f"{prefix} {years} שנים"
    else:
        if years == 1:
            return f"{prefix} שנה ו-{months} חודשים"
        return f"{prefix} {years} שנים ו-{months} חודשים"

logger = logging.getLogger(__name__)


class SharingService:
    """Generates shareable professional summaries."""

    async def generate_shareable_summary(
        self,
        darshan: Darshan,
        persist_callback: Callable[[Darshan], Awaitable[None]],
        expert: Optional[Dict[str, Any]] = None,
        expert_description: Optional[str] = None,
        crystal_insights: Optional[Dict[str, Any]] = None,
        additional_context: Optional[str] = None,
        comprehensive: bool = False,
        missing_gaps: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a shareable summary using STRUCTURED OUTPUT.

        Args:
            darshan: The Darshan state containing child understanding
            persist_callback: Async function to persist state after summary creation
            expert: Expert/professional info dict
            expert_description: Parent's description of the expert
            crystal_insights: Pre-generated insights from Crystal
            additional_context: Additional context from parent
            comprehensive: Whether to generate comprehensive summary
            missing_gaps: Known information gaps

        Returns structured JSON that the frontend renders professionally.
        This gives us full control over presentation and ensures consistency.
        """
        from .summary_schema import ProfessionalSummary, get_summary_schema

        child_name = darshan.child_name or "הילד/ה"
        now = datetime.now()

        # Build the expert description from various sources
        expert_info = self._build_expert_description(expert, expert_description)

        # Collect all relevant child information
        child_summary = self._build_child_summary_for_sharing(darshan)

        # Build crystal insights section if available
        crystal_context = ""
        if crystal_insights:
            crystal_context = f"""
Crystal Insights (what we already identified as relevant for this professional):
- Why this professional is a match: {crystal_insights.get('why_this_match', 'not specified')}
- Recommended approach: {crystal_insights.get('recommended_approach', 'not specified')}
- Professional summary: {crystal_insights.get('summary_for_professional', 'not specified')}
"""

        # Get expert name
        expert_name = "מומחה"
        if expert:
            expert_name = expert.get("profession") or expert.get("customDescription") or "מומחה"

        # Build missing data list for the schema
        missing_data_items = []
        if missing_gaps:
            for gap in missing_gaps:
                clinical_term = gap.get("clinical_term") or gap.get("parent_description") or gap.get("description", "")
                if clinical_term:
                    missing_data_items.append(clinical_term)

        # Detect recipient type for tailored language
        expert_name_lower = expert_name.lower()
        is_teacher = any(term in expert_name_lower for term in ['גננת', 'גן', 'מורה', 'חינוך', 'סייעת', 'צהרון'])
        is_medical = any(term in expert_name_lower for term in ['רופא', 'נוירולוג', 'רפואי', 'פסיכיאטר'])

        # Build recipient-specific guidance
        recipient_guidance = self._get_recipient_guidance(is_teacher, is_medical)

        # Build the structured output prompt
        prompt = f"""# Task: Generate a STRUCTURED Professional Summary

You are Chitta - a child understanding system. Generate a professional summary.

## PHILOSOPHY
- Prepare the ground, don't deliver findings
- Open doors for investigation, don't close them with conclusions
- Frame patterns as hypotheses, not facts
- Write like a PERSON, not a system
{recipient_guidance}

## About the Professional
{expert_info}
{crystal_context}

## What We Know About the Child
Name: {child_name}
Age: {_format_age_hebrew(darshan.child_birth_date, darshan.child_gender) or 'לא צוין'}

{child_summary}

{f"Additional context from parent: " + additional_context if additional_context else ""}

## Missing Information We Don't Have Yet
{', '.join(missing_data_items) if missing_data_items else 'None identified'}

## Instructions for Each Field

**essence_paragraph**: 2-3 WARM sentences about who this child IS - their personality, what lights them up, what makes them unique. NOT their problems. Write like you're describing a child you care about.

**strengths**: Strengths that can serve as BRIDGES. Format: strength + how it can be used.

**parent_observations**: What parents TOLD us - their words, their perspective. Keep factual.

**scenes**: 1-2 CONCRETE examples relevant to THIS recipient. What happens, what helps.

**patterns**: What WE noticed - frame TENTATIVELY: "נראה ש...", "יכול להיות ש..."

**practical_tips**: CRITICAL - Concrete actionable tips connecting what works to specific challenges.
Each tip has: what_works (the hook), challenge (what it addresses), suggestion (what to try).
For teachers: classroom-applicable, everyday language.
For therapists: can include professional approaches.

**developmental_notes**: Timeline info - ONLY if relevant for this recipient.

**open_questions**: Questions for THIS professional to investigate. Frame as invitations.

**missing_info**: Be honest about gaps.

**closing_note**: Brief warm closing - invitation to share back, thanks.

## Language
- Write ALL content in Hebrew
- Match the language level to the recipient (see guidance above)
- Date format: {now.strftime("%d/%m/%Y")}

Generate the structured summary now:
"""

        try:
            from app.services.llm.base import Message as LLMMessage
            from .models import SharedSummary

            llm = darshan._get_strong_llm()

            # Use structured output
            response_data = await llm.chat_with_structured_output(
                messages=[LLMMessage(role="user", content=prompt)],
                response_schema=get_summary_schema(),
                temperature=0.8,
            )

            # Validate with Pydantic
            summary_obj = ProfessionalSummary.model_validate(response_data)

            # Convert to dict for JSON response
            structured_summary = summary_obj.model_dump()

            # Ensure metadata is correct
            structured_summary["child_first_name"] = child_name
            structured_summary["summary_date"] = now.strftime("%d/%m/%Y")
            structured_summary["recipient_type"] = expert_name
            structured_summary["recipient_title"] = expert_name

            # Create legacy content for backwards compatibility (plain text version)
            legacy_content = self._structured_summary_to_text(structured_summary)

            # Determine recipient type for storage
            recipient_type_str = "professional"
            if expert and expert.get("customDescription"):
                recipient_type_str = "custom"

            # Create and save the summary (store structured data as JSON string)
            import json
            shared_summary = SharedSummary.create(
                recipient_description=expert_name,
                content=json.dumps(structured_summary, ensure_ascii=False),
                recipient_type=recipient_type_str,
                comprehensive=comprehensive,
            )

            # Add to darshan and persist
            darshan.shared_summaries.append(shared_summary)

            # Clear guided collection mode - summary is complete!
            # This allows the chat to return to normal conversation mode
            if darshan.session_flags.get("preparing_summary_for"):
                logger.info(f"Clearing guided collection mode after summary generation for {darshan.child_id}")
                darshan.session_flags.pop("preparing_summary_for", None)
                darshan.session_flags.pop("guided_collection_gaps", None)

            await persist_callback(darshan)

            logger.info(f"Saved structured summary for {darshan.child_id} to {expert_name}")

            return {
                "structured": structured_summary,  # New structured format
                "content": legacy_content,  # Legacy text format for backwards compatibility
                "expert": expert_name,
                "generated_at": now.isoformat(),
                "summary_id": shared_summary.id,
                "saved_summary": {
                    "id": shared_summary.id,
                    "recipient": shared_summary.recipient_description,
                    "created_at": shared_summary.created_at.isoformat(),
                    "comprehensive": shared_summary.comprehensive,
                    "preview": (legacy_content[:100] + "...") if len(legacy_content) > 100 else legacy_content,
                },
            }

        except Exception as e:
            logger.error(f"Error generating structured summary: {e}")
            import traceback
            traceback.print_exc()

            # Clear guided collection mode even on error - user explicitly triggered summary
            # They can restart guided collection by clicking "Add in chat" again
            if darshan.session_flags.get("preparing_summary_for"):
                logger.info(f"Clearing guided collection mode after failed summary for {darshan.child_id}")
                darshan.session_flags.pop("preparing_summary_for", None)
                darshan.session_flags.pop("guided_collection_gaps", None)
                # Persist the flag clearing
                try:
                    await persist_callback(darshan)
                except Exception as persist_err:
                    logger.warning(f"Could not persist flag clearing: {persist_err}")

            return {
                "error": str(e),
                "content": f"לצערנו לא הצלחנו ליצור סיכום. נסו שוב מאוחר יותר.",
            }

    def _get_recipient_guidance(self, is_teacher: bool, is_medical: bool) -> str:
        """Get recipient-specific language and tone guidance."""
        if is_teacher:
            return """
## RECIPIENT TYPE: EDUCATOR (גננת/מורה)

**LANGUAGE**: Everyday Hebrew - like talking to a friend, NOT clinical terms.
- "ויסות רגשי" -> "איך הוא מרגיע את עצמו"
- "עיבוד חושי" -> "איך הוא מגיב לרעשים / מגע"
- "אבני דרך התפתחותיות" -> "מתי התחיל ללכת/לדבר"
- "רגישות טקטילית" -> "לא אוהב לגעת בדברים מסוימים"

**TONE**: Warm, collaborative - like a friend sharing insights about a child you both care about.
NOT a clinical report. You're helping the teacher KNOW this child better.

**RELEVANCE FILTER**: Skip birth details, medical history, vacuum delivery etc.
Teachers need what happens NOW in daily life, not medical history.

**PRACTICAL_TIPS**: CRITICAL for teachers! 2-4 concrete, actionable tips they can try TODAY.
Connect what works to specific challenges:
- "הוא מגיב טוב למוזיקה" -> "כשקשה לו להיפרד בבוקר, שיר מוכר יכול לעזור"
- "הוא אוהב לעזור" -> "לתת לו תפקיד בכיתה יכול לגרום לו להרגיש שייך"

**developmental_notes**: Only include if directly relevant to classroom behavior."""
        elif is_medical:
            return """
## RECIPIENT TYPE: MEDICAL PROFESSIONAL

**LANGUAGE**: Clinical precision expected. Can use professional terms.
- "developmental milestones", "sensory processing", "self-regulation"
- Timeline with specific ages
- Observable patterns

**TONE**: Professional, concise, factual.

**RELEVANCE**: Medical history IS relevant - birth, early development, milestones.

**PRACTICAL_TIPS**: Can be more clinical - what interventions have worked,
what the child responds to therapeutically."""
        else:
            return """
## RECIPIENT TYPE: SPECIALIST/THERAPIST

**LANGUAGE**: Can use professional terms they understand (ויסות חושי, רגישות אודיטורית)
but balance with everyday descriptions.

**TONE**: Professional but warm. Collaborative - we're preparing the ground together.

**PRACTICAL_TIPS**: 2-3 tips connecting strengths to therapeutic approaches.
What does this child respond to? How can they use that in treatment?"""

    def _structured_summary_to_text(self, summary: Dict[str, Any]) -> str:
        """Convert structured summary to plain text for legacy compatibility."""
        lines = []

        lines.append(f"[סיכום זה נוצר ב-{summary.get('summary_date', '')}]")
        lines.append("")

        if summary.get("essence_paragraph"):
            lines.append(summary["essence_paragraph"])
            lines.append("")

        if summary.get("strengths"):
            lines.append("חוזקות:")
            for s in summary["strengths"]:
                lines.append(f"- {s.get('strength', '')}: {s.get('how_to_use', '')}")
            lines.append("")

        if summary.get("parent_observations"):
            lines.append("מה ההורים סיפרו:")
            for obs in summary["parent_observations"]:
                lines.append(f"- {obs.get('text', '')}")
            lines.append("")

        if summary.get("scenes"):
            lines.append("דוגמאות קונקרטיות:")
            for scene in summary["scenes"]:
                lines.append(f"- {scene.get('title', '')}: {scene.get('description', '')}")
                if scene.get("what_helps"):
                    lines.append(f"  מה עוזר: {scene['what_helps']}")
            lines.append("")

        if summary.get("patterns"):
            lines.append("מה שמנו לב:")
            for p in summary["patterns"]:
                lines.append(f"- {p.get('observation', '')}")
            lines.append("")

        if summary.get("practical_tips"):
            lines.append("טיפים מעשיים:")
            for tip in summary["practical_tips"]:
                what_works = tip.get('what_works', '')
                challenge = tip.get('challenge', '')
                suggestion = tip.get('suggestion', '')
                if what_works and suggestion:
                    lines.append(f"- {what_works} -> {suggestion}")
                    if challenge:
                        lines.append(f"  (עוזר עם: {challenge})")
            lines.append("")

        if summary.get("developmental_notes"):
            lines.append("ציר זמן התפתחותי:")
            for note in summary["developmental_notes"]:
                lines.append(f"- {note.get('timing', '')}: {note.get('event', '')}")
            lines.append("")

        if summary.get("open_questions"):
            lines.append("שאלות פתוחות:")
            for q in summary["open_questions"]:
                lines.append(f"- {q.get('question', '')}")
            lines.append("")

        if summary.get("missing_info"):
            lines.append("מידע שעדיין לא נאסף:")
            for m in summary["missing_info"]:
                lines.append(f"- {m.get('item', '')}")
            lines.append("")

        if summary.get("closing_note"):
            lines.append(summary["closing_note"])

        return "\n".join(lines)

    def _build_expert_description(
        self,
        expert: Optional[Dict[str, Any]],
        expert_description: Optional[str],
    ) -> str:
        """Build a rich description of the expert for the prompt."""
        parts = []

        if expert:
            # Handle crystal recommendation format
            if "profession" in expert:
                parts.append(f"**מקצוע:** {expert['profession']}")
            if "specialty" in expert:
                parts.append(f"**התמחות:** {expert['specialty']}")
            if "customDescription" in expert:
                parts.append(f"**תיאור:** {expert['customDescription']}")

        if expert_description:
            parts.append(f"**הסבר מההורה למה המומחה הזה:** {expert_description}")

        if not parts:
            return "**מומחה:** לא צוין מומחה ספציפי. כתוב סיכום כללי שיתאים לאיש מקצוע בתחום ההתפתחות."

        return "\n".join(parts)

    def _build_child_summary_for_sharing(self, darshan: Darshan) -> str:
        """Build a comprehensive child summary for sharing prompt."""
        sections = []

        # Debug: log available milestones
        logger.info(f"Building summary - milestones count: {len(darshan.understanding.milestones)}")
        for m in darshan.understanding.milestones:
            logger.info(f"  Milestone: {m.description} (domain={m.domain}, type={m.milestone_type})")

        # Essence narrative
        if darshan.understanding.essence and darshan.understanding.essence.narrative:
            sections.append(f"**מי הוא (תמצית):**\n{darshan.understanding.essence.narrative}")

        # === BIRTH HISTORY (from milestones) ===
        birth_milestones = []
        if darshan.understanding.milestones:
            birth_milestones = [
                m for m in darshan.understanding.milestones
                if getattr(m, 'milestone_type', None) == 'birth'
                or getattr(m, 'domain', None) in ('birth_history', 'medical')
            ]
        # Also check observations for birth_history domain
        birth_observations = [
            f for f in darshan.understanding.observations
            if f.domain in ('birth_history', 'medical')
        ]
        if birth_milestones or birth_observations:
            birth_items = []
            for m in birth_milestones:
                birth_items.append(f"- {m.description}")
            for f in birth_observations:
                birth_items.append(f"- {f.content}")
            sections.append(f"**היסטוריית לידה:**\n" + "\n".join(birth_items))

        # === DEVELOPMENTAL MILESTONES (from milestones) ===
        dev_milestones = []
        if darshan.understanding.milestones:
            dev_milestones = [
                m for m in darshan.understanding.milestones
                if getattr(m, 'milestone_type', None) != 'birth'
                and getattr(m, 'domain', None) not in ('birth_history', 'medical')
            ]
        if dev_milestones:
            milestone_items = []
            for m in dev_milestones:
                age_text = ""
                if m.age_months:
                    if m.age_months >= 12:
                        years = m.age_months // 12
                        months = m.age_months % 12
                        if months:
                            age_text = f" (בגיל {years} שנים ו-{months} חודשים)"
                        else:
                            age_text = f" (בגיל {years} שנים)" if years > 1 else " (בגיל שנה)"
                    else:
                        age_text = f" (בגיל {m.age_months} חודשים)"
                elif m.age_description:
                    age_text = f" ({m.age_description})"
                milestone_items.append(f"- {m.description}{age_text}")
            sections.append(f"**אבני דרך התפתחותיות:**\n" + "\n".join(milestone_items))

        # Strengths and interests
        strengths = []
        interests = []
        for fact in darshan.understanding.observations:
            if fact.domain == "strengths":
                strengths.append(fact.content)
            elif fact.domain == "interests":
                interests.append(fact.content)

        if strengths or interests:
            s = "**חוזקות ותחומי עניין:**\n"
            if strengths:
                s += f"חוזקות: {', '.join(strengths)}\n"
            if interests:
                s += f"מה מדליק אותו: {', '.join(interests)}"
            sections.append(s)

        # Patterns
        if darshan.understanding.patterns:
            patterns_text = []
            for pattern in darshan.understanding.patterns:
                domains = ", ".join(pattern.domains_involved) if pattern.domains_involved else ""
                patterns_text.append(f"- {pattern.description} (מתחברים: {domains})")
            sections.append(f"**דפוסים שזיהינו:**\n" + "\n".join(patterns_text))

        # Active investigations/concerns with temporal context
        concerns = []
        for curiosity in darshan._curiosities.get_investigating():
            theory_text = f": {curiosity.theory}" if curiosity.theory else ""
            confidence_text = ""
            if curiosity.certainty is not None:
                if curiosity.certainty > 0.7:
                    confidence_text = " (ביטחון גבוה)"
                elif curiosity.certainty < 0.4:
                    confidence_text = " (עדיין בבדיקה)"
            concerns.append(f"- {curiosity.focus}{theory_text}{confidence_text}")
        if concerns:
            sections.append(f"**תחומים שאנחנו חוקרים:**\n" + "\n".join(concerns))

        # Temporal/developmental information from explorations
        temporal_insights = self._extract_temporal_insights(darshan)
        if temporal_insights:
            sections.append(f"**התפתחות לאורך זמן:**\n{temporal_insights}")

        # Core facts (limited) - exclude birth_history/medical since already included above
        other_facts = [f.content for f in darshan.understanding.observations[:8]
                       if f.domain not in ("strengths", "interests", "birth_history", "medical")]
        if other_facts:
            sections.append(f"**עובדות נוספות:**\n" + "\n".join([f"- {f}" for f in other_facts]))

        return "\n\n".join(sections) if sections else "אין מספיק מידע עדיין"

    def _extract_temporal_insights(self, gestalt: Darshan) -> str:
        """
        Extract temporal/developmental insights from facts and explorations.

        This is critical for professionals who need to understand:
        - How long has this been going on?
        - Is it improving, stable, or worsening?
        - What interventions have been tried and their effects?
        - Trajectory of our understanding over time
        """
        insights = []

        # === FACT TIMESTAMP ANALYSIS ===
        facts = gestalt.understanding.observations
        if facts:
            # Get facts with timestamps
            dated_facts = [(f, f.t_created) for f in facts if f.t_created]

            if dated_facts:
                # Sort by creation date
                dated_facts.sort(key=lambda x: x[1])

                # Calculate span of knowledge
                earliest = dated_facts[0][1]
                latest = dated_facts[-1][1]
                span_days = (latest - earliest).days

                if span_days > 0:
                    if span_days >= 30:
                        months = span_days // 30
                        insights.append(f"- מכירים את הילד כ-{months} חודשים")
                    elif span_days >= 7:
                        weeks = span_days // 7
                        insights.append(f"- מכירים את הילד כ-{weeks} שבועות")

                # Look for domain-based temporal patterns
                domain_timeline = {}
                for fact, timestamp in dated_facts:
                    domain = fact.domain or "general"
                    if domain not in domain_timeline:
                        domain_timeline[domain] = []
                    domain_timeline[domain].append((fact.content, timestamp))

                # Analyze trajectory per domain (if multiple facts over time)
                for domain, domain_facts in domain_timeline.items():
                    if len(domain_facts) >= 2 and domain not in ("identity", "general"):
                        first_time = domain_facts[0][1]
                        last_time = domain_facts[-1][1]
                        days_diff = (last_time - first_time).days
                        if days_diff > 7:  # More than a week between observations
                            insights.append(f"- {domain}: עוקבים כבר {days_diff} ימים")

                # Recent vs early learnings (what we learned about recently)
                if span_days >= 14 and len(dated_facts) >= 5:
                    midpoint = earliest + (latest - earliest) / 2
                    early_facts = [f for f, t in dated_facts if t < midpoint]
                    recent_facts = [f for f, t in dated_facts if t >= midpoint]

                    # Check if new domains emerged recently
                    early_domains = set(f.domain for f in early_facts if f.domain)
                    recent_domains = set(f.domain for f in recent_facts if f.domain)
                    new_domains = recent_domains - early_domains
                    if new_domains:
                        insights.append(f"- לאחרונה התחלנו לבחון גם: {', '.join(new_domains)}")

        # === INVESTIGATION ANALYSIS ===
        for curiosity in gestalt._curiosities._dynamic:
            if not curiosity.investigation:
                continue
            inv = curiosity.investigation

            # Check for evidence with temporal information
            if not inv.evidence:
                continue

            supports = []
            contradicts = []
            for ev in inv.evidence:
                if ev.effect == "supports":
                    supports.append(ev.content)
                elif ev.effect == "contradicts":
                    contradicts.append(ev.content)

            # If we have both supporting and contradicting evidence, that's interesting
            if supports and contradicts:
                insights.append(f"- לגבי {curiosity.focus}: יש סימנים מעורבים - {supports[0]}, אבל גם {contradicts[0]}")
            elif len(supports) > 2:
                # Multiple supporting evidence suggests consistent pattern
                insights.append(f"- {curiosity.focus}: דפוס עקבי שנראה במספר הקשרים")

            # Check investigation age for timeline context
            if inv.started_at:
                inv_age_days = (datetime.now() - inv.started_at).days
                if inv_age_days > 14 and curiosity.status == "investigating":
                    insights.append(f"- {curiosity.focus}: בבדיקה כבר {inv_age_days} ימים")

            # Check status for developmental trajectory
            if curiosity.status == "understood" and curiosity.certainty and curiosity.certainty > 0.7:
                insights.append(f"- {curiosity.focus}: הבנה מגובשת לאחר תקופת מעקב")

        # Check for understood curiosities that might indicate progress
        understood = [c for c in gestalt._curiosities._dynamic if c.status == "understood"]
        if understood:
            insights.append(f"- סיימנו לבחון {len(understood)} תחומים והגענו למסקנות")

        # === STORY TIMESTAMP ANALYSIS ===
        if gestalt.stories:
            dated_stories = [(s, s.timestamp) for s in gestalt.stories if s.timestamp]
            if len(dated_stories) >= 2:
                dated_stories.sort(key=lambda x: x[1])
                story_span_days = (dated_stories[-1][1] - dated_stories[0][1]).days
                if story_span_days > 7:
                    insights.append(f"- יש לנו {len(dated_stories)} סיפורים לאורך {story_span_days} ימים")

        return "\n".join(insights) if insights else ""


# Singleton accessor
_sharing_service: Optional[SharingService] = None


def get_sharing_service() -> SharingService:
    """Get the singleton SharingService instance."""
    global _sharing_service
    if _sharing_service is None:
        _sharing_service = SharingService()
    return _sharing_service
