#!/bin/bash
# Start PDF extraction in a tmux session
# Usage: ./run.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$PROJECT_DIR/config.sh"

if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "Missing config.sh - copy from config.sh.example and set INPUT_DIR"
    exit 1
fi

source "$CONFIG_FILE"

if [[ -z "$INPUT_DIR" ]]; then
    echo "INPUT_DIR not set in config.sh"
    exit 1
fi

cd "$PROJECT_DIR"

if tmux has-session -t harvest 2>/dev/null; then
    echo "Session 'harvest' already running!"
    echo "Use scripts/attach.sh to view it, or scripts/kill.sh to stop it"
    exit 1
fi

tmux new-session -d -s harvest \
    "poetry run marker $INPUT_DIR \
    --output_dir ./output \
    --workers 20 \
    --output_format markdown \
    --skip_existing; \
    echo 'DONE - Press any key to close'; read"

echo "Started extraction in background tmux session 'harvest'"
echo ""
echo "Commands:"
echo "  scripts/attach.sh  - View live progress"
echo "  scripts/kill.sh    - Stop the process"
echo ""
echo "Check output count: ls output | wc -l"
