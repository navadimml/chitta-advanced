#!/usr/bin/env python3
"""
Quick test for card display condition evaluation
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.config.card_generator import get_card_generator


def main():
    """Test card condition evaluation"""

    print("\n" + "=" * 80)
    print("🧪 CARD CONDITION EVALUATION TEST")
    print("=" * 80)

    card_generator = get_card_generator()

    # Test 1: Beginning of interview (should show welcome_card, NOT show others)
    print("\n" + "-" * 80)
    print("TEST 1: Beginning of interview (completeness=0, message_count=0)")
    print("-" * 80)

    context_start = {
        "phase": "screening",
        "completeness": 0.0,
        "message_count": 0,
        "child_name": "Test Child",
        "uploaded_video_count": 0,
        "video_guidelines_status": "not_ready",
        "reports_status": "not_ready",
        "user_viewed_report": False,
        "journal_entry_count": 0,
    }

    cards_start = card_generator.get_visible_cards(context_start)
    card_ids_start = [card["card_id"] for card in cards_start]

    print(f"Visible cards: {card_ids_start}")

    # Check expectations
    if "welcome_card" in card_ids_start:
        print("  ✅ welcome_card is visible (expected)")
    else:
        print("  ❌ welcome_card is NOT visible (should be!)")

    if "interview_progress_card" not in card_ids_start:
        print("  ✅ interview_progress_card NOT visible (expected - needs message_count > 2)")
    else:
        print("  ❌ interview_progress_card is visible (should NOT be - needs message_count > 2)")

    if "interview_complete_card" not in card_ids_start:
        print("  ✅ interview_complete_card NOT visible (expected - needs completeness >= 0.80)")
    else:
        print("  ❌ interview_complete_card is visible (should NOT be - needs completeness >= 0.80)")

    if "reports_ready_card" not in card_ids_start:
        print("  ✅ reports_ready_card NOT visible (expected - needs reports_status=ready)")
    else:
        print("  ❌ reports_ready_card is visible (should NOT be - needs reports_status=ready)")

    # Test 2: Mid-interview (should show progress_card)
    print("\n" + "-" * 80)
    print("TEST 2: Mid-interview (completeness=0.50, message_count=10)")
    print("-" * 80)

    context_mid = {
        "phase": "screening",
        "completeness": 0.50,
        "message_count": 10,
        "child_name": "Test Child",
        "uploaded_video_count": 0,
        "video_guidelines_status": "not_ready",
        "reports_status": "not_ready",
        "user_viewed_report": False,
        "journal_entry_count": 0,
    }

    cards_mid = card_generator.get_visible_cards(context_mid)
    card_ids_mid = [card["card_id"] for card in cards_mid]

    print(f"Visible cards: {card_ids_mid}")

    if "interview_progress_card" in card_ids_mid:
        print("  ✅ interview_progress_card is visible (expected - completeness < 0.80, message_count > 2)")
    else:
        print("  ❌ interview_progress_card NOT visible (should be!)")

    if "interview_complete_card" not in card_ids_mid:
        print("  ✅ interview_complete_card NOT visible (expected - completeness < 0.80)")
    else:
        print("  ❌ interview_complete_card is visible (should NOT be - completeness < 0.80)")

    # Test 3: Interview complete (should show complete_card)
    print("\n" + "-" * 80)
    print("TEST 3: Interview complete (completeness=0.85, message_count=20)")
    print("-" * 80)

    context_complete = {
        "phase": "screening",
        "completeness": 0.85,
        "message_count": 20,
        "child_name": "Test Child",
        "uploaded_video_count": 0,
        "video_guidelines_status": "not_ready",
        "reports_status": "not_ready",
        "user_viewed_report": False,
        "journal_entry_count": 0,
    }

    cards_complete = card_generator.get_visible_cards(context_complete)
    card_ids_complete = [card["card_id"] for card in cards_complete]

    print(f"Visible cards: {card_ids_complete}")

    if "interview_complete_card" in card_ids_complete:
        print("  ✅ interview_complete_card is visible (expected - completeness >= 0.80)")
    else:
        print("  ❌ interview_complete_card NOT visible (should be!)")

    if "interview_progress_card" not in card_ids_complete:
        print("  ✅ interview_progress_card NOT visible (expected - completeness >= 0.80)")
    else:
        print("  ❌ interview_progress_card is visible (should NOT be - completeness >= 0.80)")

    # Test 4: Reports ready (should show reports_ready_card)
    print("\n" + "-" * 80)
    print("TEST 4: Reports ready (reports_status=ready)")
    print("-" * 80)

    context_reports = {
        "phase": "screening",
        "completeness": 0.90,
        "message_count": 25,
        "child_name": "Test Child",
        "uploaded_video_count": 3,
        "video_guidelines_status": "ready",
        "reports_status": "ready",
        "user_viewed_report": False,
        "journal_entry_count": 0,
    }

    cards_reports = card_generator.get_visible_cards(context_reports)
    card_ids_reports = [card["card_id"] for card in cards_reports]

    print(f"Visible cards: {card_ids_reports}")

    if "reports_ready_card" in card_ids_reports:
        print("  ✅ reports_ready_card is visible (expected - reports_status=ready)")
    else:
        print("  ❌ reports_ready_card NOT visible (should be!)")

    # Test 5: Ongoing phase (should show different cards)
    print("\n" + "-" * 80)
    print("TEST 5: Ongoing phase (phase=ongoing)")
    print("-" * 80)

    context_ongoing = {
        "phase": "ongoing",
        "completeness": 0.90,
        "message_count": 30,
        "child_name": "Test Child",
        "uploaded_video_count": 3,
        "video_guidelines_status": "ready",
        "reports_status": "ready",
        "user_viewed_report": True,
        "journal_entry_count": 5,
        "has_new_follow_up_summary": False,
        "user_viewed_summary": False,
        "expert_search_count": 0,
        "phase_entry_message_shown": False,
    }

    cards_ongoing = card_generator.get_visible_cards(context_ongoing)
    card_ids_ongoing = [card["card_id"] for card in cards_ongoing]

    print(f"Visible cards: {card_ids_ongoing}")

    if "ongoing_welcome_card" in card_ids_ongoing:
        print("  ✅ ongoing_welcome_card is visible (expected - phase=ongoing)")
    else:
        print("  ❌ ongoing_welcome_card NOT visible (should be!)")

    if "welcome_card" not in card_ids_ongoing:
        print("  ✅ welcome_card NOT visible (expected - only for screening phase)")
    else:
        print("  ❌ welcome_card is visible (should NOT be - only for screening)")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("\nIf all checks passed, card condition evaluation is working correctly!")
    print("If any failed, review the evaluate_display_conditions() logic.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
