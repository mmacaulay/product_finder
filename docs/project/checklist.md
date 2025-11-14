# LLM Integration Implementation Checklist

Use this checklist to track implementation progress. Mark items as complete with `[x]`.

## Phase 1: Foundation (Week 1)

### Database Models
- [ ] Create `LLMPrompt` model in `api/models.py`
- [ ] Create `LLMQueryResult` model in `api/models.py`
- [ ] Add model admin interfaces in `api/admin.py`
- [ ] Create and run migrations
- [ ] Test migrations on test database

### Base Provider Interface
- [ ] Create `api/services/llm/__init__.py`
- [ ] Create `api/services/llm/exceptions.py` with custom exceptions
- [ ] Create `api/services/llm/base_provider.py` with abstract base class
- [ ] Add docstrings and type hints

### OpenAI Provider
- [ ] Create `api/services/llm/openai_provider.py`
- [ ] Implement `query()` method
- [ ] Implement `validate_credentials()` method
- [ ] Add error handling for rate limits
- [ ] Add error handling for invalid API keys
- [ ] Add error handling for network errors

### Configuration
- [ ] Add OpenAI dependency to `pyproject.toml`
- [ ] Run `uv sync` to install dependencies
- [ ] Add `LLM_CONFIG` to `product_finder/settings.py`
- [ ] Update `.env.example` with new environment variables
- [ ] Update `README.md` with LLM setup instructions

### Testing (Phase 1)
- [ ] Create `api/tests/test_llm_providers.py`
- [ ] Write tests for OpenAI provider with mocked responses
- [ ] Write tests for provider error handling
- [ ] Create mock fixtures in `api/tests/fixtures/llm_responses.json`
- [ ] Run all tests and ensure they pass

---

## Phase 2: Service Layer (Week 2)

### LLM Service Orchestrator
- [ ] Create `api/services/llm/llm_service.py`
- [ ] Implement `__init__()` with provider initialization
- [ ] Implement `get_product_insight()` method
- [ ] Implement cache checking logic
- [ ] Implement prompt rendering with product data
- [ ] Implement result storage in database
- [ ] Add `invalidate_cache()` method
- [ ] Add `_get_provider()` helper method
- [ ] Add `_render_prompt()` helper method

### Perplexity Provider
- [ ] Create `api/services/llm/perplexity_provider.py`
- [ ] Implement using `httpx` for API calls
- [ ] Implement `query()` method
- [ ] Implement `validate_credentials()` method
- [ ] Add error handling
- [ ] Update settings with Perplexity config

### Advanced Features
- [ ] Add cache TTL checking (mark stale results)
- [ ] Add provider fallback logic (optional)
- [ ] Add cost estimation tracking in metadata
- [ ] Add logging for all LLM operations
- [ ] Add request timeout configuration

### Testing (Phase 2)
- [ ] Create `api/tests/test_llm_service.py`
- [ ] Test cache hit scenario
- [ ] Test cache miss scenario
- [ ] Test force refresh functionality
- [ ] Test prompt rendering with product data
- [ ] Test provider selection logic
- [ ] Test Perplexity provider with mocked responses
- [ ] Test error scenarios and fallbacks
- [ ] Run all tests and ensure they pass

---

## Phase 3: GraphQL Integration (Week 3)

### GraphQL Types
- [ ] Create `LLMInsightType` in `api/graphql/types.py`
- [ ] Add `review_summary` field to `ProductType`
- [ ] Implement `resolve_review_summary()` resolver
- [ ] Add optional parameters (provider, force_refresh)
- [ ] Handle errors gracefully in resolver

### GraphQL Queries
- [ ] Add `product_with_insights` query to schema
- [ ] Implement resolver for new query
- [ ] Add documentation for new query
- [ ] Test queries in GraphiQL interface

### Initial Data Setup
- [ ] Create Django management command for seeding prompts
- [ ] Create `api/management/commands/seed_llm_prompts.py`
- [ ] Add default "review_summary" prompt template
- [ ] Run seed command on dev database
- [ ] Verify prompts in Django admin

### Testing (Phase 3)
- [ ] Create `api/tests/test_llm_graphql.py`
- [ ] Test basic review_summary query
- [ ] Test with force_refresh parameter
- [ ] Test with provider parameter
- [ ] Test cache indicator in response
- [ ] Test error handling in GraphQL
- [ ] Run all tests and ensure they pass

---

## Phase 4: Production Readiness (Week 4)

### Monitoring & Logging
- [ ] Add structured logging for LLM queries
- [ ] Log cache hit/miss rates
- [ ] Log API call durations
- [ ] Log error rates by provider
- [ ] Add cost tracking logs (tokens used)

### Rate Limiting
- [ ] Add rate limit configuration per provider
- [ ] Implement backoff/retry logic
- [ ] Add circuit breaker for failed providers (optional)
- [ ] Test rate limit handling

### Performance Optimization
- [ ] Add database indexes for LLMQueryResult lookups
- [ ] Optimize cache query performance
- [ ] Add cache warming for popular products (optional)
- [ ] Profile and optimize slow queries

### Security & Best Practices
- [ ] Audit API key management
- [ ] Add input validation for prompt rendering
- [ ] Sanitize product data before sending to LLMs
- [ ] Add cost budget alerts (optional)
- [ ] Review and update `.gitignore` for sensitive files

### Documentation
- [ ] Update README with complete setup instructions
- [ ] Document environment variables
- [ ] Add GraphQL query examples
- [ ] Document prompt template syntax
- [ ] Add troubleshooting guide
- [ ] Document cost estimation and monitoring

### Final Testing
- [ ] Run full test suite
- [ ] Test with real API keys in development
- [ ] Test cache expiration behavior
- [ ] Test with multiple products
- [ ] Perform load testing (optional)
- [ ] Test error scenarios with real APIs

---

## Post-Launch Tasks

### Monitoring & Maintenance
- [ ] Set up cost monitoring dashboard
- [ ] Create alerts for high API usage
- [ ] Schedule regular cache cleanup (remove very old entries)
- [ ] Monitor cache hit rates and adjust TTL if needed
- [ ] Review and optimize prompts based on response quality

### Future Enhancements (Prioritized)
- [ ] Add more query types (ingredient analysis, comparisons, etc.)
- [ ] Implement background job processing for LLM queries
- [ ] Add user feedback mechanism (thumbs up/down)
- [ ] Implement A/B testing for different prompts
- [ ] Add multi-provider consensus (aggregate multiple LLM responses)
- [ ] Implement streaming responses for long-form content
- [ ] Add admin dashboard for LLM analytics

---

## Quick Start Commands

```bash
# Install dependencies
uv sync

# Create migrations
python manage.py makemigrations

# Run migrations
python manage.py migrate

# Seed initial prompts
python manage.py seed_llm_prompts

# Run tests
python manage.py test api.tests.test_llm_providers
python manage.py test api.tests.test_llm_service
python manage.py test api.tests.test_llm_graphql

# Run all tests
python manage.py test

# Start development server
python manage.py runserver
```

---

## Environment Variables Checklist

Required for OpenAI:
- [ ] `OPENAI_API_KEY`
- [ ] `OPENAI_MODEL` (optional, defaults to gpt-4-turbo-preview)
- [ ] `OPENAI_MAX_TOKENS` (optional, defaults to 500)
- [ ] `OPENAI_TEMPERATURE` (optional, defaults to 0.7)

Required for Perplexity:
- [ ] `PERPLEXITY_API_KEY`
- [ ] `PERPLEXITY_MODEL` (optional, defaults to pplx-70b-online)
- [ ] `PERPLEXITY_MAX_TOKENS` (optional, defaults to 500)

General LLM Config:
- [ ] `DEFAULT_LLM_PROVIDER` (optional, defaults to openai)
- [ ] `LLM_CACHE_TTL_DAYS` (optional, defaults to 30)
- [ ] `LLM_ENABLE_CACHING` (optional, defaults to true)

---

## Key Milestones

- [ ] **Milestone 1:** Database models created and migrated
- [ ] **Milestone 2:** First LLM provider (OpenAI) working with tests
- [ ] **Milestone 3:** LLM service with caching implemented
- [ ] **Milestone 4:** Second provider (Perplexity) implemented
- [ ] **Milestone 5:** GraphQL integration complete
- [ ] **Milestone 6:** All tests passing
- [ ] **Milestone 7:** Production-ready with monitoring
- [ ] **Milestone 8:** Deployed and validated in production

---

## Risk Mitigation

### High Risks
- [ ] **API Costs:** Implement budget alerts and rate limiting
- [ ] **API Reliability:** Add fallback providers and error handling
- [ ] **Cache Invalidation:** Define clear cache refresh strategy
- [ ] **Prompt Quality:** Test prompts thoroughly before production

### Medium Risks
- [ ] **Performance:** Monitor response times, optimize cache queries
- [ ] **Security:** Audit API key management and input validation
- [ ] **Data Privacy:** Review what data is sent to external APIs

---

## Team Coordination

### Code Review Checklist
- [ ] All new code has tests
- [ ] No API keys in code or commits
- [ ] Error handling covers all edge cases
- [ ] Logging is informative but not excessive
- [ ] Documentation is up to date
- [ ] Performance is acceptable (< 100ms for cached, < 3s for API calls)

### Deployment Checklist
- [ ] Environment variables configured in production
- [ ] Database migrations run successfully
- [ ] Initial prompts seeded
- [ ] Monitoring and alerts configured
- [ ] Test with real products in staging
- [ ] Rollback plan documented

---

## Notes & Learnings

Use this section to document any important decisions, gotchas, or learnings during implementation:

```
Date: 
Note: 

Date: 
Note: 

Date: 
Note: 
```

