"""
Tests for LLM service functionality.
"""

from django.test import TestCase
from django.db import IntegrityError
from unittest.mock import Mock, patch
from api.models import Product, LLMPrompt, LLMQueryResult
from api.services.llm import LLMService


class LLMServiceTestCase(TestCase):
    """Test the LLMService orchestrator"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a test product
        self.product = Product.objects.create(
            upc_code="123456789012", name="Test Product", brand="Test Brand"
        )

        # Create a test prompt
        self.prompt = LLMPrompt.objects.create(
            name="test_prompt",
            query_type="review_summary",
            prompt_template="Summarize reviews for {product_name} by {brand}",
            schema_version="1.0",
            is_active=True,
        )

        # Mock LLM response (now structured JSON)
        self.mock_llm_response = {
            "content": {
                "sentiment": "positive",
                "sentiment_score": 0.85,
                "summary": "This is a test review summary.",
                "pros": ["Great quality", "Good value", "Fast shipping"],
                "cons": ["None found"],
                "key_themes": ["quality", "value"],
                "confidence": "high",
            },
            "metadata": {
                "model": "test-model",
                "tokens_used": 100,
                "cost_estimate": 0.002,
                "finish_reason": "stop",
                "parse_success": True,
                "json_mode_enabled": True,
            },
        }

    @patch("api.services.llm.llm_service.PerplexityProvider")
    @patch("api.services.llm.llm_service.settings")
    def test_get_product_insight_cache_miss(self, mock_settings, mock_provider_class):
        """Test getting insight when cache is empty (cache miss)"""
        # Mock settings
        mock_settings.LLM_CONFIG = {
            "default_provider": "perplexity",
            "cache_ttl_days": 30,
            "enable_caching": True,
            "providers": {
                "perplexity": {
                    "api_key": "test_api_key",
                    "model": "test-model",
                    "max_tokens": 500,
                    "temperature": 0.7,
                }
            },
        }

        # Setup mock provider
        mock_provider = Mock()
        mock_provider.query.return_value = self.mock_llm_response
        mock_provider_class.return_value = mock_provider

        # Query service
        service = LLMService(default_provider="perplexity")
        result = service.get_product_insight(
            product=self.product, query_type="review_summary", provider="perplexity"
        )

        # Verify result structure
        self.assertIsInstance(result["content"], dict)
        self.assertEqual(result["content"]["sentiment"], "positive")
        self.assertEqual(result["content"]["summary"], "This is a test review summary.")
        self.assertFalse(result["cached"])
        self.assertIsNotNone(result["result_obj"])

        # Verify provider was called
        mock_provider.query.assert_called_once()

        # Verify result was cached
        cached = LLMQueryResult.objects.filter(
            product=self.product, prompt=self.prompt, provider="perplexity"
        ).first()

        self.assertIsNotNone(cached)
        self.assertIsInstance(cached.result, dict)
        self.assertEqual(cached.result["sentiment"], "positive")
        self.assertFalse(cached.is_stale)

    @patch("api.services.llm.llm_service.PerplexityProvider")
    def test_get_product_insight_cache_hit(self, mock_provider_class):
        """Test getting insight when result is cached (cache hit)"""
        # Pre-populate cache with structured data
        cached_result = {
            "sentiment": "positive",
            "sentiment_score": 0.9,
            "summary": "Cached review summary",
            "pros": ["Good"],
            "cons": ["None"],
            "key_themes": ["quality"],
            "confidence": "high",
        }
        LLMQueryResult.objects.create(
            product=self.product,
            prompt=self.prompt,
            provider="perplexity",
            query_input="Test query",
            result=cached_result,
            metadata={},
        )

        # Setup mock provider (should NOT be called)
        mock_provider = Mock()
        mock_provider_class.return_value = mock_provider

        # Query service
        service = LLMService(default_provider="perplexity")
        result = service.get_product_insight(
            product=self.product, query_type="review_summary", provider="perplexity"
        )

        # Verify cached result was returned
        self.assertIsInstance(result["content"], dict)
        self.assertEqual(result["content"]["summary"], "Cached review summary")
        self.assertEqual(result["content"]["sentiment"], "positive")
        self.assertTrue(result["cached"])
        self.assertIsNotNone(result["result_obj"])

        # Verify provider was NOT called (cache hit)
        mock_provider.query.assert_not_called()

    @patch("api.services.llm.llm_service.PerplexityProvider")
    @patch("api.services.llm.llm_service.settings")
    def test_get_product_insight_force_refresh(
        self, mock_settings, mock_provider_class
    ):
        """Test force refresh bypasses cache"""
        # Mock settings
        mock_settings.LLM_CONFIG = {
            "default_provider": "perplexity",
            "cache_ttl_days": 30,
            "enable_caching": True,
            "providers": {
                "perplexity": {
                    "api_key": "test_api_key",
                    "model": "test-model",
                    "max_tokens": 500,
                    "temperature": 0.7,
                }
            },
        }

        # Pre-populate cache with structured data
        cached_result = {
            "sentiment": "positive",
            "sentiment_score": 0.8,
            "summary": "Cached review summary",
            "pros": [],
            "cons": [],
            "key_themes": [],
            "confidence": "medium",
        }
        LLMQueryResult.objects.create(
            product=self.product,
            prompt=self.prompt,
            provider="perplexity",
            query_input="Test query",
            result=cached_result,
            metadata={},
        )

        # Setup mock provider
        mock_provider = Mock()
        mock_provider.query.return_value = self.mock_llm_response
        mock_provider_class.return_value = mock_provider

        # Query service with force_refresh=True
        service = LLMService(default_provider="perplexity")
        result = service.get_product_insight(
            product=self.product,
            query_type="review_summary",
            provider="perplexity",
            force_refresh=True,
        )

        # Verify fresh result was returned (not cached one)
        self.assertIsInstance(result["content"], dict)
        self.assertEqual(result["content"]["summary"], "This is a test review summary.")
        self.assertEqual(result["content"]["sentiment"], "positive")
        self.assertFalse(result["cached"])
        self.assertIsNotNone(result["result_obj"])

        # Verify provider WAS called (despite cache)
        mock_provider.query.assert_called_once()

    def test_invalidate_cache(self):
        """Test cache invalidation"""
        # Create some cached results with structured data
        result1 = LLMQueryResult.objects.create(
            product=self.product,
            prompt=self.prompt,
            provider="perplexity",
            query_input="Test query",
            result={"summary": "Result 1"},
            metadata={},
        )

        result2 = LLMQueryResult.objects.create(
            product=self.product,
            prompt=self.prompt,
            provider="openai",
            query_input="Test query",
            result={"summary": "Result 2"},
            metadata={},
        )

        # Invalidate cache for perplexity only
        service = LLMService()
        count = service.invalidate_cache(product=self.product, provider="perplexity")

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

        expected = "Summarize reviews for Test Product by Test Brand"
        self.assertEqual(rendered, expected)

    def test_missing_prompt(self):
        """Test error when no active prompt exists"""
        service = LLMService()

        with self.assertRaises(LLMPrompt.DoesNotExist):
            service.get_product_insight(
                product=self.product, query_type="nonexistent_query_type"
            )

    def test_get_cache_stats(self):
        """Test cache statistics"""
        # Create some cached results with structured data
        LLMQueryResult.objects.create(
            product=self.product,
            prompt=self.prompt,
            provider="perplexity",
            query_input="Test",
            result={"summary": "Result 1"},
            is_stale=False,
            metadata={},
        )

        LLMQueryResult.objects.create(
            product=self.product,
            prompt=self.prompt,
            provider="openai",
            query_input="Test",
            result={"summary": "Result 2"},
            is_stale=True,
            metadata={},
        )

        service = LLMService()
        stats = service.get_cache_stats(product=self.product)

        self.assertEqual(stats["total_cached"], 2)
        self.assertEqual(stats["fresh"], 1)
        self.assertEqual(stats["stale"], 1)
        self.assertTrue(stats["cache_enabled"])


class LLMPromptModelTestCase(TestCase):
    """Test LLMPrompt model"""

    def test_prompt_render(self):
        """Test prompt rendering with product data"""
        product = Product.objects.create(
            upc_code="123456789012", name="Coffee Beans", brand="Best Coffee"
        )

        prompt = LLMPrompt.objects.create(
            name="test",
            query_type="test",
            prompt_template="Product: {product_name}, Brand: {brand}, UPC: {upc_code}",
            is_active=True,
        )

        rendered = prompt.render(product)
        expected = "Product: Coffee Beans, Brand: Best Coffee, UPC: 123456789012"
        self.assertEqual(rendered, expected)

    def test_prompt_render_missing_brand(self):
        """Test prompt rendering when brand is None"""
        product = Product.objects.create(
            upc_code="123456789012", name="No Brand Product", brand=None
        )

        prompt = LLMPrompt.objects.create(
            name="test",
            query_type="test",
            prompt_template="Product: {product_name}, Brand: {brand}",
            is_active=True,
        )

        rendered = prompt.render(product)
        # Should use 'Unknown Brand' as fallback
        self.assertIn("Unknown Brand", rendered)


class LLMQueryResultModelTestCase(TestCase):
    """Test LLMQueryResult model"""

    def setUp(self):
        self.product = Product.objects.create(
            upc_code="123456789012", name="Test Product", brand="Test Brand"
        )

        self.prompt = LLMPrompt.objects.create(
            name="test_prompt",
            query_type="review_summary",
            prompt_template="Test",
            is_active=True,
        )

    def test_is_fresh_new_result(self):
        """Test that newly created results are fresh"""
        result = LLMQueryResult.objects.create(
            product=self.product,
            prompt=self.prompt,
            provider="perplexity",
            query_input="Test",
            result={"summary": "Fresh result"},
            metadata={},
        )

        self.assertTrue(result.is_fresh(ttl_days=30))

    def test_is_fresh_stale_flag(self):
        """Test that results marked as stale are not fresh"""
        result = LLMQueryResult.objects.create(
            product=self.product,
            prompt=self.prompt,
            provider="perplexity",
            query_input="Test",
            result={"summary": "Stale result"},
            is_stale=True,
            metadata={},
        )

        self.assertFalse(result.is_fresh(ttl_days=30))

    def test_unique_constraint(self):
        """Test that (product, prompt, provider) is unique"""
        LLMQueryResult.objects.create(
            product=self.product,
            prompt=self.prompt,
            provider="perplexity",
            query_input="Test",
            result={"summary": "Result 1"},
            metadata={},
        )

        # This should raise an IntegrityError
        with self.assertRaises(IntegrityError):
            LLMQueryResult.objects.create(
                product=self.product,
                prompt=self.prompt,
                provider="perplexity",  # Same combination
                query_input="Test 2",
                result={"summary": "Result 2"},
                metadata={},
            )


class ProviderCostCalculationTestCase(TestCase):
    """Test that providers correctly calculate costs using the pricing module"""

    def test_openai_provider_cost_estimation_gpt5_nano(self):
        """Test OpenAI provider cost estimation for GPT-5 Nano"""
        from api.services.llm.openai_provider import OpenAIProvider

        provider = OpenAIProvider(api_key="test-key", model="gpt-5-nano")

        # Estimate input cost for 10,000 tokens
        input_cost = provider.estimate_cost(10_000, is_input=True)
        # Expected: 10,000/1M * 0.05 = 0.0005
        self.assertAlmostEqual(input_cost, 0.0005, places=6)

        # Estimate output cost for 10,000 tokens
        output_cost = provider.estimate_cost(10_000, is_input=False)
        # Expected: 10,000/1M * 0.40 = 0.004
        self.assertAlmostEqual(output_cost, 0.004, places=6)

    def test_openai_provider_cost_estimation_gpt5_mini(self):
        """Test OpenAI provider cost estimation for GPT-5 Mini"""
        from api.services.llm.openai_provider import OpenAIProvider

        provider = OpenAIProvider(api_key="test-key", model="gpt-5-mini")

        # Estimate input cost
        input_cost = provider.estimate_cost(10_000, is_input=True)
        # Expected: 10,000/1M * 0.25 = 0.0025
        self.assertAlmostEqual(input_cost, 0.0025, places=6)

        # Estimate output cost
        output_cost = provider.estimate_cost(10_000, is_input=False)
        # Expected: 10,000/1M * 2.00 = 0.02
        self.assertAlmostEqual(output_cost, 0.02, places=6)

    def test_perplexity_provider_cost_estimation_sonar(self):
        """Test Perplexity provider cost estimation for Sonar"""
        from api.services.llm.perplexity_provider import PerplexityProvider

        provider = PerplexityProvider(api_key="test-key", model="sonar")

        # Estimate cost (same for input and output on Perplexity)
        cost = provider.estimate_cost(10_000, is_input=True)
        # Expected: 10,000/1M * 1.00 = 0.01
        self.assertAlmostEqual(cost, 0.01, places=6)

    def test_perplexity_provider_cost_estimation_sonar_pro(self):
        """Test Perplexity provider cost estimation for Sonar Pro"""
        from api.services.llm.perplexity_provider import PerplexityProvider

        provider = PerplexityProvider(api_key="test-key", model="sonar-pro")

        # Estimate input cost
        input_cost = provider.estimate_cost(10_000, is_input=True)
        # Expected: 10,000/1M * 3.00 = 0.03
        self.assertAlmostEqual(input_cost, 0.03, places=6)

        # Estimate output cost
        output_cost = provider.estimate_cost(10_000, is_input=False)
        # Expected: 10,000/1M * 15.00 = 0.15
        self.assertAlmostEqual(output_cost, 0.15, places=6)

    @patch("api.services.llm.openai_provider.OpenAI")
    def test_openai_query_includes_accurate_cost(self, mock_openai_class):
        """Test that OpenAI query() returns accurate cost estimates"""
        from api.services.llm.openai_provider import OpenAIProvider

        # Mock OpenAI response with JSON content
        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content='{"sentiment": "positive", "summary": "Test response"}'
                ),
                finish_reason="stop",
            )
        ]
        mock_response.usage = Mock(
            total_tokens=1000, prompt_tokens=600, completion_tokens=400
        )
        mock_response.model = "gpt-5-nano"
        mock_response.system_fingerprint = "test"

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        provider = OpenAIProvider(api_key="test-key", model="gpt-5-nano")
        result = provider.query("Test prompt", parse_json=True)

        # Verify content is parsed as dict
        self.assertIsInstance(result["content"], dict)
        self.assertEqual(result["content"]["sentiment"], "positive")

        # Verify cost is calculated correctly
        # 600 input * 0.05/1M + 400 output * 0.40/1M = 0.00003 + 0.00016 = 0.00019
        expected_cost = 0.00019
        self.assertAlmostEqual(
            result["metadata"]["cost_estimate"], expected_cost, places=6
        )

    @patch("httpx.Client")
    def test_perplexity_query_includes_accurate_cost(self, mock_client_class):
        """Test that Perplexity query() returns accurate cost estimates"""
        from api.services.llm.perplexity_provider import PerplexityProvider

        # Mock httpx response with JSON content
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": '{"sentiment": "positive", "summary": "Test response"}'
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "total_tokens": 1000,
                "prompt_tokens": 600,
                "completion_tokens": 400,
            },
            "citations": [],
        }

        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client_instance.__enter__ = Mock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = Mock(return_value=False)
        mock_client_class.return_value = mock_client_instance

        provider = PerplexityProvider(api_key="test-key", model="sonar")
        result = provider.query("Test prompt", parse_json=True)

        # Verify content is parsed as dict
        self.assertIsInstance(result["content"], dict)
        self.assertEqual(result["content"]["sentiment"], "positive")

        # Verify cost is calculated correctly
        # 600 input * 1.00/1M + 400 output * 1.00/1M = 0.0006 + 0.0004 = 0.001
        expected_cost = 0.001
        self.assertAlmostEqual(
            result["metadata"]["cost_estimate"], expected_cost, places=6
        )

    def test_provider_fallback_on_unknown_model(self):
        """Test that providers handle unknown models gracefully"""
        from api.services.llm.openai_provider import OpenAIProvider

        # Unknown model should still work (fallback to gpt-5-mini pricing)
        provider = OpenAIProvider(api_key="test-key", model="gpt-99-unknown")

        # Should not raise an error
        cost = provider.estimate_cost(1000, is_input=True)
        self.assertGreater(cost, 0.0)

    @patch("api.services.llm.openai_provider.OpenAI")
    def test_cost_metadata_included_in_response(self, mock_openai_class):
        """Test that cost metadata is properly included in query response"""
        from api.services.llm.openai_provider import OpenAIProvider

        # Mock OpenAI response with JSON content
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content='{"test": "response"}'), finish_reason="stop")
        ]
        mock_response.usage = Mock(
            total_tokens=500, prompt_tokens=300, completion_tokens=200
        )
        mock_response.model = "gpt-5-nano"
        mock_response.system_fingerprint = "test"

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        provider = OpenAIProvider(api_key="test-key", model="gpt-5-nano")
        result = provider.query("Test prompt", parse_json=True)

        # Verify content is parsed
        self.assertIsInstance(result["content"], dict)

        # Verify metadata structure
        metadata = result["metadata"]
        self.assertIn("cost_estimate", metadata)
        self.assertIn("tokens_used", metadata)
        self.assertIn("prompt_tokens", metadata)
        self.assertIn("completion_tokens", metadata)
        self.assertIn("model", metadata)
        self.assertIn("json_mode_enabled", metadata)
        self.assertIn("parse_success", metadata)

        # Verify token counts
        self.assertEqual(metadata["tokens_used"], 500)
        self.assertEqual(metadata["prompt_tokens"], 300)
        self.assertEqual(metadata["completion_tokens"], 200)

        # Verify cost is non-zero
        self.assertGreater(metadata["cost_estimate"], 0.0)
