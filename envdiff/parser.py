"""Parse .env files into key-value dictionaries."""

import re
from pathlib import Path
from typing import Dict, Optional, Tuple


def parse_env_file(filepath: str | Path) -> Dict[str, Optional[str]]:
    """Parse a .env file and return a dict of key -> value.

    Handles:
    - KEY=value
    - KEY="quoted value"
    - KEY='single quoted'
    - # comments
    - blank lines
    - export KEY=value
    - Keys with no value (KEY=)
    """
    result: Dict[str, Optional[str]] = {}
    path = Path(filepath)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Skip blank lines and comments
            if not line or line.startswith("#"):
                continue

            # Strip optional 'export ' prefix
            if line.startswith("export "):
                line = line[7:]

            # Match KEY=VALUE (value may be quoted or empty)
            match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)=(.*)?$', line)
            if not match:
                continue

            key = match.group(1)
            raw_value = match.group(2) if match.group(2) is not None else ""

            value = _strip_quotes(raw_value)
            result[key] = value

    return result


def _strip_quotes(value: str) -> str:
    """Remove surrounding quotes from a value."""
    if len(value) >= 2:
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            return value[1:-1]
    return value
