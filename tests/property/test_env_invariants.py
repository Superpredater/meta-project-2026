"""Property-based tests for environment invariants.

# Feature: openenv-email-triage, Property 8: Reward structural invariant
# Feature: openenv-email-triage, Property 10: Consecutive skip penalty
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone

from hypothesis import given, settings
from hypothesis import strategies as st

from openenv_email_triage.graders import CategorizeGrader, ManageGrader, TriageGrader
from openenv_email_triage.models import Action, Email, Operation
from openenv_email_triage.reward_calculator import RewardCalculator

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VALID_OPERATIONS = list(Operation)
_NON_SKIP_OPS = [op for op in Operation if op != Operation.skip]


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


def _make_action(op: Operation) -> Action:
    if op == Operation.prioritize:
        return Action(operation=op, priority=1)
    elif op == Operation.categorize:
        return Action(operation=op, label="spam")
    elif op == Operation.reply:
        return Action(operation=op, reply_text="Acknowledged.")
    else:
        return Action(operation=op)


_CATEGORIZE_GT = {"label": "spam", "priority": None, "reply_required": False,
                  "escalate": False, "should_archive": False, "should_delete": False}

_TRIAGE_GT = {"label": None, "priority": 2, "reply_required": True,
              "escalate": False, "should_archive": False, "should_delete": False}

_MANAGE_GT = {"label": "spam", "priority": 2, "reply_required": False,
              "escalate": False, "should_archive": True, "should_delete": False}

_GRADERS = [
    (CategorizeGrader(), _CATEGORIZE_GT),
    (TriageGrader(), _TRIAGE_GT),
    (ManageGrader(), _MANAGE_GT),
]


# ---------------------------------------------------------------------------
# Property 8: Reward structural invariant
# Validates: Requirements 7.2, 7.5
# ---------------------------------------------------------------------------

@given(
    email_id=st.text(min_size=1, max_size=20, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-_"
    )),
    op=st.sampled_from(_VALID_OPERATIONS),
    grader_index=st.integers(min_value=0, max_value=len(_GRADERS) - 1),
)
@settings(max_examples=100)
def test_p8_reward_structural_invariant(
    email_id: str, op: Operation, grader_index: int
) -> None:
    """Every Reward has non-empty partial_scores and rationale containing email id.

    **Validates: Requirements 7.2, 7.5**
    """
    # Feature: openenv-email-triage, Property 8: Reward structural invariant
    grader, ground_truth = _GRADERS[grader_index]
    email = _make_email(email_id)
    action = _make_action(op)

    calc = RewardCalculator(grader)
    reward = calc.calculate(email, action, ground_truth, consecutive_skips=0)

    # partial_scores must be non-empty
    assert len(reward.partial_scores) > 0, "partial_scores must not be empty"

    # rationale must contain the email id
    assert email_id in reward.rationale, (
        f"rationale '{reward.rationale}' does not contain email id '{email_id}'"
    )

    # score must be in valid range (enforced by Pydantic, but verify explicitly)
    assert 0.0 <= reward.score <= 1.0


# ---------------------------------------------------------------------------
# Property 10: Consecutive skip penalty
# Validates: Requirements 7.4
# ---------------------------------------------------------------------------

@given(
    consecutive_skips=st.integers(min_value=3, max_value=20),
    base_score=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
)
@settings(max_examples=100)
def test_p10_consecutive_skip_penalty_applied(
    consecutive_skips: int, base_score: float
) -> None:
    """Score is reduced by 0.05 when consecutive_skips >= 3 and action is skip.

    **Validates: Requirements 7.4**
    """
    # Feature: openenv-email-triage, Property 10: Consecutive skip penalty
    email = _make_email("e-skip-test")
    action = Action(operation=Operation.skip)

    # Use a grader that returns a known base score by using CategorizeGrader
    # with a skip action (always returns 0.0), but we need to control base_score.
    # We use a simple stub grader approach via a lambda-compatible class.
    from openenv_email_triage.models import Reward

    class StubGrader:
        def score_step(self, email: Email, action: Action, ground_truth: dict) -> Reward:
            return Reward(
                score=base_score,
                partial_scores={"stub": base_score},
                rationale=f"Email {email.id}: stub score {base_score}.",
            )

        def score_episode(self, history, inbox):
            return Reward(score=0.0, partial_scores={"stub": 0.0}, rationale="stub")

    calc = RewardCalculator(StubGrader())
    reward = calc.calculate(email, action, {}, consecutive_skips=consecutive_skips)

    expected_score = max(0.0, min(1.0, base_score - 0.05))
    assert abs(reward.score - expected_score) < 1e-9, (
        f"Expected penalized score {expected_score}, got {reward.score} "
        f"(base={base_score}, consecutive_skips={consecutive_skips})"
    )
    # Rationale must still reference the email id
    assert "e-skip-test" in reward.rationale


@given(
    consecutive_skips=st.integers(min_value=0, max_value=2),
    base_score=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
)
@settings(max_examples=100)
def test_p10_no_penalty_below_threshold(
    consecutive_skips: int, base_score: float
) -> None:
    """No penalty when consecutive_skips < 3 (fewer than 4 consecutive skips).

    **Validates: Requirements 7.4**
    """
    # Feature: openenv-email-triage, Property 10: Consecutive skip penalty
    email = _make_email("e-no-penalty")
    action = Action(operation=Operation.skip)

    from openenv_email_triage.models import Reward

    class StubGrader:
        def score_step(self, email: Email, action: Action, ground_truth: dict) -> Reward:
            return Reward(
                score=base_score,
                partial_scores={"stub": base_score},
                rationale=f"Email {email.id}: stub score {base_score}.",
            )

        def score_episode(self, history, inbox):
            return Reward(score=0.0, partial_scores={"stub": 0.0}, rationale="stub")

    calc = RewardCalculator(StubGrader())
    reward = calc.calculate(email, action, {}, consecutive_skips=consecutive_skips)

    assert abs(reward.score - base_score) < 1e-9, (
        f"Expected no penalty (score={base_score}), got {reward.score} "
        f"(consecutive_skips={consecutive_skips})"
    )


@given(
    consecutive_skips=st.integers(min_value=3, max_value=20),
    base_score=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    op=st.sampled_from(_NON_SKIP_OPS),
)
@settings(max_examples=100)
def test_p10_no_penalty_for_non_skip_action(
    consecutive_skips: int, base_score: float, op: Operation
) -> None:
    """No penalty when action is not skip, even if consecutive_skips >= 3.

    **Validates: Requirements 7.4**
    """
    # Feature: openenv-email-triage, Property 10: Consecutive skip penalty
    email = _make_email("e-non-skip")
    action = _make_action(op)

    from openenv_email_triage.models import Reward

    class StubGrader:
        def score_step(self, email: Email, action: Action, ground_truth: dict) -> Reward:
            return Reward(
                score=base_score,
                partial_scores={"stub": base_score},
                rationale=f"Email {email.id}: stub score {base_score}.",
            )

        def score_episode(self, history, inbox):
            return Reward(score=0.0, partial_scores={"stub": 0.0}, rationale="stub")

    calc = RewardCalculator(StubGrader())
    reward = calc.calculate(email, action, {}, consecutive_skips=consecutive_skips)

    assert abs(reward.score - base_score) < 1e-9, (
        f"Expected no penalty for op={op} (score={base_score}), got {reward.score}"
    )


# ---------------------------------------------------------------------------
# Imports needed for env-level properties (P5, P6, P7, P9)
# ---------------------------------------------------------------------------

import json as _json

from openenv_email_triage.env import EmailTriageEnv
from openenv_email_triage.graders import (
    CategorizeGrader as _CategorizeGrader,
    GraderRegistry as _GraderRegistry,
    ManageGrader as _ManageGrader,
    TriageGrader as _TriageGrader,
)

# Task metadata: (task_id, inbox_size)
_TASKS = [
    ("categorize_easy", 10),
    ("triage_medium", 15),
    ("manage_hard", 25),
]

_TASK_IDS = [t[0] for t in _TASKS]
_TASK_INBOX_SIZES = {t[0]: t[1] for t in _TASKS}


def _make_skip_action() -> Action:
    return Action(operation=Operation.skip)


# ---------------------------------------------------------------------------
# Property 5: Episode termination invariant
# Validates: Requirements 2.3, 2.6
# ---------------------------------------------------------------------------

@given(task_id=st.sampled_from(_TASK_IDS))
@settings(max_examples=10)
def test_p5_episode_termination_invariant(task_id: str) -> None:
    """After N steps done=True; subsequent step() raises RuntimeError.

    **Validates: Requirements 2.3, 2.6**
    """
    # Feature: openenv-email-triage, Property 5: Episode termination invariant
    env = EmailTriageEnv()
    env.reset(task_id)
    n = _TASK_INBOX_SIZES[task_id]

    done = False
    for i in range(n):
        obs, reward, done, info = env.step(_make_skip_action())

    assert done is True, f"Expected done=True after {n} steps, got done={done}"

    # Any further step must raise RuntimeError
    with pytest.raises(RuntimeError) as exc_info:
        env.step(_make_skip_action())
    assert "Episode has ended" in str(exc_info.value)
    assert "reset()" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Property 6: Step counter monotonicity
# Validates: Requirements 2.5
# ---------------------------------------------------------------------------

@given(
    task_id=st.sampled_from(_TASK_IDS),
    num_steps=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=50)
def test_p6_step_counter_monotonicity(task_id: str, num_steps: int) -> None:
    """step_number in Observation equals the call count (reset→0, k-th step→k).

    **Validates: Requirements 2.5**
    """
    # Feature: openenv-email-triage, Property 6: Step counter monotonicity
    env = EmailTriageEnv()
    obs = env.reset(task_id)
    assert obs.step_number == 0, f"reset() should return step_number=0, got {obs.step_number}"

    inbox_size = _TASK_INBOX_SIZES[task_id]
    steps_to_take = min(num_steps, inbox_size)

    for k in range(1, steps_to_take + 1):
        obs, reward, done, info = env.step(_make_skip_action())
        assert obs.step_number == k, (
            f"After {k} step(s), expected step_number={k}, got {obs.step_number}"
        )
        if done:
            break


# ---------------------------------------------------------------------------
# Property 7: State JSON-serializability
# Validates: Requirements 2.4
# ---------------------------------------------------------------------------

@given(
    task_id=st.sampled_from(_TASK_IDS),
    num_steps=st.integers(min_value=0, max_value=5),
)
@settings(max_examples=50)
def test_p7_state_json_serializability(task_id: str, num_steps: int) -> None:
    """state() is JSON-serializable at every point in an episode.

    **Validates: Requirements 2.4**
    """
    # Feature: openenv-email-triage, Property 7: State JSON-serializability
    env = EmailTriageEnv()
    env.reset(task_id)

    # state() right after reset must be serializable
    state = env.state()
    _json.dumps(state)  # raises if not serializable

    inbox_size = _TASK_INBOX_SIZES[task_id]
    steps_to_take = min(num_steps, inbox_size)

    for _ in range(steps_to_take):
        env.step(_make_skip_action())
        state = env.state()
        serialized = _json.dumps(state)
        assert isinstance(serialized, str)


# ---------------------------------------------------------------------------
# Property 9: Episode-level score matches Grader output
# Validates: Requirements 7.3
# ---------------------------------------------------------------------------

@given(task_id=st.sampled_from(_TASK_IDS))
@settings(max_examples=10)
def test_p9_episode_score_matches_grader(task_id: str) -> None:
    """Final Reward.score equals grader.score_episode() on the same history.

    **Validates: Requirements 7.3**
    """
    # Feature: openenv-email-triage, Property 9: Episode-level score matches Grader output
    env = EmailTriageEnv()
    env.reset(task_id)
    n = _TASK_INBOX_SIZES[task_id]

    final_reward = None
    for i in range(n):
        obs, reward, done, info = env.step(_make_skip_action())
        if done:
            final_reward = reward

    assert final_reward is not None, "Episode should have ended"

    # Compute expected score via a fresh grader on the same history
    registry = _GraderRegistry()
    # Use a fresh ManageGrader for manage_hard to avoid loop-detection state issues
    if task_id == "manage_hard":
        registry._registry["manage_hard"] = _ManageGrader()
    grader = registry.get(task_id)

    # Reconstruct history from env state
    state = env.state()
    from openenv_email_triage.models import Action as _Action, Reward as _Reward
    history: list[tuple[_Action, _Reward]] = []
    for entry in state["history"]:
        a = _Action.model_validate(entry["action"])
        r = _Reward.model_validate(entry["reward"])
        history.append((a, r))

    inbox = env._inbox
    expected = grader.score_episode(history, inbox)

    assert abs(final_reward.score - expected.score) < 1e-9, (
        f"Final reward score {final_reward.score} != grader.score_episode() {expected.score}"
    )
