#!/usr/bin/env python3
"""
Test User Scenario - Simulate actual conversation

Tests what cards appear at different stages of the interview.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.config.card_generator import get_card_generator


def print_cards(title, cards):
    """Print cards in a nice format"""
    print(f"\n{title}")
    print("-" * 80)

    if not cards:
        print("  ❌ NO CARDS VISIBLE")
        return

    for i, card in enumerate(cards, 1):
        card_type = card.get("type")
        status = card.get("status")
        icon = card.get("icon")
        action = card.get("action")
        title = card.get("title")
        subtitle = card.get("subtitle", "")

        clickable = "🖱️  CLICKABLE" if action else "📄 Info only"

        print(f"\n  {i}. {card_type}")
        print(f"     Title: {title}")
        if subtitle:
            print(f"     Text: {subtitle}")
        print(f"     Status: {status} | Icon: {icon} | {clickable}")


def main():
    """Test user scenarios"""

    print("\n" + "=" * 80)
    print("👤 USER SCENARIO TEST - What cards appear when?")
    print("=" * 80)

    card_generator = get_card_generator()

    # ==========================================================================
    # SCENARIO 1: Just started, said name and age only
    # ==========================================================================
    context1 = {
        "phase": "screening",
        "completeness": 0.05,
        "message_count": 2,
        "child_name": "יוני",
        "child_age": 5,
        "primary_concerns": [],  # No concerns mentioned yet
        "strengths": "",  # No strengths mentioned yet
        "uploaded_video_count": 0,
        "video_guidelines_status": "not_ready",
        "reports_status": "not_ready",
        "user_viewed_report": False,
        "journal_entry_count": 0,
    }

    cards1 = card_generator.get_visible_cards(context1)
    print_cards("SCENARIO 1: After saying name and age", cards1)

    # ==========================================================================
    # SCENARIO 2: Mentioned 2 concerns, no strengths yet
    # ==========================================================================
    context2 = {
        "phase": "screening",
        "completeness": 0.15,
        "message_count": 5,
        "child_name": "יוני",
        "child_age": 5,
        "primary_concerns": ["speech", "social"],
        "strengths": "",  # Still no strengths
        "uploaded_video_count": 0,
        "video_guidelines_status": "not_ready",
        "reports_status": "not_ready",
        "user_viewed_report": False,
        "journal_entry_count": 0,
    }

    cards2 = card_generator.get_visible_cards(context2)
    print_cards("SCENARIO 2: After mentioning concerns (no strengths)", cards2)

    # ==========================================================================
    # SCENARIO 3: Mentioned concerns AND strengths
    # ==========================================================================
    context3 = {
        "phase": "screening",
        "completeness": 0.25,
        "message_count": 8,
        "child_name": "יוני",
        "child_age": 5,
        "primary_concerns": ["speech", "social"],
        "strengths": "ילד מקסים ששוחק הרבה, אוהב לשחק עם חברים",  # NOW has strengths!
        "uploaded_video_count": 0,
        "video_guidelines_status": "not_ready",
        "reports_status": "not_ready",
        "user_viewed_report": False,
        "journal_entry_count": 0,
    }

    cards3 = card_generator.get_visible_cards(context3)
    print_cards("SCENARIO 3: After mentioning concerns AND strengths", cards3)

    # ==========================================================================
    # SCENARIO 4: strengths is None (not empty string)
    # ==========================================================================
    context4 = {
        "phase": "screening",
        "completeness": 0.15,
        "message_count": 5,
        "child_name": "יוני",
        "child_age": 5,
        "primary_concerns": ["speech", "social"],
        "strengths": None,  # None instead of empty string
        "uploaded_video_count": 0,
        "video_guidelines_status": "not_ready",
        "reports_status": "not_ready",
        "user_viewed_report": False,
        "journal_entry_count": 0,
    }

    cards4 = card_generator.get_visible_cards(context4)
    print_cards("SCENARIO 4: strengths is None (not empty string)", cards4)

    # ==========================================================================
    # SUMMARY
    # ==========================================================================
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print("\n💡 Strengths Card Display Logic:")
    print("   - Condition: strengths: '!= None'")
    print("   - Shows when: strengths field has non-empty text")
    print("   - Hidden when: strengths is None or empty string")

    print("\n📋 Expected Card Progression:")
    print("   1. After name/age → Profile card appears")
    print("   2. After concerns → Concerns card appears")
    print("   3. After strengths mentioned → Strengths card appears")
    print("   4. Progress card always visible during interview")

    print("\n⚠️  If strengths card not showing:")
    print("   - Check if extraction captured strengths from conversation")
    print("   - Verify strengths field is not None or empty string")
    print("   - Look in logs for extracted data")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
