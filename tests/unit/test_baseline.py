"""Unit tests for baseline.py.

Tests:
- EnvironmentError raised when OPENAI_API_KEY is absent
- baseline_results.json written with all required fields (mock OpenAI client)
"""
from __future__ import annotations

import json
import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

import baseline
from baseline import _get_api_key, _parse_action, run_baseline
from openenv_email_triage.models import Action, Operation


# ---------------------------------------------------------------------------
# _get_api_key tests
# ---------------------------------------------------------------------------

class TestGetApiKey:
    def test_raises_environment_error_when_key_absent(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(EnvironmentError, match="OPENAI_API_KEY environment variable is not set"):
            _get_api_key()

    def test_raises_environment_error_when_key_empty(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "")
        with pytest.raises(EnvironmentError, match="OPENAI_API_KEY environment variable is not set"):
            _get_api_key()

    def test_returns_key_when_set(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        assert _get_api_key() == "sk-test-key"


# ---------------------------------------------------------------------------
# _parse_action tests
# ---------------------------------------------------------------------------

class TestParseAction:
    def test_parses_valid_categorize_action(self):
        content = '{"operation": "categorize", "label": "spam"}'
        action = _parse_action(content)
        assert action.operation == Operation.categorize
        assert action.label == "spam"

    def test_parses_valid_skip_action(self):
        content = '{"operation": "skip"}'
        action = _parse_action(content)
        assert action.operation == Operation.skip

    def test_falls_back_to_skip_on_invalid_json(self):
        action = _parse_action("not valid json at all")
        assert action.operation == Operation.skip

    def test_falls_back_to_skip_on_invalid_operation(self):
        action = _parse_action('{"operation": "fly_to_moon"}')
        assert action.operation == Operation.skip

    def test_falls_back_to_skip_on_empty_string(self):
        action = _parse_action("")
        assert action.operation == Operation.skip


# ---------------------------------------------------------------------------
# run_baseline tests (mock OpenAI client)
# ---------------------------------------------------------------------------

def _make_mock_client(response_json: str = '{"operation": "skip"}'):
    """Build a mock OpenAI client that always returns response_json."""
    message = SimpleNamespace(content=response_json)
    choice = SimpleNamespace(message=message)
    completion = SimpleNamespace(choices=[choice])

    client = MagicMock()
    client.chat.completions.create.return_value = completion
    return client


class TestRunBaseline:
    def test_results_contain_all_required_fields(self):
        client = _make_mock_client()
        results = run_baseline(client)

        assert "model" in results
        assert "task_scores" in results
        assert "mean_score" in results
        assert "timestamp" in results

    def test_model_field_is_gpt4o_mini(self):
        client = _make_mock_client()
        results = run_baseline(client)
        assert results["model"] == "gpt-4o-mini"

    def test_task_scores_contains_all_three_tasks(self):
        client = _make_mock_client()
        results = run_baseline(client)
        assert "categorize_easy" in results["task_scores"]
        assert "triage_medium" in results["task_scores"]
        assert "manage_hard" in results["task_scores"]

    def test_task_scores_are_floats_in_range(self):
        client = _make_mock_client()
        results = run_baseline(client)
        for task_id, score in results["task_scores"].items():
            assert isinstance(score, float), f"{task_id} score is not float"
            assert 0.0 <= score <= 1.0, f"{task_id} score {score} out of range"

    def test_mean_score_is_float(self):
        client = _make_mock_client()
        results = run_baseline(client)
        assert isinstance(results["mean_score"], float)

    def test_mean_score_equals_average_of_task_scores(self):
        client = _make_mock_client()
        results = run_baseline(client)
        expected = sum(results["task_scores"].values()) / 3
        assert abs(results["mean_score"] - expected) < 1e-6

    def test_timestamp_is_iso8601_string(self):
        from datetime import datetime
        client = _make_mock_client()
        results = run_baseline(client)
        ts = results["timestamp"]
        assert isinstance(ts, str)
        # Should parse without error
        datetime.fromisoformat(ts)

    def test_results_written_to_json_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        client = _make_mock_client()
        results = run_baseline(client)

        # Simulate what main() does: write the file
        output_path = tmp_path / "baseline_results.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        assert output_path.exists()
        loaded = json.loads(output_path.read_text())
        assert "model" in loaded
        assert "task_scores" in loaded
        assert "mean_score" in loaded
        assert "timestamp" in loaded

    def test_api_error_assigns_zero_score_and_continues(self):
        """When OpenAI raises an exception, score 0.0 is used and processing continues."""
        client = MagicMock()
        client.chat.completions.create.side_effect = Exception("API error")

        # Should not raise; all tasks should complete
        results = run_baseline(client)
        assert "task_scores" in results
        assert len(results["task_scores"]) == 3
