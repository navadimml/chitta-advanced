#!/usr/bin/env python3
"""
Test dev seed endpoint directly to see errors
"""

import asyncio
import sys
import traceback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_seed():
    """Test the seed endpoint directly"""
    try:
        # Import after load_dotenv
        from app.api.dev_routes import seed_test_scenario

        print("🧪 Testing seed endpoint...")
        print("=" * 60)

        result = await seed_test_scenario(
            scenario="early_conversation",
            family_id="test_debug_123"
        )

        print("\n✅ SUCCESS!")
        print(f"Result: {result}")

    except Exception as e:
        print("\n❌ ERROR:")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        print("\nFull traceback:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_seed())
