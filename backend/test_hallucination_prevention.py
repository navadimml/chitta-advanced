#!/usr/bin/env python3
"""
Test Hallucination Prevention

Verify that the system does NOT extract data from gibberish or hallucinate information.
"""
import asyncio
import sys
import os
sys.path.insert(0, os.getcwd())

from app.services.conversation_service_simplified import get_simplified_conversation_service

async def test_case(test_name: str, user_message: str, expect_extraction: bool):
    """
    Test a single case.

    Args:
        test_name: Name of the test
        user_message: Message to send
        expect_extraction: True if we expect data extraction, False otherwise
    """
    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print(f"Message: {user_message}")
    print(f"Expected: {'Should extract' if expect_extraction else 'Should NOT extract'}")
    print(f"{'='*80}")

    service = get_simplified_conversation_service()
    family_id = f"test_hallucination_{test_name.replace(' ', '_')}"

    result = await service.process_message(
        family_id=family_id,
        user_message=user_message
    )

    extracted = result.get('extracted_data', {})
    function_calls = result.get('function_calls', [])
    response = result.get('response', '')

    # Check if extraction happened
    has_extraction = bool(extracted and any(extracted.values()))
    extraction_calls = [fc for fc in function_calls if fc['name'] == 'extract_interview_data']

    print(f"\nResult:")
    print(f"  Function calls: {len(function_calls)}")
    print(f"  Extraction calls: {len(extraction_calls)}")
    print(f"  Extracted data: {extracted}")
    print(f"  Response: {response[:150]}...")

    # Validate
    if expect_extraction and not has_extraction:
        print(f"\n❌ FAIL: Expected extraction but got none")
        return False
    elif not expect_extraction and has_extraction:
        print(f"\n❌ FAIL: Did NOT expect extraction but got: {extracted}")
        return False
    else:
        print(f"\n✅ PASS")
        return True

async def main():
    print("\n🧪 Testing Hallucination Prevention")
    print("="*80)

    tests = [
        # Gibberish tests (should NOT extract)
        ("Gibberish 1", "sdfsdf 34534 dfg", False),
        ("Gibberish 2", "nv vurtu, vngrf, akl vprunpy gk phu t, gucs,?", False),
        ("Gibberish 3", "asdasdasd 123123 qweqwe", False),
        ("Random chars", "!@#$%^&*()_+", False),

        # Off-topic tests (should NOT extract child data)
        ("Time question", "מה השעה עכשיו?", False),
        ("Weather", "איך מזג האוויר?", False),
        ("In a hurry", "אני ממהר", False),

        # Valid data tests (SHOULD extract)
        ("Valid Hebrew", "שמו דוד והוא בן 5", True),
        ("Valid Hebrew 2", "ליל והיא בת 12", True),
        ("Valid with concern", "דניאל בן 3 ויש לו קושי בדיבור", True),
    ]

    results = []
    for test_name, message, expect in tests:
        result = await test_case(test_name, message, expect)
        results.append(result)
        await asyncio.sleep(0.5)  # Small delay between tests

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("✅ ALL TESTS PASSED - No hallucination detected!")
    else:
        print(f"❌ {total - passed} TEST(S) FAILED - Hallucination detected!")

if __name__ == "__main__":
    asyncio.run(main())
