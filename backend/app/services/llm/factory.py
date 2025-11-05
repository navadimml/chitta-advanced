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
    model: Optional[str] = None,
    use_enhanced: Optional[bool] = None
) -> BaseLLMProvider:
    """
    Create LLM provider based on environment configuration or explicit parameters

    Args:
        provider_type: Override for LLM_PROVIDER env var ("gemini", "anthropic", "openai", "simulated")
        api_key: Override for API key env var
        model: Override for LLM_MODEL env var
        use_enhanced: Whether to use enhanced provider with fallback extraction (default: True for Gemini)

    Returns:
        Configured LLM provider instance

    Environment Variables:
        LLM_PROVIDER: Which provider to use (default: "simulated")
        LLM_MODEL: Model name (provider-specific)
        LLM_USE_ENHANCED: Whether to use enhanced providers (default: "true")
        GEMINI_API_KEY: Google Gemini API key
        ANTHROPIC_API_KEY: Anthropic Claude API key
        OPENAI_API_KEY: OpenAI API key

    Examples:
        >>> # Use environment variables
        >>> provider = create_llm_provider()

        >>> # Override provider type with enhanced mode
        >>> provider = create_llm_provider(provider_type="gemini", api_key="xxx", use_enhanced=True)
    """

    # Get configuration from parameters or environment
    provider_type = provider_type or os.getenv("LLM_PROVIDER", "simulated")
    provider_type = provider_type.lower()

    # Determine if enhanced mode should be used
    if use_enhanced is None:
        use_enhanced_env = os.getenv("LLM_USE_ENHANCED", "true").lower()
        use_enhanced = use_enhanced_env in ["true", "1", "yes"]

    logger.info(f"Creating LLM provider: {provider_type} (enhanced={use_enhanced})")

    # === Gemini Provider (Recommended) ===
    if provider_type == "gemini":
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY not set, falling back to simulated provider")
            return SimulatedLLMProvider()

        model = model or os.getenv("LLM_MODEL", "gemini-2.0-flash-exp")

        try:
            if use_enhanced:
                # Use enhanced provider with fallback extraction
                from .gemini_provider_enhanced import GeminiProviderEnhanced
                provider = GeminiProviderEnhanced(
                    api_key=api_key,
                    model=model,
                    enable_fallback_extraction=True,
                    enable_function_call_monitoring=True
                )
                logger.info(f"✅ Using Enhanced Gemini provider: {model}")
            else:
                # Use standard provider
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
        Dict with provider information including:
        - configured_provider: The provider set in LLM_PROVIDER env var
        - configured_model: The model set in LLM_MODEL env var
        - available_providers: Dict of which providers have API keys configured
        - will_use: Which provider will actually be used (accounting for fallbacks)
    """
    provider_type = os.getenv("LLM_PROVIDER", "simulated")
    model = os.getenv("LLM_MODEL", "default")

    # Check which API keys are configured
    has_gemini = bool(os.getenv("GEMINI_API_KEY"))
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
    has_openai = bool(os.getenv("OPENAI_API_KEY"))

    # Determine which provider will actually be used
    will_use = provider_type
    if provider_type == "gemini" and not has_gemini:
        will_use = "simulated (gemini key missing)"
    elif provider_type == "anthropic" and not has_anthropic:
        will_use = "simulated (anthropic key missing)"
    elif provider_type == "openai" and not has_openai:
        will_use = "simulated (openai key missing)"
    elif provider_type in ["anthropic", "openai"]:
        will_use = f"simulated ({provider_type} not implemented yet)"

    return {
        "configured_provider": provider_type,
        "configured_model": model,
        "available_providers": {
            "gemini": has_gemini,
            "anthropic": has_anthropic,
            "openai": has_openai,
            "simulated": True
        },
        "will_use": will_use
    }
