from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Operation(str, Enum):
    categorize = "categorize"
    prioritize = "prioritize"
    reply      = "reply"
    escalate   = "escalate"
    archive    = "archive"
    delete     = "delete"
    skip       = "skip"


class Email(BaseModel):
    model_config = ConfigDict(strict=True)

    id:          str
    subject:     str
    sender:      str
    body:        str
    timestamp:   datetime
    thread_id:   str
    labels:      list[str]
    attachments: list[str]


class Action(BaseModel):
    operation:  Operation
    label:      Optional[str] = None
    priority:   Optional[int] = Field(None, ge=1, le=3)
    reply_text: Optional[str] = None


class Observation(BaseModel):
    model_config = ConfigDict(strict=True)

    email:       Email
    inbox_size:  int
    step_number: int
    task_id:     str


class Reward(BaseModel):
    model_config = ConfigDict(strict=True)

    score:          float = Field(ge=0.0, le=1.0)
    partial_scores: dict[str, float]
    rationale:      str
