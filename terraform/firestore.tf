# Firestore Database Configuration
# Firestore is part of GCP's Always Free Tier (1 GB storage, 50K reads/20K writes per day)

# Note: Firestore database creation must be done via Firebase Console (one-time setup)
# See DEPLOYMENT.md for instructions on creating the Firestore database
# Once created, it doesn't need to be managed in Terraform

# The required APIs (firestore, firebase, identitytoolkit) are enabled in main.tf
# The IAM permissions for Firestore access are also configured in main.tf
