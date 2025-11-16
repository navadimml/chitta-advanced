#!/usr/bin/env python3
"""
Test Wu Wei Card Types - Fully Configurable from YAML

Validates that new card types can be added in YAML without code changes.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.config.card_generator import get_card_generator


def main():
    """Test Wu Wei card type configuration"""

    print("\n" + "=" * 80)
    print("🌟 WU WEI CARD TYPES TEST - Fully Configurable from YAML")
    print("=" * 80)

    card_generator = get_card_generator()

    # Check that card_types were loaded from YAML
    print("\n" + "-" * 80)
    print("Card types loaded from YAML:")
    print("-" * 80)

    card_types = card_generator._card_types
    print(f"Found {len(card_types)} card types:\n")

    for card_type_name, config in card_types.items():
        icon = config.get("icon", "N/A")
        color = config.get("color", "N/A")
        style = config.get("style", "N/A")
        print(f"  {card_type_name}:")
        print(f"    icon: {icon}")
        print(f"    color: {color}")
        print(f"    style: {style}")

    # Test that cards use these types
    print("\n" + "-" * 80)
    print("Testing card generation with YAML card types:")
    print("-" * 80)

    context = {
        "phase": "screening",
        "completeness": 0.25,
        "message_count": 5,
        "child_name": "משה",
        "child_age": 7,
        "primary_concerns": ["speech"],
        "strengths": "אוהב לצייר",
    }

    cards = card_generator.get_visible_cards(context)

    print(f"\nGenerated {len(cards)} cards:\n")
    for card in cards:
        card_type = card.get("card_type")
        color = card.get("color")
        icon = card.get("icon")

        print(f"  {card['type']}:")
        print(f"    card_type: {card_type}")
        print(f"    color: {color} (from YAML!)")
        print(f"    icon: {icon} (from YAML!)")
        print(f"    title: {card.get('title')}")

    # Summary
    print("\n" + "=" * 80)
    print("WU WEI VALIDATION - Card Types")
    print("=" * 80)

    print("\n✅ Current card types (all from YAML):")
    for card_type_name, config in card_types.items():
        print(f"   - {card_type_name}: {config.get('color')}")

    print("\n🎯 To add a new card type, just edit YAML:")
    print("""
   card_types:
     warning:
       icon: "alert-triangle"
       color: "red"
       style: "urgent"
    """)

    print("   Then use it in a card:")
    print("""
   urgent_flag_card:
     card_type: warning  # Uses new type!
     content:
       title: "⚠️ נדרש תשומת לב"
    """)

    print("\n   No code changes needed! The system will:")
    print("   ✅ Load the new card_type from YAML")
    print("   ✅ Send color='red' to frontend")
    print("   ✅ Frontend maps 'red' to red Tailwind classes")
    print("   ✅ Icon gets mapped automatically")

    print("\n" + "=" * 80)
    print("CARD TYPE FLOW (Wu Wei)")
    print("=" * 80)

    print("\n1. YAML defines card_types:")
    print("   card_types:")
    print("     guidance:")
    print("       color: 'purple'")
    print("       icon: 'lightbulb'")

    print("\n2. Backend loads and sends to frontend:")
    print("   {")
    print("     'card_type': 'guidance',")
    print("     'color': 'purple',  ← from YAML")
    print("     'icon': 'Lightbulb',  ← mapped from YAML")
    print("   }")

    print("\n3. Frontend maps color to Tailwind classes:")
    print("   'purple' → 'bg-purple-50 border-purple-200 text-purple-700'")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
