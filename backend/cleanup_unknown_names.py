#!/usr/bin/env python3
"""
Data cleanup script: Fix sessions with 'unknown' as child_name

This script fixes the bug where 'unknown' was being stored as the actual child name,
preventing proper prerequisite evaluation.

Usage:
    python cleanup_unknown_names.py [family_id]

If no family_id is provided, will process all active sessions.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.interview_service import get_interview_service

def cleanup_unknown_names(family_id=None):
    """Fix sessions with 'unknown' as child_name."""
    service = get_interview_service()

    if family_id:
        # Process specific family
        families_to_process = [family_id]
    else:
        # Process all active sessions
        families_to_process = list(service.sessions.keys())

    if not families_to_process:
        print("❌ No active sessions found")
        return

    print(f"📋 Found {len(families_to_process)} active session(s)")
    print()

    fixed_count = 0

    for fid in families_to_process:
        session = service.get_or_create_session(fid)
        data = session.extracted_data

        print(f"🔍 Family: {fid}")
        print(f"   Current child_name: {data.child_name!r}")

        # Check if child_name is 'unknown' or '(not mentioned yet)'
        if data.child_name in ['unknown', '(not mentioned yet)']:
            print(f"   ⚠️  INVALID NAME DETECTED: {data.child_name!r}")
            # Clear the invalid name
            data.child_name = None
            print(f"   ✅ CLEARED - set to None")
            fixed_count += 1

            # Also delete any artifacts that were generated with wrong data
            if "baseline_video_guidelines" in session.artifacts:
                print(f"   🗑️  DELETING artifact (will regenerate with correct data)")
                del session.artifacts["baseline_video_guidelines"]

        else:
            print(f"   ✅ Name is valid")

        print()

    print(f"✅ Done! Fixed {fixed_count} session(s)")

    if fixed_count > 0:
        print()
        print("📝 Next steps:")
        print("   1. Continue the conversation (send a message)")
        print("   2. System will re-extract child name properly")
        print("   3. Once name is correct, prerequisites will be met")
        print("   4. Artifacts will regenerate automatically")

if __name__ == "__main__":
    family_id = sys.argv[1] if len(sys.argv) > 1 else None

    if family_id:
        print(f"🎯 Processing family: {family_id}")
    else:
        print("🎯 Processing all active sessions")

    print()
    cleanup_unknown_names(family_id)
