from pathlib import Path

import pytest

from agent_harness_for_slms.errors import FilePolicyError
from agent_harness_for_slms.tools.file_reader import (
    FileReadCommand,
    FileReaderTool,
    FileReadResult,
)


def test_reads_existing_text_file(tmp_path: Path) -> None:
    file = tmp_path / "hello.txt"
    file.write_text("hello world", encoding="utf-8")

    result = FileReaderTool().read(
        FileReadCommand(path=Path("hello.txt"), repo_root=tmp_path)
    )

    assert result.exists is True
    assert result.content == "hello world"
    assert result.binary is False
    assert result.size_bytes == 11


def test_missing_file_returns_not_found(tmp_path: Path) -> None:
    result = FileReaderTool().read(
        FileReadCommand(path=Path("missing.txt"), repo_root=tmp_path)
    )

    assert result.exists is False
    assert result.content == ""


def test_path_traversal_is_denied(tmp_path: Path) -> None:
    with pytest.raises(FilePolicyError, match="Path traversal denied"):
        FileReaderTool().read(
            FileReadCommand(path=Path("../etc/passwd"), repo_root=tmp_path)
        )


def test_path_traversal_via_symlink_is_denied(tmp_path: Path) -> None:
    target = tmp_path.parent / "outside.txt"
    target.write_text("secret", encoding="utf-8")
    link = tmp_path / "link.txt"
    link.symlink_to(target)

    with pytest.raises(FilePolicyError, match="Path traversal denied"):
        FileReaderTool().read(
            FileReadCommand(path=Path("link.txt"), repo_root=tmp_path)
        )


def test_binary_file_is_detected(tmp_path: Path) -> None:
    file = tmp_path / "image.png"
    file.write_bytes(b"\x89PNG\r\n\x1a\n")

    result = FileReaderTool().read(
        FileReadCommand(path=Path("image.png"), repo_root=tmp_path)
    )

    assert result.binary is True
    assert "binary file" in result.content


def test_output_truncation_works(tmp_path: Path) -> None:
    file = tmp_path / "long.txt"
    file.write_text("a" * 1000, encoding="utf-8")

    result = FileReaderTool(max_output_chars=100).read(
        FileReadCommand(path=Path("long.txt"), repo_root=tmp_path, max_chars=100)
    )

    assert result.truncated is True
    assert "[truncated]" in result.content


def test_oversized_file_is_denied(tmp_path: Path) -> None:
    file = tmp_path / "big.txt"
    file.write_text("x" * 100, encoding="utf-8")

    with pytest.raises(FilePolicyError, match="exceeds maximum size"):
        FileReaderTool(max_file_size=50).read(
            FileReadCommand(path=Path("big.txt"), repo_root=tmp_path)
        )


def test_directory_is_denied(tmp_path: Path) -> None:
    subdir = tmp_path / "subdir"
    subdir.mkdir()

    with pytest.raises(FilePolicyError, match="not a file"):
        FileReaderTool().read(
            FileReadCommand(path=Path("subdir"), repo_root=tmp_path)
        )


def test_encoding_fallback_works(tmp_path: Path) -> None:
    file = tmp_path / "bytes.txt"
    file.write_bytes(b"hello \xff world")

    result = FileReaderTool().read(
        FileReadCommand(path=Path("bytes.txt"), repo_root=tmp_path, encoding="ascii")
    )

    assert result.exists is True
    assert "\ufffd" in result.content or "<?>" in result.content or "[truncated]" in result.content


def test_command_models_have_correct_fields() -> None:
    cmd = FileReadCommand(path=Path("f.py"), repo_root=Path("/repo"))
    assert cmd.path == Path("f.py")
    assert cmd.repo_root == Path("/repo")
    assert cmd.encoding == "utf-8"

    result = FileReadResult(
        path=Path("f.py"),
        repo_root=Path("/repo"),
        exists=False,
        content="",
        encoding="utf-8",
        truncated=False,
        binary=False,
        size_bytes=0,
    )
    assert result.exists is False
    assert result.content == ""
