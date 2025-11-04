"""
Base LLM Provider Interface

Abstract base class for all LLM providers (Gemini, Claude, OpenAI, Simulated)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class Message(BaseModel):
    """Chat message"""
    role: str = Field(..., description="Role: 'system', 'user', or 'assistant'")
    content: str = Field(..., description="Message content")


class FunctionCall(BaseModel):
    """Function call from LLM"""
    name: str = Field(..., description="Function name")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Function arguments")


class LLMResponse(BaseModel):
    """LLM response with optional function calls"""
    content: str = Field(default="", description="Text response from LLM")
    function_calls: List[FunctionCall] = Field(
        default_factory=list,
        description="List of function calls made by LLM"
    )
    finish_reason: Optional[str] = Field(
        default=None,
        description="Reason for completion: 'stop', 'function_call', 'length', etc."
    )


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers

    All providers (Gemini, Claude, OpenAI, Simulated) implement this interface
    to ensure consistent behavior across different LLMs.
    """

    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        functions: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> LLMResponse:
        """
        Send chat completion request

        Args:
            messages: List of conversation messages
            functions: Optional list of function definitions for function calling
            temperature: Sampling temperature (0.0 - 1.0)
            max_tokens: Maximum tokens in response

        Returns:
            LLMResponse with content and optional function calls
        """
        pass

    @abstractmethod
    async def chat_with_structured_output(
        self,
        messages: List[Message],
        response_schema: Dict[str, Any],
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Get structured JSON output from LLM

        Args:
            messages: List of conversation messages
            response_schema: JSON schema for expected response structure
            temperature: Sampling temperature (0.0 - 1.0)

        Returns:
            Parsed JSON matching the schema
        """
        pass

    def supports_function_calling(self) -> bool:
        """Check if this provider supports function calling"""
        return True

    def supports_structured_output(self) -> bool:
        """Check if this provider supports structured JSON output"""
        return True

    def get_provider_name(self) -> str:
        """Get the name of this provider"""
        return self.__class__.__name__
