output "cloud_run_url" {
  description = "URL of the Cloud Run service"
  value       = google_cloud_run_v2_service.app.uri
}

output "cloud_run_service_name" {
  description = "Name of the Cloud Run service"
  value       = google_cloud_run_v2_service.app.name
}

output "database_connection_name" {
  description = "Cloud SQL connection name"
  value       = google_sql_database_instance.postgres.connection_name
}

output "database_instance_name" {
  description = "Cloud SQL instance name"
  value       = google_sql_database_instance.postgres.name
}

output "database_name" {
  description = "Database name"
  value       = google_sql_database.database.name
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.repository_id}"
}

output "docker_image_url" {
  description = "Full Docker image URL for deployment"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.repository_id}/${var.app_name}"
}

output "vpc_connector_id" {
  description = "VPC Access Connector ID"
  value       = google_vpc_access_connector.connector.id
}

output "service_account_email" {
  description = "Service account email for Cloud Run"
  value       = google_service_account.cloud_run_sa.email
}

output "secret_ids" {
  description = "Secret Manager secret IDs"
  value = {
    database_url              = google_secret_manager_secret.database_url.secret_id
    django_secret_key         = google_secret_manager_secret.django_secret_key.secret_id
    django_superuser_username = google_secret_manager_secret.django_superuser_username.secret_id
    django_superuser_email    = google_secret_manager_secret.django_superuser_email.secret_id
    django_superuser_password = google_secret_manager_secret.django_superuser_password.secret_id
    de_product_api_base_url   = google_secret_manager_secret.de_product_api_base_url.secret_id
    de_product_app_key        = google_secret_manager_secret.de_product_app_key.secret_id
    de_product_auth_key       = google_secret_manager_secret.de_product_auth_key.secret_id
    de_product_field_names    = google_secret_manager_secret.de_product_field_names.secret_id
    perplexity_api_key        = google_secret_manager_secret.perplexity_api_key.secret_id
    openai_api_key            = google_secret_manager_secret.openai_api_key.secret_id
    default_llm_provider      = google_secret_manager_secret.default_llm_provider.secret_id
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

