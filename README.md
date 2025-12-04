# gpu-text-harvest

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Poetry](https://img.shields.io/badge/packaging-poetry-cyan.svg)](https://python-poetry.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![NVIDIA GPU](https://img.shields.io/badge/NVIDIA-GraceBlackwell-76B900.svg)](https://www.nvidia.com/)

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
