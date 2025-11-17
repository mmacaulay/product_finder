from django.db import models
from django.urls import reverse


class Product(models.Model):
    upc_code = models.CharField(max_length=12, null=False, unique=True)
    name = models.CharField(max_length=255, null=False)
    brand = models.CharField(max_length=255, null=True, blank=True)
    de_product_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('book-detail', args=[str(self.id)])


class LLMPrompt(models.Model):
    """Template for LLM queries with variable substitution"""
    name = models.CharField(max_length=255, unique=True, help_text="Unique identifier for this prompt")
    description = models.TextField(blank=True, help_text="What this prompt is used for")
    prompt_template = models.TextField(help_text="Prompt text with variables like {product_name}, {brand}, {upc_code}")
    query_type = models.CharField(
        max_length=50,
        help_text="Category of query (e.g., 'review_summary', 'safety_analysis')",
    )
    response_schema = models.JSONField(
        null=True,
        blank=True,
        help_text="Expected JSON schema for the response (optional, for validation)"
    )
    schema_version = models.CharField(
        max_length=20,
        default="1.0",
        help_text="Version of the response schema"
    )
    is_active = models.BooleanField(default=True, help_text="Whether this prompt is currently in use")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['query_type', 'name']
        indexes = [
            models.Index(fields=['query_type', 'is_active']),
        ]
        verbose_name = "LLM Prompt"

    def __str__(self):
        return f"{self.name} ({self.query_type})"

    def render(self, product):
        """Render the prompt template with product data"""
        return self.prompt_template.format(
            product_name=product.name or 'Unknown Product',
            brand=product.brand or 'Unknown Brand',
            upc_code=product.upc_code,
            additional_data=str(product.de_product_data) if product.de_product_data else ''
        )


class LLMQueryResult(models.Model):
    """Cached results from LLM queries"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='llm_results')
    prompt = models.ForeignKey(LLMPrompt, on_delete=models.CASCADE, related_name='results')
    provider = models.CharField(
        max_length=50,
        help_text="LLM provider used (e.g., 'openai', 'perplexity')",
    )
    query_input = models.TextField(help_text="The actual rendered prompt sent to the LLM")
    result = models.JSONField(help_text="The structured JSON response from the LLM")
    schema_version = models.CharField(
        max_length=20,
        default="1.0",
        help_text="Version of the schema used for this response"
    )
    parse_attempts = models.IntegerField(
        default=1,
        help_text="Number of attempts needed to successfully parse the response"
    )
    parse_strategy = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="JSON parsing strategy that succeeded (e.g., 'direct', 'markdown_json', 'markdown_block', 'extract_braces')"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional data like tokens used, model version, cost estimate"
    )
    is_stale = models.BooleanField(
        default=False,
        help_text="Mark for refresh if data is outdated",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'prompt', 'provider']),
            models.Index(fields=['provider']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_stale']),
        ]
        unique_together = ['product', 'prompt', 'provider']
        verbose_name = "LLM Query Result"

    def __str__(self):
        return f"{self.product.name} - {self.prompt.name} ({self.provider})"

    def is_fresh(self, ttl_days=30):
        """Check if the cached result is still fresh"""
        from django.utils import timezone
        from datetime import timedelta
        age = timezone.now() - self.created_at
        return age < timedelta(days=ttl_days) and not self.is_stale