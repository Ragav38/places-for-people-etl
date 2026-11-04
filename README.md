# California University Chapters ETL

An end-to-end ETL pipeline that extracts University Chapter data from the Ducks Unlimited ArcGIS API, filters chapters located in California, and loads the results into PostgreSQL.

The solution includes raw-data persistence, data transformation, idempotent database loading, run-level audit logging, local orchestration with Apache Airflow, cloud deployment on Google Cloud Platform (GCP), infrastructure as code using Terraform, and CI/CD through GitHub Actions.

## 1. Solution Overview

### Data Flow

    Ducks Unlimited ArcGIS API
              |
              v
           Extract
              |
              +----> Persist raw API response as JSON
              |
              v
          Transform
      - Filter California
      - Select required fields
      - Validate and normalise records
              |
              v
          PostgreSQL
      - university_chapters
      - etl_run_audit
              |
              v
         Run-level audit

### Cloud Architecture

    GitHub Repository
           |
           | Push to main
           v
    GitHub Actions
           |
           | Workload Identity Federation (OIDC)
           v
    Google Cloud
      - Artifact Registry: container image
      - Cloud Run Job: ETL execution
      - Cloud SQL for PostgreSQL: target database
      - Cloud Scheduler: daily trigger
      - Cloud Storage: raw-data storage
      - Secret Manager: database credentials

GitHub Actions authenticates to GCP using Workload Identity Federation. No service-account JSON key is stored in GitHub.

## 2. Data Source and Transformation

The source is the Ducks Unlimited University Chapters ArcGIS dataset:

https://gis.ducks.org/datasets/du-university-chapters/api

The pipeline filters records to California and selects the required chapter attributes:

- Chapter ID
- Chapter name
- City
- State
- Latitude
- Longitude

The target table is `university_chapters`. The chapter ID is the primary key, and the loader uses an UPSERT so that rerunning the pipeline does not create duplicate chapter records.

## 3. Repository Structure

    .
    ├── .github/
    │   └── workflows/
    │       └── deploy-gcp.yml
    ├── dags/
    │   └── university_chapters_dag.py
    ├── sql/
    │   ├── schema.sql
    │   └── audit_schema.sql
    ├── src/
    │   └── chapter_etl/
    │       ├── audit.py
    │       ├── database.py
    │       ├── extractor.py
    │       ├── loader.py
    │       ├── main.py
    │       ├── pipeline.py
    │       └── transformer.py
    ├── terraform/
    │   ├── main.tf
    │   ├── outputs.tf
    │   ├── variables.tf
    │   ├── versions.tf
    │   └── terraform.tfvars.example
    ├── tests/
    │   ├── test_audit.py
    │   ├── test_storage.py
    │   └── test_transformer.py
    ├── Dockerfile
    ├── Dockerfile.airflow
    ├── docker-compose.yml
    ├── pyproject.toml
    ├── .env.example
    └── README.md

Local environment files, Terraform state, generated plans, raw data, logs, and virtual environments are excluded from version control.

## 4. Local Development

### Prerequisites

- Python
- Docker and Docker Compose
- PostgreSQL client (`psql`) for database verification
- Git

### Configure the Environment

Clone the repository and enter the project directory:

    git clone https://github.com/Ragav38/places-for-people-etl.git
    cd places-for-people-etl

Create a virtual environment and install the project:

    python -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -e .

Create a local environment file from the example:

    cp .env.example .env

Set the required local database and application values in `.env`. Do not commit this file.

### Run the Tests

    pytest

### Run PostgreSQL and Airflow Locally

Start the services:

    docker compose up -d

The Airflow DAG is named `university_chapters_dag`. It is configured for a daily schedule at 06:00 UTC, with catchup disabled and one active run at a time.

The Airflow web interface is available at:

http://localhost:8080

Use the credentials configured in your local Compose environment.

Stop the services:

    docker compose down

## 5. Database Schema and Audit

The database schemas are defined in:

- `sql/schema.sql`
- `sql/audit_schema.sql`

### `university_chapters`

Stores the California chapter records, including chapter ID, name, city, state, latitude, longitude, and timestamps.

The chapter ID is the primary key. The loader performs an UPSERT to support repeatable runs.

### `etl_run_audit`

Stores run-level audit information, including:

- Run ID and DAG ID
- Start and finish timestamps
- Run status
- Extracted, transformed, and loaded record counts
- Number of raw files persisted
- Error message, when applicable

This allows each run to be monitored and reconciled.

## 6. Raw Data Persistence

The API response is persisted as JSON before transformation. Raw files are organised by date and run identifier, making it possible to inspect the source data associated with a particular execution.

Example local layout:

    data/
    └── raw/
        └── YYYY/
            └── MM/
                └── DD/
                    └── <run_id>/
                        └── page_000000.json

The cloud deployment uses the configured Cloud Storage bucket for raw-data persistence.

## 7. GCP Deployment

The cloud infrastructure is provisioned with Terraform in the `terraform/` directory.

The deployed solution uses:

- Cloud Run Jobs for ETL execution
- Cloud SQL for PostgreSQL as the target database
- Artifact Registry for the container image
- Cloud Storage for raw data
- Secret Manager for sensitive configuration
- Cloud Scheduler for the daily trigger
- Service accounts and IAM for access control

### Terraform

From the `terraform/` directory:

    terraform init
    terraform validate
    terraform plan
    terraform apply

Review the plan before applying it. Configure deployment-specific values using `terraform.tfvars`, created from the supplied example. Do not commit `terraform.tfvars`, Terraform state, or plan files.

### Cloud Run Job

The Cloud Run Job is named:

    places-for-people-etl

The configured region is:

    europe-west2

Execute the job manually:

    gcloud run jobs execute places-for-people-etl \
      --region=europe-west2 \
      --project=places-for-people-etl-project \
      --wait

## 8. CI/CD with GitHub Actions

The workflow is:

    .github/workflows/deploy-gcp.yml

It runs on pushes to `main` and supports manual execution through `workflow_dispatch`.

The workflow:

1. Checks out the repository.
2. Authenticates to GCP using GitHub OIDC and Workload Identity Federation.
3. Configures Docker authentication for Artifact Registry.
4. Builds the container image.
5. Pushes the image tagged with the Git commit SHA.
6. Updates the Cloud Run Job to use the new image.

The workflow uses the repository's configured GCP project, region, Artifact Registry repository, Cloud Run Job, and federated service account.

No long-lived service-account key is required in GitHub.

## 9. Scheduling and Monitoring

The cloud job is configured to run daily at 06:00 UTC using Cloud Scheduler.

Each execution writes an audit record to `etl_run_audit`. The audit record can be used to verify the run status, reconcile record counts, and investigate failures.

Cloud Run execution logs are available through Google Cloud Logging.

## 10. Validation

The solution was validated through local testing and cloud execution.

### GitHub Actions Deployment

The GitHub Actions workflow completed successfully after a push to `main`. The workflow built and pushed the container image and updated the Cloud Run Job.

### Cloud Run Execution

A manual execution of the deployed job completed successfully.

### Cloud SQL Audit Verification

The latest verified audit record contained:

| Metric | Result |
|---|---:|
| Status | SUCCESS |
| Records extracted | 3 |
| Records transformed | 3 |
| Records loaded | 3 |
| Raw files persisted | 1 |
| Error message | NULL |

The audit record confirms that all three extracted records were transformed and loaded, with no recorded error.

## 11. Security and Repository Hygiene

- GitHub Actions uses Workload Identity Federation rather than a service-account key.
- Database credentials are supplied through environment configuration and Secret Manager.
- `.env` and `terraform.tfvars` are excluded from Git.
- Terraform state, backups, and generated plan files are excluded from Git.
- Local editor settings, virtual environments, raw data, logs, and generated files are excluded from Git.

## 12. Potential Improvements

Possible next steps include:

- Add retry and backoff handling for transient API and database errors.
- Add data-quality checks for missing IDs, invalid coordinates, and duplicate records.
- Add alerting for failed or missed scheduled executions.
- Add retention policies for raw data and audit records.
- Separate deployment and runtime service accounts for stricter production IAM boundaries.
- Add integration tests against an ephemeral PostgreSQL instance.
