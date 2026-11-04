import logging

from chapter_etl.storage.factory import get_storage

logger = logging.getLogger(__name__)


def transform_raw_files(raw_files: list[str]) -> list[dict]:
    """Read persisted API responses and transform their features."""

    storage = get_storage()
    features = []

    for raw_path in raw_files:
        logger.info("Reading raw data from storage: %s", raw_path)

        data = storage.read_raw(raw_path)
        page_features = data.get("features", [])

        logger.info(
            "Read %s features from %s",
            len(page_features),
            raw_path,
        )

        features.extend(page_features)

    return transform_chapters(features)


def transform_chapters(features: list[dict]) -> list[dict]:
    """Transform and validate ArcGIS features."""

    chapters = []
    seen_ids = set()

    for feature in features:
        attributes = feature.get("attributes") or {}
        geometry = feature.get("geometry") or {}

        chapter = {
            "chapter_id": attributes.get("ChapterID"),
            "chapter_name": attributes.get("University_Chapter"),
            "city": attributes.get("City"),
            "state": attributes.get("State"),
            "longitude": geometry.get("x"),
            "latitude": geometry.get("y"),
        }

        required_fields = [
            "chapter_id",
            "chapter_name",
            "city",
            "state",
            "longitude",
            "latitude",
        ]

        missing = [
            field
            for field in required_fields
            if chapter[field] is None or chapter[field] == ""
        ]

        if missing:
            raise ValueError(
                f"Chapter has missing fields: {missing}"
            )

        if chapter["state"] != "CA":
            raise ValueError(
                f"Unexpected state: {chapter['state']}"
            )

        if not (-180 <= chapter["longitude"] <= 180):
            raise ValueError("Invalid longitude")

        if not (-90 <= chapter["latitude"] <= 90):
            raise ValueError("Invalid latitude")

        if chapter["chapter_id"] in seen_ids:
            raise ValueError(
                f"Duplicate chapter ID: {chapter['chapter_id']}"
            )

        seen_ids.add(chapter["chapter_id"])
        chapters.append(chapter)

    logger.info(
        "Successfully transformed %s chapters",
        len(chapters),
    )

    return chapters
