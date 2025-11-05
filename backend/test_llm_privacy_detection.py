#!/usr/bin/env python3
"""
Test LLM-based privacy question detection

This demonstrates the superiority of LLM semantic understanding over
rigid pattern matching for detecting privacy/security questions.
"""

import sys
import os
import asyncio

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.knowledge_service import get_knowledge_service
from app.services.llm.factory import create_llm_provider
from app.prompts.intent_types import IntentCategory, InformationRequestType

async def test_llm_privacy_detection():
    """Test that LLM correctly identifies privacy/security questions"""
    print("=" * 80)
    print("LLM-BASED PRIVACY DETECTION TEST")
    print("=" * 80)
    print()

    knowledge_service = get_knowledge_service()
    llm_provider = create_llm_provider()

    # Test cases that previously failed with fuzzy matching
    test_cases = [
        ("מה לגבי הסירטונים, איפה הם נישמרים?", "Video storage with typo"),
        ("איפה הסרטונים שומרים?", "Video storage"),
        ("מי רואה את המידע שלי?", "Who sees data"),
        ("כמה זה מאובטח?", "Security level"),
        ("מה לגבי פרטיות?", "General privacy"),
        ("איך אתם שומרים את הנתונים?", "Data storage"),
        ("האם המידע שלי בטוח?", "Data safety"),
        ("מי יכול לגשת לסרטונים?", "Video access"),
    ]

    context = {
        "child_name": "נועם",
        "completeness": 0.4,
        "video_count": 0,
        "reports_available": False
    }

    print(f"Testing {len(test_cases)} privacy-related questions")
    print(f"LLM Provider: {llm_provider.get_provider_name()}\n")
    print("-" * 80)

    passed = 0
    failed = 0

    for i, (test_message, description) in enumerate(test_cases, 1):
        print(f"\nTest {i}/{len(test_cases)}: {description}")
        print(f"Question: {test_message}")

        try:
            # Use LLM to detect intent
            detected_intent = await knowledge_service.detect_intent_llm(
                user_message=test_message,
                llm_provider=llm_provider,
                context=context
            )

            # Check if it was classified correctly
            is_correct = (
                detected_intent.category == IntentCategory.INFORMATION_REQUEST and
                detected_intent.information_type == InformationRequestType.PRIVACY_SECURITY
            )

            status = "✓ PASS" if is_correct else "✗ FAIL"
            print(f"{status}")
            print(f"  Category: {detected_intent.category.value}")
            if detected_intent.information_type:
                print(f"  Type: {detected_intent.information_type.value}")
            print(f"  Confidence: {detected_intent.confidence:.2f}")
            print(f"  Reasoning: {detected_intent.context.get('reasoning', 'N/A')}")

            if is_correct:
                passed += 1
            else:
                failed += 1

        except Exception as e:
            print(f"✗ ERROR: {e}")
            failed += 1

        print("-" * 80)

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total tests: {len(test_cases)}")
    print(f"Passed: {passed} ({passed/len(test_cases)*100:.1f}%)")
    print(f"Failed: {failed} ({failed/len(test_cases)*100:.1f}%)")
    print()

    if passed == len(test_cases):
        print("🎉 ALL TESTS PASSED!")
        print("LLM semantic understanding successfully detects privacy questions")
    elif passed > 0:
        print(f"⚠️  Partial success: {passed}/{len(test_cases)} tests passed")
    else:
        print("❌ ALL TESTS FAILED")

    print("=" * 80)

    return passed == len(test_cases)


async def test_knowledge_injection():
    """Test that privacy knowledge is properly injected into prompt"""
    print("\n" + "=" * 80)
    print("PRIVACY KNOWLEDGE INJECTION TEST")
    print("=" * 80)
    print()

    knowledge_service = get_knowledge_service()

    context = {
        "child_name": "נועם",
        "completeness": 0.4,
        "video_count": 0,
        "reports_available": False
    }

    # Get privacy knowledge for prompt injection
    privacy_knowledge = knowledge_service.get_knowledge_for_prompt(
        information_type=InformationRequestType.PRIVACY_SECURITY,
        context=context
    )

    print("Privacy knowledge to be injected into LLM prompt:")
    print("-" * 80)
    print(privacy_knowledge[:500])
    print(f"... (total {len(privacy_knowledge)} chars)")
    print("-" * 80)

    # Check that it contains key privacy facts
    checks = [
        ("encryption" in privacy_knowledge.lower() or "aes-256" in privacy_knowledge.lower(), "Mentions encryption"),
        ("gdpr" in privacy_knowledge.lower(), "Mentions GDPR compliance"),
        ("access" in privacy_knowledge.lower() or "רואה" in privacy_knowledge.lower(), "Mentions access control"),
        ("storage" in privacy_knowledge.lower() or "שרת" in privacy_knowledge.lower(), "Mentions storage"),
    ]

    passed = sum(1 for check, _ in checks if check)
    print(f"\nKey facts check: {passed}/{len(checks)} present")
    for check, description in checks:
        status = "✓" if check else "✗"
        print(f"  {status} {description}")

    print("\n" + "=" * 80)

    return passed >= 3  # At least 3 out of 4 checks should pass


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("LLM-BASED PRIVACY DETECTION - COMPREHENSIVE TEST")
    print("=" * 80 + "\n")

    print("This test demonstrates the superiority of LLM semantic understanding")
    print("over brittle pattern matching for privacy question detection.")
    print()

    try:
        # Run tests
        test1_passed = asyncio.run(test_llm_privacy_detection())
        test2_passed = asyncio.run(test_knowledge_injection())

        print("\n" + "=" * 80)
        print("FINAL RESULTS")
        print("=" * 80)
        print(f"LLM Privacy Detection: {'✓ PASS' if test1_passed else '✗ FAIL'}")
        print(f"Knowledge Injection: {'✓ PASS' if test2_passed else '✗ FAIL'}")

        if test1_passed and test2_passed:
            print("\n🎉 ALL TESTS PASSED - LLM-based system is working correctly!")
            sys.exit(0)
        else:
            print("\n⚠️ Some tests failed")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
