# LLM Integration Implementation Plan

## Overview
Add LLM-based product information lookup functionality with support for multiple providers (OpenAI ChatGPT, Perplexity), starting with user review summaries from the internet. The system will include prompt management, result caching, and a common interface across providers.

---

## Architecture

### 1. Database Models

#### 1.1 LLMPrompt Model
Stores reusable prompts for different query types.

```python
class LLMPrompt(models.Model):
    """Template for LLM queries"""
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    prompt_template = models.TextField()
    query_type = models.CharField(max_length=50)  # e.g., 'review_summary', 'product_comparison'
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Template Variables:**
- `{product_name}` - Product name
- `{brand}` - Product brand
- `{upc_code}` - UPC code
- `{additional_data}` - Any extra product data from DE API

**Example Prompt:**
```
Summarize user reviews for the product "{product_name}" by {brand} (UPC: {upc_code}).
Include: overall sentiment, common praise, common complaints, and key themes.
Limit response to 200 words.
```

#### 1.2 LLMQueryResult Model
Caches LLM responses to reduce API calls and costs.

```python
class LLMQueryResult(models.Model):
    """Cached results from LLM queries"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='llm_results')
    prompt = models.ForeignKey(LLMPrompt, on_delete=models.CASCADE)
    provider = models.CharField(max_length=50)  # 'openai', 'perplexity'
    query_input = models.TextField()  # The actual prompt sent
    result = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)  # tokens used, model version, etc.
    is_stale = models.BooleanField(default=False)  # Mark for refresh
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['product', 'prompt', 'provider']),
            models.Index(fields=['created_at']),
        ]
        unique_together = ['product', 'prompt', 'provider']
```

---

### 2. Service Layer Architecture

#### 2.1 Base LLM Provider Interface

```
api/services/llm/
├── __init__.py
├── base_provider.py        # Abstract base class
├── openai_provider.py      # ChatGPT implementation
├── perplexity_provider.py  # Perplexity implementation
├── llm_service.py          # Orchestrator with caching logic
└── exceptions.py           # Custom exceptions
```

#### 2.2 Base Provider Class

```python
# base_provider.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        self.config = kwargs
    
    @abstractmethod
    def query(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Send a query to the LLM provider
        
        Args:
            prompt: The prompt text
            **kwargs: Provider-specific parameters
            
        Returns:
            {
                'content': str,  # The LLM response
                'metadata': {
                    'model': str,
                    'tokens_used': int,
                    'cost_estimate': float,
                    'provider_specific': dict
                }
            }
        """
        pass
    
    @abstractmethod
    def validate_credentials(self) -> bool:
        """Verify API credentials are valid"""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider identifier"""
        pass
```

#### 2.3 Provider Implementations

**OpenAI Provider:**
- Uses `openai` Python SDK
- Supports GPT-4, GPT-3.5-turbo
- Configuration: model, temperature, max_tokens

**Perplexity Provider:**
- Uses Perplexity API (similar to OpenAI API format)
- Supports Perplexity models with web search
- Configuration: model, temperature, max_tokens, search_depth

#### 2.4 LLM Service Orchestrator

```python
# llm_service.py
class LLMService:
    """
    Main service for LLM operations with caching and provider management
    """
    
    def __init__(self, default_provider: str = 'openai'):
        self.default_provider = default_provider
        self._providers = {}
        self._initialize_providers()
    
    def get_product_insight(
        self,
        product: Product,
        query_type: str,
        provider: Optional[str] = None,
        force_refresh: bool = False
    ) -> str:
        """
        Get LLM-generated insight for a product
        
        Args:
            product: Product instance
            query_type: Type of query (e.g., 'review_summary')
            provider: LLM provider to use (defaults to self.default_provider)
            force_refresh: Skip cache and query LLM directly
            
        Returns:
            The LLM-generated content
        """
        # 1. Get appropriate prompt template
        # 2. Check cache (unless force_refresh)
        # 3. If not cached, query LLM
        # 4. Store result in cache
        # 5. Return content
        pass
    
    def invalidate_cache(self, product: Product, query_type: Optional[str] = None):
        """Mark cached results as stale"""
        pass
    
    def _get_provider(self, provider_name: str) -> BaseLLMProvider:
        """Get or create provider instance"""
        pass
    
    def _render_prompt(self, template: str, product: Product) -> str:
        """Render prompt template with product data"""
        pass
```

---

### 3. GraphQL Integration

#### 3.1 Extended ProductType

```python
# api/graphql/types.py
import graphene
from graphene_django import DjangoObjectType
from api.models import Product

class LLMInsightType(graphene.ObjectType):
    """LLM-generated insight"""
    content = graphene.String()
    provider = graphene.String()
    cached = graphene.Boolean()
    generated_at = graphene.DateTime()

class ProductType(DjangoObjectType):
    review_summary = graphene.Field(
        LLMInsightType,
        provider=graphene.String(),
        force_refresh=graphene.Boolean()
    )
    
    class Meta:
        model = Product
        fields = (
            'id',
            'upc_code',
            'name',
            'brand',
            'created_at',
            'updated_at',
        )
    
    def resolve_review_summary(self, info, provider=None, force_refresh=False):
        from api.services.llm.llm_service import LLMService
        
        llm_service = LLMService()
        content = llm_service.get_product_insight(
            product=self,
            query_type='review_summary',
            provider=provider,
            force_refresh=force_refresh
        )
        
        # Return with metadata
        cached_result = self.llm_results.filter(
            prompt__query_type='review_summary'
        ).first()
        
        return LLMInsightType(
            content=content,
            provider=cached_result.provider if cached_result else provider,
            cached=not force_refresh and cached_result is not None,
            generated_at=cached_result.created_at if cached_result else None
        )
```

#### 3.2 New Queries

```python
# api/graphql/schema.py
class Query(graphene.ObjectType):
    # ... existing queries ...
    
    product_with_insights = graphene.Field(
        ProductType,
        upc=graphene.String(),
        include_review_summary=graphene.Boolean(),
        llm_provider=graphene.String()
    )
    
    def resolve_product_with_insights(
        self,
        info,
        upc,
        include_review_summary=True,
        llm_provider=None
    ):
        # Fetch product (from DB or DE API)
        # Pre-fetch LLM insights if requested
        # Return product with insights attached
        pass
```

---

### 4. Configuration & Environment Variables

#### 4.1 New Environment Variables

```bash
# LLM Provider Configuration
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_MAX_TOKENS=500
OPENAI_TEMPERATURE=0.7

PERPLEXITY_API_KEY=pplx-...
PERPLEXITY_MODEL=pplx-70b-online
PERPLEXITY_MAX_TOKENS=500

# LLM Service Configuration
DEFAULT_LLM_PROVIDER=openai
LLM_CACHE_TTL_DAYS=30  # How long before cache is considered stale
LLM_ENABLE_CACHING=true
```

#### 4.2 Settings Updates

```python
# product_finder/settings.py

# LLM Configuration
LLM_CONFIG = {
    'default_provider': env('DEFAULT_LLM_PROVIDER', default='openai'),
    'cache_ttl_days': env.int('LLM_CACHE_TTL_DAYS', default=30),
    'enable_caching': env.bool('LLM_ENABLE_CACHING', default=True),
    'providers': {
        'openai': {
            'api_key': env('OPENAI_API_KEY', default=''),
            'model': env('OPENAI_MODEL', default='gpt-4-turbo-preview'),
            'max_tokens': env.int('OPENAI_MAX_TOKENS', default=500),
            'temperature': env.float('OPENAI_TEMPERATURE', default=0.7),
        },
        'perplexity': {
            'api_key': env('PERPLEXITY_API_KEY', default=''),
            'model': env('PERPLEXITY_MODEL', default='pplx-70b-online'),
            'max_tokens': env.int('PERPLEXITY_MAX_TOKENS', default=500),
            'temperature': env.float('PERPLEXITY_TEMPERATURE', default=0.7),
        }
    }
}
```

---

### 5. Testing Strategy

#### 5.1 Test Structure

```
api/tests/
├── test_llm_providers.py     # Unit tests for each provider
├── test_llm_service.py        # Integration tests for service
├── test_llm_graphql.py        # GraphQL query tests
└── fixtures/
    └── llm_responses.json     # Mock LLM responses
```

#### 5.2 Test Coverage

1. **Provider Tests:**
   - Mock API responses
   - Test error handling (rate limits, invalid keys, etc.)
   - Validate response format

2. **Service Tests:**
   - Cache hit/miss scenarios
   - Prompt rendering with product data
   - Provider fallback logic
   - Force refresh functionality

3. **GraphQL Tests:**
   - Query products with LLM insights
   - Test optional parameters
   - Cache indicators in responses

---

### 6. Migration Path

#### 6.1 Phase 1: Foundation (Week 1)
1. Create database models (LLMPrompt, LLMQueryResult)
2. Run migrations
3. Create base provider interface
4. Implement OpenAI provider
5. Add basic unit tests

#### 6.2 Phase 2: Service Layer (Week 2)
1. Implement LLMService orchestrator
2. Add caching logic
3. Create prompt rendering system
4. Add Perplexity provider
5. Add integration tests

#### 6.3 Phase 3: GraphQL Integration (Week 3)
1. Extend ProductType with LLM fields
2. Add new queries
3. Add GraphQL tests
4. Create initial prompt templates in database

#### 6.4 Phase 4: Production Readiness (Week 4)
1. Add monitoring/logging
2. Implement rate limiting
3. Add cost tracking
4. Performance optimization
5. Documentation

---

### 7. Future Enhancements

#### 7.1 Additional Query Types
- **Product Comparison:** Compare similar products
- **Ingredient Analysis:** Health/safety analysis
- **Usage Suggestions:** Creative ways to use product
- **Price History:** Track price trends with commentary

#### 7.2 Advanced Features
- **Multi-provider Consensus:** Query multiple LLMs and aggregate responses
- **Streaming Responses:** Real-time streaming for long-form content
- **User Feedback:** Thumbs up/down on LLM responses
- **A/B Testing:** Test different prompts and providers
- **Cost Dashboard:** Monitor LLM API costs per product/query type

#### 7.3 Performance Optimizations
- **Background Processing:** Queue LLM queries for async processing
- **Batch Queries:** Process multiple products in one request
- **Smart Caching:** Invalidate cache based on product updates
- **CDN Integration:** Cache responses at edge for faster access

---

### 8. Security & Best Practices

#### 8.1 API Key Management
- Store API keys in environment variables only
- Never commit keys to version control
- Use different keys for dev/staging/prod
- Implement key rotation strategy

#### 8.2 Rate Limiting
- Implement per-user rate limits for LLM queries
- Add backoff/retry logic for provider rate limits
- Monitor usage to prevent cost overruns

#### 8.3 Input Validation
- Sanitize product data before sending to LLMs
- Validate prompt templates before execution
- Limit prompt length to prevent injection attacks

#### 8.4 Cost Controls
- Set monthly budget alerts
- Implement circuit breakers for runaway costs
- Log all queries with cost estimates
- Dashboard for cost monitoring

---

### 9. Example Usage

#### 9.1 GraphQL Query Example

```graphql
query GetProductWithReviews {
  productByUpc(upc: "012345678901") {
    id
    name
    brand
    reviewSummary {
      content
      provider
      cached
      generatedAt
    }
  }
}
```

#### 9.2 Response Example

```json
{
  "data": {
    "productByUpc": {
      "id": 1,
      "name": "Organic Coffee Beans",
      "brand": "Great Coffee Co",
      "reviewSummary": {
        "content": "Overall, users love these organic coffee beans for their rich, bold flavor and smooth finish. Common praise includes excellent aroma, consistent quality, and good value. Some complaints mention the beans being too oily for certain grinders and occasional inconsistency in roast level. Key themes: great for espresso, eco-friendly packaging, and strong customer loyalty.",
        "provider": "openai",
        "cached": true,
        "generatedAt": "2025-11-12T10:30:00Z"
      }
    }
  }
}
```

---

## Dependencies to Add

```toml
# pyproject.toml additions
[project]
dependencies = [
    # ... existing dependencies ...
    "openai>=1.0.0",
    "httpx>=0.25.0",  # For Perplexity API calls
]
```

---

## Estimated Timeline

- **Phase 1 (Foundation):** 5-7 days
- **Phase 2 (Service Layer):** 5-7 days
- **Phase 3 (GraphQL Integration):** 3-5 days
- **Phase 4 (Production Readiness):** 5-7 days

**Total:** 3-4 weeks for full implementation

---

## Next Steps

1. Review and approve this plan
2. Set up API keys for OpenAI and Perplexity
3. Start with Phase 1: Create database models
4. Implement providers one at a time
5. Iterate and refine based on testing

---

## Questions to Consider

1. **Budget:** What's the monthly budget for LLM API calls?
2. **Refresh Strategy:** How often should cached results be refreshed?
3. **Provider Priority:** Which LLM provider should be the default?
4. **Query Types:** Beyond review summaries, what other insights are priorities?
5. **Access Control:** Should all users have access to LLM features, or should it be gated?

