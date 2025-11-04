#!/usr/bin/env python3
"""
Test Script for Gemini Interview Implementation

Run this locally with your real GEMINI_API_KEY to test:
1. Basic chat with Gemini
2. Function calling with interview data extraction
3. Multi-turn conversation with continuous extraction

Usage:
    python test_gemini_interview.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.llm.factory import create_llm_provider, get_provider_info
from app.services.llm.base import Message
from app.prompts.interview_prompt import build_interview_prompt
from app.prompts.interview_functions import INTERVIEW_FUNCTIONS


async def test_basic_chat():
    """Test 1: Basic chat with Gemini"""
    print("\n" + "="*60)
    print("TEST 1: Basic Chat with Gemini")
    print("="*60)

    # Create Gemini provider
    llm = create_llm_provider()
    print(f"✅ Provider initialized: {llm.get_provider_name()}\n")

    # Simple test message
    messages = [
        Message(role="system", content="You are a helpful assistant."),
        Message(role="user", content="Hello! Please respond in Hebrew: Say 'שלום! אני עובד/ת'")
    ]

    print("Sending test message...")
    response = await llm.chat(messages, temperature=0.7, max_tokens=100)

    print(f"\n📝 Response: {response.content}")
    print(f"🏁 Finish reason: {response.finish_reason}")
    print(f"🔧 Function calls: {len(response.function_calls)}")

    return response


async def test_function_calling():
    """Test 2: Function calling with interview data extraction"""
    print("\n" + "="*60)
    print("TEST 2: Function Calling - Interview Data Extraction")
    print("="*60)

    llm = create_llm_provider()

    # Build interview prompt
    system_prompt = build_interview_prompt(
        child_name="unknown",
        age="unknown",
        gender="unknown",
        concerns=[],
        completeness=0.0
    )

    # Parent's first message with clear data to extract
    messages = [
        Message(role="system", content=system_prompt),
        Message(role="user", content="היי, שמי רונית והילד שלי קוראים לו יוני, הוא בן 3.5 ואני מודאגת לגבי הדיבור שלו")
    ]

    print("Sending message with extractable data...")
    print(f"User message: {messages[1].content}\n")

    response = await llm.chat(
        messages,
        functions=INTERVIEW_FUNCTIONS,
        temperature=0.7,
        max_tokens=500
    )

    print(f"📝 Response content: {response.content}\n")
    print(f"🔧 Function calls: {len(response.function_calls)}")

    if response.function_calls:
        for i, fc in enumerate(response.function_calls, 1):
            print(f"\n  Function {i}: {fc.name}")
            print(f"  Arguments: {fc.arguments}")

            # Validate extraction
            if fc.name == "extract_interview_data":
                args = fc.arguments
                print("\n  ✅ Extracted data:")
                if args.get("child_name"):
                    print(f"     - Child name: {args['child_name']}")
                if args.get("age"):
                    print(f"     - Age: {args['age']}")
                if args.get("gender"):
                    print(f"     - Gender: {args['gender']}")
                if args.get("primary_concerns"):
                    print(f"     - Concerns: {args['primary_concerns']}")
    else:
        print("  ⚠️  WARNING: No function calls made!")
        print("  Expected: extract_interview_data to be called")

    return response


async def test_multi_turn_conversation():
    """Test 3: Multi-turn conversation with continuous extraction"""
    print("\n" + "="*60)
    print("TEST 3: Multi-Turn Conversation with Continuous Extraction")
    print("="*60)

    llm = create_llm_provider()

    # Build interview prompt
    system_prompt = build_interview_prompt(
        child_name="יוני",
        age="3.5",
        gender="male",
        concerns=["speech"],
        completeness=0.15,
        context_summary="Parent mentioned child's name (יוני, age 3.5, male) and concern about speech."
    )

    # Simulate conversation turns
    conversation = [
        Message(role="system", content=system_prompt),
        Message(role="user", content="היי, אני רונית. הילד שלי יוני, בן 3.5"),
        Message(role="assistant", content="שלום רונית! נעים מאוד. ספרי לי על יוני - במה הוא אוהב לעסוק?"),
        Message(role="user", content="הוא אוהב מאוד רכבות ובניית דברים. אבל הדיבור שלו ממש חלש, רק מילים בודדות")
    ]

    print("Conversation so far:")
    for msg in conversation[1:]:  # Skip system
        print(f"  {msg.role.upper()}: {msg.content}")

    print("\nSending latest message with functions...")

    response = await llm.chat(
        conversation,
        functions=INTERVIEW_FUNCTIONS,
        temperature=0.7,
        max_tokens=500
    )

    print(f"\n📝 Assistant response: {response.content}\n")
    print(f"🔧 Function calls: {len(response.function_calls)}")

    if response.function_calls:
        for i, fc in enumerate(response.function_calls, 1):
            print(f"\n  Function {i}: {fc.name}")
            if fc.name == "extract_interview_data":
                args = fc.arguments
                print("  ✅ Extracted in this turn:")
                if args.get("strengths"):
                    print(f"     - Strengths: {args['strengths']}")
                if args.get("primary_concerns"):
                    print(f"     - Concerns added: {args['primary_concerns']}")
                if args.get("concern_details"):
                    print(f"     - Details: {args['concern_details']}")

    return response


async def test_completeness_check():
    """Test 4: Interview completeness evaluation"""
    print("\n" + "="*60)
    print("TEST 4: Interview Completeness Check")
    print("="*60)

    llm = create_llm_provider()

    # Simulate nearly complete interview
    system_prompt = build_interview_prompt(
        child_name="יוני",
        age="3.5",
        gender="male",
        concerns=["speech", "social"],
        completeness=0.75,
        context_summary="""
        Gathered so far:
        - Child: יוני, 3.5 years, male
        - Concerns: Speech (only single words), social (limited eye contact)
        - Strengths: Loves trains, building
        - Daily routine: Goes to gan, plays alone mostly
        - Family: Has older sister
        - Parent goal: Want him to communicate better
        """
    )

    conversation = [
        Message(role="system", content=system_prompt),
        Message(role="user", content="אני חושבת שזה הכל, אין לי יותר מה להוסיף")
    ]

    print("Parent signals they're done")
    print("Expected: LLM should call check_interview_completeness\n")

    response = await llm.chat(
        conversation,
        functions=INTERVIEW_FUNCTIONS,
        temperature=0.7,
        max_tokens=500
    )

    print(f"📝 Response: {response.content}\n")

    if response.function_calls:
        for fc in response.function_calls:
            if fc.name == "check_interview_completeness":
                print("✅ Interview completeness check called!")
                print(f"   Ready to complete: {fc.arguments.get('ready_to_complete')}")
                print(f"   Completeness: {fc.arguments.get('completeness_estimate')}%")
                if fc.arguments.get('missing_critical_info'):
                    print(f"   Missing: {fc.arguments['missing_critical_info']}")
    else:
        print("⚠️  No completeness check function called")

    return response


async def main():
    """Run all tests"""
    print("\n" + "🧪" * 30)
    print(" GEMINI INTERVIEW IMPLEMENTATION TEST SUITE")
    print("🧪" * 30)

    # Check provider configuration
    provider_info = get_provider_info()
    print(f"\n📋 Provider Configuration:")
    print(f"   - Configured: {provider_info['configured_provider']}")
    print(f"   - Model: {provider_info['model']}")
    print(f"   - API Key Set: {provider_info['api_key_set']}")

    if provider_info['configured_provider'] != 'gemini':
        print("\n⚠️  WARNING: LLM_PROVIDER is not set to 'gemini'")
        print("   Update your .env file:")
        print("   LLM_PROVIDER=gemini")
        print("   GEMINI_API_KEY=your_actual_key")
        print("\n   Continuing with current provider...\n")

    try:
        # Run tests
        await test_basic_chat()
        await test_function_calling()
        await test_multi_turn_conversation()
        await test_completeness_check()

        print("\n" + "="*60)
        print("✅ All tests completed!")
        print("="*60)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
