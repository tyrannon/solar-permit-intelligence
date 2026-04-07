"""Minimal candidate-field extractor for three core fields.

Searches for project_address, contractor_name, and jurisdiction in processed JSON.
Uses simple label-matching and proximity-based extraction with improved boundary detection.
"""

import json
import re
import sys
from pathlib import Path
from typing import Optional, Tuple


# Label patterns to find - just the label part, not the value capture
LABEL_PATTERNS = {
    "project_address": [
        r"project\s+address\s*:?",
        r"job\s+address\s*:?",
        r"site\s+address\s*:?",
        r"installation\s+address\s*:?",
        r"service\s+address\s*:?",
    ],
    "contractor_name": [
        r"contractor\s+name\s*:?",
        r"contractor\s*/\s*installer\s*:?",
        r"contractor\s*/\s*engineer\s*(?:name)?\s*:?",
        r"contractor\s*/\s*company\s*:?",
        r"contractor\s*:?(?!\s*license)",  # "contractor:" but not "contractor license"
        r"solar\s+contractor\s*:?",
        r"installing\s+contractor\s*:?",
    ],
    "jurisdiction": [
        r"jurisdiction\s*:?",
        r"permit\s+jurisdiction\s*:?",
        r"issuing\s+authority\s*:?",
    ],
}


# Field-specific stop labels - known downstream form fields that terminate extraction
STOP_LABELS = {
    "project_address": [
        r"permit\s+number",
        r"permit\s+#",
        r"parcel\s+number",
        r"parcel\s+#",
        r"apn",
        r"property\s+owner",
        r"owner\s+name",
        r"owner\s+phone",
        r"owner\s+email",
        r"owner\s+contact",
        r"contractor\s*/\s*installer",
        r"contractor\s+name",
        r"contractor\s+contact",
        r"applicant\s+name",
    ],
    "contractor_name": [
        r"contractor\s+contact",
        r"contractor\s+phone",
        r"contractor\s+email",
        r"license\s+number",
        r"license\s+#",
        r"license\s+class",
        r"system\s+size",
        r"system\s+summary",
        r"array\s+size",
        r"project\s+description",
    ],
    "jurisdiction": [
        r"permit\s+number",
        r"permit\s+#",
        r"project\s+address",
        r"job\s+address",
        r"parcel\s+number",
        r"parcel\s+#",
        r"property\s+owner",
        r"owner\s+name",
    ],
}


# Heuristics to identify top_level_form pages (copied from inspection utility)
TOP_LEVEL_FORM_KEYWORDS = [
    "permit application",
    "application for",
    "permit number",
    "applicant name",
    "owner name",
    "contractor license",
    "license number",
    "signature",
    "date of application",
    "phone number",
    "email address",
    "job address",
    "project address",
]


def is_top_level_form_page(text: str) -> bool:
    """Check if page is likely a top-level form page.

    Args:
        text: Page text content

    Returns:
        True if page matches top_level_form heuristics
    """
    text_lower = text.lower()
    for keyword in TOP_LEVEL_FORM_KEYWORDS:
        if keyword in text_lower:
            return True
    return False


def extract_value_after_label(page_text: str, label_end_pos: int, field_name: str) -> str:
    """Extract value text after a matched label with smart boundary detection.

    Stops at:
    - Field-specific known stop labels (form fields that follow this field)
    - Generic next label pattern (capitalized word followed by colon)
    - Double newline
    - Reasonable field-specific max length

    Args:
        page_text: Full page text
        label_end_pos: Character position where label match ends
        field_name: Name of field being extracted

    Returns:
        Raw extracted value text
    """
    remaining_text = page_text[label_end_pos:]

    # Field-specific max lengths (safety limit)
    max_lengths = {
        "project_address": 200,
        "contractor_name": 120,
        "jurisdiction": 80,
    }
    max_length = max_lengths.get(field_name, 100)

    # First, check for field-specific stop labels
    # These are known downstream form fields that should terminate extraction
    stop_patterns = STOP_LABELS.get(field_name, [])
    earliest_stop = None

    for stop_pattern in stop_patterns:
        match = re.search(stop_pattern, remaining_text, re.IGNORECASE)
        if match:
            stop_pos = match.start()
            if earliest_stop is None or stop_pos < earliest_stop:
                earliest_stop = stop_pos

    # If we found a stop label, use it
    if earliest_stop is not None:
        value = remaining_text[:earliest_stop]
    else:
        # No stop label found, look for generic next label pattern
        # Capitalized word/phrase followed by colon or #
        next_label = re.search(r'\n\s*[A-Z][A-Za-z\s/\-]+\s*[:#]', remaining_text)

        if next_label:
            value = remaining_text[:next_label.start()]
        else:
            # No clear label, use max length
            value = remaining_text[:max_length]

    # Also stop at double newline (paragraph break)
    double_newline_pos = value.find('\n\n')
    if double_newline_pos != -1:
        value = value[:double_newline_pos]

    # Trim and clean
    value = value.strip()

    # Remove any trailing label fragments
    # Sometimes PDFs have label bleeding like "1234 Main St Permit Number"
    # Check if value ends with something that looks like a label start
    for stop_pattern in stop_patterns:
        # Simple check: if the value ends with words from stop pattern, trim them
        words = re.findall(r'\b\w+\b', stop_pattern)
        if len(words) >= 2:
            # Create a pattern for the last few words
            trailing_pattern = r'\s+' + r'\s+'.join(re.escape(w) for w in words[:2]) + r'.*$'
            value = re.sub(trailing_pattern, '', value, flags=re.IGNORECASE)

    return value.strip()


def looks_like_label_or_noise(value: str) -> bool:
    """Check if extracted value looks like a label, label fragment, or noise.

    Args:
        value: Extracted value to validate

    Returns:
        True if value should be rejected
    """
    value_lower = value.lower().strip()

    # Reject label-like patterns
    label_patterns = [
        r'^permit\s*#',
        r'^license\s*#',
        r'^phone',
        r'^email',
        r'^date',
        r'^signature',
        r'^owner',
        r'^applicant',
        r'^contractor\s*$',  # Just "contractor" alone
        r'^installer\s*$',   # Just "installer" alone
        r'^\/',               # Starts with "/"
        r'^/\s*installer',    # "/ installer" fragment
        r'^/\s*engineer',     # "/ engineer" fragment
        r'^/\s*company',      # "/ company" fragment
    ]

    for pattern in label_patterns:
        if re.match(pattern, value_lower):
            return True

    # Reject if it ends with a colon (it's probably a label)
    if value.strip().endswith(':'):
        return True

    return False


def clean_extracted_value(value: str, field_name: str) -> Optional[str]:
    """Clean and validate an extracted value.

    Args:
        value: Raw extracted text
        field_name: Name of field being extracted

    Returns:
        Cleaned value or None if it appears to be blank/invalid
    """
    # Remove extra whitespace, preserve structure
    lines = [line.strip() for line in value.split('\n') if line.strip()]
    value = " ".join(lines)

    # Common blank template indicators
    blank_indicators = ["___", "________", "____________"]
    for indicator in blank_indicators:
        if indicator in value:
            return None

    # If value is too short
    if len(value) < 3:
        return None

    # If value is all underscores, dots, or colons
    if all(c in "_.: " for c in value):
        return None

    # Reject if it looks like a label or noise
    if looks_like_label_or_noise(value):
        return None

    return value


def extract_field_from_page(field_name: str, page_text: str, page_num: int, is_form_page: bool) -> dict:
    """Extract a single field from a page using pattern matching.

    Args:
        field_name: Name of field to extract
        page_text: Text content of the page
        page_num: Page number
        is_form_page: Whether this page is identified as a top-level form

    Returns:
        Dictionary with extraction results
    """
    patterns = LABEL_PATTERNS.get(field_name, [])

    for pattern in patterns:
        match = re.search(pattern, page_text, re.IGNORECASE)
        if match:
            # Found label, now extract value after it
            label_end = match.end()
            label_text = match.group(0)

            raw_value = extract_value_after_label(page_text, label_end, field_name)
            cleaned_value = clean_extracted_value(raw_value, field_name)

            if cleaned_value:
                return {
                    "field_name": field_name,
                    "page_number": page_num,
                    "matched_label": label_text,
                    "candidate_value": cleaned_value,
                    "confidence": 0.8,
                    "note": "found label and extracted value"
                }
            else:
                # Determine why it failed
                if raw_value and looks_like_label_or_noise(raw_value):
                    note = "found label but value appears to be label residue or noise"
                elif raw_value:
                    note = "found label but appears to be blank template field"
                else:
                    note = "found label but no value text after it"

                return {
                    "field_name": field_name,
                    "page_number": page_num,
                    "matched_label": label_text,
                    "candidate_value": None,
                    "confidence": 0.2,
                    "note": note
                }

    # No match found
    return {
        "field_name": field_name,
        "page_number": page_num,
        "matched_label": None,
        "candidate_value": None,
        "confidence": 0.0,
        "note": "no matching label found on this page"
    }


def extract_candidates(json_path: Path) -> dict:
    """Extract candidate field values from processed JSON.

    Args:
        json_path: Path to processed JSON file

    Returns:
        Dictionary with extraction results for all fields
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    pages = data.get('pages', [])

    # Identify top_level_form pages
    form_pages = []
    other_pages = []

    for page in pages:
        page_num = page.get('page_number')
        page_text = page.get('text', '')

        if is_top_level_form_page(page_text):
            form_pages.append((page_num, page_text, True))
        else:
            other_pages.append((page_num, page_text, False))

    # Extract fields - prefer top_level_form pages
    results = {
        "document_id": data.get('document_id', 'unknown'),
        "source_file": data.get('source_file', 'unknown'),
        "total_pages": len(pages),
        "form_pages_found": len(form_pages),
        "extractions": {}
    }

    target_fields = ["project_address", "contractor_name", "jurisdiction"]

    for field_name in target_fields:
        best_result = None

        # Jurisdiction is conservative - only search form pages
        pages_to_search = form_pages if field_name == "jurisdiction" else form_pages + other_pages

        # Try form pages first, then other pages (if allowed for this field)
        for page_num, page_text, is_form in pages_to_search:
            result = extract_field_from_page(field_name, page_text, page_num, is_form)

            # Keep the best result (highest confidence)
            if best_result is None or result['confidence'] > best_result['confidence']:
                best_result = result

            # If we found a good match, stop searching
            if result['confidence'] >= 0.8:
                break

        # If we still have no result, create a default one
        if best_result is None:
            best_result = {
                "field_name": field_name,
                "page_number": None,
                "matched_label": None,
                "candidate_value": None,
                "confidence": 0.0,
                "note": "no matching label found in document"
            }

        results["extractions"][field_name] = best_result

    return results


def main():
    """Main extraction entrypoint."""
    if len(sys.argv) < 2:
        print("Usage: python -m src.extraction.extract_candidates <path_to_processed_json>")
        sys.exit(1)

    json_path = Path(sys.argv[1])

    if not json_path.exists():
        print(f"Error: File not found: {json_path}")
        sys.exit(1)

    if not json_path.suffix.lower() == '.json':
        print(f"Error: File must be JSON: {json_path}")
        sys.exit(1)

    print(f"Extracting candidates from: {json_path.name}\n")

    results = extract_candidates(json_path)

    # Print results
    print(f"Document: {results['document_id']}")
    print(f"Total pages: {results['total_pages']}")
    print(f"Form pages identified: {results['form_pages_found']}")
    print("\n" + "=" * 90)

    for field_name, extraction in results['extractions'].items():
        print(f"\nField: {field_name}")
        print(f"  Page: {extraction['page_number']}")
        print(f"  Label: {extraction['matched_label']}")
        print(f"  Value: {extraction['candidate_value']}")
        print(f"  Confidence: {extraction['confidence']:.2f}")
        print(f"  Note: {extraction['note']}")

    print("\n" + "=" * 90)


if __name__ == "__main__":
    main()
