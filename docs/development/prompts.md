# Sample LLM Prompt Templates

This document contains sample prompt templates for different query types. These can be used to seed the `LLMPrompt` database or as inspiration for creating new prompts.

---

## 1. Review Summary (Primary Use Case)

### Basic Review Summary
**Name:** `review_summary_basic`
**Query Type:** `review_summary`
**Description:** Generates a concise summary of user reviews from across the internet

**Template:**
```
Summarize user reviews for the product "{product_name}" by {brand} (UPC: {upc_code}).

Please include:
- Overall sentiment (positive/negative/mixed)
- Common praise points (top 3)
- Common complaints (top 3)
- Key themes mentioned by reviewers

Keep the response concise and under 200 words. Focus on actual user experiences, not marketing claims.
```

---

### Detailed Review Summary
**Name:** `review_summary_detailed`
**Query Type:** `review_summary`
**Description:** More comprehensive review analysis with ratings breakdown

**Template:**
```
Analyze user reviews for "{product_name}" by {brand} (UPC: {upc_code}).

Provide a comprehensive summary including:
1. Overall sentiment score (out of 5 stars)
2. Detailed breakdown of pros and cons
3. Most frequently mentioned positive aspects
4. Most frequently mentioned negative aspects
5. Quality consistency (do reviews indicate consistent quality?)
6. Value for money assessment
7. Who this product is best suited for
8. Any safety or health concerns mentioned

Limit response to 400 words. Base your analysis on actual user reviews found online.
```

---

### Review Summary with Comparisons
**Name:** `review_summary_competitive`
**Query Type:** `review_summary`
**Description:** Reviews with competitive context

**Template:**
```
Search for and summarize user reviews of "{product_name}" by {brand} (UPC: {upc_code}).

Include:
- Overall user sentiment
- Key positive and negative points
- How this product compares to similar products in its category
- Unique selling points mentioned by users
- Deal-breakers mentioned by users

Limit to 250 words. Focus on actionable insights for potential buyers.
```

---

## 2. Product Safety & Health Analysis

### Ingredient Safety Analysis
**Name:** `ingredient_safety_analysis`
**Query Type:** `safety_analysis`
**Description:** Analyzes ingredients for health and safety concerns

**Template:**
```
Analyze the ingredients and safety profile of "{product_name}" by {brand}.

Product details:
{additional_data}

Please research and provide:
1. Any potentially harmful ingredients or allergens
2. Safety certifications or warnings
3. Recent recalls or safety issues
4. Regulatory compliance notes
5. Recommendations for who should avoid this product

Be factual and cite sources where possible. Limit to 300 words.
```

---

### Environmental Impact
**Name:** `environmental_impact`
**Query Type:** `sustainability`
**Description:** Evaluates product's environmental footprint

**Template:**
```
Evaluate the environmental impact and sustainability of "{product_name}" by {brand}.

Consider:
- Packaging materials and recyclability
- Manufacturing practices (if known)
- Company's sustainability commitments
- Carbon footprint considerations
- Eco-certifications
- User feedback on environmental aspects

Provide a balanced assessment in under 250 words.
```

---

## 3. Usage & Tips

### Creative Uses
**Name:** `creative_uses`
**Query Type:** `usage_tips`
**Description:** Alternative and creative ways to use the product

**Template:**
```
Find creative and alternative uses for "{product_name}" by {brand} beyond its primary purpose.

Include:
- 5-7 innovative ways people use this product
- Tips from experienced users
- Hacks or life tips
- Unexpected applications
- Best practices for getting the most value

Make it practical and specific. Limit to 200 words.
```

---

### Troubleshooting Guide
**Name:** `troubleshooting_common_issues`
**Query Type:** `troubleshooting`
**Description:** Common problems and solutions

**Template:**
```
Research common problems users experience with "{product_name}" by {brand} and their solutions.

Format as:
- Problem 1: [description] → Solution: [how to fix]
- Problem 2: [description] → Solution: [how to fix]
- Problem 3: [description] → Solution: [how to fix]
(etc.)

Include 5-7 most common issues. Base on actual user experiences. Limit to 300 words.
```

---

## 4. Comparative Analysis

### Product Comparison
**Name:** `compare_alternatives`
**Query Type:** `comparison`
**Description:** Compares product to main competitors

**Template:**
```
Compare "{product_name}" by {brand} to its main competitors in the market.

Provide:
1. Top 3 alternative products
2. How {product_name} differs from each alternative
3. Price comparison
4. Quality comparison
5. Which product is best for different use cases

Be objective and data-driven. Limit to 350 words.
```

---

### Value Assessment
**Name:** `value_for_money`
**Query Type:** `value_analysis`
**Description:** Analyzes if product is worth the price

**Template:**
```
Assess whether "{product_name}" by {brand} (UPC: {upc_code}) offers good value for money.

Consider:
- Current market price range
- Quality vs. price ratio
- Longevity and durability
- Cost per use
- Comparison to cheaper/more expensive alternatives
- User consensus on value

Provide a verdict: Excellent Value / Good Value / Fair Value / Overpriced
Limit to 200 words.
```

---

## 5. Expert & Professional Insights

### Expert Opinions
**Name:** `expert_opinions`
**Query Type:** `expert_analysis`
**Description:** Aggregates expert and professional reviews

**Template:**
```
Search for expert and professional reviews of "{product_name}" by {brand}.

Summarize:
- Expert ratings and scores
- Professional testers' conclusions
- Laboratory or technical test results
- Industry awards or recognition
- Expert recommendations vs. user opinions (any differences?)

Focus on credible sources. Limit to 250 words.
```

---

### Industry Context
**Name:** `industry_context`
**Query Type:** `market_analysis`
**Description:** Product's position in the market

**Template:**
```
Provide market context for "{product_name}" by {brand}.

Include:
- Market segment and positioning
- Target demographic
- Market share or popularity
- Industry trends affecting this product
- Brand reputation in this category
- Future outlook

Keep it informative and factual. Limit to 250 words.
```

---

## 6. Time-Sensitive Queries

### Recent News & Updates
**Name:** `recent_news`
**Query Type:** `news_updates`
**Description:** Recent news and product updates

**Template:**
```
Find the most recent news and updates about "{product_name}" by {brand}.

Include:
- Any recent product recalls or safety alerts
- New versions or formulations
- Company announcements
- Recent notable reviews or media coverage
- Changes in availability or pricing

Only include information from the last 6 months. Limit to 200 words.
```

---

### Price History & Deals
**Name:** `price_trends`
**Query Type:** `pricing`
**Description:** Historical pricing and deal information

**Template:**
```
Research pricing trends and deals for "{product_name}" by {brand} (UPC: {upc_code}).

Provide:
- Current average price
- Historical price range (if available)
- Typical discount periods
- Best places to buy
- Price trend (increasing/stable/decreasing)
- Value compared to 6 months ago

Include actionable buying advice. Limit to 200 words.
```

---

## Template Variable Reference

When creating prompts, you can use these variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `{product_name}` | Product name from database | "Organic Fair Trade Coffee Beans" |
| `{brand}` | Product brand | "Great Coffee Co" |
| `{upc_code}` | UPC/barcode | "012345678901" |
| `{additional_data}` | JSON data from DE Product API | Full product details |

---

## Best Practices for Writing Prompts

### 1. Be Specific
✅ Good: "Summarize user reviews focusing on taste, quality, and value"
❌ Bad: "Tell me about this product"

### 2. Set Response Length
✅ Good: "Limit response to 200 words"
❌ Bad: No length limit (can result in very long/expensive responses)

### 3. Request Structure
✅ Good: "Include: 1. Pros, 2. Cons, 3. Overall sentiment"
❌ Bad: "Tell me pros and cons" (unstructured)

### 4. Specify Sources
✅ Good: "Based on actual user reviews found online"
❌ Bad: No source specification (may get generic information)

### 5. Set Tone
✅ Good: "Be objective and factual. Cite sources where possible."
❌ Bad: No tone guidance (inconsistent results)

### 6. Handle Missing Data
✅ Good: "If brand information is not available, focus on UPC: {upc_code}"
❌ Bad: Assuming all variables always have values

### 7. Avoid Bias
✅ Good: "Provide balanced pros and cons"
❌ Bad: "Why is this product the best?"

---

## Testing Your Prompts

Before deploying a new prompt, test it with:

1. **Various Products:** Test with different product types
2. **Edge Cases:** Products with missing brand, unusual names, etc.
3. **Different Providers:** OpenAI vs. Perplexity may respond differently
4. **Token Usage:** Ensure responses don't exceed your token budget
5. **Response Quality:** Are responses helpful and accurate?

---

## Prompt Versioning Strategy

When updating prompts:

1. Create a new prompt with a version suffix (e.g., `review_summary_v2`)
2. Test the new version in parallel with the old one
3. Compare results and gather feedback
4. Once validated, update the old prompt's `is_active` to `False`
5. Keep old prompts for historical reference

---

## Example: Seeding Prompts in Django

```python
# management/commands/seed_llm_prompts.py
from django.core.management.base import BaseCommand
from api.models import LLMPrompt

class Command(BaseCommand):
    help = 'Seeds initial LLM prompts'

    def handle(self, *args, **options):
        prompts = [
            {
                'name': 'review_summary_basic',
                'description': 'Basic review summary',
                'query_type': 'review_summary',
                'prompt_template': '''Summarize user reviews for the product "{product_name}" by {brand} (UPC: {upc_code}).

Please include:
- Overall sentiment (positive/negative/mixed)
- Common praise points (top 3)
- Common complaints (top 3)
- Key themes mentioned by reviewers

Keep the response concise and under 200 words.''',
                'is_active': True
            },
            # Add more prompts here...
        ]
        
        for prompt_data in prompts:
            LLMPrompt.objects.update_or_create(
                name=prompt_data['name'],
                defaults=prompt_data
            )
        
        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {len(prompts)} prompts'))
```

---

## Provider-Specific Considerations

### OpenAI (ChatGPT)
- **Strengths:** General knowledge, writing quality, instruction following
- **Best For:** Detailed analysis, structured responses, general reviews
- **Token Costs:** Moderate (GPT-4 more expensive than GPT-3.5)

### Perplexity
- **Strengths:** Real-time web search, current information, citations
- **Best For:** Recent reviews, news, price comparisons, current market data
- **Token Costs:** Similar to OpenAI, but includes web search

### Prompt Adaptation
Some prompts may work better with specific providers:
- Use Perplexity for time-sensitive queries (news, prices)
- Use OpenAI for analytical queries (value assessment, comparisons)
- Test both and choose based on response quality

---

## Cost Estimation

Approximate costs per query (as of 2025):

| Model | Cost per 1K tokens (input) | Cost per 1K tokens (output) | Typical Query Cost |
|-------|---------------------------|----------------------------|-------------------|
| GPT-4-Turbo | $0.01 | $0.03 | $0.02 - $0.05 |
| GPT-3.5-Turbo | $0.0005 | $0.0015 | $0.001 - $0.003 |
| Perplexity | ~$0.01 | ~$0.03 | $0.02 - $0.06 |

**Note:** These are estimates. Check current pricing from providers.

With caching:
- First query: Full cost
- Subsequent queries (within TTL): $0 (served from cache)
- Cache hit rate of 80% can reduce costs by 80%

---

## Monitoring Prompt Performance

Track these metrics per prompt:

- **Usage Count:** How often is this prompt used?
- **Average Token Cost:** What does each query cost?
- **Cache Hit Rate:** How often are results reused?
- **Response Quality:** User feedback or manual review
- **Error Rate:** How often does the prompt fail?
- **Average Response Time:** Including API latency

Use this data to optimize prompts and reduce costs.

