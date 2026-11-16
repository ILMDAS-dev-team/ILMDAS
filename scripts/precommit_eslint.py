"""Run ESLint from frontend/ so the flat config and lockfile are used."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def main() -> int:
    npx = "npx.cmd" if sys.platform == "win32" else "npx"
    args: list[str] = []
    for name in sys.argv[1:]:
        parts = Path(name).parts
        if parts and parts[0] == "frontend":
            args.append(str(Path(*parts[1:])))
        else:
            args.append(name)
    if not args:
        return 0
    return subprocess.call([npx, "eslint", "--fix", *args], cwd=FRONTEND)


if __name__ == "__main__":
    raise SystemExit(main())
