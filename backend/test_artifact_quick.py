"""
Quick test to see if artifact generation completes successfully
"""

import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables from .env BEFORE importing services
load_dotenv()

from app.services.lifecycle_manager import get_lifecycle_manager
from app.services.session_service import get_session_service

# Enable debug logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

async def test_quick_artifact():
    """Quick test with longer wait time"""

    family_id = "test_quick_001"
    session_service = get_session_service()
    lifecycle_manager = get_lifecycle_manager()

    # Create a session with enough data
    session = session_service.get_or_create_session(family_id)
    session_service.update_extracted_data(family_id, {
        "child_name": "דני",
        "age": 3,
        "gender": "male",
        "primary_concerns": ["speech", "social"],
        "concern_details": "דני לא מדבר הרבה ומתקשה לשחק עם ילדים אחרים.",
        "strengths": "דני אוהב לבנות עם קוביות ויש לו דמיון מדהים.",
    })
    session.completeness = 0.8

    # Build context
    from app.services.prerequisite_service import get_prerequisite_service
    prereq_service = get_prerequisite_service()
    session_data = {
        "family_id": family_id,
        "extracted_data": session.extracted_data.model_dump(),
        "message_count": 10,
        "artifacts": session.artifacts,
        "completeness": session.completeness,
    }
    context = prereq_service.get_context_for_cards(session_data)
    context["conversation_history"] = []

    # Trigger lifecycle
    print("🚀 Starting artifact generation...")
    result = await lifecycle_manager.process_lifecycle_events(
        family_id=family_id,
        context=context,
        session=session
    )

    print(f"✅ Lifecycle result: {result['artifacts_generated']}")

    # Wait for background task (increased to 60 seconds)
    print("⏳ Waiting 60 seconds for generation to complete...")
    await asyncio.sleep(60)

    # Check artifact status
    session = session_service.get_or_create_session(family_id)
    artifact = session.get_artifact("baseline_video_guidelines")

    print("\n" + "=" * 80)
    print("FINAL RESULT:")
    print("=" * 80)
    if artifact:
        print(f"Status: {artifact.status}")
        if artifact.is_ready:
            import json
            content = json.loads(artifact.content) if isinstance(artifact.content, str) else artifact.content
            scenarios = content.get('scenarios', [])
            print(f"✅ SUCCESS! Generated {len(scenarios)} scenarios")
            print(f"Duration: {artifact.generation_duration_seconds:.2f}s")
            print("\nScenarios:")
            for i, scenario in enumerate(scenarios, 1):
                print(f"  {i}. {scenario.get('title', 'N/A')}")
        elif artifact.has_error:
            print(f"❌ FAILED: {artifact.error_message}")
        elif artifact.is_generating:
            print(f"⚠️ STILL GENERATING (needs more time)")
    else:
        print("❌ ARTIFACT NOT FOUND")

if __name__ == "__main__":
    asyncio.run(test_quick_artifact())
