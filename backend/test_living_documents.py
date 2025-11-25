#!/usr/bin/env python3
"""
Test script for Living Documents (Phase 3).

Tests:
- Artifact thread model
- Structured artifact parsing
- Thread service operations
- Thread context building
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from app.models.artifact_thread import (
    ArtifactThread,
    ArtifactThreads,
    ThreadMessage,
    ThreadSummary
)
from app.models.structured_artifact import (
    StructuredArtifact,
    ArtifactSection,
    SectionType,
    parse_markdown_to_sections,
    parse_json_to_sections,
    create_structured_artifact
)
from app.services.artifact_thread_service import (
    ArtifactThreadService,
    get_artifact_thread_service
)


def test_thread_message():
    """Test ThreadMessage model."""
    print("\n" + "=" * 60)
    print("Testing ThreadMessage...")
    print("=" * 60)

    msg = ThreadMessage(role="user", content="What does this mean?")
    assert msg.role == "user"
    assert msg.content == "What does this mean?"
    assert msg.message_id is not None
    assert msg.created_at is not None
    print(f"✓ Created message: {msg.message_id[:8]}... ({msg.role})")

    print("\n✅ ThreadMessage tests passed!")
    return True


def test_artifact_thread():
    """Test ArtifactThread model."""
    print("\n" + "=" * 60)
    print("Testing ArtifactThread...")
    print("=" * 60)

    thread = ArtifactThread(
        family_id="test_family",
        artifact_id="baseline_parent_report",
        section_id="motor_development",
        section_title="התפתחות מוטורית",
        section_text="הילד מראה התקדמות יפה..."
    )

    assert thread.thread_id is not None
    assert thread.family_id == "test_family"
    assert thread.artifact_id == "baseline_parent_report"
    assert thread.section_id == "motor_development"
    print(f"✓ Created thread: {thread.thread_id[:8]}...")

    # Add messages
    msg1 = thread.add_message("user", "מה זה אומר לגבי הילד שלי?")
    assert msg1.role == "user"
    assert thread.message_count == 1
    assert thread.preview is not None
    print(f"✓ Added user message, preview: '{thread.preview}'")

    msg2 = thread.add_message("assistant", "זה אומר שהילד שלך מראה התקדמות יפה...")
    assert msg2.role == "assistant"
    assert thread.message_count == 2
    print(f"✓ Added assistant message, count: {thread.message_count}")

    # Get conversation for LLM
    conv = thread.get_conversation_for_llm()
    assert len(conv) == 2
    assert conv[0]["role"] == "user"
    assert conv[1]["role"] == "assistant"
    print(f"✓ Got conversation for LLM: {len(conv)} messages")

    print("\n✅ ArtifactThread tests passed!")
    return True


def test_artifact_threads_collection():
    """Test ArtifactThreads collection."""
    print("\n" + "=" * 60)
    print("Testing ArtifactThreads Collection...")
    print("=" * 60)

    collection = ArtifactThreads(
        artifact_id="baseline_parent_report",
        family_id="test_family"
    )
    assert collection.total_threads == 0
    print("✓ Created empty collection")

    # Add threads
    thread1 = ArtifactThread(
        family_id="test_family",
        artifact_id="baseline_parent_report",
        section_id="motor_development"
    )
    thread1.add_message("user", "Question 1")
    collection.add_thread(thread1)

    thread2 = ArtifactThread(
        family_id="test_family",
        artifact_id="baseline_parent_report",
        section_id="communication"
    )
    thread2.add_message("user", "Question 2")
    collection.add_thread(thread2)

    assert collection.total_threads == 2
    assert collection.unresolved_threads == 2
    print(f"✓ Added 2 threads, total: {collection.total_threads}")

    # Get thread by ID
    found = collection.get_thread(thread1.thread_id)
    assert found is not None
    assert found.section_id == "motor_development"
    print(f"✓ Found thread by ID")

    # Get threads for section
    section_threads = collection.get_threads_for_section("motor_development")
    assert len(section_threads) == 1
    print(f"✓ Got threads for section: {len(section_threads)}")

    # Get summaries
    summaries = collection.get_summaries()
    assert len(summaries) == 2
    assert all(isinstance(s, ThreadSummary) for s in summaries)
    print(f"✓ Got {len(summaries)} summaries")

    print("\n✅ ArtifactThreads collection tests passed!")
    return True


def test_markdown_parsing():
    """Test markdown to sections parsing."""
    print("\n" + "=" * 60)
    print("Testing Markdown Parsing...")
    print("=" * 60)

    markdown = """# דוח הורים

זהו דוח על ההתפתחות של דניאל.

## התפתחות מוטורית

דניאל מראה התקדמות יפה בתחום המוטורי.
הוא יכול לרוץ ולקפוץ.

## תקשורת

התקשורת של דניאל מתפתחת יפה.
הוא משתמש במילים רבות.

## המלצות

- להמשיך עם פעילויות מוטוריות
- לעודד שיחה
"""

    sections = parse_markdown_to_sections("test_report", markdown)

    assert len(sections) >= 4  # Intro + 3 headings
    print(f"✓ Parsed {len(sections)} sections")

    # Check headings
    headings = [s for s in sections if s.section_type == SectionType.HEADING]
    assert len(headings) >= 3
    print(f"✓ Found {len(headings)} headings")

    # Check first heading
    first_heading = headings[0]
    assert "דוח" in first_heading.title or "מוטורית" in first_heading.title
    print(f"✓ First heading: '{first_heading.title}'")

    # Check section IDs are unique
    section_ids = [s.section_id for s in sections]
    assert len(section_ids) == len(set(section_ids))
    print("✓ All section IDs are unique")

    print("\n✅ Markdown parsing tests passed!")
    return True


def test_json_parsing():
    """Test JSON to sections parsing."""
    print("\n" + "=" * 60)
    print("Testing JSON Parsing...")
    print("=" * 60)

    json_content = {
        "summary": "דניאל מראה התפתחות תקינה",
        "focus_areas": ["מוטוריקה", "תקשורת", "חברתי"],
        "scenarios": [
            {"title": "ארוחת בוקר", "description": "צפו בילד במהלך ארוחה"},
            {"title": "משחק", "description": "צפו בילד משחק"}
        ],
        "recommendations": "להמשיך עם פעילויות יומיומיות"
    }

    sections = parse_json_to_sections("test_guidelines", json_content)

    assert len(sections) >= 3
    print(f"✓ Parsed {len(sections)} sections from JSON")

    # Check section titles
    titles = [s.title for s in sections if s.title]
    print(f"✓ Section titles: {titles}")

    print("\n✅ JSON parsing tests passed!")
    return True


def test_structured_artifact():
    """Test StructuredArtifact creation."""
    print("\n" + "=" * 60)
    print("Testing StructuredArtifact...")
    print("=" * 60)

    markdown = """# דוח התפתחות

## סיכום
דניאל בן 3 מראה התפתחות תקינה.

## המלצות
- המשיכו כך
"""

    structured = create_structured_artifact(
        artifact_id="test_report",
        artifact_type="report",
        family_id="test_family",
        title="דוח הורים",
        content=markdown,
        content_format="markdown"
    )

    assert structured.artifact_id == "test_report"
    assert structured.title == "דוח הורים"
    assert len(structured.sections) > 0
    assert structured.raw_content == markdown
    print(f"✓ Created structured artifact with {len(structured.sections)} sections")

    # Test section retrieval
    headings = structured.get_headings()
    assert len(headings) >= 1
    print(f"✓ Got {len(headings)} headings")

    # Test thread count update
    thread_counts = {"test_report_סיכום": 2, "test_report_המלצות": 1}
    structured.update_thread_counts(thread_counts)
    assert structured.total_threads == 3
    print(f"✓ Updated thread counts: {structured.total_threads} total")

    print("\n✅ StructuredArtifact tests passed!")
    return True


def test_thread_service():
    """Test ArtifactThreadService."""
    print("\n" + "=" * 60)
    print("Testing ArtifactThreadService...")
    print("=" * 60)

    service = get_artifact_thread_service()
    assert service is not None
    print("✓ Got ArtifactThreadService singleton")

    # Test thread prompt building
    context = {
        "section_title": "התפתחות מוטורית",
        "section_text": "הילד מראה התקדמות יפה בתחום המוטורי.",
        "thread_history": [
            {"role": "user", "content": "מה זה אומר?"},
            {"role": "assistant", "content": "זה אומר שההתפתחות טובה."}
        ]
    }

    prompt = service.build_thread_prompt(context, "איך אני יכולה לעזור?")
    assert "התפתחות מוטורית" in prompt
    assert "איך אני יכולה לעזור" in prompt
    print("✓ Built thread prompt with context")
    print(f"  Prompt length: {len(prompt)} chars")

    print("\n✅ ArtifactThreadService tests passed!")
    return True


def main():
    """Run all tests."""
    print("\n")
    print("🧪 Living Documents Test Suite (Phase 3)")
    print("=" * 60)

    tests = [
        ("ThreadMessage", test_thread_message),
        ("ArtifactThread", test_artifact_thread),
        ("ArtifactThreads Collection", test_artifact_threads_collection),
        ("Markdown Parsing", test_markdown_parsing),
        ("JSON Parsing", test_json_parsing),
        ("StructuredArtifact", test_structured_artifact),
        ("ArtifactThreadService", test_thread_service),
    ]

    results = {}
    for name, test_fn in tests:
        try:
            results[name] = test_fn()
        except Exception as e:
            print(f"\n❌ {name} failed: {e}")
            import traceback
            traceback.print_exc()
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
        print("\n🎉 All Phase 3 tests passed! Living Documents are working!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
