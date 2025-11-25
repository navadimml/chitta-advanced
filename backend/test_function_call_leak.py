"""
Test to reproduce function call leakage bug

The bug: Function call syntax like "(<add_journal_entry>)" appears in conversation text.
The question: WHY is add_journal_entry being invoked when parent shares information?
"""

import asyncio
import logging
from app.services.conversation_service_simplified import get_simplified_conversation_service
from app.services.session_service import get_session_service
from app.services.mock_graphiti import get_mock_graphiti

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_function_call_behavior():
    """Test what happens when parent shares information"""

    family_id = "test_function_leak_001"
    conv_service = get_simplified_conversation_service()
    session_service = get_session_service()
    graphiti = get_mock_graphiti()

    # Scenario: Parent shares information about child's language development
    # Expected: extract_interview_data() should be called
    # Bug: request_action(add_journal_entry) might be called instead

    parent_message = "התפתחות שפה: הוא מתחיל לדבר במשפטים קצרים ומורכבים יותר"

    print(f"\n{'='*60}")
    print(f"TEST: Parent shares language development information")
    print(f"Message: {parent_message}")
    print(f"{'='*60}\n")

    # First, establish basic info
    await conv_service.process_message(family_id, "היי")
    await conv_service.process_message(family_id, "הילד שלי תום, בן 3")

    # Now send the problematic message
    result = await conv_service.process_message(family_id, parent_message)

    print(f"\n{'='*60}")
    print(f"RESULTS:")
    print(f"{'='*60}")
    print(f"Response: {result['response']}")
    print(f"\nFunction calls made:")
    for fc in result.get('function_calls', []):
        print(f"  - {fc['name']}: {fc['arguments']}")

    print(f"\nIntents detected:")
    for intent, value in result.get('intents_detected', {}).items():
        if value:
            print(f"  - {intent}: {value}")

    # Check if wrong function was called
    function_names = [fc['name'] for fc in result.get('function_calls', [])]

    if 'request_action' in function_names:
        print(f"\n🔴 BUG DETECTED: request_action was called!")
        for fc in result['function_calls']:
            if fc['name'] == 'request_action':
                print(f"   Action: {fc['arguments'].get('action')}")
                print(f"   This should have been extract_interview_data instead!")

    if 'extract_interview_data' in function_names:
        print(f"\n✅ CORRECT: extract_interview_data was called")

    # Check conversation history for function syntax
    state = graphiti.get_or_create_state(family_id)
    print(f"\n{'='*60}")
    print(f"CONVERSATION HISTORY:")
    print(f"{'='*60}")
    for i, msg in enumerate(state.conversation[-5:]):
        print(f"{i+1}. [{msg.role}]: {msg.content[:200]}")

        # Check for function call syntax in text
        if '(<' in msg.content or '</' in msg.content:
            print(f"   🔴 FUNCTION SYNTAX DETECTED IN TEXT!")

if __name__ == "__main__":
    asyncio.run(test_function_call_behavior())
