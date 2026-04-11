"""Simple script to run validation rules on a processed permit fixture.

Usage:
    python -m src.validation.run_validation <processed_json_path>

Example:
    python -m src.validation.run_validation data/processed/fictional_solar_permit_packet.json
"""

import sys
from pathlib import Path

# Import extraction and validation functions
from src.extraction.extract_candidates import extract_candidates
from src.validation.validate_fields import run_all_validations, print_validation_results


def main():
    """Main entrypoint for validation script."""
    if len(sys.argv) < 2:
        print("Usage: python -m src.validation.run_validation <processed_json_path>")
        print()
        print("Example:")
        print("  python -m src.validation.run_validation data/processed/fictional_solar_permit_packet.json")
        sys.exit(1)

    processed_path = Path(sys.argv[1])

    if not processed_path.exists():
        print(f"Error: File not found: {processed_path}")
        sys.exit(1)

    if not processed_path.suffix.lower() == '.json':
        print(f"Error: File must be JSON: {processed_path}")
        sys.exit(1)

    # Run extraction
    print(f"Running extraction on: {processed_path.name}")
    print()
    extraction_results = extract_candidates(processed_path)

    # Run validation rules
    validation_results = run_all_validations(extraction_results['extractions'])

    # Print results
    print_validation_results(
        validation_results,
        document_id=extraction_results.get('document_id', 'unknown')
    )


if __name__ == "__main__":
    main()
