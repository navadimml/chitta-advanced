#!/usr/bin/env python3
"""
Test script for Wu Wei configuration loading.

Validates that all YAML configurations load correctly and
that the Python configuration layer works as expected.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.config import config_loader, schema_registry, action_registry, phase_manager
from app.config import artifact_manager, card_generator, view_manager


def test_config_loader():
    """Test base configuration loader."""
    print("=" * 60)
    print("Testing ConfigLoader...")
    print("=" * 60)

    try:
        loader = config_loader.get_workflow_config_loader()
        print("✓ ConfigLoader initialized")

        # Test loading each config
        configs = {
            "extraction_schema": loader.load_extraction_schema,
            "action_graph": loader.load_action_graph,
            "phases": loader.load_phases,
            "artifacts": loader.load_artifacts,
            "context_cards": loader.load_context_cards,
            "deep_views": loader.load_deep_views,
        }

        for name, load_fn in configs.items():
            config = load_fn()
            print(f"✓ Loaded {name}: {config.get('version', 'unknown version')}")

        print("\n✅ All configurations loaded successfully!\n")
        return True

    except Exception as e:
        print(f"\n❌ Error loading configurations: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_schema_registry():
    """Test schema registry."""
    print("=" * 60)
    print("Testing SchemaRegistry...")
    print("=" * 60)

    try:
        registry = schema_registry.get_schema_registry()
        print("✓ SchemaRegistry initialized")

        # Get all fields
        fields = registry.get_all_fields()
        print(f"✓ Found {len(fields)} field definitions")

        # Test completeness calculation
        test_data = {
            "child_name": "Test Child",
            "age": "5",
            "primary_concerns": "Test concerns with enough detail to get some weight",
        }
        completeness = registry.calculate_completeness(test_data)
        print(f"✓ Calculated completeness: {completeness:.2%}")

        # Test function calling schema
        func_schema = registry.get_function_calling_schema()
        print(f"✓ Generated function schema: {func_schema.get('name')}")
        print(f"  - {len(func_schema['parameters']['properties'])} properties")

        # Test missing fields
        missing = registry.get_missing_fields_summary(test_data, top_n=3)
        print(f"✓ Top missing fields: {[m['field_name'] for m in missing[:3]]}")

        print("\n✅ SchemaRegistry working correctly!\n")
        return True

    except Exception as e:
        print(f"\n❌ Error in SchemaRegistry: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_action_registry():
    """Test action registry."""
    print("=" * 60)
    print("Testing ActionRegistry...")
    print("=" * 60)

    try:
        registry = action_registry.get_action_registry()
        print("✓ ActionRegistry initialized")

        # Get all actions
        actions = registry.get_all_actions()
        print(f"✓ Found {len(actions)} action definitions")

        # Test action availability
        test_context = {
            "phase": "screening",
            "session": type('obj', (object,), {
                "completeness": 0.50,
                "artifacts": type('obj', (object,), {"videos": []})()
            })()
        }

        result = registry.check_action_availability("continue_interview", test_context)
        print(f"✓ continue_interview available: {result['available']}")

        result = registry.check_action_availability("view_report", test_context)
        print(f"✓ view_report available: {result['available']}")
        if not result['available']:
            print(f"  - Blocked: {result.get('explanation', 'No explanation')[:50]}...")

        # Get available actions
        available = registry.get_available_actions(test_context)
        print(f"✓ {len(available)} actions currently available")

        print("\n✅ ActionRegistry working correctly!\n")
        return True

    except Exception as e:
        print(f"\n❌ Error in ActionRegistry: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_phase_manager():
    """Test phase manager."""
    print("=" * 60)
    print("Testing PhaseManager...")
    print("=" * 60)

    try:
        manager = phase_manager.get_phase_manager()
        print("✓ PhaseManager initialized")

        # Get all phases
        phases = manager.get_all_phases()
        print(f"✓ Found {len(phases)} phase definitions")
        for phase_id in phases.keys():
            print(f"  - {phase_id}")

        # Get initial phase
        initial = manager.get_initial_phase()
        print(f"✓ Initial phase: {initial}")

        # Get phase details
        screening = manager.get_phase("screening")
        if screening:
            print(f"✓ Screening phase: {screening.name}")
            print(f"  - Threshold: {screening.completeness_threshold}")
            print(f"  - Mode: {screening.conversation_mode}")
            print(f"  - Actions: {len(screening.available_actions)}")

        # Test transition check
        test_context = {"reports_ready": True, "child_name": "Test"}
        transition = manager.check_transition_trigger("screening", test_context)
        if transition:
            print(f"✓ Transition available: {transition.from_phase} → {transition.to_phase}")

        print("\n✅ PhaseManager working correctly!\n")
        return True

    except Exception as e:
        print(f"\n❌ Error in PhaseManager: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_artifact_manager():
    """Test artifact manager."""
    print("=" * 60)
    print("Testing ArtifactManager...")
    print("=" * 60)

    try:
        manager = artifact_manager.get_artifact_manager()
        print("✓ ArtifactManager initialized")

        # Get all artifacts
        artifacts = manager.get_all_artifacts()
        print(f"✓ Found {len(artifacts)} artifact definitions")

        # Get specific artifact
        report = manager.get_artifact("parent_report")
        if report:
            print(f"✓ parent_report artifact: {report.get('name_en')}")
            states = manager.get_artifact_states("parent_report")
            print(f"  - States: {states}")

        # Get phase artifacts
        screening_artifacts = manager.get_artifacts_for_phase("screening")
        print(f"✓ {len(screening_artifacts)} artifacts in screening phase")

        print("\n✅ ArtifactManager working correctly!\n")
        return True

    except Exception as e:
        print(f"\n❌ Error in ArtifactManager: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_card_generator():
    """Test card generator."""
    print("=" * 60)
    print("Testing CardGenerator...")
    print("=" * 60)

    try:
        generator = card_generator.get_card_generator()
        print("✓ CardGenerator initialized")

        # Get all cards
        cards = generator.get_all_cards()
        print(f"✓ Found {len(cards)} card definitions")

        # Test card visibility
        test_context = {
            "phase": "screening",
            "message_count": 5,
            "completeness": 0.50
        }

        visible = generator.get_visible_cards(test_context, max_cards=3)
        print(f"✓ {len(visible)} cards visible in current context")
        for card in visible:
            print(f"  - {card.get('card_id')}: priority {card.get('priority')}")

        print("\n✅ CardGenerator working correctly!\n")
        return True

    except Exception as e:
        print(f"\n❌ Error in CardGenerator: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_view_manager():
    """Test view manager."""
    print("=" * 60)
    print("Testing ViewManager...")
    print("=" * 60)

    try:
        manager = view_manager.get_view_manager()
        print("✓ ViewManager initialized")

        # Get all views
        views = manager.get_all_views()
        print(f"✓ Found {len(views)} view definitions")

        # Test view availability
        test_context = {
            "phase": "screening",
            "reports_ready": False
        }

        report_available = manager.check_view_availability("report_view", test_context)
        print(f"✓ report_view available: {report_available}")

        journal_available = manager.check_view_availability("journal_view", test_context)
        print(f"✓ journal_view available: {journal_available}")

        # Get available views
        available = manager.get_available_views(test_context)
        print(f"✓ {len(available)} views currently available")

        print("\n✅ ViewManager working correctly!\n")
        return True

    except Exception as e:
        print(f"\n❌ Error in ViewManager: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n")
    print("🧪 Wu Wei Configuration System Test Suite")
    print("=" * 60)
    print()

    tests = [
        ("ConfigLoader", test_config_loader),
        ("SchemaRegistry", test_schema_registry),
        ("ActionRegistry", test_action_registry),
        ("PhaseManager", test_phase_manager),
        ("ArtifactManager", test_artifact_manager),
        ("CardGenerator", test_card_generator),
        ("ViewManager", test_view_manager),
    ]

    results = {}
    for name, test_fn in tests:
        try:
            results[name] = test_fn()
        except Exception as e:
            print(f"❌ {name} crashed: {e}\n")
            results[name] = False

    # Summary
    print("\n")
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print()
    print(f"Result: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Wu Wei configuration system is working!\n")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review errors above.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
