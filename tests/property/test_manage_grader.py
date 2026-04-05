"""Property-based tests for ManageGrader.

# Feature: openenv-email-triage, Property 4: Correct operation scoring in manage_hard
# Feature: openenv-email-triage, Property 11: Loop detection penalty
# Feature: openenv-email-triage, Property 12: Final score clamping
# Feature: openenv-email-triage, Property 15: manage_hard weighted mean formula
"""
from __future__ import annotations

from datetime import datetime, timezone

from hypothesis import given, settings
from hypothesis import strategies as st

from openenv_email_triage.graders import ManageGrader
from openenv_email_triage.models import Action, Email, Operation, Reward

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_LABELS = ["spam", "billing", "support", "general"]
_PRIORITIES = [1, 2, 3]


def _make_email(email_id: str = "h001") -> Email:
    return Email(
        id=email_id,
        subject="Test subject",
        sender="test@example.com",
        body="Test body",
        timestamp=datetime(2024, 1, 17, 7, 0, 0, tzinfo=timezone.utc),
        thread_id="th001",
        labels=[],
        attachments=[],
    )


def _make_ground_truth(
    email_id: str = "h001",
    label: str = "support",
    priority: int = 1,
    reply_required: bool = False,
    escalate: bool = False,
    should_archive: bool = False,
    should_delete: bool = False,
) -> dict:
    return {
        "email_id": email_id,
        "label": label,
        "priority": priority,
        "reply_required": reply_required,
        "escalate": escalate,
        "should_archive": should_archive,
        "should_delete": should_delete,
    }


# ---------------------------------------------------------------------------
# Property 4: Correct operation scoring in manage_hard
# Validates: Requirements 6.3, 6.4, 6.5, 6.6
# ---------------------------------------------------------------------------

@given(
    label=st.sampled_from(_LABELS),
    gt_priority=st.integers(min_value=1, max_value=3),
    submitted_priority=st.integers(min_value=1, max_value=3),
    reply_required=st.booleans(),
    reply_text=st.one_of(st.none(), st.text(min_size=0, max_size=50)),
    escalate_gt=st.booleans(),
    should_archive_gt=st.booleans(),
    should_delete_gt=st.booleans(),
    operation=st.sampled_from([
        Operation.escalate,
        Operation.delete,
        Operation.archive,
        Operation.categorize,
        Operation.prioritize,
        Operation.reply,
        Operation.skip,
    ]),
    submitted_label=st.sampled_from(_LABELS),
)
@settings(max_examples=100)
def test_p4_correct_operation_scoring(
    label: str,
    gt_priority: int,
    submitted_priority: int,
    reply_required: bool,
    reply_text: str | None,
    escalate_gt: bool,
    should_archive_gt: bool,
    should_delete_gt: bool,
    operation: Operation,
    submitted_label: str,
) -> None:
    """Applying the matching ground-truth operation yields 1.0 sub-score;
    delete when should_delete=False yields -0.5.

    **Validates: Requirements 6.3, 6.4, 6.5, 6.6**
    """
    # Feature: openenv-email-triage, Property 4: Correct operation scoring in manage_hard
    email = _make_email("h001")
    gt = _make_ground_truth(
        label=label,
        priority=gt_priority,
        reply_required=reply_required,
        escalate=escalate_gt,
        should_archive=should_archive_gt,
        should_delete=should_delete_gt,
    )

    if operation == Operation.categorize:
        action = Action(operation=operation, label=submitted_label)
    elif operation == Operation.prioritize:
        action = Action(operation=operation, priority=submitted_priority)
    elif operation == Operation.reply:
        action = Action(operation=operation, reply_text=reply_text)
    else:
        action = Action(operation=operation)

    grader = ManageGrader()
    reward = grader.score_step(email, action, gt)

    ps = reward.partial_scores

    # Verify per-operation sub-score rules
    if operation == Operation.escalate:
        expected_esc = 1.0 if escalate_gt else 0.0
        assert ps["escalation"] == expected_esc

    elif operation == Operation.delete:
        if should_delete_gt:
            assert ps["archive_delete"] == 1.0
        else:
            assert ps["archive_delete"] == -0.5

    elif operation == Operation.archive:
        expected_arch = 1.0 if should_archive_gt else 0.0
        assert ps["archive_delete"] == expected_arch

    elif operation == Operation.categorize:
        expected_cat = 1.0 if submitted_label == label else 0.0
        assert ps["categorization"] == expected_cat

    elif operation == Operation.prioritize:
        distance = abs(submitted_priority - gt_priority)
        if distance == 0:
            expected_pri = 1.0
        elif distance == 1:
            expected_pri = 0.5
        else:
            expected_pri = 0.0
        assert ps["priority"] == expected_pri

    elif operation == Operation.reply:
        has_text = bool(reply_text and reply_text.strip())
        if reply_required and has_text:
            assert ps["reply"] == 1.0
        elif reply_required and not has_text:
            assert ps["reply"] == 0.0
        else:
            assert ps["reply"] == 0.5

    elif operation == Operation.skip:
        assert ps["categorization"] == 0.0
        assert ps["priority"] == 0.0
        assert ps["reply"] == 0.0
        assert ps["escalation"] == 0.0
        assert ps["archive_delete"] == 0.0

    # Rationale must reference the email id
    assert email.id in reward.rationale


# ---------------------------------------------------------------------------
# Property 11: Loop detection penalty
# Validates: Requirements 6.7
# ---------------------------------------------------------------------------

@given(
    email_id=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
    n_repeats=st.integers(min_value=2, max_value=5),
)
@settings(max_examples=100)
def test_p11_loop_detection_penalty(email_id: str, n_repeats: int) -> None:
    """Processing the same email id more than once incurs a 0.1 penalty per duplicate step.

    **Validates: Requirements 6.7**
    """
    # Feature: openenv-email-triage, Property 11: Loop detection penalty
    email = _make_email(email_id)
    gt = _make_ground_truth(email_id=email_id)
    action = Action(operation=Operation.skip)

    grader = ManageGrader()

    # First occurrence — no penalty
    first_reward = grader.score_step(email, action, gt)
    # skip gives raw_score=0.0, no loop penalty on first visit
    assert first_reward.score == 0.0

    # Subsequent occurrences — each should have loop penalty applied
    for _ in range(n_repeats - 1):
        dup_reward = grader.score_step(email, action, gt)
        # skip raw_score=0.0, loop penalty=0.1 → clamped to 0.0
        # The penalty is subtracted: 0.0 - 0.1 = -0.1, clamped to 0.0
        assert dup_reward.score == 0.0
        assert "loop penalty" in dup_reward.rationale

    # Now test with a non-zero base score to confirm penalty is actually subtracted
    grader2 = ManageGrader()
    gt_esc = _make_ground_truth(email_id=email_id, escalate=True)
    action_esc = Action(operation=Operation.escalate)

    first = grader2.score_step(email, action_esc, gt_esc)
    # escalate=True → esc_sub=1.0, raw = 0.15*1.0 = 0.15, no penalty
    assert abs(first.score - 0.15) < 1e-9

    second = grader2.score_step(email, action_esc, gt_esc)
    # same email again → penalty 0.1 → 0.15 - 0.1 = 0.05
    assert abs(second.score - 0.05) < 1e-9
    assert "loop penalty" in second.rationale


# ---------------------------------------------------------------------------
# Property 12: Final score clamping
# Validates: Requirements 6.8
# ---------------------------------------------------------------------------

@given(
    cat_subs=st.lists(
        st.floats(min_value=-1.0, max_value=1.0, allow_nan=False),
        min_size=1, max_size=25,
    ),
    pri_subs=st.lists(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        min_size=1, max_size=25,
    ),
    reply_subs=st.lists(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        min_size=1, max_size=25,
    ),
    esc_subs=st.lists(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        min_size=1, max_size=25,
    ),
    arch_del_subs=st.lists(
        st.floats(min_value=-0.5, max_value=1.0, allow_nan=False),
        min_size=1, max_size=25,
    ),
)
@settings(max_examples=100)
def test_p12_final_score_clamping(
    cat_subs: list[float],
    pri_subs: list[float],
    reply_subs: list[float],
    esc_subs: list[float],
    arch_del_subs: list[float],
) -> None:
    """Episode-level score is always in [0.0, 1.0] regardless of penalties.

    **Validates: Requirements 6.8**
    """
    # Feature: openenv-email-triage, Property 12: Final score clamping
    n = min(len(cat_subs), len(pri_subs), len(reply_subs), len(esc_subs), len(arch_del_subs))
    history: list[tuple[Action, Reward]] = []

    for i in range(n):
        reward = Reward(
            score=max(0.0, min(1.0, (cat_subs[i] + pri_subs[i] + reply_subs[i] + esc_subs[i]) / 4.0)),
            partial_scores={
                "categorization": cat_subs[i],
                "priority": pri_subs[i],
                "reply": reply_subs[i],
                "escalation": esc_subs[i],
                "archive_delete": arch_del_subs[i],
            },
            rationale=f"Email e{i:03d}: synthetic step.",
        )
        action = Action(operation=Operation.skip)
        history.append((action, reward))

    grader = ManageGrader()
    episode_reward = grader.score_episode(history, [])

    assert 0.0 <= episode_reward.score <= 1.0


# ---------------------------------------------------------------------------
# Property 15: manage_hard weighted mean formula
# Validates: Requirements 6.2
# ---------------------------------------------------------------------------

@given(
    cat_subs=st.lists(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        min_size=1, max_size=25,
    ),
    pri_subs=st.lists(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        min_size=1, max_size=25,
    ),
    reply_subs=st.lists(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        min_size=1, max_size=25,
    ),
    esc_subs=st.lists(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        min_size=1, max_size=25,
    ),
    arch_del_subs=st.lists(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        min_size=1, max_size=25,
    ),
)
@settings(max_examples=100)
def test_p15_manage_hard_weighted_mean_formula(
    cat_subs: list[float],
    pri_subs: list[float],
    reply_subs: list[float],
    esc_subs: list[float],
    arch_del_subs: list[float],
) -> None:
    """Episode score equals 0.25*cat + 0.25*pri + 0.20*reply + 0.15*esc + 0.15*arch_del.

    **Validates: Requirements 6.2**
    """
    # Feature: openenv-email-triage, Property 15: manage_hard weighted mean formula
    n = min(len(cat_subs), len(pri_subs), len(reply_subs), len(esc_subs), len(arch_del_subs))
    history: list[tuple[Action, Reward]] = []

    for i in range(n):
        reward = Reward(
            score=max(0.0, min(1.0, (cat_subs[i] + pri_subs[i]) / 2.0)),
            partial_scores={
                "categorization": cat_subs[i],
                "priority": pri_subs[i],
                "reply": reply_subs[i],
                "escalation": esc_subs[i],
                "archive_delete": arch_del_subs[i],
            },
            rationale=f"Email e{i:03d}: synthetic step.",
        )
        action = Action(operation=Operation.skip)
        history.append((action, reward))

    grader = ManageGrader()
    episode_reward = grader.score_episode(history, [])

    # Compute expected weighted mean
    avg_cat = sum(cat_subs[:n]) / n
    avg_pri = sum(pri_subs[:n]) / n
    avg_reply = sum(reply_subs[:n]) / n
    avg_esc = sum(esc_subs[:n]) / n
    avg_arch_del = sum(arch_del_subs[:n]) / n

    expected_weighted = (
        0.25 * avg_cat
        + 0.25 * avg_pri
        + 0.20 * avg_reply
        + 0.15 * avg_esc
        + 0.15 * avg_arch_del
    )
    expected_score = max(0.0, min(1.0, expected_weighted))

    assert abs(episode_reward.score - expected_score) < 1e-9
