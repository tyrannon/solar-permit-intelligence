"""Minimal PDF ingestion script.

Reads a single PDF, extracts metadata and text, writes intermediate JSON.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

from pypdf import PdfReader


def extract_pdf_data(pdf_path: Path) -> dict:
    """Extract metadata and text from a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Dictionary with metadata and page-by-page text
    """
    reader = PdfReader(pdf_path)

    # Extract metadata (may be empty/None for some PDFs)
    metadata = reader.metadata
    metadata_dict = {}
    if metadata:
        # Convert metadata to simple dict (metadata values can be various types)
        for key in metadata:
            try:
                metadata_dict[key] = str(metadata[key]) if metadata[key] else None
            except:
                metadata_dict[key] = None

    # Extract text page by page
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        pages.append({
            "page_number": i + 1,
            "text": text,
            "char_count": len(text) if text else 0
        })

    return {
        "document_id": pdf_path.stem,
        "source_file": str(pdf_path),
        "ingestion_timestamp": datetime.now().isoformat(),
        "page_count": len(reader.pages),
        "metadata": metadata_dict,
        "pages": pages
    }


def main():
    """Main ingestion entrypoint."""
    if len(sys.argv) < 2:
        print("Usage: python -m src.ingestion.ingest_pdf <path_to_pdf>")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])

    if not pdf_path.exists():
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)

    if not pdf_path.suffix.lower() == '.pdf':
        print(f"Error: File must be a PDF: {pdf_path}")
        sys.exit(1)

    print(f"Ingesting: {pdf_path.name}")

    # Extract data from PDF
    data = extract_pdf_data(pdf_path)

    # Write to processed directory
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{pdf_path.stem}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Print summary
    print(f"\n✓ Ingestion complete")
    print(f"  Document ID: {data['document_id']}")
    print(f"  Pages: {data['page_count']}")

    total_chars = sum(p['char_count'] for p in data['pages'])
    print(f"  Total characters extracted: {total_chars:,}")

    if data['metadata']:
        print(f"  Metadata fields: {len(data['metadata'])}")
        # Show a few metadata fields if available
        for key in list(data['metadata'].keys())[:3]:
            value = data['metadata'][key]
            if value:
                print(f"    - {key}: {value[:50]}...")
    else:
        print(f"  Metadata: None found")

    print(f"\n  Output: {output_file}")


if __name__ == "__main__":
    main()
