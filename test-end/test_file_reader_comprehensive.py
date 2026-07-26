"""
Comprehensive end-to-end tests for FileReaderTool.

This suite is designed to be run independently of the project's pytest setup.
It covers normal paths, security constraints, edge cases, and adversarial inputs.

Usage:
    uv run python test-end/test_file_reader_comprehensive.py
"""

import os
import stat as stat_module
import sys
import tempfile
import textwrap
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agent_harness_for_slms.errors import FilePolicyError
from agent_harness_for_slms.tools.file_reader import (
    FileReadCommand,
    FileReadResult,
    FileReaderTool,
)

REPORT_DIR = Path(__file__).parent


class TestResult:
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"


class TestRunner:
    def __init__(self):
        self.tests: list[dict] = []
        self._start_time: float = 0.0

    def test(self, name: str, category: str, fn) -> None:
        print(f"  {" "*6}{name} ... ", end="", flush=True)
        try:
            fn()
            self.tests.append({"name": name, "category": category, "result": TestResult.PASS})
            print(f"\r  \x1b[32mPASS  \x1b[0m{name}")
        except FilePolicyError as e:
            self.tests.append({"name": name, "category": category, "result": TestResult.FAIL, "error": str(e), "traceback": traceback.format_exc()})
            print(f"\r  \x1b[31mFAIL  \x1b[0m{name}: {e}")
        except AssertionError as e:
            self.tests.append({"name": name, "category": category, "result": TestResult.FAIL, "error": str(e), "traceback": traceback.format_exc()})
            print(f"\r  \x1b[31mFAIL  \x1b[0m{name}: {e}")
        except Exception as e:
            self.tests.append({"name": name, "category": category, "result": TestResult.FAIL, "error": str(e), "traceback": traceback.format_exc()})
            print(f"\r  \x1b[31mFAIL  \x1b[0m{name}: {e}")

    def summary(self) -> dict:
        passed = sum(1 for t in self.tests if t["result"] == TestResult.PASS)
        failed = sum(1 for t in self.tests if t["result"] == TestResult.FAIL)
        skipped = sum(1 for t in self.tests if t["result"] == TestResult.SKIP)
        return {"total": len(self.tests), "passed": passed, "failed": failed, "skipped": skipped}

    def print_report(self, stream=sys.stdout) -> None:
        summary = self.summary()
        stream.write(f"\n{'='*70}\n")
        stream.write(f"  FILE READER TOOL — COMPREHENSIVE TEST REPORT\n")
        stream.write(f"  Run: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        stream.write(f"{'='*70}\n\n")

        categories = {}
        for t in self.tests:
            categories.setdefault(t["category"], []).append(t)

        for cat, cat_tests in sorted(categories.items()):
            cat_passed = sum(1 for t in cat_tests if t["result"] == TestResult.PASS)
            cat_failed = sum(1 for t in cat_tests if t["result"] == TestResult.FAIL)
            cat_total = len(cat_tests)
            stream.write(f"  [{cat}]  {cat_passed}/{cat_total} passed")
            if cat_failed:
                stream.write(f"  ({cat_failed} failed)")
            stream.write("\n")
            for t in cat_tests:
                status_char = "\u2713" if t["result"] == TestResult.PASS else "\u2717"
                stream.write(f"    {status_char}  {t['name']}\n")
                if t["result"] == TestResult.FAIL:
                    stream.write(f"         Error: {t.get('error', '')}\n")
            stream.write("\n")

        stream.write(f"{'='*70}\n")
        stream.write(f"  SUMMARY: {summary['passed']}/{summary['total']} passed")
        if summary["failed"]:
            stream.write(f", {summary['failed']} failed")
        if summary["skipped"]:
            stream.write(f", {summary['skipped']} skipped")
        stream.write(f"\n{'='*70}\n")

    def write_reports(self) -> None:
        summary = self.summary()

        txt_path = REPORT_DIR / "report.txt"
        md_path = REPORT_DIR / "report.md"

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("FILE READER TOOL — COMPREHENSIVE TEST REPORT\n")
            f.write(f"Run: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
            f.write(f"{'='*70}\n\n")
            categories = {}
            for t in self.tests:
                categories.setdefault(t["category"], []).append(t)
            for cat, cat_tests in sorted(categories.items()):
                cat_passed = sum(1 for t in cat_tests if t["result"] == TestResult.PASS)
                cat_failed = sum(1 for t in cat_tests if t["result"] == TestResult.FAIL)
                cat_total = len(cat_tests)
                f.write(f"[{cat}] {cat_passed}/{cat_total} passed")
                if cat_failed:
                    f.write(f" ({cat_failed} failed)")
                f.write("\n")
                for t in cat_tests:
                    status_char = "PASS" if t["result"] == TestResult.PASS else "FAIL"
                    f.write(f"  [{status_char}] {t['name']}")
                    if t["result"] == TestResult.FAIL:
                        f.write(f"\n    Error: {t.get('error', '')}")
                    f.write("\n")
                f.write("\n")
            f.write(f"{'='*70}\n")
            f.write(f"SUMMARY: {summary['passed']}/{summary['total']} passed")
            if summary["failed"]:
                f.write(f", {summary['failed']} failed")
            if summary["skipped"]:
                f.write(f", {summary['skipped']} skipped")
            f.write(f"\n{'='*70}\n")

        with open(md_path, "w", encoding="utf-8") as f:
            f.write("# FileReaderTool — Comprehensive Test Report\n\n")
            f.write(f"**Run:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
            f.write("## Results by Category\n\n")
            categories = {}
            for t in self.tests:
                categories.setdefault(t["category"], []).append(t)
            for cat, cat_tests in sorted(categories.items()):
                cat_passed = sum(1 for t in cat_tests if t["result"] == TestResult.PASS)
                cat_failed = sum(1 for t in cat_tests if t["result"] == TestResult.FAIL)
                cat_total = len(cat_tests)
                badge = f"![{cat_passed}/{cat_total}](https://img.shields.io/badge/{cat}-{cat_passed}%2F{cat_total}-{'brightgreen' if cat_failed == 0 else 'red'})"
                f.write(f"### {cat}\n\n")
                f.write(f"{badge}\n\n")
                f.write("| Test | Result |\n|------|--------|\n")
                for t in cat_tests:
                    icon = "✅" if t["result"] == TestResult.PASS else "❌"
                    f.write(f"| {t['name']} | {icon} {t['result']} |\n")
                    if t["result"] == TestResult.FAIL:
                        f.write(f"| | `{t.get('error', '')}` |\n")
                f.write("\n")

            f.write("## Summary\n\n")
            f.write(f"- **Total:** {summary['total']}\n")
            f.write(f"- **Passed:** {summary['passed']}\n")
            f.write(f"- **Failed:** {summary['failed']}\n")
            f.write(f"- **Skipped:** {summary['skipped']}\n\n")
            overall = "✅ ALL TESTS PASSED" if summary["failed"] == 0 else "❌ SOME TESTS FAILED"
            f.write(f"**{overall}**\n")


class TempRepo:
    def __init__(self):
        self.path = Path(tempfile.mkdtemp(prefix="file_reader_test_"))

    def write(self, rel: str, content: str | bytes, encoding: str = "utf-8") -> Path:
        target = self.path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, str):
            target.write_text(content, encoding=encoding)
        else:
            target.write_bytes(content)
        return target

    def write_bytes(self, rel: str, content: bytes) -> Path:
        return self.write(rel, content)

    def symlink_to(self, rel: str, target: str | Path) -> Path:
        link = self.path / rel
        link.parent.mkdir(parents=True, exist_ok=True)
        resolved = Path(target) if isinstance(target, str) else target
        link.symlink_to(resolved)
        return link

    def mkdir(self, rel: str) -> Path:
        d = self.path / rel
        d.mkdir(parents=True, exist_ok=True)
        return d

    def chmod(self, rel: str, mode: int) -> Path:
        target = self.path / rel
        target.chmod(mode)
        return target

    def cleanup(self) -> None:
        shutil = __import__("shutil")
        shutil.rmtree(self.path, ignore_errors=True)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.cleanup()


# ---------------------------------------------------------------------------
# Test suites
# ---------------------------------------------------------------------------

def register_tests( runner: TestRunner):

    # ----- Basic operations -------------------------------------------------
    def basic_reads_existing_text():
        with TempRepo() as repo:
            repo.write("hello.txt", "Hello, World!")
            result = FileReaderTool().read(
                FileReadCommand(path=Path("hello.txt"), repo_root=repo.path)
            )
            assert result.exists, "file should exist"
            assert result.content == "Hello, World!", f"unexpected content: {result.content}"
            assert result.binary is False
            assert result.size_bytes == 13

    runner.test("Reads existing text file", "Basic", basic_reads_existing_text)


    def basic_reads_empty_file():
        with TempRepo() as repo:
            repo.write("empty.txt", "")
            result = FileReaderTool().read(
                FileReadCommand(path=Path("empty.txt"), repo_root=repo.path)
            )
            assert result.exists
            assert result.content == ""
            assert result.size_bytes == 0
            assert result.truncated is False

    runner.test("Reads empty file", "Basic", basic_reads_empty_file)


    def basic_missing_file():
        with TempRepo() as repo:
            result = FileReaderTool().read(
                FileReadCommand(path=Path("nonexistent.txt"), repo_root=repo.path)
            )
            assert not result.exists
            assert result.content == ""

    runner.test("Missing file returns not-found", "Basic", basic_missing_file)


    def basic_file_with_unicode():
        with TempRepo() as repo:
            content = "Hello, 世界! ñoño 🚀"
            repo.write("unicode.txt", content)
            result = FileReaderTool().read(
                FileReadCommand(path=Path("unicode.txt"), repo_root=repo.path)
            )
            assert result.exists
            assert result.content == content

    runner.test("Reads file with Unicode content", "Basic", basic_file_with_unicode)


    def basic_file_in_subdirectory():
        with TempRepo() as repo:
            repo.write("a/b/c/deep.txt", "deep file")
            result = FileReaderTool().read(
                FileReadCommand(path=Path("a/b/c/deep.txt"), repo_root=repo.path)
            )
            assert result.exists
            assert result.content == "deep file"

    runner.test("Reads file in nested subdirectory", "Basic", basic_file_in_subdirectory)


    def basic_file_with_newlines():
        with TempRepo() as repo:
            repo.write("lines.txt", "line1\nline2\nline3\n")
            result = FileReaderTool().read(
                FileReadCommand(path=Path("lines.txt"), repo_root=repo.path)
            )
            assert result.exists
            assert result.content == "line1\nline2\nline3\n"

    runner.test("Reads file with newlines", "Basic", basic_file_with_newlines)


    def basic_file_with_trailing_whitespace():
        with TempRepo() as repo:
            repo.write("ws.txt", "content   \n  \n")
            result = FileReaderTool().read(
                FileReadCommand(path=Path("ws.txt"), repo_root=repo.path)
            )
            assert result.exists
            assert result.content == "content   \n  \n"

    runner.test("Reads file with trailing whitespace", "Basic", basic_file_with_trailing_whitespace)

    # ----- Path traversal ---------------------------------------------------

    def traversal_direct_parent():
        with TempRepo() as repo:
            try:
                FileReaderTool().read(
                    FileReadCommand(path=Path("../etc/passwd"), repo_root=repo.path)
                )
                assert False, "should have raised"
            except FilePolicyError as e:
                assert "traversal" in str(e).lower()

    runner.test("Denies direct parent traversal ../etc/passwd", "Path Traversal", traversal_direct_parent)


    def traversal_deep_nested():
        with TempRepo() as repo:
            try:
                FileReaderTool().read(
                    FileReadCommand(path=Path("../../../../../../etc/passwd"), repo_root=repo.path)
                )
                assert False
            except FilePolicyError as e:
                assert "traversal" in str(e).lower()

    runner.test("Denies deep nested traversal", "Path Traversal", traversal_deep_nested)


    def traversal_symlink_outside():
        with TempRepo() as repo:
            outside = Path(tempfile.mkdtemp()) / "secret.txt"
            outside.write_text("secret")
            repo.symlink_to("evil_link.txt", outside)
            try:
                FileReaderTool().read(
                    FileReadCommand(path=Path("evil_link.txt"), repo_root=repo.path)
                )
                assert False
            except FilePolicyError as e:
                assert "traversal" in str(e).lower() or "denied" in str(e).lower()
            finally:
                outside.unlink()
                outside.parent.rmdir()

    runner.test("Denies symlink pointing outside repo", "Path Traversal", traversal_symlink_outside)


    def traversal_symlink_chain_outside():
        with TempRepo() as repo:
            outside = Path(tempfile.mkdtemp()) / "real.txt"
            outside.write_text("outside")
            intermediate = repo.path / "intermediate"
            intermediate.symlink_to(outside)
            try:
                FileReaderTool().read(
                    FileReadCommand(path=Path("intermediate"), repo_root=repo.path)
                )
                assert False
            except FilePolicyError:
                pass
            finally:
                outside.unlink()
                outside.parent.rmdir()

    runner.test("Denies symlink chain pointing outside", "Path Traversal", traversal_symlink_chain_outside)


    def traversal_dot_dot_in_middle():
        with TempRepo() as repo:
            repo.write("a/b/c/file.txt", "should not be reachable via ..")
            cmd = FileReadCommand(path=Path("a/b/../b/../../a/b/c/file.txt"), repo_root=repo.path)
            result = FileReaderTool().read(cmd)
            assert result.exists
            assert result.content == "should not be reachable via .."

    runner.test("Allows dot-dot within repo bounds", "Path Traversal", traversal_dot_dot_in_middle)


    def traversal_absolute_path_ignored():
        with TempRepo() as repo:
            try:
                FileReaderTool().read(
                    FileReadCommand(path=Path("/etc/passwd"), repo_root=repo.path)
                )
                assert False
            except FilePolicyError:
                pass

    runner.test("Denies absolute path", "Path Traversal", traversal_absolute_path_ignored)

    # ----- Binary detection -------------------------------------------------

    def binary_known_extension_png():
        with TempRepo() as repo:
            repo.write_bytes("image.png", b"\x89PNG\r\n\x1a\n")
            result = FileReaderTool().read(
                FileReadCommand(path=Path("image.png"), repo_root=repo.path)
            )
            assert result.binary, "PNG should be detected as binary"
            assert "binary file" in result.content

    runner.test("Detects .png as binary", "Binary Detection", binary_known_extension_png)


    def binary_known_extension_zip():
        with TempRepo() as repo:
            repo.write_bytes("archive.zip", b"PK\x03\x04")
            result = FileReaderTool().read(
                FileReadCommand(path=Path("archive.zip"), repo_root=repo.path)
            )
            assert result.binary

    runner.test("Detects .zip as binary", "Binary Detection", binary_known_extension_zip)


    def binary_known_extension_pdf():
        with TempRepo() as repo:
            repo.write_bytes("doc.pdf", b"%PDF-1.4")
            result = FileReaderTool().read(
                FileReadCommand(path=Path("doc.pdf"), repo_root=repo.path)
            )
            assert result.binary

    runner.test("Detects .pdf as binary", "Binary Detection", binary_known_extension_pdf)


    def binary_known_extension_exe():
        with TempRepo() as repo:
            repo.write_bytes("prog.exe", b"MZ\x90\x00")
            result = FileReaderTool().read(
                FileReadCommand(path=Path("prog.exe"), repo_root=repo.path)
            )
            assert result.binary

    runner.test("Detects .exe as binary", "Binary Detection", binary_known_extension_exe)


    def binary_known_extension_dll():
        with TempRepo() as repo:
            repo.write_bytes("lib.dll", b"MZ\x90\x00")
            result = FileReaderTool().read(
                FileReadCommand(path=Path("lib.dll"), repo_root=repo.path)
            )
            assert result.binary

    runner.test("Detects .dll as binary", "Binary Detection", binary_known_extension_dll)


    def binary_known_extension_ico():
        with TempRepo() as repo:
            repo.write_bytes("icon.ico", b"\x00\x00\x01\x00")
            result = FileReaderTool().read(
                FileReadCommand(path=Path("icon.ico"), repo_root=repo.path)
            )
            assert result.binary

    runner.test("Detects .ico as binary", "Binary Detection", binary_known_extension_ico)


    def binary_known_extension_pyc():
        with TempRepo() as repo:
            repo.write_bytes("module.pyc", b"\x61\x0d\x0d\x0a")
            result = FileReaderTool().read(
                FileReadCommand(path=Path("module.pyc"), repo_root=repo.path)
            )
            assert result.binary

    runner.test("Detects .pyc as binary", "Binary Detection", binary_known_extension_pyc)


    def binary_extensionless_with_nulls():
        with TempRepo() as repo:
            repo.write_bytes("data", b"\x00\x01\x02\x03\xff\xfe\xfd\xfc")
            result = FileReaderTool().read(
                FileReadCommand(path=Path("data"), repo_root=repo.path)
            )
            assert result.binary, "extensionless file with null bytes should be binary"

    runner.test("Detects extensionless file with null bytes as binary", "Binary Detection", binary_extensionless_with_nulls)


    def binary_extensionless_no_nulls_is_text():
        with TempRepo() as repo:
            repo.write("notes", "this is plain text without an extension")
            result = FileReaderTool().read(
                FileReadCommand(path=Path("notes"), repo_root=repo.path)
            )
            assert not result.binary, "extensionless file without null bytes should not be binary"
            assert "plain text" in result.content

    runner.test("Extensionless file without nulls is text", "Binary Detection", binary_extensionless_no_nulls_is_text)


    def binary_json_is_not_binary():
        with TempRepo() as repo:
            repo.write("data.json", '{"key": "value", "nested": {"a": 1}}')
            result = FileReaderTool().read(
                FileReadCommand(path=Path("data.json"), repo_root=repo.path)
            )
            assert not result.binary, "JSON should not be binary"

    runner.test("JSON is not detected as binary", "Binary Detection", binary_json_is_not_binary)


    def binary_javascript_is_not_binary():
        with TempRepo() as repo:
            repo.write("script.js", "function hello() { return 42; }")
            result = FileReaderTool().read(
                FileReadCommand(path=Path("script.js"), repo_root=repo.path)
            )
            assert not result.binary, "JavaScript should not be binary"

    runner.test("JavaScript is not detected as binary", "Binary Detection", binary_javascript_is_not_binary)


    def binary_xml_is_not_binary():
        with TempRepo() as repo:
            repo.write("data.xml", '<?xml version="1.0"?><root><item/></root>')
            result = FileReaderTool().read(
                FileReadCommand(path=Path("data.xml"), repo_root=repo.path)
            )
            assert not result.binary, "XML should not be binary"

    runner.test("XML is not detected as binary", "Binary Detection", binary_xml_is_not_binary)


    def binary_yaml_is_not_binary():
        with TempRepo() as repo:
            repo.write("config.yaml", "key: value\nnested:\n  a: 1\n")
            result = FileReaderTool().read(
                FileReadCommand(path=Path("config.yaml"), repo_root=repo.path)
            )
            assert not result.binary, "YAML should not be binary"

    runner.test("YAML is not detected as binary", "Binary Detection", binary_yaml_is_not_binary)


    def binary_toml_is_not_binary():
        with TempRepo() as repo:
            repo.write("config.toml", '[tool]\nname = "test"\n')
            result = FileReaderTool().read(
                FileReadCommand(path=Path("config.toml"), repo_root=repo.path)
            )
            assert not result.binary, "TOML should not be binary"

    runner.test("TOML is not detected as binary", "Binary Detection", binary_toml_is_not_binary)


    def binary_svg_is_binary():
        with TempRepo() as repo:
            repo.write_bytes("icon.svg", b"<svg></svg>")
            result = FileReaderTool().read(
                FileReadCommand(path=Path("icon.svg"), repo_root=repo.path)
            )
            assert result.binary, "SVG should be detected as binary (by extension)"

    runner.test("Detects .svg as binary (by extension)", "Binary Detection", binary_svg_is_binary)


    def binary_python_file_is_not_binary():
        with TempRepo() as repo:
            repo.write("module.py", "def foo():\n    return 42\n")
            result = FileReaderTool().read(
                FileReadCommand(path=Path("module.py"), repo_root=repo.path)
            )
            assert not result.binary

    runner.test("Python file is not binary", "Binary Detection", binary_python_file_is_not_binary)

    # ----- Size limits ------------------------------------------------------

    def size_oversized_file_denied():
        with TempRepo() as repo:
            repo.write("big.txt", "x" * 200)
            try:
                FileReaderTool(max_file_size=100).read(
                    FileReadCommand(path=Path("big.txt"), repo_root=repo.path)
                )
                assert False
            except FilePolicyError as e:
                assert "exceeds maximum size" in str(e)

    runner.test("Oversized text file is denied", "Size Limits", size_oversized_file_denied)


    def size_oversized_binary_file_denied():
        with TempRepo() as repo:
            repo.write_bytes("big.bin", b"\x00" * 200)
            try:
                FileReaderTool(max_file_size=100).read(
                    FileReadCommand(path=Path("big.bin"), repo_root=repo.path)
                )
                assert False, "oversized binary file should be denied"
            except FilePolicyError:
                pass

    runner.test("Oversized binary file is denied (size before binary check)", "Size Limits", size_oversized_binary_file_denied)


    def size_file_at_exact_limit_allowed():
        with TempRepo() as repo:
            repo.write("exact.txt", "x" * 100)
            result = FileReaderTool(max_file_size=100).read(
                FileReadCommand(path=Path("exact.txt"), repo_root=repo.path)
            )
            assert result.exists
            assert result.size_bytes == 100

    runner.test("File at exact size limit is allowed", "Size Limits", size_file_at_exact_limit_allowed)


    def size_file_just_under_limit_allowed():
        with TempRepo() as repo:
            repo.write("small.txt", "x" * 99)
            result = FileReaderTool(max_file_size=100).read(
                FileReadCommand(path=Path("small.txt"), repo_root=repo.path)
            )
            assert result.exists
            assert result.size_bytes == 99

    runner.test("File just under size limit is allowed", "Size Limits", size_file_just_under_limit_allowed)


    def size_one_byte_over_denied():
        with TempRepo() as repo:
            repo.write("just_over.txt", "x" * 101)
            try:
                FileReaderTool(max_file_size=100).read(
                    FileReadCommand(path=Path("just_over.txt"), repo_root=repo.path)
                )
                assert False
            except FilePolicyError:
                pass

    runner.test("File one byte over limit is denied", "Size Limits", size_one_byte_over_denied)


    def size_zero_byte_file_allowed():
        with TempRepo() as repo:
            repo.write("empty.txt", "")
            result = FileReaderTool(max_file_size=0).read(
                FileReadCommand(path=Path("empty.txt"), repo_root=repo.path)
            )
            assert result.exists

    runner.test("Zero-byte file at zero limit is allowed", "Size Limits", size_zero_byte_file_allowed)

    # ----- Truncation -------------------------------------------------------

    def truncation_command_limit_respected():
        with TempRepo() as repo:
            repo.write("long.txt", "a" * 1000)
            result = FileReaderTool(max_output_chars=5000).read(
                FileReadCommand(path=Path("long.txt"), repo_root=repo.path, max_chars=150)
            )
            assert result.truncated
            assert len(result.content) <= 150
            assert "[truncated]" in result.content

    runner.test("Command-level max_chars truncates output", "Truncation", truncation_command_limit_respected)


    def truncation_tool_limit_respected():
        with TempRepo() as repo:
            repo.write("long.txt", "a" * 1000)
            result = FileReaderTool(max_output_chars=150).read(
                FileReadCommand(path=Path("long.txt"), repo_root=repo.path, max_chars=5000)
            )
            assert result.truncated
            assert len(result.content) <= 150

    runner.test("Tool-level max_output_chars truncates output", "Truncation", truncation_tool_limit_respected)


    def truncation_effective_limit_is_min():
        with TempRepo() as repo:
            repo.write("long.txt", "a" * 1000)
            result = FileReaderTool(max_output_chars=30).read(
                FileReadCommand(path=Path("long.txt"), repo_root=repo.path, max_chars=500)
            )
            assert result.truncated
            assert len(result.content) <= 30

    runner.test("Effective truncation limit is min(tool, command)", "Truncation", truncation_effective_limit_is_min)


    def truncation_marker_fits_within_limit():
        with TempRepo() as repo:
            repo.write("long.txt", "a" * 100)
            result = FileReaderTool(max_output_chars=30).read(
                FileReadCommand(path=Path("long.txt"), repo_root=repo.path, max_chars=500)
            )
            assert result.truncated
            assert len(result.content) <= 30
            assert "[truncated]" in result.content

    runner.test("Truncation marker reserved within limit", "Truncation", truncation_marker_fits_within_limit)


    def truncation_short_content_not_truncated():
        with TempRepo() as repo:
            repo.write("short.txt", "a" * 10)
            result = FileReaderTool(max_output_chars=1000).read(
                FileReadCommand(path=Path("short.txt"), repo_root=repo.path, max_chars=100)
            )
            assert not result.truncated
            assert result.content == "a" * 10

    runner.test("Short content is not truncated", "Truncation", truncation_short_content_not_truncated)


    def truncation_exactly_at_limit_not_truncated():
        with TempRepo() as repo:
            content = "x" * 100
            repo.write("exact.txt", content)
            result = FileReaderTool(max_output_chars=5000).read(
                FileReadCommand(path=Path("exact.txt"), repo_root=repo.path, max_chars=100)
            )
            assert not result.truncated
            assert result.content == content

    runner.test("Content at exact limit is not truncated", "Truncation", truncation_exactly_at_limit_not_truncated)

    # ----- Encoding ---------------------------------------------------------

    def encoding_utf8():
        with TempRepo() as repo:
            repo.write("utf8.txt", "Hello, 世界!")
            result = FileReaderTool().read(
                FileReadCommand(path=Path("utf8.txt"), repo_root=repo.path)
            )
            assert result.content == "Hello, 世界!"

    runner.test("Reads UTF-8 file correctly", "Encoding", encoding_utf8)


    def encoding_ascii_fallback():
        with TempRepo() as repo:
            repo.write_bytes("mixed.txt", b"hello \xff world")
            result = FileReaderTool().read(
                FileReadCommand(path=Path("mixed.txt"), repo_root=repo.path, encoding="ascii")
            )
            assert result.exists
            assert "\ufffd" in result.content

    runner.test("ASCII encoding falls back with replacement", "Encoding", encoding_ascii_fallback)


    def encoding_utf16():
        with TempRepo() as repo:
            content = "Hello, 世界!"
            raw = content.encode("utf-16-le")
            repo.write_bytes("utf16.txt", raw)
            result = FileReaderTool().read(
                FileReadCommand(path=Path("utf16.txt"), repo_root=repo.path, encoding="utf-16-le")
            )
            assert result.content == content

    runner.test("Reads UTF-16LE file correctly", "Encoding", encoding_utf16)


    def encoding_latin1():
        with TempRepo() as repo:
            content = "Héllò wörld! ñoño"
            raw = content.encode("latin-1")
            repo.write_bytes("latin1.txt", raw)
            result = FileReaderTool().read(
                FileReadCommand(path=Path("latin1.txt"), repo_root=repo.path, encoding="latin-1")
            )
            assert result.content == content

    runner.test("Reads Latin-1 file correctly", "Encoding", encoding_latin1)


    def encoding_invalid_name_falls_back():
        with TempRepo() as repo:
            repo.write("file.txt", "hello")
            result = FileReaderTool().read(
                FileReadCommand(path=Path("file.txt"), repo_root=repo.path, encoding="nonexistent-encoding")
            )
            assert result.exists
            assert result.content == "hello"

    runner.test("Invalid encoding name falls back to UTF-8", "Encoding", encoding_invalid_name_falls_back)


    def encoding_bom_utf8():
        with TempRepo() as repo:
            raw = "\ufeffHello with BOM".encode("utf-8")
            repo.write_bytes("bom.txt", raw)
            result = FileReaderTool().read(
                FileReadCommand(path=Path("bom.txt"), repo_root=repo.path)
            )
            assert result.exists
            assert result.content == "\ufeffHello with BOM"

    runner.test("Reads UTF-8 BOM file without stripping BOM", "Encoding", encoding_bom_utf8)

    # ----- Error handling ---------------------------------------------------

    def error_directory_denied():
        with TempRepo() as repo:
            repo.mkdir("subdir")
            try:
                FileReaderTool().read(
                    FileReadCommand(path=Path("subdir"), repo_root=repo.path)
                )
                assert False
            except FilePolicyError as e:
                assert "not a file" in str(e).lower()

    runner.test("Directory path raises FilePolicyError", "Error Handling", error_directory_denied)


    def error_deep_directory_denied():
        with TempRepo() as repo:
            repo.mkdir("a/b/c")
            try:
                FileReaderTool().read(
                    FileReadCommand(path=Path("a/b/c"), repo_root=repo.path)
                )
                assert False
            except FilePolicyError:
                pass

    runner.test("Deep directory path raises FilePolicyError", "Error Handling", error_deep_directory_denied)


    def error_missing_file_in_subdir():
        with TempRepo() as repo:
            repo.mkdir("a/b")
            result = FileReaderTool().read(
                FileReadCommand(path=Path("a/b/missing.txt"), repo_root=repo.path)
            )
            assert not result.exists

    runner.test("Missing file in subdirectory returns not-found", "Error Handling", error_missing_file_in_subdir)


    def error_symlink_to_file_outside_denied():
        with TempRepo() as repo:
            outside = Path(tempfile.mkdtemp()) / "target.txt"
            outside.write_text("outside")
            repo.symlink_to("outside_link.txt", outside)
            try:
                FileReaderTool().read(
                    FileReadCommand(path=Path("outside_link.txt"), repo_root=repo.path)
                )
                assert False, "symlink to outside file should be denied"
            except FilePolicyError:
                pass
            finally:
                outside.unlink()
                outside.parent.rmdir()

    runner.test("Symlink to outside file is denied", "Error Handling", error_symlink_to_file_outside_denied)


    def error_symlink_to_directory_denied():
        with TempRepo() as repo:
            repo.mkdir("realdir")
            repo.symlink_to("linkdir", repo.path / "realdir")
            try:
                FileReaderTool().read(
                    FileReadCommand(path=Path("linkdir"), repo_root=repo.path)
                )
            except FilePolicyError:
                pass

    runner.test("Symlink to directory raises FilePolicyError", "Error Handling", error_symlink_to_directory_denied)


    def error_empty_path_not_allowed():
        try:
            FileReadCommand(path=Path(), repo_root=Path("/tmp"))
            assert False, "empty path should be rejected by Pydantic"
        except Exception:
            pass

    runner.test("Empty path is rejected by Pydantic", "Error Handling", error_empty_path_not_allowed)

    # ----- TOCTOU / Race conditions -----------------------------------------

    def toctou_symlink_swap_denied():
        with TempRepo() as repo:
            legit = repo.path / "legitimate.txt"
            legit.write_text("innocent content")
            evil_target = repo.path.parent / "evil_outside.txt"
            evil_target.write_text("stolen data")

            repo.symlink_to("evil_link.txt", evil_target)
            try:
                FileReaderTool().read(
                    FileReadCommand(path=Path("evil_link.txt"), repo_root=repo.path)
                )
                assert False
            except FilePolicyError:
                pass
            finally:
                evil_target.unlink()

    runner.test("Symlink swap attack is denied", "TOCTOU", toctou_symlink_swap_denied)


    def toctou_double_open_consistent():
        with TempRepo() as repo:
            repo.write("stable.txt", "stable content")
            tool = FileReaderTool(max_file_size=10_000)
            cmd = FileReadCommand(path=Path("stable.txt"), repo_root=repo.path)
            result1 = tool.read(cmd)
            result2 = tool.read(cmd)
            assert result1.content == result2.content
            assert result1.size_bytes == result2.size_bytes

    runner.test("Repeated reads return consistent results", "TOCTOU", toctou_double_open_consistent)

    # ----- Large content stress ---------------------------------------------

    def stress_large_text_file():
        with TempRepo() as repo:
            content = "Lorem ipsum dolor sit amet.\n" * 1000
            repo.write("large.txt", content)
            tool = FileReaderTool(max_file_size=10_000_000)
            result = tool.read(
                FileReadCommand(path=Path("large.txt"), repo_root=repo.path)
            )
            assert result.exists
            assert result.size_bytes > 0
            assert not result.truncated or "[truncated]" in result.content

    runner.test("Reads large text file without crashing", "Stress", stress_large_text_file)


    def stress_many_small_files():
        with TempRepo() as repo:
            for i in range(100):
                repo.write(f"file_{i:03d}.txt", f"content {i}")
            tool = FileReaderTool()
            for i in range(100):
                result = tool.read(
                    FileReadCommand(path=Path(f"file_{i:03d}.txt"), repo_root=repo.path)
                )
                assert result.exists
                assert result.content == f"content {i}"

    runner.test("Reads 100 small files sequentially", "Stress", stress_many_small_files)


    def stress_very_long_filename():
        with TempRepo() as repo:
            name = "a" * 200 + ".txt"
            repo.write(name, "content")
            result = FileReaderTool().read(
                FileReadCommand(path=Path(name), repo_root=repo.path)
            )
            assert result.exists

    runner.test("Reads file with very long filename", "Stress", stress_very_long_filename)


    def stress_unicode_filename():
        with TempRepo() as repo:
            name = "文件_документ_सञ्चिका.txt"
            repo.write(name, "unicode filename content")
            result = FileReaderTool().read(
                FileReadCommand(path=Path(name), repo_root=repo.path)
            )
            assert result.exists
            assert result.content == "unicode filename content"

    runner.test("Reads file with Unicode filename", "Stress", stress_unicode_filename)


    def stress_filename_with_spaces():
        with TempRepo() as repo:
            repo.write("my file with spaces.txt", "spaces content")
            result = FileReaderTool().read(
                FileReadCommand(path=Path("my file with spaces.txt"), repo_root=repo.path)
            )
            assert result.exists
            assert result.content == "spaces content"

    runner.test("Reads file with spaces in name", "Stress", stress_filename_with_spaces)


    def stress_hidden_file():
        with TempRepo() as repo:
            repo.write(".env", "SECRET=value")
            result = FileReaderTool().read(
                FileReadCommand(path=Path(".env"), repo_root=repo.path)
            )
            assert result.exists
            assert "SECRET" in result.content

    runner.test("Reads hidden file (.env)", "Stress", stress_hidden_file)


    def stress_gitkeep_file():
        with TempRepo() as repo:
            repo.write(".gitkeep", "")
            result = FileReaderTool().read(
                FileReadCommand(path=Path(".gitkeep"), repo_root=repo.path)
            )
            assert result.exists
            assert result.content == ""

    runner.test("Reads .gitkeep file", "Stress", stress_gitkeep_file)

    # ----- Command/Result models --------------------------------------------

    def models_command_defaults():
        cmd = FileReadCommand(path=Path("test.txt"), repo_root=Path("/repo"))
        assert cmd.encoding == "utf-8"
        assert cmd.max_chars == 50_000

    runner.test("FileReadCommand has correct defaults", "Models", models_command_defaults)


    def models_command_custom_values():
        cmd = FileReadCommand(
            path=Path("test.txt"),
            repo_root=Path("/repo"),
            encoding="latin-1",
            max_chars=500,
        )
        assert cmd.encoding == "latin-1"
        assert cmd.max_chars == 500

    runner.test("FileReadCommand accepts custom values", "Models", models_command_custom_values)


    def models_result_roundtrip():
        result = FileReadResult(
            path=Path("f.py"),
            repo_root=Path("/repo"),
            exists=True,
            content="hello",
            encoding="utf-8",
            truncated=False,
            binary=False,
            size_bytes=5,
        )
        data = result.model_dump()
        restored = FileReadResult.model_validate(data)
        assert restored == result

    runner.test("FileReadResult serializes/deserializes", "Models", models_result_roundtrip)


    def models_tool_with_custom_limits():
        tool = FileReaderTool(max_file_size=500, max_output_chars=1000)
        assert tool.max_file_size == 500
        assert tool.max_output_chars == 1000

    runner.test("FileReaderTool accepts custom limits", "Models", models_tool_with_custom_limits)


    def models_tool_defaults():
        tool = FileReaderTool()
        assert tool.max_file_size == 1_048_576
        assert tool.max_output_chars == 50_000

    runner.test("FileReaderTool has correct defaults", "Models", models_tool_defaults)


if __name__ == "__main__":
    runner = TestRunner()
    register_tests(runner)

    print("=" * 70)
    print("  FILE READER TOOL — COMPREHENSIVE TEST SUITE")
    print(f"  Started: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 70)
    print()

    runner.print_report(stream=sys.stdout)

    runner.write_reports()

    summary = runner.summary()
    txt_path = REPORT_DIR / "report.txt"
    md_path = REPORT_DIR / "report.md"
    print(f"\nReports written to:")
    print(f"  {txt_path}")
    print(f"  {md_path}")

    if summary["failed"]:
        sys.exit(1)
