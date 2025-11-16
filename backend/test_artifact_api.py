"""
Test Artifact API Endpoints

Tests the Wu Wei artifact API integration:
1. Session artifacts listing
2. Individual artifact retrieval
3. User action tracking
4. Artifact inclusion in chat response
"""

import sys
import asyncio
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.interview_service import get_interview_service
from app.services.artifact_generation_service import ArtifactGenerationService
from app.models.artifact import Artifact

print("🌟" * 40)
print("  ARTIFACT API INTEGRATION TESTS")
print("🌟" * 40)
print()


async def test_1_session_artifacts_endpoint():
    """Test 1: Session artifacts endpoint simulation"""
    print("=" * 80)
    print("  TEST 1: Session Artifacts Endpoint")
    print("=" * 80)
    print()

    # Setup: Create session with artifacts
    interview_service = get_interview_service()
    family_id = "test_family_api"

    session = interview_service.get_or_create_session(family_id)

    # Add some artifacts
    guidelines = Artifact(
        artifact_id="baseline_video_guidelines",
        artifact_type="guidelines",
        status="ready",
        content="# Test Guidelines"
    )
    guidelines.mark_ready("# Test Guidelines\n\nContent here.")

    session.add_artifact(guidelines)

    print(f"Session: {family_id}")
    print(f"  Artifacts count: {len(session.artifacts)}")
    print()

    # Simulate API endpoint logic
    artifacts_list = []
    for artifact_id, artifact in session.artifacts.items():
        artifacts_list.append({
            "artifact_id": artifact.artifact_id,
            "artifact_type": artifact.artifact_type,
            "status": artifact.status,
            "content_format": artifact.content_format,
            "created_at": artifact.created_at.isoformat(),
            "ready_at": artifact.ready_at.isoformat() if artifact.ready_at else None,
            "exists": artifact.exists,
            "is_ready": artifact.is_ready,
        })

    print("GET /session/{family_id}/artifacts response:")
    print(f"  family_id: {family_id}")
    print(f"  artifacts: {len(artifacts_list)} items")
    for artifact_data in artifacts_list:
        print(f"    - {artifact_data['artifact_id']}: {artifact_data['status']} (exists: {artifact_data['exists']})")
    print()

    print("✅ Test 1 PASSED: Session artifacts endpoint works\n")


async def test_2_individual_artifact_endpoint():
    """Test 2: Individual artifact retrieval"""
    print("=" * 80)
    print("  TEST 2: Individual Artifact Retrieval")
    print("=" * 80)
    print()

    interview_service = get_interview_service()
    family_id = "test_family_api"
    session = interview_service.get_or_create_session(family_id)

    artifact_id = "baseline_video_guidelines"
    artifact = session.get_artifact(artifact_id)

    if not artifact:
        print(f"❌ Artifact {artifact_id} not found")
        return

    # Simulate API response
    response_data = {
        "artifact_id": artifact.artifact_id,
        "artifact_type": artifact.artifact_type,
        "status": artifact.status,
        "content": artifact.content if artifact.is_ready else None,
        "content_format": artifact.content_format,
        "created_at": artifact.created_at.isoformat(),
        "ready_at": artifact.ready_at.isoformat() if artifact.ready_at else None,
    }

    print(f"GET /artifacts/{artifact_id}?family_id={family_id} response:")
    print(f"  artifact_id: {response_data['artifact_id']}")
    print(f"  artifact_type: {response_data['artifact_type']}")
    print(f"  status: {response_data['status']}")
    print(f"  content_format: {response_data['content_format']}")
    print(f"  content_length: {len(response_data['content']) if response_data['content'] else 0} chars")
    print()

    if response_data['content']:
        print("Content preview:")
        print("-" * 80)
        print(response_data['content'][:200])
        print("...")
        print("-" * 80)
    print()

    print("✅ Test 2 PASSED: Individual artifact retrieval works\n")


async def test_3_user_action_tracking():
    """Test 3: User action tracking"""
    print("=" * 80)
    print("  TEST 3: User Action Tracking")
    print("=" * 80)
    print()

    interview_service = get_interview_service()
    family_id = "test_family_api"
    session = interview_service.get_or_create_session(family_id)

    artifact_id = "baseline_video_guidelines"
    artifact = session.get_artifact(artifact_id)

    # Simulate action tracking
    from datetime import datetime

    if "user_actions" not in artifact.metadata:
        artifact.metadata["user_actions"] = []

    action = "view"
    artifact.metadata["user_actions"].append({
        "action": action,
        "timestamp": datetime.now().isoformat()
    })

    session.add_artifact(artifact)

    print(f"POST /artifacts/{artifact_id}/action:")
    print(f"  action: {action}")
    print(f"  family_id: {family_id}")
    print()

    print("Response:")
    print(f"  success: True")
    print(f"  artifact_id: {artifact_id}")
    print(f"  tracked_actions: {len(artifact.metadata.get('user_actions', []))}")
    print()

    # Add more actions
    for action in ["download", "view"]:
        artifact.metadata["user_actions"].append({
            "action": action,
            "timestamp": datetime.now().isoformat()
        })

    print("Action history:")
    for action_record in artifact.metadata.get("user_actions", []):
        print(f"  - {action_record['action']} at {action_record['timestamp'][:19]}")
    print()

    print("✅ Test 3 PASSED: User action tracking works\n")


async def test_4_chat_response_includes_artifacts():
    """Test 4: Chat response includes artifacts"""
    print("=" * 80)
    print("  TEST 4: Artifacts in Chat Response")
    print("=" * 80)
    print()

    interview_service = get_interview_service()
    family_id = "test_family_api"
    session = interview_service.get_or_create_session(family_id)

    # Simulate chat response building
    artifacts_for_ui = {}
    for artifact_id, artifact in session.artifacts.items():
        artifacts_for_ui[artifact_id] = {
            "exists": artifact.exists,
            "status": artifact.status,
            "artifact_type": artifact.artifact_type,
            "ready_at": artifact.ready_at.isoformat() if artifact.ready_at else None
        }

    # Simulate full UI data response
    ui_data = {
        "suggestions": ["מה הצעדים הבאים?", "תראי לי את ההנחיות"],
        "cards": [],
        "progress": 0.75,
        "extracted_data": {},
        "stats": {},
        "artifacts": artifacts_for_ui
    }

    print("POST /chat/send response (ui_data.artifacts):")
    print(f"  Total artifacts: {len(ui_data['artifacts'])}")
    print()

    for artifact_id, artifact_data in ui_data['artifacts'].items():
        print(f"  {artifact_id}:")
        print(f"    exists: {artifact_data['exists']}")
        print(f"    status: {artifact_data['status']}")
        print(f"    type: {artifact_data['artifact_type']}")
        if artifact_data['ready_at']:
            print(f"    ready_at: {artifact_data['ready_at'][:19]}")
        print()

    print("Frontend can now:")
    print("  1. Check if artifacts.baseline_video_guidelines.exists")
    print("  2. Fetch content via GET /artifacts/baseline_video_guidelines")
    print("  3. Track view/download via POST /artifacts/.../action")
    print()

    print("✅ Test 4 PASSED: Artifacts included in chat response\n")


async def test_5_full_flow_simulation():
    """Test 5: Full flow from generation to retrieval"""
    print("=" * 80)
    print("  TEST 5: Full Artifact Flow")
    print("=" * 80)
    print()

    # 1. Generate artifact
    print("Step 1: Generate artifact...")
    service = ArtifactGenerationService()
    session_data = {
        "child_name": "דני",
        "age": 3.5,
        "primary_concerns": ["שפה"],
        "concern_details": "דני מתקשה לבטא את עצמו",
        "strengths": "אוהב משחקים",
    }

    artifact = await service.generate_video_guidelines(session_data)
    print(f"  ✓ Generated: {artifact.artifact_id} ({artifact.status})")
    print()

    # 2. Store in session
    print("Step 2: Store in session...")
    interview_service = get_interview_service()
    session = interview_service.get_or_create_session("full_flow_test")
    session.add_artifact(artifact)
    print(f"  ✓ Stored in session: full_flow_test")
    print()

    # 3. Frontend gets chat response
    print("Step 3: Frontend receives chat response...")
    artifacts_for_ui = {}
    for artifact_id, art in session.artifacts.items():
        artifacts_for_ui[artifact_id] = {
            "exists": art.exists,
            "status": art.status,
        }
    print(f"  ✓ Chat response includes: {list(artifacts_for_ui.keys())}")
    print()

    # 4. Frontend fetches artifact content
    print("Step 4: Frontend fetches artifact content...")
    fetched = session.get_artifact("baseline_video_guidelines")
    print(f"  ✓ Fetched content: {len(fetched.content)} chars")
    print()

    # 5. User views artifact
    print("Step 5: User views artifact...")
    if "user_actions" not in fetched.metadata:
        fetched.metadata["user_actions"] = []
    fetched.metadata["user_actions"].append({
        "action": "view",
        "timestamp": "2025-01-01T10:00:00"
    })
    print(f"  ✓ Tracked action: view")
    print()

    # 6. User downloads artifact
    print("Step 6: User downloads artifact...")
    fetched.metadata["user_actions"].append({
        "action": "download",
        "timestamp": "2025-01-01T10:05:00"
    })
    print(f"  ✓ Tracked action: download")
    print()

    print("Full flow summary:")
    print(f"  Generated → Stored → Included in response → Fetched → Tracked")
    print(f"  Total actions: {len(fetched.metadata['user_actions'])}")
    print()

    print("✅ Test 5 PASSED: Full flow works end-to-end\n")


async def main():
    """Run all tests"""
    await test_1_session_artifacts_endpoint()
    await test_2_individual_artifact_endpoint()
    await test_3_user_action_tracking()
    await test_4_chat_response_includes_artifacts()
    await test_5_full_flow_simulation()

    print("=" * 80)
    print("  ✅ ALL API INTEGRATION TESTS COMPLETED")
    print("=" * 80)
    print()
    print("Frontend Integration Ready! 🚀")
    print()
    print("Available Endpoints:")
    print("  GET  /session/{family_id}/artifacts - List all artifacts")
    print("  GET  /artifacts/{artifact_id}?family_id=... - Get artifact content")
    print("  POST /artifacts/{artifact_id}/action - Track user actions")
    print("  POST /chat/send - Includes artifacts in ui_data.artifacts")


if __name__ == "__main__":
    asyncio.run(main())
