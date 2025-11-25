#!/usr/bin/env python3
"""
Test script for Child Space Service (Daniel's Space).

Tests Living Dashboard Phase 2:
- Slot configuration loading
- Artifact-to-slot mapping
- Slot population from family state
- Header badge generation
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from app.models.family_state import FamilyState, Video, JournalEntry, Artifact
from app.models.artifact_slot import ArtifactSlot, SlotItem, ChildSpace
from app.services.child_space_service import ChildSpaceService, get_child_space_service
from app.config.config_loader import load_artifacts


def test_slot_config_loading():
    """Test that slot configuration loads correctly."""
    print("\n" + "=" * 60)
    print("Testing Slot Configuration Loading...")
    print("=" * 60)

    config = load_artifacts()

    # Check slots section exists
    slots = config.get("slots", {})
    assert len(slots) > 0, "No slots defined in artifacts.yaml"
    print(f"✓ Found {len(slots)} slot definitions")

    # Check expected slots
    expected_slots = ["current_report", "filming_guidelines", "videos", "journal"]
    for slot_id in expected_slots:
        assert slot_id in slots, f"Missing expected slot: {slot_id}"
        slot = slots[slot_id]
        assert "slot_name" in slot, f"Slot {slot_id} missing slot_name"
        assert "icon" in slot, f"Slot {slot_id} missing icon"
        print(f"✓ Slot '{slot_id}': {slot['icon']} {slot['slot_name']}")

    # Check slot_order
    slot_order = config.get("slot_order", [])
    assert len(slot_order) > 0, "No slot_order defined"
    print(f"✓ Slot order: {slot_order}")

    print("\n✅ Slot configuration tests passed!")
    return True


def test_artifact_slot_mapping():
    """Test artifact-to-slot mapping."""
    print("\n" + "=" * 60)
    print("Testing Artifact-to-Slot Mapping...")
    print("=" * 60)

    config = load_artifacts()
    artifacts = config.get("artifacts", {})

    # Check that artifacts have slot config
    artifacts_with_slots = []
    for artifact_id, artifact_config in artifacts.items():
        if "slot" in artifact_config:
            slot_config = artifact_config["slot"]
            slot_id = slot_config.get("slot_id")
            artifacts_with_slots.append((artifact_id, slot_id))
            print(f"✓ {artifact_id} → {slot_id}")

    assert len(artifacts_with_slots) > 0, "No artifacts have slot configuration"
    print(f"\n✓ {len(artifacts_with_slots)} artifacts mapped to slots")

    # Check that both baseline and updated reports map to same slot
    report_slots = [
        (a, s) for a, s in artifacts_with_slots
        if "report" in a.lower() and "parent" in a.lower()
    ]
    if len(report_slots) >= 2:
        slot_ids = set(s for _, s in report_slots)
        assert len(slot_ids) == 1, "Parent reports should map to same slot"
        print(f"✓ Both parent reports map to '{list(slot_ids)[0]}' (version history works)")

    print("\n✅ Artifact-slot mapping tests passed!")
    return True


def test_child_space_service():
    """Test ChildSpaceService."""
    print("\n" + "=" * 60)
    print("Testing ChildSpaceService...")
    print("=" * 60)

    service = get_child_space_service()
    print("✓ ChildSpaceService initialized")

    # Create a test family state
    family_state = FamilyState(
        family_id="test_family",
        child={"name": "Daniel", "age": "3"},
    )

    # Get empty space
    space = service.get_child_space(family_state)
    assert space.family_id == "test_family"
    assert space.child_name == "Daniel"
    assert len(space.slots) > 0
    print(f"✓ Empty space: {len(space.slots)} slots, child_name='{space.child_name}'")

    # Check all slots exist
    slot_ids = [s.slot_id for s in space.slots]
    print(f"✓ Slots: {slot_ids}")

    # All slots should be empty initially
    for slot in space.slots:
        assert not slot.has_content, f"Slot {slot.slot_id} should be empty"
    print("✓ All slots empty initially")

    print("\n✅ ChildSpaceService tests passed!")
    return True


def test_slot_population():
    """Test slot population with artifacts."""
    print("\n" + "=" * 60)
    print("Testing Slot Population...")
    print("=" * 60)

    service = get_child_space_service()

    # Create family state with some artifacts
    family_state = FamilyState(
        family_id="test_family",
        child={"name": "Daniel"},
        videos_uploaded=[
            Video(
                id="vid_1",
                scenario="Morning Routine",
                uploaded_at=datetime.now(),
                duration_seconds=120,
            ),
            Video(
                id="vid_2",
                scenario="Play Time",
                uploaded_at=datetime.now(),
                duration_seconds=90,
            ),
        ],
        journal_entries=[
            JournalEntry(
                id="entry_1",
                content="Daniel said his first word today!",
                timestamp=datetime.now(),
            ),
        ],
    )

    # Get space
    space = service.get_child_space(family_state)

    # Check videos slot
    videos_slot = next((s for s in space.slots if s.slot_id == "videos"), None)
    assert videos_slot is not None
    assert videos_slot.is_collection
    assert videos_slot.item_count == 2
    assert videos_slot.has_content
    print(f"✓ Videos slot: {videos_slot.item_count} items")

    # Check journal slot
    journal_slot = next((s for s in space.slots if s.slot_id == "journal"), None)
    assert journal_slot is not None
    assert journal_slot.is_collection
    assert journal_slot.item_count == 1
    assert journal_slot.has_content
    print(f"✓ Journal slot: {journal_slot.item_count} items")

    # Check header badges
    assert len(space.header_badges) >= 2
    print(f"✓ Header badges: {len(space.header_badges)}")
    for badge in space.header_badges:
        print(f"  - {badge['icon']} {badge.get('text', badge['slot_id'])}")

    print("\n✅ Slot population tests passed!")
    return True


def test_header_summary():
    """Test header summary generation."""
    print("\n" + "=" * 60)
    print("Testing Header Summary...")
    print("=" * 60)

    service = get_child_space_service()

    # Empty state
    empty_state = FamilyState(family_id="test_empty")
    badges = service.get_header_summary(empty_state)
    assert len(badges) == 0
    print("✓ Empty state: no badges")

    # State with content
    state_with_content = FamilyState(
        family_id="test_content",
        videos_uploaded=[
            Video(id="v1", scenario="Test", uploaded_at=datetime.now()),
            Video(id="v2", scenario="Test 2", uploaded_at=datetime.now()),
            Video(id="v3", scenario="Test 3", uploaded_at=datetime.now()),
        ],
    )

    badges = service.get_header_summary(state_with_content)
    assert len(badges) >= 1
    print(f"✓ State with videos: {len(badges)} badge(s)")

    video_badge = next((b for b in badges if b["slot_id"] == "videos"), None)
    assert video_badge is not None
    assert video_badge["icon"] == "📹"
    print(f"✓ Video badge: {video_badge}")

    print("\n✅ Header summary tests passed!")
    return True


def main():
    """Run all tests."""
    print("\n")
    print("🧪 Child Space Test Suite (Phase 2: Daniel's Space)")
    print("=" * 60)

    tests = [
        ("Slot Configuration", test_slot_config_loading),
        ("Artifact-Slot Mapping", test_artifact_slot_mapping),
        ("ChildSpaceService", test_child_space_service),
        ("Slot Population", test_slot_population),
        ("Header Summary", test_header_summary),
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
        print("\n🎉 All Phase 2 tests passed! Daniel's Space is working!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
