# Field Schema

This document defines the current extracted fields (Phase 1-2) for solar permit and SolarAPP approval document intelligence.

**Current status:**
- **Phase 1 complete**: 10 fields extracted, 6 validation rules
- **Phase 2 in progress**: Service panel fields (bus/breaker ratings) added, grid_voltage/utility_service/project_type next

**For future field planning:**
- See [ROADMAP.md](../ROADMAP.md) for phased implementation plan (Phases 2-7)
- See [field_roadmap.md](field_roadmap.md) for comprehensive field universe (~60-70 total candidate fields)

**Document types supported:**
- Permit packets (primary)
- SolarAPP approval documents (emerging, Phase 3+)

The fields below represent the **current implementation** (Phase 1-2).

## Target Fields

### project_address
- **Description**: Full street address of the solar installation site
- **Type**: `string`
- **Required**: Yes
- **Example**: "123 Main Street, San Jose, CA 95112"
- **Extraction Challenges**:
  - May appear on multiple pages
  - Can be abbreviated differently (St vs Street, etc.)
  - Sometimes split across multiple fields (address line 1, city, state, zip)

### jurisdiction
- **Description**: The city or county with permitting authority
- **Type**: `string`
- **Required**: Yes
- **Example**: "City of San Jose"
- **Extraction Challenges**:
  - Sometimes implicit (only mentioned in header/footer)
  - May need to infer from address
  - Inconsistent naming (city vs. City of vs. municipality)

### contractor_name
- **Description**: Name of the licensed solar contractor performing the installation
- **Type**: `string`
- **Required**: Yes
- **Example**: "Sunrun Inc."
- **Extraction Challenges**:
  - May be labeled as "contractor", "installer", "applicant", or "company"
  - Sometimes includes license numbers in the same field
  - Can appear in multiple locations (sometimes just a signature)

### system_size_kw
- **Description**: Total DC system size in kilowatts
- **Type**: `float`
- **Required**: Yes
- **Example**: 8.5
- **Extraction Challenges**:
  - Units may vary (kW, watts, W-DC, etc.)
  - May be written as "8.5kW" or "8500W" or "8.5 kW DC"
  - Sometimes calculated from module count × module wattage
  - Can appear on electrical diagram or permit form
- **Schema Evolution Note**: This field is ambiguous (AC or DC). Phase 5 will split this into `system_size_ac_kw` and `system_size_dc_kw`. For now, interpret as DC system size unless document clearly specifies AC.

### module_count
- **Description**: Total number of solar panels/modules
- **Type**: `integer`
- **Required**: Yes
- **Example**: 20
- **Extraction Challenges**:
  - May be in a table or equipment list
  - Sometimes stated as "(Qty: 20)"
  - Could be on site plan vs. electrical diagram

### module_model
- **Description**: Manufacturer and model number of solar panels
- **Type**: `string`
- **Required**: Yes
- **Example**: "SunPower SPR-X22-370"
- **Extraction Challenges**:
  - Inconsistent formatting (spaces, dashes, slashes)
  - May include wattage rating or may not
  - Sometimes abbreviated
  - Can be in spec sheet vs. permit form

### inverter_model
- **Description**: Manufacturer and model number of inverter(s)
- **Type**: `string` (or list if multiple inverters)
- **Required**: Yes
- **Example**: "SolarEdge SE7600H-US"
- **Extraction Challenges**:
  - Multiple inverters = multiple models
  - Microinverters vs. string inverters (affects count)
  - May include quantity in same field
  - Version/revision codes often present

### battery_present
- **Description**: Whether an energy storage system (battery) is included
- **Type**: `boolean`
- **Required**: Yes
- **Example**: true
- **Extraction Challenges**:
  - May be indicated by checkbox, text, or presence of battery model
  - Sometimes implicit (battery model listed but no explicit "yes")
  - "None" vs. blank field ambiguity

### battery_model
- **Description**: Manufacturer and model of energy storage system, if present
- **Type**: `string | null`
- **Required**: If `battery_present` is true
- **Example**: "Tesla Powerwall 2"
- **Extraction Challenges**:
  - Only applicable when battery present
  - Model names evolve (Powerwall vs Powerwall 2 vs Powerwall+)
  - Capacity may or may not be included
  - Sometimes in separate attachment

### main_bus_amp_rating
- **Description**: Amperage rating of the main service panel busbar
- **Type**: `integer`
- **Required**: Strongly recommended (Phase 2)
- **Example**: 225
- **Extraction Challenges**:
  - Units may be written as "225A", "225 amps", "225A bus"
  - May be labeled as "busbar rating", "bus bar rating", "main bus rating"
  - Sometimes on electrical diagram only
  - Can be confused with breaker ratings
- **Schema Evolution Note**: Added in Phase 2. Enables service panel validation including 120% rule (Phase 6).

### main_breaker_amp_rating
- **Description**: Amperage rating of the main service panel breaker
- **Type**: `integer`
- **Required**: Strongly recommended (Phase 2)
- **Example**: 200
- **Extraction Challenges**:
  - Units may be written as "200A", "200 amps", "200 Amp"
  - May be labeled as "main breaker", "service disconnect", "main service breaker"
  - Sometimes on electrical diagram only
  - Typically should not exceed bus rating
- **Schema Evolution Note**: Added in Phase 2. Enables service panel validation. Must be ≤ main_bus_amp_rating.

## Sample JSON Output (Phase 1-2)

```json
{
  "document_id": "permit_12345",
  "extraction_timestamp": "2026-04-27T14:30:00Z",
  "fields": {
    "project_address": "123 Main Street, San Jose, CA 95112",
    "jurisdiction": "City of San Jose",
    "contractor_name": "Sunrun Inc.",
    "system_size_kw": 8.5,
    "module_count": 20,
    "inverter_model": "SolarEdge SE7600H-US",
    "battery_present": true,
    "battery_model": "Tesla Powerwall 2",
    "main_bus_amp_rating": 225,
    "main_breaker_amp_rating": 200
  },
  "confidence_scores": {
    "project_address": 0.95,
    "jurisdiction": 0.88,
    "contractor_name": 0.92,
    "system_size_kw": 0.89,
    "module_count": 0.94,
    "inverter_model": 0.87,
    "battery_present": 1.0,
    "battery_model": 0.85,
    "main_bus_amp_rating": 0.80,
    "main_breaker_amp_rating": 0.80
  }
}
```

**Note**: This sample reflects Phase 1-2 fields. `module_model` is not yet extracted. See [field_roadmap.md](field_roadmap.md) for full field universe.

## Field Prioritization

### Phase 1-2 Status (Current)

**Extracted and validated (Phase 1 complete)**:
- project_address ✓
- contractor_name ✓
- jurisdiction ✓
- system_size_kw ✓
- module_count ✓
- inverter_model ✓
- battery_present ✓
- battery_model ✓
- main_bus_amp_rating ✓ (Phase 2)
- main_breaker_amp_rating ✓ (Phase 2)

**Next to implement (Phase 2 in progress)**:
- grid_voltage (service panel voltage)
- utility_service_rating (utility service amperage)
- project_type (residential, commercial, etc.)

**Phase 3+ (see field_roadmap.md)**:
- approval_id, ahj, scope_of_work (SolarAPP metadata)
- module_manufacturer, inverter_manufacturer (equipment completeness)
- system_size_ac_kw, system_size_dc_kw (AC/DC split, breaking change)
- Many more fields...

For complete field planning, see [field_roadmap.md](field_roadmap.md) and [ROADMAP.md](../ROADMAP.md).
