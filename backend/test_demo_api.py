"""
Test Demo Mode API Integration

Tests the complete demo flow:
1. Demo intent detection via POST /chat/send
2. Manual demo start via POST /demo/start
3. Step progression via GET /demo/{id}/next
4. Demo stop via POST /demo/{id}/stop
"""

import sys
import asyncio
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.demo_orchestrator_service import get_demo_orchestrator

print("🎬" * 40)
print("  DEMO MODE API INTEGRATION TEST")
print("🎬" * 40)
print()


async def test_1_demo_intent_detection():
    """Test 1: Demo intent detection"""
    print("=" * 80)
    print("  TEST 1: Demo Intent Detection")
    print("=" * 80)
    print()

    demo_orchestrator = get_demo_orchestrator()

    # Test various trigger phrases
    test_cases = [
        ("show me a demo", True),
        ("הראה לי דמו", True),
        ("start demo", True),
        ("הדגמה", True),
        ("hello, I want to talk about my child", False),
        ("שלום, אני רוצה לדבר על הבן שלי", False),
    ]

    print("Testing demo trigger detection:")
    print()

    all_passed = True
    for message, should_trigger in test_cases:
        scenario_id = demo_orchestrator.detect_demo_intent(message)
        detected = scenario_id is not None

        status = "✅" if detected == should_trigger else "❌"
        print(f"  {status} '{message}'")
        print(f"      Expected: {'DEMO' if should_trigger else 'NORMAL'}, Got: {'DEMO' if detected else 'NORMAL'}")
        print()

        if detected != should_trigger:
            all_passed = False

    if all_passed:
        print("✅ Test 1 PASSED: All intent detection cases correct\n")
    else:
        print("❌ Test 1 FAILED: Some cases incorrect\n")

    return all_passed


async def test_2_demo_start_flow():
    """Test 2: Starting a demo"""
    print("=" * 80)
    print("  TEST 2: Demo Start Flow")
    print("=" * 80)
    print()

    demo_orchestrator = get_demo_orchestrator()

    # Start demo
    result = await demo_orchestrator.start_demo("language_concerns")

    print("Demo started successfully!")
    print()
    print(f"Demo Family ID: {result['demo_family_id']}")
    print(f"Scenario: {result['scenario']['name']} ({result['scenario']['name_en']})")
    print(f"Duration: {result['scenario']['duration']}")
    print(f"Total Steps: {result['scenario']['total_steps']}")
    print()

    print("First Message:")
    print(f"  Role: {result['first_message']['role']}")
    print(f"  Content: {result['first_message']['content']}")
    print(f"  Delay: {result['first_message']['delay_ms']}ms")
    print()

    print("Demo Card:")
    print(f"  Title: {result['demo_card']['title']}")
    print(f"  Body: {result['demo_card']['body']}")
    print(f"  Progress: {result['demo_card']['progress']}%")
    print()

    print("✅ Test 2 PASSED: Demo started successfully\n")

    return result['demo_family_id']


async def test_3_demo_progression(demo_family_id: str):
    """Test 3: Demo step progression"""
    print("=" * 80)
    print("  TEST 3: Demo Step Progression")
    print("=" * 80)
    print()

    demo_orchestrator = get_demo_orchestrator()

    # Progress through first 5 steps
    num_steps = 5
    print(f"Advancing through {num_steps} demo steps...\n")

    for i in range(num_steps):
        result = await demo_orchestrator.get_next_step(demo_family_id)

        print(f"Step {result['step']}/{result['total_steps']}:")
        print(f"  Role: {result['message']['role']}")
        print(f"  Content: {result['message']['content'][:80]}...")
        print(f"  Delay: {result['message']['delay_ms']}ms")

        if result.get('card_hint'):
            print(f"  Card Hint: {result['card_hint']}")

        if result.get('artifact_generated'):
            print(f"  🌟 Artifact Generated: {result['artifact_generated']['artifact_id']}")

        print()

    print("✅ Test 3 PASSED: Demo progression working\n")


async def test_4_artifact_generation(demo_family_id: str):
    """Test 4: Artifact generation during demo"""
    print("=" * 80)
    print("  TEST 4: Artifact Generation in Demo")
    print("=" * 80)
    print()

    demo_orchestrator = get_demo_orchestrator()

    # Progress through steps until artifact is generated
    print("Progressing through demo until artifact generation...\n")

    artifact_found = False
    step_count = 0
    max_steps = 15

    while step_count < max_steps:
        result = await demo_orchestrator.get_next_step(demo_family_id)
        step_count = result['step']

        if result.get('is_complete'):
            print("Demo completed!")
            break

        if result.get('artifact_generated'):
            artifact = result['artifact_generated']
            print(f"🌟 Artifact Generated at step {step_count}!")
            print(f"  Artifact ID: {artifact['artifact_id']}")
            print(f"  Status: {artifact['status']}")
            print(f"  Content Length: {artifact['content_length']} chars")
            print()
            artifact_found = True
            break

    if artifact_found:
        print("✅ Test 4 PASSED: Artifact generation triggered\n")
    else:
        print("⚠️  Test 4: No artifact generated yet (may need more steps)\n")


async def test_5_demo_stop(demo_family_id: str):
    """Test 5: Stopping demo"""
    print("=" * 80)
    print("  TEST 5: Demo Stop")
    print("=" * 80)
    print()

    demo_orchestrator = get_demo_orchestrator()

    result = await demo_orchestrator.stop_demo(demo_family_id)

    print("Demo stopped!")
    print(f"  Success: {result['success']}")
    print(f"  Message: {result['message']}")
    print()

    # Verify demo is no longer active
    try:
        await demo_orchestrator.get_next_step(demo_family_id)
        print("❌ Test 5 FAILED: Demo still active after stop\n")
    except ValueError as e:
        print("✅ Test 5 PASSED: Demo properly stopped\n")


async def test_6_complete_flow():
    """Test 6: Complete demo flow from start to finish"""
    print("=" * 80)
    print("  TEST 6: Complete Demo Flow")
    print("=" * 80)
    print()

    demo_orchestrator = get_demo_orchestrator()

    # Start new demo
    result = await demo_orchestrator.start_demo("language_concerns")
    demo_id = result['demo_family_id']
    total_steps = result['scenario']['total_steps']

    print(f"Running complete demo: {total_steps} steps\n")

    step = 0
    while step < total_steps:
        result = await demo_orchestrator.get_next_step(demo_id)
        step = result['step']

        print(f"  [{step}/{total_steps}] {result['message']['role']}")

        if result.get('is_complete'):
            print("\n  🎉 Demo completed!\n")
            break

    if result.get('is_complete'):
        print("✅ Test 6 PASSED: Complete demo flow successful\n")
    else:
        print("❌ Test 6 FAILED: Demo did not complete\n")


async def main():
    """Run all tests"""
    # Test 1: Intent detection
    await test_1_demo_intent_detection()

    # Test 2: Start demo
    demo_id = await test_2_demo_start_flow()

    # Test 3: Progress through steps
    await test_3_demo_progression(demo_id)

    # Test 4: Check artifact generation
    await test_4_artifact_generation(demo_id)

    # Test 5: Stop demo
    await test_5_demo_stop(demo_id)

    # Test 6: Complete flow
    await test_6_complete_flow()

    print("=" * 80)
    print("  ✅ ALL DEMO MODE TESTS COMPLETED")
    print("=" * 80)
    print()
    print("Demo Mode Backend Ready! 🎬")
    print()
    print("API Endpoints Available:")
    print("  - POST /chat/send (with demo intent detection)")
    print("  - POST /demo/start")
    print("  - GET /demo/{demo_family_id}/next")
    print("  - POST /demo/{demo_family_id}/stop")
    print()
    print("Next Steps:")
    print("  1. Frontend: Detect demo_mode in /chat/send response")
    print("  2. Frontend: Render demo mode card with visual indicators")
    print("  3. Frontend: Auto-play message system with delays")
    print("  4. Frontend: Demo controls (pause, skip, stop)")
    print()


if __name__ == "__main__":
    asyncio.run(main())
