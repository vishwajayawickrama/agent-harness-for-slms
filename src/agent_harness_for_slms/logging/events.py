"""Structured harness event models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class HarnessEvent(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    event_type: str
    data: dict[str, Any]
