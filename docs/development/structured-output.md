# Structured LLM Output Implementation - Complete

## Summary

Successfully implemented structured JSON output for all LLM queries in the product_finder application.

## What Changed

### 1. **Database Models** (`api/models.py`)
- **LLMPrompt**: Added `response_schema` (JSONField) and `schema_version` (CharField)
- **LLMQueryResult**: 
  - Changed `result` from TextField to JSONField
  - Added `schema_version` and `parse_attempts` fields
- Migration: `0007_update_for_structured_output.py`

### 2. **Schema System** (NEW)
- **`api/services/llm/schemas.py`**: Centralized schema registry
  - `REVIEW_SUMMARY_SCHEMA`: Defines expected JSON structure for review summaries
  - `SAFETY_ANALYSIS_SCHEMA`: Defines expected JSON structure for safety analysis
  - Schema validation with type coercion and defaults

### 3. **JSON Parsing** (NEW)
- **`api/services/llm/json_parser.py`**: Multi-strategy JSON parser
  - Strategy 1: Direct JSON parse
  - Strategy 2: Extract from markdown json blocks (```json ... ```)
  - Strategy 3: Extract from any markdown blocks (``` ... ```)
  - Strategy 4: Find first { to last } (embedded JSON)
  - Error response creation for parse failures

### 4. **LLM Providers**
- **OpenAIProvider** (`api/services/llm/openai_provider.py`):
  - Added `enable_json_mode` parameter (uses OpenAI's native JSON mode)
  - Added `parse_json` parameter to control JSON parsing
  - Returns structured dict instead of raw string
  - Updated system message to enforce JSON responses

- **PerplexityProvider** (`api/services/llm/perplexity_provider.py`):
  - Same updates as OpenAI provider
  - JSON mode disabled by default (may not be fully supported)

### 5. **LLM Service** (`api/services/llm/llm_service.py`)
- Added `_query_with_retry()` method with intelligent retry logic:
  - Attempts up to 2 retries for parsing failures
  - Adds stronger JSON instructions on retries
  - Validates against schema if available
  - Returns error response if all attempts fail
- Updated `_store_result()` to handle JSON data and track parse attempts

### 6. **GraphQL API** (`api/graphql/types.py`)
- **NEW: `ReviewSummaryType`**: Structured type with fields:
  - `sentiment`, `sentiment_score`, `summary`
  - `pros`, `cons`, `key_themes`, `confidence`
  - Metadata: `provider`, `cached`, `generated_at`

- **NEW: `SafetyAnalysisType`**: Structured type with fields:
  - `risk_level`, `summary`, `harmful_ingredients`
  - `allergens`, `certifications`, `recalls`
  - `recommendations`, `confidence`
  - Metadata: `provider`, `cached`, `generated_at`

- **Updated `ProductType`**:
  - `review_summary` now returns `ReviewSummaryType`
  - Added `safety_analysis` returning `SafetyAnalysisType`

### 7. **Prompts** (`api/management/commands/seed_llm_prompts.py`)
All prompts rewritten to explicitly request JSON:
- **review_summary_basic**: Now requests specific JSON structure
- **review_summary_detailed**: Enhanced with more fields
- **product_safety**: Complete safety analysis in JSON

### 8. **Tests** (`api/tests/test_llm_service.py`)
Updated all tests to work with structured JSON:
- Mock responses now return dicts instead of strings
- Assertions check dict structure and fields
- Added checks for JSON parsing metadata

## JSON Response Format

### Review Summary
```json
{
  "sentiment": "positive",
  "sentiment_score": 0.85,
  "summary": "Brief overview...",
  "pros": ["point 1", "point 2", "point 3"],
  "cons": ["complaint 1", "complaint 2", "complaint 3"],
  "key_themes": ["theme 1", "theme 2"],
  "confidence": "high"
}
```

### Safety Analysis
```json
{
  "risk_level": "low",
  "summary": "Brief safety overview...",
  "harmful_ingredients": [
    {"name": "ingredient", "concern": "concern", "severity": "low"}
  ],
  "allergens": ["allergen 1", "allergen 2"],
  "certifications": ["cert 1", "cert 2"],
  "recalls": [
    {"date": "2025-01-01", "reason": "reason", "status": "resolved"}
  ],
  "recommendations": "Who should avoid...",
  "confidence": "high"
}
```

## Error Handling Strategy

### Layer 1: Prevention
- OpenAI native JSON mode (`response_format={"type": "json_object"}`)
- Strong prompt instructions
- JSON-focused system messages

### Layer 2: Parsing
- Multi-strategy parser handles various output formats
- Type coercion for minor type mismatches
- Partial validation with defaults for missing fields

### Layer 3: Retry
- One automatic retry with stronger instructions
- Tracks parse attempts in metadata
- Logs all failures for monitoring

### Layer 4: Graceful Degradation
- Returns error response if all attempts fail
- Error response structure:
  ```json
  {
    "error": "parsing_failed",
    "error_message": "Description of error",
    "confidence": "none"
  }
  ```

## Expected Failure Rates
- **OpenAI with JSON mode**: ~1-2% (very reliable)
- **OpenAI without JSON mode**: ~5-10%
- **Perplexity**: ~10-20% (if no native JSON support)

## How to Use

### From GraphQL

```graphql
query {
  productByUpc(upc: "123456789012") {
    name
    brand
    reviewSummary {
      sentiment
      sentimentScore
      summary
      pros
      cons
      keyThemes
      confidence
      provider
      cached
      generatedAt
    }
    safetyAnalysis {
      riskLevel
      summary
      harmfulIngredients
      allergens
      certifications
      confidence
    }
  }
}
```

### From Python (LLMService)

```python
from api.services.llm import LLMService

service = LLMService()
result = service.get_product_insight(
    product=my_product,
    query_type='review_summary',
    provider='openai',  # optional
    force_refresh=False  # optional
)

# result['content'] is now a dict, not a string!
print(result['content']['sentiment'])
print(result['content']['pros'])
print(result['cached'])
```

## Next Steps (Optional Enhancements)

1. **Monitoring Dashboard**: Track parse failure rates by provider/query_type
2. **Schema Versioning UI**: Admin interface to manage schemas
3. **Additional Query Types**: Add more structured query types (e.g., competitor_analysis, price_history)
4. **Response Validation Webhooks**: Alert on high parse failure rates
5. **A/B Testing**: Test different prompt variations for best compliance

## Files Changed

- `api/models.py`
- `api/migrations/0007_update_for_structured_output.py`
- `api/services/llm/schemas.py` (NEW)
- `api/services/llm/json_parser.py` (NEW)
- `api/services/llm/openai_provider.py`
- `api/services/llm/perplexity_provider.py`
- `api/services/llm/llm_service.py`
- `api/graphql/types.py`
- `api/management/commands/seed_llm_prompts.py`
- `api/tests/test_llm_service.py`

## Migration Complete ✅

All changes have been migrated and prompts updated. The system is now ready to return structured JSON from LLM queries!

