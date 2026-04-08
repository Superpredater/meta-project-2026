"""Baseline inference script for OpenEnv Email Triage.

Runs gpt-4o-mini against all three tasks and writes baseline_results.json.

Usage::

    OPENAI_API_KEY=sk-... python baseline.py
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

from openenv_email_triage.env import EmailTriageEnv
from openenv_email_triage.models import Action, Operation

logger = logging.getLogger(__name__)

TASKS = ["categorize_easy", "triage_medium", "manage_hard"]
MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = """\
You are an email triage agent. You process emails one at a time and decide how to handle each one.

Available operations:
- categorize: Assign a label to the email. Set "label" to one of: spam, billing, support, general.
- prioritize: Assign a priority level. Set "priority" to 1 (high), 2 (medium), or 3 (low).
- reply: Draft a reply. Set "reply_text" to a non-empty string.
- escalate: Escalate the email to a human agent.
- archive: Archive the email.
- delete: Delete the email.
- skip: Skip the email without taking action.

Respond with a JSON object matching the Action schema:
{
  "operation": "<one of the operations above>",
  "label": "<optional, for categorize>",
  "priority": <optional int 1-3, for prioritize>,
  "reply_text": "<optional string, for reply>"
}

Only include fields relevant to the chosen operation. Respond with valid JSON only — no extra text.
"""


def _get_api_key() -> str:
    """Read OPENAI_API_KEY from environment or raise EnvironmentError."""
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise EnvironmentError("OPENAI_API_KEY environment variable is not set")
    return key


def _parse_action(content: str) -> Action:
    """Parse model response as an Action; fall back to skip on error."""
    try:
        data = json.loads(content)
        return Action.model_validate(data, strict=False)
    except Exception:
        return Action(operation=Operation.skip)


def run_baseline(client) -> dict:
    """Run the baseline against all three tasks and return results dict."""
    env = EmailTriageEnv()
    task_scores: dict[str, float] = {}

    for task_id in TASKS:
        obs = env.reset(task_id)
        done = False
        step_scores: list[float] = []

        while not done:
            obs_json = obs.model_dump_json()

            try:
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": obs_json},
                    ],
                    temperature=0,
                    seed=42,
                )
                content = response.choices[0].message.content or ""
                action = _parse_action(content)
            except Exception as exc:
                logger.error("OpenAI API error on task %s step %d: %s", task_id, obs.step_number, exc)
                action = Action(operation=Operation.skip)
                obs, reward, done, _ = env.step(action)
                step_scores.append(0.0)
                continue

            obs, reward, done, _ = env.step(action)
            step_scores.append(reward.score)

        # Use the final episode-level score from the last reward
        episode_score = reward.score  # type: ignore[possibly-undefined]
        task_scores[task_id] = round(episode_score, 4)
        print(f"Task: {task_id:20s}  score: {episode_score:.4f}")

    mean_score = round(sum(task_scores.values()) / len(task_scores), 4)
    print(f"\nMean score: {mean_score:.4f}")

    return {
        "model": MODEL,
        "task_scores": task_scores,
        "mean_score": mean_score,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    """Entry point: validate API key, run baseline, write results."""
    logging.basicConfig(level=logging.INFO)

    api_key = _get_api_key()

    from openai import OpenAI  # noqa: PLC0415 — deferred to allow testing without openai installed

    client = OpenAI(api_key=api_key)
    results = run_baseline(client)

    output_path = "baseline_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults written to {output_path}")


if __name__ == "__main__":
    main()
