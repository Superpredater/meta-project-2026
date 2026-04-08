"""OpenEnv validator-compatible FastAPI app."""
from __future__ import annotations

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from openenv_email_triage.env import EmailTriageEnv
from openenv_email_triage.models import Action

app = FastAPI(title="OpenEnv Email Triage Server")
env = EmailTriageEnv()


class ResetRequest(BaseModel):
    task_id: str = "categorize_easy"


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def internal_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.post("/reset")
def reset(body: ResetRequest | None = None) -> dict:
    task_id = body.task_id if body is not None else "categorize_easy"
    try:
        obs = env.reset(task_id)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return obs.model_dump(mode="json")


@app.post("/step")
def step(action: Action) -> dict:
    try:
        obs, reward, done, info = env.step(action)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    score = float(reward.score)
    if not 0.0 <= score <= 1.0:
        raise HTTPException(status_code=500, detail="Reward score out of range.")

    return {
        "observation": obs.model_dump(mode="json") if obs is not None else None,
        "reward": score,
        "done": done,
        "info": info,
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


def main() -> None:
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860, reload=False)


if __name__ == "__main__":
    main()
def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)