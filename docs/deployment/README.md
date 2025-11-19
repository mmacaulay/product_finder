# Deployment Documentation

This directory contains deployment guides and configuration documentation for the Product Finder application.

## Available Guides

### [GCP Cloud Run Setup](./gcp-setup.md)

Complete guide for deploying to Google Cloud Platform using:
- Cloud Run (serverless containers)
- Cloud SQL (managed PostgreSQL)
- Terraform (infrastructure as code)
- GitHub Actions (CI/CD)

**Topics covered:**
- Initial GCP project setup
- Secret Manager configuration
- Infrastructure provisioning with Terraform
- Automated deployments via GitHub Actions
- Troubleshooting common issues
- Cost optimization strategies
- Production considerations

## Quick Reference

### Prerequisites

- GCP account with billing enabled
- gcloud CLI installed and configured
- Terraform >= 1.5
- Docker (for local testing)
- GitHub repository

### Setup Commands

```bash
# 1. Setup GCP project
./scripts/setup-gcp.sh

# 2. Create secrets
./scripts/create-secrets.sh

# 3. Deploy infrastructure
cd terraform
terraform init
terraform apply

# 4. Deploy application (push to main branch)
git push origin main
```

### Important URLs

After deployment, you'll have:

- **Application**: `https://product-finder-staging-xxx.run.app`
- **Admin Interface**: `https://product-finder-staging-xxx.run.app/admin/`
- **GraphQL API**: `https://product-finder-staging-xxx.run.app/graphql`

### Monitoring & Management

- [Cloud Run Console](https://console.cloud.google.com/run)
- [Cloud SQL Console](https://console.cloud.google.com/sql)
- [Secret Manager](https://console.cloud.google.com/security/secret-manager)
- [Artifact Registry](https://console.cloud.google.com/artifacts)

### Cost Estimates

**Staging Environment:**
- Cloud Run: $0-5/month (scales to zero)
- Cloud SQL (db-f1-micro): $7-10/month
- Networking & Storage: $1-3/month
- **Total: ~$10-20/month**

**Production Environment:**
- Estimated $50-200/month depending on traffic
- See [gcp-setup.md](./gcp-setup.md#cost-optimization) for details

## Architecture Overview

```
GitHub → GitHub Actions → Artifact Registry → Cloud Run
                                                 ↓
                                           Cloud SQL + Secret Manager
```

**Key Features:**
- Zero-downtime deployments
- Automatic scaling (including to zero)
- Secure credential management
- Infrastructure as code
- Automated CI/CD pipeline

## Support

For issues or questions:

1. Check [troubleshooting section](./gcp-setup.md#troubleshooting) in the setup guide
2. Review [GitHub Actions logs](https://github.com/your-repo/actions)
3. Check Cloud Run logs: `gcloud run services logs read product-finder-staging --region=us-central1`

## Future Enhancements

Planned deployment improvements:

- [ ] Multi-environment support (dev, staging, production)
- [ ] Blue-green deployment strategy
- [ ] Cloud Memorystore (Redis) for caching
- [ ] Cloud CDN for static files
- [ ] Custom domain configuration
- [ ] Cloud Armor for DDoS protection
- [ ] Automated database backup verification
- [ ] Performance monitoring (APM)

