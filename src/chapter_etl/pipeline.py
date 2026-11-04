
import logging
from uuid import uuid4

from chapter_etl.audit import start_run, complete_run, fail_run
from chapter_etl.extractor import fetch_california_chapters
from chapter_etl.loader import load_chapters
from chapter_etl.transformer import transform_raw_files

logger = logging.getLogger(__name__)


def run_pipeline(run_id: str | None = None, dag_id: str | None = None) -> dict:
    """Execute the ETL pipeline and maintain run-level audit information."""

    run_id = run_id or str(uuid4())
    audit_started = False

    try:
        start_run(run_id, dag_id)
        audit_started = True

        extraction = fetch_california_chapters(run_id)
        records_extracted = extraction["records_extracted"]
        raw_files = extraction["raw_files"]
        raw_file_count = extraction["raw_file_count"]

        chapters = transform_raw_files(raw_files)
        records_transformed = len(chapters)

        records_loaded = load_chapters(chapters, run_id)

        complete_run(
            run_id=run_id,
            records_extracted=records_extracted,
            records_transformed=records_transformed,
            records_loaded=records_loaded,
            raw_file_count=raw_file_count,
        )

        logger.info("ETL run %s completed successfully", run_id)

        return {
            "run_id": run_id,
            "records_extracted": records_extracted,
            "records_transformed": records_transformed,
            "records_loaded": records_loaded,
            "raw_file_count": raw_file_count,
        }

    except Exception as exc:
        logger.exception("ETL run %s failed", run_id)

        if audit_started:
            try:
                fail_run(run_id, str(exc))
            except Exception:
                logger.exception(
                    "Could not update failure audit for run %s",
                    run_id,
                )

        raise
