"""
Perplexity AI provider implementation.

Perplexity provides LLM queries with real-time web search capabilities,
making it ideal for queries that require current information like reviews,
news, and pricing.
"""

import httpx
import logging
from typing import Dict, Any, Optional
from .base_provider import BaseLLMProvider
from .exceptions import (
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMInvalidResponseError,
    LLMTimeoutError,
    LLMNetworkError,
)

logger = logging.getLogger(__name__)


class PerplexityProvider(BaseLLMProvider):
    """
    Perplexity AI provider implementation.
    
    Perplexity uses an OpenAI-compatible API format.
    """
    
    BASE_URL = "https://api.perplexity.ai/chat/completions"
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        self.model = kwargs.get('model', 'llama-3.1-sonar-large-128k-online')
        self.max_tokens = kwargs.get('max_tokens', 500)
        self.temperature = kwargs.get('temperature', 0.7)
        self.timeout = kwargs.get('timeout', 30.0)
    
    @property
    def provider_name(self) -> str:
        return 'perplexity'
    
    def query(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Query Perplexity AI with the given prompt.
        
        Args:
            prompt: The prompt text
            **kwargs: Optional overrides for model, max_tokens, temperature
            
        Returns:
            Dict with 'content' and 'metadata' keys
        """
        model = kwargs.get('model', self.model)
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        temperature = kwargs.get('temperature', self.temperature)
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
        
        payload = {
            'model': model,
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are a helpful assistant that provides accurate, concise information about products based on web search results.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'max_tokens': max_tokens,
            'temperature': temperature,
            'top_p': 0.9,
            'return_citations': True,
            'search_recency_filter': 'month',  # Focus on recent information
            'stream': False,
        }
        
        logger.debug(f"Querying Perplexity with model={model}, max_tokens={max_tokens}")
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    self.BASE_URL,
                    headers=headers,
                    json=payload
                )
                
                # Handle different HTTP status codes
                if response.status_code == 401:
                    raise LLMAuthenticationError(
                        f"Perplexity authentication failed. Check your API key."
                    )
                elif response.status_code == 429:
                    raise LLMRateLimitError(
                        f"Perplexity rate limit exceeded. Please try again later."
                    )
                elif response.status_code >= 500:
                    raise LLMNetworkError(
                        f"Perplexity server error: {response.status_code}"
                    )
                elif response.status_code != 200:
                    raise LLMInvalidResponseError(
                        f"Unexpected status code {response.status_code}: {response.text}"
                    )
                
                data = response.json()
                
        except httpx.TimeoutException as e:
            raise LLMTimeoutError(f"Perplexity request timed out after {self.timeout}s") from e
        except httpx.NetworkError as e:
            raise LLMNetworkError(f"Network error connecting to Perplexity: {str(e)}") from e
        except Exception as e:
            if isinstance(e, (LLMAuthenticationError, LLMRateLimitError, 
                            LLMInvalidResponseError, LLMTimeoutError, LLMNetworkError)):
                raise
            raise LLMInvalidResponseError(f"Failed to query Perplexity: {str(e)}") from e
        
        # Parse response
        try:
            content = data['choices'][0]['message']['content']
            usage = data.get('usage', {})
            citations = data.get('citations', [])
            
            total_tokens = usage.get('total_tokens', 0)
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)
            
            # Estimate cost (Perplexity pricing as of 2024)
            # Approximate: $0.001 per 1K input tokens, $0.003 per 1K output tokens
            input_cost = (prompt_tokens / 1000) * 0.001
            output_cost = (completion_tokens / 1000) * 0.003
            total_cost = input_cost + output_cost
            
            metadata = {
                'model': model,
                'tokens_used': total_tokens,
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'cost_estimate': total_cost,
                'finish_reason': data['choices'][0].get('finish_reason', 'unknown'),
                'citations': citations,
                'provider_specific': {
                    'citations_count': len(citations),
                    'has_web_search': True,
                }
            }
            
            logger.info(
                f"Perplexity query successful: {total_tokens} tokens, "
                f"${total_cost:.4f} estimated cost, {len(citations)} citations"
            )
            
            return {
                'content': content,
                'metadata': metadata
            }
            
        except (KeyError, IndexError) as e:
            raise LLMInvalidResponseError(
                f"Invalid response format from Perplexity: {str(e)}"
            ) from e
    
    def validate_credentials(self) -> bool:
        """
        Validate Perplexity API credentials by making a minimal test query.
        
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
        Estimate cost for Perplexity queries.
        
        Args:
            tokens_used: Number of tokens
            is_input: True for input tokens, False for output tokens
            
        Returns:
            Estimated cost in USD
        """
        if is_input:
            # $0.001 per 1K input tokens
            return (tokens_used / 1000) * 0.001
        else:
            # $0.003 per 1K output tokens
            return (tokens_used / 1000) * 0.003



