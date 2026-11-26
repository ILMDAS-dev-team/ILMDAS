#!/usr/bin/env bash
# Run the same checks as .github/workflows/ci-cd.yml locally, before pushing.
# Usage (Git Bash, from the repo root):
#   scripts/ci-local.sh            all four CI jobs
#   scripts/ci-local.sh backend    backend lint + tests only
#   scripts/ci-local.sh frontend   frontend lint + tests only
# Stops at the first failing step, like CI. The smoke jobs are skipped because CI disables them.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-all}"

if [ -x "$ROOT/backend/.venv/Scripts/python.exe" ]; then
  PY="$ROOT/backend/.venv/Scripts/python.exe"   # Windows venv
elif [ -x "$ROOT/backend/.venv/bin/python" ]; then
  PY="$ROOT/backend/.venv/bin/python"           # Linux/macOS venv
else
  echo "No backend/.venv found. Create it and install backend/requirements/development.txt first." >&2
  exit 1
fi

step() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
pass() { printf '\033[1;32m%s passed\033[0m\n' "$*"; }

backend() {
  cd "$ROOT/backend"

  step "Backend lint: ruff check"
  "$PY" -m ruff check .
  step "Backend lint: ruff format --check"
  "$PY" -m ruff format --check .
  step "Backend lint: mypy"
  DJANGO_SETTINGS_MODULE=config.settings.test "$PY" -m mypy apps config
  step "Backend lint: secret scan (same hook as pre-commit, all tracked files)"
  (cd "$ROOT" && git ls-files -z | xargs -0 "$PY" -m detect_secrets.pre_commit_hook --baseline .secrets.baseline)
  step "Backend lint: dependency audit"
  "$PY" -m pip_audit --version >/dev/null 2>&1 || "$PY" -m pip install --quiet pip-audit
  "$PY" -m pip_audit -r requirements/base.txt
  pass "Backend lint"

  step "Backend tests: pytest with coverage >= 80%"
  DJANGO_SETTINGS_MODULE=config.settings.test \
    "$PY" -m pytest apps/ --cov=apps --cov-report=term --cov-fail-under=80 -q -p no:cacheprovider
  pass "Backend tests"
}

frontend() {
  cd "$ROOT/frontend"

  step "Frontend lint: ESLint"
  npm run -s lint
  step "Frontend lint: TypeScript"
  npm run -s type-check
  step "Frontend lint: Prettier"
  npm run -s format:check
  step "Frontend lint: npm audit (high, production deps)"
  npm audit --audit-level=high --omit=dev
  pass "Frontend lint"

  step "Frontend tests: Jest with coverage"
  npm run -s test:coverage
  step "Frontend tests: production build"
  npm run -s build
  pass "Frontend tests"
}

case "$TARGET" in
  backend) backend ;;
  frontend) frontend ;;
  all) backend; frontend ;;
  *) echo "Unknown target '$TARGET'. Use: all | backend | frontend" >&2; exit 2 ;;
esac

printf '\n\033[1;32mAll selected CI checks passed. Safe to push.\033[0m\n'
