import logging
from datetime import datetime, timezone

from chapter_etl.database import database_connection

logger = logging.getLogger(__name__)


def start_run(run_id: str, dag_id: str | None = None) -> None:
    """Create an audit record when an ETL run starts."""

    query = """
        INSERT INTO etl_run_audit (
            run_id,
            dag_id,
            started_at,
            status
        )
        VALUES (%s, %s, %s, 'RUNNING')
        ON CONFLICT (run_id) DO NOTHING;
    """

    with database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                query,
                (run_id, dag_id, datetime.now(timezone.utc)),
            )

    logger.info("Started audit record for run %s", run_id)


def complete_run(
    run_id: str,
    records_extracted: int,
    records_transformed: int,
    records_loaded: int,
    raw_file_count: int,
) -> None:
    """Mark a run as successful and record its processing counts."""

    query = """
        UPDATE etl_run_audit
        SET
            finished_at = %s,
            status = 'SUCCESS',
            records_extracted = %s,
            records_transformed = %s,
            records_loaded = %s,
            raw_file_count = %s,
            error_message = NULL
        WHERE run_id = %s
          AND status = 'RUNNING';
    """

    with database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                query,
                (
                    datetime.now(timezone.utc),
                    records_extracted,
                    records_transformed,
                    records_loaded,
                    raw_file_count,
                    run_id,
                ),
            )

            if cursor.rowcount != 1:
                raise RuntimeError(
                    f"Could not complete audit for run {run_id}"
                )

    logger.info("Completed audit record for run %s", run_id)


def fail_run(run_id: str, error_message: str) -> None:
    """Mark a run as failed and capture its error."""

    query = """
        UPDATE etl_run_audit
        SET
            finished_at = %s,
            status = 'FAILED',
            error_message = %s
        WHERE run_id = %s
          AND status = 'RUNNING';
    """

    with database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                query,
                (
                    datetime.now(timezone.utc),
                    error_message[:10000],
                    run_id,
                ),
            )

            if cursor.rowcount != 1:
                raise RuntimeError(
                    f"Could not mark audit as failed for run {run_id}"
                )

    logger.error("Failed audit record for run %s", run_id)
