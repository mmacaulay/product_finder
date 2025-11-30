# Secret Manager Secrets
# These secrets will be created but need to be populated with actual values
# Use the create-secrets.sh script to populate them

resource "google_secret_manager_secret" "django_secret_key" {
  secret_id = "${var.app_name}-${var.environment}-django-secret-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

# DE Product App Key
resource "google_secret_manager_secret" "de_product_app_key" {
  secret_id = "${var.app_name}-${var.environment}-de-product-app-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "de_product_app_key" {
  secret      = google_secret_manager_secret.de_product_app_key.id
  secret_data = "CHANGE_ME" # Placeholder - update via script

  lifecycle {
    ignore_changes = [secret_data]
  }
}

# DE Product Auth Key
resource "google_secret_manager_secret" "de_product_auth_key" {
  secret_id = "${var.app_name}-${var.environment}-de-product-auth-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "de_product_auth_key" {
  secret      = google_secret_manager_secret.de_product_auth_key.id
  secret_data = "CHANGE_ME" # Placeholder - update via script

  lifecycle {
    ignore_changes = [secret_data]
  }
}

# Perplexity API Key
resource "google_secret_manager_secret" "perplexity_api_key" {
  secret_id = "${var.app_name}-${var.environment}-perplexity-api-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "perplexity_api_key" {
  secret      = google_secret_manager_secret.perplexity_api_key.id
  secret_data = "CHANGE_ME" # Placeholder - update via script

  lifecycle {
    ignore_changes = [secret_data]
  }
}

# OpenAI API Key
resource "google_secret_manager_secret" "openai_api_key" {
  secret_id = "${var.app_name}-${var.environment}-openai-api-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "openai_api_key" {
  secret      = google_secret_manager_secret.openai_api_key.id
  secret_data = "CHANGE_ME" # Placeholder - update via script

  lifecycle {
    ignore_changes = [secret_data]
  }
}

# IAM: Grant Cloud Run service account access to secrets
# Note: Using individual resources instead of for_each to avoid dependency issues during initial apply

resource "google_secret_manager_secret_iam_member" "django_secret_key" {
  secret_id = google_secret_manager_secret.django_secret_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "de_product_app_key" {
  secret_id = google_secret_manager_secret.de_product_app_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "de_product_auth_key" {
  secret_id = google_secret_manager_secret.de_product_auth_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "perplexity_api_key" {
  secret_id = google_secret_manager_secret.perplexity_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "openai_api_key" {
  secret_id = google_secret_manager_secret.openai_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}
