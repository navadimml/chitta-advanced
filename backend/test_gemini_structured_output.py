"""
Test if Gemini 3 Pro can handle structured output
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from app.services.llm.factory import create_llm_provider
from app.services.llm.base import Message

async def test_structured_output():
    """Test if Gemini 3 Pro works with structured output"""

    # Create provider with strong model
    strong_model = os.getenv("STRONG_LLM_MODEL", "gemini-3-pro-preview")
    print(f"Testing model: {strong_model}")

    llm = create_llm_provider(
        provider_type="gemini",
        model=strong_model,
        use_enhanced=False
    )

    print(f"Provider created: {llm.model_name}")

    # Simple schema test
    simple_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "number"},
            "concerns": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["name", "age"]
    }

    messages = [
        Message(role="system", content="Extract information about the child."),
        Message(role="user", content="דני בן 3, יש לו קשיים בדיבור ובאינטראקציה חברתית.")
    ]

    print("\nTesting simple schema...")
    try:
        result = await llm.chat_with_structured_output(
            messages=messages,
            response_schema=simple_schema,
            temperature=0.7
        )
        print(f"✅ Simple schema SUCCESS: {result}")
    except Exception as e:
        print(f"❌ Simple schema FAILED: {e}")
        import traceback
        traceback.print_exc()

    # Test with actual guidelines schema (simplified)
    from google.genai import types

    guidelines_schema = types.Schema(
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

    messages2 = [
        Message(role="system", content="Generate 3 video filming guidelines for a child with speech and social concerns."),
        Message(role="user", content="Child: דני, age 3, concerns: speech, social")
    ]

    print("\nTesting guidelines schema...")
    try:
        result2 = await llm.chat_with_structured_output(
            messages=messages2,
            response_schema=guidelines_schema,
            temperature=0.7
        )
        print(f"✅ Guidelines schema SUCCESS: {result2}")
        if 'scenarios' in result2:
            print(f"   Generated {len(result2['scenarios'])} scenarios")
    except Exception as e:
        print(f"❌ Guidelines schema FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_structured_output())
