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

  # Uncomment to use GCS backend for state storage
  # backend "gcs" {
  #   bucket = "your-terraform-state-bucket"
  #   prefix = "terraform/state"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "vpcaccess.googleapis.com",
    "compute.googleapis.com",
    "servicenetworking.googleapis.com"
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

# VPC for Cloud SQL
resource "google_compute_network" "vpc" {
  name                    = "${var.app_name}-${var.environment}-vpc"
  auto_create_subnetworks = false
  
  depends_on = [google_project_service.required_apis]
}

resource "google_compute_global_address" "private_ip_address" {
  name          = "${var.app_name}-${var.environment}-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
  
  depends_on = [google_project_service.required_apis]
}

# Serverless VPC Access Connector for Cloud Run
resource "google_vpc_access_connector" "connector" {
  # Name must be <= 25 chars and match pattern ^[a-z][-a-z0-9]{0,23}[a-z0-9]$
  name          = "pf-${var.environment}-connector"  # pf-staging-connector = 20 chars
  region        = var.region
  network       = google_compute_network.vpc.name
  ip_cidr_range = "10.8.0.0/28"
  
  depends_on = [google_project_service.required_apis]
}

# Cloud SQL PostgreSQL Instance
resource "random_id" "db_name_suffix" {
  byte_length = 4
}

resource "google_sql_database_instance" "postgres" {
  name             = "${var.app_name}-${var.environment}-${random_id.db_name_suffix.hex}"
  database_version = var.database_version
  region           = var.region
  
  deletion_protection = var.environment == "production" ? true : false
  
  settings {
    tier              = var.database_tier
    availability_type = var.environment == "production" ? "REGIONAL" : "ZONAL"
    disk_size         = var.database_disk_size
    disk_type         = "PD_SSD"
    
    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = var.environment == "production" ? true : false
      start_time                     = "03:00"
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = var.environment == "production" ? 30 : 7
      }
    }
    
    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
      require_ssl     = true
    }
    
    maintenance_window {
      day          = 7  # Sunday
      hour         = 3
      update_track = "stable"
    }
    
    insights_config {
      query_insights_enabled  = true
      query_string_length     = 1024
      record_application_tags = true
    }
  }
  
  depends_on = [
    google_service_networking_connection.private_vpc_connection,
    google_project_service.required_apis
  ]
}

# Database
resource "google_sql_database" "database" {
  name     = var.database_name
  instance = google_sql_database_instance.postgres.name
}

# Database user
resource "random_password" "db_password" {
  length  = 32
  special = true
}

resource "google_sql_user" "db_user" {
  name     = var.database_user
  instance = google_sql_database_instance.postgres.name
  password = random_password.db_password.result
}

# Store database URL in Secret Manager
resource "google_secret_manager_secret" "database_url" {
  secret_id = "${var.app_name}-${var.environment}-database-url"
  
  replication {
    auto {}
  }
  
  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "database_url" {
  secret = google_secret_manager_secret.database_url.id
  secret_data = format(
    "postgresql://%s:%s@/%s?host=/cloudsql/%s",
    google_sql_user.db_user.name,
    random_password.db_password.result,
    google_sql_database.database.name,
    google_sql_database_instance.postgres.connection_name
  )
}

# Cloud Run Service
resource "google_cloud_run_v2_service" "app" {
  name     = "${var.app_name}-${var.environment}"
  location = var.region
  
  template {
    # Annotations for Cloud SQL connection
    annotations = {
      "run.googleapis.com/cloudsql-instances" = google_sql_database_instance.postgres.connection_name
    }
    
    containers {
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
        value = "*"  # Will be restricted by Cloud Run's ingress settings
      }
      
      env {
        name  = "LOG_LEVEL"
        value = var.log_level
      }
      
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      
      # Database connection via Unix socket
      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.database_url.secret_id
            version = "latest"
          }
        }
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
        cpu_idle = true
        startup_cpu_boost = true
      }
      
      startup_probe {
        http_get {
          path = "/admin/login/"  # Django admin login as health check
        }
        initial_delay_seconds = 10
        timeout_seconds       = 3
        period_seconds        = 10
        failure_threshold     = 3
      }
      
      liveness_probe {
        http_get {
          path = "/admin/login/"
        }
        initial_delay_seconds = 30
        timeout_seconds       = 3
        period_seconds        = 30
      }
    }
    
    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "PRIVATE_RANGES_ONLY"
    }
    
    max_instance_request_concurrency = 80
    timeout                          = "300s"
    
    scaling {
      min_instance_count = var.environment == "production" ? 1 : 0
      max_instance_count = var.cloud_run_max_instances
    }
    
    service_account = google_service_account.cloud_run_sa.email
  }
  
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
  
  depends_on = [
    google_project_service.required_apis,
    google_secret_manager_secret_iam_member.database_url,
    google_secret_manager_secret_iam_member.de_product_api_base_url,
    google_secret_manager_secret_iam_member.de_product_app_key,
    google_secret_manager_secret_iam_member.de_product_auth_key,
    google_secret_manager_secret_iam_member.de_product_field_names,
    google_secret_manager_secret_iam_member.perplexity_api_key,
    google_secret_manager_secret_iam_member.openai_api_key,
    google_secret_manager_secret_iam_member.default_llm_provider
  ]
}

# Service Account for Cloud Run
resource "google_service_account" "cloud_run_sa" {
  account_id   = "${var.app_name}-${var.environment}-cr-sa"
  display_name = "Cloud Run service account for ${var.app_name} ${var.environment}"
}

# IAM: Cloud SQL Client
resource "google_project_iam_member" "cloud_run_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
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
  location = google_cloud_run_v2_service.app.location
  name     = google_cloud_run_v2_service.app.name
  policy_data = data.google_iam_policy.noauth.policy_data
}

