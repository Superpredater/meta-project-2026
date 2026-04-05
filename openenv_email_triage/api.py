"""FastAPI HTTP layer for EmailTriageEnv."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from openenv_email_triage.env import EmailTriageEnv
from openenv_email_triage.models import Action

app = FastAPI(title="OpenEnv Email Triage")

# Serve static frontend
_STATIC_DIR = Path(__file__).parent.parent / "static"
if _STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

@app.get("/", include_in_schema=False)
def index():
    return FileResponse(str(_STATIC_DIR / "index.html"))

# Single global environment instance
env = EmailTriageEnv()


class ResetRequest(BaseModel):
    task_id: str


@app.post("/reset")
def reset(body: ResetRequest):
    try:
        obs = env.reset(body.task_id)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return obs.model_dump(mode="json")


@app.post("/step")
def step(action: Action):
    try:
        obs, reward, done, info = env.step(action)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "observation": obs.model_dump(mode="json") if obs is not None else None,
        "reward": reward.model_dump(mode="json"),
        "done": done,
        "info": info,
    }


@app.get("/state")
def state():
    return env.state()


@app.get("/render")
def render():
    return {"text": env.render()}
