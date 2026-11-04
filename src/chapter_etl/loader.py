import logging

from chapter_etl.database import database_connection

logger = logging.getLogger(__name__)


def load_chapters(
    chapters: list[dict],
    run_id: str,
) -> int:
    """Load chapters into PostgreSQL using an UPSERT."""

    if not chapters:
        logger.info("No chapters to load for run %s", run_id)
        return 0

    query = """
        INSERT INTO university_chapters (
            chapter_id,
            chapter_name,
            city,
            state,
            longitude,
            latitude
        )
        VALUES (
            %(chapter_id)s,
            %(chapter_name)s,
            %(city)s,
            %(state)s,
            %(longitude)s,
            %(latitude)s
        )
        ON CONFLICT (chapter_id)
        DO UPDATE SET
            chapter_name = EXCLUDED.chapter_name,
            city = EXCLUDED.city,
            state = EXCLUDED.state,
            longitude = EXCLUDED.longitude,
            latitude = EXCLUDED.latitude,
            updated_at = CURRENT_TIMESTAMP;
    """

    with database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.executemany(query, chapters)

    logger.info(
    "Run %s: successfully loaded %s chapters",
    run_id,
    len(chapters),
    )

    return len(chapters)
