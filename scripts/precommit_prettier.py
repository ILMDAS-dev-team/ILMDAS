"""Format the frontend with the Prettier version pinned in its lockfile."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def main() -> int:
    npx = "npx.cmd" if sys.platform == "win32" else "npx"
    return subprocess.call([npx, "prettier", "--write", "."], cwd=FRONTEND)


if __name__ == "__main__":
    raise SystemExit(main())
