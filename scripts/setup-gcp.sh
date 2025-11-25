#!/bin/bash
set -e

# GCP Cloud Run Setup Script
# This script prepares your GCP project for deployment

echo "========================================="
echo "GCP Cloud Run Setup Script"
echo "========================================="
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed. Please install it from:"
    echo "https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Prompt for project ID if not set
if [ -z "$GCP_PROJECT_ID" ]; then
    read -p "Enter your GCP Project ID: " GCP_PROJECT_ID
fi

# Prompt for region if not set
if [ -z "$GCP_REGION" ]; then
    read -p "Enter your preferred GCP region (default: us-east1): " GCP_REGION
    GCP_REGION=${GCP_REGION:-us-east1}
fi

# Prompt for GitHub repo
if [ -z "$GITHUB_REPO" ]; then
    read -p "Enter your GitHub repository (format: owner/repo): " GITHUB_REPO
fi

echo ""
echo "Configuration:"
echo "  Project ID: $GCP_PROJECT_ID"
echo "  Region: $GCP_REGION"
echo "  GitHub Repo: $GITHUB_REPO"
echo ""
read -p "Continue with this configuration? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ]; then
    echo "Aborted."
    exit 0
fi

# Set the project
echo ""
echo "Setting GCP project..."
gcloud config set project "$GCP_PROJECT_ID"

# Get project number (required for Workload Identity)
echo "Getting project number..."
GCP_PROJECT_NUMBER=$(gcloud projects describe "$GCP_PROJECT_ID" --format="value(projectNumber)")
echo "Project number: $GCP_PROJECT_NUMBER"

# Enable required APIs
echo ""
echo "Enabling required GCP APIs..."
gcloud services enable \
    run.googleapis.com \
    sqladmin.googleapis.com \
    secretmanager.googleapis.com \
    artifactregistry.googleapis.com \
    vpcaccess.googleapis.com \
    compute.googleapis.com \
    servicenetworking.googleapis.com \
    iamcredentials.googleapis.com \
    iam.googleapis.com \
    cloudresourcemanager.googleapis.com

echo "Waiting for APIs to be fully enabled (30 seconds)..."
sleep 30

# Create Artifact Registry repository
echo ""
echo "Creating Artifact Registry repository..."
REPO_NAME="product-finder-staging"
if gcloud artifacts repositories describe "$REPO_NAME" --location="$GCP_REGION" &> /dev/null; then
    echo "Repository $REPO_NAME already exists."
else
    gcloud artifacts repositories create "$REPO_NAME" \
        --repository-format=docker \
        --location="$GCP_REGION" \
        --description="Docker repository for Product Finder staging"
    echo "Repository created successfully."
fi

# Create service account for Terraform and deployment
echo ""
echo "Creating service account for Terraform/CI..."
SA_NAME="terraform-deploy-sa"
SA_EMAIL="${SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

if gcloud iam service-accounts describe "$SA_EMAIL" &> /dev/null; then
    echo "Service account $SA_EMAIL already exists."
else
    gcloud iam service-accounts create "$SA_NAME" \
        --display-name="Terraform and Deployment Service Account"
    echo "Service account created successfully."
fi

# Grant necessary roles to the service account
echo ""
echo "Granting IAM roles to service account..."
ROLES=(
    "roles/run.admin"
    "roles/cloudsql.admin"
    "roles/secretmanager.admin"
    "roles/artifactregistry.admin"
    "roles/compute.networkAdmin"
    "roles/vpcaccess.admin"
    "roles/iam.serviceAccountUser"
    "roles/iam.serviceAccountAdmin"
    "roles/resourcemanager.projectIamAdmin"
    "roles/servicenetworking.networksAdmin"
)

for ROLE in "${ROLES[@]}"; do
    echo "  Granting $ROLE..."
    gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="$ROLE" \
        --condition=None \
        --quiet || true
done

# Set up Workload Identity Federation for GitHub Actions
echo ""
echo "Setting up Workload Identity Federation for GitHub Actions..."

POOL_NAME="github-actions-pool"
# Note: Workload Identity uses project NUMBER, not project ID
POOL_ID="projects/${GCP_PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_NAME}"
PROVIDER_NAME="github-actions-provider"

# Create Workload Identity Pool
POOL_EXISTS=false
if gcloud iam workload-identity-pools describe "$POOL_NAME" --location="global" &> /dev/null; then
    echo "Workload Identity Pool already exists."
    POOL_EXISTS=true
else
    echo "Creating Workload Identity Pool..."
    gcloud iam workload-identity-pools create "$POOL_NAME" \
        --location="global" \
        --display-name="GitHub Actions Pool"
    echo "Workload Identity Pool creation initiated."
fi

# Wait for pool to be ready with polling
if [ "$POOL_EXISTS" = false ]; then
    echo "Waiting for pool to be ready (this may take 30-60 seconds)..."
    MAX_WAIT=60
    WAITED=0
    while [ $WAITED -lt $MAX_WAIT ]; do
        if gcloud iam workload-identity-pools describe "$POOL_NAME" --location="global" &> /dev/null; then
            echo "Pool is ready!"
            break
        fi
        echo "  Still waiting... ($WAITED/$MAX_WAIT seconds)"
        sleep 5
        WAITED=$((WAITED + 5))
    done
    
    if [ $WAITED -ge $MAX_WAIT ]; then
        echo "Warning: Pool may not be fully ready, but proceeding..."
    fi
    
    # Additional wait for propagation
    echo "Waiting for resource propagation (15 seconds)..."
    sleep 15
fi

# Create Workload Identity Provider
PROVIDER_ID="${POOL_ID}/providers/${PROVIDER_NAME}"
PROVIDER_EXISTS=false
if gcloud iam workload-identity-pools providers describe "$PROVIDER_NAME" \
    --workload-identity-pool="$POOL_NAME" \
    --location="global" &> /dev/null; then
    echo "Workload Identity Provider already exists."
    PROVIDER_EXISTS=true
else
    echo "Creating Workload Identity Provider..."
    gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_NAME" \
        --workload-identity-pool="$POOL_NAME" \
        --location="global" \
        --issuer-uri="https://token.actions.githubusercontent.com" \
        --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
        --attribute-condition="assertion.repository=='${GITHUB_REPO}'"
    echo "Workload Identity Provider creation initiated."
fi

# Wait for provider to be ready with polling
if [ "$PROVIDER_EXISTS" = false ]; then
    echo "Waiting for provider to be ready (this may take 30-60 seconds)..."
    MAX_WAIT=60
    WAITED=0
    while [ $WAITED -lt $MAX_WAIT ]; do
        if gcloud iam workload-identity-pools providers describe "$PROVIDER_NAME" \
            --workload-identity-pool="$POOL_NAME" \
            --location="global" &> /dev/null; then
            echo "Provider is ready!"
            break
        fi
        echo "  Still waiting... ($WAITED/$MAX_WAIT seconds)"
        sleep 5
        WAITED=$((WAITED + 5))
    done
    
    if [ $WAITED -ge $MAX_WAIT ]; then
        echo "Warning: Provider may not be fully ready, but proceeding..."
    fi
    
    # Additional wait for propagation
    echo "Waiting for resource propagation (15 seconds)..."
    sleep 15
fi

# Grant the service account permission to impersonate itself via Workload Identity
echo ""
echo "Configuring Workload Identity bindings..."

# Retry logic for IAM binding (can fail if resources aren't fully propagated)
MAX_RETRIES=3
RETRY_COUNT=0
BINDING_SUCCESS=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ] && [ "$BINDING_SUCCESS" = false ]; do
    if [ $RETRY_COUNT -gt 0 ]; then
        echo "Retry attempt $RETRY_COUNT of $MAX_RETRIES..."
        echo "Waiting 20 seconds for resources to propagate..."
        sleep 20
    fi
    
    if gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
        --role="roles/iam.workloadIdentityUser" \
        --member="principalSet://iam.googleapis.com/${POOL_ID}/attribute.repository/${GITHUB_REPO}"; then
        BINDING_SUCCESS=true
        echo "Workload Identity binding configured successfully!"
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            echo "Binding failed, will retry..."
        fi
    fi
done

if [ "$BINDING_SUCCESS" = false ]; then
    echo ""
    echo "ERROR: Failed to configure Workload Identity binding after $MAX_RETRIES attempts."
    echo "This may be due to resource propagation delays."
    echo ""
    echo "You can manually configure it later by running:"
    echo ""
    echo "gcloud iam service-accounts add-iam-policy-binding $SA_EMAIL \\"
    echo "  --role=\"roles/iam.workloadIdentityUser\" \\"
    echo "  --member=\"principalSet://iam.googleapis.com/${POOL_ID}/attribute.repository/${GITHUB_REPO}\""
    echo ""
    echo "Wait a few minutes and try the command above."
    exit 1
fi

echo ""
echo "Creating GCS bucket for Terraform state..."
STATE_BUCKET="${GCP_PROJECT_ID}-terraform-state"
if gcloud storage buckets describe "gs://${STATE_BUCKET}" &> /dev/null; then
    echo "State bucket already exists."
else
    gcloud storage buckets create "gs://${STATE_BUCKET}" \
        --project="${GCP_PROJECT_ID}" \
        --location="${GCP_REGION}" \
        --uniform-bucket-level-access
    
    # Enable versioning for safety
    gcloud storage buckets update "gs://${STATE_BUCKET}" --versioning
    
    echo "State bucket created."
fi

# Grant service account access to state bucket
echo "Granting service account access to state bucket..."
gcloud storage buckets add-iam-policy-binding "gs://${STATE_BUCKET}" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/storage.objectAdmin" \
    --quiet

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Add these secrets to your GitHub repository:"
echo "   - GCP_PROJECT_ID: $GCP_PROJECT_ID"
echo "   - GCP_REGION: $GCP_REGION"
echo "   - GCP_WORKLOAD_IDENTITY_PROVIDER: ${PROVIDER_ID}"
echo "   - GCP_SERVICE_ACCOUNT: $SA_EMAIL"
echo ""
echo "   Note: The Workload Identity Provider uses project number $GCP_PROJECT_NUMBER"
echo ""
echo "2. Create secrets in GCP Secret Manager:"
echo "   Run: ./scripts/create-secrets.sh"
echo ""
echo "3. Set up Terraform:"
echo "   cd terraform"
echo "   cp terraform.tfvars.example terraform.tfvars"
echo "   # Edit terraform.tfvars with your values"
echo "   terraform init"
echo "   terraform plan"
echo "   terraform apply"
echo ""
echo "4. Once infrastructure is deployed, push to main branch to trigger deployment"
echo ""

