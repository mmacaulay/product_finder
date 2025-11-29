"""
LLM Service orchestrator.

Manages LLM providers, caching, and prompt rendering.
"""

import logging
from typing import Optional, Dict, Any, Union
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from api.dao import ProductDAO, LLMPromptDAO, LLMQueryResultDAO
from .base_provider import BaseLLMProvider
from .openai_provider import OpenAIProvider
from .perplexity_provider import PerplexityProvider
from .exceptions import LLMProviderError
from .schemas import get_schema, validate_response
from .json_parser import create_error_response

logger = logging.getLogger(__name__)


class LLMService:
    """
    Main service for LLM operations with caching and provider management.

    This service:
    - Manages multiple LLM providers
    - Implements intelligent caching to reduce API costs
    - Handles prompt template rendering
    - Provides a simple interface for GraphQL and other consumers
    """

    def __init__(self, default_provider: Optional[str] = None):
        """
        Initialize the LLM service.

        Args:
            default_provider: Provider to use by default (overrides settings)
        """
        self.config = settings.LLM_CONFIG
        self.default_provider_name = default_provider or self.config["default_provider"]
        self._providers: Dict[str, BaseLLMProvider] = {}

        logger.info(
            f"LLMService initialized with default provider: {self.default_provider_name}"
        )

    def get_product_insight(
        self,
        product: Union[Dict[str, Any], str],
        query_type: str,
        provider: Optional[str] = None,
        force_refresh: bool = False,
        max_retries: int = 2,
    ) -> Dict[str, Any]:
        """
        Get LLM-generated insight for a product.

        Args:
            product: Product dict from DAO (or UPC string)
            query_type: Type of query (e.g., 'review_summary')
            provider: LLM provider to use (defaults to self.default_provider_name)
            force_refresh: Skip cache and query LLM directly
            max_retries: Maximum number of retry attempts for failed parsing (default: 2)

        Returns:
            Dictionary with:
                - content: The structured JSON data from LLM
                - cached: Whether result was from cache
                - result_obj: The LLMQueryResult dict

        Raises:
            ValueError: If no active prompt exists for query_type
            LLMProviderError: If the LLM query fails after retries
        """
        provider_name = provider or self.default_provider_name

        # Get the prompt template from DAO
        prompt_dao = LLMPromptDAO()
        prompts = prompt_dao.get_active_by_type(query_type)

        if not prompts:
            raise ValueError(f"No active prompt found for query_type '{query_type}'")

        prompt_obj = prompts[0]  # Use first active prompt

        # Ensure product is a dict
        if isinstance(product, str):
            # If it's a UPC string, fetch the product
            product_dao = ProductDAO()
            product = product_dao.get_by_upc(product)
            if not product:
                raise ValueError(f"Product with UPC {product} not found")

        product_upc = product["upc_code"]

        # Check cache unless force_refresh is True
        if not force_refresh and self.config["enable_caching"]:
            cached_result = self._check_cache(product, prompt_obj, provider_name)
            if cached_result:
                logger.info(
                    f"Cache hit for product={product_upc}, query_type={query_type}, "
                    f"provider={provider_name}"
                )
                return {
                    "content": cached_result["result"],
                    "cached": True,
                    "result_obj": cached_result,
                }

        # Cache miss or force refresh - query LLM with retry logic
        logger.info(
            f"Cache miss for product={product_upc}, query_type={query_type}, "
            f"provider={provider_name}. Querying LLM..."
        )

        # Render prompt with product data
        rendered_prompt = self._render_prompt(prompt_obj, product)

        # Get provider and query with retry logic
        llm_provider = self._get_provider(provider_name)
        response, attempts = self._query_with_retry(
            llm_provider=llm_provider,
            prompt=rendered_prompt,
            query_type=query_type,
            max_retries=max_retries,
        )

        # Validate and store result
        result_obj = self._store_result(
            product=product,
            prompt=prompt_obj,
            provider=provider_name,
            query_input=rendered_prompt,
            result=response["content"],
            metadata=response["metadata"],
            schema_version=prompt_obj["schema_version"],
            parse_attempts=attempts,
        )

        return {
            "content": response["content"],
            "cached": False,
            "result_obj": result_obj,
        }

    def invalidate_cache(
        self,
        product: Union[Dict[str, Any], str],
        query_type: Optional[str] = None,
        provider: Optional[str] = None,
    ):
        """
        Mark cached results as stale.

        Args:
            product: Product dict or UPC string to invalidate cache for
            query_type: Optional specific query type to invalidate
            provider: Optional specific provider to invalidate
        """
        # Get product UPC
        if isinstance(product, str):
            product_upc = product
        else:
            product_upc = product["upc_code"]

        result_dao = LLMQueryResultDAO()
        results = result_dao.get_by_product(product_upc)

        count = 0
        for result in results:
            # Filter by query_type and provider if specified
            if query_type and result.get("prompt_name") != query_type:
                continue
            if provider and result.get("provider") != provider:
                continue

            # Mark as stale
            result_dao.mark_stale(
                product_upc=product_upc,
                prompt_name=result["prompt_name"],
                provider=result["provider"],
            )
            count += 1

        logger.info(f"Invalidated {count} cached result(s) for product {product_upc}")
        return count

    def get_cache_stats(
        self, product: Optional[Union[Dict[str, Any], str]] = None
    ) -> Dict[str, Any]:
        """
        Get cache statistics.

        Args:
            product: Optional product dict or UPC to get stats for (otherwise global stats)

        Returns:
            Dictionary with cache statistics
        """
        result_dao = LLMQueryResultDAO()

        # Note: For global stats, we'd need to iterate through all products
        # This is simplified for now - consider implementing pagination or aggregation
        if product:
            if isinstance(product, str):
                product_upc = product
            else:
                product_upc = product["upc_code"]

            results = result_dao.get_by_product(product_upc)
            total_cached = len(results)
            fresh_cached = sum(1 for r in results if not r.get("is_stale"))
            stale_cached = sum(1 for r in results if r.get("is_stale"))

            ttl_days = self.config["cache_ttl_days"]
            cutoff_date = timezone.now() - timedelta(days=ttl_days)
            old_cached = sum(
                1
                for r in results
                if r.get("created_at") and r["created_at"] < cutoff_date
            )

            return {
                "total_cached": total_cached,
                "fresh": fresh_cached,
                "stale": stale_cached,
                "old": old_cached,
                "cache_enabled": self.config["enable_caching"],
                "ttl_days": ttl_days,
            }
        else:
            # Global stats not easily supported without scanning all Firestore docs
            # Return placeholder for now
            return {
                "total_cached": 0,
                "fresh": 0,
                "stale": 0,
                "old": 0,
                "cache_enabled": self.config["enable_caching"],
                "ttl_days": self.config["cache_ttl_days"],
                "note": "Global stats require scanning all products - use product-specific queries",
            }

    def _check_cache(
        self, product: Dict[str, Any], prompt: Dict[str, Any], provider: str
    ) -> Optional[Dict[str, Any]]:
        """
        Check if a fresh cached result exists.

        Args:
            product: Product dict
            prompt: LLMPrompt dict
            provider: Provider name

        Returns:
            LLMQueryResult dict if found and fresh, None otherwise
        """
        result_dao = LLMQueryResultDAO()
        cached = result_dao.get(
            product_upc=product["upc_code"],
            prompt_name=prompt["name"],
            provider=provider,
        )

        if not cached:
            return None

        ttl_days = self.config["cache_ttl_days"]
        if result_dao.is_fresh(cached, ttl_days=ttl_days):
            return cached
        else:
            logger.debug(f"Cached result exists but is stale (age > {ttl_days} days)")
            return None

    def _query_with_retry(
        self,
        llm_provider: BaseLLMProvider,
        prompt: str,
        query_type: str,
        max_retries: int = 2,
    ) -> tuple[Dict[str, Any], int]:
        """
        Query LLM with retry logic for parsing failures.

        Args:
            llm_provider: The LLM provider instance
            prompt: The rendered prompt
            query_type: Type of query for schema validation
            max_retries: Maximum retry attempts

        Returns:
            Tuple of (response dict, attempt count)

        Raises:
            LLMProviderError: If all attempts fail
        """
        schema = get_schema(query_type)
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                # Add stronger JSON instructions on retries
                if attempt > 1:
                    retry_prompt = f"{prompt}\n\nIMPORTANT: Your previous response had parsing errors. You MUST respond with ONLY valid JSON. No markdown, no code blocks, no explanations. Start with {{ and end with }}."
                    response = llm_provider.query(retry_prompt)
                else:
                    response = llm_provider.query(prompt)

                # Validate against schema if available
                if schema and isinstance(response["content"], dict):
                    validated_content = validate_response(response["content"], schema)
                    response["content"] = validated_content
                    logger.info(
                        f"Successfully validated response against {query_type} schema"
                    )

                logger.info(f"LLM query succeeded on attempt {attempt}")
                return response, attempt

            except (LLMProviderError, ValueError) as e:
                last_error = e
                logger.warning(f"Attempt {attempt}/{max_retries} failed: {e}")

                if attempt >= max_retries:
                    # All retries exhausted - create error response
                    logger.error(
                        f"All {max_retries} attempts failed for query_type={query_type}"
                    )
                    error_response = create_error_response(
                        error_message=str(last_error), raw_response=None
                    )
                    return {
                        "content": error_response,
                        "metadata": {"error": str(last_error), "attempts": attempt},
                    }, attempt

        # Should never reach here, but just in case
        raise LLMProviderError(
            f"Query failed after {max_retries} attempts: {last_error}"
        )

    def _store_result(
        self,
        product: Dict[str, Any],
        prompt: Dict[str, Any],
        provider: str,
        query_input: str,
        result: Dict[str, Any],
        metadata: Dict[str, Any],
        schema_version: str = "1.0",
        parse_attempts: int = 1,
    ):
        """
        Store LLM result in cache.

        Args:
            product: Product dict
            prompt: LLMPrompt dict
            provider: Provider name
            query_input: The rendered prompt sent
            result: The structured JSON response
            metadata: Response metadata (tokens, cost, etc.)
            schema_version: Version of the schema used
            parse_attempts: Number of attempts to parse successfully
        """
        # Extract parse strategy from metadata
        parse_strategy = metadata.get("parse_strategy")

        # Store via DAO
        result_dao = LLMQueryResultDAO()
        cached = result_dao.create_or_update(
            product_upc=product["upc_code"],
            prompt_name=prompt["name"],
            provider=provider,
            query_input=query_input,
            result=result,
            metadata=metadata,
            schema_version=schema_version,
            parse_attempts=parse_attempts,
            parse_strategy=parse_strategy,
        )

        logger.info(
            f"Stored cached result for product={product['upc_code']}, "
            f"prompt={prompt['name']}, provider={provider}, attempts={parse_attempts}"
        )

        return cached

    def _render_prompt(self, prompt: Dict[str, Any], product: Dict[str, Any]) -> str:
        """
        Render prompt template with product data.

        Args:
            prompt: LLMPrompt dict
            product: Product dict

        Returns:
            Rendered prompt string
        """
        try:
            # Simple template rendering using string formatting
            template = prompt["prompt_template"]

            # Build context from product data
            context = {
                "name": product.get("name", "Unknown"),
                "brand": product.get("brand", "Unknown"),
                "upc_code": product.get("upc_code", ""),
            }

            # If de_product_data exists, merge it
            if product.get("de_product_data"):
                context.update(product["de_product_data"])

            rendered = template.format(**context)
            return rendered

        except KeyError as e:
            logger.error(f"Missing variable in prompt template: {e}")
            raise ValueError(f"Prompt template error: missing variable {e}")

    def _get_provider(self, provider_name: str) -> BaseLLMProvider:
        """
        Get or create provider instance.

        Args:
            provider_name: Name of the provider ('openai', 'perplexity')

        Returns:
            Provider instance

        Raises:
            ValueError: If provider is not configured or unknown
        """
        # Return cached provider if exists
        if provider_name in self._providers:
            return self._providers[provider_name]

        # Create new provider instance
        if provider_name not in self.config["providers"]:
            raise ValueError(
                f"Unknown provider '{provider_name}'. "
                f"Available: {list(self.config['providers'].keys())}"
            )

        provider_config = self.config["providers"][provider_name]

        if not provider_config.get("api_key"):
            raise ValueError(
                f"No API key configured for provider '{provider_name}'. "
                f"Set {provider_name.upper()}_API_KEY environment variable."
            )

        # Instantiate provider
        if provider_name == "openai":
            provider = OpenAIProvider(**provider_config)
        elif provider_name == "perplexity":
            provider = PerplexityProvider(**provider_config)
        else:
            raise ValueError(f"Provider '{provider_name}' is not implemented yet")

        # Cache the provider instance
        self._providers[provider_name] = provider
        logger.info(f"Initialized {provider_name} provider")

        return provider

    def list_available_providers(self) -> list[str]:
        """
        List all configured providers.

        Returns:
            List of provider names
        """
        return list(self.config["providers"].keys())

    def validate_provider(self, provider_name: str) -> bool:
        """
        Validate that a provider is properly configured and credentials work.

        Args:
            provider_name: Name of the provider to validate

        Returns:
            True if provider is valid and credentials work
        """
        try:
            provider = self._get_provider(provider_name)
            return provider.validate_credentials()
        except Exception as e:
            logger.error(f"Provider validation failed for '{provider_name}': {e}")
            return False
