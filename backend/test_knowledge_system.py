#!/usr/bin/env python3
"""
Test script for the new knowledge architecture

Demonstrates how the system handles information requests about the app.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.knowledge_service import get_knowledge_service
from app.prompts.intent_types import InformationRequestType

def test_information_detection():
    """Test detection of information requests"""
    service = get_knowledge_service()

    test_messages = [
        ("מה עוד אני יכול לעשות פה באפליקציה הזאת?", InformationRequestType.APP_FEATURES),
        ("what can i do here?", InformationRequestType.APP_FEATURES),
        ("איך זה עובד?", InformationRequestType.PROCESS_EXPLANATION),
        ("כמה זמן לוקח התהליך?", InformationRequestType.PROCESS_EXPLANATION),
        ("איפה אני בתהליך?", InformationRequestType.CURRENT_STATE),
        ("יוני אוהב לקרוא", None),  # Regular conversation
    ]

    print("=" * 80)
    print("Testing Information Request Detection")
    print("=" * 80)

    for message, expected in test_messages:
        detected = service.detect_information_request(message)
        match = "✓" if detected == expected else "✗"
        print(f"\n{match} Message: {message}")
        print(f"  Expected: {expected}")
        print(f"  Detected: {detected}")


def test_knowledge_injection():
    """Test knowledge injection for prompts"""
    service = get_knowledge_service()

    context = {
        "child_name": "יוני",
        "completeness": 0.45,
        "video_count": 0,
        "reports_available": False
    }

    print("\n" + "=" * 80)
    print("Testing Knowledge Injection for Prompts")
    print("=" * 80)

    # Test APP_FEATURES
    print("\n1. APP_FEATURES Request:")
    print("-" * 80)
    knowledge = service.get_knowledge_for_prompt(
        InformationRequestType.APP_FEATURES,
        context
    )
    print(knowledge)

    # Test PROCESS_EXPLANATION
    print("\n2. PROCESS_EXPLANATION Request:")
    print("-" * 80)
    knowledge = service.get_knowledge_for_prompt(
        InformationRequestType.PROCESS_EXPLANATION,
        context
    )
    print(knowledge[:500] + "...")  # First 500 chars

    # Test CURRENT_STATE
    print("\n3. CURRENT_STATE Request (Interview 45% complete):")
    print("-" * 80)
    knowledge = service.get_knowledge_for_prompt(
        InformationRequestType.CURRENT_STATE,
        context
    )
    print(knowledge)


def test_faq_matching():
    """Test FAQ question matching"""
    service = get_knowledge_service()

    context = {
        "child_name": "שלומי",
        "completeness": 0.30
    }

    print("\n" + "=" * 80)
    print("Testing Direct FAQ Answers")
    print("=" * 80)

    test_questions = [
        "מה אני יכול לעשות פה?",
        "איך זה עובד?",
        "כמה זמן זה לוקח?",
    ]

    for question in test_questions:
        answer = service.get_direct_answer(question, context)
        print(f"\nQ: {question}")
        print(f"A: {answer[:200] if answer else 'No match'}...")


if __name__ == "__main__":
    print("\n🧪 Testing Knowledge Architecture\n")

    test_information_detection()
    test_knowledge_injection()
    test_faq_matching()

    print("\n" + "=" * 80)
    print("✅ All tests completed!")
    print("=" * 80)
    print("\nThis demonstrates the GENERAL → SPECIFIC architecture:")
    print("  1. Intent detection (GENERAL): Works for any domain")
    print("  2. Knowledge service (GENERAL mechanism): Reusable structure")
    print("  3. Domain knowledge (SPECIFIC content): Swap for different domains")
    print()
