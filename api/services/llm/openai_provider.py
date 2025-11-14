"""
OpenAI provider implementation.

Uses the official OpenAI Python SDK for ChatGPT queries.
"""

import logging
from typing import Dict, Any
from openai import OpenAI, APIError, AuthenticationError, RateLimitError, APITimeoutError
from .base_provider import BaseLLMProvider
from .exceptions import (
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMInvalidResponseError,
    LLMTimeoutError,
    LLMNetworkError,
)

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI ChatGPT provider implementation using the official SDK.
    """
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        self.model = kwargs.get('model', 'gpt-4-turbo-preview')
        self.max_tokens = kwargs.get('max_tokens', 500)
        self.temperature = kwargs.get('temperature', 0.7)
        self.timeout = kwargs.get('timeout', 30.0)
        
        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=self.api_key,
            timeout=self.timeout,
        )
    
    @property
    def provider_name(self) -> str:
        return 'openai'
    
    def query(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Query OpenAI ChatGPT with the given prompt.
        
        Args:
            prompt: The prompt text
            **kwargs: Optional overrides for model, max_tokens, temperature
            
        Returns:
            Dict with 'content' and 'metadata' keys
        """
        model = kwargs.get('model', self.model)
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        temperature = kwargs.get('temperature', self.temperature)
        
        logger.debug(f"Querying OpenAI with model={model}, max_tokens={max_tokens}")
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are a helpful assistant that provides accurate, concise information about products.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.9,
            )
            
        except AuthenticationError as e:
            raise LLMAuthenticationError(
                f"OpenAI authentication failed. Check your API key."
            ) from e
        except RateLimitError as e:
            raise LLMRateLimitError(
                f"OpenAI rate limit exceeded. Please try again later."
            ) from e
        except APITimeoutError as e:
            raise LLMTimeoutError(
                f"OpenAI request timed out after {self.timeout}s"
            ) from e
        except APIError as e:
            if e.status_code and e.status_code >= 500:
                raise LLMNetworkError(f"OpenAI server error: {e.status_code}") from e
            raise LLMInvalidResponseError(f"OpenAI API error: {str(e)}") from e
        except Exception as e:
            raise LLMInvalidResponseError(f"Failed to query OpenAI: {str(e)}") from e
        
        # Parse response
        try:
            content = response.choices[0].message.content
            usage = response.usage
            
            total_tokens = usage.total_tokens
            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens
            
            # TODO: Update this for GPT 5/5.1 pricing
            # Estimate cost based on model
            # GPT-4 Turbo pricing: $0.01 input / $0.03 output per 1K tokens
            # GPT-3.5 Turbo pricing: $0.0005 input / $0.0015 output per 1K tokens
            if 'gpt-4' in model.lower():
                input_cost = (prompt_tokens / 1000) * 0.01
                output_cost = (completion_tokens / 1000) * 0.03
            else:  # GPT-3.5 or other
                input_cost = (prompt_tokens / 1000) * 0.0005
                output_cost = (completion_tokens / 1000) * 0.0015
            
            total_cost = input_cost + output_cost
            
            metadata = {
                'model': response.model,
                'tokens_used': total_tokens,
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'cost_estimate': total_cost,
                'finish_reason': response.choices[0].finish_reason,
                'provider_specific': {
                    'system_fingerprint': response.system_fingerprint,
                }
            }
            
            logger.info(
                f"OpenAI query successful: {total_tokens} tokens, "
                f"${total_cost:.4f} estimated cost"
            )
            
            return {
                'content': content,
                'metadata': metadata
            }
            
        except (AttributeError, IndexError) as e:
            raise LLMInvalidResponseError(
                f"Invalid response format from OpenAI: {str(e)}"
            ) from e
    
    def validate_credentials(self) -> bool:
        """
        Validate OpenAI API credentials by making a minimal test query.
        
        Returns:
            True if credentials are valid
        """
        try:
            # Make a minimal query to test authentication
            result = self.query(
                "Test query. Respond with 'OK'.",
                max_tokens=10
            )
            return 'content' in result and len(result['content']) > 0
        except LLMAuthenticationError:
            return False
        except Exception as e:
            logger.warning(f"Credential validation failed: {str(e)}")
            return False
    
    def estimate_cost(self, tokens_used: int, is_input: bool = False) -> float:
        """
        Estimate cost for OpenAI queries.
        
        Args:
            tokens_used: Number of tokens
            is_input: True for input tokens, False for output tokens
            
        Returns:
            Estimated cost in USD
        """
        if 'gpt-4' in self.model.lower():
            if is_input:
                return (tokens_used / 1000) * 0.01
            else:
                return (tokens_used / 1000) * 0.03
        else:  # GPT-3.5 or other
            if is_input:
                return (tokens_used / 1000) * 0.0005
            else:
                return (tokens_used / 1000) * 0.0015



