"""
Test why Gemini 3 Pro Preview returns empty user-facing responses
"""
import asyncio
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

async def test_gemini_response():
    """Test Gemini 3 Pro Preview with simple prompt"""
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    # Test 1: Simple conversation without any special instructions
    print("=" * 80)
    print("TEST 1: Simple conversation (no thought suppression)")
    print("=" * 80)

    response = await client.aio.models.generate_content(
        model="gemini-3-pro-preview",
        contents=[
            types.Content(
                role="user",
                parts=[types.Part(text="שלום! מה שלומך?")]
            )
        ],
        config=types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=1000
        )
    )

    print(f"\nResponse type: {type(response)}")
    print(f"Has candidates: {hasattr(response, 'candidates')}")

    if hasattr(response, 'candidates') and response.candidates:
        candidate = response.candidates[0]
        print(f"Candidate finish_reason: {candidate.finish_reason if hasattr(candidate, 'finish_reason') else 'none'}")

        if hasattr(candidate, 'content') and candidate.content:
            if hasattr(candidate.content, 'parts'):
                print(f"Number of parts: {len(candidate.content.parts)}")
                for i, part in enumerate(candidate.content.parts):
                    part_type = str(type(part))
                    print(f"  Part {i}: {part_type}")

                    if hasattr(part, 'text') and part.text:
                        print(f"    Text: {part.text[:100]}")
                    if hasattr(part, 'thought') or 'ThoughtSignature' in part_type:
                        print(f"    ** THOUGHT_SIGNATURE DETECTED **")

    # Use response.text to see what SDK returns
    print(f"\nresponse.text: {response.text if hasattr(response, 'text') else 'NOT AVAILABLE'}")

    # Test 2: With explicit instruction NOT to show thinking
    print("\n" + "=" * 80)
    print("TEST 2: With instruction to NOT show thinking tags")
    print("=" * 80)

    response2 = await client.aio.models.generate_content(
        model="gemini-3-pro-preview",
        contents=[
            types.Content(
                role="user",
                parts=[types.Part(text="""**CRITICAL: Response Format**
- ❌ NEVER include internal thought processes, reasoning steps, or XML tags like <thought>, <thinking>, or similar in your response
- ❌ NEVER show your planning or decision-making process
- ✅ Respond directly to the user in natural Hebrew
- ✅ Your response should contain ONLY what the user should see

Now answer: מה שלומך?""")]
            )
        ],
        config=types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=1000
        )
    )

    print(f"\nResponse type: {type(response2)}")
    if hasattr(response2, 'candidates') and response2.candidates:
        candidate = response2.candidates[0]
        print(f"Candidate finish_reason: {candidate.finish_reason if hasattr(candidate, 'finish_reason') else 'none'}")

        if hasattr(candidate, 'content') and candidate.content:
            if hasattr(candidate.content, 'parts'):
                print(f"Number of parts: {len(candidate.content.parts)}")
                for i, part in enumerate(candidate.content.parts):
                    part_type = str(type(part))
                    print(f"  Part {i}: {part_type}")

                    if hasattr(part, 'text') and part.text:
                        print(f"    Text: {part.text[:100]}")
                    if hasattr(part, 'thought') or 'ThoughtSignature' in part_type:
                        print(f"    ** THOUGHT_SIGNATURE DETECTED **")

    print(f"\nresponse.text: {response2.text if hasattr(response2, 'text') else 'NOT AVAILABLE'}")

    # Test 3: Check if thought_signature can be disabled via config
    print("\n" + "=" * 80)
    print("TEST 3: Attempting to disable thought_signature via config")
    print("=" * 80)

    # Try various config options that might disable thought_signature
    try:
        response3 = await client.aio.models.generate_content(
            model="gemini-3-pro-preview",
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part(text="מה שלומך?")]
                )
            ],
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=1000,
                # Try system_instruction to guide behavior
                system_instruction="You are a helpful assistant. Respond naturally in Hebrew without any internal reasoning or thought processes."
            )
        )

        print(f"\nWith system_instruction:")
        if hasattr(response3, 'candidates') and response3.candidates:
            candidate = response3.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                if hasattr(candidate.content, 'parts'):
                    print(f"Number of parts: {len(candidate.content.parts)}")
                    for i, part in enumerate(candidate.content.parts):
                        part_type = str(type(part))
                        print(f"  Part {i}: {part_type}")

                        if hasattr(part, 'text') and part.text:
                            print(f"    Text: {part.text[:100]}")
                        if hasattr(part, 'thought') or 'ThoughtSignature' in part_type:
                            print(f"    ** THOUGHT_SIGNATURE DETECTED **")

        print(f"\nresponse.text: {response3.text if hasattr(response3, 'text') else 'NOT AVAILABLE'}")
    except Exception as e:
        print(f"Error with system_instruction: {e}")

if __name__ == "__main__":
    asyncio.run(test_gemini_response())
