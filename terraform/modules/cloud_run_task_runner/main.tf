resource "google_cloud_run_v2_job" "task_runner" {
  name     = var.job_name
  location = var.location

  template {
    template {
      containers {
        image = var.image

        # override ENTRYPOINT
        command = length(var.command) > 0 ? var.command : null

        # override CMD
        args = length(var.args) > 0 ? var.args : null

        # Normal env vars
        dynamic "env" {
          for_each = var.env_vars
          content {
            name  = env.key
            value = env.value
          }
        }

        # Secret env vars
        dynamic "env" {
          for_each = var.secret_env
          content {
            name = env.key
            value_source {
              secret_key_ref {
                secret  = env.value.secret
                version = env.value.version
              }
            }
          }
        }

        resources {
          limits = {
            cpu    = var.cpu
            memory = var.memory
          }
        }

        # Cloud SQL socket mount
        dynamic "volume_mounts" {
          for_each = var.cloudsql_enable_volume ? [1] : []
          content {
            name       = "cloudsql"
            mount_path = "/cloudsql"
          }
        }
      }

      # Attach volume for Cloud SQL Unix socket
      dynamic "volumes" {
        for_each = var.cloudsql_enable_volume && var.cloudsql_connection != null ? [1] : []
        content {
          name = "cloudsql"
          cloud_sql_instance {
            instances = [var.cloudsql_connection]
          }
        }
      }

      # VPC Connector (for private IP DB)
      dynamic "vpc_access" {
        for_each = var.vpc_connector != null ? [1] : []
        content {
          connector = var.vpc_connector
          egress    = "PRIVATE_RANGES_ONLY"
        }
      }

      service_account = var.service_account
      max_retries     = var.max_retries
      timeout         = var.timeout
    }
  }
}
