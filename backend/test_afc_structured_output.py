"""
Quick test to verify AFC is disabled in structured output
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.llm.gemini_provider import GeminiProvider
from app.services.llm.base import Message
import os

async def test_afc_disabled():
    """Test that AFC is properly disabled in structured output"""

    # Create provider
    api_key = os.getenv("GEMINI_API_KEY", "test")
    provider = GeminiProvider(api_key=api_key, model="gemini-2.5-flash")

    print("🧪 Testing structured output with AFC disabled...")

    # Simple schema with array of objects
    schema = {
        "type": "object",
        "properties": {
            "child_name": {"type": "string"},
            "vocabulary_map": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "term": {"type": "string"},
                        "translation": {"type": "string"}
                    },
                    "required": ["term", "translation"]
                }
            }
        },
        "required": ["child_name", "vocabulary_map"]
    }

    messages = [
        Message(role="user", content="Extract: Child name is דני. Parent says 'מתפוצץ' for tantrum, 'מרחף' for distracted.")
    ]

    try:
        result = await provider.chat_with_structured_output(
            messages=messages,
            response_schema=schema
        )

        print("✅ SUCCESS! Structured output returned:")
        print(f"   Child: {result.get('child_name')}")
        print(f"   Vocabulary: {result.get('vocabulary_map')}")

        return True

    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_afc_disabled())
    sys.exit(0 if success else 1)
