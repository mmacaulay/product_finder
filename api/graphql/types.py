import graphene
from graphene_django import DjangoObjectType
from api.models import Product, LLMPrompt, LLMQueryResult
from api.services.llm import LLMService
import logging

logger = logging.getLogger(__name__)


class LLMInsightType(graphene.ObjectType):
    """LLM-generated insight with metadata"""
    content = graphene.String(description="The LLM-generated content")
    provider = graphene.String(description="The LLM provider used (e.g., 'perplexity', 'openai')")
    cached = graphene.Boolean(description="Whether this result was served from cache")
    generated_at = graphene.DateTime(description="When this insight was generated")
    query_type = graphene.String(description="Type of query (e.g., 'review_summary')")
    
    def resolve_content(self, info):
        return self.get('content', '')
    
    def resolve_provider(self, info):
        return self.get('provider', '')
    
    def resolve_cached(self, info):
        return self.get('cached', False)
    
    def resolve_generated_at(self, info):
        return self.get('generated_at')
    
    def resolve_query_type(self, info):
        return self.get('query_type', '')


class ProductType(DjangoObjectType):
    # Add LLM insight fields
    review_summary = graphene.Field(
        LLMInsightType,
        provider=graphene.String(required=False),
        force_refresh=graphene.Boolean(required=False),
        description="Get a summary of user reviews from the internet"
    )
    
    class Meta:
        model = Product
        fields = (
            'id',
            'upc_code',
            'name',
            'brand',
            'created_at',
            'updated_at',
        )
    
    def resolve_review_summary(self, info, provider=None, force_refresh=False):
        """
        Resolve review summary for this product.
        
        Args:
            provider: Optional LLM provider to use
            force_refresh: If True, bypass cache and query LLM directly
            
        Returns:
            LLMInsightType with content and metadata
        """
        try:
            llm_service = LLMService()
            provider_name = provider or llm_service.default_provider_name
            
            # Get insight from LLM service (handles caching internally)
            result = llm_service.get_product_insight(
                product=self,
                query_type='review_summary',
                provider=provider,
                force_refresh=force_refresh
            )
            
            return {
                'content': result['content'],
                'provider': provider_name,
                'cached': result['cached'],
                'generated_at': result['result_obj'].created_at,
                'query_type': 'review_summary'
            }
            
        except LLMPrompt.DoesNotExist:
            logger.warning("No active 'review_summary' prompt found")
            return None
        except Exception as e:
            logger.error(f"Error resolving review_summary: {e}", exc_info=True)
            return None
