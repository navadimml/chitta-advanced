#!/usr/bin/env python3
"""
Test action_registry integration with prerequisite_service.

Verifies that config-driven prerequisite checking produces
the expected results.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.prerequisite_service import get_prerequisite_service
from app.prompts.prerequisites import Action


def test_always_available_actions():
    """Test actions that are always available"""
    print("=" * 60)
    print("Test 1: Always Available Actions")
    print("=" * 60)

    service = get_prerequisite_service()

    # Context with minimal state
    context = {
        "completeness": 0.0,
        "video_count": 0,
        "analysis_complete": False,
        "reports_available": False,
    }

    # These should always be available
    always_available = [
        "continue_interview",
        "consultation",
        "add_journal_entry",
        "view_journal",
    ]

    for action in always_available:
        result = service.check_action_feasible(action, context)
        print(f"  {action}: {'✅ Available' if result.feasible else '❌ Not available'}")
        assert result.feasible, f"{action} should always be available"

    print("✅ PASS - All always-available actions are available\n")
    return True


def test_interview_complete_required():
    """Test actions that require interview completion"""
    print("=" * 60)
    print("Test 2: Interview Complete Required")
    print("=" * 60)

    service = get_prerequisite_service()

    # Context: Interview NOT complete
    context_incomplete = {
        "completeness": 0.50,  # 50% - not complete
        "video_count": 0,
        "analysis_complete": False,
        "reports_available": False,
    }

    # Context: Interview complete
    context_complete = {
        "completeness": 0.85,  # 85% - complete
        "video_count": 0,
        "analysis_complete": False,
        "reports_available": False,
    }

    actions_requiring_interview = [
        "view_video_guidelines",
        "upload_video",
    ]

    print("\nWith incomplete interview (50%):")
    for action in actions_requiring_interview:
        result = service.check_action_feasible(action, context_incomplete)
        print(f"  {action}: {'✅' if not result.feasible else '❌'} Blocked")
        assert not result.feasible, f"{action} should be blocked when interview incomplete"
        assert result.explanation_to_user, "Should have Hebrew explanation"

    print("\nWith complete interview (85%):")
    for action in actions_requiring_interview:
        result = service.check_action_feasible(action, context_complete)
        print(f"  {action}: {'✅' if result.feasible else '❌'} Available")
        assert result.feasible, f"{action} should be available when interview complete"

    print("\n✅ PASS - Interview completion gating works\n")
    return True


def test_video_requirements():
    """Test actions that require videos"""
    print("=" * 60)
    print("Test 3: Video Requirements")
    print("=" * 60)

    service = get_prerequisite_service()

    # Interview complete, but no videos
    context_no_videos = {
        "completeness": 0.85,
        "video_count": 0,
        "analysis_complete": False,
        "reports_available": False,
    }

    # Interview complete, 2 videos (not enough)
    context_insufficient_videos = {
        "completeness": 0.85,
        "video_count": 2,
        "analysis_complete": False,
        "reports_available": False,
    }

    # Interview complete, 3 videos (enough)
    context_enough_videos = {
        "completeness": 0.85,
        "video_count": 3,
        "analysis_complete": False,
        "reports_available": False,
    }

    print("\nWith 0 videos:")
    result = service.check_action_feasible("analyze_videos", context_no_videos)
    print(f"  analyze_videos: {'✅' if not result.feasible else '❌'} Blocked")
    assert not result.feasible, "Should need videos to analyze"

    print("\nWith 2 videos (insufficient):")
    result = service.check_action_feasible("analyze_videos", context_insufficient_videos)
    print(f"  analyze_videos: {'✅' if not result.feasible else '❌'} Blocked")
    assert not result.feasible, "Should need 3+ videos"

    print("\nWith 3 videos (sufficient):")
    result = service.check_action_feasible("analyze_videos", context_enough_videos)
    print(f"  analyze_videos: {'✅' if result.feasible else '❌'} Available")
    assert result.feasible, "Should be available with 3+ videos"

    print("\n✅ PASS - Video requirements work\n")
    return True


def test_report_requirements():
    """Test actions that require reports"""
    print("=" * 60)
    print("Test 4: Report Requirements")
    print("=" * 60)

    service = get_prerequisite_service()

    # No reports
    context_no_reports = {
        "completeness": 0.85,
        "video_count": 3,
        "analysis_complete": True,
        "reports_available": False,
    }

    # Reports available (share_report requires ongoing phase)
    context_with_reports = {
        "completeness": 0.85,
        "video_count": 3,
        "analysis_complete": True,
        "reports_available": True,
        "phase": "ongoing",  # share_report requires ongoing phase
    }

    report_actions = [
        "view_report",
        "download_report",
        "share_report",
        "contact_expert",
    ]

    print("\nWithout reports:")
    for action in report_actions:
        result = service.check_action_feasible(action, context_no_reports)
        print(f"  {action}: {'✅' if not result.feasible else '❌'} Blocked")
        assert not result.feasible, f"{action} should require reports"

    print("\nWith reports available:")
    for action in report_actions:
        result = service.check_action_feasible(action, context_with_reports)
        print(f"  {action}: {'✅' if result.feasible else '❌'} Available")
        assert result.feasible, f"{action} should be available with reports"

    print("\n✅ PASS - Report requirements work\n")
    return True


def test_get_available_actions():
    """Test getting list of available actions"""
    print("=" * 60)
    print("Test 5: Get Available Actions")
    print("=" * 60)

    service = get_prerequisite_service()

    # Empty state
    context_empty = {
        "completeness": 0.0,
        "video_count": 0,
        "analysis_complete": False,
        "reports_available": False,
    }

    # Complete state
    context_complete = {
        "completeness": 0.85,
        "video_count": 3,
        "analysis_complete": True,
        "reports_available": True,
    }

    print("\nWith empty state:")
    available = service.get_available_actions(context_empty)
    action_names = [a.value for a in available]
    print(f"  Available actions: {action_names}")
    assert "continue_interview" in action_names
    assert "consultation" in action_names
    assert "view_report" not in action_names
    print("  ✅ Correct subset available")

    print("\nWith complete state (all done):")
    available = service.get_available_actions(context_complete)
    action_names = [a.value for a in available]
    print(f"  Available actions ({len(available)}): {action_names}")
    assert "view_report" in action_names
    assert "download_report" in action_names
    assert len(available) >= 10, "Most actions should be available"
    print("  ✅ All expected actions available")

    print("\n✅ PASS - get_available_actions works\n")
    return True


def test_hebrew_explanations():
    """Test that Hebrew explanations are provided"""
    print("=" * 60)
    print("Test 6: Hebrew Explanations")
    print("=" * 60)

    service = get_prerequisite_service()

    context = {
        "completeness": 0.50,
        "video_count": 0,
        "analysis_complete": False,
        "reports_available": False,
        "child_name": "יוני",
    }

    # Check blocked action has Hebrew explanation
    result = service.check_action_feasible("view_report", context)

    print(f"\nAction: view_report")
    print(f"Feasible: {result.feasible}")
    print(f"Explanation: {result.explanation_to_user[:100]}...")

    assert not result.feasible, "Should be blocked"
    assert result.explanation_to_user, "Should have explanation"
    assert len(result.explanation_to_user) > 20, "Explanation should be substantial"
    # Check for Hebrew characters (basic check)
    assert any(ord(c) >= 0x0590 and ord(c) <= 0x05FF for c in result.explanation_to_user), \
        "Explanation should contain Hebrew text"

    print("\n✅ PASS - Hebrew explanations provided\n")
    return True


def main():
    """Run all tests"""
    print("\n🧪 Action Integration Test Suite\n")

    tests = [
        ("Always Available Actions", test_always_available_actions),
        ("Interview Complete Required", test_interview_complete_required),
        ("Video Requirements", test_video_requirements),
        ("Report Requirements", test_report_requirements),
        ("Get Available Actions", test_get_available_actions),
        ("Hebrew Explanations", test_hebrew_explanations),
    ]

    results = {}
    for name, test_fn in tests:
        try:
            results[name] = test_fn()
        except Exception as e:
            print(f"❌ {name} FAILED: {e}\n")
            import traceback
            traceback.print_exc()
            results[name] = False

    # Summary
    print("\n" + "=" * 60)
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
        print("\n🎉 All tests passed! Action registry integration working!\n")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
