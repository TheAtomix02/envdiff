"""Command-line interface for envdiff."""

import sys
from pathlib import Path
from typing import List

from .diff import diff_env_files
from .reporter import print_report


def main(argv: List[str] | None = None) -> int:
    """Entry point for the envdiff CLI.

    Usage:
        envdiff .env .env.production
        envdiff .env.example .env .env.staging
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="envdiff",
        description="Compare .env files across environments.",
        epilog="Example: envdiff .env.example .env .env.production",
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="Two or more .env files to compare",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show only a summary, not the full diff",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    args = parser.parse_args(argv)

    if len(args.files) < 2:
        parser.error("Please provide at least 2 .env files to compare.")

    # Validate files exist before diffing
    missing = [f for f in args.files if not Path(f).exists()]
    if missing:
        for f in missing:
            print(f"Error: File not found: {f}", file=sys.stderr)
        return 1

    try:
        result = diff_env_files(*args.files)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print_report(result, use_color=not args.no_color, summary_only=args.summary)

    # Exit code 1 if differences found (useful for CI/pre-commit hooks)
    return 1 if result.has_differences else 0


if __name__ == "__main__":
    sys.exit(main())
