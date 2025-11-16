"""
Test consultation service and intent detection
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.knowledge_service import KnowledgeService
from app.services.consultation_service import ConsultationService
from app.services.interview_service import get_interview_service
from app.prompts.intent_types import IntentCategory


async def test_intent_detection():
    """Test that consultation intent is properly detected"""
    print("=" * 60)
    print("Testing Intent Detection")
    print("=" * 60)

    knowledge_service = KnowledgeService()

    test_cases = [
        # Consultation questions
        ("מה התכוונת בחיפוש חושי?", IntentCategory.CONSULTATION),
        ("למה כתבת שיש לו קשיים בתפקודים ניהוליים?", IntentCategory.CONSULTATION),
        ("האם הדיבור שלו השתפר?", IntentCategory.CONSULTATION),
        ("מה הפסיכולוגית כתבה על הקשב?", IntentCategory.CONSULTATION),

        # Information requests
        ("מה זה צ'יטה?", IntentCategory.INFORMATION_REQUEST),
        ("איך זה עובד?", IntentCategory.INFORMATION_REQUEST),

        # Action requests
        ("תן לי דוח", IntentCategory.ACTION_REQUEST),
        ("תראי הנחיות", IntentCategory.ACTION_REQUEST),

        # Conversation (data collection)
        ("הילד שלי בן 5", IntentCategory.DATA_COLLECTION),
        ("יש לו קושי בדיבור", IntentCategory.DATA_COLLECTION),
    ]

    passed = 0
    failed = 0

    for message, expected_category in test_cases:
        result = await knowledge_service.detect_unified_intent(message)

        if result.category == expected_category:
            print(f"✅ PASS: '{message[:40]}' → {result.category.value}")
            passed += 1
        else:
            print(f"❌ FAIL: '{message[:40]}' → Expected: {expected_category.value}, Got: {result.category.value}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Intent Detection Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


async def test_consultation_service():
    """Test consultation service basic functionality"""
    print("\n" + "=" * 60)
    print("Testing Consultation Service")
    print("=" * 60)

    # Create a test family with some data
    interview_service = get_interview_service()
    consultation_service = ConsultationService()

    family_id = "test_consultation_family"

    # Setup: Add some conversation history
    interview_service.add_conversation_turn(family_id, "user", "שלום, הבן שלי יוני בן 3")
    interview_service.add_conversation_turn(family_id, "assistant", "שלום! נעים להכיר את יוני. ספרי לי עוד עליו.")
    interview_service.add_conversation_turn(family_id, "user", "יש לו קושי בדיבור והוא אוהב לקפוץ על הספה")
    interview_service.add_conversation_turn(family_id, "assistant", "הבנתי. הקפיצה על הספה יכולה להיות חיפוש חושי. ספרי לי עוד על הדיבור.")

    # Update extracted data
    interview_service.update_extracted_data(family_id, {
        "child_name": "יוני",
        "age": 3,
        "primary_concerns": ["speech"],
        "concern_details": "קושי בדיבור - מדבר רק כמה מילים בודדות",
        "strengths": "אוהב לקפוץ על הספה, אנרגטי"
    })

    # Create an artifact (simulating a report)
    session = interview_service.get_or_create_session(family_id)
    from app.models.interview_state import Artifact
    from datetime import datetime

    session.artifacts["baseline_parent_report"] = Artifact(
        type="baseline_parent_report",
        content={
            "summary": "דוח התפתחותי ליוני בן 3",
            "sections": {
                "sensory_profile": "יוני מראה דפוסים של חיפוש חושי במערכת הווסטיבולרית - קפיצות תכופות על הספה",
                "communication": "קושי בדיבור עם שליטה במספר מוגבל של מילים"
            }
        },
        created_at=datetime.now()
    )

    print("\n📝 Setup completed - family has conversation history and artifacts")

    # Test consultation questions
    test_questions = [
        "מה זה חיפוש חושי?",
        "למה אמרת שיש לו דפוסים של חיפוש חושי?",
        "מה כתבת על הדיבור שלו?",
    ]

    print("\n🔍 Testing consultation questions:\n")

    all_passed = True

    for question in test_questions:
        print(f"\nQuestion: {question}")
        print("-" * 60)

        try:
            result = await consultation_service.handle_consultation(
                family_id=family_id,
                question=question
            )

            response = result["response"]
            sources = result["sources_used"]

            print(f"Response ({len(response)} chars):")
            print(response[:300] + "..." if len(response) > 300 else response)
            print(f"\nSources used: {sources}")
            print("✅ Consultation succeeded")

        except Exception as e:
            print(f"❌ Consultation failed: {e}")
            all_passed = False

    print("\n" + "=" * 60)
    print(f"Consultation Service: {'✅ All tests passed' if all_passed else '❌ Some tests failed'}")
    print("=" * 60)

    return all_passed


async def main():
    """Run all tests"""
    print("\n🧪 Starting Consultation System Tests\n")

    # Test 1: Intent detection
    intent_test_passed = await test_intent_detection()

    # Test 2: Consultation service
    consultation_test_passed = await test_consultation_service()

    # Final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"Intent Detection: {'✅ PASSED' if intent_test_passed else '❌ FAILED'}")
    print(f"Consultation Service: {'✅ PASSED' if consultation_test_passed else '❌ FAILED'}")
    print("=" * 60)

    if intent_test_passed and consultation_test_passed:
        print("\n🎉 All tests passed! Consultation system is working.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
