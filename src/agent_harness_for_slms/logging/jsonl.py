"""JSONL event logging."""

from pathlib import Path
from typing import Any

from agent_harness_for_slms.logging.events import HarnessEvent


class JsonlEventLogger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, event_type: str, data: dict[str, Any]) -> None:
        event = HarnessEvent(event_type=event_type, data=data)
        with self.path.open("a", encoding="utf-8") as log_file:
            log_file.write(event.model_dump_json() + "\n")
