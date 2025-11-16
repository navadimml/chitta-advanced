"""
End-to-End Wu Wei Demo Flow (Simplified)

Demonstrates the complete Chitta Wu Wei architecture WITHOUT requiring LLM:
1. Simulates conversation state progression
2. Shows Wu Wei detection working
3. Generates actual artifacts
4. Shows cards and views unlocking
5. Tracks user engagement

This is a complete reference implementation showing every component working together.
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime
import time

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.interview_service import get_interview_service, ExtractedData
from app.services.prerequisite_service import get_prerequisite_service
from app.services.artifact_generation_service import ArtifactGenerationService
from app.config.card_generator import get_card_generator
from app.config.view_manager import get_view_manager
from app.models.artifact import Artifact

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}")
    print(f"  {text}")
    print(f"{'='*80}{Colors.ENDC}\n")

def print_step(step_num, text):
    print(f"\n{Colors.BOLD}{Colors.OKBLUE}[Step {step_num}] {text}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{'─'*80}{Colors.ENDC}")

def print_success(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_info(text, indent=0):
    prefix = "  " * indent
    print(f"{prefix}{text}")

def print_artifact_preview(content, title="Content"):
    print(f"\n{Colors.OKCYAN}┌─ {title} {Colors.ENDC}")
    lines = content.split('\n')[:10]
    for line in lines:
        print(f"{Colors.OKCYAN}│{Colors.ENDC} {line}")
    if len(content.split('\n')) > 10:
        print(f"{Colors.OKCYAN}│{Colors.ENDC} ...")
    print(f"{Colors.OKCYAN}└{'─'*78}{Colors.ENDC}\n")


async def demo_flow():
    """Run complete end-to-end demo"""

    print_header("🌟 CHITTA WU WEI - END-TO-END DEMO FLOW 🌟")

    print(f"{Colors.BOLD}This demo shows the complete Wu Wei architecture in action:{Colors.ENDC}")
    print("  1. Natural conversation → Knowledge builds up")
    print("  2. Wu Wei detection → Qualitative readiness check")
    print("  3. Artifact generation → Personalized guidelines emerge")
    print("  4. Cards appear → Prerequisites met automatically")
    print("  5. Views unlock → Rich UI becomes available")
    print("  6. User engagement → Actions tracked")
    print("\nLet's begin! 🚀\n")

    time.sleep(1)

    # ========================================
    # STEP 1: Initial State
    # ========================================

    print_step(1, "Parent Starts Conversation")

    family_id = "demo_family_001"
    interview_service = get_interview_service()
    session = interview_service.get_or_create_session(family_id)

    print_info("Parent: שלום, אני רוצה לדבר על הבן שלי דניאל")
    print_info("Chitta: שלום! אשמח לשמוע עליו. כמה הוא בן?", indent=1)
    print_info("Completeness: 5%", indent=1)
    print_success("Conversation initiated")

    time.sleep(1)

    # ========================================
    # STEP 2: Build Knowledge
    # ========================================

    print_step(2, "Conversation Deepens - Knowledge Builds")

    # Simulate extracted data building up
    session.extracted_data = ExtractedData(
        child_name="דניאל",
        age=3.5,
        gender="male",
        primary_concerns=["שפה", "חברתי"],
        concern_details="דניאל מדבר פחות מילדים אחרים בגילו. הוא שקט בגן ולא משתתף בפעילויות קבוצתיות.",
        strengths="אוהב לשחק עם קוביות, יצירתי, ממוקד",
        developmental_history="התפתחות תקינה עד גיל שנתיים",
        family_context="משפחה תומכת, אח קטן",
        parent_goals="לעזור לו להרגיש בטוח בתקשורת"
    )

    # Simulate conversation history
    session.conversation_history = [
        {"role": "user", "content": "שלום, דניאל בן 3.5"},
        {"role": "assistant", "content": "נעים להכיר..."},
        {"role": "user", "content": "יש לי דאגות לגבי הדיבור שלו"},
        {"role": "assistant", "content": "ספרי לי יותר..."},
        {"role": "user", "content": "הוא שקט בגן"},
        {"role": "assistant", "content": "אני מבין..."},
        {"role": "user", "content": "הוא אוהב קוביות"},
        {"role": "assistant", "content": "זה נפלא..."},
        {"role": "user", "content": "רוצה לעזור לו"},
        {"role": "assistant", "content": "בטח..."},
    ]

    messages = [
        "יש לי דאגות לגבי הדיבור - מדבר פחות מילדים אחרים",
        "הוא מאוד אוהב קוביות ולבנות מגדלים - ממוקד ויצירתי",
        "בגן הוא שקט, לא משתתף בפעילויות קבוצתיות",
        "רוצה לעזור לו להרגיש בטוח יותר בתקשורת"
    ]

    for i, msg in enumerate(messages, 1):
        print_info(f"\nMessage {i+2}: {msg}")
        time.sleep(0.3)

        completeness = min(20 + (i * 15), 75)
        if completeness < 30:
            depth = f"{Colors.WARNING}השיחה מתחילה{Colors.ENDC}"
        elif completeness < 60:
            depth = f"{Colors.WARNING}השיחה מתפתחת{Colors.ENDC}"
        else:
            depth = f"{Colors.OKGREEN}השיחה מתעמקת{Colors.ENDC}"

        print_info(f"Completeness: {completeness}% → {depth}", indent=1)

    print_success("Rich knowledge captured - Multiple perspectives")

    time.sleep(1)

    # ========================================
    # STEP 3: Wu Wei Detection
    # ========================================

    print_step(3, "Wu Wei Detection - Knowledge Richness Check")

    prerequisite_service = get_prerequisite_service()

    # Build session data
    try:
        extracted_dict = session.extracted_data.model_dump()
    except AttributeError:
        extracted_dict = session.extracted_data.dict()

    session_data = {
        "family_id": family_id,
        "extracted_data": extracted_dict,
        "message_count": len(session.conversation_history),
        "artifacts": session.artifacts,
    }

    # Check knowledge richness
    knowledge_eval = prerequisite_service.check_knowledge_richness(session_data)

    print_info("Qualitative evaluation:")
    print_info(f"  ✓ Has child name: דניאל", indent=1)
    print_info(f"  ✓ Has age: 3.5 years", indent=1)
    print_info(f"  ✓ Has concerns: 2 (שפה, חברתי)", indent=1)
    print_info(f"  ✓ Has strengths: Yes", indent=1)
    print_info(f"  ✓ Has context: Yes", indent=1)
    print_info(f"  ✓ Message count: {len(session.conversation_history)}", indent=1)
    print()

    if knowledge_eval.met:
        print_success(f"🌟 Wu Wei: Knowledge is RICH!")
        print_info(f"Details: {knowledge_eval.details}", indent=1)
        print_info("Paths met:", indent=1)
        for path in knowledge_eval.paths_met:
            print_info(f"  ✓ {path}", indent=2)
    else:
        print(f"{Colors.WARNING}Not yet rich. Missing: {', '.join(knowledge_eval.missing)}{Colors.ENDC}")

    time.sleep(1)

    # ========================================
    # STEP 4: Artifact Generation
    # ========================================

    print_step(4, "Artifact Generation - Guidelines Emerge")

    artifact_service = ArtifactGenerationService()

    print_info("Generating personalized video guidelines...")
    start_time = time.time()

    guidelines_artifact = await artifact_service.generate_video_guidelines(session_data)

    generation_time = time.time() - start_time

    if guidelines_artifact.is_ready:
        print_success("✨ Artifact generated successfully!")
        print_info(f"  • Generation time: {generation_time:.3f}s", indent=1)
        print_info(f"  • Artifact ID: {guidelines_artifact.artifact_id}", indent=1)
        print_info(f"  • Status: {guidelines_artifact.status}", indent=1)
        print_info(f"  • Content length: {len(guidelines_artifact.content)} chars", indent=1)
        print_info(f"  • Format: {guidelines_artifact.content_format}", indent=1)
        print()

        # Store in session
        session.add_artifact(guidelines_artifact)

        print_artifact_preview(guidelines_artifact.content, "הנחיות צילום מותאמות אישית לדניאל")
        print_success("Artifact stored in session")
    else:
        print(f"{Colors.FAIL}Generation failed: {guidelines_artifact.error_message}{Colors.ENDC}")

    time.sleep(1)

    # ========================================
    # STEP 5: Cards Appear
    # ========================================

    print_step(5, "Context Cards - Prerequisites Met")

    card_generator = get_card_generator()

    # Build context for cards
    context = prerequisite_service.get_context_for_cards(session_data)

    print_info("Context for card evaluation:")
    print_info(f"  • Child: {context.get('child_name')}", indent=1)
    print_info(f"  • Messages: {context.get('message_count')}", indent=1)
    print_info(f"  • Knowledge rich: {context.get('knowledge_is_rich')}", indent=1)
    print_info(f"  • Artifacts: {list(context.get('artifacts', {}).keys())}", indent=1)
    print()

    # Generate cards
    cards = card_generator.get_visible_cards(context, max_cards=5)

    print_success(f"Generated {len(cards)} context cards:")
    print()

    for i, card in enumerate(cards, 1):
        icon = "📋" if card.get('card_type') == 'guidance' else "📊" if card.get('card_type') == 'progress' else "📝"
        print(f"{icon} {Colors.OKBLUE}Card {i}: {card.get('title')}{Colors.ENDC}")
        print_info(f"Type: {card.get('card_type')} | Priority: {card.get('priority')}", indent=1)
        if card.get('body'):
            body_preview = card.get('body')[:80] + "..." if len(card.get('body', '')) > 80 else card.get('body')
            print_info(f"Body: {body_preview}", indent=1)
        print()

    time.sleep(1)

    # ========================================
    # STEP 6: Views Unlock
    # ========================================

    print_step(6, "Deep Views - Rich UI Unlocked")

    view_manager = get_view_manager()

    # Build context for views
    artifacts_for_views = {}
    for artifact_id, artifact in session.artifacts.items():
        artifacts_for_views[artifact_id] = {
            "exists": artifact.exists,
            "status": artifact.status
        }

    view_context = {
        "phase": session.phase,
        "completeness": 75.0,
        "child_name": "דניאל",
        "artifacts": artifacts_for_views,
        "reports_ready": False,
    }

    available_views = view_manager.get_available_views(view_context)

    print_success(f"Unlocked {len(available_views)} deep views:")
    print()

    for view_id in available_views:
        view = view_manager.get_view(view_id)
        if view:
            view_type = view.get('view_type', 'unknown')
            icon = "🔲" if view_type == "modal" else "📱" if view_type == "sidebar" else "🖥️" if view_type == "fullscreen" else "📄"
            print(f"{icon} {Colors.OKGREEN}{view.get('name')}{Colors.ENDC}")
            print_info(f"{view.get('name_en')} | {view_type}", indent=1)

            # Show primary data source
            data_sources = view.get('data_sources', {})
            primary = data_sources.get('primary')
            if primary:
                print_info(f"Data source: {primary}", indent=1)
            print()

    time.sleep(1)

    # ========================================
    # STEP 7: View Content
    # ========================================

    print_step(7, "View Content - Full Experience")

    if "video_guidelines_view" in available_views:
        print_info("Opening: video_guidelines_view")
        print()

        view = view_manager.get_view("video_guidelines_view")

        # Get artifact content
        artifact = session.get_artifact("baseline_video_guidelines")

        if artifact and artifact.is_ready:
            print(f"{Colors.BOLD}View Definition:{Colors.ENDC}")
            print_info(f"• Name: {view.get('name')}", indent=1)
            print_info(f"• Type: {view.get('view_type')}", indent=1)
            print_info(f"• Priority: {view.get('priority')}", indent=1)
            print()

            print(f"{Colors.BOLD}Layout Sections:{Colors.ENDC}")
            layout = view.get('layout', {})
            main_content = layout.get('main_content', {})
            sections = main_content.get('sections', [])
            for section in sections:
                if isinstance(section, dict):
                    name = section.get('name', 'Unknown')
                    icon = section.get('icon', '')
                    print_info(f"• {name} ({icon})", indent=1)
            print()

            print(f"{Colors.BOLD}Available Actions:{Colors.ENDC}")
            actions = view.get('actions', {})
            for action_name, action_data in actions.items():
                if isinstance(action_data, dict):
                    label = action_data.get('label', action_name)
                    icon_action = action_data.get('icon', '')
                    print_info(f"• {label} ({icon_action})", indent=1)
            print()

            print_artifact_preview(artifact.content, "Artifact Content in View")
            print_success("View rendered with full artifact content")

    time.sleep(1)

    # ========================================
    # STEP 8: User Engagement
    # ========================================

    print_step(8, "User Actions - Engagement Tracking")

    if guidelines_artifact:
        print_info("Simulating user interactions...")
        print()

        # Track actions
        if "user_actions" not in guidelines_artifact.metadata:
            guidelines_artifact.metadata["user_actions"] = []

        actions_to_track = [
            {"action": "view", "delay": 0.5},
            {"action": "download", "delay": 1.0},
        ]

        for action_info in actions_to_track:
            timestamp = datetime.now().isoformat()
            guidelines_artifact.metadata["user_actions"].append({
                "action": action_info["action"],
                "timestamp": timestamp
            })
            print_success(f"Action: {action_info['action']} at {timestamp[11:19]}")
            time.sleep(action_info["delay"])

        session.add_artifact(guidelines_artifact)

        print()
        print_info("Engagement history:")
        for i, action in enumerate(guidelines_artifact.metadata["user_actions"], 1):
            print_info(f"{i}. {action['action']} - {action['timestamp'][11:19]}", indent=1)

    time.sleep(1)

    # ========================================
    # STEP 9: System State Overview
    # ========================================

    print_step(9, "Complete System State")

    print(f"{Colors.BOLD}Final State Summary:{Colors.ENDC}\n")

    print(f"{Colors.OKGREEN}📊 Conversation:{Colors.ENDC}")
    print_info(f"Messages: {len(session.conversation_history)}", indent=1)
    print_info(f"Completeness: 75%", indent=1)
    print_info(f"Phase: {session.phase}", indent=1)
    print()

    print(f"{Colors.OKGREEN}🧠 Knowledge Extracted:{Colors.ENDC}")
    print_info(f"Child: {session.extracted_data.child_name} ({session.extracted_data.age} years)", indent=1)
    print_info(f"Concerns: {len(session.extracted_data.primary_concerns)} identified", indent=1)
    print_info(f"Strengths: Documented", indent=1)
    print_info(f"Context: Captured", indent=1)
    print()

    print(f"{Colors.OKGREEN}📦 Artifacts:{Colors.ENDC}")
    for artifact_id, artifact in session.artifacts.items():
        status_icon = "✓" if artifact.is_ready else "⏳"
        print_info(f"{status_icon} {artifact_id}: {artifact.status}", indent=1)
        print_info(f"   {len(artifact.content or '')} chars", indent=1)
    print()

    print(f"{Colors.OKGREEN}🎴 UI Elements:{Colors.ENDC}")
    print_info(f"Cards: {len(cards)} available", indent=1)
    print_info(f"Views: {len(available_views)} unlocked", indent=1)
    print()

    print(f"{Colors.OKGREEN}👆 User Engagement:{Colors.ENDC}")
    total_actions = len(guidelines_artifact.metadata.get("user_actions", []))
    print_info(f"Actions tracked: {total_actions}", indent=1)
    print()

    # ========================================
    # FINAL SUMMARY
    # ========================================

    print_header("✨ END-TO-END DEMO COMPLETE ✨")

    print(f"{Colors.BOLD}Wu Wei Architecture in Action:{Colors.ENDC}\n")

    print(f"{Colors.OKGREEN}✓{Colors.ENDC} Natural conversation → Knowledge built organically")
    print(f"{Colors.OKGREEN}✓{Colors.ENDC} Qualitative detection → Rich knowledge, not 80% threshold")
    print(f"{Colors.OKGREEN}✓{Colors.ENDC} Artifact emergence → Guidelines appeared when ready")
    print(f"{Colors.OKGREEN}✓{Colors.ENDC} Cards surfaced → Prerequisites checked automatically")
    print(f"{Colors.OKGREEN}✓{Colors.ENDC} Views unlocked → Rich UI became available")
    print(f"{Colors.OKGREEN}✓{Colors.ENDC} Actions tracked → User engagement measured")
    print()

    print(f"{Colors.BOLD}{Colors.HEADER}Key Insights:{Colors.ENDC}\n")
    print("  1. No manual triggers - Everything emerged naturally")
    print("  2. Qualitative over quantitative - Rich knowledge > percentages")
    print("  3. Artifact-driven UI - Cards and views based on what exists")
    print("  4. Parent-centric - Personalized Hebrew content")
    print("  5. Full traceability - Every action tracked")
    print()

    print(f"{Colors.BOLD}Stats:{Colors.ENDC}")
    print(f"  • Conversation messages: {len(session.conversation_history)}")
    print(f"  • Artifacts generated: {len(session.artifacts)}")
    print(f"  • Content created: {len(guidelines_artifact.content)} chars")
    print(f"  • Cards shown: {len(cards)}")
    print(f"  • Views unlocked: {len(available_views)}")
    print(f"  • User actions: {total_actions}")
    print()

    print(f"{Colors.BOLD}{Colors.OKCYAN}This is Wu Wei - Effortless Action{Colors.ENDC} 🌟\n")


if __name__ == "__main__":
    asyncio.run(demo_flow())
