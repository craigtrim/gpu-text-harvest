# gpu-text-harvest

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Two-pass PDF text extraction and cleanup pipeline.

## Pipeline

1. **Pass 1 - Extract**: Fast text extraction from PDFs using PyMuPDF (~140 files/sec)
2. **Pass 2 - Clean**: LLM cleanup using Ollama/mistral to format as clean markdown

## Structure

```
gpu-text-harvest/
├── src/
│   ├── extract.py    # PyMuPDF text extraction
│   └── clean.py      # Ollama LLM cleanup
├── scripts/
│   ├── run-extract.sh
│   ├── run-clean.sh
│   └── monitor.sh
├── output-raw/       # Pass 1 output (gitignored)
└── output-clean/     # Pass 2 output (gitignored)
```

## Usage

```bash
# Pass 1: Extract text from PDFs
./scripts/run-extract.sh              # Full run
./scripts/run-extract.sh -n 100       # Limit to 100 files

# Pass 2: Clean with Ollama
./scripts/run-clean.sh                # Full run (skips existing)
./scripts/run-clean.sh -n 50          # Limit to 50 files
./scripts/run-clean.sh --overwrite    # Reprocess all

# Monitor progress
./scripts/monitor.sh
```

## Requirements

- Python 3.10+
- PyMuPDF (`pip install pymupdf`)
- Ollama with mistral model (`ollama pull mistral`)
