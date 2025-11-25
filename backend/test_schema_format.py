"""
Test to confirm the schema format issue:
- Gemini SDK requires types.Schema format, not plain dicts
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from app.services.llm.factory import create_llm_provider
from app.services.llm.base import Message
from google.genai import types

async def test_schema_formats():
    """Test both schema formats to identify the issue"""

    strong_model = os.getenv("STRONG_LLM_MODEL", "gemini-3-pro-preview")
    print(f"Testing model: {strong_model}\n")

    llm = create_llm_provider(
        provider_type="gemini",
        model=strong_model,
        use_enhanced=False
    )

    messages = [
        Message(role="user", content="Generate 3 scenarios for a child named דני, age 3, with speech concerns.")
    ]

    # Test 1: Plain dict schema (current artifact_generation_service format)
    print("=" * 80)
    print("TEST 1: Plain Dict Schema (JSON Schema format)")
    print("=" * 80)

    plain_dict_schema = {
        "type": "object",
        "properties": {
            "scenarios": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "category": {"type": "string"},
                        "what_to_film": {"type": "string"}
                    },
                    "required": ["title", "what_to_film"]
                }
            }
        },
        "required": ["scenarios"]
    }

    try:
        result1 = await llm.chat_with_structured_output(
            messages=messages,
            response_schema=plain_dict_schema,
            temperature=0.7
        )
        print(f"✅ Plain Dict Schema SUCCESS")
        print(f"Result: {result1}")
        print(f"Scenarios count: {len(result1.get('scenarios', []))}")
    except Exception as e:
        print(f"❌ Plain Dict Schema FAILED: {e}")
        import traceback
        traceback.print_exc()

    print("\n")

    # Test 2: Native types.Schema (test format that works)
    print("=" * 80)
    print("TEST 2: Native types.Schema (Gemini native format)")
    print("=" * 80)

    native_schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "scenarios": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "title": types.Schema(type=types.Type.STRING),
                        "category": types.Schema(type=types.Type.STRING),
                        "what_to_film": types.Schema(type=types.Type.STRING),
                    },
                    required=["title", "what_to_film"]
                )
            )
        },
        required=["scenarios"]
    )

    try:
        result2 = await llm.chat_with_structured_output(
            messages=messages,
            response_schema=native_schema,
            temperature=0.7
        )
        print(f"✅ Native Schema SUCCESS")
        print(f"Result: {result2}")
        print(f"Scenarios count: {len(result2.get('scenarios', []))}")
    except Exception as e:
        print(f"❌ Native Schema FAILED: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)
    print("CONCLUSION:")
    print("=" * 80)
    print("If Test 1 fails and Test 2 succeeds, the issue is schema format!")
    print("artifact_generation_service needs to use types.Schema, not plain dicts")

if __name__ == "__main__":
    asyncio.run(test_schema_formats())
