#!/bin/bash
set -e

# GCP Secret Manager Setup Script
# This script creates/updates secrets in GCP Secret Manager

echo "========================================="
echo "GCP Secret Manager Setup Script"
echo "========================================="
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed."
    exit 1
fi

# Prompt for project ID if not set
if [ -z "$GCP_PROJECT_ID" ]; then
    read -p "Enter your GCP Project ID: " GCP_PROJECT_ID
fi

# Prompt for environment
if [ -z "$ENVIRONMENT" ]; then
    read -p "Enter environment (staging/production) [staging]: " ENVIRONMENT
    ENVIRONMENT=${ENVIRONMENT:-staging}
fi

APP_NAME="product-finder"

echo ""
echo "Configuration:"
echo "  Project ID: $GCP_PROJECT_ID"
echo "  Environment: $ENVIRONMENT"
echo ""

# Set the project
gcloud config set project "$GCP_PROJECT_ID"

# Function to create or update a secret
create_or_update_secret() {
    local SECRET_NAME="$1"
    local SECRET_VALUE="$2"
    local DESCRIPTION="$3"
    
    echo "Processing secret: $SECRET_NAME"
    
    # Check if secret exists
    if gcloud secrets describe "$SECRET_NAME" &> /dev/null; then
        echo "  Secret exists, adding new version..."
        echo -n "$SECRET_VALUE" | gcloud secrets versions add "$SECRET_NAME" --data-file=-
    else
        echo "  Creating new secret..."
        echo -n "$SECRET_VALUE" | gcloud secrets create "$SECRET_NAME" \
            --data-file=- \
            --replication-policy="automatic"
    fi
    
    echo "  ✓ Done"
}

# Check if .env file exists
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    echo "Warning: .env file not found. You'll need to enter values manually."
    echo ""
else
    echo "Note: .env file found. You can press Enter to use values from .env or type new ones."
    echo ""
    
    # Safely read .env without sourcing (to avoid bash syntax errors)
    # This just sets defaults, user can override
    if [ -f "$ENV_FILE" ]; then
        while IFS='=' read -r key value; do
            # Skip comments and empty lines
            [[ "$key" =~ ^#.*$ ]] && continue
            [[ -z "$key" ]] && continue
            
            # Remove quotes if present
            value="${value%\"}"
            value="${value#\"}"
            value="${value%\'}"
            value="${value#\'}"
            
            # Export common variables
            case "$key" in
                SECRET_KEY) export SECRET_KEY="$value" ;;
                DE_PRODUCT_APP_KEY) export DE_PRODUCT_APP_KEY="$value" ;;
                DE_PRODUCT_AUTH_KEY) export DE_PRODUCT_AUTH_KEY="$value" ;;
                DE_PRODUCT_API_BASE_URL) export DE_PRODUCT_API_BASE_URL="$value" ;;
                DE_PRODUCT_FIELD_NAMES) export DE_PRODUCT_FIELD_NAMES="$value" ;;
                PERPLEXITY_API_KEY) export PERPLEXITY_API_KEY="$value" ;;
                OPENAI_API_KEY) export OPENAI_API_KEY="$value" ;;
                DEFAULT_LLM_PROVIDER) export DEFAULT_LLM_PROVIDER="$value" ;;
            esac
        done < "$ENV_FILE" 2>/dev/null || true
    fi
fi

echo ""
echo "Creating/updating secrets in GCP Secret Manager..."
echo ""

# Django Secret Key
if [ -n "$SECRET_KEY" ] && [ "$SECRET_KEY" != "your-secret-key-here-generate-a-new-one-for-production" ]; then
    echo "Using SECRET_KEY from .env file"
else
    read -sp "Enter Django SECRET_KEY (or press Enter to generate): " INPUT_SECRET_KEY
    echo ""
    if [ -n "$INPUT_SECRET_KEY" ]; then
        SECRET_KEY="$INPUT_SECRET_KEY"
    else
        # Generate a random secret key
        SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" 2>/dev/null || openssl rand -base64 50)
        echo "Generated new SECRET_KEY"
    fi
fi
create_or_update_secret "${APP_NAME}-${ENVIRONMENT}-django-secret-key" "$SECRET_KEY" "Django secret key"

# DE Product API credentials
if [ -n "$DE_PRODUCT_APP_KEY" ] && [ "$DE_PRODUCT_APP_KEY" != "your-api-key-here" ]; then
    echo "Using DE_PRODUCT_APP_KEY from .env file"
else
    read -p "Enter DE_PRODUCT_APP_KEY: " INPUT_APP_KEY
    if [ -n "$INPUT_APP_KEY" ]; then
        DE_PRODUCT_APP_KEY="$INPUT_APP_KEY"
    fi
fi
create_or_update_secret "${APP_NAME}-${ENVIRONMENT}-de-product-app-key" "$DE_PRODUCT_APP_KEY" "DE Product API app key"

if [ -n "$DE_PRODUCT_AUTH_KEY" ] && [ "$DE_PRODUCT_AUTH_KEY" != "your-api-secret-here" ]; then
    echo "Using DE_PRODUCT_AUTH_KEY from .env file"
else
    read -sp "Enter DE_PRODUCT_AUTH_KEY: " INPUT_AUTH_KEY
    echo ""
    if [ -n "$INPUT_AUTH_KEY" ]; then
        DE_PRODUCT_AUTH_KEY="$INPUT_AUTH_KEY"
    fi
fi
create_or_update_secret "${APP_NAME}-${ENVIRONMENT}-de-product-auth-key" "$DE_PRODUCT_AUTH_KEY" "DE Product API auth key"

# DE Product API Base URL (has default)
DE_PRODUCT_API_BASE_URL=${DE_PRODUCT_API_BASE_URL:-"https://digit-eyes.com/gtin/v3_0/"}
create_or_update_secret "${APP_NAME}-${ENVIRONMENT}-de-product-api-base-url" "$DE_PRODUCT_API_BASE_URL" "DE Product API base URL"

# DE Product Field Names (has default)
DE_PRODUCT_FIELD_NAMES=${DE_PRODUCT_FIELD_NAMES:-"description,uom,usage,brand,language,website,product_web_page,nutrition,formattedNutrition,ingredients,manufacturer,image,thumbnail,categories"}
create_or_update_secret "${APP_NAME}-${ENVIRONMENT}-de-product-field-names" "$DE_PRODUCT_FIELD_NAMES" "DE Product API field names"

# Perplexity API Key
if [ -n "$PERPLEXITY_API_KEY" ] && [ "$PERPLEXITY_API_KEY" != "pplx-your-api-key-here" ]; then
    echo "Using PERPLEXITY_API_KEY from .env file"
else
    read -sp "Enter PERPLEXITY_API_KEY (or leave empty to skip): " INPUT_PERPLEXITY_KEY
    echo ""
    if [ -n "$INPUT_PERPLEXITY_KEY" ]; then
        PERPLEXITY_API_KEY="$INPUT_PERPLEXITY_KEY"
    fi
fi
if [ -n "$PERPLEXITY_API_KEY" ] && [ "$PERPLEXITY_API_KEY" != "pplx-your-api-key-here" ]; then
    create_or_update_secret "${APP_NAME}-${ENVIRONMENT}-perplexity-api-key" "$PERPLEXITY_API_KEY" "Perplexity API key"
else
    create_or_update_secret "${APP_NAME}-${ENVIRONMENT}-perplexity-api-key" "CHANGE_ME" "Perplexity API key"
fi

# OpenAI API Key
if [ -n "$OPENAI_API_KEY" ] && [ "$OPENAI_API_KEY" != "sk-your-api-key-here" ]; then
    echo "Using OPENAI_API_KEY from .env file"
else
    read -sp "Enter OPENAI_API_KEY (or leave empty to skip): " INPUT_OPENAI_KEY
    echo ""
    if [ -n "$INPUT_OPENAI_KEY" ]; then
        OPENAI_API_KEY="$INPUT_OPENAI_KEY"
    fi
fi
if [ -n "$OPENAI_API_KEY" ] && [ "$OPENAI_API_KEY" != "sk-your-api-key-here" ]; then
    create_or_update_secret "${APP_NAME}-${ENVIRONMENT}-openai-api-key" "$OPENAI_API_KEY" "OpenAI API key"
else
    create_or_update_secret "${APP_NAME}-${ENVIRONMENT}-openai-api-key" "CHANGE_ME" "OpenAI API key"
fi

# Default LLM Provider
DEFAULT_LLM_PROVIDER=${DEFAULT_LLM_PROVIDER:-"perplexity"}
create_or_update_secret "${APP_NAME}-${ENVIRONMENT}-default-llm-provider" "$DEFAULT_LLM_PROVIDER" "Default LLM provider"

echo ""
echo "========================================="
echo "Secrets Created Successfully!"
echo "========================================="
echo ""
echo "All secrets have been created/updated in GCP Secret Manager."
echo ""
echo "Note: The database URL secret will be automatically created by Terraform"
echo "when you run 'terraform apply'."
echo ""
echo "Next steps:"
echo "1. Review secrets in GCP Console:"
echo "   https://console.cloud.google.com/security/secret-manager?project=$GCP_PROJECT_ID"
echo ""
echo "2. Run Terraform to create infrastructure:"
echo "   cd terraform"
echo "   terraform plan"
echo "   terraform apply"
echo ""

