# LLM Integration Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          GraphQL API Layer                               │
│                                                                           │
│  ┌──────────────────────┐         ┌──────────────────────────────────┐  │
│  │   ProductType        │         │   Query                          │  │
│  │                      │         │                                  │  │
│  │  - id                │         │  - productByUpc                  │  │
│  │  - name              │         │  - productWithInsights           │  │
│  │  - brand             │         │  - allProducts                   │  │
│  │  - reviewSummary  ◄──┼─────────┼─ Calls LLMService               │  │
│  │    (LLMInsightType)  │         │                                  │  │
│  └──────────────────────┘         └──────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       Service Layer (LLMService)                         │
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  LLMService (Orchestrator)                                         │ │
│  │  ┌──────────────────┐  ┌──────────────┐  ┌────────────────────┐  │ │
│  │  │ Cache Check      │→ │ Provider     │→ │ Store Result       │  │ │
│  │  │ (LLMQueryResult) │  │ Selection    │  │ (LLMQueryResult)   │  │ │
│  │  └──────────────────┘  └──────┬───────┘  └────────────────────┘  │ │
│  └────────────────────────────────┼─────────────────────────────────┘ │
│                                    │                                    │
│  ┌────────────────────────────────┼─────────────────────────────────┐ │
│  │  Provider Interface             ▼                                 │ │
│  │  (BaseLLMProvider)                                                │ │
│  │                                                                   │ │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │ │
│  │  │  OpenAI Provider │  │ Perplexity       │  │ Future        │ │ │
│  │  │                  │  │ Provider         │  │ Providers...  │ │ │
│  │  │  - query()       │  │                  │  │               │ │ │
│  │  │  - validate()    │  │  - query()       │  │               │ │ │
│  │  └──────────────────┘  └──────────────────┘  └───────────────┘ │ │
│  └───────────────────────────────────────────────────────────────┘ │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          Database Layer                                  │
│                                                                           │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────────┐   │
│  │   Product        │  │  LLMPrompt       │  │  LLMQueryResult    │   │
│  │                  │  │                  │  │                    │   │
│  │  - upc_code      │  │  - name          │  │  - product_id (FK) │   │
│  │  - name          │  │  - description   │  │  - prompt_id (FK)  │   │
│  │  - brand         │  │  - prompt_templ  │  │  - provider        │   │
│  │  - de_product... │  │  - query_type    │  │  - query_input     │   │
│  │                  │  │  - is_active     │  │  - result          │   │
│  └────────┬─────────┘  └──────────────────┘  │  - metadata        │   │
│           │                                   │  - is_stale        │   │
│           │   ┌──────────────────────────────┤  - created_at      │   │
│           └───┤  Foreign Key Relationships   │                    │   │
│               └──────────────────────────────┴────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       External LLM APIs                                  │
│                                                                           │
│  ┌──────────────────┐         ┌────────────────────────────┐           │
│  │  OpenAI API      │         │  Perplexity API            │           │
│  │  (ChatGPT)       │         │  (with web search)         │           │
│  └──────────────────┘         └────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────────────┘
```

## Request Flow

### 1. Initial Request (Cache Miss)
```
User Query (GraphQL)
    ↓
ProductType.resolve_review_summary()
    ↓
LLMService.get_product_insight()
    ↓
Check Cache (LLMQueryResult) → Not Found
    ↓
Get Prompt Template (LLMPrompt)
    ↓
Render Prompt with Product Data
    ↓
Select Provider (OpenAI/Perplexity)
    ↓
Provider.query() → External API Call
    ↓
Store Result in Cache (LLMQueryResult)
    ↓
Return Result to User
```

### 2. Subsequent Request (Cache Hit)
```
User Query (GraphQL)
    ↓
ProductType.resolve_review_summary()
    ↓
LLMService.get_product_insight()
    ↓
Check Cache (LLMQueryResult) → Found! (< 30 days old)
    ↓
Return Cached Result to User
(No API call, instant response)
```

### 3. Force Refresh Request
```
User Query (GraphQL, force_refresh=true)
    ↓
ProductType.resolve_review_summary(force_refresh=True)
    ↓
LLMService.get_product_insight(force_refresh=True)
    ↓
Skip Cache Check
    ↓
Query LLM Provider
    ↓
Update Cache (LLMQueryResult)
    ↓
Return Fresh Result to User
```

## Key Design Patterns

### 1. Strategy Pattern
- **BaseLLMProvider** as interface
- Concrete providers (OpenAI, Perplexity) implement the interface
- Easy to add new providers without changing core logic

### 2. Template Method Pattern
- **LLMPrompt** model stores reusable prompt templates
- Variables like `{product_name}`, `{brand}` are replaced at runtime
- Allows non-technical users to update prompts via Django admin

### 3. Cache-Aside Pattern
- Check cache first (LLMQueryResult)
- On miss, query provider and populate cache
- Reduces API calls and improves response time

### 4. Facade Pattern
- **LLMService** provides simple interface to complex operations
- Hides provider selection, caching, and error handling from GraphQL layer

## Database Relationships

```
Product ────────┐
    │           │
    │           │ (One to Many)
    │           │
    ▼           ▼
LLMPrompt   LLMQueryResult
    │           │
    │           │
    └───────────┘
    (One to Many)
```

**Relationships:**
- Product → LLMQueryResult: One-to-Many (a product can have many cached results)
- LLMPrompt → LLMQueryResult: One-to-Many (a prompt can be used for many products)
- Unique constraint: (product, prompt, provider) ensures one cache entry per combination

## Configuration Flow

```
Environment Variables (.env)
    ↓
Settings (product_finder/settings.py)
    ↓
LLM_CONFIG dictionary
    ↓
LLMService initialization
    ↓
Provider instances created with credentials
```

## Error Handling Strategy

```
LLM Provider Error
    ↓
Log Error with context
    ↓
Fallback to alternate provider? (optional)
    ↓
Return graceful error message
    ↓
Don't cache error results
```

## Monitoring Points

1. **Cache Hit Rate:** % of requests served from cache
2. **API Costs:** Track tokens/cost per provider
3. **Response Times:** Cache vs. API call latency
4. **Error Rates:** By provider and query type
5. **Cache Age:** Distribution of cached result ages

