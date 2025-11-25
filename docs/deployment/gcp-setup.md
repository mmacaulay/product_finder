# GCP Cloud Run Deployment Guide

This guide walks you through deploying the Product Finder application to Google Cloud Platform (GCP) using Cloud Run, Cloud SQL, and Terraform.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Architecture Overview](#architecture-overview)
- [Initial Setup](#initial-setup)
- [Infrastructure Deployment](#infrastructure-deployment)
- [Application Deployment](#application-deployment)
- [Post-Deployment](#post-deployment)
- [Troubleshooting](#troubleshooting)
- [Cost Optimization](#cost-optimization)

## Prerequisites

Before you begin, ensure you have:

1. **GCP Account & Project**
   - Active GCP account with billing enabled
   - A GCP project created
   - Project ID handy

2. **Tools Installed**
   - [gcloud CLI](https://cloud.google.com/sdk/docs/install) (latest version)
   - [Terraform](https://www.terraform.io/downloads) (>= 1.5)
   - [Docker](https://docs.docker.com/get-docker/) (for local testing)
   - [Git](https://git-scm.com/downloads)

3. **GitHub Repository**
   - Repository for this code
   - Admin access to configure secrets

4. **API Credentials**
   - DE Product API credentials (app key & auth key)
   - Perplexity API key (optional)
   - OpenAI API key (optional)

## Architecture Overview

```
┌─────────────────┐
│  GitHub Actions │──── Push to main ────┐
└─────────────────┘                      │
                                         ▼
┌──────────────────────────────────────────────┐
│         Artifact Registry (Docker)           │
└──────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────┐
│            Cloud Run Service                 │
│  ┌────────────────────────────────────────┐  │
│  │  Django + GraphQL + Admin + Gunicorn   │  │
│  │  WhiteNoise (static files)             │  │
│  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
┌──────────────┐       ┌──────────────────┐
│  Cloud SQL   │       │  Secret Manager  │
│  PostgreSQL  │       │  (Credentials)   │
└──────────────┘       └──────────────────┘
```

**Components:**
- **Cloud Run**: Serverless container platform for the Django app
- **Cloud SQL**: Managed PostgreSQL database
- **Secret Manager**: Secure credential storage
- **Artifact Registry**: Docker image repository
- **VPC Connector**: Private connection between Cloud Run and Cloud SQL
- **GitHub Actions**: CI/CD pipeline

## Initial Setup

### Step 1: GCP Project Setup

Run the automated setup script:

```bash
# Set environment variables
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-east1"
export GITHUB_REPO="your-username/product_finder"

# Run setup script
chmod +x scripts/setup-gcp.sh
./scripts/setup-gcp.sh
```

This script will:
- Enable required GCP APIs
- Create Artifact Registry repository
- Create service account for deployments
- Configure Workload Identity Federation for GitHub Actions
- Set up IAM permissions

**Manual Alternative:**

If you prefer manual setup or the script fails:

1. Enable APIs:
```bash
gcloud services enable run.googleapis.com sqladmin.googleapis.com \
  secretmanager.googleapis.com artifactregistry.googleapis.com \
  vpcaccess.googleapis.com compute.googleapis.com \
  servicenetworking.googleapis.com
```

2. Create Artifact Registry:
```bash
gcloud artifacts repositories create product-finder-staging \
  --repository-format=docker \
  --location=us-east1 \
  --description="Docker repository for Product Finder"
```

### Step 2: Configure Secrets

Create secrets in GCP Secret Manager:

```bash
chmod +x scripts/create-secrets.sh
./scripts/create-secrets.sh
```

The script will prompt you for:
- Django SECRET_KEY (or generate one)
- DE Product API credentials
- Perplexity API key
- OpenAI API key

**Verify secrets:**
```bash
gcloud secrets list
```

### Step 3: Configure GitHub Secrets

Add the following secrets to your GitHub repository (Settings > Secrets and variables > Actions):

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `GCP_PROJECT_ID` | Your GCP project ID | e.g., `my-project-123` |
| `GCP_REGION` | Your GCP region | e.g., `us-east1` |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | Full provider ID | From setup script output |
| `GCP_SERVICE_ACCOUNT` | Service account email | From setup script output |

**To add secrets:**
1. Go to GitHub repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add each secret name and value

## Infrastructure Deployment

### Step 1: Configure Terraform

1. Copy the example configuration:
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

2. Edit `terraform.tfvars` with your values:
```hcl
project_id  = "your-gcp-project-id"
region      = "us-east1"
environment = "staging"
```

### Step 2: Initialize Terraform

```bash
terraform init
```

### Step 3: Review Infrastructure Plan

```bash
terraform plan
```

Review the output to see what resources will be created:
- Cloud SQL instance (db-f1-micro)
- Cloud Run service
- VPC network and connector
- Secret Manager secrets
- IAM bindings

### Step 4: Apply Infrastructure

```bash
terraform apply
```

Type `yes` when prompted. This will take **10-15 minutes** as it creates:
- PostgreSQL database
- Network infrastructure
- Service accounts

**Save the outputs:**
```bash
terraform output > terraform-outputs.txt
```

Important outputs:
- `cloud_run_url`: Your application URL
- `artifact_registry_repository`: Docker image repository

### Step 5: Verify Infrastructure

```bash
# Check Cloud Run service
gcloud run services list

# Check Cloud SQL instance
gcloud sql instances list

# Check secrets
gcloud secrets list
```

## Application Deployment

### Automatic Deployment (Recommended)

Once infrastructure is deployed, automatic deployments are triggered by pushing to the `main` branch:

```bash
git add .
git commit -m "Deploy to staging"
git push origin main
```

GitHub Actions will:
1. Build Docker image
2. Push to Artifact Registry
3. Deploy to Cloud Run
4. Run database migrations

Monitor deployment:
- GitHub Actions tab in your repository
- [GCP Cloud Run Console](https://console.cloud.google.com/run)

### Manual Deployment

For testing or troubleshooting:

```bash
# Authenticate Docker with Artifact Registry
gcloud auth configure-docker us-east1-docker.pkg.dev

# Build image
docker build -t us-east1-docker.pkg.dev/YOUR_PROJECT/product-finder-staging/product-finder:latest .

# Push image
docker push us-east1-docker.pkg.dev/YOUR_PROJECT/product-finder-staging/product-finder:latest

# Deploy to Cloud Run
gcloud run services update product-finder-staging \
  --image=us-east1-docker.pkg.dev/YOUR_PROJECT/product-finder-staging/product-finder:latest \
  --region=us-east1
```

## Post-Deployment

### Step 1: Verify Deployment

Get your application URL:
```bash
terraform output cloud_run_url
# OR
gcloud run services describe product-finder-staging --region=us-east1 --format='value(status.url)'
```

Test endpoints:
```bash
# Django admin (should show login page)
curl https://your-app-url.run.app/admin/

# GraphQL endpoint
curl https://your-app-url.run.app/graphql

# Health check
curl https://your-app-url.run.app/admin/login/
```

### Step 2: Create Django Superuser

Connect to Cloud Run to create an admin user:

```bash
# Get Cloud SQL connection name
gcloud sql instances list

# Connect via Cloud SQL Proxy (in one terminal)
cloud-sql-proxy your-project:us-east1:your-instance-name

# In another terminal, use the deployed Cloud Run service to run management command
gcloud run services describe product-finder-staging --region=us-east1 --format='value(status.url)'

# Option 1: Use gcloud run jobs (if configured)
# Option 2: Manually via Cloud SQL proxy and local Django
```

**Easier method - Local with Cloud SQL Proxy:**

```bash
# Install Cloud SQL Proxy
# https://cloud.google.com/sql/docs/postgres/sql-proxy

# Get connection name
INSTANCE_CONNECTION_NAME=$(terraform output -raw database_connection_name)

# Start proxy
./cloud-sql-proxy "$INSTANCE_CONNECTION_NAME"

# In another terminal, with proper DATABASE_URL set:
export DATABASE_URL="postgresql://user:pass@localhost:5432/product_finder"
python manage.py createsuperuser
```

### Step 3: Configure ALLOWED_HOSTS

Update Cloud Run environment variable:

```bash
CLOUD_RUN_URL=$(gcloud run services describe product-finder-staging \
  --region=us-east1 --format='value(status.url)')

# Extract domain
DOMAIN=$(echo $CLOUD_RUN_URL | sed 's|https://||')

# Update Cloud Run service
gcloud run services update product-finder-staging \
  --region=us-east1 \
  --update-env-vars="ALLOWED_HOSTS=$DOMAIN,localhost,127.0.0.1"
```

Or add to Terraform's Cloud Run environment variables.

### Step 4: Test the Application

1. **Django Admin:**
   - Navigate to `https://your-url.run.app/admin/`
   - Log in with superuser credentials

2. **GraphQL API:**
   - Navigate to `https://your-url.run.app/graphql`
   - Try a test query

3. **API Functionality:**
   - Test product lookup
   - Test LLM queries

## Troubleshooting

### Cloud Run Service Not Starting

**Check logs:**
```bash
gcloud run services logs read product-finder-staging --region=us-east1 --limit=50
```

**Common issues:**
- Database connection: Verify VPC connector and Cloud SQL instance are in same region
- Secrets: Ensure all secrets exist and service account has access
- Image: Verify Docker image pushed successfully

### Database Connection Issues

**Verify Cloud SQL:**
```bash
gcloud sql instances describe YOUR_INSTANCE_NAME
```

**Check VPC connector:**
```bash
gcloud compute networks vpc-access connectors list --region=us-east1
```

**Test connection from Cloud Shell:**
```bash
gcloud sql connect YOUR_INSTANCE_NAME --user=product_finder_user --database=product_finder
```

### Secret Access Issues

**List secrets:**
```bash
gcloud secrets list
```

**Check IAM permissions:**
```bash
gcloud secrets get-iam-policy SECRET_NAME
```

**Grant access if needed:**
```bash
gcloud secrets add-iam-policy-binding SECRET_NAME \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role="roles/secretmanager.secretAccessor"
```

### GitHub Actions Deployment Failures

**Check workflow runs:**
- Go to GitHub repository → Actions tab
- Click on failed workflow
- Review logs for each step

**Common issues:**
- Workload Identity not configured: Re-run setup script
- Missing GitHub secrets: Verify all 4 secrets are set
- Insufficient permissions: Check service account IAM roles

### Static Files Not Loading

**Ensure WhiteNoise is configured:**
- Check `MIDDLEWARE` in settings.py
- Verify `STATIC_ROOT` is set
- Run `collectstatic` locally to test

**Debug:**
```bash
# Check if static files were collected in image
docker run -it YOUR_IMAGE ls -la /app/staticfiles/
```

## Cost Optimization

### Staging Environment (~$10-20/month)

Current configuration:
- Cloud Run: Scales to zero when idle (~$0-5/month)
- Cloud SQL (db-f1-micro): ~$7-10/month
- Secret Manager: ~$0.06/10k accesses
- Artifact Registry: ~$0.10/GB/month
- Network egress: Variable

**Tips to reduce costs:**

1. **Delete when not needed:**
```bash
terraform destroy
```

2. **Reduce Cloud SQL tier:**
   - Already using smallest tier (db-f1-micro)
   - Consider shared CPU for even lower cost

3. **Set Cloud Run minimum instances to 0:**
   - Already configured in staging
   - Adds cold start time but saves money

4. **Delete old Docker images:**
```bash
gcloud artifacts docker images list \
  us-east1-docker.pkg.dev/PROJECT/product-finder-staging/product-finder

# Delete old versions
gcloud artifacts docker images delete IMAGE_URL --quiet
```

5. **Monitor costs:**
   - [GCP Billing Console](https://console.cloud.google.com/billing)
   - Set up budget alerts

### Production Environment Considerations

When moving to production:

1. **Database:**
   - Use `db-custom-2-4096` or higher
   - Enable point-in-time recovery
   - Set up automated backups
   - Use REGIONAL availability

2. **Cloud Run:**
   - Increase min instances (1-2) for lower latency
   - Increase memory (2Gi) and CPU (2)
   - Set max instances based on traffic

3. **Monitoring:**
   - Enable Cloud Monitoring
   - Set up alerts for errors and latency
   - Configure log-based metrics

4. **Security:**
   - Use custom domain with Cloud Load Balancer
   - Enable Cloud Armor for DDoS protection
   - Implement proper ALLOWED_HOSTS
   - Review IAM permissions

5. **Caching:**
   - Add Cloud Memorystore (Redis)
   - Implement CDN for static files (Cloud CDN)

## Next Steps

- [ ] Set up custom domain
- [ ] Configure Cloud Monitoring and alerting
- [ ] Implement database backup verification
- [ ] Add Redis for caching
- [ ] Set up staging → production promotion workflow
- [ ] Configure log aggregation and analysis
- [ ] Implement performance monitoring (APM)
- [ ] Set up automated database backups to Cloud Storage

## Support Resources

- [GCP Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud SQL for PostgreSQL](https://cloud.google.com/sql/docs/postgres)
- [Terraform GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)

## Rolling Back

If deployment fails or has issues:

```bash
# List revisions
gcloud run revisions list --service=product-finder-staging --region=us-east1

# Rollback to previous revision
gcloud run services update-traffic product-finder-staging \
  --region=us-east1 \
  --to-revisions=REVISION_NAME=100
```

## Cleanup

To completely remove all infrastructure:

```bash
cd terraform
terraform destroy
```

**Warning:** This will delete all data including the database. Make sure you have backups!

