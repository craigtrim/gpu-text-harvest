# gpu-text-harvest

GPU-accelerated PDF text extraction using [marker-pdf](https://github.com/VikParuchuri/marker). Optimized for NVIDIA GraceBlackwell.

## Installation

```bash
poetry install
```

## Quick Start

```bash
scripts/run.sh       # Start (20 workers, skips existing)
scripts/attach.sh    # View progress (detach: Ctrl+b d)
scripts/kill.sh      # Stop
```

## Direct CLI

```bash
poetry run marker /path/to/pdfs/ \
  --output_dir ./output \
  --workers 20 \
  --skip_existing \
  --output_format markdown
```

## Requirements

- Python 3.10-3.12
- NVIDIA GPU
- tmux
