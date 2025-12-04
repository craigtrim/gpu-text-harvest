#!/bin/bash
# Start PDF extraction in a tmux session
# Usage: ./run.sh

cd /home/craigtrim/projects/gpu-text-harvest

if tmux has-session -t harvest 2>/dev/null; then
    echo "Session 'harvest' already running!"
    echo "Use scripts/attach.sh to view it, or scripts/kill.sh to stop it"
    exit 1
fi

tmux new-session -d -s harvest \
    "poetry run marker /home/craigtrim/data/maryville/transcripts/ \
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
