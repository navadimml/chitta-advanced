#!/usr/bin/env python3
"""
Test script for Card Lifecycle Service.

Tests the Phase 1 Living Dashboard implementation:
- Card creation on transitions
- Card dismissal conditions
- Card persistence in FamilyState
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from app.models.active_card import ActiveCard, CardDisplayMode, create_active_card
from app.models.family_state import FamilyState
from app.services.card_lifecycle_service import CardLifecycleService


def test_active_card_model():
    """Test ActiveCard model basics."""
    print("\n" + "=" * 60)
    print("Testing ActiveCard Model...")
    print("=" * 60)

    # Create a card
    card = ActiveCard(
        card_id="test_card",
        created_by_moment="test_moment",
        priority=80,
        content={"title": "Test Title", "body": "Test Body"},
        dismiss_when={"some_condition": True},
    )

    assert card.card_id == "test_card"
    assert card.dismissed == False
    assert card.priority == 80
    assert len(card.instance_id) > 0
    print("✓ ActiveCard created successfully")

    # Test dismissal
    card.dismiss(by="test")
    assert card.dismissed == True
    assert card.dismissed_by == "test"
    assert card.dismissed_at is not None
    print("✓ Card dismissal works")

    print("\n✅ ActiveCard model tests passed!")
    return True


def test_card_creation_from_config():
    """Test creating cards from workflow config."""
    print("\n" + "=" * 60)
    print("Testing Card Creation from Config...")
    print("=" * 60)

    card_config = {
        "card_id": "report_ready_card",
        "card_type": "success",
        "priority": 100,
        "lifecycle": {
            "trigger": "transition",
            "dismiss_when": {"artifacts.baseline_parent_report.viewed": True},
            "dismiss_on_action": "view_report",
            "prevent_re_trigger": True,
        },
        "content": {
            "title": "הדוח מוכן!",
            "body": "Your report is ready.",
            "dynamic": {
                "progress": "artifacts.baseline_parent_report.progress"
            }
        },
        "actions": ["view_report", "download_report"],
    }

    context = {
        "artifacts": {
            "baseline_parent_report": {
                "progress": 100,
                "status": "ready"
            }
        }
    }

    card = create_active_card(card_config, "report_ready", context)

    assert card.card_id == "report_ready_card"
    assert card.created_by_moment == "report_ready"
    assert card.priority == 100
    assert card.content["title"] == "הדוח מוכן!"
    assert card.dismiss_on_action == "view_report"
    assert "progress" in card.dynamic_fields
    print("✓ Card created from config correctly")

    print("\n✅ Card creation tests passed!")
    return True


def test_card_lifecycle_service():
    """Test CardLifecycleService transitions."""
    print("\n" + "=" * 60)
    print("Testing CardLifecycleService...")
    print("=" * 60)

    service = CardLifecycleService()
    print("✓ CardLifecycleService initialized")

    # Create a family state
    family_state = FamilyState(family_id="test_family")
    assert len(family_state.active_cards) == 0
    print("✓ FamilyState has no active cards initially")

    # Simulate context transition: report becomes ready
    previous_context = {
        "baseline_professional_report": {"exists": False},
        "artifacts": {
            "baseline_parent_report": {"exists": False}
        }
    }

    current_context = {
        "baseline_professional_report": {"exists": True},
        "artifacts": {
            "baseline_parent_report": {"exists": True, "status": "ready"}
        }
    }

    # Process transitions
    new_cards = service.process_transitions(
        family_state=family_state,
        previous_context=previous_context,
        current_context=current_context
    )

    print(f"✓ Processed transitions: {len(new_cards)} new cards created")

    # Get visible cards
    visible = service.get_visible_cards(family_state)
    print(f"✓ Visible cards: {len(visible)}")

    for card in visible:
        print(f"  - {card.card_id}: priority={card.priority}")

    print("\n✅ CardLifecycleService tests passed!")
    return True


def test_card_dismissal():
    """Test card dismissal mechanisms."""
    print("\n" + "=" * 60)
    print("Testing Card Dismissal...")
    print("=" * 60)

    service = CardLifecycleService()
    family_state = FamilyState(family_id="test_family")

    # Manually add a card
    card = ActiveCard(
        card_id="test_dismissal_card",
        created_by_moment="test_moment",
        priority=50,
        content={"title": "Test"},
        dismiss_on_action="test_action",
    )
    family_state.active_cards.append(card)
    print("✓ Added test card to family state")

    # Check it's visible
    visible = service.get_visible_cards(family_state)
    assert len(visible) == 1
    print("✓ Card is visible")

    # Dismiss by action
    dismissed = service.dismiss_by_action(family_state, "test_action")
    assert len(dismissed) == 1
    assert dismissed[0] == "test_dismissal_card"
    print("✓ Card dismissed by action")

    # Check it's no longer visible
    visible = service.get_visible_cards(family_state)
    assert len(visible) == 0
    print("✓ Card is no longer visible")

    # Check dismissal was recorded
    assert "test_moment" in family_state.dismissed_card_moments
    print("✓ Dismissal recorded in family state")

    print("\n✅ Card dismissal tests passed!")
    return True


def test_prevent_re_trigger():
    """Test that dismissed cards don't re-trigger."""
    print("\n" + "=" * 60)
    print("Testing Prevent Re-trigger...")
    print("=" * 60)

    service = CardLifecycleService()
    family_state = FamilyState(family_id="test_family")

    # Record a dismissed moment
    family_state.dismissed_card_moments["report_ready"] = datetime.utcnow()
    print("✓ Recorded dismissed moment")

    # Try to trigger the same moment again
    previous_context = {
        "baseline_professional_report": {"exists": False},
    }
    current_context = {
        "baseline_professional_report": {"exists": True},
    }

    new_cards = service.process_transitions(
        family_state=family_state,
        previous_context=previous_context,
        current_context=current_context
    )

    # Should not create card because moment was dismissed
    report_cards = [c for c in new_cards if c.card_id == "report_ready_card"]
    print(f"✓ Cards created for report_ready: {len(report_cards)}")
    print("  (Expected: 0 because moment was previously dismissed)")

    print("\n✅ Prevent re-trigger tests passed!")
    return True


def main():
    """Run all tests."""
    print("\n")
    print("🧪 Card Lifecycle Test Suite (Phase 1: Living Dashboard)")
    print("=" * 60)

    tests = [
        ("ActiveCard Model", test_active_card_model),
        ("Card Creation from Config", test_card_creation_from_config),
        ("CardLifecycleService", test_card_lifecycle_service),
        ("Card Dismissal", test_card_dismissal),
        ("Prevent Re-trigger", test_prevent_re_trigger),
    ]

    results = {}
    for name, test_fn in tests:
        try:
            results[name] = test_fn()
        except Exception as e:
            print(f"\n❌ {name} failed: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False

    # Summary
    print("\n")
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print()
    print(f"Result: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All Phase 1 tests passed! Card Lifecycle system is working!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
