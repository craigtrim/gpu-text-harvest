#!/bin/bash
# Step 2: Format legend chunks into CSV

INPUT_DIR="./output-legend-chunk"
OUTPUT_DIR="./output-legend-csv"

cd /home/craigtrim/projects/gpu-text-harvest

echo "=== Format Legends to CSV ==="
echo "Input:  $INPUT_DIR"
echo "Output: $OUTPUT_DIR"
echo "Model:  qwen2.5:7b"
echo ""

python src/04_legends_to_csv.py $INPUT_DIR -o $OUTPUT_DIR "$@"
