"""Tests for envdiff."""

import pytest
from pathlib import Path
import tempfile
import os

from envdiff.parser import parse_env_file
from envdiff.diff import diff_env_files


# ── Parser tests ──────────────────────────────────────────────────────────────

def write_env(content: str) -> str:
    """Write content to a temp file and return its path."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False)
    f.write(content)
    f.close()
    return f.name


def test_parse_basic_key_value():
    path = write_env("KEY=value\n")
    result = parse_env_file(path)
    assert result == {"KEY": "value"}
    os.unlink(path)


def test_parse_double_quoted():
    path = write_env('KEY="hello world"\n')
    result = parse_env_file(path)
    assert result == {"KEY": "hello world"}
    os.unlink(path)


def test_parse_single_quoted():
    path = write_env("KEY='hello world'\n")
    result = parse_env_file(path)
    assert result == {"KEY": "hello world"}
    os.unlink(path)


def test_parse_skips_comments():
    path = write_env("# This is a comment\nKEY=value\n")
    result = parse_env_file(path)
    assert "KEY" in result
    assert len(result) == 1
    os.unlink(path)


def test_parse_skips_blank_lines():
    path = write_env("\n\nKEY=value\n\n")
    result = parse_env_file(path)
    assert result == {"KEY": "value"}
    os.unlink(path)


def test_parse_export_prefix():
    path = write_env("export KEY=value\n")
    result = parse_env_file(path)
    assert result == {"KEY": "value"}
    os.unlink(path)


def test_parse_empty_value():
    path = write_env("KEY=\n")
    result = parse_env_file(path)
    assert result == {"KEY": ""}
    os.unlink(path)


def test_parse_multiple_keys():
    path = write_env("A=1\nB=2\nC=3\n")
    result = parse_env_file(path)
    assert result == {"A": "1", "B": "2", "C": "3"}
    os.unlink(path)


def test_parse_file_not_found():
    with pytest.raises(FileNotFoundError):
        parse_env_file("/nonexistent/.env")


# ── Diff tests ────────────────────────────────────────────────────────────────

def test_diff_identical_files():
    a = write_env("KEY=value\nOTHER=thing\n")
    b = write_env("KEY=value\nOTHER=thing\n")
    result = diff_env_files(a, b)
    assert not result.has_differences
    assert result.common_keys == {"KEY", "OTHER"}
    os.unlink(a)
    os.unlink(b)


def test_diff_missing_key_in_second():
    a = write_env("KEY=value\nEXTRA=x\n")
    b = write_env("KEY=value\n")
    result = diff_env_files(a, b)
    assert "EXTRA" in result.missing_keys
    assert b in result.missing_keys["EXTRA"]


def test_diff_value_differs():
    a = write_env("DB_URL=postgres://localhost/dev\n")
    b = write_env("DB_URL=postgres://prod-host/prod\n")
    result = diff_env_files(a, b)
    assert "DB_URL" in result.value_diffs


def test_diff_three_files():
    a = write_env("A=1\nB=2\nC=3\n")
    b = write_env("A=1\nB=2\n")
    c = write_env("A=1\nB=99\nC=3\n")
    result = diff_env_files(a, b, c)
    assert "C" in result.missing_keys
    assert b in result.missing_keys["C"]
    assert "B" in result.value_diffs
    os.unlink(a)
    os.unlink(b)
    os.unlink(c)


def test_diff_requires_two_files():
    a = write_env("KEY=value\n")
    with pytest.raises(ValueError):
        diff_env_files(a)
    os.unlink(a)


def test_diff_secret_warning_in_example():
    # .env.example with a real-looking secret value should trigger a warning
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".env.example", delete=False, prefix="test_"
    )
    f.write("API_KEY=sk-realkey12345\n")
    f.close()

    b = write_env("API_KEY=sk-realkey12345\n")
    result = diff_env_files(f.name, b)
    assert len(result.secret_warnings) > 0
    os.unlink(f.name)
    os.unlink(b)


def test_diff_no_warning_for_placeholder():
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".env.example", delete=False, prefix="test_"
    )
    f.write("API_KEY=your_value_here\n")
    f.close()

    b = write_env("API_KEY=real-secret-value\n")
    result = diff_env_files(f.name, b)
    assert len(result.secret_warnings) == 0
    os.unlink(f.name)
    os.unlink(b)
