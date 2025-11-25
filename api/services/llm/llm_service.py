"""
LLM Service orchestrator.

Manages LLM providers, caching, and prompt rendering.
"""

import logging
from typing import Optional, Dict, Any, Union
from django.conf import settings
from django.utils import timezone
from datetime import timedelta, datetime

# from api.models import Product, LLMPrompt, LLMQueryResult # Removed Django models
from api.firestore_models import LLMPromptDAO, LLMQueryResultDAO
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
        
        self.prompt_dao = LLMPromptDAO()
        self.result_dao = LLMQueryResultDAO()
        
        logger.info(f"LLMService initialized with default provider: {self.default_provider_name}")
    
    def get_product_insight(
        self,
        product: Any, # Can be Product model or dict
        query_type: str,
        provider: Optional[str] = None,
        force_refresh: bool = False,
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        Get LLM-generated insight for a product.
        
        Args:
            product: Product instance or dict
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
            Exception: If no active prompt exists for query_type
            LLMProviderError: If the LLM query fails after retries
        """
        provider_name = provider or self.default_provider_name
        
        # Get the prompt template
        # We assume there's only one active prompt per query_type for now, or we take the first one
        active_prompts = self.prompt_dao.get_active_by_type(query_type)
        if not active_prompts:
             raise Exception(
                f"No active prompt found for query_type '{query_type}'"
            )
        prompt_obj = active_prompts[0]
        
        # Check cache unless force_refresh is True
        if not force_refresh and self.config['enable_caching']:
            cached_result = self._check_cache(product, prompt_obj, provider_name)
            if cached_result:
                # product_id = getattr(product, 'id', None) or product.get('id')
                # logger.info(
                #     f"Cache hit for product={product_id}, query_type={query_type}, "
                #     f"provider={provider_name}"
                # )
                return {
                    'content': cached_result['result'],
                    'cached': True,
                    'result_obj': cached_result
                }
        
        # Cache miss or force refresh - query LLM with retry logic
        # logger.info(
        #     f"Cache miss for product, query_type={query_type}, "
        #     f"provider={provider_name}. Querying LLM..."
        # )
        
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
            schema_version=prompt_obj.get('schema_version', '1.0'),
            parse_attempts=attempts
        )
        
        return {
            'content': response['content'],
            'cached': False,
            'result_obj': result_obj
        }
    
    def invalidate_cache(
        self,
        product: Any,
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
        # This is harder with Firestore without a composite query or iterating
        # For now, if we have query_type and provider, we can construct the ID
        # If not, we might need to query by product_upc
        
        # Assuming we have query_type and provider for now as that's how it's used
        if query_type and provider:
            # We need prompt name. This is tricky if we don't have it.
            # But usually we invalidate specific things.
            # For now, let's just log a warning that partial invalidation is limited
            logger.warning("Cache invalidation requires specific query_type and provider in this implementation")
            
            active_prompts = self.prompt_dao.get_active_by_type(query_type)
            if active_prompts:
                prompt_name = active_prompts[0]['name']
                upc = self._get_product_upc(product)
                self.result_dao.mark_stale(upc, prompt_name, provider)
                return 1
        return 0

    def get_cache_stats(self, product: Optional[Any] = None) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Args:
            product: Optional product to get stats for (otherwise global stats)
            
        Returns:
            Dictionary with cache statistics
        """
        # Firestore stats are expensive to compute (reads).
        # Returning dummy stats for now to avoid high costs/latency
        return {
            'total_cached': 0,
            'fresh': 0,
            'stale': 0,
            'old': 0,
            'cache_enabled': self.config['enable_caching'],
            'ttl_days': self.config['cache_ttl_days'],
        }
    
    def _check_cache(
        self,
        product: Any,
        prompt: Dict[str, Any],
        provider: str
    ) -> Optional[Dict[str, Any]]:
        """
        Check if a fresh cached result exists.
        
        Args:
            product: Product instance or dict
            prompt: LLMPrompt dict
            provider: Provider name
            
        Returns:
            LLMQueryResult dict if found and fresh, None otherwise
        """
        upc = self._get_product_upc(product)
        prompt_name = prompt['name']
        
        cached = self.result_dao.get_by_composite_key(upc, prompt_name, provider)
        
        if not cached:
            return None
            
        ttl_days = self.config['cache_ttl_days']
        created_at = cached.get('created_at')
        is_stale = cached.get('is_stale', False)
        
        if not created_at:
            return None
            
        # created_at from Firestore is a datetime
        age = timezone.now() - created_at
        if age < timedelta(days=ttl_days) and not is_stale:
            return cached
        else:
            logger.debug(f"Cached result exists but is stale (age > {ttl_days} days)")
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
        product: Any,
        prompt: Dict[str, Any],
        provider: str,
        query_input: str,
        result: Dict[str, Any],
        metadata: Dict[str, Any],
        schema_version: str = "1.0",
        parse_attempts: int = 1
    ):
        """
        Store LLM result in cache.
        """
        upc = self._get_product_upc(product)
        prompt_name = prompt['name']
        
        # Extract parse strategy from metadata
        parse_strategy = metadata.get('parse_strategy')
        
        return self.result_dao.create(
            product_upc=upc,
            prompt_name=prompt_name,
            provider=provider,
            query_input=query_input,
            result=result,
            metadata=metadata,
            schema_version=schema_version,
            parse_attempts=parse_attempts,
            parse_strategy=parse_strategy
        )
    
    def _render_prompt(self, prompt: Dict[str, Any], product: Any) -> str:
        """
        Render prompt template with product data.
        """
        template = prompt.get('prompt_template', '')
        
        # Handle both Product model and dict
        if isinstance(product, dict):
            name = product.get('name', 'Unknown Product')
            brand = product.get('brand', 'Unknown Brand')
            upc = product.get('upc_code', '')
            data = product.get('de_product_data', '')
        else:
            name = getattr(product, 'name', 'Unknown Product')
            brand = getattr(product, 'brand', 'Unknown Brand')
            upc = getattr(product, 'upc_code', '')
            data = getattr(product, 'de_product_data', '')
            
        try:
            return template.format(
                product_name=name,
                brand=brand,
                upc_code=upc,
                additional_data=str(data) if data else ''
            )
        except KeyError as e:
            logger.error(f"Missing variable in prompt template: {e}")
            raise ValueError(f"Prompt template error: missing variable {e}")
    
    def _get_product_upc(self, product: Any) -> str:
        if isinstance(product, dict):
            return product.get('upc_code')
        return getattr(product, 'upc_code')

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



