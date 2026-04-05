"""Unit tests for EmailTriageEnv lifecycle.

Tests:
- reset() returns Observation with step_number=0 and correct task_id
- step() after done=True raises RuntimeError
- render() returns non-empty string
- state() returns JSON-serializable dict
"""
from __future__ import annotations

import json

import pytest

from openenv_email_triage.env import EmailTriageEnv
from openenv_email_triage.models import Action, Operation


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _skip_action() -> Action:
    return Action(operation=Operation.skip)


def _categorize_action(label: str = "spam") -> Action:
    return Action(operation=Operation.categorize, label=label)


# ---------------------------------------------------------------------------
# reset() tests
# ---------------------------------------------------------------------------

class TestReset:
    def test_reset_returns_observation_step_number_zero(self):
        env = EmailTriageEnv()
        obs = env.reset("categorize_easy")
        assert obs.step_number == 0

    def test_reset_returns_correct_task_id(self):
        env = EmailTriageEnv()
        obs = env.reset("categorize_easy")
        assert obs.task_id == "categorize_easy"

    def test_reset_triage_medium_task_id(self):
        env = EmailTriageEnv()
        obs = env.reset("triage_medium")
        assert obs.task_id == "triage_medium"
        assert obs.step_number == 0

    def test_reset_manage_hard_task_id(self):
        env = EmailTriageEnv()
        obs = env.reset("manage_hard")
        assert obs.task_id == "manage_hard"
        assert obs.step_number == 0

    def test_reset_returns_first_email(self):
        env = EmailTriageEnv()
        obs = env.reset("categorize_easy")
        assert obs.email is not None
        assert obs.email.id is not None

    def test_reset_inbox_size_correct(self):
        env = EmailTriageEnv()
        obs = env.reset("categorize_easy")
        assert obs.inbox_size == 10

    def test_reset_clears_previous_episode(self):
        env = EmailTriageEnv()
        env.reset("categorize_easy")
        env.step(_skip_action())
        # Reset again — should start fresh
        obs = env.reset("categorize_easy")
        assert obs.step_number == 0
        state = env.state()
        assert state["step"] == 0
        assert state["history"] == []

    def test_reset_unknown_task_raises(self):
        env = EmailTriageEnv()
        with pytest.raises((ValueError, FileNotFoundError)):
            env.reset("nonexistent_task")


# ---------------------------------------------------------------------------
# step() tests
# ---------------------------------------------------------------------------

class TestStep:
    def test_step_after_done_raises_runtime_error(self):
        env = EmailTriageEnv()
        env.reset("categorize_easy")
        # Exhaust all 10 emails
        for _ in range(10):
            env.step(_skip_action())
        # Now done=True — next step should raise
        with pytest.raises(RuntimeError) as exc_info:
            env.step(_skip_action())
        assert "Episode has ended" in str(exc_info.value)
        assert "reset()" in str(exc_info.value)

    def test_step_returns_tuple_of_four(self):
        env = EmailTriageEnv()
        env.reset("categorize_easy")
        result = env.step(_skip_action())
        assert len(result) == 4

    def test_step_increments_step_number(self):
        env = EmailTriageEnv()
        env.reset("categorize_easy")
        obs, reward, done, info = env.step(_skip_action())
        assert obs.step_number == 1

    def test_step_done_false_before_last_email(self):
        env = EmailTriageEnv()
        env.reset("categorize_easy")
        obs, reward, done, info = env.step(_skip_action())
        assert done is False

    def test_step_done_true_after_last_email(self):
        env = EmailTriageEnv()
        env.reset("categorize_easy")
        for _ in range(9):
            env.step(_skip_action())
        obs, reward, done, info = env.step(_skip_action())
        assert done is True

    def test_step_reward_has_score_in_range(self):
        env = EmailTriageEnv()
        env.reset("categorize_easy")
        obs, reward, done, info = env.step(_skip_action())
        assert 0.0 <= reward.score <= 1.0

    def test_step_info_is_dict(self):
        env = EmailTriageEnv()
        env.reset("categorize_easy")
        obs, reward, done, info = env.step(_skip_action())
        assert isinstance(info, dict)


# ---------------------------------------------------------------------------
# render() tests
# ---------------------------------------------------------------------------

class TestRender:
    def test_render_returns_non_empty_string(self):
        env = EmailTriageEnv()
        env.reset("categorize_easy")
        result = env.render()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_before_reset_returns_string(self):
        env = EmailTriageEnv()
        result = env.render()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_contains_task_id(self):
        env = EmailTriageEnv()
        env.reset("categorize_easy")
        result = env.render()
        assert "categorize_easy" in result

    def test_render_after_done_returns_string(self):
        env = EmailTriageEnv()
        env.reset("categorize_easy")
        for _ in range(10):
            env.step(_skip_action())
        result = env.render()
        assert isinstance(result, str)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# state() tests
# ---------------------------------------------------------------------------

class TestState:
    def test_state_returns_json_serializable_dict(self):
        env = EmailTriageEnv()
        env.reset("categorize_easy")
        state = env.state()
        # Must be a dict
        assert isinstance(state, dict)
        # Must be JSON-serializable
        serialized = json.dumps(state)
        assert isinstance(serialized, str)

    def test_state_has_required_keys(self):
        env = EmailTriageEnv()
        env.reset("categorize_easy")
        state = env.state()
        assert "task_id" in state
        assert "step" in state
        assert "done" in state
        assert "inbox_size" in state
        assert "history" in state

    def test_state_task_id_correct(self):
        env = EmailTriageEnv()
        env.reset("categorize_easy")
        state = env.state()
        assert state["task_id"] == "categorize_easy"

    def test_state_step_zero_after_reset(self):
        env = EmailTriageEnv()
        env.reset("categorize_easy")
        state = env.state()
        assert state["step"] == 0

    def test_state_done_false_after_reset(self):
        env = EmailTriageEnv()
        env.reset("categorize_easy")
        state = env.state()
        assert state["done"] is False

    def test_state_history_empty_after_reset(self):
        env = EmailTriageEnv()
        env.reset("categorize_easy")
        state = env.state()
        assert state["history"] == []

    def test_state_history_grows_with_steps(self):
        env = EmailTriageEnv()
        env.reset("categorize_easy")
        env.step(_skip_action())
        env.step(_skip_action())
        state = env.state()
        assert len(state["history"]) == 2

    def test_state_history_entries_have_action_and_reward(self):
        env = EmailTriageEnv()
        env.reset("categorize_easy")
        env.step(_skip_action())
        state = env.state()
        entry = state["history"][0]
        assert "action" in entry
        assert "reward" in entry

    def test_state_json_serializable_after_multiple_steps(self):
        env = EmailTriageEnv()
        env.reset("categorize_easy")
        for _ in range(5):
            env.step(_skip_action())
        state = env.state()
        serialized = json.dumps(state)
        assert isinstance(serialized, str)

    def test_state_done_true_after_episode_complete(self):
        env = EmailTriageEnv()
        env.reset("categorize_easy")
        for _ in range(10):
            env.step(_skip_action())
        state = env.state()
        assert state["done"] is True


# ---------------------------------------------------------------------------
# get_fixture_version() tests
# ---------------------------------------------------------------------------

class TestGetFixtureVersion:
    def test_get_fixture_version_returns_string(self):
        env = EmailTriageEnv()
        env.reset("categorize_easy")
        version = env.get_fixture_version()
        assert isinstance(version, str)
        assert len(version) > 0

    def test_get_fixture_version_is_1_0_0(self):
        env = EmailTriageEnv()
        env.reset("categorize_easy")
        version = env.get_fixture_version()
        assert version == "1.0.0"
