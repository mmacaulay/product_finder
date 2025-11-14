"""
Custom exceptions for LLM provider operations.
"""


class LLMProviderError(Exception):
    """Base exception for all LLM provider errors"""
    pass


class LLMAuthenticationError(LLMProviderError):
    """Raised when API authentication fails"""
    pass


class LLMRateLimitError(LLMProviderError):
    """Raised when API rate limits are exceeded"""
    pass


class LLMInvalidResponseError(LLMProviderError):
    """Raised when the LLM returns an invalid or unexpected response"""
    pass


class LLMTimeoutError(LLMProviderError):
    """Raised when the LLM request times out"""
    pass


class LLMNetworkError(LLMProviderError):
    """Raised when there's a network connectivity issue"""
    pass



