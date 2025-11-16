#!/usr/bin/env python3
"""
Debug: Why are no cards showing?
"""

import sys
sys.path.insert(0, '/home/user/chitta-advanced/backend')

from app.services.prerequisite_service import get_prerequisite_service
from app.config.card_generator import get_card_generator

# Simulate a real conversation scenario
session_data = {
    "family_id": "test_123",
    "extracted_data": {
        "child_name": "דני",
        "age": 4,
        "primary_concerns": ["שפה"],
    },
    "message_count": 3,
    "parent_report_id": None,  # No baseline report yet
    "video_guidelines": False,
    "uploaded_video_count": 0
}

print("=" * 80)
print("DEBUG: Card Display Issue")
print("=" * 80)
print()

# Build context
prereq_service = get_prerequisite_service()
context = prereq_service.get_context_for_cards(session_data)

print("1. Context Built:")
print(f"   message_count: {context.get('message_count')}")
print(f"   child_name: {context.get('child_name')}")
print(f"   artifacts: {context.get('artifacts')}")
print(f"   baseline_parent_report in artifacts: {'baseline_parent_report' in context.get('artifacts', {})}")
print()

# Check specific card conditions manually
print("2. Checking conversation_depth_card conditions:")
print("   Display conditions from YAML:")
print("     - baseline_parent_report.exists: false")
print("     - message_count: '> 0'")
print("     - artifacts.video_guidelines.exists: false")
print()

# Check what _get_nested_value returns
card_gen = get_card_generator()

# Test 1: baseline_parent_report.exists
value1 = card_gen._get_nested_value(context, "baseline_parent_report.exists")
print(f"   _get_nested_value('baseline_parent_report.exists') = {value1}")
print(f"   Expected: None (artifact doesn't exist)")
print(f"   Condition check: {value1} == False? {value1 == False}")
print(f"   THIS IS THE BUG! None != False, so condition fails!")
print()

# Test 2: Try to get cards
print("3. Attempting to get cards...")
cards = card_gen.get_visible_cards(context, max_cards=10)
print(f"   Cards returned: {len(cards)}")
if len(cards) == 0:
    print("   ❌ NO CARDS! This confirms the issue.")
print()

# Test 3: Check if the card would show if we fix the context
print("4. Testing with manually fixed context...")
context_fixed = context.copy()
context_fixed["baseline_parent_report"] = {"exists": False}  # Explicitly set exists to False
print(f"   Added baseline_parent_report.exists = False to context")

value2 = card_gen._get_nested_value(context_fixed, "baseline_parent_report.exists")
print(f"   _get_nested_value('baseline_parent_report.exists') = {value2}")
print(f"   Condition check: {value2} == False? {value2 == False}")

cards_fixed = card_gen.get_visible_cards(context_fixed, max_cards=10)
print(f"   Cards returned: {len(cards_fixed)}")
if len(cards_fixed) > 0:
    print("   ✅ CARDS APPEAR when baseline_parent_report.exists is explicitly False!")
    for card in cards_fixed:
        print(f"      - {card.get('type')}")
print()

print("=" * 80)
print("DIAGNOSIS:")
print("=" * 80)
print()
print("The issue is in card_generator.py's _get_nested_value():")
print()
print("When checking: baseline_parent_report.exists = false")
print("  - If artifact doesn't exist in context, _get_nested_value() returns None")
print("  - Condition check: None == False → FALSE (condition fails!)")
print("  - Expected: When artifact is missing, exists should be considered False")
print()
print("SOLUTION:")
print("  card_generator needs to handle .exists checks specially:")
print("  - If checking artifact.exists and artifact is missing → treat as exists=False")
print("  - This matches wu_wei_prerequisites.py logic")
print()
