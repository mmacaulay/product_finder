# Deployment Quick Reference

This is a quick reference guide for deploying the Product Finder application to GCP Cloud Run.

For complete documentation, see **[docs/deployment/gcp-setup.md](./docs/deployment/gcp-setup.md)**.

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
export GCP_REGION="us-central1"
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
| `GCP_REGION` | e.g., `us-central1` |
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
gcloud run services logs read product-finder-staging --region=us-central1 --limit=50
```

### Update Environment Variables

```bash
gcloud run services update product-finder-staging \
  --region=us-central1 \
  --update-env-vars="KEY=VALUE"
```

### Manual Deployment

```bash
# Build and push
docker build -t us-central1-docker.pkg.dev/PROJECT/product-finder-staging/product-finder:latest .
docker push us-central1-docker.pkg.dev/PROJECT/product-finder-staging/product-finder:latest

# Deploy
gcloud run services update product-finder-staging \
  --image=us-central1-docker.pkg.dev/PROJECT/product-finder-staging/product-finder:latest \
  --region=us-central1
```

### Rollback

```bash
# List revisions
gcloud run revisions list --service=product-finder-staging --region=us-central1

# Rollback to specific revision
gcloud run services update-traffic product-finder-staging \
  --region=us-central1 \
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
gcloud run services logs read product-finder-staging --region=us-central1
```

Common issues:
- Database connection problems
- Missing secrets
- Image build failures

### Database connection errors

Verify Cloud SQL and VPC connector:
```bash
gcloud sql instances list
gcloud compute networks vpc-access connectors list --region=us-central1
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

