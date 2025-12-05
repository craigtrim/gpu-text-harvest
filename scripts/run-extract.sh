#!/bin/bash
# Pass 1: Fast PDF text extraction using PyMuPDF

PDF_DIR="/home/craigtrim/data/maryville/transcripts"
OUTPUT_DIR="./output-raw"

cd /home/craigtrim/projects/gpu-text-harvest

echo "=== Pass 1: PDF Text Extraction ==="
echo "Input:  $PDF_DIR"
echo "Output: $OUTPUT_DIR"
echo ""

python src/01_pdf_to_text.py "$PDF_DIR" -o "$OUTPUT_DIR" -w 8 "$@"
