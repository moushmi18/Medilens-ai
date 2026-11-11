"""LLM provider module.

Provides a pluggable interface for LLM providers.
Currently supports OpenAI (when OPENAI_API_KEY is set).

When no provider is configured, returns a clear message stating
that the AI answer service is not configured.
"""
from .provider import LLMProvider, get_llm_provider
from .openai_provider import OpenAIProvider

__all__ = ["LLMProvider", "get_llm_provider", "OpenAIProvider"]
