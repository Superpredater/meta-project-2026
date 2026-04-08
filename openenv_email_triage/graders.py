"""Grader protocol and concrete grader implementations for OpenEnv Email Triage."""
from __future__ import annotations

from typing import Protocol

from openenv_email_triage.models import Action, Email, Reward


class GraderProtocol(Protocol):
    """Protocol that all grader implementations must satisfy."""

    def score_step(
        self, email: Email, action: Action, ground_truth: dict
    ) -> Reward:
        """Score a single agent step.

        Args:
            email: The email being processed.
            action: The action taken by the agent.
            ground_truth: Ground-truth annotations for this email.

        Returns:
            A Reward for this step.
        """
        ...

    def score_episode(
        self,
        history: list[tuple[Action, Reward]],
        inbox: list[Email],
    ) -> Reward:
        """Score a completed episode.

        Args:
            history: Ordered list of (action, reward) pairs from the episode.
            inbox: The full inbox used in the episode.

        Returns:
            An aggregate Reward for the entire episode.
        """
        ...


class CategorizeGrader:
    """Grader for the ``categorize_easy`` task.

    Per-step scoring:
        - 1.0 if ``action.operation == "categorize"`` AND
          ``action.label == ground_truth["label"]``
        - 0.0 otherwise (wrong label, wrong operation, or skip)

    Episode scoring:
        - ``correct_count / 10``  (fraction of correctly labelled emails)
    """

    def score_step(
        self, email: Email, action: Action, ground_truth: dict
    ) -> Reward:
        correct = (
            action.operation == "categorize"
            and action.label == ground_truth.get("label")
        )
        raw_score = 1.0 if correct else 0.0
        # Clamp to satisfy Reward.score ge=0.0, le=1.0 constraint.
        score = max(0.0, min(1.0, raw_score))

        gt_label = ground_truth.get("label", "<unknown>")
        if correct:
            rationale = (
                f"Email {email.id}: correctly categorized as '{gt_label}'."
            )
        else:
            rationale = (
                f"Email {email.id}: expected label '{gt_label}', "
                f"got operation='{action.operation}' label='{action.label}'."
            )

        return Reward(
            score=score,
            partial_scores={"categorization": score},
            rationale=rationale,
        )

    def score_episode(
        self,
        history: list[tuple[Action, Reward]],
        inbox: list[Email],
    ) -> Reward:
        correct_count = sum(
            1 for _action, reward in history if reward.score == 1.0
        )
        raw_score = correct_count / 10
        score = max(0.0, min(1.0, raw_score))

        rationale = (
            f"Episode complete: {correct_count}/10 emails correctly categorized."
        )

        return Reward(
            score=score,
            partial_scores={"categorization": score},
            rationale=rationale,
        )


class TriageGrader:
    """Grader for the ``triage_medium`` task.

    Per-step scoring (action can only be one operation at a time):
        - ``prioritize`` action: compute priority sub-score; reply sub-score
          reflects whether a reply was needed (0.0 if reply_required else 0.0).
        - ``reply`` action: compute reply sub-score; priority sub-score = 0.0.

    Priority sub-score:
        - 1.0 when |submitted - ground_truth| == 0
        - 0.5 when |submitted - ground_truth| == 1
        - 0.0 when |submitted - ground_truth| == 2

    Reply sub-score:
        - 1.0 when reply_required=True  AND operation=="reply" AND non-empty reply_text
        - 0.0 when reply_required=True  AND operation!="reply"
        - 0.5 when reply_required=False AND operation=="reply"
        - 0.0 when reply_required=False AND operation!="reply"

    Per-email score = mean(priority_sub_score, reply_sub_score)
    Episode score   = arithmetic mean of all per-email scores
    """

    def score_step(
        self, email: Email, action: Action, ground_truth: dict
    ) -> Reward:
        reply_required: bool = ground_truth.get("reply_required", False)
        gt_priority: int = ground_truth.get("priority", 2)

        if action.operation == "prioritize":
            submitted = action.priority if action.priority is not None else 2
            distance = abs(submitted - gt_priority)
            if distance == 0:
                priority_sub = 1.0
            elif distance == 1:
                priority_sub = 0.5
            else:
                priority_sub = 0.0

            # Reply sub-score: agent did not reply this step
            reply_sub = 0.0

            rationale = (
                f"Email {email.id}: prioritize action — priority sub-score "
                f"{priority_sub} (submitted={submitted}, gt={gt_priority}); "
                f"reply sub-score {reply_sub} (reply_required={reply_required}, no reply this step)."
            )

        elif action.operation == "reply":
            # Priority not provided this step
            priority_sub = 0.0

            has_text = bool(action.reply_text and action.reply_text.strip())
            if reply_required and has_text:
                reply_sub = 1.0
            elif reply_required and not has_text:
                reply_sub = 0.0
            elif not reply_required:
                reply_sub = 0.5
            else:
                reply_sub = 0.0

            rationale = (
                f"Email {email.id}: reply action — priority sub-score "
                f"{priority_sub} (not provided this step); "
                f"reply sub-score {reply_sub} (reply_required={reply_required}, "
                f"has_text={has_text})."
            )

        else:
            # Any other operation (skip, categorize, etc.) scores 0 on both
            priority_sub = 0.0
            reply_sub = 0.0
            rationale = (
                f"Email {email.id}: operation '{action.operation}' — "
                f"priority sub-score 0.0, reply sub-score 0.0."
            )

        per_email_score = (priority_sub + reply_sub) / 2.0
        score = max(0.0, min(1.0, per_email_score))

        return Reward(
            score=score,
            partial_scores={"priority": priority_sub, "reply": reply_sub},
            rationale=rationale,
        )

    def score_episode(
        self,
        history: list[tuple[Action, Reward]],
        inbox: list[Email],
    ) -> Reward:
        if not history:
            return Reward(
                score=0.0,
                partial_scores={"priority": 0.0, "reply": 0.0},
                rationale="Episode complete: no steps recorded.",
            )

        per_email_scores = [reward.score for _action, reward in history]
        episode_score = sum(per_email_scores) / len(per_email_scores)
        score = max(0.0, min(1.0, episode_score))

        rationale = (
            f"Episode complete: mean per-email score = {score:.4f} "
            f"over {len(history)} steps."
        )

        avg_priority = sum(
            r.partial_scores.get("priority", 0.0) for _, r in history
        ) / len(history)
        avg_reply = sum(
            r.partial_scores.get("reply", 0.0) for _, r in history
        ) / len(history)

        return Reward(
            score=score,
            partial_scores={"priority": avg_priority, "reply": avg_reply},
            rationale=rationale,
        )


class ManageGrader:
    """Grader for the ``manage_hard`` task.

    Per-step scoring (one operation at a time):
        - ``escalate``:   1.0 if ground_truth["escalate"] == True, else 0.0
        - ``delete``:     1.0 if ground_truth["should_delete"] == True, else -0.5
        - ``archive``:    1.0 if ground_truth["should_archive"] == True, else 0.0
        - ``categorize``: 1.0 if action.label == ground_truth["label"], else 0.0
        - ``prioritize``: 1.0/0.5/0.0 for distance 0/1/2 from ground_truth["priority"]
        - ``reply``:      1.0 if reply_required=True and non-empty reply_text,
                          0.5 if reply_required=False, 0.0 if reply_required=True and no text
        - ``skip``:       0.0 on all sub-scores

    Loop detection: if the same email id is processed more than once, subtract 0.1
    from that step's score.

    Episode scoring: weighted mean clamped to [0.0, 1.0]:
        0.25*cat + 0.25*pri + 0.20*reply + 0.15*esc + 0.15*arch_del
    """

    def __init__(self) -> None:
        self._seen_ids: set[str] = set()

    def score_step(
        self, email: Email, action: Action, ground_truth: dict
    ) -> Reward:
        op = action.operation

        # --- per-dimension sub-scores ---
        cat_sub = 0.0
        pri_sub = 0.0
        reply_sub = 0.0
        esc_sub = 0.0
        arch_del_sub = 0.0

        if op == "categorize":
            cat_sub = 1.0 if action.label == ground_truth.get("label") else 0.0

        elif op == "prioritize":
            gt_priority = ground_truth.get("priority", 2)
            submitted = action.priority if action.priority is not None else 2
            distance = abs(submitted - gt_priority)
            if distance == 0:
                pri_sub = 1.0
            elif distance == 1:
                pri_sub = 0.5
            else:
                pri_sub = 0.0

        elif op == "reply":
            reply_required: bool = ground_truth.get("reply_required", False)
            has_text = bool(action.reply_text and action.reply_text.strip())
            if reply_required and has_text:
                reply_sub = 1.0
            elif reply_required and not has_text:
                reply_sub = 0.0
            else:
                reply_sub = 0.5

        elif op == "escalate":
            esc_sub = 1.0 if ground_truth.get("escalate") is True else 0.0

        elif op == "archive":
            arch_del_sub = 1.0 if ground_truth.get("should_archive") is True else 0.0

        elif op == "delete":
            arch_del_sub = 1.0 if ground_truth.get("should_delete") is True else -0.5

        # skip: all sub-scores remain 0.0

        partial: dict[str, float] = {
            "categorization": cat_sub,
            "priority": pri_sub,
            "reply": reply_sub,
            "escalation": esc_sub,
            "archive_delete": arch_del_sub,
        }

        # Raw step score: mean of the five dimensions
        raw_score = (
            0.25 * cat_sub
            + 0.25 * pri_sub
            + 0.20 * reply_sub
            + 0.15 * esc_sub
            + 0.15 * arch_del_sub
        )

        # Loop detection penalty
        loop_penalty = 0.0
        if email.id in self._seen_ids:
            loop_penalty = 0.1
        self._seen_ids.add(email.id)

        step_score = raw_score - loop_penalty
        score = max(0.0, min(1.0, step_score))

        rationale = (
            f"Email {email.id}: op='{op}' — "
            f"cat={cat_sub:.2f}, pri={pri_sub:.2f}, reply={reply_sub:.2f}, "
            f"esc={esc_sub:.2f}, arch_del={arch_del_sub:.2f}"
            + (f"; loop penalty -{loop_penalty:.1f}" if loop_penalty else "")
            + f" → score={score:.4f}."
        )

        return Reward(score=score, partial_scores=partial, rationale=rationale)

    def score_episode(
        self,
        history: list[tuple[Action, Reward]],
        inbox: list[Email],
    ) -> Reward:
        if not history:
            return Reward(
                score=0.0,
                partial_scores={
                    "categorization": 0.0,
                    "priority": 0.0,
                    "reply": 0.0,
                    "escalation": 0.0,
                    "archive_delete": 0.0,
                },
                rationale="Episode complete: no steps recorded.",
            )

        n = len(history)

        avg_cat = sum(r.partial_scores.get("categorization", 0.0) for _, r in history) / n
        avg_pri = sum(r.partial_scores.get("priority", 0.0) for _, r in history) / n
        avg_reply = sum(r.partial_scores.get("reply", 0.0) for _, r in history) / n
        avg_esc = sum(r.partial_scores.get("escalation", 0.0) for _, r in history) / n
        avg_arch_del = sum(r.partial_scores.get("archive_delete", 0.0) for _, r in history) / n

        weighted = (
            0.25 * avg_cat
            + 0.25 * avg_pri
            + 0.20 * avg_reply
            + 0.15 * avg_esc
            + 0.15 * avg_arch_del
        )
        score = max(0.0, min(1.0, weighted))

        rationale = (
            f"Episode complete over {n} steps: "
            f"cat={avg_cat:.4f}, pri={avg_pri:.4f}, reply={avg_reply:.4f}, "
            f"esc={avg_esc:.4f}, arch_del={avg_arch_del:.4f} → "
            f"weighted={weighted:.4f}, clamped={score:.4f}."
        )

        return Reward(
            score=score,
            partial_scores={
                "categorization": avg_cat,
                "priority": avg_pri,
                "reply": avg_reply,
                "escalation": avg_esc,
                "archive_delete": avg_arch_del,
            },
            rationale=rationale,
        )


class GraderRegistry:
    """Maps task_id strings to grader instances."""

    def __init__(self) -> None:
        self._registry: dict[str, GraderProtocol] = {
            "categorize_easy": CategorizeGrader(),
            "triage_medium": TriageGrader(),
            "manage_hard": ManageGrader(),
        }

    def get(self, task_id: str) -> GraderProtocol:
        """Return the grader for the given task_id.

        Raises:
            ValueError: If task_id is not recognized.
        """
        if task_id not in self._registry:
            raise ValueError(f"Unknown task_id: {task_id}")
        return self._registry[task_id]
