"""Property-based tests for CategorizeGrader.

# Feature: openenv-email-triage, Property 2: Categorization scoring correctness
# Feature: openenv-email-triage, Property 13: Grader score formula — categorize_easy
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from openenv_email_triage.fixture_loader import FixtureLoader
from openenv_email_triage.graders import CategorizeGrader
from openenv_email_triage.models import Action, Email, Operation, Reward

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_LOADER = FixtureLoader()
_FIXTURE = _LOADER.load("categorize_easy")

# All valid labels present in the categorize_easy fixture.
_VALID_LABELS = list({gt["label"] for gt in _FIXTURE.ground_truth})

# All Operation values except "categorize".
_NON_CATEGORIZE_OPS = [op for op in Operation if op != Operation.categorize]


def _make_email(email_id: str = "e001") -> Email:
    return Email(
        id=email_id,
        subject="Test subject",
        sender="test@example.com",
        body="Test body",
        timestamp=datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc),
        thread_id="t001",
        labels=[],
        attachments=[],
    )


def _make_categorize_action(label: str) -> Action:
    return Action(operation=Operation.categorize, label=label)


def _make_non_categorize_action(operation: Operation) -> Action:
    """Build a valid Action for a non-categorize operation."""
    if operation == Operation.prioritize:
        return Action(operation=operation, priority=1)
    return Action(operation=operation)


# ---------------------------------------------------------------------------
# Property 2: Categorization scoring correctness
# Validates: Requirements 4.2, 4.3, 4.6
# ---------------------------------------------------------------------------

@given(
    gt_index=st.integers(min_value=0, max_value=len(_FIXTURE.ground_truth) - 1),
)
@settings(max_examples=100)
def test_p2_correct_label_scores_1(gt_index: int) -> None:
    """Submitting the ground-truth label yields score 1.0.

    **Validates: Requirements 4.2, 4.3, 4.6**
    """
    # Feature: openenv-email-triage, Property 2: Categorization scoring correctness
    gt = _FIXTURE.ground_truth[gt_index]
    email_data = _FIXTURE.emails[gt_index]
    email = Email.model_validate(email_data, strict=False)
    action = _make_categorize_action(gt["label"])

    grader = CategorizeGrader()
    reward = grader.score_step(email, action, gt)

    assert reward.score == 1.0
    assert reward.partial_scores["categorization"] == 1.0
    assert email.id in reward.rationale


@given(
    gt_index=st.integers(min_value=0, max_value=len(_FIXTURE.ground_truth) - 1),
    wrong_label=st.text(min_size=1, max_size=20).filter(
        lambda s: s not in _VALID_LABELS
    ),
)
@settings(max_examples=100)
def test_p2_wrong_label_scores_0(gt_index: int, wrong_label: str) -> None:
    """Submitting a wrong label yields score 0.0.

    **Validates: Requirements 4.2, 4.3, 4.6**
    """
    # Feature: openenv-email-triage, Property 2: Categorization scoring correctness
    gt = _FIXTURE.ground_truth[gt_index]
    email_data = _FIXTURE.emails[gt_index]
    email = Email.model_validate(email_data, strict=False)
    action = _make_categorize_action(wrong_label)

    grader = CategorizeGrader()
    reward = grader.score_step(email, action, gt)

    assert reward.score == 0.0
    assert reward.partial_scores["categorization"] == 0.0
    assert email.id in reward.rationale


@given(
    gt_index=st.integers(min_value=0, max_value=len(_FIXTURE.ground_truth) - 1),
    op=st.sampled_from(_NON_CATEGORIZE_OPS),
)
@settings(max_examples=100)
def test_p2_non_categorize_op_scores_0(gt_index: int, op: Operation) -> None:
    """Any non-categorize operation (including skip) yields score 0.0.

    **Validates: Requirements 4.2, 4.3, 4.6**
    """
    # Feature: openenv-email-triage, Property 2: Categorization scoring correctness
    gt = _FIXTURE.ground_truth[gt_index]
    email_data = _FIXTURE.emails[gt_index]
    email = Email.model_validate(email_data, strict=False)
    action = _make_non_categorize_action(op)

    grader = CategorizeGrader()
    reward = grader.score_step(email, action, gt)

    assert reward.score == 0.0
    assert reward.partial_scores["categorization"] == 0.0
    assert email.id in reward.rationale


# ---------------------------------------------------------------------------
# Property 13: Grader score formula — categorize_easy
# Validates: Requirements 4.4
# ---------------------------------------------------------------------------

@given(correct_count=st.integers(min_value=0, max_value=10))
@settings(max_examples=100)
def test_p13_episode_score_formula(correct_count: int) -> None:
    """Episode score equals correct_count / 10 for all 11 possible values.

    **Validates: Requirements 4.4**
    """
    # Feature: openenv-email-triage, Property 13: Grader score formula — categorize_easy
    emails = [Email.model_validate(e, strict=False) for e in _FIXTURE.emails]
    ground_truths = _FIXTURE.ground_truth

    # Build a history where exactly `correct_count` steps score 1.0.
    history: list[tuple[Action, Reward]] = []
    for i, (email, gt) in enumerate(zip(emails, ground_truths)):
        if i < correct_count:
            action = _make_categorize_action(gt["label"])
        else:
            action = Action(operation=Operation.skip)

        grader = CategorizeGrader()
        reward = grader.score_step(email, action, gt)
        history.append((action, reward))

    grader = CategorizeGrader()
    episode_reward = grader.score_episode(history, emails)

    expected = correct_count / 10
    assert abs(episode_reward.score - expected) < 1e-9
    assert abs(episode_reward.partial_scores["categorization"] - expected) < 1e-9
