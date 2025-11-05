"""
Quick test to see what FAQ response looks like
"""

import json

# Simulate what would be returned
from app.services.interview_service import ExtractedData
from datetime import datetime

# Empty extracted data (like when FAQ is hit as first message)
data = ExtractedData()

print("="*80)
print("EXTRACTED DATA STRUCTURE (when FAQ hit early)")
print("="*80)
print(json.dumps(data.model_dump(), indent=2, default=str))

print("\n" + "="*80)
print("EXPECTED VS ACTUAL")
print("="*80)

# Simulate completeness
completeness_internal = 0.0  # 0.0-1.0 scale

print(f"\n1. Internal completeness: {completeness_internal}")
print(f"2. API returns: {completeness_internal * 100}")
print(f"3. routes.py progress calculation: {(completeness_internal * 100) / 100}")
print(f"4. Final progress sent to UI: {(completeness_internal * 100) / 100:.1%}")

# What if there's partial data?
print("\n" + "="*80)
print("WITH SOME DATA (e.g., after privacy question)")
print("="*80)

data2 = ExtractedData()
data2.child_name = "נועה"
data2.age = 4
data2.primary_concerns = ["speech"]

# Calculate completeness
score = 0.0
if data2.child_name:
    score += 0.01
if data2.age:
    score += 0.03
if data2.primary_concerns:
    score += 0.05

print(f"\nExtracted data has:")
print(f"  - child_name: {data2.child_name}")
print(f"  - age: {data2.age}")
print(f"  - concerns: {data2.primary_concerns}")
print(f"\nCalculated completeness:")
print(f"  Internal (0-1): {score:.3f}")
print(f"  API returns: {score * 100:.1f}")
print(f"  UI displays: {score:.1%}")

print("\n" + "="*80)
print("POTENTIAL ISSUES")
print("="*80)
print("""
1. ❓ Pydantic default_factory issue:
   - last_updated uses datetime.now() directly
   - Should use default_factory=datetime.now
   - All instances might share same datetime

2. ❓ Empty data on FAQ path:
   - When FAQ is hit early, no data extracted yet
   - Cards only show progress card (0%)
   - Might look "incomplete" to user

3. ❓ Completeness display:
   - Format string in cards: f"{completeness:.0%}"
   - Expects 0.0-1.0, converts to "0%", "50%", "100%"
   - Should work correctly

4. ✅ API consistency:
   - conversation_service returns: completeness * 100 (0-100)
   - routes.py converts: / 100 (0-1)
   - Should be consistent
""")
