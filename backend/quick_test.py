#!/usr/bin/env python3
"""
Quick Test - Validate critical fixes efficiently

Tests:
1. Gibberish rejection (no hallucination)
2. Valid data extraction
3. Off-topic handling
4. Parent simulator response length
"""
import asyncio
import sys
import os
sys.path.insert(0, os.getcwd())

from app.services.conversation_service_simplified import get_simplified_conversation_service
from app.services.parent_simulator import get_parent_simulator
from app.services.llm.factory import create_llm_provider

# Test counter
tests_passed = 0
tests_failed = 0

def print_test(name, passed, details=""):
    global tests_passed, tests_failed
    if passed:
        tests_passed += 1
        print(f"✅ {name}")
    else:
        tests_failed += 1
        print(f"❌ {name}")
    if details:
        print(f"   {details}")

async def test_gibberish_rejection():
    """Test that gibberish doesn't get extracted as data"""
    print("\n" + "="*60)
    print("TEST 1: Gibberish Rejection")
    print("="*60)

    service = get_simplified_conversation_service()

    test_cases = [
        ("sdfsdf 34534 dfg", "Random chars"),
        ("nv vurtu, vngrf", "Encoded-like text"),
        ("!!@#$ 123 xyz", "Symbols + numbers"),
    ]

    for gibberish, label in test_cases:
        result = await service.process_message(
            family_id=f"test_gib_{label.replace(' ', '_')}",
            user_message=gibberish
        )

        extracted = result.get('extracted_data', {})
        has_data = bool(extracted and any(extracted.values()))

        print_test(
            f"Gibberish '{label}'",
            not has_data,
            f"Extracted: {extracted}" if has_data else "No extraction (correct!)"
        )

async def test_valid_extraction():
    """Test that valid data IS extracted"""
    print("\n" + "="*60)
    print("TEST 2: Valid Data Extraction")
    print("="*60)

    service = get_simplified_conversation_service()

    test_cases = [
        ("שמו דוד והוא בן 5", "דוד", 5),
        ("ליל והיא בת 12", "ליל", 12),
        ("יוסף בן 3", "יוסף", 3),
    ]

    for message, expected_name, expected_age in test_cases:
        result = await service.process_message(
            family_id=f"test_valid_{expected_name}",
            user_message=message
        )

        extracted = result.get('extracted_data', {})
        name = extracted.get('child_name')
        age = extracted.get('age')

        name_ok = name == expected_name
        age_ok = age == expected_age

        print_test(
            f"Extract '{message}'",
            name_ok and age_ok,
            f"Got: name={name}, age={age} | Expected: name={expected_name}, age={expected_age}"
        )

async def test_off_topic():
    """Test that off-topic messages don't extract child data"""
    print("\n" + "="*60)
    print("TEST 3: Off-Topic Handling")
    print("="*60)

    service = get_simplified_conversation_service()

    test_cases = [
        "מה השעה עכשיו?",
        "אני ממהר",
        "איך מזג האוויר?",
    ]

    for message in test_cases:
        result = await service.process_message(
            family_id=f"test_offtopic_{message[:10].replace(' ', '_')}",
            user_message=message
        )

        extracted = result.get('extracted_data', {})
        has_child_data = bool(
            extracted.get('child_name') or
            extracted.get('age') or
            extracted.get('primary_concerns')
        )

        print_test(
            f"Off-topic: '{message}'",
            not has_child_data,
            f"Extracted: {extracted}" if has_child_data else "No child data (correct!)"
        )

async def test_parent_simulator_brevity():
    """Test that parent simulator gives SHORT responses"""
    print("\n" + "="*60)
    print("TEST 4: Parent Simulator Response Length")
    print("="*60)

    simulator = get_parent_simulator()
    llm = create_llm_provider()

    # Use simulated graphiti
    from app.services.mock_graphiti import MockGraphiti
    graphiti = MockGraphiti()

    # Start simulation
    family_id = "test_parent_sim"
    persona_id = "sarah_language_delay"
    simulator.start_simulation(family_id, persona_id)

    test_questions = [
        "מה שם הילד/ה שלך ובן/בת כמה?",
        "ספרי לי קצת - מה מעסיק אותך?",
        "מה הוא/היא אוהב/ת לעשות?",
    ]

    for question in test_questions:
        response = await simulator.generate_response(
            family_id=family_id,
            chitta_question=question,
            llm_provider=llm,
            graphiti=graphiti
        )

        if response:
            # Save to graphiti for next turn
            graphiti.save_message(family_id, "assistant", question)
            graphiti.save_message(family_id, "user", response)

            # Check length
            sentence_count = len([s for s in response.split('.') if s.strip()])
            char_count = len(response)
            is_short = sentence_count <= 3 and char_count <= 300

            print_test(
                f"Response to '{question[:30]}...'",
                is_short,
                f"Sentences: {sentence_count}, Chars: {char_count} | Response: {response[:100]}..."
            )
        else:
            print_test(
                f"Response to '{question[:30]}...'",
                False,
                "No response returned"
            )

    # Cleanup
    simulator.stop_simulation(family_id)

async def main():
    print("\n🚀 Quick Test - Critical Fixes Validation")
    print("="*60)

    # Run all tests
    await test_gibberish_rejection()
    await test_valid_extraction()
    await test_off_topic()
    await test_parent_simulator_brevity()

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    total = tests_passed + tests_failed
    print(f"✅ Passed: {tests_passed}/{total}")
    print(f"❌ Failed: {tests_failed}/{total}")

    if tests_failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {tests_failed} test(s) failed - review above")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
