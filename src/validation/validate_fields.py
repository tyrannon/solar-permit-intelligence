"""Simple deterministic validation rules for extracted permit fields.

Implements basic consistency checks for solar permit data.
No framework abstractions - just straightforward validation functions.
"""

from typing import Optional, Dict, Any


# Rule status constants
PASS = "PASS"
FAIL = "FAIL"
REVIEW_REQUIRED = "REVIEW_REQUIRED"


def validate_battery_requires_battery_model(
    battery_present: Optional[bool],
    battery_model: Optional[str]
) -> tuple[str, str]:
    """Check that battery systems have a specified battery model.

    Logic:
    - If battery_present is True and battery_model is null/empty → FAIL
    - If battery_present is False → PASS (no battery, no model needed)
    - If battery_present is null/ambiguous → REVIEW_REQUIRED

    Args:
        battery_present: Whether battery is present (True/False/None)
        battery_model: Battery model string (or None)

    Returns:
        Tuple of (status, explanation)
    """
    # Ambiguous battery presence - needs review
    if battery_present is None:
        return (
            REVIEW_REQUIRED,
            "Battery presence unclear - cannot validate model requirement"
        )

    # No battery present - rule passes
    if battery_present is False:
        return (
            PASS,
            "No battery present - model not required"
        )

    # Battery present - model should be specified
    if battery_present is True:
        if battery_model is None or str(battery_model).strip() == "":
            return (
                FAIL,
                "Battery is present but battery_model is not specified"
            )
        else:
            return (
                PASS,
                f"Battery present with model: {battery_model}"
            )

    # Fallback (should not reach here)
    return (
        REVIEW_REQUIRED,
        f"Unexpected battery_present value: {battery_present}"
    )


def validate_battery_model_requires_battery_present(
    battery_model: Optional[str],
    battery_present: Optional[bool]
) -> tuple[str, str]:
    """Check that if a battery model is specified, battery is marked as present.

    Logic:
    - If battery_model is missing/null/empty → PASS (no model to validate)
    - If battery_model is present and battery_present is True → PASS
    - If battery_model is present and battery_present is False → REVIEW_REQUIRED
    - If battery_model is present and battery_present is null → REVIEW_REQUIRED

    Args:
        battery_model: Battery model string (or None)
        battery_present: Whether battery is present (True/False/None)

    Returns:
        Tuple of (status, explanation)
    """
    # No battery model specified - rule does not apply
    if battery_model is None or str(battery_model).strip() == "":
        return (
            PASS,
            "No battery model specified - rule does not apply"
        )

    # Battery model is specified - check battery_present consistency
    if battery_present is True:
        return (
            PASS,
            f"Battery model '{battery_model}' is consistent with battery_present=True"
        )

    if battery_present is False:
        return (
            REVIEW_REQUIRED,
            f"Battery model '{battery_model}' specified but battery_present=False (inconsistent)"
        )

    # battery_present is None/unclear
    return (
        REVIEW_REQUIRED,
        f"Battery model '{battery_model}' specified but battery_present is unclear"
    )


def validate_module_count_vs_system_size_reasonable(
    module_count: Optional[int],
    system_size_kw: Optional[float]
) -> tuple[str, str]:
    """Check if module count and system size imply reasonable watts per module.

    Logic:
    - Calculate implied watts per module: (system_size_kw * 1000) / module_count
    - Plausible range: 250W to 700W per module
    - If outside range → FAIL
    - If either field is missing → REVIEW_REQUIRED

    Args:
        module_count: Number of modules (or None)
        system_size_kw: System size in kW DC (or None)

    Returns:
        Tuple of (status, explanation)
    """
    # Missing data - needs review
    if module_count is None:
        return (
            REVIEW_REQUIRED,
            "module_count not available - cannot validate sizing"
        )

    if system_size_kw is None:
        return (
            REVIEW_REQUIRED,
            "system_size_kw not available - cannot validate sizing"
        )

    # Both fields present - calculate implied watts per module
    if module_count <= 0:
        return (
            FAIL,
            f"Invalid module_count: {module_count} (must be positive)"
        )

    if system_size_kw <= 0:
        return (
            FAIL,
            f"Invalid system_size_kw: {system_size_kw} (must be positive)"
        )

    # Calculate watts per module
    watts_per_module = (system_size_kw * 1000) / module_count

    # Check plausible range (250W to 700W)
    MIN_WATTS = 250
    MAX_WATTS = 700

    if watts_per_module < MIN_WATTS:
        return (
            FAIL,
            f"Implied {watts_per_module:.0f}W per module is below plausible minimum ({MIN_WATTS}W)"
        )

    if watts_per_module > MAX_WATTS:
        return (
            FAIL,
            f"Implied {watts_per_module:.0f}W per module exceeds plausible maximum ({MAX_WATTS}W)"
        )

    # Within plausible range
    return (
        PASS,
        f"Implied {watts_per_module:.0f}W per module is within plausible range ({MIN_WATTS}-{MAX_WATTS}W)"
    )


def validate_inverter_model_required(
    inverter_model: Optional[str]
) -> tuple[str, str]:
    """Check that inverter model is specified.

    Logic:
    - If inverter_model is present and non-empty → PASS
    - If inverter_model is missing, null, or empty → REVIEW_REQUIRED

    Args:
        inverter_model: Inverter model string (or None)

    Returns:
        Tuple of (status, explanation)
    """
    # Missing or empty inverter model - needs review
    if inverter_model is None or str(inverter_model).strip() == "":
        return (
            REVIEW_REQUIRED,
            "Inverter model not specified"
        )

    # Inverter model present
    return (
        PASS,
        f"Inverter model specified: {inverter_model}"
    )


def validate_required_core_fields_present(
    project_address: Optional[str],
    contractor_name: Optional[str],
    jurisdiction: Optional[str],
    system_size_kw: Optional[float],
    inverter_model: Optional[str]
) -> tuple[str, str]:
    """Check that all required core fields are present and non-empty.

    Logic:
    - Check five core fields: project_address, contractor_name, jurisdiction,
      system_size_kw, inverter_model
    - If all are present and non-empty → PASS
    - If one or more are missing/null/empty → REVIEW_REQUIRED

    Args:
        project_address: Project address string (or None)
        contractor_name: Contractor name string (or None)
        jurisdiction: Jurisdiction string (or None)
        system_size_kw: System size in kW DC (or None)
        inverter_model: Inverter model string (or None)

    Returns:
        Tuple of (status, explanation)
    """
    missing_fields = []

    # Check each core field
    if project_address is None or str(project_address).strip() == "":
        missing_fields.append("project_address")

    if contractor_name is None or str(contractor_name).strip() == "":
        missing_fields.append("contractor_name")

    if jurisdiction is None or str(jurisdiction).strip() == "":
        missing_fields.append("jurisdiction")

    if system_size_kw is None:
        missing_fields.append("system_size_kw")

    if inverter_model is None or str(inverter_model).strip() == "":
        missing_fields.append("inverter_model")

    # If any fields are missing - needs review
    if missing_fields:
        missing_str = ", ".join(missing_fields)
        return (
            REVIEW_REQUIRED,
            f"Missing core fields: {missing_str}"
        )

    # All core fields present
    return (
        PASS,
        "All core fields present"
    )


def run_all_validations(extractions: Dict[str, Any]) -> Dict[str, tuple[str, str]]:
    """Run all validation rules on extracted field data.

    Args:
        extractions: Dictionary of extracted field values
                    (from extract_candidates output)

    Returns:
        Dictionary mapping rule name to (status, explanation) tuples
    """
    results = {}

    # Extract field values from extractions dict
    project_address = extractions.get('project_address', {}).get('candidate_value')
    contractor_name = extractions.get('contractor_name', {}).get('candidate_value')
    jurisdiction = extractions.get('jurisdiction', {}).get('candidate_value')
    battery_present = extractions.get('battery_present', {}).get('candidate_value')
    battery_model = extractions.get('battery_model', {}).get('candidate_value')
    module_count = extractions.get('module_count', {}).get('candidate_value')
    system_size_kw = extractions.get('system_size_kw', {}).get('candidate_value')
    inverter_model = extractions.get('inverter_model', {}).get('candidate_value')

    # Run each rule
    results['required_core_fields_present'] = validate_required_core_fields_present(
        project_address, contractor_name, jurisdiction, system_size_kw, inverter_model
    )

    results['battery_requires_battery_model'] = validate_battery_requires_battery_model(
        battery_present, battery_model
    )

    results['battery_model_requires_battery_present'] = validate_battery_model_requires_battery_present(
        battery_model, battery_present
    )

    results['module_count_vs_system_size_reasonable'] = validate_module_count_vs_system_size_reasonable(
        module_count, system_size_kw
    )

    results['inverter_model_required'] = validate_inverter_model_required(
        inverter_model
    )

    return results


def print_validation_results(results: Dict[str, tuple[str, str]], document_id: str = "unknown"):
    """Print validation results in human-readable format.

    Args:
        results: Dictionary mapping rule name to (status, explanation) tuples
        document_id: Document identifier for display
    """
    print("=" * 90)
    print(f"VALIDATION RESULTS - {document_id}")
    print("=" * 90)
    print()

    # Count statuses
    pass_count = sum(1 for status, _ in results.values() if status == PASS)
    fail_count = sum(1 for status, _ in results.values() if status == FAIL)
    review_count = sum(1 for status, _ in results.values() if status == REVIEW_REQUIRED)

    # Print each rule result
    for rule_name, (status, explanation) in results.items():
        status_symbol = "✓" if status == PASS else "✗" if status == FAIL else "⚠"
        print(f"{status_symbol} {status:<20} {rule_name}")
        print(f"  → {explanation}")
        print()

    # Summary
    print("-" * 90)
    print(f"Summary: {pass_count} PASS, {fail_count} FAIL, {review_count} REVIEW_REQUIRED")
    print("=" * 90)
