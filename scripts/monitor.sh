#!/bin/bash
# Live monitoring dashboard for clean.py (Ollama LLM cleanup)

INPUT_DIR="/home/craigtrim/projects/gpu-text-harvest/output-raw"
OUTPUT_DIR="/home/craigtrim/projects/gpu-text-harvest/output-clean"

tput civis
clear
trap 'tput cnorm; exit' INT TERM

while true; do
    tput cup 0 0

    # Count files
    INPUT_COUNT=$(find "$INPUT_DIR" -name "*.md" 2>/dev/null | wc -l)
    OUTPUT_COUNT=$(find "$OUTPUT_DIR" -name "*.md" 2>/dev/null | wc -l)
    REMAINING=$((INPUT_COUNT - OUTPUT_COUNT))
    [ "$INPUT_COUNT" -gt 0 ] && PERCENT=$((OUTPUT_COUNT * 100 / INPUT_COUNT)) || PERCENT=0

    # GPU stats (Ollama uses GPU)
    GPU_LINE=$(nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null)
    GPU_UTIL=$(echo "$GPU_LINE" | awk -F', ' '{print $1}' | tr -d ' ')
    GPU_MEM_USED=$(echo "$GPU_LINE" | awk -F', ' '{print $2}' | tr -d ' ')
    GPU_MEM_TOTAL=$(echo "$GPU_LINE" | awk -F', ' '{print $3}' | tr -d ' ')

    CPU_UTIL=$(top -bn1 | grep "Cpu(s)" | awk '{printf "%.0f", $2}')

    RAM_LINE=$(free -g | awk '/Mem:/ {print $3, $2}')
    RAM_USED=$(echo "$RAM_LINE" | awk '{print $1}')
    RAM_TOTAL=$(echo "$RAM_LINE" | awk '{print $2}')
    RAM_PERCENT=$((RAM_USED * 100 / RAM_TOTAL))

    # Count ollama processes (clean.py spawns multiple)
    OLLAMA_COUNT=$(pgrep -f "ollama run" 2>/dev/null | wc -l)

    LOAD_1=$(uptime | awk -F'load average: ' '{print $2}' | awk -F', ' '{print $1}')
    LOAD_5=$(uptime | awk -F'load average: ' '{print $2}' | awk -F', ' '{print $2}')
    LOAD_15=$(uptime | awk -F'load average: ' '{print $2}' | awk -F', ' '{print $3}')

    # Handle N/A
    [ "$GPU_UTIL" = "[N/A]" ] || [ -z "$GPU_UTIL" ] && GPU_UTIL=0
    [ "$GPU_MEM_USED" = "[N/A]" ] || [ -z "$GPU_MEM_USED" ] && GPU_MEM_USED=0
    [ "$GPU_MEM_TOTAL" = "[N/A]" ] || [ -z "$GPU_MEM_TOTAL" ] && GPU_MEM_TOTAL=128
    GPU_MEM_PERCENT=$((GPU_MEM_USED * 100 / GPU_MEM_TOTAL))

    # Colors
    RST=$'\033[0m'
    YEL=$'\033[33m'
    PNK=$'\033[35m'
    RED=$'\033[31m'
    GRN=$'\033[32m'
    DIM=$'\033[90m'

    # Get color based on GPU percentage
    if [ "$GPU_UTIL" -ge 90 ]; then
        GPU_COLOR="$RED"
    elif [ "$GPU_UTIL" -ge 70 ]; then
        GPU_COLOR="$PNK"
    elif [ "$GPU_UTIL" -ge 40 ]; then
        GPU_COLOR="$YEL"
    else
        GPU_COLOR="$GRN"
    fi

    # Bar function - 20 chars
    bar() {
        local p=$1
        local f=$((p * 20 / 100))
        local e=$((20 - f))
        for ((i=0; i<f; i++)); do printf "█"; done
        for ((i=0; i<e; i++)); do printf "░"; done
    }

    PBAR=$(bar $PERCENT)
    GBAR=$(bar $GPU_UTIL)
    VBAR=$(bar $GPU_MEM_PERCENT)
    CBAR=$(bar $CPU_UTIL)
    RBAR=$(bar $RAM_PERCENT)

    SBAR="${DIM}░░░░░░░░░░░░░░░░░░░░${RST}"

    # Get latest output file timestamp
    LATEST_FILE=$(ls -t "$OUTPUT_DIR" 2>/dev/null | head -1)
    if [ -n "$LATEST_FILE" ]; then
        LATEST_TIME=$(stat -c %Y "$OUTPUT_DIR/$LATEST_FILE" 2>/dev/null)
        LATEST_FMT=$(date -d "@$LATEST_TIME" "+%H:%M:%S" 2>/dev/null)
        SECS_AGO=$(( $(date +%s) - LATEST_TIME ))
        if [ "$SECS_AGO" -lt 60 ]; then
            AGO="${SECS_AGO}s ago"
        else
            AGO="$((SECS_AGO / 60))m ago"
        fi
    else
        LATEST_FMT="--:--:--"
        AGO=""
    fi

    # Estimate ETA based on rate
    if [ "$OUTPUT_COUNT" -gt 0 ]; then
        FIRST_FILE=$(ls -tr "$OUTPUT_DIR" 2>/dev/null | head -1)
        if [ -n "$FIRST_FILE" ]; then
            FIRST_TIME=$(stat -c %Y "$OUTPUT_DIR/$FIRST_FILE" 2>/dev/null)
            NOW=$(date +%s)
            ELAPSED=$((NOW - FIRST_TIME))
            if [ "$ELAPSED" -gt 0 ] && [ "$OUTPUT_COUNT" -gt 0 ]; then
                RATE=$(echo "scale=2; $OUTPUT_COUNT / $ELAPSED * 60" | bc 2>/dev/null)
                ETA_SECS=$(echo "scale=0; $REMAINING * $ELAPSED / $OUTPUT_COUNT" | bc 2>/dev/null)
                if [ -n "$ETA_SECS" ] && [ "$ETA_SECS" -gt 0 ]; then
                    if [ "$ETA_SECS" -gt 3600 ]; then
                        ETA_STR=$(echo "scale=1; $ETA_SECS / 3600" | bc)h
                    elif [ "$ETA_SECS" -gt 60 ]; then
                        ETA_STR=$(echo "scale=0; $ETA_SECS / 60" | bc)m
                    else
                        ETA_STR="${ETA_SECS}s"
                    fi
                else
                    ETA_STR="--"
                fi
            else
                RATE="--"
                ETA_STR="--"
            fi
        else
            RATE="--"
            ETA_STR="--"
        fi
    else
        RATE="--"
        ETA_STR="--"
    fi

    # Color code load based on 20 cores
    color_load() {
        local load=$1
        local pct=$(echo "$load * 100 / 20" | bc 2>/dev/null || echo 0)
        if [ "$pct" -ge 75 ]; then echo "$RED"
        elif [ "$pct" -ge 50 ]; then echo "$PNK"
        elif [ "$pct" -ge 25 ]; then echo "$YEL"
        else echo "$GRN"
        fi
    }
    L1_COL=$(color_load "$LOAD_1")
    L5_COL=$(color_load "$LOAD_5")
    L15_COL=$(color_load "$LOAD_15")

    DIV="═══════════════════════════════════════════════════════════════"

    echo ""
    echo "  $DIV"
    echo "                    GPU TEXT HARVEST"
    echo "  $DIV"
    printf "  Files  %b %5d / %-5d  (%d remaining)\n" "$SBAR" "$OUTPUT_COUNT" "$INPUT_COUNT" "$REMAINING"
    printf "         %s  %3d%%\n" "$PBAR" "$PERCENT"
    echo "  $DIV"
    printf "  GPU    %b%s%b  %3d%%\n" "$GPU_COLOR" "$GBAR" "$RST" "$GPU_UTIL"
    printf "  VRAM   %s  %3d%%  %5dG\n" "$VBAR" "$GPU_MEM_PERCENT" "$GPU_MEM_USED"
    echo "  $DIV"
    printf "  CPU    %s  %3d%%\n" "$CBAR" "$CPU_UTIL"
    printf "  RAM    %s  %3d%%  %5dG\n" "$RBAR" "$RAM_PERCENT" "$RAM_USED"
    echo "  $DIV"
    printf "  Ollama: %-2d active     Rate: %s/min     ETA: %s\n" "$OLLAMA_COUNT" "$RATE" "$ETA_STR"
    printf "  Latest: %s (%s)\n" "$LATEST_FMT" "$AGO"
    printf "  Load:   %b%s%b (1m)  %b%s%b (5m)  %b%s%b (15m)\n" "$L1_COL" "$LOAD_1" "$RST" "$L5_COL" "$LOAD_5" "$RST" "$L15_COL" "$LOAD_15" "$RST"
    echo "  $DIV"
    echo ""
    echo "  Ctrl+C to exit"

    sleep 2
done
