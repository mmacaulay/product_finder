variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-east1"
}

variable "app_name" {
  description = "Application name (used for resource naming)"
  type        = string
  default     = "product-finder"
}

variable "environment" {
  description = "Environment name (staging, production)"
  type        = string
  default     = "staging"
  
  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Environment must be either 'staging' or 'production'."
  }
}

# Database Configuration
variable "database_version" {
  description = "PostgreSQL version"
  type        = string
  default     = "POSTGRES_15"
}

variable "database_tier" {
  description = "Cloud SQL tier (db-f1-micro for dev/staging, db-custom-* for production)"
  type        = string
  default     = "db-f1-micro"
}

variable "database_disk_size" {
  description = "Database disk size in GB"
  type        = number
  default     = 10
}

variable "database_name" {
  description = "Database name"
  type        = string
  default     = "product_finder"
}

variable "database_user" {
  description = "Database user name"
  type        = string
  default     = "product_finder_user"
}

# Cloud Run Configuration
variable "cloud_run_cpu" {
  description = "CPU allocation for Cloud Run (e.g., '1', '2', '4')"
  type        = string
  default     = "1"
}

variable "cloud_run_memory" {
  description = "Memory allocation for Cloud Run (e.g., '512Mi', '1Gi', '2Gi')"
  type        = string
  default     = "512Mi"
}

variable "cloud_run_max_instances" {
  description = "Maximum number of Cloud Run instances"
  type        = number
  default     = 10
}

variable "cloud_run_allow_unauthenticated" {
  description = "Allow unauthenticated access to Cloud Run service"
  type        = bool
  default     = true
}

variable "log_level" {
  description = "Application log level"
  type        = string
  default     = "INFO"
  
  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], var.log_level)
    error_message = "Log level must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL."
  }
}

# Domain Configuration (optional, for future use)
variable "domain_name" {
  description = "Custom domain name for the application (optional)"
  type        = string
  default     = ""
}