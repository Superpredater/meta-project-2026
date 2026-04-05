"""Unit tests for FixtureLoader — checksum validation, version warning, deserialization."""
from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

import pytest

from openenv_email_triage.fixture_loader import FixtureData, FixtureLoader


# ── helpers ──────────────────────────────────────────────────────────────────

def _compute_checksum(data: dict) -> str:
    data_copy = dict(data)
    data_copy["checksum"] = ""
    serialized = json.dumps(data_copy, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode()).hexdigest()


def _make_minimal_fixture(tmp_path: Path, task_id: str = "test_task", version: str = "1.0.0") -> Path:
    """Write a minimal valid fixture file and return its path."""
    data = {
        "fixture_version": version,
        "checksum": "",
        "task_id": task_id,
        "emails": [
            {
                "id": "e001",
                "subject": "Test email",
                "sender": "test@example.com",
                "body": "Hello world",
                "timestamp": "2024-01-15T09:00:00Z",
                "thread_id": "t001",
                "labels": [],
                "attachments": [],
            }
        ],
        "ground_truth": [
            {
                "email_id": "e001",
                "label": "general",
                "priority": None,
                "reply_required": False,
                "escalate": False,
                "should_archive": False,
                "should_delete": False,
            }
        ],
    }
    data["checksum"] = _compute_checksum(data)
    fixture_path = tmp_path / f"{task_id}.json"
    fixture_path.write_text(json.dumps(data, indent=2, sort_keys=True))
    return fixture_path


# ── FileNotFoundError ─────────────────────────────────────────────────────────

def test_load_missing_file_raises_file_not_found(tmp_path, monkeypatch):
    """FixtureLoader.load raises FileNotFoundError when fixture file is absent."""
    import openenv_email_triage.fixture_loader as fl_module
    monkeypatch.setattr(fl_module, "FIXTURES_DIR", tmp_path)

    loader = FixtureLoader()
    with pytest.raises(FileNotFoundError, match="nonexistent"):
        loader.load("nonexistent")


# ── Checksum validation ───────────────────────────────────────────────────────

def test_load_valid_checksum_succeeds(tmp_path, monkeypatch):
    """FixtureLoader.load succeeds when checksum is correct."""
    import openenv_email_triage.fixture_loader as fl_module
    monkeypatch.setattr(fl_module, "FIXTURES_DIR", tmp_path)

    _make_minimal_fixture(tmp_path, task_id="test_task")
    loader = FixtureLoader()
    result = loader.load("test_task")
    assert isinstance(result, FixtureData)


def test_load_bad_checksum_raises_value_error(tmp_path, monkeypatch):
    """FixtureLoader.load raises ValueError when checksum does not match."""
    import openenv_email_triage.fixture_loader as fl_module
    monkeypatch.setattr(fl_module, "FIXTURES_DIR", tmp_path)

    fixture_path = _make_minimal_fixture(tmp_path, task_id="bad_checksum")
    # Corrupt the checksum field
    data = json.loads(fixture_path.read_text())
    data["checksum"] = "deadbeef" * 8  # wrong but same length
    fixture_path.write_text(json.dumps(data))

    loader = FixtureLoader()
    with pytest.raises(ValueError, match="Checksum mismatch"):
        loader.load("bad_checksum")


def test_verify_checksum_raises_on_mismatch(tmp_path):
    """verify_checksum raises ValueError with path in message on mismatch."""
    loader = FixtureLoader()
    fake_path = tmp_path / "fake.json"
    data = {"fixture_version": "1.0.0", "checksum": "wrong", "task_id": "x", "emails": [], "ground_truth": []}
    with pytest.raises(ValueError) as exc_info:
        loader.verify_checksum(data, fake_path)
    assert str(fake_path) in str(exc_info.value)


def test_verify_checksum_passes_with_correct_hash(tmp_path):
    """verify_checksum does not raise when checksum is correct."""
    loader = FixtureLoader()
    fake_path = tmp_path / "fake.json"
    data = {"fixture_version": "1.0.0", "checksum": "", "task_id": "x", "emails": [], "ground_truth": []}
    data["checksum"] = _compute_checksum(data)
    loader.verify_checksum(data, fake_path)  # should not raise


# ── Version mismatch warning ──────────────────────────────────────────────────

def test_load_version_mismatch_logs_warning(tmp_path, monkeypatch, caplog):
    """FixtureLoader.load emits a warning when fixture_version != expected."""
    import openenv_email_triage.fixture_loader as fl_module
    monkeypatch.setattr(fl_module, "FIXTURES_DIR", tmp_path)

    _make_minimal_fixture(tmp_path, task_id="old_version", version="0.9.0")
    loader = FixtureLoader()
    with caplog.at_level(logging.WARNING, logger="openenv_email_triage.fixture_loader"):
        result = loader.load("old_version")

    assert result.fixture_version == "0.9.0"
    assert any("version mismatch" in record.message.lower() for record in caplog.records)


def test_load_correct_version_no_warning(tmp_path, monkeypatch, caplog):
    """FixtureLoader.load does not warn when fixture_version matches expected."""
    import openenv_email_triage.fixture_loader as fl_module
    monkeypatch.setattr(fl_module, "FIXTURES_DIR", tmp_path)

    _make_minimal_fixture(tmp_path, task_id="current_version", version="1.0.0")
    loader = FixtureLoader()
    with caplog.at_level(logging.WARNING, logger="openenv_email_triage.fixture_loader"):
        loader.load("current_version")

    assert not any("version mismatch" in record.message.lower() for record in caplog.records)


# ── Deserialization ───────────────────────────────────────────────────────────

def test_load_returns_fixture_data_fields(tmp_path, monkeypatch):
    """FixtureLoader.load returns FixtureData with correct task_id, version, emails, ground_truth."""
    import openenv_email_triage.fixture_loader as fl_module
    monkeypatch.setattr(fl_module, "FIXTURES_DIR", tmp_path)

    _make_minimal_fixture(tmp_path, task_id="my_task")
    loader = FixtureLoader()
    result = loader.load("my_task")

    assert result.task_id == "my_task"
    assert result.fixture_version == "1.0.0"
    assert len(result.emails) == 1
    assert result.emails[0]["id"] == "e001"
    assert len(result.ground_truth) == 1
    assert result.ground_truth[0]["email_id"] == "e001"


# ── Real fixture files ────────────────────────────────────────────────────────

@pytest.mark.parametrize("task_id,expected_count", [
    ("categorize_easy", 10),
    ("triage_medium", 15),
    ("manage_hard", 25),
])
def test_real_fixtures_load_successfully(task_id, expected_count):
    """All three real fixture files load without error and have the correct email count."""
    loader = FixtureLoader()
    result = loader.load(task_id)
    assert result.task_id == task_id
    assert result.fixture_version == "1.0.0"
    assert len(result.emails) == expected_count
    assert len(result.ground_truth) == expected_count


def test_categorize_easy_has_correct_label_distribution():
    """categorize_easy fixture has 3 spam, 2 billing, 3 support, 2 general."""
    loader = FixtureLoader()
    result = loader.load("categorize_easy")
    labels = [gt["label"] for gt in result.ground_truth]
    assert labels.count("spam") == 3
    assert labels.count("billing") == 2
    assert labels.count("support") == 3
    assert labels.count("general") == 2


def test_triage_medium_has_reply_required_emails():
    """triage_medium fixture has ~8 emails with reply_required=True."""
    loader = FixtureLoader()
    result = loader.load("triage_medium")
    reply_required_count = sum(1 for gt in result.ground_truth if gt["reply_required"])
    assert reply_required_count >= 7  # spec says ~8


def test_manage_hard_has_all_operations_represented():
    """manage_hard fixture has emails requiring escalate, archive, and delete."""
    loader = FixtureLoader()
    result = loader.load("manage_hard")
    assert any(gt["escalate"] for gt in result.ground_truth)
    assert any(gt["should_archive"] for gt in result.ground_truth)
    assert any(gt["should_delete"] for gt in result.ground_truth)
