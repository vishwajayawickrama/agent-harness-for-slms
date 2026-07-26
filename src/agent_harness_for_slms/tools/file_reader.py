"""Controlled file reading tool with safety constraints."""

import errno
import mimetypes
import os
import stat
from pathlib import Path

from pydantic import BaseModel, Field

from agent_harness_for_slms.errors import FilePolicyError

MAX_FILE_SIZE = 1_024 * 1_024
MAX_OUTPUT_CHARS = 50_000
TRUNCATION_MARKER = "\n[truncated]"
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

TEXT_LIKE_APP_TYPES = frozenset({
    "application/json",
    "application/javascript",
    "application/xml",
    "application/x-yaml",
    "application/toml",
    "application/x-toml",
})


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

        try:
            fd = os.open(resolved, os.O_RDONLY | os.O_NOFOLLOW)
        except FileNotFoundError:
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
        except OSError as exc:
            if exc.errno == errno.ELOOP:
                raise FilePolicyError(f"Symlink denied: {command.path}")
            raise FilePolicyError(f"Cannot open file: {command.path}")

        try:
            stat_result = os.fstat(fd)
            size = stat_result.st_size

            if not stat.S_ISREG(stat_result.st_mode):
                raise FilePolicyError(f"Path is not a file: {command.path}")

            if size > self.max_file_size:
                raise FilePolicyError(
                    f"File exceeds maximum size ({size} > {self.max_file_size} bytes): {command.path}"
                )

            header = os.read(fd, 512)
            os.lseek(fd, 0, os.SEEK_SET)

            if self._is_binary(resolved, header):
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

            raw_bytes = b""
            while True:
                chunk = os.read(fd, 65536)
                if not chunk:
                    break
                raw_bytes += chunk
        finally:
            os.close(fd)

        content = self._decode(raw_bytes, command.encoding)
        effective_max = min(self.max_output_chars, command.max_chars)
        truncated = len(content) > effective_max
        if truncated:
            keep = max(0, effective_max - len(TRUNCATION_MARKER))
            content = content[:keep] + TRUNCATION_MARKER if keep > 0 else TRUNCATION_MARKER

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

    def _is_binary(self, path: Path, content_sample: bytes | None = None) -> bool:
        suffix = path.suffix.lower()
        if suffix in BINARY_EXTENSIONS:
            return True

        mime_type, _ = mimetypes.guess_type(path)
        if mime_type is not None:
            if mime_type in TEXT_LIKE_APP_TYPES:
                return False
            if not mime_type.startswith("text/"):
                return True
            return False

        if content_sample and b"\x00" in content_sample:
            return True
        return False

    def _decode(self, raw_bytes: bytes, encoding: str) -> str:
        try:
            return raw_bytes.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            return raw_bytes.decode("utf-8", errors="replace")
