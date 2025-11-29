terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  # GCS backend for state storage - enables state sharing between local and CI/CD
  backend "gcs" {
    bucket = "product-finder-478702-terraform-state"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "firestore.googleapis.com",
    "firebase.googleapis.com",
    "identitytoolkit.googleapis.com"
  ])

  service            = each.value
  disable_on_destroy = false
}

# Artifact Registry for Docker images
resource "google_artifact_registry_repository" "docker_repo" {
  location      = var.region
  repository_id = "${var.app_name}-${var.environment}"
  description   = "Docker repository for ${var.app_name}"
  format        = "DOCKER"

  depends_on = [google_project_service.required_apis]
}

# Service Account for Cloud Run
resource "google_service_account" "cloud_run_sa" {
  account_id   = "${var.app_name}-${var.environment}-cr-sa"
  display_name = "Cloud Run service account for ${var.app_name} ${var.environment}"
}

# IAM: Grant Firestore access
resource "google_project_iam_member" "cloud_run_datastore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Cloud Run Service
resource "google_cloud_run_v2_service" "app" {
  name     = "${var.app_name}-${var.environment}"
  location = var.region

  template {
    containers {
      # Image tag is managed by GitHub Actions deployment
      # Terraform ignores changes to avoid drift on every deploy
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.repository_id}/${var.app_name}:latest"

      ports {
        container_port = 8080
      }

      env {
        name  = "DEBUG"
        value = var.environment == "production" ? "false" : "true"
      }

      env {
        name  = "ALLOWED_HOSTS"
        value = "*" # Will be restricted by Cloud Run's ingress settings
      }

      env {
        name  = "LOG_LEVEL"
        value = var.log_level
      }

      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }

      # Firestore configuration
      env {
        name  = "FIRESTORE_PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }

      env {
        name = "SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.django_secret_key.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "DE_PRODUCT_API_BASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.de_product_api_base_url.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "DE_PRODUCT_APP_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.de_product_app_key.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "DE_PRODUCT_AUTH_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.de_product_auth_key.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "DE_PRODUCT_FIELD_NAMES"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.de_product_field_names.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "PERPLEXITY_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.perplexity_api_key.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "OPENAI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.openai_api_key.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "DEFAULT_LLM_PROVIDER"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.default_llm_provider.secret_id
            version = "latest"
          }
        }
      }

      resources {
        limits = {
          cpu    = var.cloud_run_cpu
          memory = var.cloud_run_memory
        }
        cpu_idle          = true
        startup_cpu_boost = true
      }

      startup_probe {
        http_get {
          path = "/graphql/" # GraphQL endpoint as health check
        }
        initial_delay_seconds = 10
        timeout_seconds       = 3
        period_seconds        = 10
        failure_threshold     = 3
      }

      liveness_probe {
        http_get {
          path = "/graphql/"
        }
        initial_delay_seconds = 30
        timeout_seconds       = 3
        period_seconds        = 30
      }
    }

    max_instance_request_concurrency = 80
    timeout                          = "300s"

    scaling {
      min_instance_count = var.environment == "production" ? 1 : 0
      max_instance_count = var.cloud_run_max_instances
    }

    service_account = google_service_account.cloud_run_sa.email
  }

  # Ignore changes managed outside Terraform
  # - Image tag: managed by GitHub Actions
  # - Annotations: Cloud Run adds additional annotations automatically
  # - Volumes: Cloud Run may add internal volume mounts
  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
      template[0].containers[0].volume_mounts,
      template[0].volumes,
      template[0].annotations,
      client,
      client_version
    ]
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [
    google_project_service.required_apis,
    google_secret_manager_secret_iam_member.de_product_api_base_url,
    google_secret_manager_secret_iam_member.de_product_app_key,
    google_secret_manager_secret_iam_member.de_product_auth_key,
    google_secret_manager_secret_iam_member.de_product_field_names,
    google_secret_manager_secret_iam_member.perplexity_api_key,
    google_secret_manager_secret_iam_member.openai_api_key,
    google_secret_manager_secret_iam_member.default_llm_provider,
    google_project_iam_member.cloud_run_datastore_user
  ]
}

# Make Cloud Run service publicly accessible (or restrict as needed)
data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"
    members = var.cloud_run_allow_unauthenticated ? [
      "allUsers",
    ] : []
  }
}

resource "google_cloud_run_v2_service_iam_policy" "noauth" {
  location    = google_cloud_run_v2_service.app.location
  name        = google_cloud_run_v2_service.app.name
  policy_data = data.google_iam_policy.noauth.policy_data
}

# Seed LLM prompts task
module "seed_llm_prompts" {
  source          = "./modules/cloud_run_task_runner"
  location        = var.region
  service_account = google_service_account.cloud_run_sa.email
  job_name        = "seed-llm-prompts"
  image           = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.repository_id}/${var.app_name}:latest"

  command = ["python"]
  args    = ["manage.py", "seed_llm_prompts"]

  secret_env = {
    SECRET_KEY = {
      secret  = google_secret_manager_secret.django_secret_key.secret_id
      version = "latest"
    }
  }

  env_vars = {
    FIRESTORE_PROJECT_ID = var.project_id
    GOOGLE_CLOUD_PROJECT = var.project_id
  }

  cloudsql_connection    = null
  cloudsql_enable_volume = false
}
