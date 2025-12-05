#!/usr/bin/env python3
"""
Step 4: Format legend chunks into CSV.

Converts extracted legend text into structured CODE,DESCRIPTION CSV format.

Usage:
    python 04_legends_to_csv.py ./output-legend-chunk -o ./output-legend-csv
    python 04_legends_to_csv.py ./output-legend-chunk -o ./output-legend-csv -n 10
"""

import argparse
import requests
from pathlib import Path


OLLAMA_URL = "http://localhost:11434/api/generate"


PROMPT_TEMPLATE = """Convert to CSV: CODE,DESCRIPTION

Only letter codes (A, B, W, WP, AU, I, P). No symbols, no header.

{text}

CSV:"""


def format_csv(chunk: str, model: str) -> str | None:
    """Format legend chunk into CSV."""
    escaped_text = chunk.replace("{", "{{").replace("}", "}}")
    prompt = PROMPT_TEMPLATE.format(text=escaped_text)

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
        if resp.status_code != 200:
            return None

        response = resp.json().get("response", "").strip()
        if not response:
            return None

        # Validate and clean CSV
        lines = []
        for line in response.split("\n"):
            line = line.strip()
            if not line:
                continue
            # Skip lines that don't look like CSV
            if "," not in line:
                continue
            parts = line.split(",", 1)
            if len(parts) != 2:
                continue
            code = parts[0].strip()
            desc = parts[1].strip()
            # Validate code is letters only, max 4 chars
            if code and code.isalpha() and len(code) <= 4:
                lines.append(f"{code},{desc}")

        return "\n".join(lines) if lines else None

    except requests.Timeout:
        return None
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser(description="Format legend chunks into CSV")
    parser.add_argument("input_dir", help="Directory containing legend chunk .txt files")
    parser.add_argument("--output", "-o", default="./output-legend-csv", help="Output directory")
    parser.add_argument("--model", "-m", default="qwen2.5:7b", help="Ollama model")
    parser.add_argument("--limit", "-n", type=int, help="Limit number of files")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing output files")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Only process non-empty chunk files
    txt_files = sorted(input_dir.glob("*.txt"))
    txt_files = [f for f in txt_files if f.stat().st_size > 0]

    if args.limit:
        txt_files = txt_files[:args.limit]

    # Skip existing by default
    if not args.overwrite:
        original_count = len(txt_files)
        txt_files = [f for f in txt_files if not (output_dir / f.with_suffix(".csv").name).exists()]
        skipped = original_count - len(txt_files)
        if skipped:
            print(f"Skipped: {skipped} existing files")

    print(f"Input: {input_dir}")
    print(f"Output: {output_dir}")
    print(f"Model: {args.model}")
    print(f"Files: {len(txt_files)}")
    print()

    if not txt_files:
        print("No files to process.")
        return

    successful = 0

    for i, txt_file in enumerate(txt_files, 1):
        print(f"[{i}/{len(txt_files)}] {txt_file.name}...", end=" ", flush=True)

        chunk = txt_file.read_text()
        csv_content = format_csv(chunk, args.model)

        output_file = output_dir / txt_file.with_suffix(".csv").name

        if csv_content:
            successful += 1
            output_file.write_text(csv_content)
            line_count = len(csv_content.split("\n"))
            print(f"{line_count} entries")
        else:
            output_file.write_text("")
            print("failed")

    print()
    print(f"Successful: {successful}/{len(txt_files)}")
    print(f"Output: {output_dir}")


if __name__ == "__main__":
    main()
