#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"

usage() {
  echo "Usage: ./install.sh"
  echo "  Prepare a local virtual environment and install the current package plus test tools."
  echo "  Forces stock-platform to be reinstalled so the current tree is always used."
  echo ""
  echo "Options:"
  echo "  -h, --help    Show this help."
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

cd "$PROJECT_ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required." >&2
  exit 1
fi

if [[ ! -e "$VENV_DIR/bin/python3" ]]; then
  rm -rf "$VENV_DIR"
  python3 -m venv "$VENV_DIR"
fi

PIPYTHON="$VENV_DIR/bin/python3"

if command -v uv >/dev/null 2>&1; then
  "$PIPYTHON" -m pip uninstall -y stock-platform >/dev/null 2>&1 || true
  uv sync --project "$PROJECT_ROOT" --extra test --reinstall-package stock-platform
else
  "$PIPYTHON" -m pip uninstall -y stock-platform >/dev/null 2>&1 || true
  "$PIPYTHON" -m pip install --upgrade pip >/dev/null
  "$PIPYTHON" -m pip install -e ".[test]"
fi

echo "Installed and activated project in $VENV_DIR."
echo "Run: source .venv/bin/activate"
