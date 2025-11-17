"""
Schema definitions and validation for structured LLM responses.

Each query_type has a defined schema that specifies the expected JSON structure.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class FieldDefinition:
    """Definition of a schema field"""
    field_type: type
    required: bool = True
    default: Any = None
    description: str = ""


@dataclass
class ResponseSchema:
    """Schema definition for a query type"""
    query_type: str
    version: str
    fields: Dict[str, FieldDefinition]
    description: str = ""
    
    def get_required_fields(self) -> List[str]:
        """Get list of required field names"""
        return [name for name, defn in self.fields.items() if defn.required]
    
    def get_optional_fields(self) -> List[str]:
        """Get list of optional field names"""
        return [name for name, defn in self.fields.items() if not defn.required]
    
    def get_json_template(self) -> str:
        """Generate a JSON template string for prompts"""
        template = "{\n"
        for name, defn in self.fields.items():
            if defn.field_type == str:
                example = f'"{defn.description or "value"}"'
            elif defn.field_type == float:
                example = "0.85"
            elif defn.field_type == int:
                example = "1"
            elif defn.field_type == bool:
                example = "true"
            elif defn.field_type == list:
                example = '["item1", "item2"]'
            elif defn.field_type == dict:
                example = '{"key": "value"}'
            else:
                example = '"value"'
            
            template += f'  "{name}": {example}'
            if name != list(self.fields.keys())[-1]:
                template += ","
            template += "\n"
        template += "}"
        return template


# Define schemas for each query type
REVIEW_SUMMARY_SCHEMA = ResponseSchema(
    query_type="review_summary",
    version="1.0",
    description="Summary of user reviews for a product",
    fields={
        "sentiment": FieldDefinition(
            field_type=str,
            required=True,
            description="Overall sentiment: positive, negative, or mixed"
        ),
        "sentiment_score": FieldDefinition(
            field_type=float,
            required=True,
            description="Sentiment score from 0.0 (very negative) to 1.0 (very positive)"
        ),
        "summary": FieldDefinition(
            field_type=str,
            required=True,
            description="Brief overview of reviews (under 100 words)"
        ),
        "pros": FieldDefinition(
            field_type=list,
            required=True,
            default=[],
            description="Top 3 positive points from reviews"
        ),
        "cons": FieldDefinition(
            field_type=list,
            required=True,
            default=[],
            description="Top 3 negative points from reviews"
        ),
        "key_themes": FieldDefinition(
            field_type=list,
            required=False,
            default=[],
            description="Main themes mentioned by reviewers"
        ),
        "confidence": FieldDefinition(
            field_type=str,
            required=False,
            default="medium",
            description="Confidence level: high, medium, or low"
        ),
    }
)


SAFETY_ANALYSIS_SCHEMA = ResponseSchema(
    query_type="safety_analysis",
    version="1.0",
    description="Safety and ingredient analysis for a product",
    fields={
        "risk_level": FieldDefinition(
            field_type=str,
            required=True,
            description="Overall risk level: low, medium, or high"
        ),
        "summary": FieldDefinition(
            field_type=str,
            required=True,
            description="Brief safety overview"
        ),
        "harmful_ingredients": FieldDefinition(
            field_type=list,
            required=True,
            default=[],
            description="List of potentially harmful ingredients with details"
        ),
        "allergens": FieldDefinition(
            field_type=list,
            required=True,
            default=[],
            description="List of common allergens present"
        ),
        "certifications": FieldDefinition(
            field_type=list,
            required=False,
            default=[],
            description="Safety certifications or standards met"
        ),
        "recalls": FieldDefinition(
            field_type=list,
            required=False,
            default=[],
            description="Recent recalls or safety issues"
        ),
        "recommendations": FieldDefinition(
            field_type=str,
            required=False,
            default="",
            description="Who should avoid this product"
        ),
        "confidence": FieldDefinition(
            field_type=str,
            required=False,
            default="medium",
            description="Confidence level: high, medium, or low"
        ),
    }
)


# Schema registry - maps query_type to schema
SCHEMA_REGISTRY: Dict[str, ResponseSchema] = {
    "review_summary": REVIEW_SUMMARY_SCHEMA,
    "review_summary_detailed": REVIEW_SUMMARY_SCHEMA,  # Use same schema
    "safety_analysis": SAFETY_ANALYSIS_SCHEMA,
}


def get_schema(query_type: str) -> Optional[ResponseSchema]:
    """
    Get schema for a query type.
    
    Args:
        query_type: The query type identifier
        
    Returns:
        ResponseSchema if found, None otherwise
    """
    return SCHEMA_REGISTRY.get(query_type)


def validate_response(data: dict, schema: ResponseSchema) -> Dict[str, Any]:
    """
    Validate response data against schema with type coercion and defaults.
    
    Args:
        data: The parsed JSON data from LLM
        schema: The schema to validate against
        
    Returns:
        Validated and normalized data dict
        
    Raises:
        ValueError: If required fields are missing or invalid
    """
    validated = {}
    missing_required = []
    
    for field_name, field_def in schema.fields.items():
        if field_name in data:
            value = data[field_name]
            
            # Type coercion
            try:
                if field_def.field_type == float and isinstance(value, (int, str)):
                    value = float(value)
                elif field_def.field_type == int and isinstance(value, (float, str)):
                    value = int(value)
                elif field_def.field_type == str and not isinstance(value, str):
                    value = str(value)
                elif field_def.field_type == bool and isinstance(value, str):
                    value = value.lower() in ('true', 'yes', '1')
                elif field_def.field_type == list and not isinstance(value, list):
                    value = [value] if value else []
            except (ValueError, TypeError):
                if field_def.required:
                    raise ValueError(
                        f"Field '{field_name}' has invalid type. "
                        f"Expected {field_def.field_type.__name__}, got {type(value).__name__}"
                    )
                value = field_def.default
            
            validated[field_name] = value
        else:
            # Missing field
            if field_def.required:
                missing_required.append(field_name)
            else:
                validated[field_name] = field_def.default
    
    if missing_required:
        raise ValueError(
            f"Missing required fields: {', '.join(missing_required)}"
        )
    
    return validated


def list_available_schemas() -> List[str]:
    """Get list of all available query types with schemas"""
    return list(SCHEMA_REGISTRY.keys())

