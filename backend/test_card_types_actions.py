#!/usr/bin/env python3
"""
Test Card Types and Actions

Verifies that cards have correct types (guidance vs progress) and correct actions (clickable vs not).
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.config.card_generator import get_card_generator


def main():
    """Test card types and clickability"""

    print("\n" + "=" * 80)
    print("🎨 CARD TYPES & ACTIONS TEST")
    print("=" * 80)

    card_generator = get_card_generator()

    # Context with profile, concerns, and strengths
    context = {
        "phase": "screening",
        "completeness": 0.25,
        "message_count": 8,
        "child_name": "יוני",
        "child_age": 5,
        "primary_concerns": ["speech", "social"],
        "strengths": "ילד מקסים ששוחק הרבה",
        "uploaded_video_count": 0,
        "video_guidelines_status": "not_ready",
        "reports_status": "not_ready",
        "user_viewed_report": False,
        "journal_entry_count": 0,
    }

    cards = card_generator.get_visible_cards(context)

    print("\n" + "-" * 80)
    print(f"Found {len(cards)} visible cards")
    print("-" * 80)

    for card in cards:
        card_type = card.get("type")
        status = card.get("status")
        icon = card.get("icon")
        action = card.get("action")
        title = card.get("title")

        print(f"\n{card_type}:")
        print(f"  Title: {title}")
        print(f"  Status: {status}")
        print(f"  Icon: {icon}")
        print(f"  Action: {action if action else 'None (not clickable)'}")

        # Check expectations
        if card_type == "child_profile_card":
            if status == "instruction":
                print("  ✅ Correct status (guidance → instruction)")
            else:
                print(f"  ❌ Wrong status! Expected 'instruction', got '{status}'")

            if action is None:
                print("  ✅ Not clickable (correct)")
            else:
                print(f"  ❌ Clickable! Should not have action: {action}")

        elif card_type == "concerns_card":
            if status == "instruction":
                print("  ✅ Correct status (guidance → instruction)")
            else:
                print(f"  ❌ Wrong status! Expected 'instruction', got '{status}'")

            if action is None:
                print("  ✅ Not clickable (correct)")
            else:
                print(f"  ❌ Clickable! Should not have action: {action}")

        elif card_type == "strengths_card":
            if status == "new":
                print("  ✅ Correct status (success → new)")
            else:
                print(f"  ❌ Wrong status! Expected 'new', got '{status}'")

            if action is None:
                print("  ✅ Not clickable (correct)")
            else:
                print(f"  ❌ Clickable! Should not have action: {action}")

        elif card_type == "interview_progress_card":
            if status == "processing":
                print("  ✅ Correct status (progress → processing)")
            else:
                print(f"  ❌ Wrong status! Expected 'processing', got '{status}'")

            if action == "continue_interview":
                print("  ✅ Clickable with continue_interview action (correct)")
            else:
                print(f"  ⚠️  Different action: {action}")

    print("\n" + "=" * 80)
    print("EXPECTED BEHAVIOR")
    print("=" * 80)

    print("\nCard Type Mappings:")
    print("  - guidance → status: 'instruction' (purple, no animation)")
    print("  - progress → status: 'processing' (blue, pulsing animation)")
    print("  - success → status: 'new' (green, celebration)")
    print("  - action_needed → status: 'action' (orange, alert)")

    print("\nClickable vs Non-Clickable:")
    print("  - Profile card: NOT clickable (informational)")
    print("  - Concerns card: NOT clickable (informational)")
    print("  - Strengths card: NOT clickable (informational)")
    print("  - Progress card: CLICKABLE (has action)")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
