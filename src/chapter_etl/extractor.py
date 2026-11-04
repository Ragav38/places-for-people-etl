import logging
from datetime import datetime, timezone
from uuid import uuid4

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from chapter_etl.storage.factory import get_storage

logger = logging.getLogger(__name__)

BASE_URL = (
    "https://services2.arcgis.com/5I7u4SJE1vUr79JC/"
    "arcgis/rest/services/UniversityChapters_Public/"
    "FeatureServer/0/query"
)

OUT_FIELDS = "ChapterID,University_Chapter,City,State"
PAGE_SIZE = 1000
TIMEOUT = (5, 30)


def fetch_california_chapters(run_id: str | None = None) -> dict:
    """Fetch California chapters and persist each raw API response."""

    if run_id is None:
        run_id = str(uuid4())

    run_timestamp = datetime.now(timezone.utc)
    timestamp_folder = run_timestamp.strftime("%Y%m%dT%H%M%SZ")

    storage = get_storage()

    saved_files: list[str] = []
    offset = 0
    page_number = 0
    records_extracted = 0

    retry_strategy = Retry(
    total=3,
    connect=3,
    read=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
    )

    with requests.Session() as session:
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        while True:
            params = {
                "where": "State='CA'",
                "outFields": OUT_FIELDS,
                "returnGeometry": "true",
                "outSR": "4326",
                "f": "json",
                "resultOffset": offset,
                "resultRecordCount": PAGE_SIZE,
                "orderByFields": "OBJECTID ASC",
            }

            logger.info("Fetching records from offset %s", offset)

            response = session.get(
                BASE_URL,
                params=params,
                timeout=TIMEOUT,
            )
            response.raise_for_status()

            data = response.json()

            if "error" in data:
                raise RuntimeError(f"ArcGIS API error: {data['error']}")

            page = data.get("features", [])
            records_extracted += len(page)

            raw_path = storage.write_raw(
                run_id=run_id,
                timestamp_folder=timestamp_folder,
                page_number=page_number,
                data=data,
            )
            saved_files.append(raw_path)

            logger.info(
                "Retrieved %s records and saved raw response to %s",
                len(page),
                raw_path,
            )

            if not page or not data.get("exceededTransferLimit", False):
                break

            offset += len(page)
            page_number += 1

    logger.info(
        "Extraction completed. Run ID: %s. Pages saved: %s",
        run_id,
        len(saved_files),
    )

    return {
        "run_id": run_id,
        "raw_files": saved_files,
        "records_extracted": records_extracted,
        "raw_file_count": len(saved_files),
    }
