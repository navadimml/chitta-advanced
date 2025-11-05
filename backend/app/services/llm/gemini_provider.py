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

            # Check if response has valid content
            if not hasattr(response, 'text') or not response.text:
                # Check if response has candidates with content
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            # Try to extract text from parts
                            text_parts = [part.text for part in candidate.content.parts if hasattr(part, 'text') and part.text]
                            if text_parts:
                                response_text = ''.join(text_parts)
                            else:
                                logger.warning("No text found in response parts for structured output")
                                return {}
                        else:
                            logger.warning("candidate.content.parts is None or empty for structured output")
                            return {}
                    else:
                        logger.warning("candidate.content is None or missing for structured output")
                        return {}
                else:
                    logger.warning("No candidates in response for structured output")
                    return {}
            else:
                response_text = response.text

            # Parse JSON from text
            if not response_text or not response_text.strip():
                logger.warning("Empty response text for structured output")
                return {}

            return json.loads(response_text)

        except json.JSONDecodeError as e:
            logger.error(f"Gemini structured output JSON decode error: {e}")
            logger.error(f"Response text was: {response_text if 'response_text' in locals() else 'N/A'}")
            return {}
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

        Gemini format: Tool with FunctionDeclaration (as per official docs)
        Note: We can pass plain dicts directly to types.Tool() - the SDK handles conversion
        """
        # Per official Gemini documentation, we can pass dicts directly to types.Tool
        # The SDK will internally convert them to FunctionDeclaration objects
        return [types.Tool(function_declarations=functions)]

    def _parse_gemini_response(self, response) -> LLMResponse:
        """
        Parse Gemini response into our LLMResponse format

        Handles:
        - Text responses
        - Function calls
        - Finish reasons
        - Empty responses (safety filters, etc.)

        Note: Unlike the official documentation examples which directly access
        response.candidates[0].content.parts[0], we safely check for None/empty
        at each level to prevent errors when Gemini returns filtered/empty responses.
        """
        function_calls = []
        content = ""
        finish_reason = None

        try:
            # Debug: log response structure
            logger.debug(f"Response type: {type(response)}")
            logger.debug(f"Response attributes: {dir(response)}")

            # Check for candidates
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                logger.debug(f"Candidate: {candidate}")

                # Get finish reason
                if hasattr(candidate, 'finish_reason'):
                    finish_reason = str(candidate.finish_reason)

                # Check for content parts
                if hasattr(candidate, 'content') and candidate.content:
                    logger.debug(f"Content: {candidate.content}")

                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
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
                    else:
                        logger.warning("candidate.content.parts is None or empty")
                        # Response was received but has no content (possibly filtered by safety settings)
                        # This is a valid state - set finish_reason if not already set
                        if not finish_reason:
                            finish_reason = "empty_content"
                else:
                    logger.warning("candidate.content is None or missing")
                    # Response was received but has no content (possibly filtered by safety settings)
                    # This is a valid state - set finish_reason if not already set
                    if not finish_reason:
                        finish_reason = "empty_content"

            # Fallback to simple text if available (only if we have no candidates)
            if not content and not function_calls:
                if hasattr(response, 'text') and response.text:
                    content = response.text
                    logger.debug("Used response.text fallback")
                elif not hasattr(response, 'candidates') or not response.candidates:
                    logger.warning("No content found in response")
                    # Only use str(response) if we have no candidates at all
                    # This indicates an unexpected response structure
                    content = str(response) if response else "No response"
                    finish_reason = "unexpected_response"

        except Exception as e:
            logger.error(f"Error parsing Gemini response: {e}", exc_info=True)
            content = f"Error parsing response: {str(e)}"

        # CRITICAL FIX: Ensure content is always a valid string, never None
        if content is None:
            content = ""
        
        # If we have function calls but no content, that's valid - set empty string
        if not content and function_calls:
            content = ""

        return LLMResponse(
            content=content,
            function_calls=function_calls,
            finish_reason=finish_reason or "unknown"
        )

    def get_provider_name(self) -> str:
        return f"Gemini ({self.model_name})"
