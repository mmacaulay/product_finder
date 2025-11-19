# Secret Manager Secrets
# These secrets will be created but need to be populated with actual values
# Use the create-secrets.sh script to populate them

# Django Secret Key
resource "google_secret_manager_secret" "django_secret_key" {
  secret_id = "${var.app_name}-${var.environment}-django-secret-key"
  
  replication {
    auto {}
  }
  
  depends_on = [google_project_service.required_apis]
}

# Note: Secret version for django_secret_key is managed outside Terraform
# The secret value was created by create-secrets.sh and should not be managed by Terraform

resource "random_id" "secret_placeholder" {
  byte_length = 16
}

# DE Product API Base URL
resource "google_secret_manager_secret" "de_product_api_base_url" {
  secret_id = "${var.app_name}-${var.environment}-de-product-api-base-url"
  
  replication {
    auto {}
  }
  
  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "de_product_api_base_url" {
  secret = google_secret_manager_secret.de_product_api_base_url.id
  secret_data = "https://digit-eyes.com/gtin/v3_0/"
  
  lifecycle {
    ignore_changes = [secret_data]
  }
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
  secret = google_secret_manager_secret.de_product_app_key.id
  secret_data = "CHANGE_ME"  # Placeholder - update via script
  
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
  secret = google_secret_manager_secret.de_product_auth_key.id
  secret_data = "CHANGE_ME"  # Placeholder - update via script
  
  lifecycle {
    ignore_changes = [secret_data]
  }
}

# DE Product Field Names
resource "google_secret_manager_secret" "de_product_field_names" {
  secret_id = "${var.app_name}-${var.environment}-de-product-field-names"
  
  replication {
    auto {}
  }
  
  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "de_product_field_names" {
  secret = google_secret_manager_secret.de_product_field_names.id
  secret_data = "description,uom,usage,brand,language,website,product_web_page,nutrition,formattedNutrition,ingredients,manufacturer,image,thumbnail,categories"
  
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
  secret = google_secret_manager_secret.perplexity_api_key.id
  secret_data = "CHANGE_ME"  # Placeholder - update via script
  
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
  secret = google_secret_manager_secret.openai_api_key.id
  secret_data = "CHANGE_ME"  # Placeholder - update via script
  
  lifecycle {
    ignore_changes = [secret_data]
  }
}

# Default LLM Provider
resource "google_secret_manager_secret" "default_llm_provider" {
  secret_id = "${var.app_name}-${var.environment}-default-llm-provider"
  
  replication {
    auto {}
  }
  
  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "default_llm_provider" {
  secret = google_secret_manager_secret.default_llm_provider.id
  secret_data = "perplexity"
  
  lifecycle {
    ignore_changes = [secret_data]
  }
}

# IAM: Grant Cloud Run service account access to secrets
# Note: Using individual resources instead of for_each to avoid dependency issues during initial apply

resource "google_secret_manager_secret_iam_member" "database_url" {
  secret_id = google_secret_manager_secret.database_url.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Note: IAM binding for django_secret_key managed outside Terraform
# The secret was created before Terraform, so IAM is also managed externally

resource "google_secret_manager_secret_iam_member" "de_product_api_base_url" {
  secret_id = google_secret_manager_secret.de_product_api_base_url.secret_id
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

resource "google_secret_manager_secret_iam_member" "de_product_field_names" {
  secret_id = google_secret_manager_secret.de_product_field_names.secret_id
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

resource "google_secret_manager_secret_iam_member" "default_llm_provider" {
  secret_id = google_secret_manager_secret.default_llm_provider.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

