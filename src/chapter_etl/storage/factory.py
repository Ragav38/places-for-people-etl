import os

from chapter_etl.storage.base import RawStorage
from chapter_etl.storage.gcs import GCSStorage
from chapter_etl.storage.local import LocalStorage


def get_storage() -> RawStorage:
    """Select raw storage for the execution environment."""

    environment = os.getenv("ENVIRONMENT", "local")

    if environment == "local":
        return LocalStorage()

    if environment == "gcp":
        bucket_name = os.getenv("GCS_RAW_BUCKET")

        if not bucket_name:
            raise RuntimeError(
                "GCS_RAW_BUCKET is required for GCP execution"
            )

        return GCSStorage(bucket_name)

    raise ValueError(
        f"Unsupported environment: {environment}"
    )
