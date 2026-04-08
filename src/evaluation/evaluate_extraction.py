"""Minimal evaluation utility for field extraction.

Compares extracted field values against ground truth for four core fields:
- project_address
- contractor_name
- jurisdiction
- system_size_kw
"""

import json
import sys
from pathlib import Path
from typing import Union, Optional

# Import the extraction function
from src.extraction.extract_candidates import extract_candidates


def normalize_for_comparison(value: Union[str, float, None]) -> Union[str, float]:
    """Normalize a value for comparison.

    Args:
        value: Field value (may be None, string, or float)

    Returns:
        Normalized value for comparison (string or float)
    """
    if value is None:
        return ""

    # Numeric values stay as-is
    if isinstance(value, (int, float)):
        return float(value)

    # String values: remove extra whitespace, lowercase
    return " ".join(str(value).split()).lower().strip()


def evaluate_extraction(processed_json_path: Path, ground_truth_path: Path) -> dict:
    """Evaluate extraction results against ground truth.

    Args:
        processed_json_path: Path to processed JSON file
        ground_truth_path: Path to ground truth JSON file

    Returns:
        Dictionary with evaluation results
    """
    # Run extraction
    print(f"Running extraction on: {processed_json_path.name}")
    extraction_results = extract_candidates(processed_json_path)

    # Load ground truth
    print(f"Loading ground truth from: {ground_truth_path.name}\n")
    with open(ground_truth_path, 'r', encoding='utf-8') as f:
        ground_truth_data = json.load(f)

    ground_truth = ground_truth_data.get('ground_truth', {})

    # Fields to evaluate
    target_fields = ["project_address", "contractor_name", "jurisdiction", "system_size_kw"]

    # Perform comparison
    results = {
        "document_id": extraction_results.get('document_id', 'unknown'),
        "total_fields": len(target_fields),
        "exact_matches": 0,
        "field_results": []
    }

    for field_name in target_fields:
        expected_value = ground_truth.get(field_name)

        extraction = extraction_results['extractions'].get(field_name, {})
        actual_value = extraction.get('candidate_value')

        # Normalize for comparison
        expected_norm = normalize_for_comparison(expected_value)
        actual_norm = normalize_for_comparison(actual_value)

        # Check match based on field type
        if field_name == "system_size_kw":
            # Numeric field: allow small tolerance (0.01 kW)
            if isinstance(expected_norm, (int, float)) and isinstance(actual_norm, (int, float)):
                exact_match = abs(expected_norm - actual_norm) < 0.01
            else:
                exact_match = False
        else:
            # String fields: exact match after normalization
            exact_match = expected_norm == actual_norm and expected_norm != ""

        if exact_match:
            results["exact_matches"] += 1

        results["field_results"].append({
            "field_name": field_name,
            "expected": expected_value,
            "actual": actual_value,
            "exact_match": exact_match,
            "page_number": extraction.get('page_number'),
            "confidence": extraction.get('confidence', 0.0),
        })

    # Calculate accuracy
    results["accuracy"] = results["exact_matches"] / results["total_fields"] if results["total_fields"] > 0 else 0.0

    return results


def print_evaluation_results(results: dict):
    """Print evaluation results in a readable format.

    Args:
        results: Evaluation results dictionary
    """
    print("=" * 90)
    print(f"Evaluation Results for: {results['document_id']}")
    print("=" * 90)

    for field_result in results['field_results']:
        field_name = field_result['field_name']
        expected = field_result['expected']
        actual = field_result['actual']
        exact_match = field_result['exact_match']
        page = field_result['page_number']
        confidence = field_result['confidence']

        print(f"\nField: {field_name}")
        print(f"  Expected: {expected if expected else '(null)'}")
        print(f"  Actual:   {actual if actual else '(null)'}")
        print(f"  Page:     {page if page else 'N/A'}")
        print(f"  Confidence: {confidence:.2f}")
        print(f"  Match:    {'✓ YES' if exact_match else '✗ NO'}")

    print("\n" + "=" * 90)
    print(f"Summary:")
    print(f"  Total fields:   {results['total_fields']}")
    print(f"  Exact matches:  {results['exact_matches']}")
    print(f"  Accuracy:       {results['accuracy']:.1%}")
    print("=" * 90)


def main():
    """Main evaluation entrypoint."""
    if len(sys.argv) < 3:
        print("Usage: python -m src.evaluation.evaluate_extraction <processed_json> <ground_truth_json>")
        print("\nExample:")
        print("  python -m src.evaluation.evaluate_extraction \\")
        print("    data/processed/fictional_solar_permit_packet.json \\")
        print("    data/labeled/fictional_solar_permit_packet_truth.json")
        sys.exit(1)

    processed_json_path = Path(sys.argv[1])
    ground_truth_path = Path(sys.argv[2])

    # Validate inputs
    if not processed_json_path.exists():
        print(f"Error: Processed JSON not found: {processed_json_path}")
        sys.exit(1)

    if not ground_truth_path.exists():
        print(f"Error: Ground truth JSON not found: {ground_truth_path}")
        sys.exit(1)

    # Run evaluation
    results = evaluate_extraction(processed_json_path, ground_truth_path)

    # Print results
    print_evaluation_results(results)


if __name__ == "__main__":
    main()
