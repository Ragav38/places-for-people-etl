import json

from google.cloud import storage

from chapter_etl.storage.base import RawStorage


class GCSStorage(RawStorage):
    """Persist raw API responses directly to Google Cloud Storage."""

    def __init__(self, bucket_name: str):
        if not bucket_name:
            raise ValueError("GCS_RAW_BUCKET is required")

        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)

    def write_raw(
        self,
        run_id: str,
        timestamp_folder: str,
        page_number: int,
        data: dict,
    ) -> str:
        object_name = (
            f"raw/{timestamp_folder[:4]}/"
            f"{timestamp_folder[4:6]}/"
            f"{timestamp_folder[6:8]}/"
            f"{timestamp_folder}_{run_id}/"
            f"page_{page_number:06d}.json"
        )

        blob = self.bucket.blob(object_name)

        blob.upload_from_string(
            json.dumps(data, indent=2, ensure_ascii=False),
            content_type="application/json",
        )

        return f"gs://{self.bucket.name}/{object_name}"

    def read_raw(self, path: str) -> dict:
        prefix = f"gs://{self.bucket.name}/"

        if not path.startswith(prefix):
            raise ValueError(
                f"Raw path does not belong to bucket {self.bucket.name}"
            )

        object_name = path[len(prefix):]
        blob = self.bucket.blob(object_name)

        return json.loads(blob.download_as_text(encoding="utf-8"))
