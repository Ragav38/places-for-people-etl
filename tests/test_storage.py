import pytest

from chapter_etl.storage.factory import get_storage
from chapter_etl.storage.gcs import GCSStorage
from chapter_etl.storage.local import LocalStorage


def test_local_environment_selects_local_storage(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "local")
    monkeypatch.delenv("GCS_RAW_BUCKET", raising=False)

    storage = get_storage()

    assert isinstance(storage, LocalStorage)


def test_gcp_environment_selects_gcs_storage(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "gcp")
    monkeypatch.setenv("GCS_RAW_BUCKET", "test-raw-bucket")

    class FakeBucket:
        name = "test-raw-bucket"

    class FakeClient:
        def bucket(self, bucket_name):
            assert bucket_name == "test-raw-bucket"
            return FakeBucket()

    monkeypatch.setattr(
        "chapter_etl.storage.gcs.storage.Client",
        lambda: FakeClient(),
    )

    storage = get_storage()

    assert isinstance(storage, GCSStorage)
    assert storage.bucket.name == "test-raw-bucket"


def test_gcp_environment_requires_bucket(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "gcp")
    monkeypatch.delenv("GCS_RAW_BUCKET", raising=False)

    with pytest.raises(
        RuntimeError,
        match="GCS_RAW_BUCKET is required",
    ):
        get_storage()


def test_unsupported_environment_fails(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "unsupported")

    with pytest.raises(
        ValueError,
        match="Unsupported environment",
    ):
        get_storage()


def test_gcs_write_raw_uploads_json_and_returns_uri(monkeypatch):
    import json

    from chapter_etl.storage.gcs import GCSStorage

    class FakeBlob:
        def upload_from_string(self, content, content_type):
            self.content = content
            self.content_type = content_type

    class FakeBucket:
        name = "test-raw-bucket"

        def blob(self, object_name):
            self.object_name = object_name
            self.fake_blob = FakeBlob()
            return self.fake_blob

    class FakeClient:
        def bucket(self, bucket_name):
            assert bucket_name == "test-raw-bucket"
            return fake_bucket

    fake_bucket = FakeBucket()

    monkeypatch.setattr(
        "chapter_etl.storage.gcs.storage.Client",
        lambda: FakeClient(),
    )

    storage = GCSStorage("test-raw-bucket")

    data = {"features": [{"attributes": {"ChapterID": 123}}]}

    uri = storage.write_raw(
        run_id="run-123",
        timestamp_folder="20261101T171837Z",
        page_number=0,
        data=data,
    )

    assert uri == (
        "gs://test-raw-bucket/"
        "raw/2026/11/01/20261101T171837Z_run-123/page_000000.json"
    )
    assert fake_bucket.fake_blob.content_type == "application/json"
    assert json.loads(fake_bucket.fake_blob.content) == data


def test_gcs_read_raw_downloads_and_parses_json(monkeypatch):
    import json

    from chapter_etl.storage.gcs import GCSStorage

    expected_data = {"features": [{"attributes": {"ChapterID": 123}}]}

    class FakeBlob:
        def download_as_text(self, encoding):
            assert encoding == "utf-8"
            return json.dumps(expected_data)

    class FakeBucket:
        name = "test-raw-bucket"

        def blob(self, object_name):
            assert object_name == "raw/test/page_000000.json"
            return FakeBlob()

    class FakeClient:
        def bucket(self, bucket_name):
            return FakeBucket()

    monkeypatch.setattr(
        "chapter_etl.storage.gcs.storage.Client",
        lambda: FakeClient(),
    )

    storage = GCSStorage("test-raw-bucket")

    result = storage.read_raw(
        "gs://test-raw-bucket/raw/test/page_000000.json"
    )

    assert result == expected_data


def test_gcs_read_raw_rejects_uri_from_another_bucket(monkeypatch):
    from chapter_etl.storage.gcs import GCSStorage

    class FakeBucket:
        name = "test-raw-bucket"

    class FakeClient:
        def bucket(self, bucket_name):
            return FakeBucket()

    monkeypatch.setattr(
        "chapter_etl.storage.gcs.storage.Client",
        lambda: FakeClient(),
    )

    storage = GCSStorage("test-raw-bucket")

    with pytest.raises(ValueError, match="does not belong to bucket"):
        storage.read_raw(
            "gs://another-bucket/raw/test/page_000000.json"
        )
