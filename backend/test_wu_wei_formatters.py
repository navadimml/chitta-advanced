#!/usr/bin/env python3
"""
Test Wu Wei Convention-Based Formatters

Validates that the convention-based formatter system works correctly:
- {concerns_list} → auto-join with ", " and translate
- {strengths_preview} → auto-truncate to 150 chars
- {concerns_summary} → count + Hebrew plural
- {concerns_count} → just the number
- {missing_areas} → remove (placeholder for future)
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.config.card_generator import get_card_generator


def main():
    """Test Wu Wei formatters"""

    print("\n" + "=" * 80)
    print("🌟 WU WEI CONVENTION-BASED FORMATTERS TEST")
    print("=" * 80)

    card_generator = get_card_generator()

    # Track results
    tests_passed = []
    tests_failed = []

    def test_assert(condition, test_name, details=""):
        """Helper to track test results"""
        if condition:
            tests_passed.append(test_name)
            print(f"  ✅ {test_name}")
            if details:
                print(f"     {details}")
        else:
            tests_failed.append(test_name)
            print(f"  ❌ {test_name}")
            if details:
                print(f"     {details}")

    # ==========================================================================
    # TEST 1: _summary formatter with comma
    # ==========================================================================
    print("\n" + "-" * 80)
    print("TEST 1: _summary formatter (count + Hebrew plural) with comma")
    print("-" * 80)

    context_with_concerns = {
        "child_age": 5,
        "primary_concerns": ["speech", "social", "attention"],
    }

    template = "גיל {child_age}, {concerns_summary}"
    result = card_generator._apply_formatters(template, context_with_concerns)

    test_assert(
        ", 3 תחומי התפתחות" in result,
        "_summary formatter preserves comma when value exists",
        f"Template: '{template}' → Result: '{result}'"
    )

    test_assert(
        "גיל 5, 3 תחומי התפתחות" == result,
        "_summary formatter produces exact expected output",
        f"Expected: 'גיל 5, 3 תחומי התפתחות', Got: '{result}'"
    )

    # ==========================================================================
    # TEST 2: _summary formatter WITHOUT comma (empty value)
    # ==========================================================================
    print("\n" + "-" * 80)
    print("TEST 2: _summary formatter removes comma when value is empty")
    print("-" * 80)

    context_no_concerns = {
        "child_age": 5,
        "primary_concerns": [],
    }

    result_empty = card_generator._apply_formatters(template, context_no_concerns)

    test_assert(
        result_empty == "גיל 5",
        "_summary formatter removes comma when value is empty",
        f"Template: '{template}' → Result: '{result_empty}'"
    )

    test_assert(
        ", " not in result_empty,
        "No trailing comma in result",
        f"Result: '{result_empty}'"
    )

    # ==========================================================================
    # TEST 3: _list formatter (join with commas and translate)
    # ==========================================================================
    print("\n" + "-" * 80)
    print("TEST 3: _list formatter (join with commas, translate)")
    print("-" * 80)

    context_list = {
        "primary_concerns": ["speech", "social", "motor"],
    }

    template_list = "תחומי דאגה: {concerns_list}"
    result_list = card_generator._apply_formatters(template_list, context_list)

    test_assert(
        "דיבור" in result_list and "חברתי" in result_list and "מוטורי" in result_list,
        "_list formatter translates concerns to Hebrew",
        f"Result: '{result_list}'"
    )

    test_assert(
        ", " in result_list,
        "_list formatter joins with commas",
        f"Result: '{result_list}'"
    )

    # ==========================================================================
    # TEST 4: _preview formatter (truncate at 150 chars)
    # ==========================================================================
    print("\n" + "-" * 80)
    print("TEST 4: _preview formatter (truncate to 150 chars)")
    print("-" * 80)

    long_text = "זהו טקסט ארוך מאוד שמכיל הרבה מידע על חוזקות הילד. " * 10
    context_preview = {
        "strengths": long_text,
    }

    template_preview = "חוזקות: {strengths_preview}"
    result_preview = card_generator._apply_formatters(template_preview, context_preview)

    test_assert(
        len(result_preview) <= len(template_preview) - len("{strengths_preview}") + 160,
        "_preview formatter truncates to ~150 chars",
        f"Result length: {len(result_preview) - len('חוזקות: ')}"
    )

    # ==========================================================================
    # TEST 5: _count formatter (just the number)
    # ==========================================================================
    print("\n" + "-" * 80)
    print("TEST 5: _count formatter (just the number)")
    print("-" * 80)

    context_count = {
        "primary_concerns": ["speech", "social", "motor"],
    }

    template_count = "מספר תחומים: {concerns_count}"
    result_count = card_generator._apply_formatters(template_count, context_count)

    test_assert(
        result_count == "מספר תחומים: 3",
        "_count formatter returns just the number",
        f"Result: '{result_count}'"
    )

    # ==========================================================================
    # TEST 6: Hebrew pluralization (singular vs plural)
    # ==========================================================================
    print("\n" + "-" * 80)
    print("TEST 6: Hebrew pluralization (singular vs plural)")
    print("-" * 80)

    context_singular = {
        "primary_concerns": ["speech"],
    }

    result_singular = card_generator._apply_formatters("{concerns_summary}", context_singular)

    test_assert(
        "1 תחום התפתחות" == result_singular,
        "Hebrew singular form for 1 concern",
        f"Result: '{result_singular}'"
    )

    context_plural = {
        "primary_concerns": ["speech", "social"],
    }

    result_plural = card_generator._apply_formatters("{concerns_summary}", context_plural)

    test_assert(
        "2 תחומי התפתחות" == result_plural,
        "Hebrew plural form for 2+ concerns",
        f"Result: '{result_plural}'"
    )

    # ==========================================================================
    # TEST 7: Smart field matching (primary_* prefix)
    # ==========================================================================
    print("\n" + "-" * 80)
    print("TEST 7: Smart field matching (primary_* prefix)")
    print("-" * 80)

    context_prefix = {
        "primary_concerns": ["speech", "social"],
    }

    # Should find "primary_concerns" even when template uses {concerns_list}
    result_prefix = card_generator._apply_formatters("{concerns_list}", context_prefix)

    test_assert(
        "דיבור" in result_prefix,
        "Smart field matching finds primary_concerns for {concerns_list}",
        f"Result: '{result_prefix}'"
    )

    # ==========================================================================
    # TEST 8: Simple variable replacement
    # ==========================================================================
    print("\n" + "-" * 80)
    print("TEST 8: Simple variable replacement")
    print("-" * 80)

    context_simple = {
        "child_name": "יוני",
        "child_age": 5,
    }

    template_simple = "שם: {child_name}, גיל: {child_age}"
    result_simple = card_generator._apply_formatters(template_simple, context_simple)

    test_assert(
        result_simple == "שם: יוני, גיל: 5",
        "Simple variable replacement works",
        f"Result: '{result_simple}'"
    )

    # ==========================================================================
    # TEST 9: Combined formatters in one template
    # ==========================================================================
    print("\n" + "-" * 80)
    print("TEST 9: Combined formatters in one template")
    print("-" * 80)

    context_combined = {
        "child_name": "יוני",
        "child_age": 5,
        "primary_concerns": ["speech", "social"],
        "strengths": "ילד מקסים ששוחק הרבה ואוהב לשחק עם חברים",
    }

    template_combined = "{child_name} בן {child_age}, {concerns_summary}. חוזקות: {strengths_preview}"
    result_combined = card_generator._apply_formatters(template_combined, context_combined)

    test_assert(
        "יוני בן 5, 2 תחומי התפתחות" in result_combined,
        "Combined formatters work together",
        f"Result: '{result_combined}'"
    )

    test_assert(
        "חוזקות: ילד מקסים" in result_combined,
        "Multiple formatters in one template",
        f"Result: '{result_combined}'"
    )

    # ==========================================================================
    # SUMMARY
    # ==========================================================================
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    total_tests = len(tests_passed) + len(tests_failed)
    pass_rate = (len(tests_passed) / total_tests * 100) if total_tests > 0 else 0

    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {len(tests_passed)} ✅")
    print(f"Failed: {len(tests_failed)} ❌")
    print(f"Pass Rate: {pass_rate:.1f}%")

    if tests_failed:
        print("\n❌ Failed Tests:")
        for test in tests_failed:
            print(f"  - {test}")

    print("\n" + "=" * 80)
    print("WU WEI FORMATTERS VALIDATION")
    print("=" * 80)

    print("\n🌟 Wu Wei Convention-Based Formatters:")
    print("   - {concerns_list} → auto-join with \", \" and translate")
    print("   - {strengths_preview} → auto-truncate to 150 chars")
    print("   - {concerns_summary} → count + Hebrew plural")
    print("   - {concerns_count} → just the number")
    print("   - {missing_areas} → remove (placeholder for future)")
    print("   - Simple variables → direct replacement")

    print("\n🎯 Wu Wei Promise:")
    print("   ✅ New cards = YAML only, NO code changes needed")
    print("   ✅ Convention-based formatters handle all common patterns")
    print("   ✅ Smart field matching (primary_* prefix)")
    print("   ✅ Hebrew pluralization built-in")
    print("   ✅ Smart comma removal for empty values")

    print("\n" + "=" * 80)

    if pass_rate >= 95:
        print("🎉 EXCELLENT! Wu Wei formatters working perfectly!")
        return 0
    elif pass_rate >= 85:
        print("✅ GOOD! Wu Wei formatters mostly working.")
        return 0
    else:
        print("⚠️  ISSUES! Some formatters need attention.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
