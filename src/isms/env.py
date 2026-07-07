"""Environment-file loader compatible with the ISMS Go CLI's `loadEnvFile`.

Reads simple `KEY=VALUE` lines from a file, stripping surrounding quotes and
ignoring blank lines and comments. Sets values into `os.environ` unless
`override=False` and the key is already set.
"""

from __future__ import annotations

import os
from pathlib import Path


def load_env_file(path: str | os.PathLike[str], *, override: bool = True) -> dict[str, str]:
    """Load KEY=VALUE lines from ``path`` into ``os.environ``.

    Returns the mapping of keys that were read from the file (whether or not
    they were set into the environment). If ``override`` is ``False``, existing
    environment values are not replaced.

    Blank lines and lines starting with ``#`` are ignored. Values wrapped in
    single or double quotes have their outer quotes stripped, mirroring the
    Go implementation.
    """
    p = Path(path)
    if not p.is_file():
        return {}

    read: dict[str, str] = {}
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip()
        if len(val) >= 2 and (
            (val[0] == '"' and val[-1] == '"') or (val[0] == "'" and val[-1] == "'")
        ):
            val = val[1:-1]
        read[key] = val
        if override or key not in os.environ:
            os.environ[key] = val
    return read
