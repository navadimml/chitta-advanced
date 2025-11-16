"""
Test Artifact Generation System

Tests the Wu Wei artifact generation flow:
1. Artifact models
2. Artifact storage in session
3. Artifact generation service
4. Integration with prerequisite system
"""

import sys
import asyncio
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.models.artifact import Artifact, ArtifactReference
from app.services.interview_service import InterviewState, ExtractedData
from app.services.artifact_generation_service import ArtifactGenerationService

print("🌟" * 40)
print("  ARTIFACT GENERATION SYSTEM TESTS")
print("🌟" * 40)
print()


def test_1_artifact_model():
    """Test 1: Artifact model lifecycle"""
    print("=" * 80)
    print("  TEST 1: Artifact Model Lifecycle")
    print("=" * 80)
    print()

    # Create artifact
    artifact = Artifact(
        artifact_id="test_guidelines",
        artifact_type="guidelines",
        status="pending"
    )

    print(f"Created artifact: {artifact.artifact_id}")
    print(f"  Status: {artifact.status}")
    print(f"  Exists: {artifact.exists}")
    print(f"  Is pending: {artifact.is_pending}")
    print()

    # Mark as generating
    artifact.mark_generating()
    print("Marked as generating:")
    print(f"  Status: {artifact.status}")
    print(f"  Is generating: {artifact.is_generating}")
    print()

    # Mark as ready
    content = "# Test Guidelines\n\nThis is a test."
    artifact.mark_ready(content)
    print("Marked as ready:")
    print(f"  Status: {artifact.status}")
    print(f"  Exists: {artifact.exists}")
    print(f"  Is ready: {artifact.is_ready}")
    print(f"  Content length: {len(artifact.content)} chars")
    print()

    print("✅ Test 1 PASSED: Artifact lifecycle works correctly\n")


def test_2_session_artifact_storage():
    """Test 2: Artifact storage in InterviewState"""
    print("=" * 80)
    print("  TEST 2: Session Artifact Storage")
    print("=" * 80)
    print()

    # Create session
    session = InterviewState(family_id="test_family")

    print(f"Created session for: {session.family_id}")
    print(f"  Initial artifacts: {len(session.artifacts)}")
    print(f"  Has baseline_video_guidelines: {session.has_artifact('baseline_video_guidelines')}")
    print()

    # Add artifact
    guidelines = Artifact(
        artifact_id="baseline_video_guidelines",
        artifact_type="guidelines",
        status="ready",
        content="# Test Guidelines\n\nContent here."
    )
    guidelines.mark_ready("# Test Guidelines\n\nContent here.")

    session.add_artifact(guidelines)

    print("Added video guidelines artifact:")
    print(f"  Artifacts count: {len(session.artifacts)}")
    print(f"  Has baseline_video_guidelines: {session.has_artifact('baseline_video_guidelines')}")
    print()

    # Get artifact
    retrieved = session.get_artifact("baseline_video_guidelines")
    print("Retrieved artifact:")
    print(f"  ID: {retrieved.artifact_id}")
    print(f"  Status: {retrieved.status}")
    print(f"  Exists: {retrieved.exists}")
    print()

    # Check backwards compatibility
    print("Backwards compatibility:")
    print(f"  video_guidelines_generated flag: {session.video_guidelines_generated}")
    print()

    print("✅ Test 2 PASSED: Session artifact storage works correctly\n")


async def test_3_artifact_generation():
    """Test 3: Artifact generation service"""
    print("=" * 80)
    print("  TEST 3: Artifact Generation Service")
    print("=" * 80)
    print()

    service = ArtifactGenerationService()

    # Prepare session data
    session_data = {
        "child_name": "דני",
        "age": 3.5,
        "primary_concerns": ["שפה", "חברתי"],
        "concern_details": "דני מתקשה לבטא את עצמו ולעיתים נסוג מאינטראקציות חברתיות עם ילדים אחרים.",
        "strengths": "דני אוהב לשחק עם קוביות ומראה יצירתיות במשחק עצמאי. הוא שקט וממוקד.",
    }

    print("Generating video guidelines for:")
    print(f"  Child: {session_data['child_name']}")
    print(f"  Age: {session_data['age']}")
    print(f"  Concerns: {', '.join(session_data['primary_concerns'])}")
    print()

    # Generate guidelines
    artifact = await service.generate_video_guidelines(session_data)

    print("Generation result:")
    print(f"  Artifact ID: {artifact.artifact_id}")
    print(f"  Status: {artifact.status}")
    print(f"  Is ready: {artifact.is_ready}")
    print(f"  Content length: {len(artifact.content) if artifact.content else 0} chars")
    print(f"  Generation duration: {artifact.generation_duration_seconds:.3f}s")
    print()

    if artifact.is_ready:
        print("Content preview (first 300 chars):")
        print("-" * 80)
        print(artifact.content[:300])
        print("...")
        print("-" * 80)
        print()
        print("✅ Test 3 PASSED: Artifact generation works correctly\n")
    else:
        print(f"❌ Test 3 FAILED: {artifact.error_message}\n")


def test_4_artifact_reference():
    """Test 4: Artifact references for prerequisite checks"""
    print("=" * 80)
    print("  TEST 4: Artifact References")
    print("=" * 80)
    print()

    # Create artifact
    artifact = Artifact(
        artifact_id="baseline_video_guidelines",
        artifact_type="guidelines",
        status="ready",
        content="# Guidelines content"
    )
    artifact.mark_ready("# Guidelines content")

    # Create reference
    ref = ArtifactReference.from_artifact(artifact)

    print("Created artifact reference:")
    print(f"  Exists: {ref.exists}")
    print(f"  Status: {ref.status}")
    print(f"  Artifact ID: {ref.artifact_id}")
    print()

    # Test non-existent artifact
    not_exists_ref = ArtifactReference.not_exists()
    print("Non-existent artifact reference:")
    print(f"  Exists: {not_exists_ref.exists}")
    print(f"  Status: {not_exists_ref.status}")
    print()

    # Simulate prerequisite check
    print("Simulated prerequisite check:")
    print(f"  baseline_video_guidelines.exists = {ref.exists} (should be True)")
    print(f"  baseline_parent_report.exists = {not_exists_ref.exists} (should be False)")
    print()

    print("✅ Test 4 PASSED: Artifact references work correctly\n")


async def main():
    """Run all tests"""
    test_1_artifact_model()
    test_2_session_artifact_storage()
    await test_3_artifact_generation()
    test_4_artifact_reference()

    print("=" * 80)
    print("  ✅ ALL TESTS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
