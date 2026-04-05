"""Unit tests for Pydantic data models (Requirements 1.1–1.6)."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from openenv_email_triage.models import Action, Email, Observation, Operation, Reward


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_email(**overrides) -> dict:
    base = {
        "id": "e001",
        "subject": "Hello",
        "sender": "alice@example.com",
        "body": "Body text",
        "timestamp": datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc),
        "thread_id": "t001",
        "labels": [],
        "attachments": [],
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Email model
# ---------------------------------------------------------------------------

class TestEmail:
    def test_valid_email(self):
        email = Email(**_make_email())
        assert email.id == "e001"
        assert email.labels == []
        assert email.attachments == []

    def test_email_with_labels_and_attachments(self):
        email = Email(**_make_email(labels=["spam"], attachments=["file.pdf"]))
        assert email.labels == ["spam"]
        assert email.attachments == ["file.pdf"]

    def test_email_missing_required_field_raises(self):
        data = _make_email()
        del data["subject"]
        with pytest.raises(ValidationError):
            Email(**data)

    def test_email_strict_mode_rejects_wrong_type(self):
        # strict=True: passing int where str expected should fail
        with pytest.raises(ValidationError):
            Email(**_make_email(id=123))


# ---------------------------------------------------------------------------
# Action model
# ---------------------------------------------------------------------------

class TestAction:
    def test_action_with_operation_only(self):
        action = Action(operation=Operation.skip)
        assert action.operation == Operation.skip
        assert action.label is None
        assert action.priority is None
        assert action.reply_text is None

    def test_action_all_fields(self):
        action = Action(
            operation=Operation.reply,
            label="billing",
            priority=2,
            reply_text="Thank you for reaching out.",
        )
        assert action.priority == 2
        assert action.reply_text == "Thank you for reaching out."

    def test_action_priority_boundary_valid(self):
        for p in (1, 2, 3):
            a = Action(operation=Operation.prioritize, priority=p)
            assert a.priority == p

    def test_action_priority_zero_raises(self):
        with pytest.raises(ValidationError):
            Action(operation=Operation.prioritize, priority=0)

    def test_action_priority_four_raises(self):
        with pytest.raises(ValidationError):
            Action(operation=Operation.prioritize, priority=4)

    def test_action_priority_negative_raises(self):
        with pytest.raises(ValidationError):
            Action(operation=Operation.prioritize, priority=-1)

    def test_action_invalid_operation_raises(self):
        with pytest.raises(ValidationError):
            Action(operation="fly")

    def test_all_operations_accepted(self):
        for op in Operation:
            a = Action(operation=op)
            assert a.operation == op


# ---------------------------------------------------------------------------
# Observation model
# ---------------------------------------------------------------------------

class TestObservation:
    def test_valid_observation(self):
        email = Email(**_make_email())
        obs = Observation(email=email, inbox_size=10, step_number=0, task_id="categorize_easy")
        assert obs.step_number == 0
        assert obs.task_id == "categorize_easy"

    def test_observation_missing_field_raises(self):
        email = Email(**_make_email())
        with pytest.raises(ValidationError):
            Observation(email=email, inbox_size=10, step_number=0)  # missing task_id


# ---------------------------------------------------------------------------
# Reward model
# ---------------------------------------------------------------------------

class TestReward:
    def test_valid_reward(self):
        r = Reward(score=0.75, partial_scores={"categorization": 0.75}, rationale="Good job.")
        assert r.score == 0.75

    def test_reward_score_zero(self):
        r = Reward(score=0.0, partial_scores={}, rationale="No match.")
        assert r.score == 0.0

    def test_reward_score_one(self):
        r = Reward(score=1.0, partial_scores={"cat": 1.0}, rationale="Perfect.")
        assert r.score == 1.0

    def test_reward_score_below_zero_raises(self):
        with pytest.raises(ValidationError):
            Reward(score=-0.1, partial_scores={}, rationale="Bad.")

    def test_reward_score_above_one_raises(self):
        with pytest.raises(ValidationError):
            Reward(score=1.01, partial_scores={}, rationale="Too high.")
