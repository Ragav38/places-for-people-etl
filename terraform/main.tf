locals {
  container_image = coalesce(
    var.container_image,
    "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_registry_repository}/etl:latest"
  )
}

resource "google_project_service" "required_apis" {
  for_each = toset([
    "artifactregistry.googleapis.com",
    "run.googleapis.com",
    "cloudscheduler.googleapis.com",
    "sqladmin.googleapis.com",
    "storage.googleapis.com",
    "secretmanager.googleapis.com",
    "iam.googleapis.com",
  ])

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "etl" {
  location      = var.region
  repository_id = var.artifact_registry_repository
  description   = "Private container registry for the ETL application"
  format        = "DOCKER"

  depends_on = [
    google_project_service.required_apis
  ]
}

resource "google_storage_bucket" "raw_data" {
  name                        = "${var.project_id}-${var.raw_bucket_name}"
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false

  versioning {
    enabled = true
  }

  depends_on = [
    google_project_service.required_apis
  ]
}

resource "google_service_account" "etl_runtime" {
  account_id   = "places-for-people-etl"
  display_name = "Places for People ETL runtime"

  depends_on = [
    google_project_service.required_apis
  ]
}

resource "google_project_iam_member" "etl_cloud_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.etl_runtime.email}"
}

resource "google_storage_bucket_iam_member" "etl_raw_data_writer" {
  bucket = google_storage_bucket.raw_data.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.etl_runtime.email}"
}

resource "google_sql_database_instance" "postgres" {
  name             = var.db_instance_name
  region           = var.region
  database_version = "POSTGRES_16"

  deletion_protection = true

  settings {
    tier              = var.db_tier
    edition           = "ENTERPRISE"
    activation_policy = "ALWAYS"
    availability_type = "ZONAL"
    disk_type         = "PD_SSD"
    disk_size         = 10
    disk_autoresize   = true

    ip_configuration {
      ipv4_enabled = true
    }

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = false
    }
  }

  depends_on = [
    google_project_service.required_apis
  ]
}

resource "google_sql_database" "chapters" {
  name     = var.db_name
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "etl_user" {
  name     = var.db_user
  instance = google_sql_database_instance.postgres.name

  password_wo         = var.db_password
  password_wo_version = 1
}

resource "google_secret_manager_secret" "db_password" {
  secret_id = "places-for-people-db-password"

  replication {
    auto {}
  }

  depends_on = [
    google_project_service.required_apis
  ]
}

resource "google_secret_manager_secret_version" "db_password" {
  secret                 = google_secret_manager_secret.db_password.id
  secret_data_wo         = var.db_password
  secret_data_wo_version = 1
}

resource "google_secret_manager_secret_iam_member" "etl_db_password_access" {
  secret_id = google_secret_manager_secret.db_password.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.etl_runtime.email}"
}

resource "google_cloud_run_v2_job" "etl" {
  name     = "places-for-people-etl"
  location = var.region

  template {
    template {
      service_account = google_service_account.etl_runtime.email
      timeout         = "1800s"
      max_retries     = 1

      containers {
        image = local.container_image

        env {
          name  = "ENVIRONMENT"
          value = "gcp"
        }

        env {
          name  = "GCS_RAW_BUCKET"
          value = google_storage_bucket.raw_data.name
        }

        env {
          name  = "INSTANCE_CONNECTION_NAME"
          value = google_sql_database_instance.postgres.connection_name
        }

        env {
          name  = "DB_NAME"
          value = var.db_name
        }

        env {
          name  = "DB_USER"
          value = var.db_user
        }

        env {
          name = "DB_PASSWORD"

          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.db_password.secret_id
              version = "latest"
            }
          }
        }
      }
    }
  }

  depends_on = [
    google_project_service.required_apis,
    google_secret_manager_secret_iam_member.etl_db_password_access,
    google_project_iam_member.etl_cloud_sql_client,
    google_secret_manager_secret_version.db_password,
  ]
}

resource "google_service_account" "scheduler" {
  account_id   = "places-for-people-scheduler"
  display_name = "Places for People ETL scheduler"

  depends_on = [
    google_project_service.required_apis
  ]
}

resource "google_cloud_run_v2_job_iam_member" "scheduler_invoker" {
  project  = var.project_id
  location = google_cloud_run_v2_job.etl.location
  name     = google_cloud_run_v2_job.etl.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler.email}"
}

resource "google_cloud_scheduler_job" "daily_etl" {
  name        = "places-for-people-etl-daily"
  description = "Run the California university chapters ETL daily"
  region      = var.region

  # Every day at 06:00 UTC
  schedule  = "0 6 * * *"
  time_zone = "Etc/UTC"

  http_target {
    http_method = "POST"

    uri = "https://run.googleapis.com/v2/projects/${var.project_id}/locations/${var.region}/jobs/${google_cloud_run_v2_job.etl.name}:run"

    body = base64encode("{}")

    headers = {
      "Content-Type" = "application/json"
    }

    oauth_token {
      service_account_email = google_service_account.scheduler.email
      scope                 = "https://www.googleapis.com/auth/cloud-platform"
    }
  }

  depends_on = [
    google_cloud_run_v2_job_iam_member.scheduler_invoker
  ]
}

