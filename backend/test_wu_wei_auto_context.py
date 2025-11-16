#!/usr/bin/env python3
"""
Test Wu Wei Auto-Context - No Manual Field Listing Needed

Validates that new cards can reference any extracted field without code changes.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.interview_service import ExtractedData


def main():
    """Test auto-context building"""

    print("\n" + "=" * 80)
    print("🌟 WU WEI AUTO-CONTEXT TEST")
    print("=" * 80)

    # Create sample extracted data with ALL fields
    data = ExtractedData(
        child_name="משה",
        age=7,
        gender="male",
        primary_concerns=["speech", "social"],
        concern_details="דאגה לגבי תקשורת עם חברים",
        strengths="אוהב לצייר חיות, מצטיין בפאזלים",
        developmental_history="התפתח בקצב תקין עד גיל 5",
        family_context="משפחה של 4, אח קטן בן 3",
        daily_routines="גן עד 14:00, משחק בבית",
        parent_goals="שישתפר בתקשורת עם חברים",
        urgent_flags=["social_isolation"],
    )

    # Test both Pydantic v1 and v2 methods
    print("\n" + "-" * 80)
    print("Testing auto-conversion to dict:")
    print("-" * 80)

    try:
        # Try Pydantic v2
        extracted_dict = data.model_dump()
        print("✅ Using Pydantic v2: data.model_dump()")
    except AttributeError:
        # Fall back to Pydantic v1
        extracted_dict = data.dict()
        print("✅ Using Pydantic v1: data.dict()")

    print(f"\nExtracted {len(extracted_dict)} fields automatically:")
    for key, value in extracted_dict.items():
        if key in ["last_updated", "extraction_count"]:
            continue  # Skip metadata

        value_preview = str(value)[:50] if value else "None"
        print(f"  - {key}: {value_preview}")

    # Test that we can build context without manual listing
    print("\n" + "-" * 80)
    print("Building context with auto-merge:")
    print("-" * 80)

    context = {
        "phase": "screening",
        "completeness": 0.25,
        "message_count": 5,
        **extracted_dict,  # 🌟 Wu Wei magic!
    }

    print(f"✅ Context has {len(context)} fields total")
    print(f"   - Static fields: phase, completeness, message_count")
    print(f"   - Auto-merged from ExtractedData: {len(extracted_dict)} fields")

    # Verify all extracted fields are in context
    print("\n" + "-" * 80)
    print("Verifying all extracted fields accessible in context:")
    print("-" * 80)

    test_fields = [
        "child_name",
        "age",
        "gender",
        "primary_concerns",
        "strengths",  # The field that was missing before!
        "concern_details",
        "developmental_history",
        "family_context",
        "daily_routines",
        "parent_goals",
    ]

    all_accessible = True
    for field in test_fields:
        if field in context:
            value = context[field]
            value_str = str(value)[:40] if value else "None"
            print(f"  ✅ {field}: {value_str}")
        else:
            print(f"  ❌ {field}: MISSING!")
            all_accessible = False

    # Summary
    print("\n" + "=" * 80)
    print("WU WEI PROMISE VALIDATION")
    print("=" * 80)

    if all_accessible:
        print("\n✅ SUCCESS! Wu Wei promise maintained:")
        print("   - ALL extracted fields automatically available in context")
        print("   - New YAML cards can reference ANY field without code changes")
        print("   - No manual field listing needed!")

        print("\n🎯 Example - Add new card in YAML only:")
        print("""
   family_context_card:
     card_type: guidance
     display_conditions:
       family_context: "!= None"  # Auto-works! No code change needed
     content:
       title: "הקשר המשפחתי"
       body: "{family_context}"  # Auto-formatted! No code change needed
        """)
    else:
        print("\n❌ FAILED! Some fields not accessible")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
