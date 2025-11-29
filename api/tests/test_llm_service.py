"""
Tests for LLM service functionality.
"""

from unittest.mock import Mock, patch, MagicMock
from api.tests.base import FirestoreTestCase
from api.services.llm import LLMService


class LLMServiceTestCase(FirestoreTestCase):
    """Test the LLMService orchestrator"""

    def setUp(self):
        """Set up test fixtures"""
        super().setUp()

        # Create test product data (as dict, not ORM object)
        self.product = {
            "id": "123456789012",
            "upc_code": "123456789012",
            "name": "Test Product",
            "brand": "Test Brand",
            "image_url": None,
            "created_at": None,
            "updated_at": None,
        }

        # Create test prompt data (as dict, not ORM object)
        self.prompt = {
            "id": "test_prompt",
            "name": "test_prompt",
            "query_type": "review_summary",
            "prompt_template": "Summarize reviews for {name} by {brand}",
            "schema_version": "1.0",
            "is_active": True,
            "description": "Test prompt",
            "response_schema": None,
            "created_at": None,
            "updated_at": None,
        }

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

        # Setup Firestore mocks for prompts
        mock_prompt_doc = MagicMock()
        mock_prompt_doc.exists = True
        mock_prompt_doc.to_dict.return_value = self.prompt
        mock_prompt_doc.id = "test_prompt"

        # Configure mock to return prompt when querying
        def mock_stream_prompts():
            return [mock_prompt_doc]

        self.mock_firestore.collection.return_value.where.return_value.where.return_value.stream.return_value = (
            mock_stream_prompts()
        )

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

        # Verify result was cached in Firestore
        self.mock_firestore.collection.return_value.document.return_value.set.assert_called_once()
        call_args = (
            self.mock_firestore.collection.return_value.document.return_value.set.call_args
        )
        cached_data = call_args[0][0]

        self.assertIsInstance(cached_data["result"], dict)
        self.assertEqual(cached_data["result"]["sentiment"], "positive")
        self.assertFalse(cached_data["is_stale"])

    @patch("api.services.llm.llm_service.PerplexityProvider")
    def test_get_product_insight_cache_hit(self, mock_provider_class):
        """Test getting insight when result is cached (cache hit)"""
        from django.utils import timezone

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
        cached_doc_data = {
            "id": "123456789012_test_prompt_perplexity",
            "product_upc": "123456789012",
            "prompt_name": "test_prompt",
            "provider": "perplexity",
            "query_input": "Test query",
            "result": cached_result,
            "metadata": {},
            "is_stale": False,
            "created_at": timezone.now(),
            "updated_at": timezone.now(),
        }

        # Mock Firestore to return cached result
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = cached_doc_data
        mock_doc.id = cached_doc_data["id"]

        self.mock_firestore.collection.return_value.document.return_value.get.return_value = (
            mock_doc
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
        from django.utils import timezone

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
        cached_doc_data = {
            "id": "123456789012_test_prompt_perplexity",
            "product_upc": "123456789012",
            "prompt_name": "test_prompt",
            "provider": "perplexity",
            "query_input": "Test query",
            "result": cached_result,
            "metadata": {},
            "is_stale": False,
            "created_at": timezone.now(),
            "updated_at": timezone.now(),
        }

        # Mock Firestore to return cached result
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = cached_doc_data
        mock_doc.id = cached_doc_data["id"]

        self.mock_firestore.collection.return_value.document.return_value.get.return_value = (
            mock_doc
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
        from django.utils import timezone

        # Mock cached results with structured data
        result1_data = {
            "id": "123456789012_test_prompt_perplexity",
            "product_upc": "123456789012",
            "prompt_name": "test_prompt",
            "provider": "perplexity",
            "query_input": "Test query",
            "result": {"summary": "Result 1"},
            "metadata": {},
            "is_stale": False,
            "created_at": timezone.now(),
            "updated_at": timezone.now(),
        }
        result2_data = {
            "id": "123456789012_test_prompt_openai",
            "product_upc": "123456789012",
            "prompt_name": "test_prompt",
            "provider": "openai",
            "query_input": "Test query",
            "result": {"summary": "Result 2"},
            "metadata": {},
            "is_stale": False,
            "created_at": timezone.now(),
            "updated_at": timezone.now(),
        }

        # Mock Firestore query to return result with perplexity provider
        mock_doc1 = MagicMock()
        mock_doc1.to_dict.return_value = result1_data
        mock_doc1.id = result1_data["id"]
        mock_doc1.reference = MagicMock()

        # Mock the query chain for get_by_product (single where)
        self.mock_firestore.collection.return_value.where.return_value.stream.return_value = [
            mock_doc1
        ]

        # Mock the document.get() for mark_stale check
        mock_doc_exists = MagicMock()
        mock_doc_exists.exists = True
        self.mock_firestore.collection.return_value.document.return_value.get.return_value = (
            mock_doc_exists
        )

        # Invalidate cache for perplexity only
        service = LLMService()
        count = service.invalidate_cache(product=self.product, provider="perplexity")

        self.assertEqual(count, 1)

        # Verify Firestore update was called to mark as stale
        # Note: mark_stale calls collection.document(doc_id).update()
        update_calls = (
            self.mock_firestore.collection.return_value.document.return_value.update.call_args_list
        )
        self.assertEqual(len(update_calls), 1)
        # Check that is_stale was set to True
        self.assertIn("is_stale", update_calls[0][0][0])
        self.assertTrue(update_calls[0][0][0]["is_stale"])

    def test_prompt_rendering(self):
        """Test prompt template rendering with product data"""
        service = LLMService()
        rendered = service._render_prompt(self.prompt, self.product)

        expected = "Summarize reviews for Test Product by Test Brand"
        self.assertEqual(rendered, expected)

    def test_missing_prompt(self):
        """Test error when no active prompt exists"""
        # Mock Firestore to return no prompts for this query_type
        self.mock_firestore.collection.return_value.where.return_value.where.return_value.stream.return_value = (
            []
        )

        service = LLMService()

        with self.assertRaises(ValueError):
            service.get_product_insight(
                product=self.product, query_type="nonexistent_query_type"
            )

    def test_get_cache_stats(self):
        """Test cache statistics"""
        from django.utils import timezone

        # Mock cached results
        result1 = {
            "id": "123456789012_test_prompt_perplexity",
            "product_upc": "123456789012",
            "prompt_name": "test_prompt",
            "provider": "perplexity",
            "query_input": "Test",
            "result": {"summary": "Result 1"},
            "is_stale": False,
            "metadata": {},
            "created_at": timezone.now(),
        }
        result2 = {
            "id": "123456789012_test_prompt_openai",
            "product_upc": "123456789012",
            "prompt_name": "test_prompt",
            "provider": "openai",
            "query_input": "Test",
            "result": {"summary": "Result 2"},
            "is_stale": True,
            "metadata": {},
            "created_at": timezone.now(),
        }

        # Mock Firestore query to return these results
        mock_doc1 = MagicMock()
        mock_doc1.to_dict.return_value = result1
        mock_doc1.id = result1["id"]

        mock_doc2 = MagicMock()
        mock_doc2.to_dict.return_value = result2
        mock_doc2.id = result2["id"]

        self.mock_firestore.collection.return_value.where.return_value.stream.return_value = [
            mock_doc1,
            mock_doc2,
        ]

        service = LLMService()
        stats = service.get_cache_stats(product=self.product)

        self.assertEqual(stats["total_cached"], 2)
        self.assertEqual(stats["fresh"], 1)
        self.assertEqual(stats["stale"], 1)
        self.assertTrue(stats["cache_enabled"])


