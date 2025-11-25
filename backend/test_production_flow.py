"""
Test using EXACT production code path to diagnose function calling issue
"""
import asyncio
import os
from dotenv import load_dotenv

# Import production code
from app.services.llm.factory import create_llm_provider
from app.services.llm.base import Message
from app.prompts.extraction_prompt import build_extraction_prompt
from app.prompts.conversation_functions import CONVERSATION_FUNCTIONS_COMPREHENSIVE

load_dotenv()

async def test_production_flow():
    """Test with exact production flow - using Message objects and factory"""

    # Create provider using factory (same as production)
    llm = create_llm_provider()

    print("=" * 80)
    print("TEST: Production Flow Exact Replication")
    print("=" * 80)
    print(f"\nProvider: {llm.get_provider_name()}")
    print(f"Model: {llm.model_name}")

    # Build exact context from production logs
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

    # Build messages using Message objects (same as production at line 174-177)
    extraction_prompt = build_extraction_prompt()
    extraction_messages = [
        Message(role="system", content=extraction_prompt),
        Message(role="user", content=extraction_context)
    ]

    print(f"\nExtraction prompt length: {len(extraction_prompt)} chars")
    print(f"Number of messages: {len(extraction_messages)}")
    print(f"Message 0: role={extraction_messages[0].role}, length={len(extraction_messages[0].content)}")
    print(f"Message 1: role={extraction_messages[1].role}, length={len(extraction_messages[1].content)}")
    print(f"\nNumber of functions: {len(CONVERSATION_FUNCTIONS_COMPREHENSIVE)}")
    print(f"Function names: {[f['name'] for f in CONVERSATION_FUNCTIONS_COMPREHENSIVE]}")

    # Call LLM using production code path (same as conversation_service_simplified.py line 529-534)
    print(f"\n🚀 Calling llm.chat() with functions (production code path)...")

    try:
        llm_response = await llm.chat(
            messages=extraction_messages,
            functions=CONVERSATION_FUNCTIONS_COMPREHENSIVE,
            temperature=0.0,  # Same as production (line 185)
            max_tokens=2000  # Same as production (line 187)
        )

        print(f"\n✅ Response received!")
        print(f"Finish reason: {llm_response.finish_reason}")
        print(f"Number of function calls: {len(llm_response.function_calls)}")
        print(f"Content length: {len(llm_response.content or '')}")

        if llm_response.function_calls:
            for i, fc in enumerate(llm_response.function_calls):
                print(f"\n  Function call {i}:")
                print(f"    Name: {fc.name}")
                print(f"    Arguments: {fc.arguments}")
        else:
            print(f"\n❌ NO FUNCTION CALLS!")
            print(f"Content preview: {(llm_response.content or '')[:200]}")

        print(f"\n{'='*80}")
        print(f"RESULT:")
        print(f"  Function calls: {len(llm_response.function_calls)}")
        print(f"  Expected: 1 function call with filming_preference='wants_videos'")

        if len(llm_response.function_calls) == 0:
            print(f"\n❌ BUG REPRODUCED! Production code path returns 0 function calls!")
        elif len(llm_response.function_calls) == 1:
            fc = llm_response.function_calls[0]
            if fc.name == "extract_interview_data" and fc.arguments.get("filming_preference") == "wants_videos":
                print(f"\n✅ PERFECT! Bug NOT reproduced - function calling works!")
            else:
                print(f"\n⚠️  Function called but with unexpected args")
        else:
            print(f"\n⚠️  Multiple function calls (unexpected)")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_production_flow())
