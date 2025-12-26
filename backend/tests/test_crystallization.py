"""
Test to verify crystallization LLM call and parsing.

Run: PYTHONPATH=. pytest tests/test_crystallization.py -v -s

NOTE: Requires GEMINI_API_KEY to be set (loaded from .env)
"""

import pytest
import asyncio
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@pytest.mark.asyncio
async def test_crystallization_generates_all_fields():
    """Test that crystallization generates patterns, intervention_pathways, and portrait_sections."""

    from app.chitta.synthesis import SynthesisService
    from app.chitta.models import (
        Understanding, TemporalFact,
        Story, Evidence
    )
    from app.chitta.curiosity_types import Hypothesis
    from app.chitta.curiosity_types import Evidence as CuriosityEvidence
    from app.chitta.curiosity_manager import CuriosityManager

    # Create service
    synthesis = SynthesisService()

    # Build Understanding with observations
    understanding = Understanding(
        observations=[
            TemporalFact(content="דניאל בן 3.5", domain="identity", confidence=1.0, source="conversation"),
            TemporalFact(content="מתקשה במעברים בין פעילויות", domain="behavioral", confidence=0.9, source="conversation"),
            TemporalFact(content="רגיש לרעשים חזקים", domain="sensory", confidence=0.85, source="conversation"),
            TemporalFact(content="אוהב מוזיקה ויכול לשיר שירים שלמים", domain="strengths", confidence=0.95, source="conversation"),
            TemporalFact(content="יצירתי מאוד בציור ובנייה עם קוביות", domain="strengths", confidence=0.9, source="conversation"),
            TemporalFact(content="לא אוהב להתלכלך בחול", domain="sensory", confidence=0.85, source="conversation"),
        ]
    )

    # Build curiosities with an investigation (V2)
    curiosities = CuriosityManager()
    hypothesis = Hypothesis.create(
        focus="קושי במעברים",
        theory="יכול להיות שמעברים קשים לו כי השינוי מרגיש גדול",
        domain="behavioral",
        reasoning="Test hypothesis for crystallization",
        video_appropriate=True,
        confidence=0.6,
    )
    hypothesis.start_investigation()  # Start investigation for this hypothesis
    # Add evidence through investigation
    evidence = CuriosityEvidence.create(
        content="מתפרץ כשצריך לצאת מהבית",
        effect="supports",
        session_id="test_session",
        source_observation="test_obs",
        reasoning="Test evidence",
        confidence_before=0.6,
        confidence_after=0.7,
    )
    hypothesis.add_evidence(evidence, "Test evidence added")
    curiosities.add(hypothesis)

    # Build stories
    stories = [
        Story(
            summary="אתמול דניאל התפרץ כשצריך היה לצאת מהבית לגן. לקח 20 דקות להרגיע אותו.",
            reveals=["קושי במעברים", "קושי בוויסות רגשי"],
            domains=["behavioral", "emotional"],
            significance=0.8,
            timestamp=datetime.now()
        ),
        Story(
            summary="בגן המטפלת אמרה שדניאל לא מצטרף לחוג עם הילדים האחרים. הוא יושב בצד ומשחק לבד.",
            reveals=["קושי חברתי", "העדפה למשחק עצמאי"],
            domains=["social"],
            significance=0.75,
            timestamp=datetime.now()
        )
    ]

    print("\n" + "="*60)
    print("TRIGGERING CRYSTALLIZATION")
    print("="*60)

    # Patch to capture raw LLM response for debugging
    import logging
    logging.basicConfig(level=logging.INFO)

    # Call crystallize with individual parameters
    crystal = await synthesis.crystallize(
        child_name="דניאל",
        understanding=understanding,
        stories=stories,
        curiosities=curiosities,
        latest_observation_at=datetime.now(),
        existing_crystal=None,  # Force fresh generation
    )

    print("\n" + "="*60)
    print("CRYSTAL RESULT")
    print("="*60)

    print(f"\n📝 essence_narrative: {crystal.essence_narrative}")
    print(f"\n🎭 temperament: {crystal.temperament}")
    print(f"\n⭐ core_qualities: {crystal.core_qualities}")

    print(f"\n🔍 PATTERNS ({len(crystal.patterns)}):")
    for i, p in enumerate(crystal.patterns):
        print(f"  {i+1}. {p.description}")
        print(f"     domains: {p.domains_involved}")

    print(f"\n💡 INTERVENTION_PATHWAYS ({len(crystal.intervention_pathways)}):")
    for i, ip in enumerate(crystal.intervention_pathways):
        print(f"  {i+1}. {ip.hook} -> {ip.concern}")
        suggestion_preview = ip.suggestion[:80] if len(ip.suggestion) > 80 else ip.suggestion
        print(f"     suggestion: {suggestion_preview}...")

    print(f"\n🖼️ PORTRAIT_SECTIONS ({len(crystal.portrait_sections)}):")
    for i, ps in enumerate(crystal.portrait_sections):
        print(f"  {i+1}. {ps.icon} {ps.title}")
        print(f"     type: {ps.content_type}")
        content_preview = ps.content[:80] if len(ps.content) > 80 else ps.content
        print(f"     content: {content_preview}...")

    print(f"\n👨‍⚕️ EXPERT_RECOMMENDATIONS ({len(crystal.expert_recommendations)}):")
    for i, er in enumerate(crystal.expert_recommendations):
        print(f"  {i+1}. {er.profession} - {er.specialization}")
        print(f"     professional_summaries count: {len(er.professional_summaries)}")
        for ps in er.professional_summaries:
            print(f"       - {ps.recipient_type}:")
            who_preview = ps.who_this_child_is[:60] if len(ps.who_this_child_is) > 60 else ps.who_this_child_is
            print(f"         who: {who_preview}...")
            role_preview = ps.role_specific_section[:60] if len(ps.role_specific_section) > 60 else ps.role_specific_section
            print(f"         role_specific: {role_preview}...")

    print(f"\n❓ OPEN_QUESTIONS ({len(crystal.open_questions)}):")
    for i, q in enumerate(crystal.open_questions):
        print(f"  {i+1}. {q}")

    print("\n" + "="*60)

    # Assertions
    assert crystal.essence_narrative, "essence_narrative should not be empty"
    assert len(crystal.patterns) > 0, "patterns should not be empty"
    assert len(crystal.intervention_pathways) > 0, "intervention_pathways should not be empty"
    assert len(crystal.portrait_sections) > 0, "portrait_sections should not be empty"

    # Verify holistic-first professional summaries if expert_recommendations exist
    if len(crystal.expert_recommendations) > 0:
        er = crystal.expert_recommendations[0]
        assert len(er.professional_summaries) == 3, "expert_recommendation should have 3 professional_summaries (teacher, specialist, medical)"
        recipient_types = {ps.recipient_type for ps in er.professional_summaries}
        assert recipient_types == {"teacher", "specialist", "medical"}, f"expected all 3 recipient types, got: {recipient_types}"
        for ps in er.professional_summaries:
            assert ps.who_this_child_is, f"professional_summary for {ps.recipient_type} missing who_this_child_is"
            assert ps.role_specific_section, f"professional_summary for {ps.recipient_type} missing role_specific_section"

    print("\n✅ ALL ASSERTIONS PASSED!")


if __name__ == "__main__":
    asyncio.run(test_crystallization_generates_all_fields())
