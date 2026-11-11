"""LLM provider interface and factory."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator, Optional

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class LLMResponse:
    """Response from LLM provider."""
    content: str
    model: str
    usage: Optional[dict] = None
    finish_reason: Optional[str] = None


@dataclass
class LLMMessage:
    """Message for LLM conversation."""
    role: str  # "system", "user", "assistant"
    content: str


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if provider is properly configured."""
        pass
    
    @abstractmethod
    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Generate a response from the LLM.
        
        Args:
            messages: Conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            LLMResponse with generated content
        """
        pass
    
    @abstractmethod
    async def generate_stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        """Generate a streaming response from the LLM.
        
        Args:
            messages: Conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            
        Yields:
            Chunks of generated text
        """
        pass


class UnconfiguredProvider(LLMProvider):
    """Provider returned when no LLM is configured.
    
    Does NOT fake answers - returns a clear message that the service
    is not configured.
    """
    
    NOT_CONFIGURED_MESSAGE = (
        "The AI answer service is not currently configured. "
        "Please contact the administrator to set up the OpenAI API key."
    )
    
    @property
    def is_configured(self) -> bool:
        return False
    
    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        return LLMResponse(
            content=self.NOT_CONFIGURED_MESSAGE,
            model="unconfigured",
            finish_reason="error",
        )
    
    async def generate_stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        yield self.NOT_CONFIGURED_MESSAGE


_provider_instance: Optional[LLMProvider] = None


def get_llm_provider() -> LLMProvider:
    """Get the configured LLM provider.
    
    Returns OpenAI provider if OPENAI_API_KEY is set,
    otherwise returns UnconfiguredProvider.
    """
    global _provider_instance
    
    if _provider_instance is not None:
        return _provider_instance
    
    settings = get_settings()
    
    if settings.openai_api_key:
        from .openai_provider import OpenAIProvider
        _provider_instance = OpenAIProvider(settings.openai_api_key)
        logger.info("llm_provider_initialized", provider="openai")
    else:
        _provider_instance = UnconfiguredProvider()
        logger.warning("llm_provider_not_configured")
    
    return _provider_instance


def reset_provider() -> None:
    """Reset provider instance (for testing)."""
    global _provider_instance
    _provider_instance = None
