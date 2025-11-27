"""
Perplexity AI provider implementation.

Perplexity provides LLM queries with real-time web search capabilities,
making it ideal for queries that require current information like reviews,
news, and pricing.
"""

import httpx
import logging
from typing import Dict, Any
from .base_provider import BaseLLMProvider
from .pricing import PerplexityPricing
from .json_parser import parse_llm_json, JSONParseError
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
        self.model = kwargs.get("model", "sonar")
        self.max_tokens = kwargs.get("max_tokens", 400)
        self.temperature = kwargs.get("temperature", 0.5)
        self.timeout = kwargs.get("timeout", 30.0)
        self.enable_json_mode = kwargs.get(
            "enable_json_mode", False
        )  # Perplexity may not support JSON mode

    @property
    def provider_name(self) -> str:
        return "perplexity"

    def query(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Query Perplexity AI with the given prompt.

        Args:
            prompt: The prompt text
            **kwargs: Optional overrides for model, max_tokens, temperature, parse_json

        Returns:
            Dict with 'content' (parsed JSON dict if parse_json=True, else string) and 'metadata' keys
        """
        model = kwargs.get("model", self.model)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        temperature = kwargs.get("temperature", self.temperature)
        parse_json = kwargs.get("parse_json", True)  # Default to parsing JSON
        enable_json_mode = kwargs.get("enable_json_mode", self.enable_json_mode)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a JSON API that provides accurate, structured information about products based on web search results. Always respond with valid JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 0.9,
            "return_citations": True,
            "search_recency_filter": "month",  # Focus on recent information
            "stream": False,
        }

        # Try to enable JSON mode if supported and requested
        if enable_json_mode and parse_json:
            payload["response_format"] = {"type": "json_object"}

        logger.debug(
            f"Querying Perplexity with model={model}, max_tokens={max_tokens}, json_mode={enable_json_mode}"
        )

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(self.BASE_URL, headers=headers, json=payload)

                # Handle different HTTP status codes
                if response.status_code == 401:
                    raise LLMAuthenticationError(
                        "Perplexity authentication failed. Check your API key."
                    )
                elif response.status_code == 429:
                    raise LLMRateLimitError(
                        "Perplexity rate limit exceeded. Please try again later."
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
            raise LLMTimeoutError(
                f"Perplexity request timed out after {self.timeout}s"
            ) from e
        except httpx.NetworkError as e:
            raise LLMNetworkError(
                f"Network error connecting to Perplexity: {str(e)}"
            ) from e
        except Exception as e:
            if isinstance(
                e,
                (
                    LLMAuthenticationError,
                    LLMRateLimitError,
                    LLMInvalidResponseError,
                    LLMTimeoutError,
                    LLMNetworkError,
                ),
            ):
                raise
            raise LLMInvalidResponseError(
                f"Failed to query Perplexity: {str(e)}"
            ) from e

        # Parse response
        try:
            raw_content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            citations = data.get("citations", [])

            total_tokens = usage.get("total_tokens", 0)
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)

            # Calculate cost using centralized pricing configuration
            try:
                pricing = PerplexityPricing.get_pricing(model)
                total_cost = pricing.calculate_cost(prompt_tokens, completion_tokens)
            except Exception as e:
                logger.warning(f"Error calculating cost for model '{model}': {e}")
                # Fallback calculation using small model rates
                total_cost = (prompt_tokens / 1_000_000) * 0.20 + (
                    completion_tokens / 1_000_000
                ) * 0.20

            # Parse JSON if requested
            content = raw_content
            parse_success = True
            parse_strategy = None
            if parse_json:
                try:
                    content, parse_strategy = parse_llm_json(
                        raw_content, strict=enable_json_mode
                    )
                    logger.debug(
                        f"Successfully parsed JSON response using strategy: {parse_strategy}"
                    )
                except JSONParseError as e:
                    logger.warning(
                        f"Failed to parse JSON from Perplexity response: {e}"
                    )
                    parse_success = False
                    # If parsing fails, raise error to trigger retry logic
                    raise LLMInvalidResponseError(
                        f"Failed to parse JSON response: {e}"
                    ) from e

            metadata = {
                "model": model,
                "tokens_used": total_tokens,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "cost_estimate": total_cost,
                "finish_reason": data["choices"][0].get("finish_reason", "unknown"),
                "citations": citations,
                "json_mode_enabled": enable_json_mode and parse_json,
                "parse_success": parse_success,
                "parse_strategy": parse_strategy,
                "provider_specific": {
                    "citations_count": len(citations),
                    "has_web_search": True,
                },
            }

            logger.info(
                f"Perplexity query successful: {total_tokens} tokens, "
                f"${total_cost:.4f} estimated cost, {len(citations)} citations"
            )

            return {"content": content, "metadata": metadata}

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
            result = self.query("Test query. Respond with 'OK'.", max_tokens=10)
            return "content" in result and len(result["content"]) > 0
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
        try:
            pricing = PerplexityPricing.get_pricing(self.model)
            return pricing.estimate_cost(tokens_used, is_input)
        except Exception as e:
            logger.warning(f"Error estimating cost for model '{self.model}': {e}")
            # Fallback to base class generic estimate
            return super().estimate_cost(tokens_used, is_input)
