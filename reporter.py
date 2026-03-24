"""Format and print diff results to the terminal."""

from pathlib import Path
from typing import Optional

from .diff import EnvDiffResult

# ANSI color codes
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def _c(text: str, *codes: str, use_color: bool = True) -> str:
    if not use_color:
        return text
    return "".join(codes) + text + RESET


def print_report(result: EnvDiffResult, use_color: bool = True, summary_only: bool = False) -> None:
    """Print a human-readable diff report to stdout."""
    short_names = [Path(f).name for f in result.files]

    # Header
    print(_c("envdiff", BOLD, use_color=use_color) + " — comparing " +
          " vs ".join(_c(n, CYAN, use_color=use_color) for n in short_names))
    print()

    if not result.has_differences and not result.secret_warnings:
        print(_c("✓ All files are in sync. No differences found.", GREEN, BOLD, use_color=use_color))
        _print_summary(result, use_color)
        return

    if not summary_only:
        # Missing keys section
        if result.missing_keys:
            print(_c("Missing keys", BOLD, use_color=use_color))
            print(_c("─" * 50, DIM, use_color=use_color))
            for key, missing_in_files in sorted(result.missing_keys.items()):
                missing_names = [Path(f).name for f in missing_in_files]
                present_names = [Path(f).name for f in result.files if f not in missing_in_files]
                print(
                    f"  {_c('✗', RED, use_color=use_color)} "
                    f"{_c(key, BOLD, use_color=use_color)}"
                )
                print(
                    f"    present in:  {_c(', '.join(present_names), GREEN, use_color=use_color)}"
                )
                print(
                    f"    missing in:  {_c(', '.join(missing_names), RED, use_color=use_color)}"
                )
            print()

        # Value differences section
        if result.value_diffs:
            print(_c("Value differences", BOLD, use_color=use_color))
            print(_c("─" * 50, DIM, use_color=use_color))
            for key, values_by_file in sorted(result.value_diffs.items()):
                print(f"  {_c('~', YELLOW, use_color=use_color)} {_c(key, BOLD, use_color=use_color)}")
                for filepath, value in values_by_file.items():
                    fname = Path(filepath).name
                    display = _mask_value(value)
                    print(
                        f"    {_c(fname, CYAN, use_color=use_color)}: "
                        f"{_c(display, DIM, use_color=use_color)}"
                    )
            print()

    # Secret warnings
    if result.secret_warnings:
        print(_c("⚠ Security warnings", YELLOW, BOLD, use_color=use_color))
        print(_c("─" * 50, DIM, use_color=use_color))
        for warning in result.secret_warnings:
            print(f"  {_c('!', YELLOW, use_color=use_color)} {warning}")
        print()

    _print_summary(result, use_color)


def _print_summary(result: EnvDiffResult, use_color: bool) -> None:
    total = len(result.common_keys) + len(result.missing_keys) + len(result.value_diffs)
    print(_c("Summary", BOLD, use_color=use_color))
    print(_c("─" * 50, DIM, use_color=use_color))
    print(f"  Total keys tracked : {total}")
    print(f"  {_c('✓', GREEN, use_color=use_color)} In sync          : {len(result.common_keys)}")
    if result.missing_keys:
        print(f"  {_c('✗', RED, use_color=use_color)} Missing keys      : {len(result.missing_keys)}")
    if result.value_diffs:
        print(f"  {_c('~', YELLOW, use_color=use_color)} Value differences : {len(result.value_diffs)}")
    if result.secret_warnings:
        print(f"  {_c('!', YELLOW, use_color=use_color)} Security warnings : {len(result.secret_warnings)}")


def _mask_value(value: Optional[str]) -> str:
    """Show a short masked preview of a value."""
    if value is None or value == "":
        return "(empty)"
    if len(value) <= 4:
        return "***"
    return value[:2] + "***" + value[-1]
