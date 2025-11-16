#!/usr/bin/env python3
"""
Enhanced Test Script for Improved Function Calling

This script tests the enhanced function calling system with:
1. Lite prompts for less capable models
2. Fallback extraction mechanisms
3. Function calling monitoring
4. Comparison between standard and enhanced modes

Usage:
    # Test with Flash model (automatically uses lite mode)
    LLM_MODEL=gemini-2.5-flash python test_gemini_interview_enhanced.py

    # Test with Pro model (uses full mode)
    LLM_MODEL=gemini-2.5-pro python test_gemini_interview_enhanced.py

    # Force enhanced mode off for comparison
    LLM_USE_ENHANCED=false python test_gemini_interview_enhanced.py
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import List

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Load environment variables
from dotenv import load_dotenv
env_path = backend_dir / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded environment from: {env_path}")
else:
    print(f"⚠️  .env file not found at: {env_path}")

# Setup logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(name)s - %(levelname)s - %(message)s'
)

# Silence noisy loggers
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('google_genai').setLevel(logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.WARNING)

# Keep our app logs at INFO level
logging.getLogger('app.services.llm').setLevel(logging.INFO)

from app.services.llm.factory import create_llm_provider, get_provider_info
from app.services.llm.base import Message
from app.prompts.interview_prompt import build_interview_prompt
from app.prompts.interview_prompt_lite import build_interview_prompt_lite
from app.prompts.interview_functions import INTERVIEW_FUNCTIONS
from app.prompts.interview_functions_lite import (
    INTERVIEW_FUNCTIONS_LITE,
    should_use_lite_functions,
    get_appropriate_functions
)


async def test_basic_function_calling(use_lite: bool = False):
    """Test basic function calling with optional lite mode"""
    mode = "LITE" if use_lite else "FULL"
    print("\n" + "="*60)
    print(f"TEST: Basic Function Calling ({mode} mode)")
    print("="*60)

    llm = create_llm_provider()
    model_name = getattr(llm, 'model_name', 'unknown')
    print(f"✅ Provider: {llm.get_provider_name()}")
    print(f"   Model: {model_name}")

    # Choose appropriate prompt and functions
    if use_lite:
        system_prompt = build_interview_prompt_lite(
            child_name="unknown",
            age="unknown",
            gender="unknown"
        )
        functions = INTERVIEW_FUNCTIONS_LITE
        print("   Using: LITE prompt + LITE functions")
    else:
        system_prompt = build_interview_prompt(
            child_name="unknown",
            age="unknown",
            gender="unknown"
        )
        functions = INTERVIEW_FUNCTIONS
        print("   Using: FULL prompt + FULL functions")

    # Test message with clear data to extract
    messages = [
        Message(role="system", content=system_prompt),
        Message(role="user", content="השם שלו יוני והוא בן 3.5 ואני מודאגת לגבי הדיבור שלו")
    ]

    print(f"\n📨 User message: {messages[1].content}\n")
    print("Expected: Should call extract_interview_data with name, age, gender, concerns")

    response = await llm.chat(
        messages,
        functions=functions,
        temperature=0.7,
        max_tokens=10000
    )

    print(f"\n📝 Response: {response.content[:200]}...")
    print(f"\n🔧 Function calls: {len(response.function_calls)}")

    success = False
    if response.function_calls:
        for i, fc in enumerate(response.function_calls, 1):
            print(f"\n  Function {i}: {fc.name}")
            print(f"  Arguments: {fc.arguments}")

            if fc.name == "extract_interview_data":
                args = fc.arguments
                checks = []

                if args.get("child_name"):
                    checks.append(f"✅ Child name: {args['child_name']}")
                else:
                    checks.append("❌ Child name: MISSING")

                if args.get("age"):
                    checks.append(f"✅ Age: {args['age']}")
                else:
                    checks.append("❌ Age: MISSING")

                if args.get("gender"):
                    checks.append(f"✅ Gender: {args['gender']}")
                else:
                    checks.append("❌ Gender: MISSING")

                concerns = args.get("primary_concerns") or args.get("concerns") or []
                if concerns:
                    checks.append(f"✅ Concerns: {concerns}")
                else:
                    checks.append("❌ Concerns: MISSING")

                print("\n  Extraction check:")
                for check in checks:
                    print(f"     {check}")

                success = all("✅" in check for check in checks)
    else:
        print("  ⚠️  WARNING: No function calls made!")
        print("  Expected: extract_interview_data should be called")

    # Show statistics if enhanced mode
    if hasattr(llm, 'get_statistics'):
        stats = llm.get_statistics()
        print(f"\n📊 Enhanced Mode Statistics:")
        print(f"   Success rate: {stats['success_rate']:.1f}%")
        print(f"   Fallback rate: {stats['fallback_rate']:.1f}%")

    return success


async def test_multi_turn_with_monitoring():
    """Test multi-turn conversation with function call monitoring"""
    print("\n" + "="*60)
    print("TEST: Multi-Turn Conversation with Monitoring")
    print("="*60)

    llm = create_llm_provider()
    model_name = getattr(llm, 'model_name', 'unknown')

    # Use lite mode for flash models
    use_lite = should_use_lite_functions(model_name)
    print(f"✅ Provider: {llm.get_provider_name()}")
    print(f"   Auto-detected lite mode: {use_lite}")

    # Get appropriate functions
    functions = get_appropriate_functions(model_name)

    # Build prompt (lite for Flash, full for others)
    if use_lite:
        system_prompt = build_interview_prompt_lite(
            child_name="יוני",
            age="3.5",
            gender="male",
            concerns=["speech"],
            completeness=0.15
        )
    else:
        system_prompt = build_interview_prompt(
            child_name="יוני",
            age="3.5",
            gender="male",
            concerns=["speech"],
            completeness=0.15
        )

    # Simulate multiple turns
    turns = [
        "השם שלו יוני והוא בן 3.5",
        "הוא אוהב לשחק ברכבות ולבנות דברים",
        "אבל הדיבור שלו ממש חלש, רק מילים בודדות כמו אמא, אבא, מים",
        "הוא כמעט לא מסתכל בעיניים כשמדברים איתו",
        "אני מודאגת כי הוא לא משחק עם ילדים אחרים בגן"
    ]

    conversation = [Message(role="system", content=system_prompt)]
    function_calls_per_turn = []

    print("\nRunning 5 conversation turns...\n")

    for turn_num, user_msg in enumerate(turns, 1):
        print(f"--- Turn {turn_num} ---")
        print(f"User: {user_msg}")

        conversation.append(Message(role="user", content=user_msg))

        response = await llm.chat(
            conversation,
            functions=functions,
            temperature=0.7,
            max_tokens=10000
        )

        # Track function calls
        num_calls = len(response.function_calls)
        function_calls_per_turn.append(num_calls)

        if response.function_calls:
            print(f"✅ Function calls: {num_calls}")
            for fc in response.function_calls:
                if fc.name == "extract_interview_data":
                    print(f"   Extracted: {list(fc.arguments.keys())}")
        else:
            print(f"⚠️  No function calls (fallback may have kicked in)")

        conversation.append(Message(role="assistant", content=response.content))
        print(f"Assistant: {response.content[:100]}...\n")

    # Summary
    total_calls = sum(function_calls_per_turn)
    print("\n" + "-"*60)
    print(f"Summary: {total_calls} function calls across {len(turns)} turns")
    print(f"Function calls per turn: {function_calls_per_turn}")

    if total_calls >= 4:
        print("✅ PASS: Good function calling consistency")
    elif total_calls >= 2:
        print("⚠️  PARTIAL: Some function calls made, but could be better")
    else:
        print("❌ FAIL: Very few function calls - check fallback extraction")

    # Show statistics if enhanced mode
    if hasattr(llm, 'get_statistics'):
        stats = llm.get_statistics()
        print(f"\n📊 Enhanced Mode Statistics:")
        print(f"   Total calls: {stats['total_calls']}")
        print(f"   Function calls made: {stats['function_calls_made']}")
        print(f"   Fallback extractions: {stats['fallback_extractions']}")
        print(f"   Failed extractions: {stats['failed_extractions']}")
        print(f"   Success rate: {stats['success_rate']:.1f}%")
        print(f"   Fallback rate: {stats['fallback_rate']:.1f}%")

    return total_calls >= 4


async def test_comparison_standard_vs_enhanced():
    """Compare standard vs enhanced provider performance"""
    print("\n" + "="*60)
    print("TEST: Standard vs Enhanced Mode Comparison")
    print("="*60)

    test_message = "השם שלה מיה והיא בת 4 ולא משחקת עם ילדים אחרים"

    results = {}

    # Test 1: Standard mode (no enhancement)
    print("\n--- Testing STANDARD mode (no enhancement) ---")
    os.environ["LLM_USE_ENHANCED"] = "false"

    llm_standard = create_llm_provider()
    print(f"Provider: {llm_standard.get_provider_name()}")

    messages = [
        Message(role="system", content=build_interview_prompt()),
        Message(role="user", content=test_message)
    ]

    response_standard = await llm_standard.chat(
        messages,
        functions=INTERVIEW_FUNCTIONS,
        temperature=0.7,
        max_tokens=10000
    )

    results['standard'] = {
        'function_calls': len(response_standard.function_calls),
        'extracted_data': response_standard.function_calls[0].arguments if response_standard.function_calls else {}
    }

    print(f"Function calls: {results['standard']['function_calls']}")

    # Test 2: Enhanced mode
    print("\n--- Testing ENHANCED mode (with fallback) ---")
    os.environ["LLM_USE_ENHANCED"] = "true"

    llm_enhanced = create_llm_provider()
    print(f"Provider: {llm_enhanced.get_provider_name()}")

    messages = [
        Message(role="system", content=build_interview_prompt()),
        Message(role="user", content=test_message)
    ]

    response_enhanced = await llm_enhanced.chat(
        messages,
        functions=INTERVIEW_FUNCTIONS,
        temperature=0.7,
        max_tokens=10000
    )

    results['enhanced'] = {
        'function_calls': len(response_enhanced.function_calls),
        'extracted_data': response_enhanced.function_calls[0].arguments if response_enhanced.function_calls else {}
    }

    print(f"Function calls: {results['enhanced']['function_calls']}")

    # Show statistics for enhanced
    if hasattr(llm_enhanced, 'get_statistics'):
        stats = llm_enhanced.get_statistics()
        print(f"Fallback extractions: {stats['fallback_extractions']}")

    # Comparison
    print("\n" + "-"*60)
    print("COMPARISON:")
    print(f"Standard mode: {results['standard']['function_calls']} function calls")
    print(f"Enhanced mode: {results['enhanced']['function_calls']} function calls")

    if results['enhanced']['function_calls'] >= results['standard']['function_calls']:
        print("✅ Enhanced mode performed equal or better!")
    else:
        print("⚠️  Enhanced mode performed worse (unexpected)")

    return results['enhanced']['function_calls'] > 0


async def main():
    """Run all enhanced tests"""
    print("\n" + "🧪" * 30)
    print(" ENHANCED FUNCTION CALLING TEST SUITE")
    print("🧪" * 30)

    # Check provider configuration
    provider_info = get_provider_info()
    print(f"\n📋 Provider Configuration:")
    print(f"   Configured: {provider_info['configured_provider']}")
    print(f"   Model: {provider_info['configured_model']}")
    print(f"   Enhanced mode: {os.getenv('LLM_USE_ENHANCED', 'true')}")
    print(f"   Will use: {provider_info['will_use']}")

    if not provider_info['available_providers']['gemini']:
        print("\n⚠️  WARNING: GEMINI_API_KEY not found")
        print("   Add your API key to .env:")
        print("   GEMINI_API_KEY=your_actual_key")
        return 1

    try:
        # Run tests
        print("\n" + "="*60)
        print("Starting Tests...")
        print("="*60)

        # Test 1: Basic with LITE mode
        success1 = await test_basic_function_calling(use_lite=True)

        # Test 2: Basic with FULL mode
        success2 = await test_basic_function_calling(use_lite=False)

        # Test 3: Multi-turn with monitoring
        success3 = await test_multi_turn_with_monitoring()

        # Test 4: Comparison
        success4 = await test_comparison_standard_vs_enhanced()

        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        results = [
            ("Basic Function Calling (LITE)", success1),
            ("Basic Function Calling (FULL)", success2),
            ("Multi-Turn with Monitoring", success3),
            ("Standard vs Enhanced Comparison", success4)
        ]

        passed = sum(1 for _, success in results if success)
        total = len(results)

        for test_name, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {status}: {test_name}")

        print(f"\nOverall: {passed}/{total} tests passed")

        if passed == total:
            print("\n🎉 All tests passed!")
            return 0
        else:
            print(f"\n⚠️  {total - passed} test(s) failed")
            return 1

    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
