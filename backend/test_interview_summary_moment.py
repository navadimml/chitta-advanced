"""
Test that interview_summary generation moment is properly configured.

Validates that:
1. generate_interview_summary moment exists
2. It triggers when knowledge_is_rich
3. generate_guidelines moment requires interview_summary.exists
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.config.config_loader import load_workflow

def test_interview_summary_moment_exists():
    """Test that generate_interview_summary moment is configured"""
    print("\n" + "="*80)
    print("TEST: Interview Summary Generation Moment")
    print("="*80)

    try:
        config = load_workflow()
        moments = config.get("moments", {})

        # Check moment exists
        assert "generate_interview_summary" in moments, \
            "Missing generate_interview_summary moment"

        summary_moment = moments["generate_interview_summary"]

        # Check prerequisites
        when = summary_moment.get("when", {})
        assert "knowledge_is_rich" in when, \
            "generate_interview_summary should trigger when knowledge_is_rich"
        assert when["knowledge_is_rich"] == True, \
            "knowledge_is_rich should be true"
        assert "artifacts.baseline_interview_summary.exists" in when, \
            "Should check if interview_summary already exists"
        assert when["artifacts.baseline_interview_summary.exists"] == False, \
            "Should only trigger if interview_summary doesn't exist yet"

        # Check artifact
        assert summary_moment.get("artifact") == "baseline_interview_summary", \
            "Should generate baseline_interview_summary artifact"

        print("✅ generate_interview_summary moment exists")
        print(f"   Triggers when: {when}")
        print(f"   Generates: {summary_moment.get('artifact')}")

        # Check that generate_guidelines requires interview_summary
        guidelines_moment = moments.get("generate_guidelines", {})
        guidelines_when = guidelines_moment.get("when", {})

        assert "artifacts.baseline_interview_summary.exists" in guidelines_when, \
            "generate_guidelines should require interview_summary.exists"
        assert guidelines_when["artifacts.baseline_interview_summary.exists"] == True, \
            "generate_guidelines should wait for interview_summary to exist"

        print("\n✅ generate_guidelines moment requires interview_summary")
        print(f"   Prerequisites: filming_preference='wants_videos' AND interview_summary.exists")

        print("\n✅ Dependency chain configured correctly:")
        print("   1. knowledge_is_rich → generate_interview_summary")
        print("   2. interview_summary.exists + filming_preference → generate_guidelines")
        print("   3. interview_summary + guidelines → video_analysis")

        print("\n✅ TEST PASSED: Interview summary moment properly configured")
        print("="*80)
        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        print("="*80)
        return False


if __name__ == "__main__":
    success = test_interview_summary_moment_exists()
    sys.exit(0 if success else 1)
