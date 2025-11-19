#!/bin/bash
set -e

echo "==========================================="
echo "Importing Existing GCP Resources"
echo "==========================================="
echo ""

cd "$(dirname "$0")"

# Import Artifact Registry
echo "1. Importing Artifact Registry..."
terraform import google_artifact_registry_repository.docker_repo \
  "projects/product-finder-478702/locations/northamerica-northeast2/repositories/product-finder-staging" 2>&1 | grep -v "Warning" || echo "  (already imported or error - continuing...)"

# Import secrets (metadata)
echo ""
echo "2. Importing Secret Manager secrets..."

secrets=(
  "django_secret_key"
  "de_product_api_base_url"
  "de_product_app_key"
  "de_product_auth_key"
  "de_product_field_names"
  "perplexity_api_key"
  "openai_api_key"
  "default_llm_provider"
)

for secret in "${secrets[@]}"; do
  echo "  Importing $secret..."
  terraform import "google_secret_manager_secret.$secret" \
    "projects/329270625966/secrets/product-finder-staging-$secret" 2>&1 | grep -v "Warning" || echo "    (already imported or error - continuing...)"
done

# Import secret versions
echo ""
echo "3. Importing Secret Manager secret versions..."

for secret in "${secrets[@]}"; do
  echo "  Importing $secret version..."
  terraform import "google_secret_manager_secret_version.$secret" \
    "projects/329270625966/secrets/product-finder-staging-$secret/versions/latest" 2>&1 | grep -v "Warning" || echo "    (already imported or error - continuing...)"
done

echo ""
echo "==========================================="
echo "Import Complete!"
echo "==========================================="
echo ""
echo "Next steps:"
echo "1. Run: terraform plan"
echo "2. Review the plan (should show new resources, no 'already exists' errors)"
echo "3. Run: terraform apply"
echo ""

