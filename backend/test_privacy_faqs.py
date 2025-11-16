#!/usr/bin/env python3
"""
Test script for the comprehensive privacy and quality assurance FAQs
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.prompts import domain_knowledge

def test_faq_matching():
    """Test that privacy questions match to appropriate FAQs"""

    test_cases = [
        # Privacy questions
        ("איפה אתם שומרים את המידע?", "data_privacy_comprehensive"),
        ("מי יכול לראות את הנתונים שלי?", "data_privacy_comprehensive"),
        ("האם זה בטוח?", "data_privacy_comprehensive"),

        # Video questions
        ("למה צריך לצלם סרטון?", "why_video_and_how"),

        # Human oversight questions
        ("מי בודק את הדוחות?", "human_oversight_quality"),
        ("בן אדם רואה את זה או רק AI?", "human_oversight_quality"),
        ("יש בקרת איכות?", "human_oversight_quality"),

        # Expert recommendations
        ("יש לכם המלצות ממומחים?", "expert_recommendations"),
        ("מי ממליץ על זה?", "expert_recommendations"),
    ]

    print("=" * 80)
    print("Testing Privacy & Quality Assurance FAQ Matching")
    print("=" * 80)

    for question, expected_faq in test_cases:
        matched = False
        matched_key = None

        for faq_key, faq_data in domain_knowledge.FAQ.items():
            patterns = faq_data.get("question_patterns", [])
            question_lower = question.lower()

            for pattern in patterns:
                if pattern.lower() in question_lower:
                    matched = True
                    matched_key = faq_key
                    break

            if matched:
                break

        status = "✓" if matched_key == expected_faq else "✗"
        print(f"\n{status} Q: {question}")
        print(f"  Expected: {expected_faq}")
        print(f"  Matched: {matched_key if matched else 'None'}")

        if matched and matched_key == expected_faq:
            answer = domain_knowledge.FAQ[matched_key]["answer_hebrew"]
            print(f"  Answer preview: {answer[:100]}...")


if __name__ == "__main__":
    print("\n🧪 Testing Privacy & Quality Assurance FAQs\n")
    test_faq_matching()
    print("\n" + "=" * 80)
    print("✅ Test completed!")
    print("=" * 80)
    print()
