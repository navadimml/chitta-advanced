"""
Test knowledge_is_rich Prerequisite Fix

Validates that the lifecycle_manager properly evaluates knowledge_is_rich
by delegating to WuWeiPrerequisites.evaluate_knowledge_richness().

This test verifies the fix for the bug where offer_filming moment was not
triggering because knowledge_is_rich was expected to be in context but was
never added.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.lifecycle_manager import LifecycleManager
from app.services.artifact_generation_service import ArtifactGenerationService
from app.services.llm.factory import create_llm_provider

def test_knowledge_rich_prerequisite_evaluation():
    """Test that knowledge_is_rich is properly evaluated dynamically"""
    print("\n" + "="*80)
    print("TEST: knowledge_is_rich Dynamic Evaluation")
    print("="*80)

    try:
        # Create lifecycle manager
        llm_provider = create_llm_provider("gemini", "gemini-2.0-flash-exp", use_enhanced=False)
        artifact_service = ArtifactGenerationService(llm_provider)
        lifecycle_manager = LifecycleManager(artifact_service)

        # Test Case 1: Empty context (knowledge NOT rich)
        print("\n📋 Test Case 1: Empty Context")
        print("-" * 80)

        empty_context = {
            "child_name": None,
            "age": None,
            "primary_concerns": [],
            "concern_description": None,
            "strengths": None,
            "other_info": "",
            "message_count": 2,
            "artifacts": {}
        }

        prerequisites = {"knowledge_is_rich": True}
        result = lifecycle_manager._evaluate_prerequisites(prerequisites, empty_context)

        assert result == False, "Empty context should NOT be knowledge_rich"
        print("✅ Empty context correctly evaluated as NOT knowledge_rich")

        # Test Case 2: Rich context (Path 1: structured data)
        print("\n📋 Test Case 2: Rich Context (Structured)")
        print("-" * 80)

        rich_context = {
            "child_name": "דני",
            "age": 3,
            "primary_concerns": ["speech", "social"],
            "concern_description": "דני לא מדבר הרבה ומתקשה לשחק עם ילדים אחרים. כשהוא משחק בגן, הוא נוטה לשחק לבד.",
            "strengths": "דני אוהב לבנות עם קוביות ויש לו דמיון מדהים. הוא יכול לבנות מגדלים גבוהים.",
            "other_info": "דני הוא הילד הראשון במשפחה, יש לו אח קטן בן שנה. אבא עובד הרבה.",
            "message_count": 12,
            "artifacts": {}
        }

        result = lifecycle_manager._evaluate_prerequisites(prerequisites, rich_context)

        assert result == True, "Rich context should be knowledge_rich"
        print("✅ Rich context correctly evaluated as knowledge_rich")

        # Test Case 3: Not rich yet (insufficient data)
        print("\n📋 Test Case 3: Insufficient Context")
        print("-" * 80)

        insufficient_context = {
            "child_name": "דני",
            "age": 3,
            "primary_concerns": ["speech"],
            "concern_description": "דני לא מדבר",  # Too short (< 50 chars)
            "strengths": None,
            "other_info": "",
            "message_count": 5,  # Not enough messages
            "artifacts": {}
        }

        result = lifecycle_manager._evaluate_prerequisites(prerequisites, insufficient_context)

        assert result == False, "Insufficient context should NOT be knowledge_rich"
        print("✅ Insufficient context correctly evaluated as NOT knowledge_rich")

        # Test Case 4: offer_filming prerequisites (knowledge_is_rich + filming_preference: None)
        print("\n📋 Test Case 4: offer_filming Prerequisites")
        print("-" * 80)

        offer_filming_context = rich_context.copy()
        offer_filming_context["filming_preference"] = None

        offer_filming_prereqs = {
            "knowledge_is_rich": True,
            "filming_preference": None
        }

        result = lifecycle_manager._evaluate_prerequisites(offer_filming_prereqs, offer_filming_context)

        assert result == True, "offer_filming prerequisites should be met with rich context and filming_preference=None"
        print("✅ offer_filming prerequisites correctly evaluated as MET")
        print(f"   - knowledge_is_rich: True ✓")
        print(f"   - filming_preference: None ✓")

        # Test Case 5: offer_filming with filming_preference set (should NOT match)
        print("\n📋 Test Case 5: offer_filming with filming_preference='wants_videos'")
        print("-" * 80)

        set_preference_context = rich_context.copy()
        set_preference_context["filming_preference"] = "wants_videos"

        result = lifecycle_manager._evaluate_prerequisites(offer_filming_prereqs, set_preference_context)

        assert result == False, "offer_filming should NOT match when filming_preference is set"
        print("✅ offer_filming correctly NOT matching when filming_preference is already set")

        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED!")
        print("="*80)
        print("\n🎉 Fix Confirmed:")
        print("   ✓ knowledge_is_rich is now dynamically evaluated")
        print("   ✓ Delegates to WuWeiPrerequisites.evaluate_knowledge_richness()")
        print("   ✓ No longer requires knowledge_is_rich to be pre-computed in context")
        print("   ✓ offer_filming moment will now trigger correctly")
        print("="*80 + "\n")

        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        print("="*80)
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("="*80)
        return False


if __name__ == "__main__":
    success = test_knowledge_rich_prerequisite_evaluation()
    sys.exit(0 if success else 1)
