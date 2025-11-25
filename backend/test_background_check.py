#!/usr/bin/env python3
"""
Test background completeness check - verify it doesn't block responses
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000/api"

def send_message(family_id: str, message: str, turn_num: int):
    """Send a message and measure response time"""
    start_time = time.time()

    response = requests.post(
        f"{BASE_URL}/chat/send",
        json={
            "family_id": family_id,
            "message": message
        }
    )

    elapsed = time.time() - start_time

    if response.status_code == 200:
        data = response.json()
        print(f"\n{'='*80}")
        print(f"Turn {turn_num}: ✅ Response in {elapsed:.2f}s")
        print(f"Message: {message[:50]}...")
        print(f"Response: {data.get('response', '')[:100]}...")
        print(f"{'='*80}")
    else:
        print(f"\n❌ Turn {turn_num} failed: {response.status_code}")
        print(f"Error: {response.text}")

    return elapsed

def main():
    # Use test family
    family_id = "test_background_check_family"

    print("\n🧪 Testing Background Completeness Check")
    print("=" * 80)
    print("Plan:")
    print("1. Send messages 1-6 (check triggers at turn 6)")
    print("2. Verify turn 6 response is FAST (not blocked)")
    print("3. Send turn 7 (should receive check result)")
    print("=" * 80)

    # Conversation to reach turn 6
    messages = [
        "שלום, אני רוצה לדבר על הילד שלי",  # Turn 1
        "השם שלו דניאל והוא בן 3",  # Turn 2
        "יש לי דאגות לגבי דיבור וחברתיות",  # Turn 3
        "הוא מתקשה לדבר במשפטים מלאים",  # Turn 4
        "והוא לא ממש משחק עם ילדים אחרים",  # Turn 5
        "מה אני צריכה לעשות?"  # Turn 6 - CHECK TRIGGERS HERE!
    ]

    response_times = []

    for i, msg in enumerate(messages, 1):
        elapsed = send_message(family_id, msg, i)
        response_times.append(elapsed)

        # Small delay between messages
        time.sleep(0.5)

    # Analyze turn 6 performance
    print("\n📊 Performance Analysis:")
    print(f"Average response time (turns 1-5): {sum(response_times[:5]) / 5:.2f}s")
    print(f"Turn 6 response time: {response_times[5]:.2f}s")

    if response_times[5] < sum(response_times[:5]) / 5 + 2:
        print("✅ Turn 6 was FAST - background check didn't block!")
    else:
        print("❌ Turn 6 was SLOW - check may have blocked")

    # Wait a bit for background check to complete
    print("\n⏳ Waiting 3s for background check to complete...")
    time.sleep(3)

    # Send turn 7 - should receive check result
    print("\n📬 Sending turn 7 to receive check result...")
    send_message(family_id, "תודה, אני רוצה להמשיך לדבר", 7)

    print("\n✅ Test complete! Check backend logs for:")
    print("   - '🚀 Background check task started'")
    print("   - '✅ Background completeness check completed'")
    print("   - '✅ Completeness check context injected'")

if __name__ == "__main__":
    main()
