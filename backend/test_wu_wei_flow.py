#!/usr/bin/env python3
"""
Test Wu Wei Architecture - Prerequisite System & Card Generation

This script tests the complete Wu Wei flow:
1. Qualitative knowledge richness check
2. Context building with artifacts and flags
3. Card generation based on prerequisites
4. Progressive conversation depth
"""

import sys
import logging
from typing import Dict, Any

# Setup path
sys.path.insert(0, '/home/user/chitta-advanced/backend')

from app.services.wu_wei_prerequisites import get_wu_wei_prerequisites
from app.services.prerequisite_service import get_prerequisite_service
from app.config.card_generator import get_card_generator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_section(title: str):
    """Print a section divider"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def test_knowledge_richness_progression():
    """Test 1: Qualitative knowledge richness at different conversation stages"""
    print_section("TEST 1: Knowledge Richness Progression (Qualitative)")

    wu_wei = get_wu_wei_prerequisites()

    scenarios = [
        {
            "name": "👋 Just Started - Only basic info",
            "context": {
                "child_name": "דני",
                "age": 4,
                "message_count": 2
            }
        },
        {
            "name": "💬 Early Conversation - Basic info + 1 concern",
            "context": {
                "child_name": "דני",
                "age": 4,
                "primary_concerns": ["שפה"],
                "message_count": 5
            }
        },
        {
            "name": "🌱 Developing - Has concerns but no strengths yet",
            "context": {
                "child_name": "דני",
                "age": 4,
                "primary_concerns": ["שפה", "חברתי"],
                "concern_description": "מדבר מעט, מתקשה לבטא את עצמו. מעדיף להיות לבד.",
                "message_count": 8
            }
        },
        {
            "name": "💭 Deepening - Has concerns + strengths",
            "context": {
                "child_name": "דני",
                "age": 4,
                "primary_concerns": ["שפה", "חברתי"],
                "concern_description": "מדבר מעט, מתקשה לבטא את עצמו. מעדיף להיות לבד.",
                "strengths": ["יצירתי מאוד, אוהב לצייר", "סקרן ומתעניין בדברים חדשים"],
                "message_count": 12
            }
        },
        {
            "name": "✨ Rich - Complete picture with context",
            "context": {
                "child_name": "דני",
                "age": 4,
                "primary_concerns": ["שפה", "חברתי"],
                "concern_description": "מדבר מעט, מתקשה לבטא את עצמו. התחיל לדבר מאוחר בגיל 3. מעדיף להיות לבד.",
                "strengths": ["יצירתי מאוד, אוהב לצייר", "סקרן ומתעניין בדברים חדשים"],
                "other_info": "יחיד, הולך לגן רגיל, אוכל טוב, ישן טוב",
                "message_count": 15
            }
        }
    ]

    for scenario in scenarios:
        print(f"Scenario: {scenario['name']}")
        print(f"  Message count: {scenario['context']['message_count']}")
        print(f"  Child name: {scenario['context'].get('child_name', 'None')}")
        print(f"  Concerns: {scenario['context'].get('primary_concerns', [])}")
        print(f"  Strengths: {len(scenario['context'].get('strengths', '')) if isinstance(scenario['context'].get('strengths', ''), str) else len(scenario['context'].get('strengths', []))}")
        print(f"  Context: {len(scenario['context'].get('other_info', ''))}")

        result = wu_wei.evaluate_knowledge_richness(scenario['context'])

        status = "✅ RICH" if result.met else "⏳ NOT YET"
        print(f"  Result: {status}")
        if not result.met:
            print(f"  Missing: {result.missing}")
        print()


def test_artifact_prerequisites():
    """Test 2: Artifact-based prerequisite checks"""
    print_section("TEST 2: Artifact-Based Prerequisites")

    wu_wei = get_wu_wei_prerequisites()
    prereq_service = get_prerequisite_service()

    # Scenario: Initial assessment (no baseline report yet)
    context_initial = {
        "artifacts": {},  # No artifacts yet
        "re_assessment": {"active": False}
    }

    print("Scenario: Initial Assessment State")
    print("  Artifacts: None")
    print("  Re-assessment: Not active")
    print()

    # Check: Should show welcome_card (baseline_parent_report.exists: false)
    prerequisites = {"baseline_parent_report.exists": False}
    result = wu_wei.evaluate_prerequisites(prerequisites, context_initial)
    print(f"  Check: baseline_parent_report.exists = false")
    print(f"  Result: {'✅ MET' if result.met else '❌ NOT MET'}")
    print()

    # Scenario: Ongoing support (baseline report exists)
    context_ongoing = {
        "artifacts": {
            "baseline_parent_report": {
                "exists": True,
                "status": "ready",
                "artifact_id": "report_123"
            }
        },
        "re_assessment": {"active": False}
    }

    print("Scenario: Ongoing Support State")
    print("  Artifacts: baseline_parent_report exists")
    print("  Re-assessment: Not active")
    print()

    # Check: Should NOT show welcome_card
    prerequisites_not_initial = {
        "baseline_parent_report.exists": False
    }
    result = wu_wei.evaluate_prerequisites(prerequisites_not_initial, context_ongoing)
    print(f"  Check: baseline_parent_report.exists = false")
    print(f"  Result: {'✅ MET (should NOT show welcome)' if not result.met else '❌ UNEXPECTED - welcome would show'}")
    print()

    # Check: Should show ongoing cards
    prerequisites_ongoing = {
        "baseline_parent_report.exists": True,
        "re_assessment.active": False
    }
    result = wu_wei.evaluate_prerequisites(prerequisites_ongoing, context_ongoing)
    print(f"  Check: baseline_parent_report.exists = true AND re_assessment.active = false")
    print(f"  Result: {'✅ MET (ongoing cards should show)' if result.met else '❌ NOT MET'}")
    print()


def test_context_building():
    """Test 3: Context building for card_generator"""
    print_section("TEST 3: Context Building for Cards")

    prereq_service = get_prerequisite_service()

    # Simulate session data (as it would come from database/interview_service)
    session_data = {
        "family_id": "test_family_123",
        "extracted_data": {
            "child_name": "דני",
            "age": 4,
            "primary_concerns": ["שפה", "חברתי"],
            "concern_description": "מדבר מעט, מתקשה לבטא את עצמו",
            "strengths": ["יצירתי מאוד", "סקרן"],
            "other_info": "יחיד, גן רגיל"
        },
        "message_count": 15,
        "video_guidelines": False,
        "parent_report_id": None,
        "uploaded_video_count": 0,
        "re_assessment_active": False
    }

    print("Input: session_data")
    print(f"  child_name: {session_data['extracted_data']['child_name']}")
    print(f"  message_count: {session_data['message_count']}")
    print(f"  concerns: {session_data['extracted_data']['primary_concerns']}")
    print(f"  parent_report_id: {session_data['parent_report_id']}")
    print()

    # Build context using prerequisite_service
    context = prereq_service.get_context_for_cards(session_data)

    print("Output: context for card_generator")
    print(f"  ✓ child_name: {context.get('child_name')}")
    print(f"  ✓ message_count: {context.get('message_count')}")
    print(f"  ✓ knowledge_is_rich: {context.get('knowledge_is_rich')}")
    print(f"  ✓ phase (emergent): {context.get('phase')}")
    print(f"  ✓ artifacts: {list(context.get('artifacts', {}).keys())}")
    print(f"  ✓ re_assessment.active: {context.get('re_assessment', {}).get('active')}")
    print()

    # Verify artifact detection
    has_baseline = context.get('artifacts', {}).get('baseline_parent_report') is not None
    print(f"Artifact Detection:")
    print(f"  baseline_parent_report exists: {has_baseline}")
    print(f"  Expected: False (no report yet)")
    print(f"  Status: {'✅ CORRECT' if not has_baseline else '❌ INCORRECT'}")
    print()


def test_card_generation():
    """Test 4: Card generation with artifact prerequisites"""
    print_section("TEST 4: Card Generation with Prerequisites")

    card_generator = get_card_generator()
    prereq_service = get_prerequisite_service()

    # Scenario 1: Initial assessment (knowledge not yet rich)
    print("Scenario 1: Early Conversation (knowledge NOT rich)")
    session_data_early = {
        "extracted_data": {
            "child_name": "דני",
            "age": 4,
            "primary_concerns": ["שפה"],
            "message_count": 3
        },
        "message_count": 3,
        "parent_report_id": None,
        "video_guidelines": False
    }

    context_early = prereq_service.get_context_for_cards(session_data_early)
    cards_early = card_generator.get_visible_cards(context_early, max_cards=10)

    print(f"  knowledge_is_rich: {context_early.get('knowledge_is_rich')}")
    print(f"  Cards generated: {len(cards_early)}")
    for card in cards_early:
        print(f"    - {card.get('type')}: {card.get('title')}")
    print()

    # Scenario 2: Rich knowledge (should offer guidelines)
    print("Scenario 2: Rich Knowledge (ready for guidelines)")
    session_data_rich = {
        "extracted_data": {
            "child_name": "דני",
            "age": 4,
            "primary_concerns": ["שפה", "חברתי"],
            "concern_description": "מדבר מעט, מתקשה לבטא את עצמו",
            "strengths": ["יצירתי מאוד", "סקרן"],
            "other_info": "יחיד, גן רגיל"
        },
        "message_count": 15,
        "parent_report_id": None,
        "video_guidelines": False
    }

    context_rich = prereq_service.get_context_for_cards(session_data_rich)
    cards_rich = card_generator.get_visible_cards(context_rich, max_cards=10)

    print(f"  knowledge_is_rich: {context_rich.get('knowledge_is_rich')}")
    print(f"  Cards generated: {len(cards_rich)}")
    for card in cards_rich:
        print(f"    - {card.get('type')}: {card.get('title')}")
    print()

    # Check if guidelines_offer_card would show
    has_guidelines_offer = any(card.get('type') == 'guidelines_offer_card' for card in cards_rich)
    print(f"Guidelines offer card present: {has_guidelines_offer}")
    if not has_guidelines_offer:
        print(f"  Note: Card may not appear due to other display_conditions")
        print(f"  Check: artifacts.video_guidelines.prerequisites_met")
    print()


def test_qualitative_progression():
    """Test 5: Qualitative depth indicator progression"""
    print_section("TEST 5: Qualitative Depth Indicators")

    card_generator = get_card_generator()

    stages = [
        ("👋 מתחילים להכיר", {"child_name": None, "message_count": 1}),
        ("💬 השיחה מתחילה", {"child_name": "דני", "age": 4, "message_count": 3}),
        ("🌱 השיחה מתפתחת", {"child_name": "דני", "age": 4, "primary_concerns": ["שפה"], "message_count": 8}),
        ("💭 השיחה מתעמקת", {"child_name": "דני", "age": 4, "primary_concerns": ["שפה"], "strengths": ["יצירתי"], "message_count": 12}),
        ("✨ השיחה עשירה", {"child_name": "דני", "age": 4, "primary_concerns": ["שפה"], "strengths": ["יצירתי"], "other_info": "גן רגיל", "message_count": 15})
    ]

    for expected_text, context in stages:
        emoji, text = card_generator._get_knowledge_depth_indicator(context)
        status = "✅" if text == expected_text.split(" ", 1)[1] else "⚠️"
        print(f"{status} Expected: {expected_text}")
        print(f"   Got: {emoji} {text}")
        print()


def run_all_tests():
    """Run all Wu Wei tests"""
    print("\n" + "🌟" * 40)
    print("  WU WEI ARCHITECTURE - INTEGRATION TESTS")
    print("🌟" * 40)

    try:
        test_knowledge_richness_progression()
        test_artifact_prerequisites()
        test_context_building()
        test_card_generation()
        test_qualitative_progression()

        print("\n" + "=" * 80)
        print("  ✅ ALL TESTS COMPLETED")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(run_all_tests())
