"""
Test if combining system+user messages breaks function calling
"""
import asyncio
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from app.prompts.extraction_prompt import build_extraction_prompt
from app.prompts.conversation_functions import CONVERSATION_FUNCTIONS_COMPREHENSIVE

load_dotenv()

async def test_message_formats():
    """Compare different message formats"""
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    extraction_prompt = build_extraction_prompt()
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

    # Convert functions
    declarations = [
        types.FunctionDeclaration(
            name=func["name"],
            description=func.get("description", ""),
            parameters=func.get("parameters", {})
        )
        for func in CONVERSATION_FUNCTIONS_COMPREHENSIVE
    ]
    tools = [types.Tool(function_declarations=declarations)]

    # Config with AFC disabled
    config = types.GenerateContentConfig(
        tools=tools,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(
                mode=types.FunctionCallingConfigMode.ANY
            )
        ),
        temperature=0.0,
        max_output_tokens=2000
    )

    print("=" * 80)
    print("TEST 1: Two separate user messages (THIS WORKS)")
    print("=" * 80)

    messages1 = [
        types.Content(role="user", parts=[types.Part(text=extraction_prompt)]),
        types.Content(role="user", parts=[types.Part(text=extraction_context)])
    ]

    response1 = await client.aio.models.generate_content(
        model="gemini-flash-latest",
        contents=messages1,
        config=config
    )

    fc_count_1 = sum(1 for part in response1.candidates[0].content.parts
                      if hasattr(part, 'function_call') and part.function_call)
    print(f"✅ Result: {fc_count_1} function calls")

    print("\n" + "=" * 80)
    print("TEST 2: Single combined user message (PRODUCTION FORMAT)")
    print("=" * 80)

    # Simulate what _convert_messages_to_contents() does (line 314)
    combined_text = f"{extraction_prompt}\n\n{extraction_context}"
    messages2 = [
        types.Content(role="user", parts=[types.Part(text=combined_text)])
    ]

    response2 = await client.aio.models.generate_content(
        model="gemini-flash-latest",
        contents=messages2,
        config=config
    )

    fc_count_2 = sum(1 for part in response2.candidates[0].content.parts
                      if hasattr(part, 'function_call') and part.function_call)
    print(f"Result: {fc_count_2} function calls")

    print("\n" + "=" * 80)
    print("COMPARISON:")
    print("=" * 80)
    print(f"Two separate messages: {fc_count_1} function calls {'✅ WORKS' if fc_count_1 > 0 else '❌ FAILS'}")
    print(f"Single combined message: {fc_count_2} function calls {'✅ WORKS' if fc_count_2 > 0 else '❌ FAILS'}")

    if fc_count_1 > 0 and fc_count_2 == 0:
        print("\n🔍 ROOT CAUSE FOUND!")
        print("Combining system prompt + context into single message breaks function calling!")
    elif fc_count_1 > 0 and fc_count_2 > 0:
        print("\n⚠️ Both formats work - issue must be elsewhere")

if __name__ == "__main__":
    asyncio.run(test_message_formats())
