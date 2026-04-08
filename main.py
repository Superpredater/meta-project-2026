
"""Run the OpenEnv Email Triage FastAPI server.


This script starts the FastAPI application defined in
openenv_email_triage.api:app on port 7860.
"""
from __future__ import annotations

import uvicorn


def main() -> None:
    """Start the uvicorn server."""

    uvicorn.run(
        "openenv_email_triage.api:app",
        host="0.0.0.0",
        port=7860,
        reload=False,
    )


if __name__ == "__main__":
    main()
