"""OpenAI LLM provider implementation."""
from typing import AsyncIterator, Optional

from app.core.logging import get_logger
from .provider import LLMProvider, LLMMessage, LLMResponse

logger = get_logger(__name__)


class OpenAIProvider(LLMProvider):
    """LLM provider using OpenAI API."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
    ):
        self.api_key = api_key
        self.model = model
        self._client: Optional["openai.AsyncOpenAI"] = None
    
    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    def _get_client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            try:
                import openai
                self._client = openai.AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                raise RuntimeError(
                    "openai package is required. Install with: pip install openai"
                )
        return self._client
    
    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Generate a response using OpenAI API."""
        client = self._get_client()
        
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            choice = response.choices[0]
            
            usage = None
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
            
            return LLMResponse(
                content=choice.message.content or "",
                model=response.model,
                usage=usage,
                finish_reason=choice.finish_reason,
            )
            
        except Exception as e:
            logger.error("openai_generation_failed", error=str(e))
            raise
    
    async def generate_stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        """Generate a streaming response using OpenAI API."""
        client = self._get_client()
        
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        try:
            stream = await client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error("openai_stream_failed", error=str(e))
            raise
