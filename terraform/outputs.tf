output "cloud_run_url" {
  description = "URL of the Cloud Run service"
  value       = google_cloud_run_v2_service.app.uri
}

output "cloud_run_service_name" {
  description = "Name of the Cloud Run service"
  value       = google_cloud_run_v2_service.app.name
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.repository_id}"
}

output "docker_image_url" {
  description = "Full Docker image URL for deployment"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.repository_id}/${var.app_name}"
}

output "service_account_email" {
  description = "Service account email for Cloud Run"
  value       = google_service_account.cloud_run_sa.email
}

output "secret_ids" {
  description = "Secret Manager secret IDs"
  value = {
    django_secret_key       = google_secret_manager_secret.django_secret_key.secret_id
    de_product_api_base_url = google_secret_manager_secret.de_product_api_base_url.secret_id
    de_product_app_key      = google_secret_manager_secret.de_product_app_key.secret_id
    de_product_auth_key     = google_secret_manager_secret.de_product_auth_key.secret_id
    de_product_field_names  = google_secret_manager_secret.de_product_field_names.secret_id
    perplexity_api_key      = google_secret_manager_secret.perplexity_api_key.secret_id
    openai_api_key          = google_secret_manager_secret.openai_api_key.secret_id
    default_llm_provider    = google_secret_manager_secret.default_llm_provider.secret_id
    firestore_project_id    = google_secret_manager_secret.firestore_project_id.secret_id
    firestore_database      = google_secret_manager_secret.firestore_database.secret_id
  }
}

output "project_id" {
  description = "GCP Project ID"
  value       = var.project_id
}

output "region" {
  description = "GCP Region"
  value       = var.region
}

output "environment" {
  description = "Environment name"
  value       = var.environment
}

