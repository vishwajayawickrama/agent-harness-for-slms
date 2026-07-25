import json
from pathlib import Path

from agent_harness_for_slms.logging.jsonl import JsonlEventLogger


def test_log_file_is_created(tmp_path: Path) -> None:
    path = tmp_path / "logs" / "events.jsonl"
    JsonlEventLogger(path).write("test", {"value": 1})

    assert path.exists()


def test_each_line_is_valid_json(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    logger = JsonlEventLogger(path)
    logger.write("one", {})
    logger.write("two", {})

    lines = path.read_text(encoding="utf-8").splitlines()

    assert len(lines) == 2
    assert all(json.loads(line) for line in lines)


def test_event_type_and_data_are_preserved(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    JsonlEventLogger(path).write("test_event", {"answer": 42})

    event = json.loads(path.read_text(encoding="utf-8"))

    assert event["event_type"] == "test_event"
    assert event["data"] == {"answer": 42}


def test_parent_directory_is_created(tmp_path: Path) -> None:
    path = tmp_path / "missing" / "events.jsonl"
    JsonlEventLogger(path)

    assert path.parent.exists()
