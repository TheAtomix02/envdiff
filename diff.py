"""Core diff logic for comparing .env files."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

from .parser import parse_env_file


@dataclass
class KeyDiff:
    """Represents a difference found between env files."""
    key: str
    status: str  # 'missing_in', 'extra_in', 'value_differs', 'empty_in'
    details: str


@dataclass
class EnvDiffResult:
    """Full diff result between two or more .env files."""
    files: List[str]
    missing_keys: Dict[str, List[str]] = field(default_factory=dict)
    # key -> {filename: value}
    value_diffs: Dict[str, Dict[str, Optional[str]]] = field(default_factory=dict)
    # keys present in all files (no differences)
    common_keys: Set[str] = field(default_factory=set)
    # keys that look like secrets but are non-empty in example-like files
    secret_warnings: List[str] = field(default_factory=list)

    @property
    def has_differences(self) -> bool:
        return bool(self.missing_keys or self.value_diffs)

    @property
    def total_issues(self) -> int:
        return len(self.missing_keys) + len(self.value_diffs)


def diff_env_files(*filepaths: str) -> EnvDiffResult:
    """Compare two or more .env files and return a diff result.

    Args:
        *filepaths: Paths to .env files to compare.

    Returns:
        EnvDiffResult containing all differences found.

    Raises:
        ValueError: If fewer than 2 files are provided.
        FileNotFoundError: If any file does not exist.
    """
    if len(filepaths) < 2:
        raise ValueError("At least 2 files are required for comparison.")

    parsed: Dict[str, Dict[str, Optional[str]]] = {}
    for fp in filepaths:
        parsed[fp] = parse_env_file(fp)

    all_keys: Set[str] = set()
    for env_data in parsed.values():
        all_keys.update(env_data.keys())

    result = EnvDiffResult(files=list(filepaths))

    for key in sorted(all_keys):
        files_with_key = [fp for fp in filepaths if key in parsed[fp]]
        files_without_key = [fp for fp in filepaths if key not in parsed[fp]]

        if files_without_key:
            result.missing_keys[key] = files_without_key
        else:
            # Key exists in all files — check if values differ
            values = {fp: parsed[fp][key] for fp in filepaths}
            unique_values = set(v for v in values.values() if v is not None)
            if len(unique_values) > 1:
                result.value_diffs[key] = values
            else:
                result.common_keys.add(key)

    # Warn about secrets in example-like files
    result.secret_warnings = _find_secret_leaks(filepaths, parsed)

    return result


_SECRET_PATTERNS = [
    "secret", "password", "passwd", "token", "api_key", "apikey",
    "private_key", "auth", "credential", "cert", "key",
]

_EXAMPLE_PATTERNS = ["example", "sample", "template", "default", "dist"]


def _is_example_file(filepath: str) -> bool:
    name = Path(filepath).name.lower()
    return any(p in name for p in _EXAMPLE_PATTERNS)


def _looks_like_secret(key: str) -> bool:
    key_lower = key.lower()
    return any(p in key_lower for p in _SECRET_PATTERNS)


def _find_secret_leaks(
    filepaths: tuple,
    parsed: Dict[str, Dict[str, Optional[str]]]
) -> List[str]:
    """Warn if a secret-looking key has a real (non-empty, non-placeholder) value in an example file."""
    warnings = []
    placeholders = {"", "your_value_here", "changeme", "todo", "xxx", "example", "placeholder"}

    for fp in filepaths:
        if not _is_example_file(fp):
            continue
        for key, value in parsed[fp].items():
            if not _looks_like_secret(key):
                continue
            if value and value.lower() not in placeholders and not value.startswith("<"):
                warnings.append(
                    f"Possible secret leak: '{key}' in '{Path(fp).name}' has a real-looking value."
                )
    return warnings
