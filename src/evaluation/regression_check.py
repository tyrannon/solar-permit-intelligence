"""Simple regression check utility for all labeled fixtures.

Runs extraction and evaluation across all labeled fixtures and prints a compact summary.
"""

import sys
from pathlib import Path
from io import StringIO
from contextlib import redirect_stdout

# Import evaluation function
from src.evaluation.evaluate_extraction import evaluate_extraction


def find_fixtures():
    """Find all labeled truth files and their corresponding processed files.

    Returns:
        List of tuples: (fixture_name, processed_path, truth_path)
    """
    labeled_dir = Path("data/labeled")
    processed_dir = Path("data/processed")

    fixtures = []

    # Find all truth files
    for truth_file in sorted(labeled_dir.glob("*_truth.json")):
        # Extract fixture name by removing _truth.json suffix
        fixture_name = truth_file.stem.replace("_truth", "")

        # Find corresponding processed file
        processed_file = processed_dir / f"{fixture_name}.json"

        if processed_file.exists():
            fixtures.append((fixture_name, processed_file, truth_file))
        else:
            print(f"Warning: No processed file found for {fixture_name}", file=sys.stderr)

    return fixtures


def run_regression_check():
    """Run regression check on all fixtures and print summary."""

    fixtures = find_fixtures()

    if not fixtures:
        print("No fixtures found for regression check.")
        return 1

    print("=" * 90)
    print("REGRESSION CHECK - Field Extraction Accuracy")
    print("=" * 90)
    print()

    # Table header
    print(f"{'Fixture':<45} {'Fields':<10} {'Matches':<10} {'Accuracy':<10}")
    print("-" * 90)

    total_fields = 0
    total_matches = 0
    all_results = []

    # Run evaluation on each fixture
    for fixture_name, processed_path, truth_path in fixtures:
        try:
            # Suppress extraction progress output
            with redirect_stdout(StringIO()):
                results = evaluate_extraction(processed_path, truth_path)

            fields = results['total_fields']
            matches = results['exact_matches']
            accuracy = results['accuracy']

            total_fields += fields
            total_matches += matches
            all_results.append((fixture_name, fields, matches, accuracy))

            # Print row
            print(f"{fixture_name:<45} {fields:<10} {matches:<10} {accuracy:>8.1%}")

        except Exception as e:
            print(f"{fixture_name:<45} ERROR: {str(e)}")

    # Overall summary
    print("-" * 90)
    overall_accuracy = total_matches / total_fields if total_fields > 0 else 0.0
    print(f"{'OVERALL':<45} {total_fields:<10} {total_matches:<10} {overall_accuracy:>8.1%}")
    print("=" * 90)
    print()

    # Return exit code based on results
    if overall_accuracy < 1.0:
        print(f"⚠ Warning: Overall accuracy is {overall_accuracy:.1%} (not 100%)")
        return 1
    else:
        print(f"✓ All fixtures passing at 100% accuracy")
        return 0


def main():
    """Main entrypoint for regression check."""
    exit_code = run_regression_check()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
