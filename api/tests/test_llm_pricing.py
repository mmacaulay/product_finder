"""
Tests for LLM pricing calculations.
"""

from django.test import TestCase
from api.services.llm.pricing import (
    ModelPricing,
    OpenAIPricing,
    PerplexityPricing,
)


class ModelPricingTestCase(TestCase):
    """Test the ModelPricing dataclass"""

    def test_calculate_cost(self):
        """Test cost calculation with known values"""
        pricing = ModelPricing(
            input_cost_per_million=1.25,
            output_cost_per_million=10.00,
            model_name="test-model",
        )

        # 1000 input tokens, 500 output tokens
        cost = pricing.calculate_cost(1000, 500)

        # Expected: (1000/1M * 1.25) + (500/1M * 10.00)
        # = 0.00125 + 0.005 = 0.00625
        self.assertAlmostEqual(cost, 0.00625, places=6)

    def test_calculate_cost_zero_tokens(self):
        """Test cost calculation with zero tokens"""
        pricing = ModelPricing(
            input_cost_per_million=1.25,
            output_cost_per_million=10.00,
            model_name="test-model",
        )

        cost = pricing.calculate_cost(0, 0)
        self.assertEqual(cost, 0.0)

    def test_calculate_cost_large_tokens(self):
        """Test cost calculation with large token counts"""
        pricing = ModelPricing(
            input_cost_per_million=1.25,
            output_cost_per_million=10.00,
            model_name="test-model",
        )

        # 1 million input tokens, 500k output tokens
        cost = pricing.calculate_cost(1_000_000, 500_000)

        # Expected: (1M/1M * 1.25) + (500K/1M * 10.00)
        # = 1.25 + 5.00 = 6.25
        self.assertAlmostEqual(cost, 6.25, places=2)

    def test_estimate_input_cost(self):
        """Test input token cost estimation"""
        pricing = ModelPricing(
            input_cost_per_million=1.25,
            output_cost_per_million=10.00,
            model_name="test-model",
        )

        cost = pricing.estimate_cost(1000, is_input=True)
        # Expected: 1000/1M * 1.25 = 0.00125
        self.assertAlmostEqual(cost, 0.00125, places=6)

    def test_estimate_output_cost(self):
        """Test output token cost estimation"""
        pricing = ModelPricing(
            input_cost_per_million=1.25,
            output_cost_per_million=10.00,
            model_name="test-model",
        )

        cost = pricing.estimate_cost(500, is_input=False)
        # Expected: 500/1M * 10.00 = 0.005
        self.assertAlmostEqual(cost, 0.005, places=6)


class OpenAIPricingTestCase(TestCase):
    """Test OpenAI pricing configuration"""

    def test_gpt5_nano_pricing(self):
        """Test GPT-5 Nano pricing lookup"""
        pricing = OpenAIPricing.get_pricing("gpt-5-nano")
        self.assertEqual(pricing.input_cost_per_million, 0.05)
        self.assertEqual(pricing.output_cost_per_million, 0.40)
        self.assertEqual(pricing.model_name, "gpt-5-nano")

    def test_gpt5_mini_pricing(self):
        """Test GPT-5 Mini pricing lookup"""
        pricing = OpenAIPricing.get_pricing("gpt-5-mini")
        self.assertEqual(pricing.input_cost_per_million, 0.25)
        self.assertEqual(pricing.output_cost_per_million, 2.00)
        self.assertEqual(pricing.model_name, "gpt-5-mini")

    def test_gpt5_pricing(self):
        """Test GPT-5 pricing lookup"""
        pricing = OpenAIPricing.get_pricing("gpt-5")
        self.assertEqual(pricing.input_cost_per_million, 1.25)
        self.assertEqual(pricing.output_cost_per_million, 10.00)
        self.assertEqual(pricing.model_name, "gpt-5")

    def test_gpt5_1_pricing(self):
        """Test GPT-5.1 pricing lookup"""
        pricing = OpenAIPricing.get_pricing("gpt-5.1")
        self.assertEqual(pricing.input_cost_per_million, 1.25)
        self.assertEqual(pricing.output_cost_per_million, 10.00)
        self.assertEqual(pricing.model_name, "gpt-5.1")

    def test_gpt5_pro_pricing(self):
        """Test GPT-5 Pro pricing"""
        pricing = OpenAIPricing.get_pricing("gpt-5-pro")
        self.assertEqual(pricing.input_cost_per_million, 15.00)
        self.assertEqual(pricing.output_cost_per_million, 120.00)
        self.assertEqual(pricing.model_name, "gpt-5-pro")

    def test_exact_model_lookup(self):
        """Test exact model name lookup"""
        pricing = OpenAIPricing.get_pricing("gpt-5-mini")
        self.assertEqual(pricing.model_name, "gpt-5-mini")
        self.assertEqual(pricing.input_cost_per_million, 0.25)

    def test_unknown_model_fallback(self):
        """Test fallback for unknown models"""
        pricing = OpenAIPricing.get_pricing("gpt-99-ultra")
        # Should fallback to gpt-5-mini pricing
        self.assertEqual(pricing.model_name, "gpt-5-mini")
        self.assertEqual(pricing.input_cost_per_million, 0.25)

    def test_cost_calculation_gpt5_nano(self):
        """Test actual cost calculation for GPT-5 Nano"""
        pricing = OpenAIPricing.get_pricing("gpt-5-nano")

        # Example: 10,000 input tokens, 2,000 output tokens
        cost = pricing.calculate_cost(10_000, 2_000)

        # Expected: (10K/1M * 0.05) + (2K/1M * 0.40)
        # = 0.0005 + 0.0008 = 0.0013
        self.assertAlmostEqual(cost, 0.0013, places=6)

    def test_cost_calculation_gpt5_mini(self):
        """Test actual cost calculation for GPT-5 Mini"""
        pricing = OpenAIPricing.get_pricing("gpt-5-mini")

        # Example: 10,000 input tokens, 2,000 output tokens
        cost = pricing.calculate_cost(10_000, 2_000)

        # Expected: (10K/1M * 0.25) + (2K/1M * 2.00)
        # = 0.0025 + 0.004 = 0.0065
        self.assertAlmostEqual(cost, 0.0065, places=6)

    def test_cost_calculation_gpt5(self):
        """Test actual cost calculation for GPT-5"""
        pricing = OpenAIPricing.get_pricing("gpt-5")

        # Example: 10,000 input tokens, 2,000 output tokens
        cost = pricing.calculate_cost(10_000, 2_000)

        # Expected: (10K/1M * 1.25) + (2K/1M * 10.00)
        # = 0.0125 + 0.02 = 0.0325
        self.assertAlmostEqual(cost, 0.0325, places=6)


class PerplexityPricingTestCase(TestCase):
    """Test Perplexity pricing configuration"""

    def test_sonar_pricing(self):
        """Test Sonar pricing"""
        pricing = PerplexityPricing.get_pricing("sonar")
        self.assertEqual(pricing.input_cost_per_million, 1.00)
        self.assertEqual(pricing.output_cost_per_million, 1.00)
        self.assertEqual(pricing.model_name, "sonar")

    def test_sonar_pro_pricing(self):
        """Test Sonar Pro pricing"""
        pricing = PerplexityPricing.get_pricing("sonar-pro")
        self.assertEqual(pricing.input_cost_per_million, 3.00)
        self.assertEqual(pricing.output_cost_per_million, 15.00)
        self.assertEqual(pricing.model_name, "sonar-pro")

    def test_sonar_reasoning_pricing(self):
        """Test Sonar Reasoning pricing"""
        pricing = PerplexityPricing.get_pricing("sonar-reasoning")
        self.assertEqual(pricing.input_cost_per_million, 1.00)
        self.assertEqual(pricing.output_cost_per_million, 5.00)
        self.assertEqual(pricing.model_name, "sonar-reasoning")

    def test_sonar_reasoning_pro_pricing(self):
        """Test Sonar Reasoning Pro pricing"""
        pricing = PerplexityPricing.get_pricing("sonar-reasoning-pro")
        self.assertEqual(pricing.input_cost_per_million, 2.00)
        self.assertEqual(pricing.output_cost_per_million, 8.00)
        self.assertEqual(pricing.model_name, "sonar-reasoning-pro")

    def test_sonar_deep_research_pricing(self):
        """Test Sonar Deep Research pricing"""
        pricing = PerplexityPricing.get_pricing("sonar-deep-research")
        self.assertEqual(pricing.input_cost_per_million, 2.00)
        self.assertEqual(pricing.output_cost_per_million, 8.00)
        self.assertEqual(pricing.model_name, "sonar-deep-research")

    def test_exact_model_lookup(self):
        """Test exact model name matching"""
        pricing = PerplexityPricing.get_pricing("sonar-pro")
        self.assertEqual(pricing.model_name, "sonar-pro")
        self.assertEqual(pricing.input_cost_per_million, 3.00)

    def test_unknown_model_fallback(self):
        """Test fallback for unknown models"""
        pricing = PerplexityPricing.get_pricing("unknown-model")
        # Should fallback to sonar
        self.assertEqual(pricing.model_name, "sonar")
        self.assertEqual(pricing.input_cost_per_million, 1.00)

    def test_cost_calculation_sonar(self):
        """Test cost calculation for Sonar"""
        pricing = PerplexityPricing.get_pricing("sonar")

        # Example: 5,000 input tokens, 1,000 output tokens
        cost = pricing.calculate_cost(5_000, 1_000)

        # Expected: (5K/1M * 1.00) + (1K/1M * 1.00)
        # = 0.005 + 0.001 = 0.006
        self.assertAlmostEqual(cost, 0.006, places=6)

    def test_cost_calculation_sonar_pro(self):
        """Test cost calculation for Sonar Pro"""
        pricing = PerplexityPricing.get_pricing("sonar-pro")

        # Example: 5,000 input tokens, 1,000 output tokens
        cost = pricing.calculate_cost(5_000, 1_000)

        # Expected: (5K/1M * 3.00) + (1K/1M * 15.00)
        # = 0.015 + 0.015 = 0.030
        self.assertAlmostEqual(cost, 0.030, places=6)


class CostComparisonTestCase(TestCase):
    """Test cost comparisons between providers and models"""

    def test_gpt5_nano_vs_gpt5_mini(self):
        """Compare costs between GPT-5 Nano and GPT-5 Mini"""
        gpt5_nano = OpenAIPricing.get_pricing("gpt-5-nano")
        gpt5_mini = OpenAIPricing.get_pricing("gpt-5-mini")

        # Same token usage
        tokens_in, tokens_out = 10_000, 2_000

        cost_nano = gpt5_nano.calculate_cost(tokens_in, tokens_out)
        cost_mini = gpt5_mini.calculate_cost(tokens_in, tokens_out)

        # GPT-5 Nano should be significantly cheaper
        self.assertGreater(cost_mini, cost_nano)

        # Calculate savings percentage
        savings = ((cost_mini - cost_nano) / cost_mini) * 100
        self.assertGreater(savings, 75)  # Should be >75% cheaper

    def test_gpt5_vs_gpt5_pro(self):
        """Compare costs between GPT-5 and GPT-5 Pro"""
        gpt5 = OpenAIPricing.get_pricing("gpt-5")
        gpt5_pro = OpenAIPricing.get_pricing("gpt-5-pro")

        # Same token usage
        tokens_in, tokens_out = 10_000, 2_000

        cost_gpt5 = gpt5.calculate_cost(tokens_in, tokens_out)
        cost_pro = gpt5_pro.calculate_cost(tokens_in, tokens_out)

        # GPT-5 Pro should be much more expensive
        self.assertGreater(cost_pro, cost_gpt5)

    def test_openai_vs_perplexity_budget_models(self):
        """Compare costs between budget models"""
        gpt5_nano = OpenAIPricing.get_pricing("gpt-5-nano")
        sonar = PerplexityPricing.get_pricing("sonar")

        # Same token usage
        tokens_in, tokens_out = 10_000, 2_000

        cost_openai = gpt5_nano.calculate_cost(tokens_in, tokens_out)
        cost_perplexity = sonar.calculate_cost(tokens_in, tokens_out)

        # Both should be very cost-effective
        self.assertLess(cost_openai, 0.01)
        self.assertLess(cost_perplexity, 0.02)  # Sonar is slightly more expensive

    def test_perplexity_model_tiers(self):
        """Compare costs across Perplexity model tiers"""
        sonar = PerplexityPricing.get_pricing("sonar")
        sonar_pro = PerplexityPricing.get_pricing("sonar-pro")

        tokens_in, tokens_out = 10_000, 2_000

        cost_sonar = sonar.calculate_cost(tokens_in, tokens_out)
        cost_sonar_pro = sonar_pro.calculate_cost(tokens_in, tokens_out)

        # Verify ordering: sonar < sonar_pro
        self.assertLess(cost_sonar, cost_sonar_pro)


class RealisticUsageTestCase(TestCase):
    """Test with realistic usage patterns"""

    def test_review_summary_cost_gpt5_nano(self):
        """Test realistic cost for a review summary with GPT-5 Nano"""
        pricing = OpenAIPricing.get_pricing("gpt-5-nano")

        # Realistic review summary: 200 token prompt, 400 token response
        cost = pricing.calculate_cost(200, 400)

        # Should be extremely cheap (< $0.0002)
        self.assertLess(cost, 0.0002)

        # For 1000 queries per month
        monthly_cost = cost * 1000
        self.assertLess(monthly_cost, 0.20)  # Less than $0.20/month

    def test_review_summary_cost_perplexity(self):
        """Test realistic cost for a review summary with Perplexity Sonar"""
        pricing = PerplexityPricing.get_pricing("sonar")

        # Realistic review summary: 200 token prompt, 400 token response
        cost = pricing.calculate_cost(200, 400)

        # Should be cheap (< $0.001)
        self.assertLess(cost, 0.001)

        # For 1000 queries per month
        monthly_cost = cost * 1000
        self.assertLess(monthly_cost, 1.00)  # Less than $1/month

    def test_monthly_budget_scenarios(self):
        """Test various monthly budget scenarios"""
        gpt5_nano = OpenAIPricing.get_pricing("gpt-5-nano")
        sonar = PerplexityPricing.get_pricing("sonar")

        # Typical query: 300 input, 400 output
        typical_in, typical_out = 300, 400

        cost_per_query_openai = gpt5_nano.calculate_cost(typical_in, typical_out)
        cost_per_query_perplexity = sonar.calculate_cost(typical_in, typical_out)

        budget = 10.00  # $10/month budget

        # How many queries can we afford?
        queries_openai = int(budget / cost_per_query_openai)
        queries_perplexity = int(budget / cost_per_query_perplexity)

        # Both should allow many thousands of queries
        self.assertGreater(queries_openai, 10000)
        self.assertGreater(queries_perplexity, 1000)

    def test_with_caching_cost_reduction(self):
        """Test cost reduction with caching"""
        pricing = OpenAIPricing.get_pricing("gpt-5-nano")

        # Typical query cost
        cost_per_query = pricing.calculate_cost(300, 400)

        # 1000 queries per month with different cache hit rates
        monthly_queries = 1000

        # No caching
        cost_no_cache = cost_per_query * monthly_queries

        # 50% cache hit rate
        cost_50_cache = cost_per_query * (monthly_queries * 0.5)

        # 80% cache hit rate
        cost_80_cache = cost_per_query * (monthly_queries * 0.2)

        # Verify cost reduction
        self.assertAlmostEqual(cost_50_cache, cost_no_cache * 0.5, places=6)
        self.assertAlmostEqual(cost_80_cache, cost_no_cache * 0.2, places=6)

        # 80% caching should save 80% of costs
        savings = cost_no_cache - cost_80_cache
        savings_pct = (savings / cost_no_cache) * 100
        self.assertAlmostEqual(savings_pct, 80.0, places=1)

    def test_large_product_catalog_costs(self):
        """Test costs for a large product catalog"""
        gpt5_nano = OpenAIPricing.get_pricing("gpt-5-nano")

        # Assumptions:
        # - 10,000 products
        # - Each product queried once per month
        # - 300 input, 400 output tokens per query
        # - 80% cache hit rate (only 20% hit API)

        products = 10_000
        cache_hit_rate = 0.80
        api_queries = int(products * (1 - cache_hit_rate))

        cost_per_query = gpt5_nano.calculate_cost(300, 400)
        monthly_cost = cost_per_query * api_queries

        # Should be very reasonable even for large catalog
        self.assertLess(monthly_cost, 1.00)  # Less than $1/month with GPT-5 Nano!


class EdgeCaseTestCase(TestCase):
    """Test edge cases and error conditions"""

    def test_zero_cost_models(self):
        """Test models with zero cost (hypothetical)"""
        pricing = ModelPricing(
            input_cost_per_million=0.0,
            output_cost_per_million=0.0,
            model_name="free-model",
        )

        cost = pricing.calculate_cost(1000, 1000)
        self.assertEqual(cost, 0.0)

    def test_very_expensive_model(self):
        """Test with hypothetical expensive model"""
        pricing = ModelPricing(
            input_cost_per_million=1000.0,
            output_cost_per_million=2000.0,
            model_name="expensive-model",
        )

        # 1 million tokens each
        cost = pricing.calculate_cost(1_000_000, 1_000_000)

        # Should be $3000
        self.assertEqual(cost, 3000.0)

    def test_fractional_tokens(self):
        """Test that fractional costs work correctly"""
        pricing = OpenAIPricing.get_pricing("gpt-5-nano")

        # Just 1 token
        cost = pricing.calculate_cost(1, 1)

        # Should be very small but non-zero
        self.assertGreater(cost, 0.0)
        self.assertLess(cost, 0.000001)
