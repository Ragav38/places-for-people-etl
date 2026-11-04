from typing import Protocol


class RawStorage(Protocol):
    """Interface for persisting and reading raw API responses."""

    def write_raw(
        self,
        run_id: str,
        timestamp_folder: str,
        page_number: int,
        data: dict,
    ) -> str:
        """Persist a raw API response and return its storage path."""

    def read_raw(self, path: str) -> dict:
        """Read a persisted raw API response."""
