"""
Test if gemini-flash-latest also has thought_signature
"""
import asyncio
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

async def test_flash_thought():
    """Test both flash and pro models for thought_signature"""
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    models = [
        "gemini-flash-latest",
        "gemini-2.5-flash",
        "gemini-3-pro-preview"
    ]

    for model in models:
        print("=" * 80)
        print(f"Testing: {model}")
        print("=" * 80)

        try:
            response = await client.aio.models.generate_content(
                model=model,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part(text="שלום! מה שלומך?")]
                    )
                ],
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=500
                )
            )

            print(f"Model: {model}")

            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]

                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts'):
                        print(f"Number of parts: {len(candidate.content.parts)}")

                        for i, part in enumerate(candidate.content.parts):
                            part_type = str(type(part))
                            print(f"  Part {i}: {part_type}")

                            has_text = hasattr(part, 'text') and part.text
                            has_thought = hasattr(part, 'thought')

                            print(f"    Has text: {has_text}")
                            print(f"    Has thought_signature: {has_thought}")

                            if has_text:
                                print(f"    Text preview: {part.text[:80]}...")

            print(f"\nresponse.text exists: {hasattr(response, 'text')}")
            if hasattr(response, 'text'):
                print(f"response.text preview: {response.text[:80] if response.text else 'None'}...")

        except Exception as e:
            print(f"❌ Error with {model}: {e}")

        print()

if __name__ == "__main__":
    asyncio.run(test_flash_thought())
