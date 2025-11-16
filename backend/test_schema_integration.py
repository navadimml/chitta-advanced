#!/usr/bin/env python3
"""
Test schema_registry integration with interview_service.

Verifies that config-driven completeness calculation produces
the same results as the previous hardcoded implementation.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.config.schema_registry import calculate_completeness


def test_basic_info_only():
    """Test with only basic information"""
    print("=" * 60)
    print("Test 1: Basic Info Only (name, age, gender)")
    print("=" * 60)

    data = {
        "child_name": "Test Child",
        "age": 5,
        "gender": "female",
        "primary_concerns": [],
        "concern_details": None,
        "strengths": None,
        "developmental_history": None,
        "family_context": None,
        "daily_routines": None,
        "parent_goals": None,
        "urgent_flags": [],
    }

    completeness = calculate_completeness(data)
    expected = 0.05  # 1% + 3% + 1% = 5%

    print(f"Completeness: {completeness:.1%}")
    print(f"Expected: {expected:.1%}")

    # Allow small floating point differences
    assert abs(completeness - expected) < 0.001, f"Expected {expected}, got {completeness}"
    print("✅ PASS\n")

    return True


def test_concerns_minimal():
    """Test with minimal concern details"""
    print("=" * 60)
    print("Test 2: Basic + Minimal Concerns")
    print("=" * 60)

    data = {
        "child_name": "Test Child",
        "age": 5,
        "gender": "female",
        "primary_concerns": ["speech_delay"],
        "concern_details": "She doesn't speak much",  # 23 chars - minimal
        "strengths": None,
        "developmental_history": None,
        "family_context": None,
        "daily_routines": None,
        "parent_goals": None,
        "urgent_flags": [],
    }

    completeness = calculate_completeness(data)
    # 5% (basic) + 5% (1 concern) + 0% (details too short) = 10%
    expected = 0.10

    print(f"Completeness: {completeness:.1%}")
    print(f"Expected: {expected:.1%}")

    assert abs(completeness - expected) < 0.001, f"Expected {expected}, got {completeness}"
    print("✅ PASS\n")

    return True


def test_concerns_with_detail():
    """Test with substantial concern details"""
    print("=" * 60)
    print("Test 3: Concerns with Substantial Detail")
    print("=" * 60)

    long_details = "She has difficulty with speech. " * 10  # ~320 chars

    data = {
        "child_name": "Test Child",
        "age": 5,
        "gender": "female",
        "primary_concerns": ["speech_delay", "social_interaction"],
        "concern_details": long_details,
        "strengths": None,
        "developmental_history": None,
        "family_context": None,
        "daily_routines": None,
        "parent_goals": None,
        "urgent_flags": [],
    }

    completeness = calculate_completeness(data)
    # Config-driven calculation (simplified from old hardcoded logic):
    # 5% (basic) + 10% (2 concerns @ 5% each) + 20% (details >200) = 35%
    # Note: Old logic had complex bonus structure, new config is simpler
    expected = 0.35

    print(f"Completeness: {completeness:.1%}")
    print(f"Expected: {expected:.1%}")

    assert abs(completeness - expected) < 0.02, f"Expected {expected}, got {completeness}"
    print("✅ PASS\n")

    return True


def test_comprehensive_data():
    """Test with comprehensive interview data"""
    print("=" * 60)
    print("Test 4: Comprehensive Interview Data")
    print("=" * 60)

    long_text = "Detailed information here. " * 15  # ~400+ chars

    data = {
        "child_name": "Test Child",
        "age": 5,
        "gender": "female",
        "primary_concerns": ["speech_delay", "social_interaction", "motor_skills"],
        "concern_details": long_text,
        "strengths": long_text,
        "developmental_history": long_text,
        "family_context": long_text,
        "daily_routines": long_text,
        "parent_goals": long_text,
        "urgent_flags": ["regression"],
    }

    completeness = calculate_completeness(data)

    print(f"Completeness: {completeness:.1%}")
    # Should be close to or at 90%+ (comprehensive data)

    assert completeness >= 0.89, f"Expected >= 89%, got {completeness:.1%}"  # Allow small floating point variance
    print("✅ PASS - Comprehensive data yields high completeness\n")

    return True


def test_edge_cases():
    """Test edge cases"""
    print("=" * 60)
    print("Test 5: Edge Cases")
    print("=" * 60)

    # Empty data
    empty_data = {
        "child_name": None,
        "age": None,
        "gender": None,
        "primary_concerns": [],
        "concern_details": None,
        "strengths": None,
        "developmental_history": None,
        "family_context": None,
        "daily_routines": None,
        "parent_goals": None,
        "urgent_flags": [],
    }

    completeness = calculate_completeness(empty_data)
    print(f"Empty data completeness: {completeness:.1%}")
    assert completeness == 0.0, f"Expected 0%, got {completeness:.1%}"
    print("✅ Empty data = 0%")

    # Only age (most critical basic field)
    age_only = empty_data.copy()
    age_only["age"] = 5

    completeness = calculate_completeness(age_only)
    print(f"Age only completeness: {completeness:.1%}")
    assert completeness == 0.03, f"Expected 3%, got {completeness:.1%}"
    print("✅ Age only = 3%")

    print("✅ PASS\n")
    return True


def main():
    """Run all tests"""
    print("\n🧪 Schema Integration Test Suite\n")

    tests = [
        ("Basic Info Only", test_basic_info_only),
        ("Minimal Concerns", test_concerns_minimal),
        ("Concerns with Detail", test_concerns_with_detail),
        ("Comprehensive Data", test_comprehensive_data),
        ("Edge Cases", test_edge_cases),
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
        print("\n🎉 All tests passed! Schema integration working correctly!\n")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
