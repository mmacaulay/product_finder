# Firestore Database Configuration
# Firestore is part of GCP's Always Free Tier (1 GB storage, 50K reads/20K writes per day)

# Note: Firestore database creation must be done via Firebase Console (one-time setup)
# See DEPLOYMENT.md for instructions on creating the Firestore database
# Database name should follow the pattern: ${var.app_name}-${var.environment}
# Example: "product-finder-staging" or "product-finder-production"
# Once created, it doesn't need to be managed in Terraform

# Configuration:
# - Project ID: Uses var.project_id (same as rest of infrastructure)
# - Database name: Configured via FIRESTORE_DATABASE env var in main.tf
# - Required APIs (firestore, firebase, identitytoolkit) are enabled in main.tf
# - IAM permissions (roles/datastore.user) are configured in main.tf
