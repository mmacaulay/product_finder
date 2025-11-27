"""
LLM service layer for product information queries.

This module provides a common interface for querying different LLM providers
(OpenAI, Perplexity, etc.) with caching support.
"""

from .llm_service import LLMService
from .base_provider import BaseLLMProvider
from .exceptions import (
    LLMProviderError,
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMInvalidResponseError,
)

__all__ = [
    "LLMService",
    "BaseLLMProvider",
    "LLMProviderError",
    "LLMAuthenticationError",
    "LLMRateLimitError",
    "LLMInvalidResponseError",
]
