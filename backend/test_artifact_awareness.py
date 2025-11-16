"""
Test artifact awareness injection in conversation prompt

This demonstrates the fix for the synchronization issue where:
- Lifecycle manager generates artifacts (e.g., video guidelines)
- Context cards show "Video guidelines ready!"
- BUT conversation prompt doesn't know about it
- So Chitta might say "I'll generate guidelines" instead of "Guidelines are ready"

With the fix, Chitta's prompt always includes what artifacts exist.
"""
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.conversation_service import ConversationService
from app.services.interview_service import get_interview_service
from app.models.interview_state import Artifact


def test_artifact_awareness_injection():
    """Test that artifacts are properly injected into conversation prompt"""
    print("=" * 60)
    print("Testing Artifact Awareness Injection")
    print("=" * 60)

    interview_service = get_interview_service()
    conv_service = ConversationService()

    family_id = "test_artifact_sync"

    # Setup: Create session with some data
    interview_service.update_extracted_data(family_id, {
        "child_name": "יוני",
        "age": 3,
        "primary_concerns": ["speech", "motor"],
        "concern_details": "קושי בדיבור ותנועה"
    })

    session = interview_service.get_or_create_session(family_id)

    print("\n📝 Scenario: Lifecycle manager just generated video guidelines")
    print("-" * 60)

    # Simulate lifecycle manager generating artifact
    session.artifacts["baseline_video_guidelines"] = Artifact(
        type="baseline_video_guidelines",
        content={
            "title": "הנחיות צילום ליוני",
            "sections": {
                "speech": "צלמו את יוני מדבר או מנסה לתקשר",
                "motor": "צלמו את יוני רץ, קופץ, ומטפס"
            }
        },
        created_at=datetime.now()
    )

    print("✅ Artifact created: baseline_video_guidelines")
    print(f"   Created at: {session.artifacts['baseline_video_guidelines'].created_at}")

    # Test: Build artifact awareness
    print("\n🔍 Building artifact awareness for prompt injection...")
    artifact_awareness = conv_service._build_artifact_awareness(session)

    print("\n📋 Artifact Awareness Output:")
    print("=" * 60)
    print(artifact_awareness)
    print("=" * 60)

    # Verify it contains key elements
    checks = {
        "Contains Hebrew heading": "מסמכים שכבר יצרת" in artifact_awareness,
        "Contains artifact name": "הנחיות צילום" in artifact_awareness,
        "Contains creation date": "נוצר:" in artifact_awareness,
        "Contains 'already exists' warning": "כבר קיימים" in artifact_awareness,
        "Contains usage instructions": "אל תאמר" in artifact_awareness,
        "Contains example responses": "כבר הכנתי" in artifact_awareness,
    }

    print("\n✅ Verification Checks:")
    all_passed = True
    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check_name}")
        if not passed:
            all_passed = False

    # Test with multiple artifacts
    print("\n\n📝 Scenario 2: Multiple artifacts generated")
    print("-" * 60)

    session.artifacts["baseline_parent_report"] = Artifact(
        type="baseline_parent_report",
        content={"summary": "דוח מקיף על יוני"},
        created_at=datetime.now()
    )

    session.artifacts["sensory_profile"] = Artifact(
        type="sensory_profile",
        content={"profile": "פרופיל חושי"},
        created_at=datetime.now()
    )

    print("✅ Added 2 more artifacts (total: 3)")

    artifact_awareness_multi = conv_service._build_artifact_awareness(session)

    print("\n📋 Artifact Awareness with Multiple Artifacts:")
    print("=" * 60)
    print(artifact_awareness_multi)
    print("=" * 60)

    # Count checkmarks (should be 3)
    checkmark_count = artifact_awareness_multi.count("✅")
    print(f"\n✅ Found {checkmark_count} artifacts in output (expected: 3)")

    if checkmark_count == 3:
        print("   ✅ Correct!")
    else:
        print(f"   ❌ Expected 3, got {checkmark_count}")
        all_passed = False

    # Test with no artifacts
    print("\n\n📝 Scenario 3: No artifacts yet")
    print("-" * 60)

    empty_session = interview_service.get_or_create_session("test_empty")
    artifact_awareness_empty = conv_service._build_artifact_awareness(empty_session)

    print(f"✅ Empty session artifacts: {len(empty_session.artifacts)}")
    print(f"✅ Artifact awareness output: '{artifact_awareness_empty}'")

    if artifact_awareness_empty == "":
        print("   ✅ Correctly returns empty string when no artifacts")
    else:
        print("   ❌ Should return empty string but got content")
        all_passed = False

    # Final summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    if all_passed:
        print("✅ All tests passed!")
        print("\n🎉 Artifact awareness injection working correctly!")
        print("\nHow it fixes the sync issue:")
        print("1. Lifecycle manager generates artifact → Added to session.artifacts")
        print("2. Next conversation turn → _build_artifact_awareness() called")
        print("3. Artifact info injected into Chitta's prompt")
        print("4. Chitta knows what exists and can reference it properly")
        print("\n✅ No more 'I'll generate' when artifact already exists!")
        return 0
    else:
        print("❌ Some tests failed - review output above")
        return 1


if __name__ == "__main__":
    exit_code = test_artifact_awareness_injection()
    sys.exit(exit_code)
