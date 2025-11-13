#!/usr/bin/env python3
"""
Helper script to delete old markdown-format artifacts and trigger regeneration with new JSON format.

Usage:
    python regenerate_guidelines.py [family_id]

If no family_id is provided, will process all active sessions.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.interview_service import get_interview_service

def regenerate_guidelines(family_id=None):
    """Delete old artifacts to trigger regeneration."""
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

    for fid in families_to_process:
        session = service.get_or_create_session(fid)

        print(f"🔍 Family: {fid}")
        print(f"   Messages: {len(session.conversation_history)}")
        print(f"   Completeness: {session.completeness:.0%}")

        if "baseline_video_guidelines" in session.artifacts:
            artifact = session.artifacts["baseline_video_guidelines"]
            print(f"   📄 Has guidelines artifact (status: {artifact.status})")

            # Check if it's old markdown format
            content = artifact.content if artifact.content else ""
            is_markdown = isinstance(content, str) and content.strip().startswith('#')

            if is_markdown:
                print(f"   ⚠️  OLD MARKDOWN FORMAT DETECTED")
                # Delete it
                del session.artifacts["baseline_video_guidelines"]
                print(f"   ✅ DELETED old artifact")
                print(f"   💡 Next: Continue conversation or trigger lifecycle event")
                print(f"      The artifact will regenerate automatically with JSON format")
            else:
                print(f"   ✅ Already in new JSON format")
        else:
            print(f"   ℹ️  No guidelines artifact yet")

        print()

    print("✅ Done! Old artifacts have been deleted.")
    print()
    print("📝 Next steps:")
    print("   1. Continue the conversation (send a message)")
    print("   2. OR trigger lifecycle event manually")
    print("   3. Guidelines will regenerate automatically in JSON format")
    print()
    print("🧠 Using STRONG_LLM_MODEL from .env for high-quality generation")

if __name__ == "__main__":
    family_id = sys.argv[1] if len(sys.argv) > 1 else None

    if family_id:
        print(f"🎯 Processing family: {family_id}")
    else:
        print("🎯 Processing all active sessions")

    print()
    regenerate_guidelines(family_id)
