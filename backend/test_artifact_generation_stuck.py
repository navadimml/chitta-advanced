"""
Test to diagnose why artifact generation gets stuck in "generating" status
"""

import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables from .env BEFORE importing services
load_dotenv()

from app.services.lifecycle_manager import get_lifecycle_manager
from app.services.session_service import get_session_service
from app.services.prerequisite_service import get_prerequisite_service

# Enable debug logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

async def test_stuck_artifact():
    """Test artifact generation to see if it completes"""

    family_id = "test_stuck_artifact_001"
    session_service = get_session_service()
    lifecycle_manager = get_lifecycle_manager()
    prereq_service = get_prerequisite_service()

    # Create a session with enough data to trigger guidelines
    session = session_service.get_or_create_session(family_id)
    session_service.update_extracted_data(family_id, {
        "child_name": "דני",
        "age": 3,
        "gender": "male",
        "primary_concerns": ["speech", "social"],
        "concern_details": "דני לא מדבר הרבה ומתקשה לשחק עם ילדים אחרים. כשהוא משחק בגן, הוא נוטה לשחק לבד ולא מגיב כשילדים מנסים להצטרף אליו.",
        "strengths": "דני אוהב לבנות עם קוביות ויש לו דמיון מדהים. הוא יכול לבנות מגדלים גבוהים ומורכבים.",
        "developmental_history": "דני נולד בזמן, התפתחות תקינה עד גיל שנה וחצי, אז החלו הקשיים בשפה.",
        "family_context": "דני הוא הילד הראשון במשפחה, יש לו אח קטן בן שנה.",
        "daily_routines": "דני הולך לגן בבוקר, אוכל טוב, ישן היטב בלילה."
    })

    # Set completeness high
    session.completeness = 0.8

    print(f"\n{'='*60}")
    print(f"TEST: Checking if artifact generation works")
    print(f"Family: {family_id}")
    print(f"Child: {session.extracted_data.child_name}, age {session.extracted_data.age}")
    print(f"Completeness: {session.completeness}")
    print(f"{'='*60}\n")

    # Build context for prerequisite check
    session_data = {
        "family_id": family_id,
        "extracted_data": session.extracted_data.model_dump(),
        "message_count": 10,
        "artifacts": session.artifacts,
        "completeness": session.completeness,
    }
    context = prereq_service.get_context_for_cards(session_data)
    context["conversation_history"] = []

    # Manually trigger lifecycle event
    print("Triggering lifecycle events...")
    result = await lifecycle_manager.process_lifecycle_events(
        family_id=family_id,
        context=context,
        session=session
    )

    print(f"\n{'='*60}")
    print(f"LIFECYCLE RESULT:")
    print(f"{'='*60}")
    print(f"Artifacts generated: {result['artifacts_generated']}")
    print(f"Events triggered: {[e['event_name'] for e in result['events_triggered']]}")
    print(f"Capabilities unlocked: {result['capabilities_unlocked']}")

    # Check artifact status
    print(f"\n{'='*60}")
    print(f"ARTIFACT STATUS:")
    print(f"{'='*60}")

    artifact = session.get_artifact("baseline_video_guidelines")
    if artifact:
        print(f"Artifact exists: True")
        print(f"Status: {artifact.status}")
        print(f"Is generating: {artifact.is_generating}")
        print(f"Is ready: {artifact.is_ready}")
        print(f"Has error: {artifact.has_error}")
        if artifact.has_error:
            print(f"Error: {artifact.error_message}")
        if artifact.is_ready:
            import json
            content = json.loads(artifact.content) if isinstance(artifact.content, str) else artifact.content
            print(f"Content: {len(artifact.content)} chars")
            print(f"Scenarios: {len(content.get('scenarios', []))}")
    else:
        print(f"Artifact exists: False")

    # Wait a bit for background task
    print(f"\n{'='*60}")
    print("Waiting 10 seconds for background generation...")
    print(f"{'='*60}\n")
    await asyncio.sleep(10)

    # Check again
    session = session_service.get_or_create_session(family_id)
    artifact = session.get_artifact("baseline_video_guidelines")

    print(f"\n{'='*60}")
    print(f"AFTER 10 SECONDS:")
    print(f"{'='*60}")
    if artifact:
        print(f"Status: {artifact.status}")
        print(f"Is generating: {artifact.is_generating}")
        print(f"Is ready: {artifact.is_ready}")
        print(f"Has error: {artifact.has_error}")
        if artifact.has_error:
            print(f"Error: {artifact.error_message}")
        if artifact.is_ready:
            import json
            content = json.loads(artifact.content) if isinstance(artifact.content, str) else artifact.content
            print(f"✅ SUCCESS: Artifact generated with {len(content.get('scenarios', []))} scenarios")
        elif artifact.is_generating:
            print(f"⚠️ STILL GENERATING: Background task not complete")
        elif artifact.has_error:
            print(f"❌ FAILED: {artifact.error_message}")
    else:
        print(f"❌ ARTIFACT DISAPPEARED")

if __name__ == "__main__":
    asyncio.run(test_stuck_artifact())
