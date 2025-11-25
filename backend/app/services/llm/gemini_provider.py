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
        model: str = "gemini-2.5-flash",
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
        max_tokens: int = 1000,
        response_format: Optional[str] = None  # Support "json" for JSON mode
    ) -> LLMResponse:
        """
        Send chat completion with optional function calling

        Args:
            messages: Conversation messages
            functions: Function definitions for function calling
            temperature: Sampling temperature
            max_tokens: Maximum output tokens
            response_format: If "json", requests JSON-formatted output

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
        config_params = {
            "temperature": temp,
            "max_output_tokens": max_tokens,
            "tools": tools
        }

        # CRITICAL: Do NOT include safety_settings when using function calling!
        # Safety settings can interfere with function calling behavior
        if not tools:
            config_params["safety_settings"] = self.safety_settings

        # CRITICAL FIX: Explicitly disable automatic function calling (AFC)
        # The SDK enables AFC by default (as of 2024), but we need manual function calling
        # so we can process and save the function call results ourselves
        #
        # IMPORTANT: AFC must ALWAYS be disabled, even when no tools are provided!
        # Otherwise Phase 2 (response without functions) gets very short responses (10 chars)
        #
        # TWO SEPARATE CONFIGURATIONS ARE NEEDED:
        # 1. automatic_function_calling.disable = True  → Prevents SDK from auto-executing functions
        # 2. tool_config.function_calling_config.mode = ANY → Forces model to call functions (only when tools provided)

        # ALWAYS disable AFC to prevent short responses in Phase 2
        # CRITICAL: Must set maximum_remote_calls=0 to fully disable AFC!
        # Setting only disable=True isn't enough - the default maximum_remote_calls=10 re-enables it!
        config_params["automatic_function_calling"] = types.AutomaticFunctionCallingConfig(
            disable=True,
            maximum_remote_calls=0  # CRITICAL: Must be 0 to fully disable AFC
        )

        # Only configure function calling behavior if tools are provided
        if tools:
            # Force function calling mode (model-level behavior)
            config_params["tool_config"] = types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(
                    mode=types.FunctionCallingConfigMode.ANY  # Model MUST call a function
                )
            )

        # Add JSON mode if requested
        if response_format == "json":
            config_params["response_mime_type"] = "application/json"

        config = types.GenerateContentConfig(**config_params)

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
        # CRITICAL: Must disable AFC to prevent schema validation errors!
        # AFC (Automatic Function Calling) interferes with structured output schema validation
        config = types.GenerateContentConfig(
            temperature=temp,
            max_output_tokens=8000,  # Increased from default to prevent MAX_TOKENS truncation
            response_mime_type="application/json",
            response_schema=response_schema,
            safety_settings=self.safety_settings,
            # CRITICAL: Disable AFC for structured output to prevent schema validation errors
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True,
                maximum_remote_calls=0  # Must be 0 to fully disable AFC
            )
        )

        try:
            # Generate JSON response using async client
            # Direct .aio access without context manager (same pattern as chat())
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config
            )

            # Check if response has text content
            if not response.text:
                # Gemini returned empty/None response - diagnose why
                finish_reason = None
                safety_info = ""

                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]

                    if hasattr(candidate, 'finish_reason'):
                        finish_reason = str(candidate.finish_reason)

                    if hasattr(candidate, 'safety_ratings') and candidate.safety_ratings:
                        safety_info = f"\nSafety ratings: {candidate.safety_ratings}"

                error_msg = (
                    f"Gemini returned empty response for structured output. "
                    f"Finish reason: {finish_reason}.{safety_info}\n"
                    f"This usually indicates content was blocked by safety filters, "
                    f"token limit was hit, or an API error occurred."
                )
                logger.error(f"❌ {error_msg}")
                raise ValueError(error_msg)

            # Parse JSON from text
            return json.loads(response.text)

        except json.JSONDecodeError as e:
            logger.error(f"Gemini returned invalid JSON: {e}")
            logger.error(f"Response text: {response.text[:500] if response.text else 'None'}")
            raise ValueError(f"Gemini returned invalid JSON: {str(e)}")
        except Exception as e:
            logger.error(f"Gemini structured output error: {e}")
            raise  # Re-raise instead of returning empty dict!

    def _convert_messages_to_contents(self, messages: List[Message]) -> List[types.Content]:
        """
        Convert our Message format to Gemini Content format

        Gemini format:
        - System message: Send as separate user message (DO NOT combine - breaks function calling!)
        - User/Assistant: Content with role and parts
        - Function responses: Special Part.from_function_response format
        """
        contents = []

        for msg in messages:
            if msg.role == "system":
                # CRITICAL FIX: Send system prompt as separate user message
                # Combining system+user into single message breaks function calling in some cases
                contents.append(
                    types.Content(
                        role="user",
                        parts=[types.Part(text=msg.content)]
                    )
                )
                continue

            # Handle assistant messages with function calls (per Gemini docs)
            # CRITICAL: Must add assistant's function calls to history before sending results
            if msg.role == "assistant" and msg.function_calls:
                # Convert our FunctionCall objects to Gemini Parts
                parts = []
                for fc in msg.function_calls:
                    parts.append(
                        types.Part(
                            function_call=types.FunctionCall(
                                name=fc.name,
                                args=fc.arguments
                            )
                        )
                    )

                contents.append(
                    types.Content(
                        role="model",  # Assistant role = model in Gemini
                        parts=parts
                    )
                )
                continue

            # Handle function responses (from function execution results)
            if msg.role == "function" and msg.function_response:
                # Gemini expects function responses as user role with function_response parts
                parts = []

                # Support both dict (old format) and list (new format for multiple calls)
                if isinstance(msg.function_response, dict):
                    # Old format: dict of {func_name: result}
                    for func_name, result in msg.function_response.items():
                        parts.append(
                            types.Part.from_function_response(
                                name=func_name,
                                response={"result": result}
                            )
                        )
                elif isinstance(msg.function_response, list):
                    # New format: list of {"name": func_name, "result": result}
                    # This preserves order and supports multiple calls to same function
                    for item in msg.function_response:
                        parts.append(
                            types.Part.from_function_response(
                                name=item["name"],
                                response={"result": item["result"]}
                            )
                        )

                contents.append(
                    types.Content(
                        role="user",  # Function responses are sent as user role in Gemini
                        parts=parts
                    )
                )
                continue

            # Map our roles to Gemini roles
            role = "model" if msg.role == "assistant" else "user"

            # Create Content with Parts
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part(text=msg.content)]
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

                # Check for safety ratings if blocked
                safety_info = ""
                if hasattr(candidate, 'safety_ratings') and candidate.safety_ratings:
                    safety_info = f" Safety ratings: {candidate.safety_ratings}"

                # Check for content parts
                if hasattr(candidate, 'content') and candidate.content:
                    logger.debug(f"Content: {candidate.content}")

                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        for part in candidate.content.parts:
                            # ⚠️ CRITICAL FIX: thought_signature is an ATTRIBUTE of the Part, not a separate part!
                            # The same Part can have BOTH part.text (user-facing) and part.thought (internal reasoning).
                            # We want the TEXT but not the thought.
                            # DO NOT skip the entire part - just extract the text and ignore the thought attribute!

                            # Text content (user-facing response)
                            if hasattr(part, 'text') and part.text:
                                content += part.text
                                # Log if this part also has thought_signature (for debugging)
                                if hasattr(part, 'thought'):
                                    logger.debug("🧠 Part has thought_signature (ignored, text extracted)")

                            # DON'T skip parts with thought! They might also have function_call!
                            # Just ignore the thought attribute itself

                            # Function call (can coexist with thought attribute!)
                            if hasattr(part, 'function_call') and part.function_call:
                                fc = part.function_call
                                function_calls.append(
                                    FunctionCall(
                                        name=fc.name,
                                        arguments=dict(fc.args) if hasattr(fc, 'args') else {}
                                    )
                                )
                    else:
                        logger.warning(
                            f"candidate.content.parts is None or empty. "
                            f"Finish reason: {finish_reason}.{safety_info}"
                        )
                else:
                    # Log detailed info when content is missing
                    logger.warning(
                        f"⚠️ candidate.content is None or missing! "
                        f"Finish reason: {finish_reason}.{safety_info} "
                        f"This usually indicates: "
                        f"SAFETY (blocked by filters), "
                        f"MAX_TOKENS (hit limit), "
                        f"RECITATION (copyright), or "
                        f"other API issues."
                    )

            # ⚠️ CRITICAL: Do NOT use response.text as fallback!
            # response.text concatenates ALL parts including thought_signature from Gemini 3 Pro,
            # which leaks internal reasoning (<thinking> tags) to users.
            # If there's no text content after parsing parts, it means Gemini returned
            # ONLY non-text parts (thought_signature, function_calls, etc.) with no actual text response.
            # In this case, returning empty string is correct behavior.
            if not content and not function_calls:
                logger.warning(
                    f"⚠️ Gemini response has no text content! "
                    f"Only non-text parts returned (thought_signature, etc.). "
                    f"This indicates the model didn't generate a user-facing response."
                )

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
