# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Setup and Dependencies
```bash
# Install dependencies with uv
uv sync

# Set up environment
cp env.example .env
# Then edit .env with your credentials

# Run database migrations
uv run python manage.py migrate

# Seed initial LLM prompts
uv run python manage.py seed_llm_prompts

# Create admin user
uv run python manage.py createsuperuser
```

### Running the Application
```bash
# Start development server
uv run python manage.py runserver

# With Docker Compose (includes PostgreSQL + Firestore Emulator)
docker-compose up

# Access points:
# - GraphQL: http://localhost:8000/graphql/
# - Admin: http://localhost:8000/admin/
# - PostgreSQL: localhost:6000
# - Firestore Emulator: localhost:8080
```

### Testing
```bash
# Run all tests
uv run python manage.py test

# Run specific test module
uv run python manage.py test api.tests.test_llm_service

# Run specific test class
uv run python manage.py test api.tests.test_graphql.GraphQLTestCase

# Run specific test method
uv run python manage.py test api.tests.test_graphql.GraphQLTestCase.test_product_by_upc

# Keep database between test runs (faster)
uv run python manage.py test --keepdb
```

### Database Operations
```bash
# Create new migration after model changes
uv run python manage.py makemigrations

# Apply migrations
uv run python manage.py migrate

# Access PostgreSQL shell
psql -h localhost -p 6000 -U postgres -d product_finder_dev
```

## Architecture Overview

### Dual Storage System
The application is transitioning from PostgreSQL to Firestore:
- **PostgreSQL**: Legacy Django ORM models in `api/models.py` (Product, LLMPrompt, LLMQueryResult)
- **Firestore**: Current data layer using DAOs in `api/firestore_models.py` (ProductDAO, LLMPromptDAO, LLMQueryResultDAO)
- GraphQL schema uses Firestore DAOs exclusively
- Firestore Emulator runs locally via Docker Compose on port 8080

When working with data access:
- Use DAO classes from `api/firestore_models.py` for all GraphQL operations
- DAOs return dictionaries, not Django model instances
- Document IDs are meaningful: UPC codes for products, names for prompts, composite keys for query results
- Timestamps use `firestore.SERVER_TIMESTAMP` for creation/updates

### LLM Integration Architecture
The LLM system follows a multi-layer architecture:

**Service Layer** (`api/services/llm/llm_service.py`):
- `LLMService` is the main orchestrator - always use this, never call providers directly
- Manages caching, prompt rendering, provider selection, and retry logic
- Uses DAOs for data access instead of Django ORM
- Key method: `get_product_insight(product, query_type, provider=None, force_refresh=False, max_retries=2)`
- Caches results in Firestore (30-day TTL by default)
- Implements automatic retry with stronger JSON instructions on parse failures

**Provider Layer** (`api/services/llm/`):
- `BaseLLMProvider`: Abstract interface all providers implement
- `OpenAIProvider`: OpenAI ChatGPT integration
- `PerplexityProvider`: Perplexity AI with real-time web search
- Each provider handles JSON parsing with multiple fallback strategies
- Returns structured dict: `{'content': dict, 'metadata': dict}`

**GraphQL Layer** (`api/graphql/types.py`):
- Typed resolvers (ReviewSummaryType, SafetyAnalysisType) query LLMService
- Products are Firestore dicts, not Django models
- Resolvers pass `self` (the product dict) directly to LLMService
- Add `_metadata` to responses for provider, cache status, timestamp

**Prompt Management**:
- Prompts stored in Firestore via `seed_llm_prompts.py` management command
- Template variables: `{product_name}`, `{brand}`, `{upc_code}`, `{additional_data}`
- Query types define categories: 'review_summary', 'safety_analysis'
- Schemas in `api/services/llm/schemas.py` validate LLM responses
- Schema validation happens automatically after successful parsing

### GraphQL API
The API uses JWT authentication:
- REST endpoints for auth: `/api/auth/register/`, `/api/auth/login/`, `/api/auth/token/refresh/`
- GraphQL endpoint requires `Authorization: Bearer <token>` header
- In DEBUG mode, GraphiQL interface accessible without auth (GET requests only)
- Production mode requires authentication for all GraphQL requests

**Query Patterns**:
```graphql
# Basic product lookup (fetches from Firestore or DE Product API)
productByUpc(upc: "012345678901") { id name brand }

# LLM insights with caching
productByUpc(upc: "012345678901") {
  reviewSummary { sentiment pros cons }
  safetyAnalysis { risk_level harmful_ingredients }
}

# Force fresh LLM query
reviewSummary(forceRefresh: true, provider: "openai") { ... }
```

### External API Integration
`DEProductAPI` (`api/services/de_product_api.py`) fetches product data:
- Requires HMAC-SHA1 authentication
- GraphQL resolver checks Firestore first, falls back to DE API
- Successful API fetches automatically stored in Firestore
- All configuration via environment variables in `DE_PRODUCT_CONFIG`

### Testing Infrastructure
Tests use `responses` library to mock HTTP requests:
- Base class: `MockedAPITestCase` in `api/tests/base.py`
- Automatically mocks all `requests.get/post` calls
- Test fixtures in `api/tests/fixtures.py`
- All tests run against in-memory test database
- HTTP mocks prevent accidental external API calls during tests

## Configuration

### Environment Variables
Required variables in `.env`:
```bash
# Django
SECRET_KEY=your-secret-key
DEBUG=True

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:6000/product_finder_dev

# Firestore
FIRESTORE_PROJECT_ID=product-finder-dev
FIRESTORE_EMULATOR_HOST=localhost:8080  # For local dev

# JWT (optional, have defaults)
JWT_ACCESS_TOKEN_LIFETIME=60  # minutes
JWT_REFRESH_TOKEN_LIFETIME=7  # days

# DE Product API
DE_PRODUCT_API_BASE_URL=https://api.example.com
DE_PRODUCT_APP_KEY=your_app_key
DE_PRODUCT_AUTH_KEY=your_auth_key
DE_PRODUCT_FIELD_NAMES=description,brand

# LLM Providers (configure at least one)
PERPLEXITY_API_KEY=pplx-your-key
OPENAI_API_KEY=sk-your-key
DEFAULT_LLM_PROVIDER=perplexity
```

### Settings Structure
Django settings (`product_finder/settings.py`) expose:
- `LLM_CONFIG`: Provider settings, caching config, model parameters
- `DE_PRODUCT_CONFIG`: External API credentials
- `FIRESTORE_PROJECT_ID`, `FIRESTORE_CREDENTIALS`, `FIRESTORE_EMULATOR_HOST`
- All config uses `django-environ` for environment variable parsing

## Deployment

### GCP Cloud Run
Infrastructure managed via Terraform in `terraform/`:
- Cloud Run service with auto-scaling
- Cloud SQL (PostgreSQL)
- Firestore database
- Secret Manager for credentials
- Artifact Registry for container images

Deploy via GitHub Actions (CI/CD pipeline):
```bash
# Push to main branch triggers deployment
git push origin main
```

Manual Terraform deployment:
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with project settings
terraform init
terraform apply
```

## Key Patterns

### Adding a New LLM Query Type
1. Create prompt in Firestore (via admin or seed command):
   - Set `name`, `query_type`, `prompt_template`
   - Define `response_schema` for validation
   - Mark `is_active=True`

2. Add schema in `api/services/llm/schemas.py`:
   ```python
   SCHEMAS = {
       'your_query_type': {
           'type': 'object',
           'required': ['field1', 'field2'],
           'properties': {...}
       }
   }
   ```

3. Add GraphQL type in `api/graphql/types.py`:
   ```python
   class YourInsightType(graphene.ObjectType):
       field1 = graphene.String()
       # ... define fields matching schema
   ```

4. Add resolver to ProductType:
   ```python
   your_insight = graphene.Field(YourInsightType, ...)

   def resolve_your_insight(self, info, provider=None, force_refresh=False):
       llm_service = LLMService()
       result = llm_service.get_product_insight(
           product=self,
           query_type='your_query_type',
           provider=provider,
           force_refresh=force_refresh
       )
       content = result['content']
       content['_metadata'] = {...}
       return content
   ```

### Adding a New LLM Provider
1. Create provider class implementing `BaseLLMProvider`:
   ```python
   class MyProvider(BaseLLMProvider):
       def query(self, prompt, **kwargs):
           # API call and JSON parsing

       def validate_credentials(self):
           # Test API key

       @property
       def provider_name(self):
           return 'myprovider'
   ```

2. Update `LLMService._get_provider()` to instantiate new provider

3. Add config to `settings.py`:
   ```python
   LLM_CONFIG = {
       'providers': {
           'myprovider': {
               'api_key': env('MYPROVIDER_API_KEY'),
               'model': env('MYPROVIDER_MODEL'),
               # ...
           }
       }
   }
   ```

### Working with Firestore DAOs
```python
# Create
dao = ProductDAO()
product = dao.create(upc_code='123', name='Product', brand='Brand')

# Read
product = dao.get_by_upc('123')  # Returns dict or None

# Update
dao.update('123', name='New Name')

# Query with filters (for prompts)
prompts = LLMPromptDAO().get_active_by_type('review_summary')

# Composite keys (for query results)
result = LLMQueryResultDAO().get_by_composite_key(upc, prompt_name, provider)
```

## Documentation
Comprehensive docs in `docs/`:
- `docs/user/`: End-user guides (authentication, LLM usage)
- `docs/development/`: Architecture, implementation details, prompts
- `docs/deployment/`: GCP setup, troubleshooting
- `docs/project/`: Implementation history, checklists
