"""Inference script for OpenEnv Email Triage.

Runs the configured model against all three tasks.

Usage::

    API_BASE_URL=https://... MODEL_NAME=gpt-4o-mini python inference.py
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

from openai import OpenAI

from openenv_email_triage.env import EmailTriageEnv
from openenv_email_triage.models import Action, Operation

# Environment variables with defaults
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")  # HF Router
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")  # HF Model
HF_TOKEN = os.getenv("HF_TOKEN")  # Required
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")  # Optional, for from_docker_image()

TASKS = ["categorize_easy", "triage_medium", "manage_hard"]

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


def _get_client() -> OpenAI:
    """Create OpenAI client configured via environment variables."""
    api_key = os.environ.get("HF_TOKEN")
    if not api_key:
        raise EnvironmentError("HF_TOKEN environment variable is not set")
    return OpenAI(api_key=api_key, base_url=API_BASE_URL)


def _parse_action(content: str) -> Action:
    """Parse model response as an Action; fall back to skip on error."""
    try:
        data = json.loads(content)
        return Action.model_validate(data, strict=False)
    except Exception:
        return Action(operation=Operation.skip)


def run_inference(client: OpenAI) -> dict:
    """Run inference against all three tasks and return results dict."""
    env = EmailTriageEnv()
    task_scores: dict[str, float] = {}

    for task_id in TASKS:
        print(f"[START] task={task_id}", flush=True)

        obs = env.reset(task_id)
        done = False
        step_num = 0
        episode_score = 0.0

        while not done:
            step_num += 1
            obs_json = obs.model_dump_json()

            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
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
                print(
                    f"API error on task {task_id} step {step_num}: {exc}",
                    file=sys.stderr,
                    flush=True,
                )
                action = Action(operation=Operation.skip)

            obs, reward, done, _ = env.step(action)
            print(f"[STEP] step={step_num} reward={reward.score}", flush=True)
            if done:
                episode_score = reward.score

        task_scores[task_id] = round(episode_score, 4)

        print(
            f"[END] task={task_id} score={episode_score} steps={step_num}",
            flush=True,
        )

    mean_score = round(sum(task_scores.values()) / len(task_scores), 4)

    return {
        "model": MODEL_NAME,
        "api_base_url": API_BASE_URL,
        "task_scores": task_scores,
        "mean_score": mean_score,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    """Entry point: validate configuration, run inference, write results."""
    client = _get_client()
    results = run_inference(client)

    output_path = "inference_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults written to {output_path}")
    print(f"Mean score: {results['mean_score']:.4f}")


if __name__ == "__main__":
    main()
