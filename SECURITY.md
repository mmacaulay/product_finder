# Security Notice

## Terraform State Management

**IMPORTANT**: Terraform state files (`*.tfstate`) contain sensitive information including:
- API keys
- Database passwords
- Secret values

### Local Development

These files are gitignored and should NEVER be committed to version control.

### CI/CD (GitHub Actions)

Our GitHub Actions workflows:
1. **Do NOT store terraform state** in the repository
2. **Use minimal logging** (`TF_LOG=ERROR`) to prevent secret exposure
3. **Pass variables via GitHub Secrets**, not files

### Recommended: Remote State Backend

For production, configure GCS backend in `terraform/main.tf`:

```hcl
terraform {
  backend "gcs" {
    bucket = "your-terraform-state-bucket"
    prefix = "terraform/state"
  }
}
```

This will:
- ✅ Store state securely in GCS
- ✅ Enable state locking
- ✅ Allow team collaboration
- ✅ Keep secrets out of GitHub Actions logs

## If an API Key is Leaked

1. **Immediately revoke** the exposed key in the provider's dashboard
2. **Generate a new key**
3. **Update GCP Secret Manager**:
   ```bash
   echo -n "new-key-value" | gcloud secrets versions add SECRET_NAME --data-file=-
   ```
4. **Review GitHub Actions logs** and delete any runs that exposed the key
5. **Check git history** for accidental commits:
   ```bash
   git log --all --full-history -- "*.tfstate" ".env"
   ```

## Secret Management Best Practices

✅ **DO**:
- Store all secrets in GCP Secret Manager
- Use `lifecycle { ignore_changes = [secret_data] }` in Terraform
- Rotate keys regularly
- Use separate keys for staging/production

❌ **DON'T**:
- Commit `.env` files
- Commit `*.tfstate` files
- Print secrets in logs
- Share keys via chat/email
- Use production keys in development

## Reporting Security Issues

If you discover a security vulnerability, please email: [your-email]

Do NOT open a public GitHub issue for security vulnerabilities.

