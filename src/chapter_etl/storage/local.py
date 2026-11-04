import json
from pathlib import Path

from chapter_etl.storage.base import RawStorage


class LocalStorage(RawStorage):
    """Persist raw API responses to the local filesystem."""

    def write_raw(
        self,
        run_id: str,
        timestamp_folder: str,
        page_number: int,
        data: dict,
    ) -> str:
        output_dir = (
            Path("data")
            / "raw"
            / timestamp_folder[:4]
            / timestamp_folder[4:6]
            / timestamp_folder[6:8]
            / f"{timestamp_folder}_{run_id}"
        )

        output_dir.mkdir(parents=True, exist_ok=True)

        file_path = output_dir / f"page_{page_number:06d}.json"

        with file_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)

        return str(file_path)

    def read_raw(self, path: str) -> dict:
        with Path(path).open("r", encoding="utf-8") as file:
            return json.load(file)
