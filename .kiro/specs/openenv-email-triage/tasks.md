# Implementation Plan: OpenEnv Email Triage

## Overview

Implement the OpenEnv Email Triage RL benchmark environment in Python. Tasks follow the layered architecture: data models → fixture loading → graders → environment core → FastAPI layer → baseline script → deployment artifacts.

## Tasks

- [x] 1. Set up project structure and Pydantic data models
  - Create package layout: `openenv_email_triage/`, `tests/unit/`, `tests/property/`, `fixtures/`
  - Implement `openenv_email_triage/models.py` with `Operation`, `Email`, `Action`, `Observation`, `Reward` using Pydantic v2 `ConfigDict(strict=True)`
  - Enforce `priority` field constraint `ge=1, le=3` via `Field`
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

  - [ ]* 1.1 Write property test for invalid Action validation (P1)
    - **Property 1: Invalid Action raises ValidationError without state mutation**
    - **Validates: Requirements 1.4, 1.5**
    - Generate arbitrary strings not in `Operation` enum and ints outside {1, 2, 3}; assert `ValidationError` is raised

  - [ ]* 1.2 Write unit tests for data models
    - Test all model fields, optional fields default to `None`, and `Reward.score` bounds

- [x] 2. Implement fixture files and FixtureLoader
  - Create `fixtures/categorize_easy.json` (10 emails, 4 categories), `fixtures/triage_medium.json` (15 emails), `fixtures/manage_hard.json` (25 emails) with `fixture_version`, `checksum`, `task_id`, `emails`, and `ground_truth` arrays
  - Implement `openenv_email_triage/fixture_loader.py` with `FixtureLoader.load()` and `FixtureLoader.verify_checksum()`
  - SHA-256 checksum computed over file contents excluding the `checksum` field; raise `ValueError` on mismatch, `FileNotFoundError` if file missing, `logging.warning` on version mismatch
  - _Requirements: 10.1, 10.2, 10.4, 10.5_

  - [ ]* 2.1 Write unit tests for FixtureLoader
    - Test checksum validation pass/fail, version warning, correct deserialization of all three fixtures

- [x] 3. Implement GraderProtocol and CategorizeGrader
  - Define `GraderProtocol` in `openenv_email_triage/graders.py` with `score_step()` and `score_episode()` methods
  - Implement `CategorizeGrader`: per-email score 1.0 for correct label, 0.0 otherwise (including skip); episode score = `correct_count / 10`
  - _Requirements: 4.2, 4.3, 4.4, 4.6_

  - [ ]* 3.1 Write property test for categorization scoring correctness (P2)
    - **Property 2: Categorization scoring correctness**
    - **Validates: Requirements 4.2, 4.3, 4.6**

  - [ ]* 3.2 Write property test for categorize_easy score formula (P13)
    - **Property 13: Grader score formula — categorize_easy**
    - **Validates: Requirements 4.4**
    - Generate all 11 possible correct-count values (0..10); assert episode score equals `c / 10`

- [x] 4. Implement TriageGrader
  - Implement `TriageGrader` in `openenv_email_triage/graders.py`
  - Priority sub-score: 1.0 for exact match, 0.5 for distance 1, 0.0 for distance 2
  - Reply sub-score: 1.0 when `reply_required=True` and non-empty `reply_text` provided; 0.0 when `reply_required=True` and reply not submitted; 0.5 when `reply_required=False` and reply submitted
  - Episode score = arithmetic mean of all per-email scores (mean of priority + reply sub-scores)
  - _Requirements: 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8_

  - [ ]* 4.1 Write property test for priority scoring by distance (P3)
    - **Property 3: Priority scoring by distance**
    - **Validates: Requirements 5.2, 5.3, 5.4**
    - Generate `(ground_truth, submitted)` priority pairs with known distance; assert sub-score formula

  - [ ]* 4.2 Write property test for triage_medium score formula (P14)
    - **Property 14: Grader score formula — triage_medium**
    - **Validates: Requirements 5.7**
    - Generate random per-email sub-score combinations; verify episode score equals arithmetic mean

- [x] 5. Implement ManageGrader
  - Implement `ManageGrader` in `openenv_email_triage/graders.py`
  - Per-operation sub-scores: escalate 1.0 when `escalate=True`; delete 1.0 when `should_delete=True`, -0.5 when `should_delete=False`; archive 1.0 when `should_archive=True`
  - Episode score = weighted mean: `0.25*cat + 0.25*pri + 0.20*reply + 0.15*esc + 0.15*arch_del`, clamped to [0.0, 1.0]
  - Loop detection: subtract 0.1 per step when same email `id` processed more than once
  - _Requirements: 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8_

  - [ ]* 5.1 Write property test for correct operation scoring in manage_hard (P4)
    - **Property 4: Correct operation scoring in manage_hard**
    - **Validates: Requirements 6.3, 6.4, 6.5, 6.6**

  - [ ]* 5.2 Write property test for loop detection penalty (P11)
    - **Property 11: Loop detection penalty**
    - **Validates: Requirements 6.7**

  - [ ]* 5.3 Write property test for final score clamping (P12)
    - **Property 12: Final score clamping**
    - **Validates: Requirements 6.8**
    - Generate worst-case penalty-heavy episodes; assert episode score in [0.0, 1.0]

  - [ ]* 5.4 Write property test for manage_hard weighted mean formula (P15)
    - **Property 15: Grader score formula — manage_hard weighted mean**
    - **Validates: Requirements 6.2**
    - Generate random sub-score vectors; verify weighted sum formula

- [x] 6. Implement GraderRegistry
  - Implement `GraderRegistry` in `openenv_email_triage/graders.py` mapping `task_id` strings to grader instances
  - Raise `ValueError("Unknown task_id: <id>")` for unrecognized task IDs
  - _Requirements: (supports 4.1, 5.1, 6.1 via task routing)_

- [x] 7. Implement RewardCalculator and consecutive skip penalty
  - Implement `openenv_email_triage/reward_calculator.py`
  - Delegate per-step scoring to the appropriate grader; populate `partial_scores` dict and `rationale` string referencing the email `id`
  - Apply consecutive skip penalty: reduce score by 0.05 per step beyond the 3rd consecutive skip
  - _Requirements: 7.1, 7.2, 7.4, 7.5_

  - [ ]* 7.1 Write property test for reward structural invariant (P8)
    - **Property 8: Reward structural invariant**
    - **Validates: Requirements 7.2, 7.5**
    - Run random episodes; assert every `Reward` has non-empty `partial_scores` and `rationale` containing the email `id`

  - [ ]* 7.2 Write property test for consecutive skip penalty (P10)
    - **Property 10: Consecutive skip penalty**
    - **Validates: Requirements 7.4**
    - Generate sequences with 4+ consecutive skips; assert score reduction of 0.05 per step beyond 3rd

- [x] 8. Implement EmailTriageEnv core
  - Implement `openenv_email_triage/env.py` with `EmailTriageEnv`
  - `reset(task_id)`: load fixture via `FixtureLoader`, initialize `_inbox`, `_step=0`, `_done=False`, `_history=[]`, `_consecutive_skips=0`; return first `Observation`
  - `step(action)`: validate not done, score via `RewardCalculator`, advance step, set `done` when last email processed, append to `_history`; return `(Observation, Reward, done, info)`
  - `state()`: return JSON-serializable dict of full episode state including all past actions and rewards
  - `render()`: return human-readable summary string of current observation
  - `get_fixture_version()`: delegate to `FixtureLoader`
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 10.4_

  - [ ]* 8.1 Write property test for episode termination invariant (P5)
    - **Property 5: Episode termination invariant**
    - **Validates: Requirements 2.3, 2.6**
    - Run full episodes on all three tasks; assert `done=True` after N steps and `RuntimeError` on subsequent `step()`

  - [ ]* 8.2 Write property test for step counter monotonicity (P6)
    - **Property 6: Step counter monotonicity**
    - **Validates: Requirements 2.5**
    - Run random-length partial episodes; assert `step_number` equals call count (0-indexed from reset)

  - [ ]* 8.3 Write property test for state JSON-serializability (P7)
    - **Property 7: State JSON-serializability**
    - **Validates: Requirements 2.4**
    - Run random episodes; call `state()` at each step and assert `json.dumps()` succeeds

  - [ ]* 8.4 Write property test for episode-level score matches Grader (P9)
    - **Property 9: Episode-level score matches Grader output**
    - **Validates: Requirements 7.3**
    - Run full episodes; compare final `Reward.score` to direct `grader.score_episode()` call on same history

  - [ ]* 8.5 Write property test for deterministic grading (P16)
    - **Property 16: Deterministic grading**
    - **Validates: Requirements 10.3, 4.5**
    - Run same action sequence twice via `reset()`; assert identical `Reward` sequences

  - [ ]* 8.6 Write unit tests for env lifecycle
    - Test `reset()` returns `Observation` with `step_number=0` and correct `task_id`
    - Test `step()` after `done=True` raises `RuntimeError`
    - Test `render()` returns non-empty string

- [x] 9. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Create openenv.yaml manifest
  - Write `openenv.yaml` at repository root with all required fields: `name`, `version`, `description`, `observation_space`, `action_space`, `reward_range: [0.0, 1.0]`, `tasks` (all three with `id`, `difficulty`, `description`), and `space_url`
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 9.5_

  - [ ]* 10.1 Write unit tests for openenv.yaml structure
    - Parse and assert all required fields present, `reward_range` equals `[0.0, 1.0]`, all three task IDs listed

- [x] 11. Implement FastAPI HTTP layer
  - Create `openenv_email_triage/api.py` with a FastAPI app
  - Implement `POST /reset`, `POST /step`, `GET /state`, `GET /render` routes proxying to `EmailTriageEnv` methods
  - No business logic in routes — only serialization and routing
  - _Requirements: 9.4_

- [x] 12. Implement baseline inference script
  - Create `baseline.py` at repository root
  - Read `OPENAI_API_KEY` from environment; raise `EnvironmentError("OPENAI_API_KEY environment variable is not set")` if absent
  - Run `gpt-4o-mini` against all three tasks with `temperature=0, seed=42`; serialize `Observation` as JSON string in user message
  - On API error: log error, assign score 0.0 for that step, continue
  - Write `baseline_results.json` with `model`, `task_scores`, `mean_score`, `timestamp` (ISO 8601)
  - Print per-task score and mean score to stdout
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

  - [ ]* 12.1 Write property test for baseline error resilience (P17)
    - **Property 17: Baseline error resilience**
    - **Validates: Requirements 8.6**
    - Mock OpenAI client to raise errors on random steps; assert score 0.0 assigned and no unhandled exception

  - [ ]* 12.2 Write unit tests for baseline script
    - Test `EnvironmentError` raised when `OPENAI_API_KEY` absent
    - Test `baseline_results.json` written with all required fields

- [x] 13. Add Dockerfile, requirements.txt, and README.md
  - Write `requirements.txt` with pinned versions for all dependencies (pydantic, fastapi, uvicorn, hypothesis, openai, pyyaml, etc.)
  - Write `Dockerfile` using `python:3.11` base, install from `requirements.txt`, expose port 7860, set `CMD` to launch FastAPI via uvicorn
  - Write `README.md` tagged with `openenv` covering: environment description, action/observation space definitions, task descriptions, setup/usage instructions, and baseline scores placeholder
  - _Requirements: 9.1, 9.2, 9.3, 9.6_

- [x] 14. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 15. Scaffold React frontend
  - Bootstrap a Vite + React + TypeScript project under `frontend/`
  - Install and configure Tailwind CSS v3 for styling
  - Set up Vite proxy to forward `/reset`, `/step`, `/state`, `/render` to `http://localhost:7860` during development
  - Create `frontend/src/api.ts` with typed fetch wrappers for all four API endpoints
  - Define shared TypeScript types in `frontend/src/types.ts` mirroring the backend Pydantic models (`Email`, `Action`, `Observation`, `Reward`, `Operation`)

- [x] 16. Build core UI components
  - `TaskSelector` — sidebar cards for the three tasks with difficulty badges (Easy/Medium/Hard), progress bars, and best-score display; clicking a card calls `POST /reset`
  - `EmailViewer` — renders the current email (subject, sender, timestamp, body, attachments) in a clean card layout
  - `ActionPanel` — 7 operation buttons (Categorize, Prioritize, Reply, Escalate, Archive, Delete, Skip); shows contextual sub-fields (label dropdown, priority selector, reply textarea) based on selected operation; Submit button calls `POST /step`
  - `StepBar` — top progress bar showing current step / inbox size and live running score
  - `RewardToast` — animated feedback strip showing per-step score and rationale after each action

- [x] 17. Build episode state and results UI
  - `HistoryPanel` — sidebar list of past steps with operation icon, email ID, and color-coded score (green ≥ 0.7, yellow ≥ 0.3, red < 0.3)
  - `ScoreWidget` — sidebar score display showing current running score with color coding
  - `EpisodeCompleteModal` — full-screen overlay shown when `done=true`; displays final score, emoji rating, partial score breakdown chips, and a "Play Again" button that re-calls `POST /reset`
  - `WelcomeScreen` — shown before any task is started; explains the 4-step workflow with step cards

- [x] 18. Wire up global state and finalize
  - Implement `useEpisode` custom hook managing all episode state: `obs`, `done`, `stepHistory`, `runningScore`, `selectedOp`
  - Connect all components through the hook; ensure API online/offline status is shown in the header
  - Update `Dockerfile` to add a multi-stage build: Node stage builds the React app (`npm run build`), Python stage copies `frontend/dist` into `static/` and serves it via FastAPI's `StaticFiles`
  - Verify the full flow works end-to-end: select task → process emails → see episode complete modal

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests use Hypothesis with a minimum of 100 iterations per test
- Each property test must include a comment: `# Feature: openenv-email-triage, Property <N>: <property_text>`
- Checkpoints ensure incremental validation before moving to the next layer
