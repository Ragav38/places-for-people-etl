import os
from contextlib import contextmanager

import psycopg
from google.cloud.sql.connector import Connector, IPTypes


@contextmanager
def database_connection():
    """Yield a transactional database connection and clean it up."""

    environment = os.getenv("ENVIRONMENT", "local")
    connector = None
    connection = None

    try:
        if environment == "local":
            database_url = os.getenv("DATABASE_URL")

            if not database_url:
                raise RuntimeError(
                    "DATABASE_URL is required for local execution"
                )

            connection = psycopg.connect(database_url)

        elif environment == "gcp":
            instance_connection_name = os.getenv(
                "INSTANCE_CONNECTION_NAME"
            )
            db_user = os.getenv("DB_USER")
            db_name = os.getenv("DB_NAME")
            db_password = os.getenv("DB_PASSWORD")

            required = {
                "INSTANCE_CONNECTION_NAME": instance_connection_name,
                "DB_USER": db_user,
                "DB_NAME": db_name,
                "DB_PASSWORD": db_password,
            }

            missing = [
                name for name, value in required.items() if not value
            ]

            if missing:
                raise RuntimeError(
                    "Missing required GCP database settings: "
                    + ", ".join(missing)
                )

            connector = Connector()

            connection = connector.connect(
                instance_connection_name,
                "psycopg",
                user=db_user,
                password=db_password,
                db=db_name,
                ip_type=IPTypes.PUBLIC,
            )

        else:
            raise ValueError(
                f"Unsupported environment: {environment}"
            )

        # Commit on success, rollback on exception.
        with connection:
            yield connection

    finally:
        if connection is not None:
            connection.close()

        if connector is not None:
            connector.close()