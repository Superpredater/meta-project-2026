"""OpenEnv-compliant FastAPI server entry point.

This module provides the required entry point for OpenEnv validation.
It imports the FastAPI app and provides a main() function to run it.
"""
from __future__ import annotations

import uvicorn

from openenv_email_triage.api import app

__all__ = ["app", "main"]


def main() -> None:
    """Start the uvicorn server for the FastAPI app."""
    uvicorn.run(
        "server.app:app",
        host="0.0.0.0",
        port=7860,
        reload=False,
    )


if __name__ == "__main__":
    main()
