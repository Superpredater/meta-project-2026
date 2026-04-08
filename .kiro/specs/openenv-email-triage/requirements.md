# Requirements Document

## Introduction

OpenEnv Email Triage is a reinforcement-learning environment that simulates the real-world task of processing an inbox. An AI agent receives emails one at a time and must decide how to handle each one: categorize it, assign a priority, draft a reply, escalate, archive, or delete. The environment exposes the standard OpenEnv interface (reset / step / state) with typed Pydantic models, an openenv.yaml manifest, and a programmatic grader for each of three tasks of increasing difficulty. A baseline inference script runs an OpenAI-compatible model against all three tasks and reports reproducible scores. The project ships as a Hugging Face Space with a working Dockerfile.

---

## Glossary

- **Environment**: The OpenEnv Email Triage simulation that manages inbox state and evaluates agent actions.
- **Agent**: The software under evaluation that calls reset(), step(), and state() to interact with the Environment.
- **Observation**: A typed Pydantic model returned to the Agent after each step, describing the current email and inbox context.
- **Action**: A typed Pydantic model submitted by the Agent to step(), encoding the chosen operation on the current email.
- **Reward**: A typed Pydantic model returned alongside each Observation, carrying a scalar score in [0.0, 1.0] and a human-readable rationale.
- **Episode**: A single run from reset() through a terminal state, covering one Task.
- **Task**: A concrete objective the Agent must accomplish within one Episode, evaluated by a deterministic Grader.
- **Grader**: A pure function that maps the full Episode trajectory to a scalar score in [0.0, 1.0].
- **Inbox**: The ordered collection of Email objects available during an Episode.
- **Email**: A structured object with fields: id, subject, sender, body, timestamp, thread_id, labels, and attachments.
- **Label**: A string tag applied to an Email (e.g. "urgent", "spam", "billing", "support").
- **Priority**: An integer in {1, 2, 3} where 1 = high, 2 = medium, 3 = low.
- **Baseline**: The inference script that runs a fixed model against all three Tasks and records scores.
- **Space**: A Hugging Face Space hosting the Environment as a deployable service.

---

## Requirements

### Requirement 1: Typed Data Models

**User Story:** As an Agent developer, I want all inputs and outputs to use validated Pydantic models, so that I can rely on schema correctness without writing defensive parsing code.

#### Acceptance Criteria

1. THE Environment SHALL define an `Observation` Pydantic model with at minimum the fields: `email` (Email object), `inbox_size` (int), `step_number` (int), and `task_id` (str).
2. THE Environment SHALL define an `Action` Pydantic model with at minimum the fields: `operation` (enum: categorize | prioritize | reply | escalate | archive | delete | skip), `label` (optional str), `priority` (optional int in {1,2,3}), and `reply_text` (optional str).
3. THE Environment SHALL define a `Reward` Pydantic model with fields: `score` (float in [0.0, 1.0]), `partial_scores` (dict[str, float]), and `rationale` (str).
4. IF an Action is submitted with an invalid `operation` value, THEN THE Environment SHALL raise a `ValidationError` before modifying any state.
5. IF an Action sets `priority` to a value outside {1, 2, 3}, THEN THE Environment SHALL raise a `ValidationError`.
6. THE Environment SHALL define an `Email` Pydantic model with fields: `id` (str), `subject` (str), `sender` (str), `body` (str), `timestamp` (datetime), `thread_id` (str), `labels` (list[str]), and `attachments` (list[str]).

---

### Requirement 2: OpenEnv Interface

**User Story:** As an Agent developer, I want a standard reset/step/state API, so that I can swap environments without changing my agent loop.

#### Acceptance Criteria

1. THE Environment SHALL expose a `reset(task_id: str) -> Observation` method that initializes a new Episode for the given Task and returns the first Observation.
2. WHEN `step(action: Action)` is called, THE Environment SHALL apply the Action to the current Email, advance to the next Email, and return a tuple of `(Observation, Reward, done: bool, info: dict)`.
3. WHEN the last Email in the Inbox has been processed, THE Environment SHALL set `done = True` in the next step response.
4. THE Environment SHALL expose a `state() -> dict` method that returns a JSON-serializable snapshot of the full current Episode state, including all past actions and rewards.
5. WHILE an Episode is active, THE Environment SHALL increment `step_number` by 1 on each call to `step()`.
6. IF `step()` is called after `done = True`, THEN THE Environment SHALL raise a `RuntimeError` with the message "Episode has ended. Call reset() to start a new episode."
7. THE Environment SHALL expose a `render() -> str` method that returns a human-readable summary of the current Observation.

---

### Requirement 3: openenv.yaml Manifest

**User Story:** As a platform operator, I want a machine-readable manifest, so that the openenv validate tool can confirm compliance without running the environment.

#### Acceptance Criteria

1. THE Environment SHALL include an `openenv.yaml` file at the repository root with fields: `name`, `version`, `description`, `observation_space`, `action_space`, `reward_range`, and `tasks`.
2. THE `tasks` field in `openenv.yaml` SHALL list all three Task identifiers with their `difficulty` (easy | medium | hard) and a one-sentence `description`.
3. THE `reward_range` field SHALL specify `[0.0, 1.0]`.
4. THE `observation_space` and `action_space` fields SHALL each reference the corresponding Pydantic model by its fully-qualified Python class name.

---

### Requirement 4: Task 1 — Single-Label Categorization (Easy)

**User Story:** As an Agent, I want to correctly categorize each email into exactly one label, so that the inbox is organized by topic.

#### Acceptance Criteria

1. THE Environment SHALL provide Task `task_id = "categorize_easy"` containing an Inbox of 10 emails drawn from 4 categories: spam, billing, support, and general.
2. WHEN the Agent applies the `categorize` operation with a correct `label`, THE Environment SHALL assign a per-email reward of 1.0.
3. WHEN the Agent applies the `categorize` operation with an incorrect `label`, THE Environment SHALL assign a per-email reward of 0.0.
4. THE Grader for `categorize_easy` SHALL compute the final score as the fraction of emails correctly labeled (correct_count / 10).
5. THE Environment SHALL include ground-truth labels for all 10 emails, stored in a deterministic fixture file so that scores are reproducible across runs.
6. WHEN the Agent applies the `skip` operation, THE Environment SHALL assign a per-email reward of 0.0 and count the email as incorrectly handled.

---

### Requirement 5: Task 2 — Priority Triage with Reply (Medium)

**User Story:** As an Agent, I want to assign the correct priority and draft an appropriate reply for each email, so that urgent issues are handled first and senders receive timely responses.

#### Acceptance Criteria

1. THE Environment SHALL provide Task `task_id = "triage_medium"` containing an Inbox of 15 emails with ground-truth priority levels and reply-required flags.
2. WHEN the Agent applies the `prioritize` operation with the correct `priority`, THE Environment SHALL assign a priority sub-score of 1.0 for that email.
3. WHEN the Agent applies the `prioritize` operation with a `priority` that differs by 1 from the ground truth, THE Environment SHALL assign a priority sub-score of 0.5.
4. WHEN the Agent applies the `prioritize` operation with a `priority` that differs by 2 from the ground truth, THE Environment SHALL assign a priority sub-score of 0.0.
5. WHEN an email has `reply_required = True` and the Agent applies the `reply` operation with a non-empty `reply_text`, THE Environment SHALL assign a reply sub-score of 1.0 for that email.
6. WHEN an email has `reply_required = True` and the Agent does not apply the `reply` operation before the Episode ends, THE Environment SHALL assign a reply sub-score of 0.0 for that email.
7. THE Grader for `triage_medium` SHALL compute the final score as the mean of all per-email scores, where each per-email score is the mean of its priority sub-score and reply sub-score.
8. WHEN an email has `reply_required = False` and the Agent applies the `reply` operation, THE Environment SHALL assign a reply sub-score of 0.5 (unnecessary but not harmful).

---

### Requirement 6: Task 3 — Full Inbox Management (Hard)

**User Story:** As an Agent, I want to correctly categorize, prioritize, reply to, escalate, archive, and delete emails across a mixed inbox, so that the inbox reaches a clean, well-organized state.

#### Acceptance Criteria

1. THE Environment SHALL provide Task `task_id = "manage_hard"` containing an Inbox of 25 emails requiring a mix of all six operations: categorize, prioritize, reply, escalate, archive, and delete.
2. THE Grader for `manage_hard` SHALL compute the final score as the weighted mean of five sub-scores: categorization accuracy (weight 0.25), priority accuracy (weight 0.25), reply quality (weight 0.20), escalation accuracy (weight 0.15), and archive/delete accuracy (weight 0.15).
3. WHEN the Agent applies the `escalate` operation to an email whose ground truth is `escalate = True`, THE Environment SHALL assign an escalation sub-score of 1.0.
4. WHEN the Agent applies the `delete` operation to an email whose ground truth is `should_delete = True`, THE Environment SHALL assign a delete sub-score of 1.0.
5. WHEN the Agent applies the `delete` operation to an email whose ground truth is `should_delete = False`, THE Environment SHALL assign a delete sub-score of -0.5, penalizing destructive incorrect actions.
6. WHEN the Agent applies the `archive` operation to an email whose ground truth is `should_archive = True`, THE Environment SHALL assign an archive sub-score of 1.0.
7. THE Environment SHALL penalize the Agent 0.1 per step when the same email is processed more than once within a single Episode (loop detection).
8. THE Grader for `manage_hard` SHALL clamp the final score to [0.0, 1.0] after applying all penalties.

---

### Requirement 7: Reward Function — Partial Progress Signals

**User Story:** As an Agent developer, I want rewards after every step (not just at episode end), so that my agent receives a learning signal throughout the trajectory.

#### Acceptance Criteria

1. THE Environment SHALL return a non-zero `Reward` on every call to `step()` where the Agent's action partially or fully satisfies the ground truth for that email.
2. THE Environment SHALL include a `partial_scores` dict in every `Reward` that breaks down the score by sub-dimension (e.g. `{"categorization": 1.0, "priority": 0.5}`).
3. WHEN the Agent completes an Episode, THE Environment SHALL return a final summary `Reward` with `score` equal to the Grader's episode-level score.
4. THE Environment SHALL penalize the Agent with a `score` reduction of 0.05 per step when the `skip` operation is used more than 3 consecutive times.
5. THE `Reward.rationale` field SHALL contain a human-readable string explaining the score for that step, referencing the specific email id and the ground-truth expectation.

---

### Requirement 8: Baseline Inference Script

**User Story:** As a researcher, I want a runnable baseline script, so that I can reproduce reference scores and compare my agent's performance.

#### Acceptance Criteria

1. THE Baseline SHALL read the OpenAI API key from the environment variable `OPENAI_API_KEY` and raise a `EnvironmentError` if the variable is not set.
2. THE Baseline SHALL run the model `gpt-4o-mini` against all three Tasks in sequence and print the per-task score and mean score to stdout.
3. THE Baseline SHALL use the OpenAI Python client's chat completions API with the Observation serialized as a JSON string in the user message.
4. THE Baseline SHALL produce identical scores on repeated runs given the same model and fixture data (temperature=0, seed=42).
5. THE Baseline SHALL write a `baseline_results.json` file containing: `model`, `task_scores` (dict[task_id, float]), `mean_score` (float), and `timestamp` (ISO 8601).
6. IF the OpenAI API returns an error for a given step, THEN THE Baseline SHALL log the error, assign a score of 0.0 for that step, and continue to the next email.

---

### Requirement 9: Dockerfile and Hugging Face Space Deployment

**User Story:** As a platform operator, I want a working Dockerfile and Hugging Face Space configuration, so that the environment can be deployed and validated without local setup.

#### Acceptance Criteria

1. THE Repository SHALL include a `Dockerfile` that builds a runnable image using a Python 3.11 base, installs all dependencies from `requirements.txt`, and exposes port 7860.
2. THE Dockerfile SHALL set the default `CMD` to launch a FastAPI application serving the Environment's HTTP endpoints.
3. THE Repository SHALL include a `README.md` tagged with `openenv` that contains: environment description and motivation, action and observation space definitions, task descriptions with expected difficulty, setup and usage instructions, and baseline scores.
4. THE FastAPI application SHALL expose HTTP endpoints: `POST /reset`, `POST /step`, `GET /state`, and `GET /render` that proxy to the corresponding Environment methods.
5. THE `openenv.yaml` SHALL include a `space_url` field pointing to the Hugging Face Space URL.
6. THE Repository SHALL include a `requirements.txt` listing all Python dependencies with pinned versions.

---

### Requirement 10: Fixture Data and Reproducibility

**User Story:** As a researcher, I want deterministic fixture data for all tasks, so that benchmark scores are comparable across different agents and runs.

#### Acceptance Criteria

1. THE Environment SHALL load all Email fixtures from static JSON files under `fixtures/` at import time, not generated at runtime.
2. THE fixture files SHALL be versioned with a `fixture_version` field and the Environment SHALL log a warning if the loaded version does not match the expected version.
3. FOR ALL valid Episode trajectories on a given Task, running the same sequence of Actions SHALL produce the same sequence of Rewards (deterministic grading).
4. THE Environment SHALL expose a `get_fixture_version() -> str` method that returns the current fixture version string.
5. THE fixture JSON files SHALL include a `checksum` field (SHA-256 of the file contents excluding the checksum field itself), and THE Environment SHALL verify the checksum on load and raise a `ValueError` if it does not match.
