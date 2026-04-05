"""EmailTriageEnv: core environment class for OpenEnv Email Triage."""
from __future__ import annotations

import json

from openenv_email_triage.fixture_loader import FixtureLoader
from openenv_email_triage.graders import GraderRegistry, ManageGrader
from openenv_email_triage.models import Action, Email, Observation, Reward
from openenv_email_triage.reward_calculator import RewardCalculator


class EmailTriageEnv:
    """Stateful RL environment for email triage.

    Usage::

        env = EmailTriageEnv()
        obs = env.reset("categorize_easy")
        while True:
            action = agent.act(obs)
            obs, reward, done, info = env.step(action)
            if done:
                break
    """

    def __init__(self) -> None:
        self._fixture_loader = FixtureLoader()
        self._task_id: str = ""
        self._inbox: list[Email] = []
        self._ground_truths: list[dict] = []
        self._step: int = 0
        self._done: bool = False
        self._history: list[tuple[Action, Reward]] = []
        self._consecutive_skips: int = 0
        self._grader_registry: GraderRegistry = GraderRegistry()
        self._reward_calculator: RewardCalculator | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reset(self, task_id: str) -> Observation:
        """Initialize a new episode for *task_id* and return the first Observation.

        Args:
            task_id: One of "categorize_easy", "triage_medium", "manage_hard".

        Returns:
            The first Observation (step_number=0).

        Raises:
            FileNotFoundError: If the fixture file is missing.
            ValueError: If the fixture checksum is invalid or task_id is unknown.
        """
        fixture = self._fixture_loader.load(task_id)

        # Fresh GraderRegistry with a new ManageGrader instance for loop detection
        self._grader_registry = GraderRegistry()
        # Override manage_hard grader with a fresh instance to reset loop state
        self._grader_registry._registry["manage_hard"] = ManageGrader()

        grader = self._grader_registry.get(task_id)
        self._reward_calculator = RewardCalculator(grader)

        self._task_id = task_id
        self._step = 0
        self._done = False
        self._history = []
        self._consecutive_skips = 0

        self._inbox = [
            Email.model_validate(e, strict=False) for e in fixture.emails
        ]
        self._ground_truths = fixture.ground_truth

        return Observation(
            email=self._inbox[0],
            inbox_size=len(self._inbox),
            step_number=0,
            task_id=self._task_id,
        )

    def step(self, action: Action) -> tuple[Observation | None, Reward, bool, dict]:
        """Apply *action* to the current email and advance the episode.

        Args:
            action: The action to apply.

        Returns:
            A tuple of (Observation, Reward, done, info).
            When done=True, Observation is the last email's observation with
            step_number equal to the inbox size.

        Raises:
            RuntimeError: If called after the episode has ended.
        """
        if self._done:
            raise RuntimeError(
                "Episode has ended. Call reset() to start a new episode."
            )

        current_email = self._inbox[self._step]
        ground_truth = self._ground_truths[self._step]

        assert self._reward_calculator is not None
        reward = self._reward_calculator.calculate(
            current_email, action, ground_truth, self._consecutive_skips
        )

        # Update consecutive skip counter
        if action.operation == "skip":
            self._consecutive_skips += 1
        else:
            self._consecutive_skips = 0

        self._history.append((action, reward))
        self._step += 1

        if self._step >= len(self._inbox):
            self._done = True
            grader = self._grader_registry.get(self._task_id)
            final_reward = grader.score_episode(self._history, self._inbox)

            # Return the last email's observation with step_number = inbox size
            terminal_obs = Observation(
                email=current_email,
                inbox_size=len(self._inbox),
                step_number=self._step,
                task_id=self._task_id,
            )
            return terminal_obs, final_reward, True, {}

        next_obs = Observation(
            email=self._inbox[self._step],
            inbox_size=len(self._inbox),
            step_number=self._step,
            task_id=self._task_id,
        )
        return next_obs, reward, False, {}

    def state(self) -> dict:
        """Return a JSON-serializable snapshot of the current episode state.

        Returns:
            A dict with task_id, step, done, inbox_size, and history.
        """
        return {
            "task_id": self._task_id,
            "step": self._step,
            "done": self._done,
            "inbox_size": len(self._inbox),
            "history": [
                {
                    "action": action.model_dump(),
                    "reward": reward.model_dump(),
                }
                for action, reward in self._history
            ],
        }

    def render(self) -> str:
        """Return a human-readable summary of the current observation.

        Returns:
            A formatted string describing the current email and episode state.
        """
        if not self._inbox:
            return "No active episode. Call reset() to start."

        if self._done:
            return (
                f"Episode complete. Task: {self._task_id}, "
                f"Steps: {self._step}/{len(self._inbox)}"
            )

        email = self._inbox[self._step] if self._step < len(self._inbox) else self._inbox[-1]
        return (
            f"Task: {self._task_id} | Step: {self._step}/{len(self._inbox)}\n"
            f"Email ID: {email.id}\n"
            f"From: {email.sender}\n"
            f"Subject: {email.subject}\n"
            f"Body: {email.body[:200]}{'...' if len(email.body) > 200 else ''}"
        )

    def get_fixture_version(self) -> str:
        """Return the fixture version string for the current task.

        Returns:
            The fixture_version string from the loaded fixture.
        """
        fixture = self._fixture_loader.load(self._task_id)
        return fixture.fixture_version
