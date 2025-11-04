"""
Google Gemini Provider

Recommended provider for Chitta:
- Free during preview period
- Native video analysis (crucial for video screening)
- 1M token context window
- Excellent Hebrew support
- Function calling support
- JSON mode for structured output
"""

import logging
from typing import List, Dict, Any, Optional
import json

try:
    import google.generativeai as genai
    from google.generativeai import GenerativeModel
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("google-genai not installed. Install with: pip install google-genai")

from .base import BaseLLMProvider, Message, LLMResponse, FunctionCall

logger = logging.getLogger(__name__)


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM Provider"""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash-exp",
        default_temperature: float = 0.7
    ):
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-genai is not installed. Install with: pip install google-genai"
            )

        # Configure Gemini
        genai.configure(api_key=api_key)

        self.model_name = model
        self.default_temperature = default_temperature

        # Safety settings - minimal blocking for clinical conversations
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        logger.info(f"✅ Gemini provider initialized: {model}")

    async def chat(
        self,
        messages: List[Message],
        functions: Optional[List[Dict[str, Any]]] = None,
        temperature: float = None,
        max_tokens: int = 1000
    ) -> LLMResponse:
        """
        Send chat completion with optional function calling

        Args:
            messages: Conversation messages
            functions: Function definitions for function calling
            temperature: Sampling temperature
            max_tokens: Maximum output tokens

        Returns:
            LLMResponse with content and function calls
        """
        temp = temperature if temperature is not None else self.default_temperature

        # Convert messages to Gemini format
        gemini_messages = self._convert_messages_to_gemini(messages)

        # Prepare tools if functions provided
        tools = None
        if functions:
            tools = self._convert_functions_to_tools(functions)

        # Create model with configuration
        generation_config = {
            "temperature": temp,
            "max_output_tokens": max_tokens,
        }

        model = GenerativeModel(
            model_name=self.model_name,
            generation_config=generation_config,
            safety_settings=self.safety_settings,
            tools=tools
        )

        try:
            # Generate response
            response = await model.generate_content_async(gemini_messages)

            # Parse response
            return self._parse_gemini_response(response)

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            # Return error response
            return LLMResponse(
                content=f"Error: {str(e)}",
                function_calls=[],
                finish_reason="error"
            )

    async def chat_with_structured_output(
        self,
        messages: List[Message],
        response_schema: Dict[str, Any],
        temperature: float = None
    ) -> Dict[str, Any]:
        """
        Get structured JSON output using Gemini's JSON mode

        Args:
            messages: Conversation messages
            response_schema: JSON schema for response
            temperature: Sampling temperature

        Returns:
            Parsed JSON matching schema
        """
        temp = temperature if temperature is not None else self.default_temperature

        # Convert messages
        gemini_messages = self._convert_messages_to_gemini(messages)

        # Create model with JSON mode
        generation_config = {
            "temperature": temp,
            "response_mime_type": "application/json",
            "response_schema": response_schema
        }

        model = GenerativeModel(
            model_name=self.model_name,
            generation_config=generation_config,
            safety_settings=self.safety_settings
        )

        try:
            # Generate JSON response
            response = await model.generate_content_async(gemini_messages)

            # Parse JSON
            return json.loads(response.text)

        except Exception as e:
            logger.error(f"Gemini structured output error: {e}")
            return {}

    def _convert_messages_to_gemini(self, messages: List[Message]) -> List[Dict]:
        """
        Convert our Message format to Gemini format

        Gemini format:
        - System message: Separate parameter
        - User/Assistant: List of {"role": "user/model", "parts": ["text"]}
        """
        gemini_messages = []

        for msg in messages:
            # Skip system messages here (handled separately)
            if msg.role == "system":
                continue

            role = "model" if msg.role == "assistant" else "user"
            gemini_messages.append({
                "role": role,
                "parts": [msg.content]
            })

        return gemini_messages

    def _convert_functions_to_tools(self, functions: List[Dict[str, Any]]) -> List[Dict]:
        """
        Convert function definitions to Gemini tools format

        Our format (OpenAI-style):
        {
            "name": "function_name",
            "description": "...",
            "parameters": {...}
        }

        Gemini format:
        tools = [FunctionDeclaration(...)]
        """
        from google.generativeai.types import FunctionDeclaration, Tool

        declarations = []
        for func in functions:
            declarations.append(
                FunctionDeclaration(
                    name=func["name"],
                    description=func.get("description", ""),
                    parameters=func.get("parameters", {})
                )
            )

        return [Tool(function_declarations=declarations)]

    def _parse_gemini_response(self, response) -> LLMResponse:
        """
        Parse Gemini response into our LLMResponse format

        Handles:
        - Text responses
        - Function calls
        - Finish reasons
        """
        function_calls = []
        content = ""
        finish_reason = None

        # Check for function calls
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]

            # Get finish reason
            if hasattr(candidate, 'finish_reason'):
                finish_reason = str(candidate.finish_reason)

            # Check for function calls in parts
            if hasattr(candidate.content, 'parts'):
                for part in candidate.content.parts:
                    # Text content
                    if hasattr(part, 'text') and part.text:
                        content += part.text

                    # Function call
                    if hasattr(part, 'function_call') and part.function_call:
                        fc = part.function_call
                        function_calls.append(
                            FunctionCall(
                                name=fc.name,
                                arguments=dict(fc.args) if fc.args else {}
                            )
                        )

        # Fallback to simple text if no parts
        if not content and not function_calls:
            content = response.text if hasattr(response, 'text') else ""

        return LLMResponse(
            content=content,
            function_calls=function_calls,
            finish_reason=finish_reason
        )

    def get_provider_name(self) -> str:
        return f"Gemini ({self.model_name})"
