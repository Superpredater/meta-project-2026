"""Unit tests for openenv.yaml manifest structure."""
import yaml
from pathlib import Path

MANIFEST_PATH = Path(__file__).parent.parent.parent / "openenv.yaml"
REQUIRED_FIELDS = {"name", "version", "description", "observation_space", "action_space", "reward_range", "space_url", "tasks"}
EXPECTED_TASK_IDS = {"categorize_easy", "triage_medium", "manage_hard"}


def load_manifest() -> dict:
    with open(MANIFEST_PATH) as f:
        return yaml.safe_load(f)


def test_manifest_all_required_fields_present():
    manifest = load_manifest()
    missing = REQUIRED_FIELDS - set(manifest.keys())
    assert not missing, f"Missing required fields: {missing}"


def test_manifest_reward_range():
    manifest = load_manifest()
    assert manifest["reward_range"] == [0.0, 1.0]


def test_manifest_all_task_ids_listed():
    manifest = load_manifest()
    task_ids = {task["id"] for task in manifest["tasks"]}
    assert task_ids == EXPECTED_TASK_IDS


def test_manifest_observation_space_references_correct_class():
    manifest = load_manifest()
    assert manifest["observation_space"] == "openenv_email_triage.models.Observation"


def test_manifest_action_space_references_correct_class():
    manifest = load_manifest()
    assert manifest["action_space"] == "openenv_email_triage.models.Action"
