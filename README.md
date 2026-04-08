---
title: OpenEnv Email Triage
emoji: 📧
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
tags:
  - openenv
  - reinforcement-learning
  - email-triage
---

# OpenEnv Email Triage

An inbox management reinforcement-learning benchmark environment. An AI agent processes emails one at a time, choosing from six operations — or skipping — and receives a reward signal after every step. The environment follows the standard OpenEnv interface (`reset` / `step` / `state`) and ships with three tasks of increasing difficulty.

## Motivation

Real-world inbox management requires a mix of classification, prioritization, communication, and triage decisions. This environment provides a reproducible, graded benchmark for evaluating how well an agent can handle that mix, with deterministic fixture data and partial reward signals at every step.

---

## Observation Space

Defined by `openenv_email_triage.models.Observation`:

| Field | Type | Description |
|---|---|---|
| `email` | `Email` | The current email to process |
| `inbox_size` | `int` | Total number of emails in the inbox |
| `step_number` | `int` | Current step index (0-indexed) |
| `task_id` | `str` | Identifier of the active task |

### Email fields

| Field | Type | Description |
|---|---|---|
| `id` | `str` | Unique email identifier |
| `subject` | `str` | Email subject line |
| `sender` | `str` | Sender address |
| `body` | `str` | Email body text |
| `timestamp` | `datetime` | Send time (ISO 8601) |
| `thread_id` | `str` | Conversation thread identifier |
| `labels` | `list[str]` | Existing labels on the email |
| `attachments` | `list[str]` | List of attachment filenames |

---

## Action Space

Defined by `openenv_email_triage.models.Action`:

| Field | Type | Description |
|---|---|---|
| `operation` | `Operation` | One of: `categorize`, `prioritize`, `reply`, `escalate`, `archive`, `delete`, `skip` |
| `label` | `str \| None` | Label to apply (used with `categorize`) |
| `priority` | `int \| None` | Priority level 1–3 (1=high; used with `prioritize`) |
| `reply_text` | `str \| None` | Reply body (used with `reply`) |

---

## Reward

Defined by `openenv_email_triage.models.Reward`:

| Field | Type | Description |
|---|---|---|
| `score` | `float` | Scalar reward in [0.0, 1.0] |
| `partial_scores` | `dict[str, float]` | Per-dimension breakdown |
| `rationale` | `str` | Human-readable explanation referencing the email id |

---

## Tasks

| Task ID | Difficulty | Inbox Size | Description |
|---|---|---|---|
| `categorize_easy` | Easy | 10 emails | Assign a single correct label to each email (spam, billing, support, general). Score = correct_count / 10. |
| `triage_medium` | Medium | 15 emails | Assign priority (1–3) and draft replies for emails with mixed urgency. Score = mean of per-email (priority + reply) sub-scores. |
| `manage_hard` | Hard | 25 emails | Apply all six operations across a mixed inbox. Score = weighted mean: categorization (0.25), priority (0.25), reply (0.20), escalation (0.15), archive/delete (0.15). |

### Scoring details

- **categorize_easy**: 1.0 for correct label, 0.0 for wrong label or skip.
- **triage_medium**: Priority sub-score is 1.0 / 0.5 / 0.0 for distance 0 / 1 / 2 from ground truth. Reply sub-score is 1.0 for a non-empty reply when required, 0.5 for an unnecessary reply, 0.0 if required but omitted.
- **manage_hard**: Escalate/archive/delete correct = 1.0; delete when `should_delete=False` = -0.5. Final score clamped to [0.0, 1.0].
- **Consecutive skip penalty**: >3 consecutive skips reduces the step reward by 0.05 per extra skip.
- **Loop detection penalty** (manage_hard): Processing the same email id more than once incurs a 0.1 penalty per duplicate step.

---

## Baseline Scores

| Model | categorize_easy | triage_medium | manage_hard | Mean |
|---|---|---|---|---|
| gpt-4o-mini | — | — | — | — |

*Scores will be populated after running `python baseline.py`.*

---

## Setup and Usage

### Prerequisites

- Python 3.11+
- An OpenAI API key (for the baseline script)

### Local

```bash
# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server
python main.py
# Server runs at http://localhost:7860
```

### Python API

```python
from openenv_email_triage.env import EmailTriageEnv
from openenv_email_triage.models import Action, Operation

env = EmailTriageEnv()

obs = env.reset("categorize_easy")
print(obs.email.subject)

action = Action(operation=Operation.categorize, label="spam")
obs, reward, done, info = env.step(action)
print(reward.score, reward.rationale)
```

### Baseline script

```bash
export OPENAI_API_KEY=sk-...
python baseline.py
# Writes baseline_results.json and prints per-task scores
```

### Docker

```bash
docker build -t openenv-email-triage .
docker run -p 7860:7860 -e OPENAI_API_KEY=sk-... openenv-email-triage
```

### Hugging Face Space

The environment is hosted at: https://huggingface.co/spaces/Superpredater231/openenv-email-triage

The Space uses the `docker` SDK. The `Dockerfile` at the repository root is the entry point.

---

## API Endpoints

| Method | Path | Body | Returns |
|---|---|---|---|
| `POST` | `/reset` | `{"task_id": "categorize_easy"}` | `Observation` |
| `POST` | `/step` | `Action` JSON | `{observation, reward, done, info}` |
| `GET` | `/state` | — | Episode state dict |
| `GET` | `/render` | — | `{"text": "..."}` |

### Example: reset

```bash
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "categorize_easy"}'
```

### Example: step

```bash
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{"operation": "categorize", "label": "spam"}'
```

---

## Fixture Data

Static fixture files live under `fixtures/`. Each file includes a `fixture_version` and a SHA-256 `checksum` that the environment verifies on load. Scores are fully reproducible across runs and agents.

---

## Running Tests

```bash
# Unit tests
pytest tests/unit/

# Property-based tests
pytest tests/property/

# All tests
pytest
```
