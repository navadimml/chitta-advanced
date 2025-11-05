#!/usr/bin/env python3
"""
Test script to verify the privacy FAQ improvements

Tests:
1. Fuzzy pattern matching for video storage questions
2. Context-aware privacy responses
3. Different question variations
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.prompts import domain_knowledge
from app.services.knowledge_service import get_knowledge_service

def test_pattern_matching():
    """Test that the improved pattern matching works"""
    print("=" * 80)
    print("TEST 1: Pattern Matching")
    print("=" * 80)

    test_cases = [
        "מה לגבי הסירטונים, איפה הם נישמרים?",  # Original failing case
        "איפה הסרטונים שומרים?",
        "איפה הוידאו נשמר?",
        "מה עם פרטיות הסרטונים?",
        "לפני שאנחנו ממשיכים, מה לגבי פרטיות?",
        "איך אתם שומרים את המידע?",
        "מי רואה את הסרטונים?",
    ]

    for i, test_message in enumerate(test_cases, 1):
        faq_key = domain_knowledge.match_faq_question(test_message)
        status = "✓" if faq_key == "data_privacy_comprehensive" else "✗"
        print(f"{status} Test {i}: {test_message}")
        print(f"   Matched: {faq_key}")
        print()

    print()

def test_contextual_responses():
    """Test that contextual responses adapt to the question"""
    print("=" * 80)
    print("TEST 2: Context-Aware Responses")
    print("=" * 80)

    knowledge_service = get_knowledge_service()

    test_cases = [
        ("מה לגבי הסירטונים, איפה הם נישמרים?", "Video storage question"),
        ("מי רואה את המידע שלי?", "Who sees question"),
        ("כמה זה מאובטח?", "Security question"),
        ("מה לגבי פרטיות?", "General privacy question"),
    ]

    context = {
        "child_name": "נועם",
        "completeness": 0.4,
        "video_count": 0,
        "reports_available": False
    }

    for i, (test_message, description) in enumerate(test_cases, 1):
        print(f"Test {i}: {description}")
        print(f"Question: {test_message}")
        print()

        answer = knowledge_service.get_direct_answer(test_message, context)

        if answer:
            # Print first 300 chars of response
            print("Response preview:")
            print("-" * 80)
            print(answer[:500])
            if len(answer) > 500:
                print(f"... (total {len(answer)} chars)")
            print("-" * 80)
        else:
            print("✗ No answer generated")

        print("\n")

def test_response_length():
    """Test that responses are shorter and more focused"""
    print("=" * 80)
    print("TEST 3: Response Length Comparison")
    print("=" * 80)

    knowledge_service = get_knowledge_service()

    # Get the old static FAQ response
    old_response = domain_knowledge.FAQ["data_privacy_comprehensive"]["answer_hebrew"]

    # Get a new contextual response
    context = {"child_name": "נועם", "completeness": 0.4}
    test_message = "מה לגבי הסירטונים, איפה הם נישמרים?"
    new_response = knowledge_service._get_contextual_privacy_answer(test_message, context)

    print(f"Old static response length: {len(old_response)} characters")
    print(f"New contextual response length: {len(new_response)} characters")
    print(f"Reduction: {len(old_response) - len(new_response)} characters ({(1 - len(new_response)/len(old_response))*100:.1f}%)")
    print()

    # Check that response is focused
    if "איפה הסרטונים נשמרים" in new_response:
        print("✓ Response addresses the specific question about videos")
    else:
        print("✗ Response may not be addressing the specific question")

    print()

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("PRIVACY FAQ IMPROVEMENTS - TEST SUITE")
    print("=" * 80 + "\n")

    try:
        test_pattern_matching()
        test_contextual_responses()
        test_response_length()

        print("=" * 80)
        print("ALL TESTS COMPLETED")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
