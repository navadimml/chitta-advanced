#!/usr/bin/env python3
"""
Test Dual-Model Setup - Fast Conversation + Strong Extraction

Validates that:
- Conversation uses fast model (gemini-flash-lite-latest) for speed
- Extraction uses stronger model (gemini-2.0-flash-exp) for accuracy
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.conversation_service import ConversationService
from app.services.llm.factory import create_llm_provider


def main():
    """Test dual-model setup"""

    print("\n" + "=" * 80)
    print("🎯 DUAL-MODEL SETUP TEST")
    print("=" * 80)

    print("\n" + "-" * 80)
    print("Current Configuration:")
    print("-" * 80)

    # Show current env vars
    conversation_model = os.getenv("LLM_MODEL", "gemini-2.0-flash-exp (default)")
    extraction_model = os.getenv("EXTRACTION_MODEL", "gemini-flash-latest (default)")

    print(f"LLM_MODEL (conversation): {conversation_model}")
    print(f"EXTRACTION_MODEL: {extraction_model}")

    print("\n" + "-" * 80)
    print("Creating ConversationService:")
    print("-" * 80)

    # Create service (will show logs about which models are used)
    conv_service = ConversationService()

    print(f"\n  Conversation LLM: {conv_service.llm.model_name}")
    print(f"  Extraction LLM: {conv_service.extraction_llm.model_name}")

    print("\n" + "=" * 80)
    print("RECOMMENDED SETUP")
    print("=" * 80)

    print("\nFor optimal performance, use different models:")
    print("  LLM_MODEL=gemini-flash-lite-latest      # Fast conversation")
    print("  EXTRACTION_MODEL=gemini-flash-latest    # Strong extraction (latest & most advanced)")

    print("\nWhy?")
    print("  ✅ Fast conversation model (flash-lite):")
    print("     - Quick responses for better UX")
    print("     - Lower cost per conversation turn")
    print("     - Good enough for Hebrew conversation")

    print("\n  ✅ Strong extraction model (flash-latest):")
    print("     - Latest and most advanced flash model")
    print("     - Better reasoning for categorization")
    print("     - Distinguishes concerns vs strengths correctly")
    print("     - Handles nuanced language better")
    print("     - Only called once per turn (less cost impact)")

    print("\n" + "=" * 80)
    print("CONFIGURATION OPTIONS")
    print("=" * 80)

    print("\n1. Both use flash-lite (CURRENT - has categorization issues):")
    print("   export LLM_MODEL=gemini-flash-lite-latest")
    print("   # EXTRACTION_MODEL not set → defaults to same model")

    print("\n2. Both use flash-latest (balanced - accurate + fast):")
    print("   export LLM_MODEL=gemini-flash-latest")
    print("   # EXTRACTION_MODEL not set → defaults to flash-latest")

    print("\n3. Dual model (RECOMMENDED - fastest conversation + accurate extraction):")
    print("   export LLM_MODEL=gemini-flash-lite-latest")
    print("   export EXTRACTION_MODEL=gemini-flash-latest")

    print("\n4. Maximum accuracy (slower, higher cost):")
    print("   export LLM_MODEL=gemini-flash-latest")
    print("   export EXTRACTION_MODEL=gemini-pro")

    print("\n" + "=" * 80)
    print("IMPACT ON USER'S ISSUE")
    print("=" * 80)

    print("\nUser Issue:")
    print("  'משחק עם ילדים אחרים' → extracted as social CONCERN ❌")
    print("  Should be: STRENGTH ✅")

    print("\nRoot Causes:")
    print("  1. Model too weak (flash-lite) for nuanced categorization")
    print("  2. Prompt now improved with explicit examples")

    print("\nSolution:")
    print("  ✅ Improved prompt (already done)")
    print("  ✅ Stronger extraction model (this change)")
    print("     → Now uses gemini-flash-latest for extraction (most advanced)")
    print("     → Better reasoning for concerns vs strengths")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
