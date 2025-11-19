import graphene
from graphene_django import DjangoObjectType
from graphene.types.generic import GenericScalar
from api.models import Product, LLMPrompt, LLMQueryResult
from api.services.llm import LLMService
import logging

logger = logging.getLogger(__name__)


class ReviewSummaryType(graphene.ObjectType):
    """Structured review summary data"""
    sentiment = graphene.String(description="Overall sentiment: positive, negative, or mixed")
    sentiment_score = graphene.Float(description="Sentiment score from 0.0 (negative) to 1.0 (positive)")
    summary = graphene.String(description="Brief overview of reviews")
    pros = graphene.List(graphene.String, description="Top positive points from reviews")
    cons = graphene.List(graphene.String, description="Top negative points from reviews")
    key_themes = graphene.List(graphene.String, description="Main themes mentioned")
    confidence = graphene.String(description="Confidence level: high, medium, or low")
    
    # Metadata fields
    provider = graphene.String(description="LLM provider used")
    cached = graphene.Boolean(description="Whether this result was served from cache")
    generated_at = graphene.DateTime(description="When this insight was generated")
    
    def resolve_sentiment(self, info):
        return self.get('sentiment', 'unknown')
    
    def resolve_sentiment_score(self, info):
        return self.get('sentiment_score', 0.5)
    
    def resolve_summary(self, info):
        return self.get('summary', '')
    
    def resolve_pros(self, info):
        return self.get('pros', [])
    
    def resolve_cons(self, info):
        return self.get('cons', [])
    
    def resolve_key_themes(self, info):
        return self.get('key_themes', [])
    
    def resolve_confidence(self, info):
        return self.get('confidence', 'medium')
    
    def resolve_provider(self, info):
        return self.get('_metadata', {}).get('provider', '')
    
    def resolve_cached(self, info):
        return self.get('_metadata', {}).get('cached', False)
    
    def resolve_generated_at(self, info):
        return self.get('_metadata', {}).get('generated_at')


class SafetyAnalysisType(graphene.ObjectType):
    """Structured safety analysis data"""
    risk_level = graphene.String(description="Overall risk level: low, medium, or high")
    summary = graphene.String(description="Brief safety overview")
    harmful_ingredients = graphene.List(GenericScalar, description="List of potentially harmful ingredients")
    allergens = graphene.List(graphene.String, description="Common allergens present")
    certifications = graphene.List(graphene.String, description="Safety certifications or standards")
    recalls = graphene.List(GenericScalar, description="Recent recalls or safety issues")
    recommendations = graphene.String(description="Who should avoid this product")
    confidence = graphene.String(description="Confidence level: high, medium, or low")
    
    # Metadata fields
    provider = graphene.String(description="LLM provider used")
    cached = graphene.Boolean(description="Whether this result was served from cache")
    generated_at = graphene.DateTime(description="When this insight was generated")
    
    def resolve_risk_level(self, info):
        return self.get('risk_level', 'unknown')
    
    def resolve_summary(self, info):
        return self.get('summary', '')
    
    def resolve_harmful_ingredients(self, info):
        return self.get('harmful_ingredients', [])
    
    def resolve_allergens(self, info):
        return self.get('allergens', [])
    
    def resolve_certifications(self, info):
        return self.get('certifications', [])
    
    def resolve_recalls(self, info):
        return self.get('recalls', [])
    
    def resolve_recommendations(self, info):
        return self.get('recommendations', '')
    
    def resolve_confidence(self, info):
        return self.get('confidence', 'medium')
    
    def resolve_provider(self, info):
        return self.get('_metadata', {}).get('provider', '')
    
    def resolve_cached(self, info):
        return self.get('_metadata', {}).get('cached', False)
    
    def resolve_generated_at(self, info):
        return self.get('_metadata', {}).get('generated_at')


class ProductType(DjangoObjectType):
    # Add LLM insight fields with structured types
    review_summary = graphene.Field(
        ReviewSummaryType,
        provider=graphene.String(required=False),
        force_refresh=graphene.Boolean(required=False),
        description="Get a structured summary of user reviews from the internet"
    )
    
    safety_analysis = graphene.Field(
        SafetyAnalysisType,
        provider=graphene.String(required=False),
        force_refresh=graphene.Boolean(required=False),
        description="Get a structured safety analysis for this product"
    )
    
    class Meta:
        model = Product
        fields = (
            'id',
            'upc_code',
            'name',
            'brand',
            'image_url',
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
            ReviewSummaryType with structured data and metadata
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
            
            # Add metadata to response
            content = result['content']
            if isinstance(content, dict):
                content['_metadata'] = {
                    'provider': provider_name,
                    'cached': result['cached'],
                    'generated_at': result['result_obj'].created_at,
                }
                return content
            else:
                # Fallback for error responses
                logger.warning(f"Non-dict content returned: {content}")
                return None
            
        except LLMPrompt.DoesNotExist:
            logger.warning("No active 'review_summary' prompt found")
            return None
        except Exception as e:
            logger.error(f"Error resolving review_summary: {e}", exc_info=True)
            return None
    
    def resolve_safety_analysis(self, info, provider=None, force_refresh=False):
        """
        Resolve safety analysis for this product.
        
        Args:
            provider: Optional LLM provider to use
            force_refresh: If True, bypass cache and query LLM directly
            
        Returns:
            SafetyAnalysisType with structured data and metadata
        """
        try:
            llm_service = LLMService()
            provider_name = provider or llm_service.default_provider_name
            
            # Get insight from LLM service (handles caching internally)
            result = llm_service.get_product_insight(
                product=self,
                query_type='safety_analysis',
                provider=provider,
                force_refresh=force_refresh
            )
            
            # Add metadata to response
            content = result['content']
            if isinstance(content, dict):
                content['_metadata'] = {
                    'provider': provider_name,
                    'cached': result['cached'],
                    'generated_at': result['result_obj'].created_at,
                }
                return content
            else:
                logger.warning(f"Non-dict content returned: {content}")
                return None
            
        except LLMPrompt.DoesNotExist:
            logger.warning("No active 'safety_analysis' prompt found")
            return None
        except Exception as e:
            logger.error(f"Error resolving safety_analysis: {e}", exc_info=True)
            return None
