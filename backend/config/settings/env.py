"""Environment loading for ILMDAS.

Required names are read from the process environment. The example env file
lists those names with empty values so a developer machine never receives a
real credential from the repository.
"""

from __future__ import annotations

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BACKEND_DIR = Path(__file__).resolve().parents[2]


def load_env_file(path: Path | None = None) -> None:
    """Load KEY=VALUE lines from backend/.env without overriding real env vars."""

    if os.environ.get("ILMDAS_SKIP_ENV_FILE") == "1":
        return
    env_path = path or BACKEND_DIR / ".env"
    if not env_path.is_file():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        if name and name not in os.environ:
            os.environ[name] = value.strip().strip('"').strip("'")


def require_env(*names: str) -> dict[str, str]:
    """Return the named variables or refuse to start."""

    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        raise ImproperlyConfigured("Missing required environment variables: " + ", ".join(missing))
    return {name: os.environ[name] for name in names}
