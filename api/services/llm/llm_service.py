"""
LLM Service orchestrator.

Manages LLM providers, caching, and prompt rendering.
"""

import logging
from typing import Optional, Dict, Any
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from api.models import Product, LLMPrompt, LLMQueryResult
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
        self.default_provider_name = default_provider or self.config['default_provider']
        self._providers: Dict[str, BaseLLMProvider] = {}
        
        logger.info(f"LLMService initialized with default provider: {self.default_provider_name}")
    
    def get_product_insight(
        self,
        product: Product,
        query_type: str,
        provider: Optional[str] = None,
        force_refresh: bool = False,
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        Get LLM-generated insight for a product.
        
        Args:
            product: Product instance
            query_type: Type of query (e.g., 'review_summary')
            provider: LLM provider to use (defaults to self.default_provider_name)
            force_refresh: Skip cache and query LLM directly
            max_retries: Maximum number of retry attempts for failed parsing (default: 2)
            
        Returns:
            Dictionary with:
                - content: The structured JSON data from LLM
                - cached: Whether result was from cache
                - result_obj: The LLMQueryResult instance
            
        Raises:
            LLMPrompt.DoesNotExist: If no active prompt exists for query_type
            LLMProviderError: If the LLM query fails after retries
        """
        provider_name = provider or self.default_provider_name
        
        # Get the prompt template
        prompt_obj = LLMPrompt.objects.filter(
            query_type=query_type,
            is_active=True
        ).first()
        
        if not prompt_obj:
            raise LLMPrompt.DoesNotExist(
                f"No active prompt found for query_type '{query_type}'"
            )
        
        # Check cache unless force_refresh is True
        if not force_refresh and self.config['enable_caching']:
            cached_result = self._check_cache(product, prompt_obj, provider_name)
            if cached_result:
                logger.info(
                    f"Cache hit for product={product.id}, query_type={query_type}, "
                    f"provider={provider_name}"
                )
                return {
                    'content': cached_result.result,
                    'cached': True,
                    'result_obj': cached_result
                }
        
        # Cache miss or force refresh - query LLM with retry logic
        logger.info(
            f"Cache miss for product={product.id}, query_type={query_type}, "
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
            max_retries=max_retries
        )
        
        # Validate and store result
        result_obj = self._store_result(
            product=product,
            prompt=prompt_obj,
            provider=provider_name,
            query_input=rendered_prompt,
            result=response['content'],
            metadata=response['metadata'],
            schema_version=prompt_obj.schema_version,
            parse_attempts=attempts
        )
        
        return {
            'content': response['content'],
            'cached': False,
            'result_obj': result_obj
        }
    
    def invalidate_cache(
        self,
        product: Product,
        query_type: Optional[str] = None,
        provider: Optional[str] = None
    ):
        """
        Mark cached results as stale.
        
        Args:
            product: Product to invalidate cache for
            query_type: Optional specific query type to invalidate
            provider: Optional specific provider to invalidate
        """
        queryset = LLMQueryResult.objects.filter(product=product)
        
        if query_type:
            queryset = queryset.filter(prompt__query_type=query_type)
        if provider:
            queryset = queryset.filter(provider=provider)
        
        count = queryset.update(is_stale=True)
        logger.info(f"Invalidated {count} cached result(s) for product {product.id}")
        return count
    
    def get_cache_stats(self, product: Optional[Product] = None) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Args:
            product: Optional product to get stats for (otherwise global stats)
            
        Returns:
            Dictionary with cache statistics
        """
        queryset = LLMQueryResult.objects.all()
        if product:
            queryset = queryset.filter(product=product)
        
        total_cached = queryset.count()
        fresh_cached = queryset.filter(is_stale=False).count()
        stale_cached = queryset.filter(is_stale=True).count()
        
        ttl_days = self.config['cache_ttl_days']
        cutoff_date = timezone.now() - timedelta(days=ttl_days)
        old_cached = queryset.filter(created_at__lt=cutoff_date).count()
        
        return {
            'total_cached': total_cached,
            'fresh': fresh_cached,
            'stale': stale_cached,
            'old': old_cached,
            'cache_enabled': self.config['enable_caching'],
            'ttl_days': ttl_days,
        }
    
    def _check_cache(
        self,
        product: Product,
        prompt: LLMPrompt,
        provider: str
    ) -> Optional[LLMQueryResult]:
        """
        Check if a fresh cached result exists.
        
        Args:
            product: Product instance
            prompt: LLMPrompt instance
            provider: Provider name
            
        Returns:
            LLMQueryResult if found and fresh, None otherwise
        """
        try:
            cached = LLMQueryResult.objects.get(
                product=product,
                prompt=prompt,
                provider=provider
            )
            
            ttl_days = self.config['cache_ttl_days']
            if cached.is_fresh(ttl_days=ttl_days):
                return cached
            else:
                logger.debug(f"Cached result exists but is stale (age > {ttl_days} days)")
                return None
                
        except LLMQueryResult.DoesNotExist:
            return None
    
    def _query_with_retry(
        self,
        llm_provider: BaseLLMProvider,
        prompt: str,
        query_type: str,
        max_retries: int = 2
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
                if schema and isinstance(response['content'], dict):
                    validated_content = validate_response(response['content'], schema)
                    response['content'] = validated_content
                    logger.info(f"Successfully validated response against {query_type} schema")
                
                logger.info(f"LLM query succeeded on attempt {attempt}")
                return response, attempt
                
            except (LLMProviderError, ValueError) as e:
                last_error = e
                logger.warning(f"Attempt {attempt}/{max_retries} failed: {e}")
                
                if attempt >= max_retries:
                    # All retries exhausted - create error response
                    logger.error(f"All {max_retries} attempts failed for query_type={query_type}")
                    error_response = create_error_response(
                        error_message=str(last_error),
                        raw_response=None
                    )
                    return {
                        'content': error_response,
                        'metadata': {'error': str(last_error), 'attempts': attempt}
                    }, attempt
        
        # Should never reach here, but just in case
        raise LLMProviderError(f"Query failed after {max_retries} attempts: {last_error}")
    
    def _store_result(
        self,
        product: Product,
        prompt: LLMPrompt,
        provider: str,
        query_input: str,
        result: Dict[str, Any],
        metadata: Dict[str, Any],
        schema_version: str = "1.0",
        parse_attempts: int = 1
    ):
        """
        Store LLM result in cache.
        
        Args:
            product: Product instance
            prompt: LLMPrompt instance
            provider: Provider name
            query_input: The rendered prompt sent
            result: The structured JSON response
            metadata: Response metadata (tokens, cost, etc.)
            schema_version: Version of the schema used
            parse_attempts: Number of attempts to parse successfully
        """
        # Extract parse strategy from metadata
        parse_strategy = metadata.get('parse_strategy')
        
        # Update or create cache entry
        cached, created = LLMQueryResult.objects.update_or_create(
            product=product,
            prompt=prompt,
            provider=provider,
            defaults={
                'query_input': query_input,
                'result': result,
                'metadata': metadata,
                'schema_version': schema_version,
                'parse_attempts': parse_attempts,
                'parse_strategy': parse_strategy,
                'is_stale': False,
            }
        )
        
        action = "Created" if created else "Updated"
        logger.info(
            f"{action} cached result for product={product.id}, "
            f"prompt={prompt.name}, provider={provider}, attempts={parse_attempts}"
        )
        
        return cached
    
    def _render_prompt(self, prompt: LLMPrompt, product: Product) -> str:
        """
        Render prompt template with product data.
        
        Args:
            prompt: LLMPrompt instance
            product: Product instance
            
        Returns:
            Rendered prompt string
        """
        try:
            return prompt.render(product)
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
        if provider_name not in self.config['providers']:
            raise ValueError(
                f"Unknown provider '{provider_name}'. "
                f"Available: {list(self.config['providers'].keys())}"
            )
        
        provider_config = self.config['providers'][provider_name]
        
        if not provider_config.get('api_key'):
            raise ValueError(
                f"No API key configured for provider '{provider_name}'. "
                f"Set {provider_name.upper()}_API_KEY environment variable."
            )
        
        # Instantiate provider
        if provider_name == 'openai':
            provider = OpenAIProvider(**provider_config)
        elif provider_name == 'perplexity':
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
        return list(self.config['providers'].keys())
    
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



