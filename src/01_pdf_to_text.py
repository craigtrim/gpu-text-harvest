#!/usr/bin/env python3
"""
Step 1: Fast PDF text extraction using PyMuPDF.

Extracts raw text from PDF files in parallel.

Usage:
    python 01_pdf_to_text.py /path/to/pdfs -o ./output-raw
    python 01_pdf_to_text.py /path/to/pdfs -o ./output-raw -n 100  # limit to 100 files
"""

import argparse
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import fitz  # PyMuPDF


def extract_text(pdf_path: str) -> tuple[str, str, int]:
    """Extract text from PDF using PyMuPDF. Returns (filename, text, page_count)."""
    try:
        doc = fitz.open(pdf_path)
        text = "\n".join(page.get_text() for page in doc)
        page_count = len(doc)
        doc.close()
        return os.path.basename(pdf_path), text, page_count
    except Exception as e:
        return os.path.basename(pdf_path), f"ERROR: {e}", 0


def process_pdf(args: tuple) -> dict:
    """Process a single PDF file."""
    pdf_path, output_dir = args
    start = time.time()

    filename, text, page_count = extract_text(pdf_path)
    extract_time = time.time() - start

    # Save output
    base_name = Path(filename).stem
    output_path = Path(output_dir) / f"{base_name}.md"
    output_path.write_text(text)

    return {
        "file": filename,
        "pages": page_count,
        "extract_time": extract_time,
        "chars": len(text)
    }


def main():
    parser = argparse.ArgumentParser(description="Fast PDF text extraction")
    parser.add_argument("input_dir", help="Directory containing PDFs")
    parser.add_argument("--output", "-o", default="./output-raw", help="Output directory")
    parser.add_argument("--workers", "-w", type=int, default=8, help="Number of workers")
    parser.add_argument("--limit", "-n", type=int, help="Limit number of files to process")
    args = parser.parse_args()

    # Setup
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find PDFs
    pdf_files = list(input_dir.glob("*.pdf"))
    if args.limit:
        pdf_files = pdf_files[:args.limit]

    print(f"Found {len(pdf_files)} PDFs")
    print(f"Output: {output_dir}")
    print(f"Workers: {args.workers}")
    print()

    # Process
    start_time = time.time()
    completed = 0
    total_pages = 0

    task_args = [(str(f), str(output_dir)) for f in pdf_files]

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process_pdf, arg): arg for arg in task_args}

        for future in as_completed(futures):
            try:
                result = future.result()
                completed += 1
                total_pages += result["pages"]

                elapsed = time.time() - start_time
                rate = completed / elapsed if elapsed > 0 else 0

                print(f"[{completed}/{len(pdf_files)}] {result['file']}: "
                      f"{result['pages']} pages, {result['extract_time']:.3f}s | {rate:.1f} files/sec")

            except Exception as e:
                print(f"Error: {e}")

    # Summary
    total_time = time.time() - start_time
    print()
    print(f"Completed: {completed} files, {total_pages} pages")
    print(f"Total time: {total_time:.1f}s")
    if completed:
        print(f"Average: {total_time/completed:.3f}s per file")
        print(f"Rate: {completed/total_time:.1f} files/sec")


if __name__ == "__main__":
    main()
