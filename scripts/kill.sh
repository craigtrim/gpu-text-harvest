#!/bin/bash
# Kill the running harvest process

if tmux has-session -t harvest 2>/dev/null; then
    tmux kill-session -t harvest
    echo "Killed harvest session"
else
    echo "No harvest session running"
fi
