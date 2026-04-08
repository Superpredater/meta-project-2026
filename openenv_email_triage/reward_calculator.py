"""RewardCalculator: wraps a grader and applies the consecutive skip penalty."""
from __future__ import annotations

from openenv_email_triage.graders import GraderProtocol
from openenv_email_triage.models import Action, Email, Reward


class RewardCalculator:
    """Computes per-step Reward objects, applying the consecutive skip penalty.

    The consecutive skip penalty applies when ``consecutive_skips >= 3``
    (i.e., this is the 4th or later consecutive skip in a row) AND the
    current action is also a skip.  In that case 0.05 is subtracted from
    the base score, clamped to [0.0, 1.0].
    """

    def __init__(self, grader: GraderProtocol) -> None:
        self._grader = grader

    def calculate(
        self,
        email: Email,
        action: Action,
        ground_truth: dict,
        consecutive_skips: int,
    ) -> Reward:
        """Calculate the reward for a single step.

        Args:
            email: The email being processed.
            action: The action taken by the agent.
            ground_truth: Ground-truth annotations for this email.
            consecutive_skips: Number of consecutive skips *before* this action.

        Returns:
            A Reward, possibly penalized for excessive consecutive skips.
        """
        base_reward = self._grader.score_step(email, action, ground_truth)

        # Apply consecutive skip penalty: if this is the 4th+ consecutive skip
        if consecutive_skips >= 3 and action.operation == "skip":
            penalized_score = max(0.0, min(1.0, base_reward.score - 0.05))
            return Reward(
                score=penalized_score,
                partial_scores=base_reward.partial_scores,
                rationale=(
                    f"{base_reward.rationale} "
                    f"[consecutive skip penalty -0.05 applied; "
                    f"consecutive_skips={consecutive_skips}]"
                ),
            )

        return base_reward
