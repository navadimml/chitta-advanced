"""
Test if using a stronger model fixes the function calling issue
"""
import asyncio
import os
from dotenv import load_dotenv

from app.services.llm.factory import create_llm_provider
from app.services.llm.base import Message
from app.prompts.extraction_prompt import build_extraction_prompt
from app.prompts.conversation_functions import CONVERSATION_FUNCTIONS_COMPREHENSIVE

load_dotenv()

async def test_models():
    """Test function calling with different models"""

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

    extraction_prompt = build_extraction_prompt()
    extraction_messages = [
        Message(role="system", content=extraction_prompt),
        Message(role="user", content=extraction_context)
    ]

    models_to_test = [
        "gemini-flash-latest",
        "gemini-2.0-flash-exp",
        "gemini-2.5-pro",
    ]

    for model in models_to_test:
        print("\n" + "=" * 80)
        print(f"Testing with model: {model}")
        print("=" * 80)

        try:
            llm = create_llm_provider(model=model)

            response = await llm.chat(
                messages=extraction_messages,
                functions=CONVERSATION_FUNCTIONS_COMPREHENSIVE,
                temperature=0.0,
                max_tokens=2000
            )

            print(f"  Function calls: {len(response.function_calls)}")
            print(f"  Finish reason: {response.finish_reason}")

            if response.function_calls:
                for fc in response.function_calls:
                    print(f"    ✅ {fc.name}: {fc.arguments}")
            else:
                print(f"    ❌ NO FUNCTION CALLS")

        except Exception as e:
            print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_models())
