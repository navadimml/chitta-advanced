#!/usr/bin/env python3
"""
Test to reproduce the family_id inconsistency bug in test mode.

The bug: Chitta forgets name and age mid-conversation because
different family_ids are being used for the same test session.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv()

from app.core.app_state import app_state
from app.services.parent_simulator import get_parent_simulator
from app.services.conversation_service_simplified import get_simplified_conversation_service
from app.services.llm.factory import create_llm_provider


async def test_family_id_consistency():
    """
    Reproduce the amnesia bug by tracking family_ids throughout a test session.
    """
    print("\n" + "=" * 80)
    print("🐛 FAMILY ID CONSISTENCY BUG TEST")
    print("=" * 80)

    # Initialize app
    if not app_state.initialized:
        await app_state.initialize()

    # Get services
    simulator = get_parent_simulator()
    conversation_service = get_simplified_conversation_service()

    # === STEP 1: Start test mode ===
    print("\n📍 STEP 1: Starting test mode with persona 'dani_anxious_questioner'")
    persona_id = "dani_anxious_questioner"

    # Simulate /test/start endpoint
    existing_family_id = simulator.get_active_simulation_for_persona(persona_id)
    if existing_family_id:
        family_id = existing_family_id
        print(f"   ♻️ Reusing existing simulation: {family_id}")
    else:
        family_id = f"test_{persona_id}"
        print(f"   🆕 Creating new simulation: {family_id}")

    result = simulator.start_simulation(persona_id, family_id)
    print(f"   ✅ Test started with family_id: {family_id}")
    print(f"   📋 Persona: {result['persona']['parent_name']}, Child: {result['persona']['child_name']} ({result['persona']['child_age']} years)")

    # === STEP 2: First message - Chitta's greeting ===
    print("\n📍 STEP 2: Sending Chitta's first message")
    chitta_message_1 = "שלום! שמי צ'יטה. אשמח להכיר את הילד או הילדה שלך. מה שמו/ה ובאיזה גיל?"

    # Check what family_id is being used
    print(f"   Using family_id: {family_id}")

    # Simulate parent response
    test_llm = create_llm_provider(provider_type="gemini", model="gemini-2.5-flash")
    from app.services.mock_graphiti import get_mock_graphiti
    graphiti = get_mock_graphiti()

    parent_response_1 = await simulator.generate_response(
        family_id=family_id,
        chitta_question=chitta_message_1,
        llm_provider=test_llm,
        graphiti=graphiti
    )
    print(f"   👤 Parent response: {parent_response_1}")

    # === STEP 3: Process parent's response ===
    print("\n📍 STEP 3: Processing parent's response (extraction phase)")
    print(f"   Using family_id: {family_id}")

    result_1 = await conversation_service.process_message(
        family_id=family_id,
        user_message=parent_response_1,
        temperature=0.7
    )

    # Check what was extracted
    from app.services.session_service import get_session_service
    session_service = get_session_service()
    session_1 = session_service.get_or_create_session(family_id)
    data_1 = session_1.extracted_data

    print(f"   ✅ Chitta's response: {result_1['response'][:100]}...")
    print(f"   📊 Extracted data:")
    print(f"      - Name: {data_1.child_name}")
    print(f"      - Age: {data_1.age}")
    print(f"      - Concerns: {data_1.primary_concerns}")

    chitta_message_2 = result_1['response']

    # === STEP 4: Second exchange ===
    print("\n📍 STEP 4: Second exchange - Chitta asks follow-up")

    parent_response_2 = await simulator.generate_response(
        family_id=family_id,
        chitta_question=chitta_message_2,
        llm_provider=test_llm,
        graphiti=graphiti
    )
    print(f"   👤 Parent response: {parent_response_2}")

    print(f"\n   Processing parent's response with family_id: {family_id}")
    result_2 = await conversation_service.process_message(
        family_id=family_id,
        user_message=parent_response_2,
        temperature=0.7
    )

    # Check if data persisted
    session_2 = session_service.get_or_create_session(family_id)
    data_2 = session_2.extracted_data

    print(f"   ✅ Chitta's response: {result_2['response'][:100]}...")
    print(f"   📊 Extracted data (should still have name/age):")
    print(f"      - Name: {data_2.child_name}")
    print(f"      - Age: {data_2.age}")
    print(f"      - Concerns: {data_2.primary_concerns}")

    # === VERIFICATION ===
    print("\n" + "=" * 80)
    print("🔍 VERIFICATION")
    print("=" * 80)

    if data_2.child_name and data_2.age:
        print("✅ SUCCESS: Name and age persisted between turns!")
        print(f"   Name: {data_2.child_name}, Age: {data_2.age}")

        # Check if Chitta is asking for name/age again (the amnesia bug)
        chitta_response_lower = result_2['response'].lower()
        if ('שם' in chitta_response_lower or 'קוראים' in chitta_response_lower) and \
           ('גיל' in chitta_response_lower or 'בת כמה' in chitta_response_lower or 'בן כמה' in chitta_response_lower):
            print("❌ BUG DETECTED: Chitta is asking for name/age AGAIN even though she already knows!")
            print(f"   Chitta's response: {result_2['response']}")
            return False
        else:
            print("✅ Chitta is NOT asking for name/age again - bug NOT reproduced in this test")
            return True
    else:
        print("❌ FAILURE: Name and/or age were lost between turns!")
        print(f"   Turn 1: Name={data_1.child_name}, Age={data_1.age}")
        print(f"   Turn 2: Name={data_2.child_name}, Age={data_2.age}")
        print("   This indicates the family_id changed or sessions are not persisting")
        return False


async def main():
    """Run the test"""
    try:
        success = await test_family_id_consistency()
        if success:
            print("\n✅ Test completed - No amnesia bug detected")
            return 0
        else:
            print("\n❌ Test failed - Amnesia bug detected!")
            return 1
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
