"""
Final test to verify artifact generation fix
"""

import asyncio
import json
from dotenv import load_dotenv

# Load .env FIRST!
load_dotenv()

from app.services.artifact_generation_service import ArtifactGenerationService

async def test_direct_generation():
    """Test artifact generation directly without lifecycle complexity"""

    service = ArtifactGenerationService()

    # Minimal session data that should trigger generation
    session_data = {
        "child_name": "דני",
        "age": 3,
        "primary_concerns": ["speech", "social"],
        "concern_details": "דני לא מדבר הרבה ומתקשה לשחק עם ילדים. כשהוא משחק בגן, הוא נוטה לשחק לבד ולא מגיב כשילדים מנסים להצטרף אליו.",
        "strengths": "דני אוהב לבנות עם קוביות ויש לו דמיון מדהים. הוא יכול לבנות מגדלים גבוהים ומורכבים.",
        "conversation_history": [
            {"role": "assistant", "content": "שלום! שמחה לפגוש אותך. ספרי לי על הילד שלך"},
            {"role": "user", "content": "זה דני, הוא בן 3. יש לו קשיים בדיבור ובחברתיות"},
            {"role": "assistant", "content": "תודה שפתחת. ספרי לי יותר על הקשיים"},
            {"role": "user", "content": "דני לא מדבר הרבה ומתקשה לשחק עם ילדים. כשהוא משחק בגן, הוא נוטה לשחק לבד"},
            {"role": "assistant", "content": "מה דני אוהב לעשות?"},
            {"role": "user", "content": "הוא אוהב לבנות עם קוביות, יש לו דמיון מדהים"}
        ]
    }

    print("=" * 80)
    print("TESTING ARTIFACT GENERATION DIRECTLY")
    print("=" * 80)
    print(f"Child: {session_data['child_name']}, Age: {session_data['age']}")
    print(f"Concerns: {', '.join(session_data['primary_concerns'])}")
    print("=" * 80)
    print("\nGenerating guidelines (this may take 30-60 seconds)...\n")

    try:
        # Generate artifact
        artifact = await service.generate_video_guidelines(session_data)

        print("=" * 80)
        print("RESULT:")
        print("=" * 80)

        if artifact.is_ready:
            print(f"✅ SUCCESS!")
            print(f"   Status: {artifact.status}")
            print(f"   Generation time: {artifact.generation_duration_seconds:.2f}s")
            print(f"   Model used: {artifact.generation_model}")

            # Parse content
            content = json.loads(artifact.content) if isinstance(artifact.content, str) else artifact.content
            scenarios = content.get('scenarios', [])
            print(f"   Scenarios generated: {len(scenarios)}")

            print("\n   Scenario titles:")
            for i, scenario in enumerate(scenarios, 1):
                print(f"     {i}. {scenario.get('title', 'N/A')}")

        elif artifact.has_error:
            print(f"❌ FAILED!")
            print(f"   Status: {artifact.status}")
            print(f"   Error: {artifact.error_message}")

        else:
            print(f"⚠️ UNEXPECTED STATUS: {artifact.status}")

    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_direct_generation())
