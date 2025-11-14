"""
Tests for LLM service functionality.
"""

from django.test import TestCase
from django.db import IntegrityError
from unittest.mock import Mock, patch, MagicMock
from api.models import Product, LLMPrompt, LLMQueryResult
from api.services.llm import LLMService
from api.services.llm.exceptions import (
    LLMProviderError,
    LLMAuthenticationError,
)


class LLMServiceTestCase(TestCase):
    """Test the LLMService orchestrator"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a test product
        self.product = Product.objects.create(
            upc_code='123456789012',
            name='Test Product',
            brand='Test Brand'
        )
        
        # Create a test prompt
        self.prompt = LLMPrompt.objects.create(
            name='test_prompt',
            query_type='review_summary',
            prompt_template='Summarize reviews for {product_name} by {brand}',
            is_active=True
        )
        
        # Mock LLM response
        self.mock_llm_response = {
            'content': 'This is a test review summary.',
            'metadata': {
                'model': 'test-model',
                'tokens_used': 100,
                'cost_estimate': 0.002,
                'finish_reason': 'stop',
            }
        }
    
    @patch('api.services.llm.llm_service.PerplexityProvider')
    @patch('api.services.llm.llm_service.settings')
    def test_get_product_insight_cache_miss(self, mock_settings, mock_provider_class):
        """Test getting insight when cache is empty (cache miss)"""
        # Mock settings
        mock_settings.LLM_CONFIG = {
            'default_provider': 'perplexity',
            'cache_ttl_days': 30,
            'enable_caching': True,
            'providers': {
                'perplexity': {
                    'api_key': 'test_api_key',
                    'model': 'test-model',
                    'max_tokens': 500,
                    'temperature': 0.7,
                }
            }
        }
        
        # Setup mock provider
        mock_provider = Mock()
        mock_provider.query.return_value = self.mock_llm_response
        mock_provider_class.return_value = mock_provider
        
        # Query service
        service = LLMService(default_provider='perplexity')
        result = service.get_product_insight(
            product=self.product,
            query_type='review_summary',
            provider='perplexity'
        )
        
        # Verify result
        self.assertEqual(result['content'], 'This is a test review summary.')
        self.assertFalse(result['cached'])
        self.assertIsNotNone(result['result_obj'])
        
        # Verify provider was called
        mock_provider.query.assert_called_once()
        
        # Verify result was cached
        cached = LLMQueryResult.objects.filter(
            product=self.product,
            prompt=self.prompt,
            provider='perplexity'
        ).first()
        
        self.assertIsNotNone(cached)
        self.assertEqual(cached.result, 'This is a test review summary.')
        self.assertFalse(cached.is_stale)
    
    @patch('api.services.llm.llm_service.PerplexityProvider')
    def test_get_product_insight_cache_hit(self, mock_provider_class):
        """Test getting insight when result is cached (cache hit)"""
        # Pre-populate cache
        LLMQueryResult.objects.create(
            product=self.product,
            prompt=self.prompt,
            provider='perplexity',
            query_input='Test query',
            result='Cached review summary',
            metadata={}
        )
        
        # Setup mock provider (should NOT be called)
        mock_provider = Mock()
        mock_provider_class.return_value = mock_provider
        
        # Query service
        service = LLMService(default_provider='perplexity')
        result = service.get_product_insight(
            product=self.product,
            query_type='review_summary',
            provider='perplexity'
        )
        
        # Verify cached result was returned
        self.assertEqual(result['content'], 'Cached review summary')
        self.assertTrue(result['cached'])
        self.assertIsNotNone(result['result_obj'])
        
        # Verify provider was NOT called (cache hit)
        mock_provider.query.assert_not_called()
    
    @patch('api.services.llm.llm_service.PerplexityProvider')
    @patch('api.services.llm.llm_service.settings')
    def test_get_product_insight_force_refresh(self, mock_settings, mock_provider_class):
        """Test force refresh bypasses cache"""
        # Mock settings
        mock_settings.LLM_CONFIG = {
            'default_provider': 'perplexity',
            'cache_ttl_days': 30,
            'enable_caching': True,
            'providers': {
                'perplexity': {
                    'api_key': 'test_api_key',
                    'model': 'test-model',
                    'max_tokens': 500,
                    'temperature': 0.7,
                }
            }
        }
        
        # Pre-populate cache
        LLMQueryResult.objects.create(
            product=self.product,
            prompt=self.prompt,
            provider='perplexity',
            query_input='Test query',
            result='Cached review summary',
            metadata={}
        )
        
        # Setup mock provider
        mock_provider = Mock()
        mock_provider.query.return_value = self.mock_llm_response
        mock_provider_class.return_value = mock_provider
        
        # Query service with force_refresh=True
        service = LLMService(default_provider='perplexity')
        result = service.get_product_insight(
            product=self.product,
            query_type='review_summary',
            provider='perplexity',
            force_refresh=True
        )
        
        # Verify fresh result was returned (not cached one)
        self.assertEqual(result['content'], 'This is a test review summary.')
        self.assertFalse(result['cached'])
        self.assertIsNotNone(result['result_obj'])
        
        # Verify provider WAS called (despite cache)
        mock_provider.query.assert_called_once()
    
    def test_invalidate_cache(self):
        """Test cache invalidation"""
        # Create some cached results
        result1 = LLMQueryResult.objects.create(
            product=self.product,
            prompt=self.prompt,
            provider='perplexity',
            query_input='Test query',
            result='Result 1',
            metadata={}
        )
        
        result2 = LLMQueryResult.objects.create(
            product=self.product,
            prompt=self.prompt,
            provider='openai',
            query_input='Test query',
            result='Result 2',
            metadata={}
        )
        
        # Invalidate cache for perplexity only
        service = LLMService()
        count = service.invalidate_cache(
            product=self.product,
            provider='perplexity'
        )
        
        self.assertEqual(count, 1)
        
        # Check result1 is stale, result2 is not
        result1.refresh_from_db()
        result2.refresh_from_db()
        self.assertTrue(result1.is_stale)
        self.assertFalse(result2.is_stale)
    
    def test_prompt_rendering(self):
        """Test prompt template rendering with product data"""
        service = LLMService()
        rendered = service._render_prompt(self.prompt, self.product)
        
        expected = 'Summarize reviews for Test Product by Test Brand'
        self.assertEqual(rendered, expected)
    
    def test_missing_prompt(self):
        """Test error when no active prompt exists"""
        service = LLMService()
        
        with self.assertRaises(LLMPrompt.DoesNotExist):
            service.get_product_insight(
                product=self.product,
                query_type='nonexistent_query_type'
            )
    
    def test_get_cache_stats(self):
        """Test cache statistics"""
        # Create some cached results
        LLMQueryResult.objects.create(
            product=self.product,
            prompt=self.prompt,
            provider='perplexity',
            query_input='Test',
            result='Result 1',
            is_stale=False,
            metadata={}
        )
        
        LLMQueryResult.objects.create(
            product=self.product,
            prompt=self.prompt,
            provider='openai',
            query_input='Test',
            result='Result 2',
            is_stale=True,
            metadata={}
        )
        
        service = LLMService()
        stats = service.get_cache_stats(product=self.product)
        
        self.assertEqual(stats['total_cached'], 2)
        self.assertEqual(stats['fresh'], 1)
        self.assertEqual(stats['stale'], 1)
        self.assertTrue(stats['cache_enabled'])


class LLMPromptModelTestCase(TestCase):
    """Test LLMPrompt model"""
    
    def test_prompt_render(self):
        """Test prompt rendering with product data"""
        product = Product.objects.create(
            upc_code='123456789012',
            name='Coffee Beans',
            brand='Best Coffee'
        )
        
        prompt = LLMPrompt.objects.create(
            name='test',
            query_type='test',
            prompt_template='Product: {product_name}, Brand: {brand}, UPC: {upc_code}',
            is_active=True
        )
        
        rendered = prompt.render(product)
        expected = 'Product: Coffee Beans, Brand: Best Coffee, UPC: 123456789012'
        self.assertEqual(rendered, expected)
    
    def test_prompt_render_missing_brand(self):
        """Test prompt rendering when brand is None"""
        product = Product.objects.create(
            upc_code='123456789012',
            name='No Brand Product',
            brand=None
        )
        
        prompt = LLMPrompt.objects.create(
            name='test',
            query_type='test',
            prompt_template='Product: {product_name}, Brand: {brand}',
            is_active=True
        )
        
        rendered = prompt.render(product)
        # Should use 'Unknown Brand' as fallback
        self.assertIn('Unknown Brand', rendered)


class LLMQueryResultModelTestCase(TestCase):
    """Test LLMQueryResult model"""
    
    def setUp(self):
        self.product = Product.objects.create(
            upc_code='123456789012',
            name='Test Product',
            brand='Test Brand'
        )
        
        self.prompt = LLMPrompt.objects.create(
            name='test_prompt',
            query_type='review_summary',
            prompt_template='Test',
            is_active=True
        )
    
    def test_is_fresh_new_result(self):
        """Test that newly created results are fresh"""
        result = LLMQueryResult.objects.create(
            product=self.product,
            prompt=self.prompt,
            provider='perplexity',
            query_input='Test',
            result='Fresh result',
            metadata={}
        )
        
        self.assertTrue(result.is_fresh(ttl_days=30))
    
    def test_is_fresh_stale_flag(self):
        """Test that results marked as stale are not fresh"""
        result = LLMQueryResult.objects.create(
            product=self.product,
            prompt=self.prompt,
            provider='perplexity',
            query_input='Test',
            result='Stale result',
            is_stale=True,
            metadata={}
        )
        
        self.assertFalse(result.is_fresh(ttl_days=30))
    
    def test_unique_constraint(self):
        """Test that (product, prompt, provider) is unique"""
        LLMQueryResult.objects.create(
            product=self.product,
            prompt=self.prompt,
            provider='perplexity',
            query_input='Test',
            result='Result 1',
            metadata={}
        )
        
        # This should raise an IntegrityError
        with self.assertRaises(IntegrityError):
            LLMQueryResult.objects.create(
                product=self.product,
                prompt=self.prompt,
                provider='perplexity',  # Same combination
                query_input='Test 2',
                result='Result 2',
                metadata={}
            )

