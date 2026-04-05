"""FixtureLoader: loads and validates fixture JSON files for OpenEnv Email Triage."""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
EXPECTED_VERSION = "1.0.0"


@dataclass
class FixtureData:
    task_id: str
    fixture_version: str
    emails: list[dict[str, Any]]
    ground_truth: list[dict[str, Any]]


class FixtureLoader:
    """Loads fixture JSON files, verifies checksums, and warns on version mismatch."""

    def load(self, task_id: str) -> FixtureData:
        """Load fixture for *task_id* from ``fixtures/{task_id}.json``.

        Raises:
            FileNotFoundError: if the fixture file does not exist.
            ValueError: if the checksum does not match.
        """
        path = FIXTURES_DIR / f"{task_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Fixture file not found: {path}")

        with path.open("r", encoding="utf-8") as fh:
            data: dict[str, Any] = json.load(fh)

        self.verify_checksum(data, path)

        version: str = data.get("fixture_version", "")
        if version != EXPECTED_VERSION:
            logger.warning(
                "Fixture version mismatch for %s: expected %s, got %s",
                path,
                EXPECTED_VERSION,
                version,
            )

        return FixtureData(
            task_id=data["task_id"],
            fixture_version=version,
            emails=data["emails"],
            ground_truth=data["ground_truth"],
        )

    def verify_checksum(self, data: dict[str, Any], path: Path) -> None:
        """Verify the SHA-256 checksum stored in *data*.

        The checksum is computed over the JSON serialisation of *data* with the
        ``checksum`` field set to an empty string, using sorted keys and no
        extra whitespace.

        Raises:
            ValueError: if the stored checksum does not match the computed one.
        """
        stored: str = data.get("checksum", "")
        data_copy = dict(data)
        data_copy["checksum"] = ""
        serialized = json.dumps(data_copy, sort_keys=True, separators=(",", ":"))
        computed = hashlib.sha256(serialized.encode()).hexdigest()
        if computed != stored:
            raise ValueError(f"Checksum mismatch for fixture {path}")
