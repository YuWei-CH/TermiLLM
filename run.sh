#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/vllm-chat-venv"

if [[ ! -d "$VENV_DIR" ]]; then
    echo "Virtual environment not found at $VENV_DIR"
    echo "Run ./venv.sh first to create the environment and install dependencies."
    exit 1
fi

source "$VENV_DIR/bin/activate"
exec python3 "$SCRIPT_DIR/TermiLLM.py" "$@"
