#!/usr/bin/env python3
"""
Step 2: LLM cleanup pass for raw extracted text using Ollama.

Cleans and formats raw PDF text into structured markdown.

Usage:
    python 02_clean_text.py ./output-raw -o ./output-clean
    python 02_clean_text.py ./output-raw -o ./output-clean --model qwen2.5:7b
    python 02_clean_text.py ./output-raw -o ./output-clean -n 10  # limit to 10 files
"""

import argparse
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock


OLLAMA_URL = "http://localhost:11434/api/generate"


PROMPT_TEMPLATE = """Clean up this university transcript text. Output ONLY the cleaned content.

CRITICAL RULES:
1. Output ALL data - NEVER use "..." or "continued" or skip anything
2. NO preamble like "Here's the cleaned..." - start directly with the content
3. NO markdown code blocks (no triple backticks)
4. Merge broken lines into complete sentences
5. Use markdown tables for course/grade data

Raw text:
{text}

Cleaned output (start immediately, no preamble):"""

DEFAULT_CHUNK_SIZE = 2000  # characters per chunk
chunk_size = DEFAULT_CHUNK_SIZE

print_lock = Lock()


def chunk_text(text: str, size: int = None) -> list[str]:
    """Split text into chunks, trying to break at paragraph boundaries."""
    cs = size if size else chunk_size
    if len(text) <= cs:
        return [text]

    chunks = []
    remaining = text

    while remaining:
        if len(remaining) <= cs:
            chunks.append(remaining)
            break

        # Try to find a good break point (double newline, then single newline)
        chunk = remaining[:cs]

        # Look for paragraph break
        break_point = chunk.rfind('\n\n')
        if break_point == -1 or break_point < cs // 2:
            # Fall back to single newline
            break_point = chunk.rfind('\n')
        if break_point == -1 or break_point < cs // 2:
            # Fall back to space
            break_point = chunk.rfind(' ')
        if break_point == -1:
            break_point = cs

        chunks.append(remaining[:break_point].strip())
        remaining = remaining[break_point:].strip()

    return chunks


def clean_chunk_with_ollama(text: str, model: str) -> str:
    """Use Ollama to clean a single chunk of text."""
    prompt = PROMPT_TEMPLATE.format(text=text)

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
            if response:
                return response
        return text
    except requests.Timeout:
        return text  # Keep original on timeout
    except Exception:
        return text  # Keep original on error


def clean_with_ollama(text: str, model: str) -> str:
    """Clean text by processing in chunks and combining results."""
    chunks = chunk_text(text)

    if len(chunks) == 1:
        return clean_chunk_with_ollama(text, model)

    # Process each chunk
    cleaned_chunks = []
    for chunk in chunks:
        cleaned = clean_chunk_with_ollama(chunk, model)
        if cleaned:
            cleaned_chunks.append(cleaned)

    return "\n\n".join(cleaned_chunks) if cleaned_chunks else text


def process_file(args: tuple) -> dict:
    """Process a single file. Returns result dict."""
    md_file, output_path, model = args
    start = time.time()

    raw_text = md_file.read_text()
    cleaned = clean_with_ollama(raw_text, model)
    elapsed = time.time() - start

    if cleaned is None:
        # Error or timeout - keep original
        output_path.write_text(raw_text)
        return {"file": md_file.name, "time": elapsed, "status": "error"}

    output_path.write_text(cleaned)
    return {"file": md_file.name, "time": elapsed, "status": "ok"}


def main():
    parser = argparse.ArgumentParser(description="LLM cleanup pass for extracted text")
    parser.add_argument("input_dir", help="Directory containing raw .md files")
    parser.add_argument("--output", "-o", default="./output-clean", help="Output directory")
    parser.add_argument("--model", "-m", default="qwen2.5:7b", help="Ollama model")
    parser.add_argument("--limit", "-n", type=int, help="Limit number of files")
    parser.add_argument("--workers", "-w", type=int, default=1, help="Parallel workers")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing output files")
    parser.add_argument("--chunk-size", "-c", type=int, default=DEFAULT_CHUNK_SIZE, help="Chunk size in chars")
    args = parser.parse_args()

    global chunk_size
    chunk_size = args.chunk_size

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    md_files = sorted(input_dir.glob("*.md"))
    if args.limit:
        md_files = md_files[:args.limit]

    # Skip existing by default (unless --overwrite)
    if not args.overwrite:
        original_count = len(md_files)
        md_files = [f for f in md_files if not (output_dir / f.name).exists()]
        skipped = original_count - len(md_files)
        if skipped:
            print(f"Skipped: {skipped} existing files")

    print(f"Input: {input_dir}")
    print(f"Output: {output_dir}")
    print(f"Model: {args.model}")
    print(f"Chunk size: {chunk_size} chars")
    print(f"Files: {len(md_files)}")
    print(f"Workers: {args.workers}")
    print()

    if not md_files:
        print("No files to process.")
        return

    start_time = time.time()
    completed = 0
    errors = 0

    # Build task list
    tasks = [(f, output_dir / f.name, args.model) for f in md_files]

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process_file, task): task for task in tasks}

        for future in as_completed(futures):
            result = future.result()
            completed += 1
            if result["status"] == "error":
                errors += 1

            elapsed = time.time() - start_time
            rate = completed / elapsed if elapsed > 0 else 0
            remaining = len(md_files) - completed
            eta_seconds = remaining / rate if rate > 0 else 0

            if eta_seconds > 3600:
                eta_str = f"{eta_seconds/3600:.1f}h"
            elif eta_seconds > 60:
                eta_str = f"{eta_seconds/60:.0f}m"
            else:
                eta_str = f"{eta_seconds:.0f}s"

            status = "err" if result["status"] == "error" else "ok"
            with print_lock:
                print(f"[{completed}/{len(md_files)}] {result['file']}: "
                      f"{result['time']:.1f}s [{status}] | {rate:.1f}/min ETA: {eta_str}")

    total_time = time.time() - start_time
    print()
    print(f"Completed: {completed} files ({errors} errors)")
    print(f"Total time: {total_time:.1f}s")
    if completed:
        print(f"Throughput: {completed/total_time*60:.1f} files/min")


if __name__ == "__main__":
    main()
