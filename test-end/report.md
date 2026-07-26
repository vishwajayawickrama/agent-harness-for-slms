# FileReaderTool — Comprehensive Test Report

**Run:** 2026-07-26 15:48:18 UTC

## Results by Category

### Basic

![7/7](https://img.shields.io/badge/Basic-7%2F7-brightgreen)

| Test | Result |
|------|--------|
| Reads existing text file | ✅ PASS |
| Reads empty file | ✅ PASS |
| Missing file returns not-found | ✅ PASS |
| Reads file with Unicode content | ✅ PASS |
| Reads file in nested subdirectory | ✅ PASS |
| Reads file with newlines | ✅ PASS |
| Reads file with trailing whitespace | ✅ PASS |

### Binary Detection

![16/16](https://img.shields.io/badge/Binary Detection-16%2F16-brightgreen)

| Test | Result |
|------|--------|
| Detects .png as binary | ✅ PASS |
| Detects .zip as binary | ✅ PASS |
| Detects .pdf as binary | ✅ PASS |
| Detects .exe as binary | ✅ PASS |
| Detects .dll as binary | ✅ PASS |
| Detects .ico as binary | ✅ PASS |
| Detects .pyc as binary | ✅ PASS |
| Detects extensionless file with null bytes as binary | ✅ PASS |
| Extensionless file without nulls is text | ✅ PASS |
| JSON is not detected as binary | ✅ PASS |
| JavaScript is not detected as binary | ✅ PASS |
| XML is not detected as binary | ✅ PASS |
| YAML is not detected as binary | ✅ PASS |
| TOML is not detected as binary | ✅ PASS |
| Detects .svg as binary (by extension) | ✅ PASS |
| Python file is not binary | ✅ PASS |

### Encoding

![6/6](https://img.shields.io/badge/Encoding-6%2F6-brightgreen)

| Test | Result |
|------|--------|
| Reads UTF-8 file correctly | ✅ PASS |
| ASCII encoding falls back with replacement | ✅ PASS |
| Reads UTF-16LE file correctly | ✅ PASS |
| Reads Latin-1 file correctly | ✅ PASS |
| Invalid encoding name falls back to UTF-8 | ✅ PASS |
| Reads UTF-8 BOM file without stripping BOM | ✅ PASS |

### Error Handling

![6/6](https://img.shields.io/badge/Error Handling-6%2F6-brightgreen)

| Test | Result |
|------|--------|
| Directory path raises FilePolicyError | ✅ PASS |
| Deep directory path raises FilePolicyError | ✅ PASS |
| Missing file in subdirectory returns not-found | ✅ PASS |
| Symlink to outside file is denied | ✅ PASS |
| Symlink to directory raises FilePolicyError | ✅ PASS |
| Empty path is rejected by Pydantic | ✅ PASS |

### Models

![5/5](https://img.shields.io/badge/Models-5%2F5-brightgreen)

| Test | Result |
|------|--------|
| FileReadCommand has correct defaults | ✅ PASS |
| FileReadCommand accepts custom values | ✅ PASS |
| FileReadResult serializes/deserializes | ✅ PASS |
| FileReaderTool accepts custom limits | ✅ PASS |
| FileReaderTool has correct defaults | ✅ PASS |

### Path Traversal

![6/6](https://img.shields.io/badge/Path Traversal-6%2F6-brightgreen)

| Test | Result |
|------|--------|
| Denies direct parent traversal ../etc/passwd | ✅ PASS |
| Denies deep nested traversal | ✅ PASS |
| Denies symlink pointing outside repo | ✅ PASS |
| Denies symlink chain pointing outside | ✅ PASS |
| Allows dot-dot within repo bounds | ✅ PASS |
| Denies absolute path | ✅ PASS |

### Size Limits

![6/6](https://img.shields.io/badge/Size Limits-6%2F6-brightgreen)

| Test | Result |
|------|--------|
| Oversized text file is denied | ✅ PASS |
| Oversized binary file is denied (size before binary check) | ✅ PASS |
| File at exact size limit is allowed | ✅ PASS |
| File just under size limit is allowed | ✅ PASS |
| File one byte over limit is denied | ✅ PASS |
| Zero-byte file at zero limit is allowed | ✅ PASS |

### Stress

![7/7](https://img.shields.io/badge/Stress-7%2F7-brightgreen)

| Test | Result |
|------|--------|
| Reads large text file without crashing | ✅ PASS |
| Reads 100 small files sequentially | ✅ PASS |
| Reads file with very long filename | ✅ PASS |
| Reads file with Unicode filename | ✅ PASS |
| Reads file with spaces in name | ✅ PASS |
| Reads hidden file (.env) | ✅ PASS |
| Reads .gitkeep file | ✅ PASS |

### TOCTOU

![2/2](https://img.shields.io/badge/TOCTOU-2%2F2-brightgreen)

| Test | Result |
|------|--------|
| Symlink swap attack is denied | ✅ PASS |
| Repeated reads return consistent results | ✅ PASS |

### Truncation

![6/6](https://img.shields.io/badge/Truncation-6%2F6-brightgreen)

| Test | Result |
|------|--------|
| Command-level max_chars truncates output | ✅ PASS |
| Tool-level max_output_chars truncates output | ✅ PASS |
| Effective truncation limit is min(tool, command) | ✅ PASS |
| Truncation marker reserved within limit | ✅ PASS |
| Short content is not truncated | ✅ PASS |
| Content at exact limit is not truncated | ✅ PASS |

## Summary

- **Total:** 67
- **Passed:** 67
- **Failed:** 0
- **Skipped:** 0

**✅ ALL TESTS PASSED**
