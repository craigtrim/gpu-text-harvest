#!/bin/bash
# Attach to the running harvest session
# Detach without stopping: Ctrl+b then d

if tmux has-session -t harvest 2>/dev/null; then
    echo "Attaching to harvest session..."
    echo "(Detach with Ctrl+b then d)"
    tmux attach -t harvest
else
    echo "No harvest session running"
    echo "Start one with: scripts/run.sh"
fi
