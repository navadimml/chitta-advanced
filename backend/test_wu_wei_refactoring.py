"""
Test Wu Wei Refactoring - Phase 1
Tests config-driven artifact generation system
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config.config_loader import load_artifact_generators, load_app_messages
from app.config.artifact_manager import get_artifact_manager
from app.services.artifact_generation_service import ArtifactGenerationService
from app.services.llm.factory import create_llm_provider
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_1_load_artifact_generators_config():
    """Test 1: Verify artifact_generators.yaml loads correctly"""
    print("\n" + "="*80)
    print("TEST 1: Load artifact_generators.yaml")
    print("="*80)

    try:
        config = load_artifact_generators()

        # Check structure
        assert "version" in config, "Missing 'version' field"
        assert "artifact_generators" in config, "Missing 'artifact_generators' field"

        generators = config["artifact_generators"]

        # Check expected generators exist
        expected_generators = [
            "baseline_interview_summary",
            "baseline_video_guidelines",
            "baseline_video_analysis",
            "baseline_professional_report",
            "baseline_parent_report"
        ]

        for gen_id in expected_generators:
            assert gen_id in generators, f"Missing generator: {gen_id}"
            gen_config = generators[gen_id]
            assert "method" in gen_config, f"{gen_id}: Missing 'method' field"
            print(f"✅ {gen_id}: method={gen_config['method']}")

        # Check dependency chain
        print("\n📊 Dependency Chain:")
        print("  interview_summary → (no dependencies)")
        print(f"  video_guidelines → requires: {generators['baseline_video_guidelines'].get('requires_artifacts', [])}")
        print(f"  video_analysis → requires: {generators['baseline_video_analysis'].get('requires_artifacts', [])}")
        print(f"  professional_report → requires: {generators['baseline_professional_report'].get('requires_artifacts', [])}")
        print(f"  parent_report → requires: {generators['baseline_parent_report'].get('requires_artifacts', [])}")

        print("\n✅ TEST 1 PASSED: artifact_generators.yaml loaded successfully")
        return True

    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_2_artifact_manager_get_generator_config():
    """Test 2: Verify artifact_manager.get_generator_config() works"""
    print("\n" + "="*80)
    print("TEST 2: ArtifactManager.get_generator_config()")
    print("="*80)

    try:
        artifact_manager = get_artifact_manager()

        # Test getting config for interview summary
        config = artifact_manager.get_generator_config("baseline_interview_summary")
        assert config is not None, "Failed to get config for baseline_interview_summary"
        assert config["method"] == "generate_interview_summary", "Wrong method for interview summary"
        print(f"✅ baseline_interview_summary: {config['method']}")

        # Test getting config for video guidelines
        config = artifact_manager.get_generator_config("baseline_video_guidelines")
        assert config is not None, "Failed to get config for baseline_video_guidelines"
        assert config["method"] == "generate_video_guidelines", "Wrong method for video guidelines"
        assert "baseline_interview_summary" in config.get("requires_artifacts", []), "Missing dependency"
        print(f"✅ baseline_video_guidelines: {config['method']}, requires: {config.get('requires_artifacts')}")

        # Test validation config
        validation = config.get("validation")
        assert validation is not None, "Missing validation config"
        assert validation["type"] == "json_structure", "Wrong validation type"
        print(f"✅ Validation config present: {validation['type']}")

        # Test non-existent artifact
        config = artifact_manager.get_generator_config("non_existent_artifact")
        assert config is None, "Should return None for non-existent artifact"
        print("✅ Returns None for non-existent artifact")

        print("\n✅ TEST 2 PASSED: ArtifactManager working correctly")
        return True

    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_3_load_app_messages_config():
    """Test 3: Verify app_messages.yaml loads correctly"""
    print("\n" + "="*80)
    print("TEST 3: Load app_messages.yaml")
    print("="*80)

    try:
        config = load_app_messages()

        # Check structure
        assert "version" in config, "Missing 'version' field"
        assert "message_catalog_name" in config, "Missing 'message_catalog_name' field"
        assert "system_triggers" in config, "Missing 'system_triggers' field"

        # Check system triggers
        triggers = config["system_triggers"]
        assert "start_demo" in triggers, "Missing start_demo trigger"
        assert "start_test_mode" in triggers, "Missing start_test_mode trigger"

        demo_trigger = triggers["start_demo"]
        assert "keywords" in demo_trigger, "Missing keywords"
        assert "en" in demo_trigger["keywords"], "Missing English keywords"
        assert "he" in demo_trigger["keywords"], "Missing Hebrew keywords"
        print(f"✅ start_demo keywords: {demo_trigger['keywords']}")

        # Check error messages
        errors = config.get("errors", {})
        assert "technical_error" in errors, "Missing technical_error message"
        print(f"✅ Error messages: {list(errors.keys())}")

        # Check suggestions
        suggestions = config.get("suggestions", {})
        assert "generic" in suggestions, "Missing generic suggestions"
        print(f"✅ Suggestions: {list(suggestions.keys())}")

        print("\n✅ TEST 3 PASSED: app_messages.yaml loaded successfully")
        return True

    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_4_artifact_service_methods_exist():
    """Test 4: Verify ArtifactGenerationService has new methods"""
    print("\n" + "="*80)
    print("TEST 4: ArtifactGenerationService Methods")
    print("="*80)

    try:
        # Create service
        llm_provider = create_llm_provider("gemini", "gemini-2.0-flash-exp", use_enhanced=False)
        service = ArtifactGenerationService(llm_provider)

        # Check methods exist
        assert hasattr(service, "generate_artifact"), "Missing generate_artifact method"
        print("✅ generate_artifact method exists")

        assert hasattr(service, "generate_interview_summary"), "Missing generate_interview_summary method"
        print("✅ generate_interview_summary method exists")

        assert hasattr(service, "generate_video_guidelines"), "Missing generate_video_guidelines method"
        print("✅ generate_video_guidelines method exists")

        assert hasattr(service, "generate_professional_report"), "Missing generate_professional_report method"
        print("✅ generate_professional_report method exists")

        assert hasattr(service, "generate_parent_report"), "Missing generate_parent_report method"
        print("✅ generate_parent_report method exists")

        # Check method signatures (they should accept artifact_id now)
        import inspect

        sig = inspect.signature(service.generate_interview_summary)
        params = list(sig.parameters.keys())
        assert "artifact_id" in params, "generate_interview_summary missing artifact_id parameter"
        print(f"✅ generate_interview_summary signature: {params}")

        sig = inspect.signature(service.generate_video_guidelines)
        params = list(sig.parameters.keys())
        assert "artifact_id" in params, "generate_video_guidelines missing artifact_id parameter"
        print(f"✅ generate_video_guidelines signature: {params}")

        print("\n✅ TEST 4 PASSED: All methods exist with correct signatures")
        return True

    except Exception as e:
        print(f"\n❌ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_5_mock_artifact_generation():
    """Test 5: Mock test of artifact generation flow"""
    print("\n" + "="*80)
    print("TEST 5: Mock Artifact Generation Flow")
    print("="*80)

    try:
        # Create mock session data
        session_data = {
            "family_id": "test_family",
            "child_name": "תום",
            "age": "3 שנים",
            "conversation_history": [
                {"role": "assistant", "content": "שלום! ספרי לי על הילד שלך."},
                {"role": "user", "content": "שלום, אני מודאגת מההתפתחות של תום."}
            ],
            "extracted_data": {
                "child_name": "תום",
                "age": 3,
                "primary_concerns": ["speech"]
            },
            "artifacts": {}
        }

        print("\n📝 Testing config-driven dispatch...")

        # Test 1: Try to get generator config for interview_summary
        artifact_manager = get_artifact_manager()
        config = artifact_manager.get_generator_config("baseline_interview_summary")
        print(f"✅ Got config for baseline_interview_summary: method={config['method']}")

        # Test 2: Verify dependencies check
        config = artifact_manager.get_generator_config("baseline_video_guidelines")
        required = config.get("requires_artifacts", [])
        print(f"✅ baseline_video_guidelines requires: {required}")

        # Simulate: interview_summary exists
        session_data["artifacts"]["baseline_interview_summary"] = {
            "exists": True,
            "status": "ready",
            "content": '{"child": {"name": "תום"}, "parent_emotional_vibe": "חרדה"}',
            "artifact_id": "baseline_interview_summary"
        }

        # Test 3: Check if we can now proceed with video_guidelines
        interview_summary_exists = session_data["artifacts"].get("baseline_interview_summary", {}).get("exists", False)
        print(f"✅ Interview summary exists: {interview_summary_exists}")

        # Test 4: Check validation config
        validation = artifact_manager.get_generator_config("baseline_video_guidelines").get("validation")
        print(f"✅ Validation config: {validation}")

        print("\n✅ TEST 5 PASSED: Mock flow working correctly")
        return True

    except Exception as e:
        print(f"\n❌ TEST 5 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🌟 WU WEI REFACTORING - PHASE 1 TEST SUITE")
    print("="*80)

    results = []

    # Run tests
    results.append(("Load artifact_generators.yaml", test_1_load_artifact_generators_config()))
    results.append(("ArtifactManager.get_generator_config()", test_2_artifact_manager_get_generator_config()))
    results.append(("Load app_messages.yaml", test_3_load_app_messages_config()))
    results.append(("ArtifactGenerationService methods", await test_4_artifact_service_methods_exist()))
    results.append(("Mock artifact generation flow", await test_5_mock_artifact_generation()))

    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\n{'='*80}")
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ Phase 1 refactoring is working correctly")
        print("✅ Config-driven artifact generation system operational")
        print("✅ Ready to proceed with Phase 2 or production testing")
    else:
        print(f"⚠️  {total - passed} test(s) failed")
        print("Please review errors above before proceeding")

    print("="*80 + "\n")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
