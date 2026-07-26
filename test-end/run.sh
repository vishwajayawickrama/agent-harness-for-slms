#!/usr/bin/env bash
#
# FileReaderTool — Comprehensive End-to-End Test Runner
#
# Runs the isolated test suite and generates three report artifacts:
#   report.log   — raw stdout/stderr capture
#   report.txt   — plain-text summary
#   report.md    — Markdown summary
#
# Usage:
#   cd /path/to/repo && bash test-end/run.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

REPORT_LOG="$SCRIPT_DIR/report.log"
REPORT_TXT="$SCRIPT_DIR/report.txt"
REPORT_MD="$SCRIPT_DIR/report.md"

cd "$REPO_DIR"

echo "========================================================"
echo "  Agent Harness for SLMs"
echo "  FileReaderTool — Comprehensive End-to-End Test Suite"
echo "========================================================"
echo ""
echo "Repository : $REPO_DIR"
echo "Output dir : $SCRIPT_DIR"
echo "Started    : $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo ""

# Ensure the package is importable
if [ ! -f "$REPO_DIR/pyproject.toml" ]; then
    echo "ERROR: pyproject.toml not found. Run this script from the repo root."
    exit 1
fi

echo "Running tests..."
echo ""

# Run the test suite, capturing ALL output to report.log
uv run python "$SCRIPT_DIR/test_file_reader_comprehensive.py" 2>&1 | tee "$REPORT_LOG"
EXIT_CODE="${PIPESTATUS[0]}"

echo ""
echo "========================================================"
echo "  Test run complete"
echo "  Exit code: $EXIT_CODE"
echo ""
echo "  Artifacts:"
echo "    $REPORT_LOG"
echo "    $REPORT_TXT"
echo "    $REPORT_MD"
echo "========================================================"

exit $EXIT_CODE
