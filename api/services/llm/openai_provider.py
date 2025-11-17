"""
OpenAI provider implementation.

Uses the official OpenAI Python SDK for ChatGPT queries.
"""

import logging
from typing import Dict, Any, Optional
from openai import OpenAI, APIError, AuthenticationError, RateLimitError, APITimeoutError
from .base_provider import BaseLLMProvider
from .pricing import OpenAIPricing
from .json_parser import parse_llm_json, JSONParseError
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
        self.model = kwargs.get('model', 'gpt-5-nano')
        self.max_tokens = kwargs.get('max_tokens', 400)
        self.temperature = kwargs.get('temperature', 0.5)
        self.timeout = kwargs.get('timeout', 30.0)
        self.enable_json_mode = kwargs.get('enable_json_mode', True)
        
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
            **kwargs: Optional overrides for model, max_tokens, temperature, parse_json
            
        Returns:
            Dict with 'content' (parsed JSON dict if parse_json=True, else string) and 'metadata' keys
        """
        model = kwargs.get('model', self.model)
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        temperature = kwargs.get('temperature', self.temperature)
        parse_json = kwargs.get('parse_json', True)  # Default to parsing JSON
        enable_json_mode = kwargs.get('enable_json_mode', self.enable_json_mode)
        
        logger.debug(f"Querying OpenAI with model={model}, max_tokens={max_tokens}, json_mode={enable_json_mode}")
        
        # Build request parameters
        request_params = {
            'model': model,
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are a JSON API that provides accurate, structured information about products. Always respond with valid JSON only.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'max_tokens': max_tokens,
            'temperature': temperature,
            'top_p': 0.9,
        }
        
        # Enable JSON mode if requested and supported
        if enable_json_mode and parse_json:
            request_params['response_format'] = {'type': 'json_object'}
        
        try:
            response = self.client.chat.completions.create(**request_params)
            
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
            raw_content = response.choices[0].message.content
            usage = response.usage
            
            total_tokens = usage.total_tokens
            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens
            
            # Calculate cost using centralized pricing configuration
            try:
                pricing = OpenAIPricing.get_pricing(model)
                total_cost = pricing.calculate_cost(prompt_tokens, completion_tokens)
            except Exception as e:
                logger.warning(f"Error calculating cost for model '{model}': {e}")
                # Fallback calculation using GPT-3.5 rates
                total_cost = (prompt_tokens / 1_000_000) * 0.50 + \
                           (completion_tokens / 1_000_000) * 1.50
            
            # Parse JSON if requested
            content = raw_content
            parse_success = True
            parse_strategy = None
            if parse_json:
                try:
                    content, parse_strategy = parse_llm_json(raw_content, strict=enable_json_mode)
                    logger.debug(f"Successfully parsed JSON response using strategy: {parse_strategy}")
                except JSONParseError as e:
                    logger.warning(f"Failed to parse JSON from OpenAI response: {e}")
                    parse_success = False
                    # If parsing fails, raise error to trigger retry logic
                    raise LLMInvalidResponseError(f"Failed to parse JSON response: {e}") from e
            
            metadata = {
                'model': response.model,
                'tokens_used': total_tokens,
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'cost_estimate': total_cost,
                'finish_reason': response.choices[0].finish_reason,
                'json_mode_enabled': enable_json_mode and parse_json,
                'parse_success': parse_success,
                'parse_strategy': parse_strategy,
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
        try:
            pricing = OpenAIPricing.get_pricing(self.model)
            return pricing.estimate_cost(tokens_used, is_input)
        except Exception as e:
            logger.warning(f"Error estimating cost for model '{self.model}': {e}")
            # Fallback to base class generic estimate
            return super().estimate_cost(tokens_used, is_input)



