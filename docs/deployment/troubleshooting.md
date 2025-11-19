# Deployment Troubleshooting Guide

## Common Issues and Solutions

### Terraform State Issues

#### Problem: "Resource already exists" errors

**Symptoms:**
- Terraform says resources already exist (Error 409)
- `terraform plan` shows resources need to be created when they already exist in GCP

**Cause:**
- Terraform state got out of sync with actual GCP resources
- Usually happens when resources are created/deleted outside of Terraform
- Or when there are concurrent Terraform operations

**Solution:**
1. Re-import the missing resources:
   ```bash
   cd terraform
   
   # For Cloud Run service
   terraform import google_cloud_run_v2_service.app \
     "projects/PROJECT_ID/locations/REGION/services/SERVICE_NAME"
   
   # For Cloud Run IAM policy
   terraform import google_cloud_run_v2_service_iam_policy.noauth \
     "projects/PROJECT_ID/locations/REGION/services/SERVICE_NAME"
   ```

2. Or refresh the state:
   ```bash
   terraform refresh -var="project_id=PROJECT_ID" -var="region=REGION"
   ```

3. Verify with plan:
   ```bash
   terraform plan -var="project_id=PROJECT_ID" -var="region=REGION"
   ```

### Permission Errors in GitHub Actions

#### Problem: GitHub Actions can't access GCP resources

**Common permission errors:**
- `storage.objects.list` - Missing storage bucket access
- `vpcaccess.connectors.get` - Missing VPC Access permissions
- `secretmanager.versions.access` - Missing Secret Manager access

**Solution:**

Grant missing roles to the service account:

```bash
# Storage (for Terraform state)
gcloud storage buckets add-iam-policy-binding gs://BUCKET_NAME \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role="roles/storage.objectAdmin"

# VPC Access
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role="roles/vpcaccess.admin"

# Secret Manager (usually already granted)
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role="roles/secretmanager.admin"
```

### Static Files Permission Errors

#### Problem: `PermissionError: [Errno 13] Permission denied: '/app/staticfiles'`

**Cause:**
- Docker container switches to non-root user before creating staticfiles directory

**Solution:**
Create the directory with proper permissions before switching users in Dockerfile:

```dockerfile
# Create staticfiles directory with proper permissions
RUN mkdir -p /app/staticfiles && chown -R appuser:appuser /app/staticfiles

# THEN switch to non-root user
USER appuser
```

### Database Connection Failures

#### Problem: Container fails with "Database is unavailable" timeout

**Cause:**
- Cloud Run doesn't have Cloud SQL annotation
- Entrypoint script checking localhost instead of Unix socket

**Solution:**

1. Add Cloud SQL annotation in Terraform:
   ```hcl
   template {
     annotations = {
       "run.googleapis.com/cloudsql-instances" = INSTANCE_CONNECTION_NAME
     }
   }
   ```

2. Update entrypoint to skip localhost check (Cloud SQL uses Unix sockets)

### Startup Probe Failures

#### Problem: "The user-provided container failed the configured startup probe checks"

**Common causes:**
- Database connection timing out
- Application taking too long to start
- Application crashing during startup

**Debug steps:**

1. Check Cloud Run logs:
   ```bash
   gcloud run services logs read SERVICE_NAME --region=REGION --limit=100
   ```

2. Check for specific errors:
   - Database connection issues
   - Missing environment variables
   - Python/Django errors
   - Permission errors

3. Increase probe timeouts if needed (in Terraform):
   ```hcl
   startup_probe {
     initial_delay_seconds = 30  # Increase if needed
     timeout_seconds       = 10  # Increase if needed
     period_seconds        = 10
     failure_threshold     = 3
   }
   ```

### API Key Leaks

#### Problem: API key exposed in logs or git history

**Immediate action:**
1. Revoke the exposed key in the provider's dashboard
2. Generate new key
3. Update Secret Manager:
   ```bash
   echo -n "NEW_KEY" | gcloud secrets versions add SECRET_NAME --data-file=-
   ```

**Prevention:**
- Never commit `.env` files
- Never commit `*.tfstate` files
- Use `TF_LOG=ERROR` in CI/CD to minimize output
- Always use Secret Manager for sensitive values
- Review GitHub Actions logs and delete runs that exposed secrets

### Recovering from Complete State Loss

If Terraform state is completely lost:

1. **Don't panic** - resources still exist in GCP
2. **Option 1: Import everything** (recommended)
   - Use the import script: `terraform/import-existing-resources.sh`
   - Manually import any additional resources

3. **Option 2: Start fresh** (destructive)
   ```bash
   # Delete all GCP resources manually via console
   # Then run terraform apply to recreate
   ```

## Prevention Best Practices

1. **Always use remote state** (GCS backend configured)
2. **Never run terraform locally and in CI/CD simultaneously**
3. **Use state locking** (automatic with GCS backend)
4. **Regular state backups** (versioning enabled on state bucket)
5. **Document manual changes** if you must make them
6. **Test in staging** before applying to production

## Getting Help

If you encounter issues not covered here:

1. Check Terraform output for detailed error messages
2. Check GCP Cloud Run logs
3. Check GitHub Actions logs
4. Search GCP documentation for specific error codes
5. Check Terraform provider issues on GitHub

## Useful Commands

```bash
# View Terraform state
terraform state list
terraform state show RESOURCE_NAME

# Check what Terraform thinks should happen
terraform plan

# Refresh state without making changes
terraform refresh

# Get resource info from GCP
gcloud run services describe SERVICE_NAME --region=REGION
gcloud sql instances describe INSTANCE_NAME
gcloud secrets list

# View logs
gcloud run services logs read SERVICE_NAME --region=REGION
gcloud logging read "resource.type=cloud_run_revision" --limit=50

# Check IAM permissions
gcloud projects get-iam-policy PROJECT_ID
gcloud secrets get-iam-policy SECRET_NAME
```

