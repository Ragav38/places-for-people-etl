output "artifact_registry_repository" {
  description = "Artifact Registry repository name"
  value       = google_artifact_registry_repository.etl.name
}

output "artifact_registry_image_base" {
  description = "Base URI for ETL container images"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_registry_repository}"
}

output "raw_data_bucket_name" {
  description = "Cloud Storage bucket for raw ETL responses"
  value       = google_storage_bucket.raw_data.name
}

output "etl_runtime_service_account" {
  description = "Service account used by the ETL runtime"
  value       = google_service_account.etl_runtime.email
}

output "cloud_sql_instance_connection_name" {
  description = "Cloud SQL connection name for proxy and Cloud Run"
  value       = google_sql_database_instance.postgres.connection_name
}

output "cloud_sql_database_name" {
  description = "Application database name"
  value       = google_sql_database.chapters.name
}