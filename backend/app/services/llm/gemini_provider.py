"""
Google Gemini Provider (Modern SDK)

Uses the google-genai SDK (2024+) with improved API

Recommended provider for Chitta:
- Free during preview period
- Native video analysis (crucial for video screening)
- 2M token context window (Gemini 2.0)
- Excellent Hebrew support
- Function calling support
- JSON mode for structured output
"""

import logging
from typing import List, Dict, Any, Optional
import json

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("google-genai not installed. Install with: pip install google-genai")

from .base import BaseLLMProvider, Message, LLMResponse, FunctionCall

logger = logging.getLogger(__name__)


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM Provider using modern SDK"""

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

        # Create Gemini client (modern SDK)
        self.client = genai.Client(api_key=api_key)
        self.model_name = model
        self.default_temperature = default_temperature

        # Safety settings - minimal blocking for clinical conversations
        self.safety_settings = [
            types.SafetySetting(
                category="HARM_CATEGORY_HATE_SPEECH",
                threshold="BLOCK_NONE"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT",
                threshold="BLOCK_NONE"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_HARASSMENT",
                threshold="BLOCK_NONE"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                threshold="BLOCK_NONE"
            ),
        ]

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
        contents = self._convert_messages_to_contents(messages)

        # Prepare tools if functions provided
        tools = None
        if functions:
            tools = self._convert_functions_to_tools(functions)

        # Create configuration
        config = types.GenerateContentConfig(
            temperature=temp,
            max_output_tokens=max_tokens,
            safety_settings=self.safety_settings,
            tools=tools
        )

        try:
            # Generate response using async client
            # Using direct .aio access without context manager
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config
            )

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
        contents = self._convert_messages_to_contents(messages)

        # Create config with JSON mode
        config = types.GenerateContentConfig(
            temperature=temp,
            response_mime_type="application/json",
            response_schema=response_schema,
            safety_settings=self.safety_settings
        )

        try:
            # Generate JSON response
            async with self.client.aio as aclient:
                response = await aclient.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=config
                )

            # Parse JSON from text
            return json.loads(response.text)

        except Exception as e:
            logger.error(f"Gemini structured output error: {e}")
            return {}

    def _convert_messages_to_contents(self, messages: List[Message]) -> List[types.Content]:
        """
        Convert our Message format to Gemini Content format

        Gemini format:
        - System message: Included as first user message with system prompt prefix
        - User/Assistant: Content with role and parts
        """
        contents = []
        system_prompt = None

        for msg in messages:
            if msg.role == "system":
                # Save system prompt to prepend to first user message
                system_prompt = msg.content
                continue

            # Map our roles to Gemini roles
            role = "model" if msg.role == "assistant" else "user"

            # If this is the first user message and we have a system prompt, prepend it
            content_text = msg.content
            if role == "user" and system_prompt and not contents:
                content_text = f"{system_prompt}\n\n{msg.content}"
                system_prompt = None  # Only use once

            # Create Content with Parts
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part(text=content_text)]
                )
            )

        return contents

    def _convert_functions_to_tools(self, functions: List[Dict[str, Any]]) -> List[types.Tool]:
        """
        Convert function definitions to Gemini Tool format

        Our format (OpenAI-style):
        {
            "name": "function_name",
            "description": "...",
            "parameters": {...}
        }

        Gemini format: Tool with FunctionDeclaration
        """
        declarations = []

        for func in functions:
            # Create FunctionDeclaration
            declaration = types.FunctionDeclaration(
                name=func["name"],
                description=func.get("description", ""),
                parameters=func.get("parameters", {})
            )
            declarations.append(declaration)

        # Return list with single Tool containing all declarations
        return [types.Tool(function_declarations=declarations)]

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

        # Check for candidates
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]

            # Get finish reason
            if hasattr(candidate, 'finish_reason'):
                finish_reason = str(candidate.finish_reason)

            # Check for content parts
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
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
                                arguments=dict(fc.args) if hasattr(fc, 'args') else {}
                            )
                        )

        # Fallback to simple text if available
        if not content and not function_calls:
            if hasattr(response, 'text'):
                content = response.text

        return LLMResponse(
            content=content,
            function_calls=function_calls,
            finish_reason=finish_reason
        )

    def get_provider_name(self) -> str:
        return f"Gemini ({self.model_name})"
