"""
Management command to seed initial LLM prompts.
"""

from django.core.management.base import BaseCommand
from api.models import LLMPrompt


class Command(BaseCommand):
    help = 'Seeds initial LLM prompt templates'

    def handle(self, *args, **options):
        prompts = [
            {
                'name': 'review_summary_basic',
                'description': 'Basic review summary for products with structured JSON output',
                'query_type': 'review_summary',
                'schema_version': '1.0',
                'prompt_template': '''Analyze user reviews for the product "{product_name}" by {brand} (UPC: {upc_code}).

You MUST respond with ONLY valid JSON in this exact format. Do not include markdown, code blocks, or any other text:

{{
  "sentiment": "positive|negative|mixed",
  "sentiment_score": 0.85,
  "summary": "Brief overview of user reviews in under 100 words",
  "pros": ["top positive point 1", "top positive point 2", "top positive point 3"],
  "cons": ["top complaint 1", "top complaint 2", "top complaint 3"],
  "key_themes": ["theme 1", "theme 2"],
  "confidence": "high|medium|low"
}}

Instructions:
- sentiment_score: 0.0 (very negative) to 1.0 (very positive)
- pros/cons: Exactly 3 items each (or fewer if not enough data)
- key_themes: Main recurring topics in reviews
- confidence: Based on number and quality of reviews found
- Focus on actual user experiences, not marketing claims''',
                'is_active': True
            },
            {
                'name': 'review_summary_detailed',
                'description': 'Detailed review analysis with structured JSON output',
                'query_type': 'review_summary_detailed',
                'schema_version': '1.0',
                'prompt_template': '''Perform a comprehensive analysis of user reviews for "{product_name}" by {brand} (UPC: {upc_code}).

You MUST respond with ONLY valid JSON in this exact format:

{{
  "sentiment": "positive|negative|mixed",
  "sentiment_score": 0.85,
  "summary": "Comprehensive overview including quality consistency, value for money, and target audience. Maximum 200 words.",
  "pros": ["detailed positive point 1", "detailed positive point 2", "detailed positive point 3"],
  "cons": ["detailed complaint 1", "detailed complaint 2", "detailed complaint 3"],
  "key_themes": ["theme 1", "theme 2", "theme 3", "theme 4"],
  "confidence": "high|medium|low"
}}

Include in your analysis:
- Quality consistency across reviews
- Value for money assessment
- Who this product is best suited for
- Long-term durability or performance mentions''',
                'is_active': False  # Not active by default
            },
            {
                'name': 'product_safety',
                'description': 'Safety and ingredient analysis with structured JSON output',
                'query_type': 'safety_analysis',
                'schema_version': '1.0',
                'prompt_template': '''Analyze the safety profile and ingredients of "{product_name}" by {brand} (UPC: {upc_code}).

You MUST respond with ONLY valid JSON in this exact format:

{{
  "risk_level": "low|medium|high",
  "summary": "Brief safety overview in under 100 words",
  "harmful_ingredients": [
    {{"name": "ingredient name", "concern": "health concern", "severity": "low|medium|high"}}
  ],
  "allergens": ["allergen 1", "allergen 2"],
  "certifications": ["certification 1", "certification 2"],
  "recalls": [
    {{"date": "YYYY-MM-DD", "reason": "recall reason", "status": "active|resolved"}}
  ],
  "recommendations": "Who should avoid this product and why",
  "confidence": "high|medium|low"
}}

Instructions:
- Be factual and evidence-based
- harmful_ingredients: List any ingredients with known health concerns
- allergens: Common allergens (nuts, dairy, gluten, etc.)
- certifications: Safety certifications, organic labels, etc.
- recalls: Recent safety recalls if any
- confidence: Based on available safety data''',
                'is_active': False  # Not active by default
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for prompt_data in prompts:
            prompt, created = LLMPrompt.objects.update_or_create(
                name=prompt_data['name'],
                defaults=prompt_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created prompt: {prompt.name}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'→ Updated prompt: {prompt.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully seeded {created_count} new and updated {updated_count} existing prompts'
            )
        )



