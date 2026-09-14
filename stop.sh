#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$PROJECT_ROOT/.start.pid"

for arg in "$@"; do
  if [[ "$arg" == "-h" || "$arg" == "--help" ]]; then
    echo "Usage: ./stop.sh"
    echo "  Stop the most recently started background server."
    exit 0
  fi
done

if [[ -s "$PID_FILE" ]]; then
  PID="$(cat "$PID_FILE")"
  kill "$PID" 2>/dev/null || true
  if wait "$PID" 2>/dev/null; then
    echo "Stopped background server with PID $PID."
  else
    echo "Background server with PID $PID is no longer running."
  fi
  mv "$PID_FILE" "$PID_FILE.bak" 2>/dev/null || true
else
  echo "No background server is currently recorded."
fi
