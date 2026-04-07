# Validation Rules v1

This document defines the deterministic validation rules applied to extracted permit data. These rules catch logical inconsistencies and missing required information.

## Rule Definitions

### Rule 1: Required Core Fields Present

**Name**: `required_core_fields`

**Description**: Ensures that the three most critical fields are present and non-empty.

**Logic**:
- Check that `project_address` is not null/empty
- Check that `contractor_name` is not null/empty
- Check that `system_size_kw` is not null and > 0

**Behavior**:
- **PASS**: All three fields are present and valid
- **FAIL**: One or more core fields missing or invalid
- **Review Required**: N/A (hard requirement)

**Example**:
```python
if not fields.project_address or not fields.contractor_name or not fields.system_size_kw:
    return FAIL
return PASS
```

---

### Rule 2: Battery Consistency Check

**Name**: `battery_consistency`

**Description**: If a battery is marked as present, a battery model must be specified. If no battery is present, battery model should be null.

**Logic**:
- If `battery_present == True`, then `battery_model` must not be null/empty
- If `battery_present == False`, then `battery_model` should be null/empty (warning if populated)

**Behavior**:
- **PASS**: Battery status and model are consistent
- **FAIL**: Battery marked present but no model specified
- **Review Required**: Battery marked absent but model is specified (possible extraction error)

**Example**:
```python
if fields.battery_present and not fields.battery_model:
    return FAIL
if not fields.battery_present and fields.battery_model:
    return REVIEW_REQUIRED
return PASS
```

---

### Rule 3: System Size Reasonableness

**Name**: `system_size_range`

**Description**: System size should fall within typical residential ranges (2-20 kW for residential installs).

**Logic**:
- Check if `system_size_kw` is between 2.0 and 20.0
- Flag for review if outside this range (may be legitimate but unusual)

**Behavior**:
- **PASS**: System size between 2 and 20 kW
- **FAIL**: N/A (no hard limit)
- **Review Required**: System size < 2 kW or > 20 kW (possibly commercial or data error)

**Example**:
```python
if fields.system_size_kw < 2.0 or fields.system_size_kw > 20.0:
    return REVIEW_REQUIRED
return PASS
```

---

### Rule 4: Module Count and System Size Correlation

**Name**: `module_system_correlation`

**Description**: If both module count and system size are present, verify they're roughly consistent (assuming typical module wattages of 300-450W).

**Logic**:
- Calculate expected system size range: `module_count × 0.3` to `module_count × 0.45` kW
- Check if `system_size_kw` falls within this range

**Behavior**:
- **PASS**: System size consistent with module count
- **FAIL**: N/A (different module wattages possible)
- **Review Required**: System size inconsistent with module count (possible extraction error or unusual modules)

**Example**:
```python
if fields.module_count and fields.system_size_kw:
    expected_min = fields.module_count * 0.3
    expected_max = fields.module_count * 0.45
    if not (expected_min <= fields.system_size_kw <= expected_max):
        return REVIEW_REQUIRED
return PASS
```

---

### Rule 5: Service Panel Rating Adequacy

**Name**: `service_panel_adequate`

**Description**: If main service panel rating is present, it should be at least 100A (minimum for solar in most jurisdictions).

**Logic**:
- If `main_service_panel_rating` is present, check if >= 100

**Behavior**:
- **PASS**: Panel rating >= 100A or not specified
- **FAIL**: N/A
- **Review Required**: Panel rating < 100A (unusual, possible error)

**Example**:
```python
if fields.main_service_panel_rating and fields.main_service_panel_rating < 100:
    return REVIEW_REQUIRED
return PASS
```

---

### Rule 6: Equipment Models Specified

**Name**: `equipment_models_present`

**Description**: Critical equipment models should be specified for permitting.

**Logic**:
- Check that `module_model` is not null/empty
- Check that `inverter_model` is not null/empty

**Behavior**:
- **PASS**: Both models specified
- **FAIL**: One or both models missing
- **Review Required**: N/A

**Example**:
```python
if not fields.module_model or not fields.inverter_model:
    return FAIL
return PASS
```

---

### Rule 7: Address Format Validation

**Name**: `address_format_check`

**Description**: Project address should contain basic components (street number, street name, and state).

**Logic**:
- Check for presence of digits (street number)
- Check for presence of state abbreviation or "CA", "California" etc.
- Minimum length check (> 15 characters for reasonable address)

**Behavior**:
- **PASS**: Address appears well-formed
- **FAIL**: N/A
- **Review Required**: Address appears incomplete or malformed

**Example**:
```python
address = fields.project_address
if not address or len(address) < 15 or not any(char.isdigit() for char in address):
    return REVIEW_REQUIRED
return PASS
```

---

### Rule 8: Jurisdiction Specified

**Name**: `jurisdiction_present`

**Description**: Jurisdiction should be identified (may be critical for compliance).

**Logic**:
- Check that `jurisdiction` is not null/empty

**Behavior**:
- **PASS**: Jurisdiction specified
- **FAIL**: Jurisdiction missing (may need manual lookup)
- **Review Required**: N/A

**Example**:
```python
if not fields.jurisdiction:
    return FAIL
return PASS
```

---

## Rule Processing Order

Rules should be processed in this order:
1. `required_core_fields` (exit early if fails)
2. `equipment_models_present`
3. `jurisdiction_present`
4. `battery_consistency`
5. `system_size_range`
6. `module_system_correlation`
7. `service_panel_adequate`
8. `address_format_check`

## Rule Result Schema

Each rule produces a result with:
- `rule_name`: Identifier
- `status`: "PASS" | "FAIL" | "REVIEW_REQUIRED"
- `message`: Human-readable explanation
- `severity`: "critical" | "warning" | "info"

Example:
```json
{
  "rule_name": "battery_consistency",
  "status": "FAIL",
  "message": "Battery marked as present but no battery model specified",
  "severity": "critical"
}
```

## Notes

- Rules are intentionally simple and deterministic for v1
- More sophisticated validation (ML-based anomaly detection, cross-document consistency) is out of scope
- Rules should be easy to modify as we learn from real data
- Consider making thresholds configurable in v2
