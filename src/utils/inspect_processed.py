"""Minimal inspection utility for processed JSON files.

Reads processed JSON and prints compact page summaries with simple heuristic tags.
"""

import json
import sys
from pathlib import Path


# Simple keyword-based heuristics for page tagging
HEURISTIC_RULES = {
    "top_level_form": [
        "permit application",
        "applicant information",
        "owner information",
        "contractor information",
        "project information",
    ],
    "calculations": [
        "calculation",
        "load calculation",
        "ampacity",
        "wire sizing",
        "voltage drop",
        "maximum power",
    ],
    "inverter_info": [
        "inverter",
        "micro inverter",
        "string inverter",
        "inverter spec",
        "inverter model",
    ],
    "module_info": [
        "module",
        "solar panel",
        "pv module",
        "module spec",
        "panel spec",
        "watts per module",
    ],
    "diagram": [
        "diagram",
        "site plan",
        "one-line",
        "single-line",
        "schematic",
        "layout",
        "electrical drawing",
    ],
    "labels_markings": [
        "label",
        "placard",
        "warning label",
        "marking",
        "signage",
    ],
    "grounding_bonding": [
        "grounding",
        "bonding",
        "ground fault",
        "equipment ground",
        "grounding electrode",
    ],
    "rapid_shutdown": [
        "rapid shutdown",
        "rapid shut down",
        "nec 690.12",
        "module-level",
        "mlpe",
    ],
    "load_center": [
        "load center",
        "service panel",
        "main panel",
        "breaker panel",
        "bus bar",
        "busbar",
    ],
}


def apply_heuristics(text: str) -> list[str]:
    """Apply simple keyword matching to identify page tags.

    Args:
        text: Page text content

    Returns:
        List of matched tag names
    """
    text_lower = text.lower()
    tags = []

    for tag_name, keywords in HEURISTIC_RULES.items():
        for keyword in keywords:
            if keyword in text_lower:
                tags.append(tag_name)
                break  # Only add each tag once per page

    return tags


def truncate_preview(text: str, max_length: int = 60) -> str:
    """Create a short preview of text content.

    Args:
        text: Full text
        max_length: Maximum preview length

    Returns:
        Truncated preview with ellipsis if needed
    """
    # Clean up whitespace
    text = " ".join(text.split())

    if len(text) <= max_length:
        return text

    return text[:max_length] + "..."


def inspect_processed_json(json_path: Path):
    """Read and inspect a processed JSON file.

    Args:
        json_path: Path to processed JSON file
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Print header
    print(f"\nInspecting: {data.get('document_id', 'unknown')}")
    print(f"Source: {data.get('source_file', 'unknown')}")
    print(f"Pages: {data.get('page_count', 0)}")
    print(f"Ingested: {data.get('ingestion_timestamp', 'unknown')}")
    print("\n" + "=" * 100)

    # Print one line per page
    pages = data.get('pages', [])
    for page in pages:
        page_num = page.get('page_number', '?')
        char_count = page.get('char_count', 0)
        text = page.get('text', '')

        # Apply heuristics
        tags = apply_heuristics(text)
        tags_str = ", ".join(tags) if tags else "no_tags"

        # Create preview
        preview = truncate_preview(text, max_length=50)

        # Print compact line
        print(f"p{page_num:2d} | {char_count:5d} chars | [{tags_str:30s}] | {preview}")

    print("=" * 100)

    # Print tag summary
    all_tags = []
    for page in pages:
        all_tags.extend(apply_heuristics(page.get('text', '')))

    tag_counts = {}
    for tag in all_tags:
        tag_counts[tag] = tag_counts.get(tag, 0) + 1

    if tag_counts:
        print("\nTag Summary:")
        for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1]):
            print(f"  {tag}: {count} page(s)")
    else:
        print("\nNo tags identified across all pages.")


def main():
    """Main inspection entrypoint."""
    if len(sys.argv) < 2:
        print("Usage: python -m src.utils.inspect_processed <path_to_processed_json>")
        sys.exit(1)

    json_path = Path(sys.argv[1])

    if not json_path.exists():
        print(f"Error: File not found: {json_path}")
        sys.exit(1)

    if not json_path.suffix.lower() == '.json':
        print(f"Error: File must be JSON: {json_path}")
        sys.exit(1)

    inspect_processed_json(json_path)


if __name__ == "__main__":
    main()
