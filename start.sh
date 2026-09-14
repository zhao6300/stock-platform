#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"
PYTHONPATH="$PROJECT_ROOT/src:${PYTHONPATH:-}"
BACKGROUND=false
LOG_FILE="$PROJECT_ROOT/.start.log"
PID_FILE="$PROJECT_ROOT/.start.pid"

for arg in "$@"; do
  if [[ "$arg" == "-d" || "$arg" == "--background" ]]; then
    BACKGROUND=true
    break
  fi
done

for arg in "$@"; do
  if [[ "$arg" == "-h" || "$arg" == "--help" ]]; then
echo "Usage: ./start.sh"
echo "  Serve the default FastAPI application on http://127.0.0.1:\$PORT."
echo "  Uses .venv/bin/uvicorn when available, otherwise falls back to your active Python environment."
echo "  PORT environment variable controls the port (default: 8000)."
echo "  -d, --background  Start without blocking and write logs/pid files."
    exit 0
  fi
done

# Bind to a local host only when invoked without explicit user overrides.
HOST="${STOCK_PLATFORM_HOST:-127.0.0.1}"
PORT="${STOCK_PLATFORM_PORT:-8000}"
HOST="${HOST}"; PORT="${PORT}"

if [[ "$BACKGROUND" == false ]]; then
  if [[ -x "$VENV_DIR/bin/uvicorn" ]]; then
    cd "$PROJECT_ROOT"
    exec "$VENV_DIR/bin/uvicorn" stock_platform.web.main:app \
      --host "$HOST" \
      --port "$PORT"
  elif command -v uvicorn >/dev/null 2>&1; then
    export PYTHONPATH
    cd "$PROJECT_ROOT"
    exec "$(command -v uvicorn)" stock_platform.web.main:app \
      --host "$HOST" \
      --port "$PORT"
  else
    "$PROJECT_ROOT/install.sh"
    cd "$PROJECT_ROOT"
    exec "$VENV_DIR/bin/uvicorn" stock_platform.web.main:app \
      --host "$HOST" \
      --port "$PORT"
  fi
fi

if [[ -x "$VENV_DIR/bin/uvicorn" ]]; then
  UVICORN="$VENV_DIR/bin/uvicorn"
elif command -v uvicorn >/dev/null 2>&1; then
  export PYTHONPATH
  UVICORN="$(command -v uvicorn)"
else
  "$PROJECT_ROOT/install.sh"
  cd "$PROJECT_ROOT"
  UVICORN="$VENV_DIR/bin/uvicorn"
fi

cd "$PROJECT_ROOT"
nohup "$UVICORN" stock_platform.web.main:app --host "$HOST" --port "$PORT" \
  >"$LOG_FILE" 2>&1 &
echo "$!" > "$PID_FILE"
echo "Background server started: http://$HOST:$PORT"
echo "Log file: $LOG_FILE"
echo "PID file: $PID_FILE"

if [[ -x "$VENV_DIR/bin/uvicorn" ]]; then
  cd "$PROJECT_ROOT"
  exec "$VENV_DIR/bin/uvicorn" stock_platform.web.main:app --host "$HOST" --port "$PORT"
elif command -v uvicorn >/dev/null 2>&1; then
  export PYTHONPATH
  cd "$PROJECT_ROOT"
  exec "$(command -v uvicorn)" stock_platform.web.main:app --host "$HOST" --port "$PORT"
else
  "$PROJECT_ROOT/install.sh"
  cd "$PROJECT_ROOT"
  exec "$VENV_DIR/bin/uvicorn" stock_platform.web.main:app --host "$HOST" --port "$PORT"
fi
