"""
LLM Factory - Creates appropriate provider based on configuration

Supports:
- Gemini (recommended for Chitta)
- Claude (Anthropic)
- GPT-4 (OpenAI)
- Simulated (for development)
"""

import os
import logging
from typing import Optional

from .base import BaseLLMProvider
from .simulated_provider import SimulatedLLMProvider

logger = logging.getLogger(__name__)


def create_llm_provider(
    provider_type: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None
) -> BaseLLMProvider:
    """
    Create LLM provider based on environment configuration or explicit parameters

    Args:
        provider_type: Override for LLM_PROVIDER env var ("gemini", "anthropic", "openai", "simulated")
        api_key: Override for API key env var
        model: Override for LLM_MODEL env var

    Returns:
        Configured LLM provider instance

    Environment Variables:
        LLM_PROVIDER: Which provider to use (default: "simulated")
        LLM_MODEL: Model name (provider-specific)
        GEMINI_API_KEY: Google Gemini API key
        ANTHROPIC_API_KEY: Anthropic Claude API key
        OPENAI_API_KEY: OpenAI API key

    Examples:
        >>> # Use environment variables
        >>> provider = create_llm_provider()

        >>> # Override provider type
        >>> provider = create_llm_provider(provider_type="gemini", api_key="xxx")
    """

    # Get configuration from parameters or environment
    provider_type = provider_type or os.getenv("LLM_PROVIDER", "simulated")
    provider_type = provider_type.lower()

    logger.info(f"Creating LLM provider: {provider_type}")

    # === Gemini Provider (Recommended) ===
    if provider_type == "gemini":
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY not set, falling back to simulated provider")
            return SimulatedLLMProvider()

        model = model or os.getenv("LLM_MODEL", "gemini-2.0-flash-exp")

        try:
            from .gemini_provider import GeminiProvider
            provider = GeminiProvider(api_key=api_key, model=model)
            logger.info(f"✅ Using Gemini provider: {model}")
            return provider
        except ImportError as e:
            logger.error(f"Failed to import GeminiProvider: {e}")
            logger.error("Install with: pip install google-genai")
            logger.warning("Falling back to simulated provider")
            return SimulatedLLMProvider()
        except Exception as e:
            logger.error(f"Failed to create Gemini provider: {e}")
            logger.warning("Falling back to simulated provider")
            return SimulatedLLMProvider()

    # === Anthropic Claude Provider ===
    elif provider_type == "anthropic" or provider_type == "claude":
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("ANTHROPIC_API_KEY not set, falling back to simulated provider")
            return SimulatedLLMProvider()

        model = model or os.getenv("LLM_MODEL", "claude-3-5-sonnet-20241022")

        logger.warning("Anthropic provider not yet implemented")
        logger.info("Falling back to simulated provider")
        return SimulatedLLMProvider()

        # Future implementation:
        # from .anthropic_provider import AnthropicProvider
        # return AnthropicProvider(api_key=api_key, model=model)

    # === OpenAI GPT-4 Provider ===
    elif provider_type == "openai" or provider_type == "gpt":
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY not set, falling back to simulated provider")
            return SimulatedLLMProvider()

        model = model or os.getenv("LLM_MODEL", "gpt-4-turbo-preview")

        logger.warning("OpenAI provider not yet implemented")
        logger.info("Falling back to simulated provider")
        return SimulatedLLMProvider()

        # Future implementation:
        # from .openai_provider import OpenAIProvider
        # return OpenAIProvider(api_key=api_key, model=model)

    # === Simulated Provider (Default) ===
    else:
        if provider_type != "simulated":
            logger.warning(f"Unknown provider type: {provider_type}, using simulated")

        provider = SimulatedLLMProvider()
        logger.info("✅ Using simulated provider (no API calls)")
        return provider


def get_provider_info() -> dict:
    """
    Get information about current provider configuration

    Returns:
        Dict with provider information
    """
    provider_type = os.getenv("LLM_PROVIDER", "simulated")
    model = os.getenv("LLM_MODEL", "default")

    # Check which API keys are configured
    has_gemini = bool(os.getenv("GEMINI_API_KEY"))
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
    has_openai = bool(os.getenv("OPENAI_API_KEY"))

    return {
        "configured_provider": provider_type,
        "configured_model": model,
        "available_providers": {
            "gemini": has_gemini,
            "anthropic": has_anthropic,
            "openai": has_openai,
            "simulated": True
        }
    }
