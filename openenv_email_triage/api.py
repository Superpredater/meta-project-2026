"""FastAPI HTTP layer for EmailTriageEnv."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel

from openenv_email_triage.env import EmailTriageEnv
from openenv_email_triage.models import Action

app = FastAPI(title="OpenEnv Email Triage")

# Custom exception handler to ensure JSON responses for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

# Serve static frontend
_STATIC_DIR = Path(__file__).parent.parent / "static"
if _STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

@app.get("/", include_in_schema=False)
def index():
    """Serve frontend HTML if available, otherwise return JSON status."""
    index_file = _STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"status": "ok", "message": "OpenEnv Email Triage API"}

# Single global environment instance
env = EmailTriageEnv()


class ResetRequest(BaseModel):
    task_id: str


@app.post("/reset")
def reset(body: Optional[ResetRequest] = None):
    """Reset environment to start a new episode.
    
    Accepts either:
    - JSON body with task_id field
    - No body (uses default task)
    - Simple JSON like {"status": "ok"} for health checks
    
    Returns:
    - Observation JSON if task_id provided
    - Status JSON if no task_id provided
    """
    # Handle simple health check or validation without task_id
    if body is None:
        return {"status": "ok", "message": "Reset endpoint ready. Provide task_id to reset environment."}
    
    try:
        obs = env.reset(body.task_id)
        return obs.model_dump(mode="json")
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


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


@app.get("/observation")
def get_observation():
    """Get the current observation without taking a step.
    
    This endpoint provides the current observation state, which is useful
    for validators and debuggers that need to inspect the environment
    without modifying it.
    """
    try:
        state_data = env.state()
        # Return current observation if available
        if state_data.get("done"):
            return {"observation": None, "done": True, "message": "Episode has ended"}
        
        # If we have a current observation, return it
        # Otherwise return state info
        return {
            "task_id": state_data.get("task_id"),
            "step": state_data.get("step"),
            "done": state_data.get("done"),
            "inbox_size": state_data.get("inbox_size"),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/metadata")
def metadata():
    """Return environment metadata."""
    return {
        "name": "openenv-email-triage",
        "description": "Inbox management RL environment with three tasks of increasing difficulty.",
        "version": "1.0.0",
        "observation_space": "openenv_email_triage.models.Observation",
        "action_space": "openenv_email_triage.models.Action",
        "reward_range": [0.0, 1.0],
    }


@app.get("/schema")
def schema():
    """Return JSON schemas for action, observation, and state."""
    from openenv_email_triage.models import Action, Observation
    
    return {
        "action": Action.model_json_schema(),
        "observation": Observation.model_json_schema(),
        "state": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "step": {"type": "integer"},
                "done": {"type": "boolean"},
                "inbox_size": {"type": "integer"},
                "history": {"type": "array"}
            }
        }
    }


@app.post("/mcp")
def mcp(request: dict):
    """MCP (Model Context Protocol) JSON-RPC endpoint."""
    return {
        "jsonrpc": "2.0",
        "id": request.get("id", 1),
        "result": {
            "status": "ok",
            "message": "MCP endpoint available"
        }
    }


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "openenv-email-triage"}
