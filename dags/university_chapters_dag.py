
import logging
import re

import pendulum
from airflow.decorators import dag, task
from airflow.operators.python import get_current_context

from chapter_etl.pipeline import run_pipeline

logger = logging.getLogger(__name__)

DAG_ID = "university_chapters_dag"


def safe_run_id(airflow_run_id: str) -> str:
    """Convert Airflow's run ID into a filesystem- and SQL-safe ID."""
    safe_id = re.sub(r"[^A-Za-z0-9_-]", "_", airflow_run_id)
    return safe_id[:90]


@dag(
    dag_id=DAG_ID,
    description="Run the California university chapters ETL pipeline",
    schedule="0 6 * * *",
    start_date=pendulum.datetime(2026, 10, 31, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    tags=["etl", "arcgis", "postgres"],
)
def university_chapters_pipeline():

    @task
    def run_etl_task() -> dict:
        """Execute the shared ETL pipeline."""
        context = get_current_context()
        airflow_run_id = context["dag_run"].run_id
        run_id = safe_run_id(airflow_run_id)

        logger.info(
            "Starting ETL pipeline for Airflow run %s",
            airflow_run_id,
        )

        return run_pipeline(
            run_id=run_id,
            dag_id=DAG_ID,
        )

    run_etl_task()


university_chapters_pipeline()
