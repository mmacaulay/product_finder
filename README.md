# Product Finder

A Django-based GraphQL API for product information lookup with AI-powered insights.

## Features

- **Product Lookup**: Search products by UPC code
- **GraphQL API**: Modern, flexible API with GraphQL
- **AI-Powered Insights**: Get review summaries, safety analysis, and more using LLMs
  - Perplexity AI (with real-time web search)
  - OpenAI ChatGPT
- **Intelligent Caching**: Automatic result caching to reduce costs and improve speed
- **Admin Interface**: Manage products, prompts, and cached results
- **External API Integration**: Connects to DE Product API for product data

## Quick Start

### Prerequisites

- Python 3.14+
- PostgreSQL
- API keys for:
  - DE Product API
  - Perplexity and/or OpenAI (for LLM features)

### Installation

1. **Clone the repository**

```bash
git clone <your-repo-url>
cd product_finder
```

2. **Install dependencies**

```bash
uv sync
```

3. **Configure environment**

```bash
# Copy environment template
cp env.example .env

# Edit .env with your credentials
```

Required environment variables:
```bash
# Django
SECRET_KEY=your-secret-key
DEBUG=True

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:6000/product_finder_dev

# DE Product API
DE_PRODUCT_API_BASE_URL=https://api.example.com
DE_PRODUCT_APP_KEY=your_app_key
DE_PRODUCT_AUTH_KEY=your_auth_key
DE_PRODUCT_FIELD_NAMES=description,brand

# LLM Providers (add at least one)
PERPLEXITY_API_KEY=pplx-your-key
OPENAI_API_KEY=sk-your-key
DEFAULT_LLM_PROVIDER=perplexity
```

4. **Run migrations**

```bash
uv run python manage.py migrate
```

5. **Seed LLM prompts**

```bash
uv run python manage.py seed_llm_prompts
```

6. **Create admin user** (optional)

```bash
uv run python manage.py createsuperuser
```

7. **Start the server**

```bash
uv run python manage.py runserver
```

## Usage

### GraphQL Endpoint

Visit: http://localhost:8000/graphql/

### Example Queries

#### Get Product by UPC

```graphql
query GetProduct {
  productByUpc(upc: "012345678901") {
    id
    name
    brand
    upcCode
  }
}
```

#### Get Product with AI Review Summary

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

#### Force Refresh Reviews

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

#### Use Specific AI Provider

```graphql
query GetOpenAIReviews {
  productByUpc(upc: "012345678901") {
    reviewSummary(provider: "openai") {
      content
      provider
    }
  }
}
```

## LLM Integration

The product finder includes powerful AI integration for product insights:

### Features

- **Review Summaries**: Aggregate and summarize user reviews from across the internet
- **Smart Caching**: Results cached for 30 days (configurable)
- **Multiple Providers**: Support for Perplexity and OpenAI
- **Cost Effective**: ~80% cost reduction with caching

### Cost Estimates

With $20/month budget and caching enabled:
- ~2,000-5,000 product insights per month
- First query: ~$0.02-$0.05
- Cached queries: $0 (free)

### Documentation

For complete documentation, see the **[docs/](./docs/)** directory:

- **[LLM Usage Guide](./docs/user/llm-usage.md)** - Complete user guide with setup, examples, and troubleshooting
- **[Architecture](./docs/development/architecture.md)** - System architecture and design patterns
- **[Implementation Guide](./docs/development/implementation.md)** - Technical specification
- **[Prompt Examples](./docs/development/prompts.md)** - Sample prompts and best practices

## Admin Interface

Access the Django admin at: http://localhost:8000/admin/

Manage:
- Products
- LLM Prompts (create custom AI queries)
- LLM Query Results (view cached responses)

## Testing

```bash
# Run all tests
uv run python manage.py test

# Run specific test suite
uv run python manage.py test api.tests.test_llm_service

# With coverage
uv run python manage.py test --keepdb
```

## Development

### Project Structure

```
product_finder/
├── api/
│   ├── graphql/          # GraphQL schema and types
│   ├── models.py         # Database models
│   ├── services/
│   │   ├── de_product_api.py     # External API client
│   │   └── llm/                   # LLM service layer
│   │       ├── llm_service.py    # Main orchestrator
│   │       ├── base_provider.py  # Provider interface
│   │       ├── perplexity_provider.py
│   │       └── openai_provider.py
│   ├── management/
│   │   └── commands/
│   │       └── seed_llm_prompts.py
│   └── tests/
├── product_finder/       # Django settings
└── manage.py
```

### Adding New LLM Query Types

1. Create a prompt in Django Admin:
   - Name: `my_custom_query`
   - Query Type: `custom_analysis`
   - Prompt Template: Your prompt with `{product_name}`, `{brand}`, etc.
   - Is Active: ✓

2. Add resolver to GraphQL schema (optional):

```python
# api/graphql/types.py
class ProductType(DjangoObjectType):
    custom_analysis = graphene.Field(
        LLMInsightType,
        provider=graphene.String(required=False),
        force_refresh=graphene.Boolean(required=False)
    )
    
    def resolve_custom_analysis(self, info, provider=None, force_refresh=False):
        # Similar to resolve_review_summary
        ...
```

### Adding New LLM Providers

1. Create provider class in `api/services/llm/`:

```python
from .base_provider import BaseLLMProvider

class MyProvider(BaseLLMProvider):
    def query(self, prompt, **kwargs):
        # Implement API call
        pass
    
    def validate_credentials(self):
        # Test API key
        pass
    
    @property
    def provider_name(self):
        return 'myprovider'
```

2. Update `llm_service.py`:

```python
def _get_provider(self, provider_name):
    # ...
    elif provider_name == 'myprovider':
        provider = MyProvider(**provider_config)
    # ...
```

3. Add configuration to `settings.py` and `.env`

## Documentation

For comprehensive documentation, visit the **[docs/](./docs/)** directory:

- **User Guides**: [docs/user/](./docs/user/) - How to use the API and features
- **Development**: [docs/development/](./docs/development/) - Architecture and technical details
- **Project Records**: [docs/project/](./docs/project/) - Implementation history and checklists

## License

[Your License]

## Contributing

[Your contribution guidelines]



