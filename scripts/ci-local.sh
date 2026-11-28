#!/usr/bin/env bash
# Run the same checks as .github/workflows/ci-cd.yml locally, before pushing.
# Usage (Git Bash, from the repo root):
#   scripts/ci-local.sh            all four CI jobs
#   scripts/ci-local.sh backend    backend lint + tests only
#   scripts/ci-local.sh frontend   frontend lint + tests only
# Where the backend (Python) checks run, set with CI_LOCAL_BACKEND:
#   docker   in the dev backend image from docker-compose.dev.yml
#            (the default when Docker is running; no host Python tools needed)
#   venv     in a host virtualenv: the active $VIRTUAL_ENV, else backend/.venv,
#            else .venv or venv at the repo root
#   e.g.  CI_LOCAL_BACKEND=venv scripts/ci-local.sh backend
# The frontend checks always run natively (npm), like local development.
# Stops at the first failing step, like CI. The smoke jobs are skipped because CI disables them.

set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-all}"

# Docker on Windows needs a Windows-style path (C:/...), which `pwd -W` gives in Git Bash.
HOST_ROOT="$(cd "$ROOT" && (pwd -W 2>/dev/null || pwd))"
COMPOSE_FILE="$HOST_ROOT/docker-compose.dev.yml"
# MSYS_NO_PATHCONV stops Git Bash rewriting container paths such as /repo or VAR=/home/...
dc() { MSYS_NO_PATHCONV=1 docker compose -f "$COMPOSE_FILE" "$@"; }

# In Docker, tool caches (mypy, ruff, coverage, pip-audit) live in the container's
# /home/django, not in the bind-mounted backend/. One-off containers keep them in the
# named volume ilmdas_ci_home. This avoids permission clashes with cache files that a
# container running as a different user (e.g. root) left in backend/.
CI_CACHE=/home/django/.cache/ilmdas-ci
DOCKER_ENV=(
  -e DJANGO_SETTINGS_MODULE=config.settings.test
  -e CI_CACHE="$CI_CACHE"
  -e MYPY_CACHE_DIR="$CI_CACHE/mypy"
  -e RUFF_CACHE_DIR="$CI_CACHE/ruff"
  -e COVERAGE_FILE="$CI_CACHE/coverage"
)
# .github is mounted at /.github (the parent of /app is the "repo root" for the tests),
# so the platform tests that read the CI workflow run instead of being skipped.
DOCKER_RUN=(run --rm --no-deps -T -v ilmdas_ci_home:/home/django -v "$HOST_ROOT/.github:/.github:ro")

# Progress: each job has 6 steps; shown as [done/total percent] with timings.
case "$TARGET" in
  backend | frontend) TOTAL_STEPS=6 ;;
  *) TOTAL_STEPS=12 ;;
esac
STEP_NO=0
RUN_START=$SECONDS
STEP_START=$SECONDS
CURRENT_STEP="setup"

STEP_OPEN=0
finish_step() {
  if [ "$STEP_OPEN" -eq 1 ]; then
    printf '\033[2m    done in %ss\033[0m\n' "$((SECONDS - STEP_START))"
    STEP_OPEN=0
  fi
}
step() {
  finish_step
  STEP_NO=$((STEP_NO + 1))
  STEP_START=$SECONDS
  STEP_OPEN=1
  CURRENT_STEP="$*"
  local pct=$(((STEP_NO - 1) * 100 / TOTAL_STEPS))
  printf '\n\033[1;34m==> [%d/%d, %d%% complete, %ss elapsed] %s\033[0m\n' \
    "$STEP_NO" "$TOTAL_STEPS" "$pct" "$((SECONDS - RUN_START))" "$*"
}
pass() { finish_step; printf '\033[1;32m%s passed\033[0m\n' "$*"; }
on_fail() {
  printf '\n\033[1;31mFAILED at step %d/%d: %s (after %ss)\033[0m\n' \
    "$STEP_NO" "$TOTAL_STEPS" "$CURRENT_STEP" "$((SECONDS - RUN_START))" >&2
  printf 'Fix it, then rerun: scripts/ci-local.sh %s\n' "$TARGET" >&2
}
trap on_fail ERR

# ---------------------------------------------------------------------------
# Backend runner: docker or venv
# ---------------------------------------------------------------------------
BACKEND_RUNNER=""
DOCKER_MODE=""   # exec (backend container already running) or run (one-off container)
PY=""
BACKEND_TOOLS="ruff mypy mypy_django_plugin pytest pytest_django pytest_cov detect_secrets"
# Prints the missing tool modules, space-separated; exits 1 if any are missing.
TOOLS_CHECK_PY="import importlib.util as u, sys; m=[t for t in '$BACKEND_TOOLS pip_audit'.split() if u.find_spec(t) is None]; print(' '.join(m)); sys.exit(1 if m else 0)"

find_venv_python() {
  local dir
  for dir in "${VIRTUAL_ENV:-}" "$ROOT/backend/.venv" "$ROOT/.venv" "$ROOT/venv"; do
    [ -n "$dir" ] || continue
    if command -v cygpath >/dev/null 2>&1; then
      dir="$(cygpath -u "$dir")"   # VIRTUAL_ENV set by PowerShell uses C:\... paths
    fi
    if [ -x "$dir/Scripts/python.exe" ]; then
      echo "$dir/Scripts/python.exe"   # Windows venv
      return 0
    elif [ -x "$dir/bin/python" ]; then
      echo "$dir/bin/python"           # Linux/macOS venv
      return 0
    fi
  done
  return 1
}

no_runner_help() {
  cat >&2 <<'EOF'
Start Docker Desktop and rerun (the backend checks then run in the dev image), or
create a venv and install the backend tools into it:
  cd backend && python -m venv .venv
  .venv/Scripts/python.exe -m pip install -r requirements/development.txt   # macOS/Linux: .venv/bin/python
EOF
}

setup_venv_runner() {
  if ! PY="$(find_venv_python)"; then
    echo "Backend runner: venv, but no virtualenv was found (checked \$VIRTUAL_ENV, backend/.venv, .venv, venv)." >&2
    no_runner_help
    exit 1
  fi
  local missing
  # pip-audit is not required here: the audit step installs it into the venv if missing.
  missing="$("$PY" -c "import importlib.util as u; print(' '.join(t for t in '$BACKEND_TOOLS'.split() if u.find_spec(t) is None))")"
  if [ -n "$missing" ]; then
    {
      echo "Backend runner: venv, using $PY"
      echo "These backend tools are not installed in that Python: $missing"
      echo "Install them into that same Python:"
      echo "  \"$PY\" -m pip install -r \"$ROOT/backend/requirements/development.txt\""
      echo "Or start Docker and rerun, so the checks run in the dev image (CI_LOCAL_BACKEND=docker)."
    } >&2
    exit 1
  fi
  printf '\033[1mBackend runner: venv (%s)\033[0m\n' "$PY"
}

setup_docker_runner() {
  CURRENT_STEP="prepare backend image (docker compose build backend)"
  printf '\033[1mBackend runner: docker (backend image from docker-compose.dev.yml)\033[0m\n'
  printf '\033[2m    building the backend image if requirements changed...\033[0m\n'
  dc build -q backend
  if dc ps --status running --services 2>/dev/null | grep -qx backend &&
    dc exec -T backend python -c "$TOOLS_CHECK_PY" >/dev/null 2>&1; then
    DOCKER_MODE=exec
    printf '\033[2m    backend container is running: using docker compose exec\033[0m\n'
  elif dc ps --status running --services 2>/dev/null | grep -qx backend; then
    # The running container predates the rebuilt image (e.g. requirements changed),
    # so it lacks some tools. Use fresh one-off containers from the new image instead.
    DOCKER_MODE=run
    printf '\033[33m    the running backend container is older than the image and lacks some tools:\033[0m\n'
    printf '\033[33m    using one-off containers from the new image. To update it, restart the stack:\033[0m\n'
    printf '\033[33m      docker compose -f docker-compose.dev.yml up -d --build   (or: make up)\033[0m\n'
  else
    DOCKER_MODE=run
    printf '\033[2m    backend container is not running: using one-off containers (docker compose run --rm --no-deps)\033[0m\n'
  fi
  CURRENT_STEP="setup"
}

setup_backend_runner() {
  local requested="${CI_LOCAL_BACKEND:-auto}"
  case "$requested" in
    docker)
      if ! docker info >/dev/null 2>&1; then
        echo "CI_LOCAL_BACKEND=docker, but Docker is not running. Start Docker Desktop, or use CI_LOCAL_BACKEND=venv." >&2
        exit 1
      fi
      BACKEND_RUNNER=docker
      ;;
    venv) BACKEND_RUNNER=venv ;;
    auto)
      if docker info >/dev/null 2>&1; then BACKEND_RUNNER=docker; else BACKEND_RUNNER=venv; fi
      ;;
    *)
      echo "Unknown CI_LOCAL_BACKEND '$requested'. Use: docker | venv" >&2
      exit 2
      ;;
  esac

  if [ "$BACKEND_RUNNER" = docker ]; then
    setup_docker_runner
  else
    if [ "$requested" = auto ]; then
      printf '\033[2mDocker is not running: falling back to a host virtualenv.\033[0m\n'
    fi
    setup_venv_runner
  fi
}

# Run backend Python (in backend/, with the test settings) using the selected runner.
bpy() {
  if [ "$BACKEND_RUNNER" = venv ]; then
    (cd "$ROOT/backend" && DJANGO_SETTINGS_MODULE=config.settings.test "$PY" "$@")
  elif [ "$DOCKER_MODE" = exec ]; then
    dc exec -T "${DOCKER_ENV[@]}" backend sh -c 'mkdir -p "$CI_CACHE" && exec python "$@"' sh "$@"
  else
    dc "${DOCKER_RUN[@]}" "${DOCKER_ENV[@]}" backend sh -c 'mkdir -p "$CI_CACHE" && exec python "$@"' sh "$@"
  fi
}

# Secret scan over all tracked files (same hook as pre-commit).
secret_scan() {
  if [ "$BACKEND_RUNNER" = venv ]; then
    (cd "$ROOT" && git ls-files -z | xargs -0 "$PY" -m detect_secrets.pre_commit_hook --baseline .secrets.baseline)
  else
    # The backend container mounts only backend/ and has no git, so list the files on
    # the host and scan them in a one-off container with the repo mounted at /repo.
    (cd "$ROOT" && git ls-files -z) |
      dc "${DOCKER_RUN[@]}" -v "$HOST_ROOT:/repo" -w /repo backend \
        sh -c 'xargs -0 python -m detect_secrets.pre_commit_hook --baseline .secrets.baseline'
  fi
}

backend() {
  setup_backend_runner

  step "Backend lint: ruff check"
  bpy -m ruff check .
  step "Backend lint: ruff format --check"
  bpy -m ruff format --check .
  step "Backend lint: mypy"
  bpy -m mypy apps config
  step "Backend lint: secret scan (same hook as pre-commit, all tracked files)"
  secret_scan
  step "Backend lint: dependency audit"
  if [ "$BACKEND_RUNNER" = venv ]; then
    "$PY" -m pip_audit --version >/dev/null 2>&1 || "$PY" -m pip install --quiet pip-audit
  fi
  bpy -m pip_audit -r requirements/base.txt
  pass "Backend lint"

  step "Backend tests: pytest with coverage >= 80%"
  bpy -m pytest apps/ --cov=apps --cov-report=term --cov-fail-under=80 -q -p no:cacheprovider
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

printf '\n\033[1;32m[%d/%d, 100%% complete] All selected CI checks passed in %ss. Safe to push.\033[0m\n' \
  "$STEP_NO" "$TOTAL_STEPS" "$((SECONDS - RUN_START))"
