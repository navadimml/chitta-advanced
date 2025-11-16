#!/usr/bin/env python3
"""
Test Conversation Service End-to-End

Tests the complete conversation flow with real LLM:
1. InterviewService state management
2. ConversationService orchestration
3. Function calling and extraction
4. Completeness calculation
5. Context card generation

Usage:
    python test_conversation_service.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Load environment
from dotenv import load_dotenv
load_dotenv(backend_dir / '.env')

# Setup logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

# Silence noisy loggers
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('google_genai').setLevel(logging.WARNING)

from app.services.conversation_service import get_conversation_service
from app.services.interview_service import get_interview_service


async def test_basic_conversation():
    """Test basic conversation flow"""
    print("\n" + "="*70)
    print("TEST 1: Basic Conversation Flow")
    print("="*70)

    conversation_service = get_conversation_service()
    interview_service = get_interview_service()

    family_id = "test_family_001"

    # Test messages simulating a parent's conversation
    messages = [
        "שלום, אני רוצה לדבר על הילד שלי",
        "שמו יוני והוא בן 3.5",
        "הוא מאוד אוהב לשחק ברכבות ולבנות דברים",
        "אבל הדיבור שלו ממש חלש, רק מילים בודדות",
    ]

    for i, message in enumerate(messages, 1):
        print(f"\n--- Turn {i} ---")
        print(f"User: {message}")

        result = await conversation_service.process_message(
            family_id=family_id,
            user_message=message
        )

        print(f"\nAssistant: {result['response'][:150]}...")
        print(f"Completeness: {result['completeness']:.1f}%")

        if result.get('extracted_data'):
            print(f"Extracted: {list(result['extracted_data'].keys())}")

        if result.get('function_calls'):
            print(f"Function calls: {len(result['function_calls'])}")

    # Check final state
    print("\n" + "="*70)
    print("FINAL STATE")
    print("="*70)

    stats = interview_service.get_session_stats(family_id)
    print(f"Total turns: {stats['conversation_turns']}")
    print(f"Completeness: {stats['completeness_pct']}")
    print(f"Extractions: {stats['extraction_count']}")
    print(f"Has child name: {stats['has_child_name']}")
    print(f"Has age: {stats['has_age']}")
    print(f"Concerns count: {stats['concerns_count']}")

    # Get session data
    session = interview_service.get_or_create_session(family_id)
    data = session.extracted_data

    print(f"\nExtracted Data:")
    print(f"  Child name: {data.child_name}")
    print(f"  Age: {data.age}")
    print(f"  Gender: {data.gender}")
    print(f"  Concerns: {data.primary_concerns}")
    print(f"  Strengths: {data.strengths[:100] if data.strengths else 'None'}...")

    # Verify we got data
    assert data.child_name, "❌ Failed to extract child name"
    assert data.age, "❌ Failed to extract age"
    assert data.primary_concerns, "❌ Failed to extract concerns"
    assert session.completeness > 0.20, f"❌ Completeness too low: {session.completeness}"

    print("\n✅ TEST PASSED - Basic conversation flow works!")
    return True


async def test_completeness_progression():
    """Test that completeness increases as more data is collected"""
    print("\n" + "="*70)
    print("TEST 2: Completeness Progression")
    print("="*70)

    conversation_service = get_conversation_service()
    interview_service = get_interview_service()

    family_id = "test_family_002"

    # Progressive messages covering different areas
    test_sequence = [
        ("שמה מיה והיא בת 4", "basic info"),
        ("היא מאוד אוהבת לצייר ולקרוא ספרים", "strengths"),
        ("אבל היא לא משחקת עם ילדים אחרים בגן", "concerns"),
        ("נולדה בזמן, הכל היה תקין בהריון", "developmental history"),
        ("יש לה אח גדול בן 7, שניהם הולכים לאותו גן", "family context"),
        ("הבוקר שלה קשה, לא אוהבת ללכת לגן", "daily routines"),
        ("אני רוצה שהיא תהיה יותר חברתית ובטוחה בעצמה", "parent goals"),
    ]

    completeness_progression = []

    for message, area in test_sequence:
        result = await conversation_service.process_message(
            family_id=family_id,
            user_message=message
        )

        completeness = result['completeness']
        completeness_progression.append((area, completeness))

        print(f"\n{area:20s}: {completeness:5.1f}%")

    # Verify progression
    print("\n" + "-"*70)
    print("Completeness Progression:")
    for i, (area, comp) in enumerate(completeness_progression):
        symbol = "✅" if i == 0 or comp > completeness_progression[i-1][1] else "⚠️"
        print(f"  {symbol} {area:20s}: {comp:.1f}%")

    # Check final completeness
    final = completeness_progression[-1][1]
    assert final > 60, f"❌ Final completeness too low: {final}%"
    assert final >= completeness_progression[0][1], "❌ Completeness didn't increase!"

    print(f"\n✅ TEST PASSED - Completeness progressed from {completeness_progression[0][1]:.1f}% to {final:.1f}%")
    return True


async def test_context_cards():
    """Test context card generation"""
    print("\n" + "="*70)
    print("TEST 3: Context Cards Generation")
    print("="*70)

    conversation_service = get_conversation_service()
    family_id = "test_family_003"

    # Send a message with extractable data
    result = await conversation_service.process_message(
        family_id=family_id,
        user_message="שמו יוני בן 3.5 ויש לי דאגות לגבי הדיבור שלו"
    )

    cards = result.get('context_cards', [])

    print(f"\nGenerated {len(cards)} context cards:")
    for i, card in enumerate(cards, 1):
        print(f"\n  Card {i}: {card['title']}")
        print(f"    Subtitle: {card['subtitle']}")
        print(f"    Icon: {card.get('icon', 'N/A')}")
        print(f"    Status: {card.get('status', 'N/A')}")

    # Verify expected cards
    assert len(cards) >= 1, "❌ No context cards generated"

    # Should have at least a progress card
    titles = [c['title'] for c in cards]
    assert any('שיחת' in t or 'התקדמות' in t or 'פרופיל' in t for t in titles), \
        "❌ Missing expected context cards"

    print("\n✅ TEST PASSED - Context cards generated correctly")
    return True


async def main():
    """Run all tests"""
    print("\n" + "🧪" * 35)
    print(" CONVERSATION SERVICE END-TO-END TEST SUITE")
    print("🧪" * 35)

    try:
        # Check environment
        import os
        provider = os.getenv("LLM_PROVIDER", "not set")
        model = os.getenv("LLM_MODEL", "not set")
        has_key = bool(os.getenv("GEMINI_API_KEY"))

        print(f"\nEnvironment:")
        print(f"  Provider: {provider}")
        print(f"  Model: {model}")
        print(f"  API Key: {'✅ Set' if has_key else '❌ Not set'}")

        if not has_key and provider == "gemini":
            print("\n⚠️  WARNING: GEMINI_API_KEY not set")
            print("   Tests will use simulated provider")

        # Run tests
        results = []

        results.append(await test_basic_conversation())
        results.append(await test_completeness_progression())
        results.append(await test_context_cards())

        # Summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)

        passed = sum(results)
        total = len(results)

        test_names = [
            "Basic Conversation Flow",
            "Completeness Progression",
            "Context Cards Generation"
        ]

        for name, success in zip(test_names, results):
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {status}: {name}")

        print(f"\nOverall: {passed}/{total} tests passed")

        if passed == total:
            print("\n🎉 All tests passed! Backend integration is working!")
            return 0
        else:
            print(f"\n⚠️  {total - passed} test(s) failed")
            return 1

    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
