# Claude Session Memory - GPU Text Harvest

## Project Overview

A multi-step PDF transcript extraction pipeline optimized for GPU (Nvidia Graceblackwell). Processes ~17,697 university transcripts.

## Pipeline Steps

| Step | Script | Shell Script | Description |
|------|--------|--------------|-------------|
| 1 | `src/01_pdf_to_text.py` | `scripts/run-extract.sh` | PyMuPDF PDF extraction → `output-raw/` |
| 2 | `src/02_clean_text.py` | `scripts/run-clean.sh` | LLM cleanup → `output-clean/` |
| 3 | `src/03_extract_legends.py` | `scripts/run-legend-chunk.sh` | Legend extraction → `output-legend-chunk/` |
| 4 | `src/04_legends_to_csv.py` | `scripts/run-legend-csv.sh` | CSV formatting → `output-legend-csv/` |

## Key Technical Decisions

### Model Selection
- **Use `qwen2.5:7b`** for accuracy over speed (not mistral)
- Default model is set in all scripts

### HTTP API vs Subprocess
- Switched from `subprocess.run(["ollama", "run", model])` to HTTP API
- Endpoint: `http://localhost:11434/api/generate`
- Significant performance improvement

### Worker Count
- **Use 1 worker with single GPU** - multiple workers just queue up
- Default `--workers 1` in `02_clean_text.py`

### Chunking Strategy
- `03_extract_legends.py` uses **sliding window chunking**
- Default: `chunk_size=3000`, `overlap=1000`
- Prevents legends from being split at chunk boundaries

### Fallback Prompts
- `03_extract_legends.py` has two prompts (PROMPT_TEMPLATE and PROMPT_TEMPLATE_2)
- If first prompt fails on all chunks, tries second prompt
- Returns tuple `(result, prompt_number)` to track which succeeded

### Skip Existing Files
- All scripts skip existing output files by default
- Use `--overwrite` flag to reprocess

## Pending Cleanup (DO THIS FIRST)

The following old files need to be deleted:
```bash
cd /home/craigtrim/projects/gpu-text-harvest
rm src/extract.py src/clean.py src/extract_legend_chunk.py src/extract_legend_csv.py src/extract_legends.py scripts/run-legends.sh
```

Then commit:
```bash
git add -A
git commit -m "Rename scripts with numbered prefixes for clarity

- extract.py → 01_pdf_to_text.py
- clean.py → 02_clean_text.py
- extract_legend_chunk.py → 03_extract_legends.py
- extract_legend_csv.py → 04_legends_to_csv.py
- Updated shell scripts to reference new filenames
- Removed legacy extract_legends.py and run-legends.sh

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push
```

## Output Directories

| Directory | Contents | Format |
|-----------|----------|--------|
| `output-raw/` | Raw PDF text extraction | `.md` |
| `output-clean/` | LLM-cleaned markdown | `.md` |
| `output-legend-chunk/` | Extracted grade legends | `.txt` |
| `output-legend-csv/` | Structured grade codes | `.csv` |

## Common Commands

```bash
# Run full pipeline
./scripts/run-extract.sh
./scripts/run-clean.sh
./scripts/run-legend-chunk.sh
./scripts/run-legend-csv.sh

# Process limited files for testing
python src/01_pdf_to_text.py /path/to/pdfs -o ./output-raw -n 10
python src/02_clean_text.py ./output-raw -o ./output-clean -n 10
python src/03_extract_legends.py ./output-clean -o ./output-legend-chunk -n 10
python src/04_legends_to_csv.py ./output-legend-chunk -o ./output-legend-csv -n 10

# Force reprocessing
python src/02_clean_text.py ./output-raw -o ./output-clean --overwrite
```

## Sanity Check Notes

- Empty `.txt` files in `output-legend-chunk/` are **expected** when transcripts have no grade legend
- Not all transcripts contain grade legends - this is normal
- High school transcripts and some transfer credit docs often lack legends

## Session Issues (Previous Session)

- Bash tool was failing due to non-existent working directory (`fast-extract/`)
- Always start Claude Code from `/home/craigtrim/projects/gpu-text-harvest`
- If Bash fails with exit code 1 and no output, check working directory exists

## File Locations

- PDF source: `/home/craigtrim/data/maryville/transcripts/`
- Project root: `/home/craigtrim/projects/gpu-text-harvest/`
