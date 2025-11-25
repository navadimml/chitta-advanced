#!/usr/bin/env python3
"""
Test Extraction Validation - Verify gibberish and off-topic concerns are rejected
"""
import sys
import os
sys.path.insert(0, os.getcwd())

from app.services.session_service import ExtractedData, SessionService

def test_gibberish_name():
    """Test that gibberish names are rejected"""
    print("\n" + "="*80)
    print("Test 1: Gibberish name rejection")
    print("="*80)

    gibberish_inputs = [
        "nv vurtu",  # ROT13-like gibberish
        "akl vprunpy",  # More gibberish
        "!!!",  # Only punctuation
        "123",  # Only numbers
        "x",  # Too short
        "",  # Empty
    ]

    for gibberish in gibberish_inputs:
        try:
            data = ExtractedData(child_name=gibberish)
            if data.child_name is None:
                print(f"✅ PASS: Rejected gibberish name '{gibberish}'")
            else:
                print(f"❌ FAIL: Accepted gibberish name '{gibberish}' as '{data.child_name}'")
        except Exception as e:
            print(f"⚠️  Exception for '{gibberish}': {e}")

def test_valid_hebrew_names():
    """Test that valid Hebrew names are accepted"""
    print("\n" + "="*80)
    print("Test 2: Valid Hebrew names acceptance")
    print("="*80)

    valid_names = [
        "ליל",
        "דניאל",
        "נועה",
        "יוסף",
        "שרה"
    ]

    for name in valid_names:
        try:
            data = ExtractedData(child_name=name)
            if data.child_name == name:
                print(f"✅ PASS: Accepted valid Hebrew name '{name}'")
            else:
                print(f"❌ FAIL: Rejected valid Hebrew name '{name}'")
        except Exception as e:
            print(f"❌ FAIL: Exception for '{name}': {e}")

def test_concern_validation():
    """Test that 'other' as sole concern is rejected"""
    print("\n" + "="*80)
    print("Test 3: Concern validation")
    print("="*80)

    # Test 1: 'other' as sole concern (should be rejected)
    data1 = ExtractedData(primary_concerns=['other'])
    if len(data1.primary_concerns) == 0:
        print("✅ PASS: Rejected 'other' as sole concern")
    else:
        print(f"❌ FAIL: Accepted 'other' as sole concern: {data1.primary_concerns}")

    # Test 2: 'other' with valid concern (should be accepted)
    data2 = ExtractedData(primary_concerns=['speech', 'other'])
    if 'speech' in data2.primary_concerns and 'other' in data2.primary_concerns:
        print("✅ PASS: Accepted 'other' when combined with 'speech'")
    else:
        print(f"❌ FAIL: Rejected valid combined concerns: {data2.primary_concerns}")

    # Test 3: Valid concerns only (should be accepted)
    data3 = ExtractedData(primary_concerns=['speech', 'social'])
    if data3.primary_concerns == ['speech', 'social']:
        print("✅ PASS: Accepted valid concerns ['speech', 'social']")
    else:
        print(f"❌ FAIL: Incorrect concerns: {data3.primary_concerns}")

    # Test 4: Invalid concern (should be filtered out)
    data4 = ExtractedData(primary_concerns=['speech', 'invalid_concern'])
    if data4.primary_concerns == ['speech']:
        print("✅ PASS: Filtered out invalid concern, kept 'speech'")
    else:
        print(f"❌ FAIL: Incorrect filtering: {data4.primary_concerns}")

def test_full_extraction():
    """Test full extraction with valid data"""
    print("\n" + "="*80)
    print("Test 4: Full extraction with valid data")
    print("="*80)

    service = SessionService()
    family_id = "test_extraction_validation"

    # Test valid extraction: "ליל והיא בת 12"
    service.update_extracted_data(family_id, {
        'child_name': 'ליל',
        'age': 12,
        'gender': 'female'
    })

    session = service.get_or_create_session(family_id)
    data = session.extracted_data

    if data.child_name == 'ליל' and data.age == 12 and data.gender == 'female':
        print("✅ PASS: Successfully extracted valid Hebrew data")
        print(f"   Name: {data.child_name}, Age: {data.age}, Gender: {data.gender}")
    else:
        print("❌ FAIL: Failed to extract valid data")
        print(f"   Got: name={data.child_name}, age={data.age}, gender={data.gender}")

def main():
    print("\n🧪 Testing Extraction Validation")
    print("="*80)
    print("Verifying that gibberish and off-topic concerns are properly rejected")
    print("="*80)

    test_gibberish_name()
    test_valid_hebrew_names()
    test_concern_validation()
    test_full_extraction()

    print("\n" + "="*80)
    print("✅ All tests completed")
    print("="*80)

if __name__ == "__main__":
    main()
