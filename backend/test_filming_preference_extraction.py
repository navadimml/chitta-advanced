"""
Test why filming_preference extraction is failing with seeded scenario
"""
import asyncio
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from app.prompts.extraction_prompt import build_extraction_prompt
from app.prompts.conversation_functions import CONVERSATION_FUNCTIONS_COMPREHENSIVE

load_dotenv()

async def test_filming_preference():
    """Test extraction with exact scenario from logs"""
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    # Build exact context from logs
    extraction_context = """<already_extracted>
- Name: דני
- Age: 3 years
- Gender: male
- Primary concerns: speech, social
- Strengths: דני אוהב לבנות עם קוביות ויש לו דמיון מדהים. הוא יכול לבנות מגדלים גבוהים ומורכבים. הוא גם אוהב ספרים ויכול להתרכז בהם לזמן ארוך
- Concern details: דני לא מדבר הרבה ומתקשה לשחק עם ילדים אחרים. כשהוא משחק בגן, הוא נו...
</already_extracted>

<parent_message>
כן רוצה לצלם סירטונים
</parent_message>"""

    # Get extraction prompt
    extraction_prompt = build_extraction_prompt()

    print("=" * 80)
    print("TEST: Filming Preference Extraction")
    print("=" * 80)
    print(f"\nExtraction prompt length: {len(extraction_prompt)} chars")
    print(f"\nContext: {extraction_context[:200]}...")
    print(f"\nNumber of functions: {len(CONVERSATION_FUNCTIONS_COMPREHENSIVE)}")
    print(f"\nFunction names: {[f['name'] for f in CONVERSATION_FUNCTIONS_COMPREHENSIVE]}")

    # Convert functions to tools
    declarations = []
    for func in CONVERSATION_FUNCTIONS_COMPREHENSIVE:
        declaration = types.FunctionDeclaration(
            name=func["name"],
            description=func.get("description", ""),
            parameters=func.get("parameters", {})
        )
        declarations.append(declaration)

    tools = [types.Tool(function_declarations=declarations)]

    # Build config with AFC disabled and mode=ANY
    config = types.GenerateContentConfig(
        tools=tools,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(
            disable=True
        ),
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(
                mode=types.FunctionCallingConfigMode.ANY  # MUST call a function
            )
        ),
        temperature=0.0,
        max_output_tokens=2000
    )

    print(f"\nConfig:")
    print(f"  Tools: {len(tools[0].function_declarations)} functions")
    print(f"  AFC disabled: {config.automatic_function_calling.disable}")
    print(f"  Mode: {config.tool_config.function_calling_config.mode}")

    # Build messages
    messages = [
        types.Content(role="user", parts=[types.Part(text=extraction_prompt)]),
        types.Content(role="user", parts=[types.Part(text=extraction_context)])
    ]

    print(f"\nSending {len(messages)} messages to gemini-flash-latest...")

    try:
        response = await client.aio.models.generate_content(
            model="gemini-flash-latest",
            contents=messages,
            config=config
        )

        print(f"\n✅ Response received!")
        print(f"Finish reason: {response.candidates[0].finish_reason}")
        print(f"Number of parts: {len(response.candidates[0].content.parts)}")

        function_calls_found = 0
        text_found = False

        for i, part in enumerate(response.candidates[0].content.parts):
            print(f"\nPart {i}:")
            if hasattr(part, 'function_call') and part.function_call:
                function_calls_found += 1
                print(f"  ✅ FUNCTION CALL: {part.function_call.name}")
                print(f"  Args: {dict(part.function_call.args)}")
            if hasattr(part, 'text') and part.text:
                text_found = True
                print(f"  Text: {part.text[:100]}...")
            if hasattr(part, 'thought'):
                print(f"  Has thought_signature: Yes")

        print(f"\n{'='*80}")
        print(f"RESULT:")
        print(f"  Function calls: {function_calls_found}")
        print(f"  Text found: {text_found}")
        print(f"  Expected: 1 function call with filming_preference='wants_videos'")

        if function_calls_found == 0:
            print(f"\n❌ BUG REPRODUCED! No function calls even with mode=ANY!")
            print(f"This matches the bug in production.")
        else:
            print(f"\n✅ Function calling works! Bug NOT reproduced.")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_filming_preference())
