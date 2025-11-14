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
                'description': 'Basic review summary for products',
                'query_type': 'review_summary',
                'prompt_template': '''Summarize user reviews for the product "{product_name}" by {brand} (UPC: {upc_code}).

Please include:
- Overall sentiment (positive/negative/mixed)
- Common praise points (top 3)
- Common complaints (top 3)
- Key themes mentioned by reviewers

Keep the response concise and under 200 words. Focus on actual user experiences found online, not marketing claims.''',
                'is_active': True
            },
            {
                'name': 'review_summary_detailed',
                'description': 'Detailed review analysis with ratings breakdown',
                'query_type': 'review_summary_detailed',
                'prompt_template': '''Analyze user reviews for "{product_name}" by {brand} (UPC: {upc_code}).

Provide a comprehensive summary including:
1. Overall sentiment score
2. Detailed breakdown of pros and cons
3. Most frequently mentioned positive aspects
4. Most frequently mentioned negative aspects
5. Quality consistency (do reviews indicate consistent quality?)
6. Value for money assessment
7. Who this product is best suited for

Limit response to 400 words. Base your analysis on actual user reviews found online.''',
                'is_active': False  # Not active by default
            },
            {
                'name': 'product_safety',
                'description': 'Safety and ingredient analysis',
                'query_type': 'safety_analysis',
                'prompt_template': '''Analyze the safety profile and ingredients of "{product_name}" by {brand}.

Please research and provide:
1. Any potentially harmful ingredients or allergens
2. Safety certifications or warnings
3. Recent recalls or safety issues
4. Regulatory compliance notes
5. Recommendations for who should avoid this product

Be factual and cite sources where possible. Limit to 300 words.''',
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



