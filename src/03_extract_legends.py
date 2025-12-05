#!/usr/bin/env python3
"""
Step 3: Extract raw legend text chunks from cleaned transcripts.

Processes in overlapping chunks to handle long transcripts and avoid
missing legends that span chunk boundaries.

Usage:
    python 03_extract_legends.py ./output-clean -o ./output-legend-chunk
    python 03_extract_legends.py ./output-clean -o ./output-legend-chunk -n 10
"""

import argparse
import requests
from pathlib import Path


OLLAMA_URL = "http://localhost:11434/api/generate"


DEFAULT_CHUNK_SIZE = 3000  # characters per chunk
DEFAULT_OVERLAP = 1000  # overlap between chunks
chunk_size = DEFAULT_CHUNK_SIZE
chunk_overlap = DEFAULT_OVERLAP

PROMPT_TEMPLATE = """Extract the transcript's **GRADE LEGEND** section verbatim.

Focus on CONTENT, not headers.

Identify any block whose primary purpose is to define grade codes and their meanings.
Such blocks typically contain multiple entries of the form:
- A = ...
- B = ...
- W = ...
- I = ...
- AU = ...
- P / NP / S / U / WF / WP, etc.

These may appear as:
- Code → description lists
- Paragraphs explaining what each grade symbol means
- Tables of grade codes
- Any cluster of grade symbols paired with definitions

Rules:
1. Copy the entire block **exactly as-is** (no rewriting, no formatting changes).
2. If multiple separate legend blocks exist, return all of them in the order found.
3. If nothing matches, output: NO_LEGEND

{text}"""

PROMPT_TEMPLATE_2 = """Find the GRADING SYSTEM or GRADE KEY in this transcript.

Look for ANY section that explains what letter grades mean. This includes:
- Tables with Grade and Quality Points columns
- Lists explaining A, B, C, D, F grades
- Sections titled "Grading System", "Grade Legend", "Marking System", "Grade Scale"
- Any explanation of codes like W (Withdraw), I (Incomplete), AU (Audit), P (Pass)

If you find such a section, copy it EXACTLY as it appears.
If not found, output: NO_LEGEND

{text}"""


def chunk_text(text: str) -> list[str]:
    """Split text into overlapping chunks using sliding window."""
    cs = chunk_size
    overlap = chunk_overlap

    if len(text) <= cs:
        return [text]

    chunks = []
    start = 0
    stride = cs - overlap  # how far to advance each iteration

    while start < len(text):
        end = min(start + cs, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # If we've reached the end, stop
        if end >= len(text):
            break

        start += stride

    return chunks


def extract_from_chunk(text: str, model: str, prompt_template: str) -> str | None:
    """Extract legend from a single chunk using given prompt template."""
    escaped_text = text.replace("{", "{{").replace("}", "}}")
    prompt = prompt_template.format(text=escaped_text)

    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )
        if resp.status_code == 200:
            response = resp.json().get("response", "").strip()
            if response and "NO_LEGEND" not in response:
                return response
        return None
    except requests.Timeout:
        return None
    except Exception:
        return None


def extract_chunk(text: str, model: str) -> tuple[str | None, int]:
    """Extract legend from transcript, processing in chunks.

    Returns tuple of (result, prompt_number) where prompt_number is 1 or 2.
    """
    chunks = chunk_text(text)

    # Try each chunk with first prompt
    for chunk in chunks:
        result = extract_from_chunk(chunk, model, PROMPT_TEMPLATE)
        if result:
            return result, 1

    # If first prompt failed, try second prompt on all chunks
    for chunk in chunks:
        result = extract_from_chunk(chunk, model, PROMPT_TEMPLATE_2)
        if result:
            return result, 2

    return None, 0


def main():
    parser = argparse.ArgumentParser(description="Extract legend chunks from transcripts")
    parser.add_argument("input_dir", help="Directory containing cleaned .md files")
    parser.add_argument("--output", "-o", default="./output-legend-chunk", help="Output directory")
    parser.add_argument("--model", "-m", default="qwen2.5:7b", help="Ollama model")
    parser.add_argument("--limit", "-n", type=int, help="Limit number of files")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing output files")
    parser.add_argument("--chunk-size", "-c", type=int, default=DEFAULT_CHUNK_SIZE, help="Chunk size in chars")
    parser.add_argument("--overlap", type=int, default=DEFAULT_OVERLAP, help="Overlap between chunks in chars")
    args = parser.parse_args()

    global chunk_size, chunk_overlap
    chunk_size = args.chunk_size
    chunk_overlap = args.overlap

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    md_files = sorted(input_dir.glob("*.md"))

    if args.limit:
        md_files = md_files[:args.limit]

    # Skip existing by default
    if not args.overwrite:
        original_count = len(md_files)
        md_files = [f for f in md_files if not (output_dir / f.with_suffix(".txt").name).exists()]
        skipped = original_count - len(md_files)
        if skipped:
            print(f"Skipped: {skipped} existing files")

    print(f"Input: {input_dir}")
    print(f"Output: {output_dir}")
    print(f"Model: {args.model}")
    print(f"Chunk size: {chunk_size}, overlap: {chunk_overlap}")
    print(f"Files: {len(md_files)}")
    print()

    if not md_files:
        print("No files to process.")
        return

    files_with_chunks = 0

    for i, md_file in enumerate(md_files, 1):
        print(f"[{i}/{len(md_files)}] {md_file.name}...", end=" ", flush=True)

        text = md_file.read_text()
        num_chunks = len(chunk_text(text))

        chunk, prompt_num = extract_chunk(text, args.model)

        output_file = output_dir / md_file.with_suffix(".txt").name

        if chunk:
            files_with_chunks += 1
            output_file.write_text(chunk)
            print(f"found ({len(chunk)} chars, {num_chunks} chunks, prompt {prompt_num})")
        else:
            output_file.write_text("")
            print(f"no legend ({num_chunks} chunks)")

    print()
    print(f"Files with legends: {files_with_chunks}/{len(md_files)}")
    print(f"Output: {output_dir}")


if __name__ == "__main__":
    main()
