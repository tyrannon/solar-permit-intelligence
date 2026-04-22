"""Minimal candidate-field extractor for ten core fields.

Searches for project_address, contractor_name, jurisdiction, system_size_kw, module_count, inverter_model, battery_present, battery_model, main_bus_amp_rating, and main_breaker_amp_rating in processed JSON.
Uses simple label-matching and proximity-based extraction with improved boundary detection.
"""

import json
import re
import sys
from pathlib import Path
from typing import Optional, Tuple, Union


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
    "system_size_kw": [
        r"system\s+size\s*\(?\s*kw\s*\)?\s*:?",
        r"system\s+size\s*:?",
        r"total\s+system\s+size\s*\(?\s*kw\s*\)?\s*:?",
        r"total\s+system\s+size\s*:?",
        r"pv\s+system\s+size\s*\(?\s*kw\s*\)?\s*:?",
        r"array\s+size\s*\(?\s*kw\s*\)?\s*:?",
    ],
    "module_count": [
        r"module\s+(?:quantity|count)\s*:?",
        r"number\s+of\s+modules\s*:?",
        r"total\s+modules\s*:?",
        r"module\s+qty\s*:?",
        r"panel\s+(?:quantity|count)\s*:?",
        r"number\s+of\s+panels\s*:?",
        r"total\s+panels\s*:?",
    ],
    "inverter_model": [
        r"inverter\s+manufacturer\s*/\s*model\s*:?",
        r"inverter\s+manufacturer\s+/\s+model\s*:?",
        r"inverter\s+manufacturer\s+and\s+model\s*:?",
        r"inverter\s+model\s+number\s*:",  # Require colon for "model number"
        r"inverter\s+model\s*:",           # Require colon for standalone "model"
        r"inverter\s+manufacturer\s*:",    # Require colon for standalone "manufacturer"
    ],
    "battery_present": [
        r"battery\s+energy\s+storage\s*:?",
        r"energy\s+storage\s+system\s*:?",
        r"battery\s+storage\s*:?",
        r"battery\s+included\s*:?",
        r"battery\s*:?",
        r"ess\s*:?",
        r"battery\s+system\s*:?",
    ],
    "battery_model": [
        r"battery\s+manufacturer\s*/\s*model\s*:?",
        r"battery\s+manufacturer\s+/\s+model\s*:?",
        r"battery\s+manufacturer\s+and\s+model\s*:?",
        r"battery\s+storage\s+model\s*:?",
        r"battery\s+model\s*:",           # Require colon for standalone "battery model"
        r"battery\s+manufacturer\s*:",    # Require colon for standalone "battery manufacturer"
        r"storage\s+model\s*:",           # Require colon for standalone "storage model"
        r"ess\s+model\s*:",               # Require colon for standalone "ESS model"
        r"energy\s+storage\s+system\s+model\s*:?",
        r"battery\s+storage\s*:",         # Require colon to avoid matching narrative
        r"battery\s+energy\s+storage\s*:", # "Battery Energy Storage: Yes - Tesla Powerwall 2"
    ],
    "main_bus_amp_rating": [
        r"main\s+bus\s+amp(?:ere)?\s+rating\s*:?",
        r"main\s+bus\s+rating\s*:?",
        r"busbar\s+rating\s*:?",
        r"busbar\s+amp(?:ere)?\s+rating\s*:?",
        r"main\s+bus\s*:?",
        r"bus\s+rating\s*:?",
        r"panel\s+busbar\s+rating\s*:?",
    ],
    "main_breaker_amp_rating": [
        r"main\s+breaker\s+amp(?:ere)?\s+rating\s*:?",
        r"main\s+breaker\s+rating\s*:?",
        r"main\s+breaker\s*/\s*service\s+disconnect\s+amp(?:ere)?\s+rating\s*:?",
        r"main\s+breaker\s*:?",
        r"service\s+disconnect\s+amp(?:ere)?\s+rating\s*:?",
        r"main\s+service\s+breaker\s*:?",
        r"service\s+panel\s+main\s+breaker\s*:?",
    ],
}


# Field-specific stop labels - known downstream form fields that terminate extraction
STOP_LABELS = {
    "project_address": [
        r"permit\s+number",
        r"permit\s+#",
        r"assessor\s+parcel\s+number",  # Address-adjacent metadata
        r"parcel\s+number",
        r"parcel\s+#",
        r"apn",
        r"assessor",  # Standalone "Assessor" label
        r"parcel",    # Standalone "Parcel" label
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
        r"building\s+division",
        r"permit\s+application\s+type",
        r"application\s+type",
        r"permit\s+number",
        r"permit\s+#",
        r"project\s+address",
        r"job\s+address",
        r"parcel\s+number",
        r"parcel\s+#",
        r"property\s+owner",
        r"owner\s+name",
        r"scope\s+summary",
    ],
    "system_size_kw": [
        r"module\s+count",
        r"number\s+of\s+modules",
        r"panel\s+count",
        r"inverter",
        r"battery",
        r"utility\s+company",
        r"meter\s+number",
    ],
    "module_count": [
        r"module\s+model",
        r"module\s+type",
        r"panel\s+model",
        r"panel\s+type",
        r"module\s+manufacturer",
        r"inverter",
        r"system\s+size",
        r"wattage",
        r"watts",
    ],
    "inverter_model": [
        r"scope\s+summary",
        r"system\s+summary",
        r"number\s+of\s+inverters",
        r"inverter\s+quantity",
        r"rapid\s+shutdown",
        r"battery",
        r"main\s+service\s+panel",
        r"service\s+panel",
        r"point\s+of\s+connection",
        r"interconnection",
        r"module\s+manufacturer",
        r"module\s+model",
        r"module\s+quantity",
    ],
    "battery_present": [
        r"battery\s+model",
        r"battery\s+manufacturer",
        r"main\s+service\s+panel",
        r"service\s+panel",
        r"point\s+of\s+connection",
        r"interconnection",
        r"rapid\s+shutdown",
        r"array\s+configuration",
        r"system\s+overview",
    ],
    "battery_model": [
        r"battery\s+gateway",
        r"battery\s+inverter",
        r"battery\s+capacity",
        r"battery\s+specifications",
        r"energy\s+capacity",
        r"power\s+rating",
        r"usable\s+capacity",
        r"backup\s+gateway",
        r"racking\s+system",
        r"main\s+service\s+panel",
        r"service\s+panel",
        r"installation\s+notes",
        r"array\s+configuration",
        r"quantity",
        r"specifications",
    ],
    "main_bus_amp_rating": [
        r"main\s+breaker",
        r"pv\s+breaker",
        r"photovoltaic\s+breaker",
        r"service\s+disconnect",
        r"point\s+of\s+connection",
        r"interconnection",
        r"grounding",
        r"nominal",
        r"voltage",
        r"rapid\s+shutdown",
    ],
    "main_breaker_amp_rating": [
        r"main\s+bus",
        r"busbar",
        r"pv\s+breaker",
        r"photovoltaic\s+breaker",
        r"point\s+of\s+connection",
        r"interconnection",
        r"grounding",
        r"nominal\s+voltage",
        r"grid\s+voltage",
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
        "system_size_kw": 50,  # Numeric field, short value
        "module_count": 50,    # Integer field, short value
        "inverter_model": 100, # String field, model names can be long
        "battery_present": 150, # Boolean field, may have descriptive text
        "battery_model": 100,  # String field, battery model names
        "main_bus_amp_rating": 50,     # Integer field, short value
        "main_breaker_amp_rating": 50, # Integer field, short value
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

    # Remove trailing slashes and whitespace (common in jurisdiction fields)
    value = value.rstrip('/ \t')

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


def parse_numeric_value(value: str) -> Optional[float]:
    """Parse a numeric value from text.

    Handles formats like:
    - "7.2"
    - "7.2 kW"
    - "7.2kW"
    - "7.2 kw"

    Args:
        value: Raw text containing a number

    Returns:
        Parsed float value or None if invalid
    """
    # Remove common units and whitespace
    cleaned = value.lower().strip()
    cleaned = re.sub(r'\s*kw\s*', '', cleaned)
    cleaned = re.sub(r'\s*kilowatt[s]?\s*', '', cleaned)
    cleaned = cleaned.strip()

    # Try to extract a number (integer or decimal)
    number_match = re.search(r'(\d+\.?\d*)', cleaned)
    if number_match:
        try:
            num = float(number_match.group(1))
            # Sanity check for system size (typically 1-100 kW for residential/commercial)
            if 0.1 <= num <= 1000:
                return num
        except ValueError:
            pass

    return None


def parse_integer_value(value: str) -> Optional[int]:
    """Parse an integer value from text.

    Handles formats like:
    - "24"
    - "24 modules"
    - "24 panels"

    Rejects values that look like wattage or model numbers.

    Args:
        value: Raw text containing an integer

    Returns:
        Parsed integer value or None if invalid
    """
    cleaned = value.strip()

    # Reject if it looks like wattage (contains "w" or "watt")
    if re.search(r'\d+\s*w(?:att)?(?:s)?\b', cleaned, re.IGNORECASE):
        return None

    # Reject if it contains model-like patterns (letters mixed with numbers)
    # e.g., "ABC-400" or "Model 400W"
    if re.search(r'[a-z]\d+|[a-z]-\d+|\d+-[a-z]', cleaned, re.IGNORECASE):
        return None

    # Try to extract just the integer (first occurrence)
    number_match = re.search(r'(\d+)', cleaned)
    if number_match:
        try:
            num = int(number_match.group(1))
            # Sanity check for module count (typically 5-100 for residential, up to 500 for commercial)
            if 1 <= num <= 1000:
                return num
        except ValueError:
            pass

    return None


def parse_amperage_rating(value: str) -> Optional[int]:
    """Parse an amperage rating from text.

    Handles formats like:
    - "200"
    - "200A"
    - "200 amps"
    - "200 Amp"
    - "200 AMP"
    - "225A bus, compliant with 120%"

    Args:
        value: Raw text containing an amperage rating

    Returns:
        Parsed integer amperage value or None if invalid
    """
    # Take only the first line to avoid contamination from multi-line extraction
    first_line = value.split('\n')[0].strip()

    # Look for amperage pattern: number followed by optional "A" or "amp" unit
    # This should match before any voltage patterns (which have "V")
    amp_pattern = r'(\d+)\s*a(?:mp(?:s|ere)?(?:s)?)?(?:\s|,|;|$|\s+\w+)'
    amp_match = re.search(amp_pattern, first_line, re.IGNORECASE)

    if amp_match:
        try:
            num = int(amp_match.group(1))
            # Sanity check for amperage rating (typically 50-600 for service panels)
            # Covers residential (100A, 125A, 150A, 200A) and commercial (400A, 600A)
            if 50 <= num <= 600:
                return num
        except ValueError:
            pass

    # Fallback: look for standalone number in plausible range (if no amp units found)
    # Only use this if no voltage or wattage indicators present
    if not re.search(r'\d+\s*[vw](?:olt|att)?', first_line, re.IGNORECASE):
        # Reject if it contains model-like patterns (letters mixed with numbers)
        if not re.search(r'[a-z]\d+|[a-z]-\d+|\d+-[a-z]', first_line, re.IGNORECASE):
            number_match = re.search(r'(\d+)', first_line)
            if number_match:
                try:
                    num = int(number_match.group(1))
                    if 50 <= num <= 600:
                        return num
                except ValueError:
                    pass

    return None


def parse_boolean_value(value: str) -> Optional[bool]:
    """Parse a boolean value from text.

    Handles formats like:
    - "yes" / "no"
    - "Yes - Tesla Powerwall 2"
    - "No battery proposed"
    - "included" / "not included"
    - "no ESS"

    Returns True if battery presence is clearly indicated,
    False if battery absence is clearly indicated,
    None if ambiguous or unclear.

    Args:
        value: Raw text potentially indicating boolean state

    Returns:
        True, False, or None
    """
    cleaned = value.lower().strip()

    # Explicit "yes" patterns - battery is present
    yes_patterns = [
        r'^yes\b',
        r'\byes\b.*battery',
        r'\byes\b.*storage',
        r'\byes\b.*ess',
        r'battery.*\byes\b',          # "Battery: Yes"
        r'storage.*\byes\b',          # "Energy Storage: Yes"
        r'ess.*\byes\b',              # "ESS: Yes"
        r'battery\s+included',
        r'ess\s+included',
        r'storage\s+included',
        r'with\s+battery',
        r'includes\s+battery',
    ]

    for pattern in yes_patterns:
        if re.search(pattern, cleaned):
            return True

    # Explicit "no" patterns - battery is absent
    no_patterns = [
        r'^no\b',
        r'\bno\s+battery',
        r'\bno\s+ess',
        r'\bno\s+storage',
        r'\bno\s+energy\s+storage',
        r'battery\s+not\s+included',
        r'ess\s+not\s+included',
        r'without\s+battery',
        r'does\s+not\s+include\s+battery',
    ]

    for pattern in no_patterns:
        if re.search(pattern, cleaned):
            return False

    # If we can't determine clearly, return None
    return None


def clean_battery_model(value: str) -> str:
    """Clean battery model value by removing common prefixes and annotations.

    Args:
        value: Raw battery model text

    Returns:
        Cleaned battery model string
    """
    # Remove "Yes - " or "No - " prefix (from "Battery Storage: Yes - Tesla Powerwall 2")
    value = re.sub(r'^(?:yes|no)\s*[-–—]\s*', '', value, flags=re.IGNORECASE)

    # Remove capacity annotations in parentheses at the end
    # e.g., "(13.5 kWh)" or "(5 kW / 13.5 kWh)"
    value = re.sub(r'\s*\([^)]*k[Ww]h?[^)]*\)\s*$', '', value)

    # Remove other common annotations in parentheses at the end
    value = re.sub(r'\s*\([^)]+\)\s*$', '', value)

    return value.strip()


def clean_extracted_value(value: str, field_name: str) -> Optional[Union[str, float, int, bool]]:
    """Clean and validate an extracted value.

    Args:
        value: Raw extracted text
        field_name: Name of field being extracted

    Returns:
        Cleaned value (string, float, int, or bool depending on field) or None if invalid
    """
    # Remove extra whitespace, preserve structure
    lines = [line.strip() for line in value.split('\n') if line.strip()]
    value = " ".join(lines)

    # Common blank template indicators
    blank_indicators = ["___", "________", "____________"]
    for indicator in blank_indicators:
        if indicator in value:
            return None

    # Handle type-specific fields
    if field_name == "system_size_kw":
        return parse_numeric_value(value)

    if field_name == "module_count":
        return parse_integer_value(value)

    if field_name in ("main_bus_amp_rating", "main_breaker_amp_rating"):
        return parse_amperage_rating(value)

    if field_name == "battery_present":
        return parse_boolean_value(value)

    # Battery model cleanup
    if field_name == "battery_model":
        value = clean_battery_model(value)

    # String fields below
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
    # Special handling for battery_present - check entire page text for indicators
    if field_name == "battery_present":
        battery_value = parse_boolean_value(page_text)
        if battery_value is not None:
            return {
                "field_name": field_name,
                "page_number": page_num,
                "matched_label": "battery indicator in page text",
                "candidate_value": battery_value,
                "confidence": 0.8,
                "note": "found battery presence/absence indicator in page text"
            }
        else:
            return {
                "field_name": field_name,
                "page_number": page_num,
                "matched_label": None,
                "candidate_value": None,
                "confidence": 0.0,
                "note": "no clear battery indicator found"
            }

    patterns = LABEL_PATTERNS.get(field_name, [])

    for pattern in patterns:
        match = re.search(pattern, page_text, re.IGNORECASE)
        if match:
            # Found label, now extract value after it
            label_end = match.end()
            label_text = match.group(0)

            raw_value = extract_value_after_label(page_text, label_end, field_name)
            cleaned_value = clean_extracted_value(raw_value, field_name)

            # Check for None explicitly (not just falsy, since False is a valid boolean value)
            if cleaned_value is not None:
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

    target_fields = ["project_address", "contractor_name", "jurisdiction", "system_size_kw", "module_count", "inverter_model", "battery_present", "battery_model", "main_bus_amp_rating", "main_breaker_amp_rating"]

    for field_name in target_fields:
        best_result = None

        # Jurisdiction is conservative - only search form pages
        # System size, module count, and inverter model typically appear on form pages or summary pages
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
