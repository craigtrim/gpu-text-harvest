#!/bin/bash
# Pass 2: LLM cleanup using Ollama/qwen2.5:7b

INPUT_DIR="./output-raw"
OUTPUT_DIR="./output-clean"

cd /home/craigtrim/projects/gpu-text-harvest

echo "=== Pass 2: LLM Cleanup ==="
echo "Input:  $INPUT_DIR"
echo "Output: $OUTPUT_DIR"
echo "Model:  qwen2.5:7b"
echo ""

python src/02_clean_text.py $INPUT_DIR -o $OUTPUT_DIR "$@"
