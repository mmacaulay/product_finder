# LLM Integration Usage Guide

This guide explains how to use the LLM (Large Language Model) integration for product insights.

## Overview

The LLM integration allows you to query AI services (Perplexity, OpenAI) to get intelligent insights about products, such as:
- User review summaries from the internet
- Safety and ingredient analysis
- Product comparisons
- And more...

Results are automatically cached to reduce API costs and improve response times.

---

## Setup

### 1. Install Dependencies

Dependencies are already included in `pyproject.toml`. If you need to reinstall:

```bash
uv sync
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and add your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add at least one LLM provider API key:

```bash
# For Perplexity (recommended for product reviews)
PERPLEXITY_API_KEY=pplx-your-api-key-here

# Or for OpenAI
OPENAI_API_KEY=sk-your-api-key-here

# Choose default provider
DEFAULT_LLM_PROVIDER=perplexity
```

### 3. Run Migrations

```bash
uv run python manage.py migrate
```

### 4. Seed Initial Prompts

```bash
uv run python manage.py seed_llm_prompts
```

This creates default prompt templates for common queries like review summaries.

---

## Usage

### GraphQL Queries

#### Basic Review Summary

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
      queryType
    }
  }
}
```

**Response:**

```json
{
  "data": {
    "productByUpc": {
      "id": 1,
      "name": "Organic Coffee Beans",
      "brand": "Great Coffee Co",
      "reviewSummary": {
        "content": "Overall, users love these organic coffee beans for their rich, bold flavor...",
        "provider": "perplexity",
        "cached": true,
        "generatedAt": "2025-11-12T18:30:00Z",
        "queryType": "review_summary"
      }
    }
  }
}
```

#### Force Refresh (Bypass Cache)

```graphql
query GetFreshReviews {
  productByUpc(upc: "012345678901") {
    reviewSummary(forceRefresh: true) {
      content
      cached
    }
  }
}
```

#### Use Specific Provider

```graphql
query GetReviewsFromOpenAI {
  productByUpc(upc: "012345678901") {
    reviewSummary(provider: "openai") {
      content
      provider
    }
  }
}
```

---

## Managing Prompts

Prompts are stored in the database and can be managed through Django Admin.

### Access Django Admin

1. Create a superuser if you haven't:
   ```bash
   uv run python manage.py createsuperuser
   ```

2. Start the server:
   ```bash
   uv run python manage.py runserver
   ```

3. Visit: http://localhost:8000/admin/

4. Navigate to **LLM Prompts**

### Create a New Prompt

1. Click **Add LLM Prompt**
2. Fill in the fields:
   - **Name**: Unique identifier (e.g., `review_summary_detailed`)
   - **Query Type**: Category (e.g., `review_summary`, `safety_analysis`)
   - **Description**: What this prompt does
   - **Prompt Template**: The actual prompt text with variables
   - **Is Active**: Check to enable this prompt

### Prompt Variables

Use these variables in your prompt templates:

- `{product_name}` - Product name
- `{brand}` - Brand name
- `{upc_code}` - UPC code
- `{additional_data}` - Full product data from DE API

**Example Prompt:**

```
Summarize user reviews for "{product_name}" by {brand} (UPC: {upc_code}).

Include:
- Overall sentiment
- Top 3 pros
- Top 3 cons
- Key themes

Limit response to 200 words.
```

---

## Caching System

### How It Works

1. **First Query**: Calls LLM API, stores result in database
2. **Subsequent Queries**: Returns cached result instantly (no API call)
3. **Cache TTL**: Results expire after 30 days (configurable)
4. **Force Refresh**: Bypass cache when needed

### Cache Configuration

In `.env`:

```bash
# How long to keep cached results (days)
LLM_CACHE_TTL_DAYS=30

# Enable/disable caching
LLM_ENABLE_CACHING=true
```

### Manage Cache via Admin

1. Go to **LLM Query Results** in Django Admin
2. View all cached results
3. Use bulk actions:
   - **Mark as stale** - Forces refresh on next request
   - **Mark as fresh** - Keeps result in cache

### Programmatic Cache Management

```python
from api.services.llm import LLMService
from api.models import Product

service = LLMService()
product = Product.objects.get(upc_code='012345678901')

# Invalidate all cache for a product
service.invalidate_cache(product)

# Invalidate specific query type
service.invalidate_cache(product, query_type='review_summary')

# Invalidate specific provider
service.invalidate_cache(product, provider='perplexity')

# Get cache statistics
stats = service.get_cache_stats(product)
print(f"Total cached: {stats['total_cached']}")
print(f"Fresh: {stats['fresh']}")
print(f"Stale: {stats['stale']}")
```

---

## Cost Management

### Estimated Costs (as of 2025)

**Without Caching:**
- Perplexity: ~$0.02-$0.05 per query
- OpenAI GPT-4: ~$0.02-$0.05 per query
- OpenAI GPT-3.5: ~$0.001-$0.003 per query

**With 80% Cache Hit Rate:**
- Cost reduction: ~80%
- Example: 1,000 queries = ~$4-10 instead of $20-50

### Budget Guidelines

For a $20/month budget with caching:
- ~400-1,000 uncached queries/month
- ~2,000-5,000 effective queries/month (with caching)

### Monitor Costs

View cost estimates in Django Admin:
1. Go to **LLM Query Results**
2. Click on any result
3. Check the **Metadata** field for `cost_estimate`

---

## Python API

### Direct Service Usage

```python
from api.services.llm import LLMService
from api.models import Product

# Initialize service
service = LLMService()

# Get product insight
product = Product.objects.get(upc_code='012345678901')
summary = service.get_product_insight(
    product=product,
    query_type='review_summary',
    provider='perplexity',  # Optional
    force_refresh=False      # Optional
)

print(summary)
```

### Available Providers

```python
# List all configured providers
providers = service.list_available_providers()
# Returns: ['openai', 'perplexity']

# Validate provider credentials
is_valid = service.validate_provider('perplexity')
# Returns: True or False
```

---

## Troubleshooting

### "No active prompt found"

**Problem:** GraphQL query returns `null` for `reviewSummary`

**Solution:**
1. Run `uv run python manage.py seed_llm_prompts`
2. Or create a prompt manually in Django Admin with `query_type='review_summary'` and `is_active=True`

### "No API key configured"

**Problem:** Error about missing API key

**Solution:**
1. Check your `.env` file has the correct API key
2. Restart the Django server after changing `.env`
3. Verify environment variable names match exactly

### Slow Response Times

**Problem:** First query takes several seconds

**Expected:** First query calls the LLM API (slow), subsequent queries are instant (cached)

**If always slow:**
1. Check `LLM_ENABLE_CACHING=true` in `.env`
2. Verify cache is working: check `cached: true` in GraphQL response

### Rate Limiting

**Problem:** "Rate limit exceeded" error

**Solution:**
1. Wait before retrying
2. Use caching to reduce API calls
3. Consider upgrading your API plan

---

## Advanced Configuration

### Custom Models

In `.env`:

```bash
# Use different Perplexity models
PERPLEXITY_MODEL=llama-3.1-sonar-small-128k-online  # Cheaper
PERPLEXITY_MODEL=llama-3.1-sonar-large-128k-online  # Better quality

# Use different OpenAI models
OPENAI_MODEL=gpt-3.5-turbo     # Cheaper
OPENAI_MODEL=gpt-4-turbo-preview  # Better quality
```

### Token Limits

Control response length:

```bash
PERPLEXITY_MAX_TOKENS=500  # Shorter responses
PERPLEXITY_MAX_TOKENS=1000 # Longer responses
```

### Temperature

Control response creativity:

```bash
PERPLEXITY_TEMPERATURE=0.0  # Deterministic
PERPLEXITY_TEMPERATURE=0.7  # Balanced (default)
PERPLEXITY_TEMPERATURE=1.0  # Creative
```

---

## Testing

### Run Tests

```bash
# All LLM tests
uv run python manage.py test api.tests.test_llm_service

# All tests
uv run python manage.py test
```

### Mock API Calls

Tests use mocked API calls to avoid costs. See `api/tests/test_llm_service.py` for examples.

---

## Best Practices

1. **Use Caching**: Let the system cache results automatically
2. **Choose Right Provider**: 
   - Perplexity: Best for current info (reviews, news, prices)
   - OpenAI: Best for analysis and reasoning
3. **Optimize Prompts**: Shorter prompts = lower costs
4. **Set Token Limits**: Prevent runaway costs
5. **Monitor Usage**: Check cache hit rates and costs regularly
6. **Update Prompts**: Refine prompts based on response quality

---

## API Reference

### GraphQL Schema

```graphql
type ProductType {
  id: Int!
  upcCode: String!
  name: String!
  brand: String
  createdAt: DateTime!
  updatedAt: DateTime!
  
  reviewSummary(
    provider: String
    forceRefresh: Boolean
  ): LLMInsightType
}

type LLMInsightType {
  content: String!
  provider: String!
  cached: Boolean!
  generatedAt: DateTime
  queryType: String!
}
```

---

## Support

For issues or questions:
1. Check this guide
2. Review [Implementation Guide](../development/implementation.md) for architecture details
3. Check Django Admin logs
4. Review test cases in `api/tests/test_llm_service.py`



