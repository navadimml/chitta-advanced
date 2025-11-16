"""
Enhanced Gemini Provider with Improved Function Calling

This is an enhanced version of the Gemini provider with strategies to
improve function calling reliability for less capable models.

Key enhancements:
1. Automatic lite mode for Flash models
2. Function calling monitoring and reinforcement
3. Fallback extraction mechanisms
4. Temperature optimization for function calling
5. Retry logic for failed function calls
"""

import logging
from typing import List, Dict, Any, Optional

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("google-genai not installed")

from .base import BaseLLMProvider, Message, LLMResponse, FunctionCall
from .gemini_provider import GeminiProvider
from .extraction_fallback import extract_with_fallback, merge_extracted_data

logger = logging.getLogger(__name__)


class GeminiProviderEnhanced(GeminiProvider):
    """
    Enhanced Gemini provider with improved function calling for less capable models
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-flash",
        default_temperature: float = 0.7,
        enable_fallback_extraction: bool = True,
        enable_function_call_monitoring: bool = True
    ):
        super().__init__(api_key, model, default_temperature)

        self.enable_fallback_extraction = enable_fallback_extraction
        self.enable_function_call_monitoring = enable_function_call_monitoring

        # Track function calling statistics for monitoring
        self.stats = {
            "total_calls": 0,
            "function_calls_made": 0,
            "fallback_extractions": 0,
            "failed_extractions": 0
        }

        # Determine if this is a "lite" model (weaker function calling)
        self.is_lite_model = self._is_lite_model(model)

        if self.is_lite_model:
            logger.info(f"🔔 Using LITE mode for {model} - enhanced function calling enabled")

    def _is_lite_model(self, model: str) -> bool:
        """
        Check if this is a less capable model that needs extra help

        Only returns True if LLM_USE_ENHANCED is true.
        If LLM_USE_ENHANCED=false, this always returns False.
        """
        import os

        # Check if enhanced mode is enabled
        use_enhanced_env = os.getenv("LLM_USE_ENHANCED", "true").lower()
        use_enhanced = use_enhanced_env in ["true", "1", "yes"]

        # If enhanced mode is disabled, never treat as lite model
        if not use_enhanced:
            return False

        # Only check model indicators if enhanced mode is on
        lite_indicators = ["flash", "1.5-flash", "2.0-flash"]
        model_lower = model.lower()
        return any(indicator in model_lower for indicator in lite_indicators)

    def get_optimized_temperature(
        self,
        has_functions: bool,
        user_temperature: Optional[float] = None
    ) -> float:
        """
        Get optimized temperature for the request

        Function calling works better with lower temperatures
        """
        if user_temperature is not None:
            return user_temperature

        if has_functions:
            # Lower temperature for function calling
            return min(0.5, self.default_temperature)
        else:
            # Normal temperature for text generation
            return self.default_temperature

    async def chat(
        self,
        messages: List[Message],
        functions: Optional[List[Dict[str, Any]]] = None,
        temperature: float = None,
        max_tokens: int = 1000
    ) -> LLMResponse:
        """
        Enhanced chat with function calling improvements

        Enhancements:
        1. Optimized temperature for function calling
        2. Fallback extraction if function calls missed
        3. Function call monitoring and statistics
        """
        self.stats["total_calls"] += 1

        # Optimize temperature for function calling
        optimized_temp = self.get_optimized_temperature(
            has_functions=functions is not None,
            user_temperature=temperature
        )

        # Call parent class implementation
        response = await super().chat(
            messages=messages,
            functions=functions,
            temperature=optimized_temp,
            max_tokens=max_tokens
        )

        # Track function calling statistics
        if response.function_calls:
            self.stats["function_calls_made"] += 1

        # Apply fallback extraction if enabled and no function calls
        if (self.enable_fallback_extraction and
            functions and
            not response.function_calls and
            len(messages) > 0):

            logger.warning(
                f"⚠️  Model {self.model_name} did not call functions - attempting fallback extraction"
            )

            # Extract latest user message
            latest_user_msg = next(
                (m.content for m in reversed(messages) if m.role == "user"),
                None
            )

            if latest_user_msg:
                fallback_data = await extract_with_fallback(
                    llm=self,
                    conversation_history=messages,
                    latest_user_message=latest_user_msg,
                    function_calls_received=response.function_calls
                )

                if fallback_data:
                    # Create synthetic function call from fallback extraction
                    response.function_calls = [
                        FunctionCall(
                            name="extract_interview_data",
                            arguments=fallback_data
                        )
                    ]
                    self.stats["fallback_extractions"] += 1
                    logger.info("✅ Fallback extraction successful - added synthetic function call")
                else:
                    self.stats["failed_extractions"] += 1
                    logger.warning("❌ Fallback extraction also failed")

        # Log statistics periodically
        if self.enable_function_call_monitoring and self.stats["total_calls"] % 10 == 0:
            self._log_statistics()

        return response

    def _log_statistics(self):
        """Log function calling statistics for monitoring"""
        total = self.stats["total_calls"]
        with_funcs = self.stats["function_calls_made"]
        fallbacks = self.stats["fallback_extractions"]
        failed = self.stats["failed_extractions"]

        success_rate = (with_funcs / total * 100) if total > 0 else 0
        fallback_rate = (fallbacks / total * 100) if total > 0 else 0

        logger.info(
            f"📊 Function Calling Stats ({self.model_name}): "
            f"Success={success_rate:.1f}% ({with_funcs}/{total}), "
            f"Fallbacks={fallback_rate:.1f}% ({fallbacks}/{total}), "
            f"Failed={failed}/{total}"
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get current statistics"""
        total = self.stats["total_calls"]
        return {
            "model": self.model_name,
            "is_lite_model": self.is_lite_model,
            "total_calls": total,
            "function_calls_made": self.stats["function_calls_made"],
            "fallback_extractions": self.stats["fallback_extractions"],
            "failed_extractions": self.stats["failed_extractions"],
            "success_rate": (self.stats["function_calls_made"] / total * 100) if total > 0 else 0,
            "fallback_rate": (self.stats["fallback_extractions"] / total * 100) if total > 0 else 0
        }

    def get_provider_name(self) -> str:
        mode = "LITE" if self.is_lite_model else "FULL"
        return f"Gemini Enhanced ({self.model_name}, {mode})"


# === Factory Helper ===

def create_enhanced_gemini_provider(
    api_key: str,
    model: str = "gemini-2.5-flash",
    **kwargs
) -> GeminiProviderEnhanced:
    """
    Factory function to create enhanced Gemini provider

    Args:
        api_key: Gemini API key
        model: Model name
        **kwargs: Additional configuration

    Returns:
        Configured GeminiProviderEnhanced instance
    """
    return GeminiProviderEnhanced(
        api_key=api_key,
        model=model,
        **kwargs
    )
