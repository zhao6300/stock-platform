#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$PROJECT_ROOT"
bash -n install.sh
bash -n start.sh
"$PROJECT_ROOT/install.sh" --help >/dev/null
"$PROJECT_ROOT/start.sh" --help >/dev/null
