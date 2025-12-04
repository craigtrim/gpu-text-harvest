"""CLI for GPU-accelerated PDF text extraction."""

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered


def extract_single(pdf_path: Path, output_dir: Path, models: dict) -> dict:
    """Extract text from a single PDF."""
    converter = PdfConverter(artifact_dict=models)
    rendered = converter(str(pdf_path))
    text, _, images = text_from_rendered(rendered)

    result = {
        "source_file": pdf_path.name,
        "markdown": text,
        "image_count": len(images),
    }

    # Create subdirectories
    md_dir = output_dir / "md"
    json_dir = output_dir / "json"
    md_dir.mkdir(parents=True, exist_ok=True)
    json_dir.mkdir(parents=True, exist_ok=True)

    # Save markdown output
    md_path = md_dir / f"{pdf_path.stem}.md"
    md_path.write_text(text, encoding="utf-8")

    # Save JSON metadata
    json_path = json_dir / f"{pdf_path.stem}.json"
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    return result


def main():
    parser = argparse.ArgumentParser(
        prog="harvest",
        description="GPU-accelerated PDF text extraction using marker-pdf",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  harvest /path/to/file.pdf -o ./output
  harvest /path/to/pdfs/ -o ./output
  harvest /path/to/pdfs/ -o ./output -n 100 -w 4
        """,
    )
    parser.add_argument(
        "input",
        type=Path,
        metavar="INPUT",
        help="Input PDF file or directory containing PDFs",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path("./output"),
        metavar="DIR",
        help="Output directory (creates md/ and json/ subdirs) [default: ./output]",
    )
    parser.add_argument(
        "-w", "--workers",
        type=int,
        default=1,
        metavar="N",
        help="Number of parallel workers [default: 1]",
    )
    parser.add_argument(
        "-n", "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Limit number of PDFs to process [default: all]",
    )
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: Input path does not exist: {args.input}", file=sys.stderr)
        sys.exit(1)

    args.output.mkdir(parents=True, exist_ok=True)

    print("Loading models...")
    models = create_model_dict()
    print("Models loaded.")

    if args.input.is_file():
        pdf_files = [args.input]
    else:
        pdf_files = list(args.input.glob("*.pdf"))

    if not pdf_files:
        print("No PDF files found.", file=sys.stderr)
        sys.exit(1)

    if args.limit:
        pdf_files = pdf_files[:args.limit]

    total = len(pdf_files)
    print(f"Processing {total} PDF(s) with {args.workers} worker(s)...")

    if args.workers == 1:
        for i, pdf_path in enumerate(pdf_files, 1):
            print(f"[{i}/{total}] {pdf_path.name}")
            try:
                result = extract_single(pdf_path, args.output, models)
                print(f"  -> {result['image_count']} images")
            except Exception as e:
                print(f"  -> ERROR: {e}", file=sys.stderr)
    else:
        completed = 0
        errors = 0
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(extract_single, pdf, args.output, models): pdf
                for pdf in pdf_files
            }
            for future in as_completed(futures):
                pdf_path = futures[future]
                completed += 1
                try:
                    result = future.result()
                    print(f"[{completed}/{total}] {pdf_path.name} -> {result['image_count']} images")
                except Exception as e:
                    errors += 1
                    print(f"[{completed}/{total}] {pdf_path.name} -> ERROR: {e}", file=sys.stderr)

        if errors:
            print(f"\nCompleted with {errors} error(s).")

    print("Done.")


if __name__ == "__main__":
    main()
