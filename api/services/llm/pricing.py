"""
LLM Provider Pricing Configuration

Centralized pricing data for all LLM providers. Makes it easy to:
- Update pricing when providers change rates
- Add new models
- Test cost calculations
- Audit costs across providers

Pricing sources:
- OpenAI: https://openai.com/api/pricing/ (as of November 2025)
- Perplexity: https://docs.perplexity.ai/guides/pricing (as of November 2025)
"""

from dataclasses import dataclass
from typing import Dict
import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModelPricing:
    """Pricing for a specific model (immutable)"""
    input_cost_per_million: float  # Cost per 1M input tokens
    output_cost_per_million: float  # Cost per 1M output tokens
    model_name: str
    
    def calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Calculate total cost for a query.
        
        Args:
            prompt_tokens: Number of input/prompt tokens
            completion_tokens: Number of output/completion tokens
            
        Returns:
            Total cost in USD
        """
        input_cost = (prompt_tokens / 1_000_000) * self.input_cost_per_million
        output_cost = (completion_tokens / 1_000_000) * self.output_cost_per_million
        return input_cost + output_cost
    
    def estimate_cost(self, tokens: int, is_input: bool = False) -> float:
        """
        Estimate cost for a given number of tokens.
        
        Args:
            tokens: Number of tokens
            is_input: True for input tokens, False for output tokens
            
        Returns:
            Estimated cost in USD
        """
        if is_input:
            return (tokens / 1_000_000) * self.input_cost_per_million
        else:
            return (tokens / 1_000_000) * self.output_cost_per_million


class BasePricing:
    """Base class for provider pricing with common get_pricing logic"""
    
    MODELS: Dict[str, ModelPricing] = {}
    DEFAULT_MODEL: str = ''
    
    @classmethod
    def get_pricing(cls, model: str) -> ModelPricing:
        """
        Get pricing for a model.
        
        Args:
            model: Exact model name as used in API calls
            
        Returns:
            ModelPricing instance
        """
        if model in cls.MODELS:
            return cls.MODELS[model]
        
        # Unknown model - use fallback
        logger.warning(
            f"Unknown {cls.__name__} model '{model}', using {cls.DEFAULT_MODEL} pricing as fallback"
        )
        return cls.MODELS[cls.DEFAULT_MODEL]


class OpenAIPricing(BasePricing):
    """
    OpenAI pricing as of November 2025
    Source: https://openai.com/api/pricing/
    
    GPT-5 series models with various performance/cost tiers.
    Note: Cached input tokens available at 90% discount (not yet implemented).
    """
    
    # Pricing per 1M tokens (input/output)
    MODELS: Dict[str, ModelPricing] = {
        'gpt-5-nano': ModelPricing(
            input_cost_per_million=0.05,
            output_cost_per_million=0.40,
            model_name='gpt-5-nano'
        ),
        'gpt-5-mini': ModelPricing(
            input_cost_per_million=0.25,
            output_cost_per_million=2.00,
            model_name='gpt-5-mini'
        ),
        'gpt-5.1': ModelPricing(
            input_cost_per_million=1.25,
            output_cost_per_million=10.00,
            model_name='gpt-5.1'
        ),
        'gpt-5': ModelPricing(
            input_cost_per_million=1.25,
            output_cost_per_million=10.00,
            model_name='gpt-5'
        ),
        'gpt-5-pro': ModelPricing(
            input_cost_per_million=15.00,
            output_cost_per_million=120.00,
            model_name='gpt-5-pro'
        ),
    }
    
    # Default fallback model for unknown models
    DEFAULT_MODEL = 'gpt-5-mini'


class PerplexityPricing(BasePricing):
    """
    Perplexity AI pricing as of November 2025
    Source: https://docs.perplexity.ai/guides/pricing
    
    Sonar series models with web search capabilities.
    Note: Some models have additional costs for search queries and reasoning tokens.
    """
    
    # Pricing per 1M tokens (input/output)
    MODELS: Dict[str, ModelPricing] = {
        'sonar': ModelPricing(
            input_cost_per_million=1.00,
            output_cost_per_million=1.00,
            model_name='sonar'
        ),
        'sonar-pro': ModelPricing(
            input_cost_per_million=3.00,
            output_cost_per_million=15.00,
            model_name='sonar-pro'
        ),
        'sonar-reasoning': ModelPricing(
            input_cost_per_million=1.00,
            output_cost_per_million=5.00,
            model_name='sonar-reasoning'
        ),
        'sonar-reasoning-pro': ModelPricing(
            input_cost_per_million=2.00,
            output_cost_per_million=8.00,
            model_name='sonar-reasoning-pro'
        ),
        'sonar-deep-research': ModelPricing(
            input_cost_per_million=2.00,
            output_cost_per_million=8.00,
            model_name='sonar-deep-research'
        ),
    }
    
    # Default fallback model for unknown models
    DEFAULT_MODEL = 'sonar'


