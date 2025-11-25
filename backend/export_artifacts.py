"""
Simple script to export all artifacts for a family to JSON files.
Usage: python export_artifacts.py <family_id>
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.services.session_service import get_session_service

def export_artifacts(family_id: str):
    """Export all artifacts for a family to JSON files."""

    # Get session with artifacts
    session_service = get_session_service()
    session = session_service.get_or_create_session(family_id)

    # Create export directory
    export_dir = Path(f"artifacts_export/{family_id}")
    export_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n📂 Exporting artifacts for {family_id}")
    print(f"📁 Export directory: {export_dir.absolute()}\n")

    if not session.artifacts:
        print("⚠️  No artifacts found for this family")
        return

    exported_files = []

    # Export each artifact
    for artifact_id, artifact in session.artifacts.items():
        # Convert Artifact object to dict for JSON serialization
        artifact_data = {
            "artifact_id": artifact_id,
            "status": artifact.status,
            "content": artifact.content,
            "error_message": artifact.error_message,
            "created_at": str(artifact.created_at) if hasattr(artifact, 'created_at') else None,
        }

        # Save to file
        file_path = export_dir / f"{artifact_id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(artifact_data, f, ensure_ascii=False, indent=2)

        exported_files.append(str(file_path))

        # Print summary
        status_emoji = "✅" if artifact.status == "ready" else "⚠️" if artifact.status == "error" else "⏳"
        content_size = len(artifact.content) if artifact.content else 0
        print(f"{status_emoji} {artifact_id}: {artifact.status} ({content_size} chars)")

    print(f"\n✅ Exported {len(exported_files)} artifacts")
    print(f"📁 Files saved to: {export_dir.absolute()}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python export_artifacts.py <family_id>")
        print("\nExample: python export_artifacts.py guidelines_ready_miblgw9g")
        sys.exit(1)

    family_id = sys.argv[1]
    export_artifacts(family_id)
