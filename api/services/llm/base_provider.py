"""
Abstract base class for LLM providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""

    def __init__(self, api_key: str, **kwargs):
        """
        Initialize the provider.

        Args:
            api_key: API key for authentication
            **kwargs: Provider-specific configuration options
        """
        self.api_key = api_key
        self.config = kwargs
        self._validate_config()

    def _validate_config(self):
        """Validate provider configuration. Override in subclasses if needed."""
        if not self.api_key:
            raise ValueError(f"{self.provider_name} API key is required")

    @abstractmethod
    def query(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Send a query to the LLM provider.

        Args:
            prompt: The prompt text to send
            **kwargs: Provider-specific parameters

        Returns:
            Dictionary with the following structure:
            {
                'content': str,  # The LLM response text
                'metadata': {
                    'model': str,
                    'tokens_used': int,
                    'cost_estimate': float,
                    'finish_reason': str,
                    'provider_specific': dict  # Any additional provider data
                }
            }

        Raises:
            LLMProviderError: If the query fails
            LLMAuthenticationError: If authentication fails
            LLMRateLimitError: If rate limits are exceeded
            LLMInvalidResponseError: If response format is invalid
        """
        pass

    @abstractmethod
    def validate_credentials(self) -> bool:
        """
        Verify that API credentials are valid.

        Returns:
            True if credentials are valid, False otherwise
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider identifier (e.g., 'openai', 'perplexity')"""
        pass

    def estimate_cost(self, tokens_used: int, is_input: bool = False) -> float:
        """
        Estimate the cost of a query based on token usage.
        Override in subclasses with actual pricing.

        Args:
            tokens_used: Number of tokens
            is_input: True for input tokens, False for output tokens

        Returns:
            Estimated cost in USD
        """
        # Default rough estimate: $0.00002 per token
        return tokens_used * 0.00002

    def __str__(self):
        return f"{self.provider_name} Provider"

    def __repr__(self):
        return f"<{self.__class__.__name__}(provider='{self.provider_name}')>"
