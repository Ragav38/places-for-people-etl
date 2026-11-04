import logging

from chapter_etl.pipeline import run_pipeline


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)


if __name__ == "__main__":
    run_pipeline()
