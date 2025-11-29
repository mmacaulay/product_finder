# Firestore Migration Deployment Guide

This guide covers deploying the Firestore-based application to GCP Cloud Run.

**Note:** The application now uses Firestore + Firebase Auth instead of PostgreSQL + Django Auth.

## Quick Start: Firestore Migration Deployment

### Step 1: Create Firestore Database (One-time)

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Add your GCP project (or select existing)
3. Navigate to **Build → Firestore Database**
4. Click **Create database**
5. Choose **Production mode** (Native mode)
6. Select location: `us-east1` (to match Cloud Run region)
7. Wait for provisioning (~1 minute)

### Step 2: Update Terraform Configuration

Your Terraform still has PostgreSQL resources that need to be removed. You have two options:

**Option A: I'll help you update Terraform** (recommended - let me know and I'll create the updated files)

**Option B: Manual updates** - Remove these resources from `terraform/main.tf`:
- All Cloud SQL resources (`google_sql_*`)
- VPC networking (`google_compute_network`, `google_vpc_access_connector`)
- Database URL secret
- Update Cloud Run to use Firestore environment variables

### Step 3: Deploy

Once Terraform is updated:

```bash
cd terraform
terraform init
terraform plan -out=tfplan
terraform apply tfplan

# Run seed task to populate Firestore
gcloud run jobs execute seed-llm-prompts --region=us-east1
```

### Step 4: Verify

```bash
# Get Cloud Run URL
terraform output cloud_run_url

# Test GraphQL endpoint
curl https://your-service-url/graphql/
```

## Cost Comparison

**Before (PostgreSQL):**
- Cloud SQL: ~$10-50/month
- VPC networking: ~$10/month
- **Total: ~$20-60/month**

**After (Firestore):**
- Firestore: **$0** (Always Free Tier - 1GB storage, 50K reads/20K writes per day)
- Firebase Auth: **$0** (free tier)
- **Total: $0 for low traffic** 🎉

---

## Old Deployment Documentation (Pre-Firestore Migration)

## Prerequisites Checklist

- [ ] GCP account with billing enabled
- [ ] GCP project created
- [ ] `gcloud` CLI installed and authenticated
- [ ] Terraform >= 1.5 installed
- [ ] Docker installed (for local testing)
- [ ] GitHub repository set up
- [ ] API credentials ready:
  - [ ] DE Product API (app key & auth key)
  - [ ] Perplexity API key
  - [ ] OpenAI API key (optional)

## Deployment Steps

### 1. Initial GCP Setup (One-time)

```bash
# Set your configuration
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-east1"
export GITHUB_REPO="your-username/product_finder"

# Run setup script
chmod +x scripts/setup-gcp.sh scripts/create-secrets.sh
./scripts/setup-gcp.sh
```

**What this does:**
- Enables required GCP APIs
- Creates Artifact Registry for Docker images
- Sets up service account with proper permissions
- Configures Workload Identity for GitHub Actions

### 2. Configure GitHub Secrets

Add these secrets to your GitHub repository (Settings → Secrets and variables → Actions):

| Secret Name | Value |
|-------------|-------|
| `GCP_PROJECT_ID` | Your GCP project ID |
| `GCP_REGION` | e.g., `us-east1` |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | From setup script output |
| `GCP_SERVICE_ACCOUNT` | From setup script output |

### 3. Create GCP Secrets

```bash
./scripts/create-secrets.sh
```

This will prompt you for all required API keys and credentials.

### 4. Deploy Infrastructure with Terraform

```bash
cd terraform

# Configure Terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your project details

# Initialize and deploy
terraform init
terraform plan
terraform apply
```

**Wait ~10-15 minutes** for infrastructure to be created.

### 5. Deploy Application

```bash
# Commit and push to main branch
git add .
git commit -m "Initial deployment setup"
git push origin main
```

GitHub Actions will automatically:
1. Build Docker image
2. Push to Artifact Registry
3. Deploy to Cloud Run
4. Run migrations

### 6. Verify Deployment

```bash
# Get your application URL
terraform output cloud_run_url

# Test endpoints
curl https://your-app-url.run.app/admin/
curl https://your-app-url.run.app/graphql
```

## Common Commands

### View Logs

```bash
gcloud run services logs read product-finder-staging --region=us-east1 --limit=50
```

### Update Environment Variables

```bash
gcloud run services update product-finder-staging \
  --region=us-east1 \
  --update-env-vars="KEY=VALUE"
```

### Manual Deployment

```bash
# Build and push
docker build -t us-east1-docker.pkg.dev/PROJECT/product-finder-staging/product-finder:latest .
docker push us-east1-docker.pkg.dev/PROJECT/product-finder-staging/product-finder:latest

# Deploy
gcloud run services update product-finder-staging \
  --image=us-east1-docker.pkg.dev/PROJECT/product-finder-staging/product-finder:latest \
  --region=us-east1
```

### Rollback

```bash
# List revisions
gcloud run revisions list --service=product-finder-staging --region=us-east1

# Rollback to specific revision
gcloud run services update-traffic product-finder-staging \
  --region=us-east1 \
  --to-revisions=REVISION_NAME=100
```

### Destroy Infrastructure

```bash
cd terraform
terraform destroy
```

⚠️ **Warning:** This will delete all data including the database!

## Cost Estimates

**Staging Environment:**
- Cloud Run: $0-5/month (scales to zero when idle)
- Cloud SQL (db-f1-micro): $7-10/month
- Networking & Storage: $1-3/month
- **Total: ~$10-20/month**

## Troubleshooting

### Application won't start

Check logs:
```bash
gcloud run services logs read product-finder-staging --region=us-east1
```

Common issues:
- Database connection problems
- Missing secrets
- Image build failures

### Database connection errors

Verify Cloud SQL and VPC connector:
```bash
gcloud sql instances list
gcloud compute networks vpc-access connectors list --region=us-east1
```

### Secret access denied

Check IAM permissions:
```bash
gcloud secrets list
gcloud secrets get-iam-policy SECRET_NAME
```

## Next Steps

After successful deployment:

1. [ ] Create Django superuser (see main docs)
2. [ ] Test all GraphQL queries
3. [ ] Configure custom domain (optional)
4. [ ] Set up monitoring and alerts
5. [ ] Review security settings
6. [ ] Plan for production environment

## Support

- **Full Documentation**: [docs/deployment/gcp-setup.md](./docs/deployment/gcp-setup.md)
- **GCP Console**: https://console.cloud.google.com
- **Cloud Run**: https://console.cloud.google.com/run
- **GitHub Actions**: Check the Actions tab in your repository

## Files Created

This deployment setup includes:

```
.
├── Dockerfile                              # Container configuration
├── docker-entrypoint.sh                    # Startup script
├── .dockerignore                           # Docker build exclusions
├── requirements.txt                        # Python dependencies
├── terraform/                              # Infrastructure as code
│   ├── main.tf                            # Core infrastructure
│   ├── variables.tf                       # Configuration variables
│   ├── outputs.tf                         # Deployment outputs
│   ├── secrets.tf                         # Secret Manager config
│   └── terraform.tfvars.example           # Configuration template
├── .github/workflows/                      # CI/CD pipelines
│   ├── deploy-staging.yml                 # Deployment workflow
│   ├── terraform-plan.yml                 # Infrastructure preview
│   └── terraform-apply.yml                # Infrastructure deployment
├── scripts/                                # Setup automation
│   ├── setup-gcp.sh                       # GCP project setup
│   └── create-secrets.sh                  # Secret creation
└── docs/deployment/                        # Documentation
    ├── gcp-setup.md                       # Complete guide
    └── README.md                          # Deployment overview
```

