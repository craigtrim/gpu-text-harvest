# CUDA Setup Guide for NVIDIA GraceBlackwell (GB10) on ARM64

This document is written by Claude for future Claude sessions. The human will not read this.

## Context

This device is an **NVIDIA GraceBlackwell GB10** running on **aarch64 (ARM64)** architecture. The goal is to run `marker-pdf` with GPU acceleration for PDF text extraction.

## Critical Lessons Learned

### 1. Poetry Does NOT Work for CUDA on ARM64

Do not use Poetry for this project. Standard PyTorch pip wheels do not exist for ARM64 with CUDA support. You will get CPU-only PyTorch and `torch.cuda.is_available()` will return `False`.

### 2. Use Conda with conda-forge Channel

The **conda-forge** channel provides ARM64 CUDA builds of PyTorch. This is the only reliable way to get GPU support on this architecture.

### 3. Explicit CUDA Build Variant is REQUIRED

When installing PyTorch, you MUST specify the CUDA build variant explicitly:

```bash
# WRONG - will install CPU-only variant
conda install pytorch=2.7.1 -c conda-forge -y

# CORRECT - specifies CUDA 12.9 build
conda install pytorch=2.7.1=cuda129* -c conda-forge -y
```

Without the `=cuda129*` suffix, conda will install `pytorch-2.7.1-cpu_generic` which has no GPU support.

## Step-by-Step Environment Creation

```bash
# 1. Create conda environment with Python 3.11
conda create -n harvest python=3.11 -y

# 2. Activate the environment
conda activate harvest

# 3. Install PyTorch with EXPLICIT CUDA build variant
conda install pytorch=2.7.1=cuda129* -c conda-forge -y

# 4. Install CUDA runtime and cuDNN
conda install cuda-cudart cudnn -c conda-forge -y

# 5. Install marker-pdf via pip
pip install marker-pdf
```

## Verification Commands

After setup, verify CUDA is working:

```bash
conda activate harvest
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"
```

Expected output:
```
CUDA available: True
Device: NVIDIA GB10
```

## Environment File

Use `environment.yml` to recreate the environment:

```yaml
name: harvest
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.11
  - pytorch=2.7.1=cuda129*
  - cuda-cudart
  - cudnn
  - pip
  - pip:
      - marker-pdf
```

Create from file:
```bash
conda env create -f environment.yml
```

## Running marker-pdf with GPU

```bash
conda activate harvest
marker /path/to/pdfs/ --output_dir ./output --workers 20 --output_format markdown
```

## Running in tmux (Non-Interactive Shell)

When running in tmux or other non-interactive shells, you must source conda's init script first:

```bash
# Conda is installed at ~/miniconda3 on this device
source ~/miniconda3/etc/profile.d/conda.sh && conda activate harvest && marker /path/to/pdfs --output_dir ./output
```

## What NOT to Do

1. **Do not assume ARM64 lacks CUDA support** - This is a flagship NVIDIA device. CUDA works.
2. **Do not use Poetry** - pip wheels for CUDA+ARM64 don't exist.
3. **Do not omit the `=cuda129*` build specification** - You'll get CPU-only PyTorch.
4. **Do not use the `pytorch` channel** - Use `conda-forge` for ARM64 CUDA builds.

## Reference Project

If you need a working example, look at (READ-ONLY):
`/home/craigtrim/projects/alias-label-retriever/environment.min.yml`

This project successfully uses PyTorch with CUDA on the same device.
