#!/bin/bash
# Step 1: Extract legend chunks from cleaned transcripts

INPUT_DIR="./output-clean"
OUTPUT_DIR="./output-legend-chunk"
MODEL="qwen2.5:7b"

cd /home/craigtrim/projects/gpu-text-harvest

echo "=== Extract Legend Chunks ==="
echo "Input:  $INPUT_DIR"
echo "Output: $OUTPUT_DIR"
echo "Model:  $MODEL"
echo ""

python src/03_extract_legends.py $INPUT_DIR -o $OUTPUT_DIR -m $MODEL "$@"
