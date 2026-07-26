"""Controlled file reading tool with safety constraints."""

import mimetypes
from pathlib import Path

from pydantic import BaseModel, Field

from agent_harness_for_slms.errors import FilePolicyError

MAX_FILE_SIZE = 1_024 * 1_024
MAX_OUTPUT_CHARS = 50_000
BINARY_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".so",
    ".dll",
    ".dylib",
    ".bin",
    ".exe",
    ".o",
    ".a",
    ".lib",
    ".class",
    ".jar",
    ".war",
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".7z",
    ".rar",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".ico",
    ".svg",
    ".webp",
    ".ttf",
    ".otf",
    ".woff",
    ".woff2",
    ".eot",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".mp3",
    ".mp4",
    ".avi",
    ".mov",
    ".wav",
    ".flac",
    ".ogg",
    ".webm",
    ".lock",
    ".db",
    ".sqlite",
    ".DS_Store",
    ".gitkeep",
    ".gitignore",
}


class FileReadCommand(BaseModel):
    path: Path = Field(description="Path to the file to read, relative to the repository root.")
    repo_root: Path = Field(description="Repository root directory. Used to prevent path traversal.")
    encoding: str = Field(default="utf-8", description="Text encoding to use when reading the file.")
    max_chars: int = Field(
        default=MAX_OUTPUT_CHARS,
        ge=100,
        le=MAX_OUTPUT_CHARS,
        description="Maximum number of characters to return.",
    )


class FileReadResult(BaseModel):
    path: Path
    repo_root: Path
    exists: bool
    content: str
    encoding: str
    truncated: bool
    binary: bool
    size_bytes: int


class FileReaderTool:
    def __init__(self, max_file_size: int = MAX_FILE_SIZE, max_output_chars: int = MAX_OUTPUT_CHARS) -> None:
        self.max_file_size = max_file_size
        self.max_output_chars = max_output_chars

    def read(self, command: FileReadCommand) -> FileReadResult:
        resolved = self._resolve_path(command.path, command.repo_root)

        if not resolved.exists():
            return FileReadResult(
                path=command.path,
                repo_root=command.repo_root,
                exists=False,
                content="",
                encoding=command.encoding,
                truncated=False,
                binary=False,
                size_bytes=0,
            )

        if not resolved.is_file():
            raise FilePolicyError(f"Path is not a file: {command.path}")

        size = resolved.stat().st_size
        if self._is_binary(resolved):
            return FileReadResult(
                path=command.path,
                repo_root=command.repo_root,
                exists=True,
                content=f"[binary file: {size} bytes]",
                encoding=command.encoding,
                truncated=False,
                binary=True,
                size_bytes=size,
            )

        if size > self.max_file_size:
            raise FilePolicyError(
                f"File exceeds maximum size ({size} > {self.max_file_size} bytes): {command.path}"
            )

        raw_bytes = resolved.read_bytes()
        content = self._decode(raw_bytes, command.encoding)
        truncated = len(content) > command.max_chars
        if truncated:
            content = content[: command.max_chars] + "\n[truncated]"

        return FileReadResult(
            path=command.path,
            repo_root=command.repo_root,
            exists=True,
            content=content,
            encoding=command.encoding,
            truncated=truncated,
            binary=False,
            size_bytes=size,
        )

    def _resolve_path(self, path: Path, repo_root: Path) -> Path:
        repo_root = repo_root.expanduser().resolve()
        resolved = (repo_root / path).expanduser().resolve()
        try:
            resolved.relative_to(repo_root)
        except ValueError:
            raise FilePolicyError(
                f"Path traversal denied: {path} resolves outside the repository root."
            )
        return resolved

    def _is_binary(self, path: Path) -> bool:
        suffix = path.suffix.lower()
        if suffix in BINARY_EXTENSIONS:
            return True
        mime_type, _ = mimetypes.guess_type(path)
        return mime_type is not None and not mime_type.startswith("text/")

    def _decode(self, raw_bytes: bytes, encoding: str) -> str:
        try:
            return raw_bytes.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            return raw_bytes.decode("utf-8", errors="replace")
