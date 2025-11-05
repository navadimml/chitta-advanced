#!/usr/bin/env python3
"""
Test script to verify context-aware prerequisite explanations
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.prompts.prerequisites import Action, get_prerequisite_explanation

def test_view_report_explanations():
    """Test VIEW_REPORT explanations in different states"""

    print("=" * 80)
    print("Testing VIEW_REPORT Context-Aware Explanations")
    print("=" * 80)

    # Scenario 1: Interview not complete (30%)
    print("\n1. Interview 30% complete, no videos:")
    print("-" * 80)
    explanation = get_prerequisite_explanation(
        Action.VIEW_REPORT,
        child_name="יוני",
        video_count=0,
        required_videos=3,
        interview_complete=False,
        analysis_complete=False,
        completeness=0.30
    )
    print(explanation)

    # Scenario 2: Interview complete, no videos
    print("\n2. Interview complete (85%), no videos yet:")
    print("-" * 80)
    explanation = get_prerequisite_explanation(
        Action.VIEW_REPORT,
        child_name="יוני",
        video_count=0,
        required_videos=3,
        interview_complete=True,
        analysis_complete=False,
        completeness=0.85
    )
    print(explanation)

    # Scenario 3: Interview complete, 1 video uploaded
    print("\n3. Interview complete, 1 video uploaded:")
    print("-" * 80)
    explanation = get_prerequisite_explanation(
        Action.VIEW_REPORT,
        child_name="יוני",
        video_count=1,
        required_videos=3,
        interview_complete=True,
        analysis_complete=False,
        completeness=0.85
    )
    print(explanation)

    # Scenario 4: Interview complete, 2 videos uploaded
    print("\n4. Interview complete, 2 videos uploaded:")
    print("-" * 80)
    explanation = get_prerequisite_explanation(
        Action.VIEW_REPORT,
        child_name="יוני",
        video_count=2,
        required_videos=3,
        interview_complete=True,
        analysis_complete=False,
        completeness=0.85
    )
    print(explanation)

    # Scenario 5: Interview complete, 3 videos, analyzing
    print("\n5. Interview complete, 3 videos, analysis in progress:")
    print("-" * 80)
    explanation = get_prerequisite_explanation(
        Action.VIEW_REPORT,
        child_name="יוני",
        video_count=3,
        required_videos=3,
        interview_complete=True,
        analysis_complete=False,  # Still analyzing
        completeness=0.85
    )
    print(explanation)

    # Scenario 6: Analysis complete, generating report
    print("\n6. Analysis complete, generating report:")
    print("-" * 80)
    explanation = get_prerequisite_explanation(
        Action.VIEW_REPORT,
        child_name="יוני",
        video_count=3,
        required_videos=3,
        interview_complete=True,
        analysis_complete=True,  # Analysis done
        completeness=0.85
    )
    print(explanation)


def test_upload_video_explanations():
    """Test UPLOAD_VIDEO explanations"""

    print("\n" + "=" * 80)
    print("Testing UPLOAD_VIDEO Context-Aware Explanations")
    print("=" * 80)

    # Interview not complete
    print("\n1. Interview 45% complete:")
    print("-" * 80)
    explanation = get_prerequisite_explanation(
        Action.UPLOAD_VIDEO,
        child_name="יוני",
        video_count=0,
        required_videos=3,
        interview_complete=False,
        analysis_complete=False,
        completeness=0.45
    )
    print(explanation)


def test_analyze_videos_explanations():
    """Test ANALYZE_VIDEOS explanations"""

    print("\n" + "=" * 80)
    print("Testing ANALYZE_VIDEOS Context-Aware Explanations")
    print("=" * 80)

    # No interview
    print("\n1. Interview not complete:")
    print("-" * 80)
    explanation = get_prerequisite_explanation(
        Action.ANALYZE_VIDEOS,
        child_name="יוני",
        video_count=0,
        required_videos=3,
        interview_complete=False,
        analysis_complete=False,
        completeness=0.50
    )
    print(explanation)

    # Interview done but no videos
    print("\n2. Interview complete, but no videos:")
    print("-" * 80)
    explanation = get_prerequisite_explanation(
        Action.ANALYZE_VIDEOS,
        child_name="יוני",
        video_count=0,
        required_videos=3,
        interview_complete=True,
        analysis_complete=False,
        completeness=0.85
    )
    print(explanation)

    # Interview done, only 2 videos
    print("\n3. Interview complete, 2 videos (need 3):")
    print("-" * 80)
    explanation = get_prerequisite_explanation(
        Action.ANALYZE_VIDEOS,
        child_name="יוני",
        video_count=2,
        required_videos=3,
        interview_complete=True,
        analysis_complete=False,
        completeness=0.85
    )
    print(explanation)


if __name__ == "__main__":
    print("\n🧪 Testing Context-Aware Prerequisite Explanations\n")

    test_view_report_explanations()
    test_upload_video_explanations()
    test_analyze_videos_explanations()

    print("\n" + "=" * 80)
    print("✅ All tests completed!")
    print("=" * 80)
    print("\nVerify that explanations are:")
    print("  1. Context-aware (different based on actual state)")
    print("  2. Accurate (match the screening flow: Interview → Guidelines → Film → Upload → Analyze → Report)")
    print("  3. Helpful (guide user to next step)")
    print()
