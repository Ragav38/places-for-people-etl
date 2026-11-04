variable "project_id" {
  description = "Google Cloud project ID"
  type        = string
}

variable "region" {
  description = "Google Cloud region for deployment"
  type        = string
  default     = "europe-west2"
}

variable "artifact_registry_repository" {
  description = "Artifact Registry repository name"
  type        = string
  default     = "places-for-people-etl"
}

variable "container_image" {
  description = "Full container image URI including tag"
  type        = string
  default     = null
}

variable "raw_bucket_name" {
  description = "Base name for the raw-data Cloud Storage bucket"
  type        = string
  default     = "places-for-people-etl-raw"
}

variable "db_instance_name" {
  description = "Cloud SQL PostgreSQL instance name"
  type        = string
  default     = "places-for-people-pg"
}

variable "db_name" {
  description = "Application database name"
  type        = string
  default     = "chapters_db"
}

variable "db_user" {
  description = "Application database username"
  type        = string
  default     = "etl_user"
}

variable "db_tier" {
  description = "Cloud SQL machine tier"
  type        = string
  default     = "db-f1-micro"
}

variable "db_password" {
  description = "Application database password"
  type        = string
  sensitive   = true
}
