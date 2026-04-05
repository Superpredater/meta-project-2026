import uvicorn
from openenv_email_triage.api import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
