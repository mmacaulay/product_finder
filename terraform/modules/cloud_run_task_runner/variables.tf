variable "job_name" {
  type        = string
  description = "Name of the Cloud Run job."
}

variable "location" {
  type        = string
  description = "Region for the job."
  default     = "us-east1"
}

variable "image" {
  type        = string
  description = "Container image to run."
}

variable "command" {
  type        = list(string)
  description = "Optional command override (ENTRYPOINT)."
  default     = []
}

variable "args" {
  type        = list(string)
  description = "Arguments passed to the container CMD."
  default     = []
}

variable "env_vars" {
  type        = map(string)
  description = "Non-sensitive environment variables."
  default     = {}
}

variable "secret_env" {
  description = <<EOT
Map of environment variables backed by Secret Manager.
Format:
{
  ENV_NAME = {
    secret = "secret-name"
    version = "latest"
  }
}
EOT
  type = map(object({
    secret  = string
    version = string
  }))
  default = {}
}

variable "cloudsql_connection" {
  type        = string
  description = "Optional Cloud SQL INSTANCE connection name (<project>:<region>:<name>)."
  default     = null
}

variable "cloudsql_enable_volume" {
  type        = bool
  description = "If true, mounts the Cloud SQL Unix socket (/cloudsql)."
  default     = false
}

variable "vpc_connector" {
  type        = string
  description = "Optional VPC Access Connector for private IP DB."
  default     = null
}

variable "cpu" {
  type    = string
  default = "1"
}

variable "memory" {
  type    = string
  default = "512Mi"
}

variable "timeout" {
  type    = string
  default = "900s"
}

variable "max_retries" {
  type    = number
  default = 1
}

variable "service_account" {
  type        = string
  description = "Optional service account to use for the job."
  default     = null
}