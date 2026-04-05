"""Property-based tests for TriageGrader.

# Feature: openenv-email-triage, Property 3: Priority scoring by distance
# Feature: openenv-email-triage, Property 14: Grader score formula — triage_medium
"""
from __future__ import annotations

from datetime import datetime, timezone

from hypothesis import given, settings
from hypothesis import strategies as st

from openenv_email_triage.fixture_loader import FixtureLoader
from openenv_email_triage.graders import TriageGrader
from openenv_email_triage.models import Action, Email, Operation, Reward

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_LOADER = FixtureLoader()
_FIXTURE = _LOADER.load("triage_medium")

_NUM_EMAILS = len(_FIXTURE.emails)  # 15


def _make_email(email_id: str = "m001") -> Email:
    return Email(
        id=email_id,
        subject="Test subject",
        sender="test@example.com",
        body="Test body",
        timestamp=datetime(2024, 1, 16, 7, 0, 0, tzinfo=timezone.utc),
        thread_id="tm001",
        labels=[],
        attachments=[],
    )


# ---------------------------------------------------------------------------
# Property 3: Priority scoring by distance
# Validates: Requirements 5.2, 5.3, 5.4
# ---------------------------------------------------------------------------

@given(
    gt_priority=st.integers(min_value=1, max_value=3),
    submitted=st.integers(min_value=1, max_value=3),
)
@settings(max_examples=100)
def test_p3_priority_sub_score_by_distance(
    gt_priority: int, submitted: int
) -> None:
    """Priority sub-score is 1.0/0.5/0.0 for distance 0/1/2.

    **Validates: Requirements 5.2, 5.3, 5.4**
    """
    # Feature: openenv-email-triage, Property 3: Priority scoring by distance
    email = _make_email("m001")
    ground_truth = {
        "email_id": "m001",
        "priority": gt_priority,
        "reply_required": False,
    }
    action = Action(operation=Operation.prioritize, priority=submitted)

    grader = TriageGrader()
    reward = grader.score_step(email, action, ground_truth)

    distance = abs(submitted - gt_priority)
    if distance == 0:
        expected_priority_sub = 1.0
    elif distance == 1:
        expected_priority_sub = 0.5
    else:
        expected_priority_sub = 0.0

    assert reward.partial_scores["priority"] == expected_priority_sub
    assert email.id in reward.rationale
    # reply_sub should be 0.0 (no reply this step, reply_required=False)
    assert reward.partial_scores["reply"] == 0.0
    # per-email score = mean(priority_sub, reply_sub)
    expected_score = (expected_priority_sub + 0.0) / 2.0
    assert abs(reward.score - expected_score) < 1e-9


# ---------------------------------------------------------------------------
# Property 14: Grader score formula — triage_medium
# Validates: Requirements 5.7
# ---------------------------------------------------------------------------

@given(
    per_email_priority_subs=st.lists(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        min_size=1,
        max_size=15,
    ),
    per_email_reply_subs=st.lists(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        min_size=1,
        max_size=15,
    ),
)
@settings(max_examples=100)
def test_p14_triage_medium_episode_score_formula(
    per_email_priority_subs: list[float],
    per_email_reply_subs: list[float],
) -> None:
    """Episode score equals arithmetic mean of per-email scores,
    where each per-email score = mean(priority_sub, reply_sub).

    **Validates: Requirements 5.7**
    """
    # Feature: openenv-email-triage, Property 14: Grader score formula — triage_medium
    n = min(len(per_email_priority_subs), len(per_email_reply_subs))
    priority_subs = per_email_priority_subs[:n]
    reply_subs = per_email_reply_subs[:n]

    # Build synthetic history using Reward objects directly
    emails = [_make_email(f"e{i:03d}") for i in range(n)]
    history: list[tuple[Action, Reward]] = []

    for i in range(n):
        p_sub = priority_subs[i]
        r_sub = reply_subs[i]
        per_email = (p_sub + r_sub) / 2.0
        per_email_clamped = max(0.0, min(1.0, per_email))
        reward = Reward(
            score=per_email_clamped,
            partial_scores={"priority": p_sub, "reply": r_sub},
            rationale=f"Email e{i:03d}: synthetic step.",
        )
        action = Action(operation=Operation.prioritize, priority=1)
        history.append((action, reward))

    grader = TriageGrader()
    episode_reward = grader.score_episode(history, emails)

    # Expected: arithmetic mean of per-email scores
    per_email_scores = [(p + r) / 2.0 for p, r in zip(priority_subs, reply_subs)]
    per_email_clamped = [max(0.0, min(1.0, s)) for s in per_email_scores]
    expected = sum(per_email_clamped) / n

    assert abs(episode_reward.score - expected) < 1e-9
