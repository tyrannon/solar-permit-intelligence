# Field Schema

This document defines the target fields for v1 extraction. These fields represent the minimum viable set of information needed to validate a solar permit application.

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

### main_service_panel_rating
- **Description**: Amperage rating of the home's main electrical panel
- **Type**: `integer`
- **Required**: Strongly recommended
- **Example**: 200
- **Extraction Challenges**:
  - Units may be written as "200A", "200 amps", "200 Amp"
  - May be abbreviated as "MSP" or "Main Panel"
  - Sometimes on electrical diagram only
  - Can be confused with sub-panel ratings

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

## Sample JSON Output

```json
{
  "document_id": "permit_12345",
  "extraction_timestamp": "2026-04-07T14:30:00Z",
  "fields": {
    "project_address": "123 Main Street, San Jose, CA 95112",
    "jurisdiction": "City of San Jose",
    "contractor_name": "Sunrun Inc.",
    "system_size_kw": 8.5,
    "module_count": 20,
    "module_model": "SunPower SPR-X22-370",
    "inverter_model": "SolarEdge SE7600H-US",
    "main_service_panel_rating": 200,
    "battery_present": true,
    "battery_model": "Tesla Powerwall 2"
  },
  "confidence_scores": {
    "project_address": 0.95,
    "jurisdiction": 0.88,
    "contractor_name": 0.92,
    "system_size_kw": 0.89,
    "module_count": 0.94,
    "module_model": 0.91,
    "inverter_model": 0.87,
    "main_service_panel_rating": 0.78,
    "battery_present": 1.0,
    "battery_model": 0.85
  }
}
```

## Field Prioritization for v1

**Must extract (pipeline fails without these)**:
- project_address
- contractor_name
- system_size_kw

**Should extract (warnings if missing)**:
- module_count
- module_model
- inverter_model
- battery_present

**Nice to have (log if missing but don't fail)**:
- jurisdiction
- main_service_panel_rating
- battery_model (if battery_present)

This prioritization helps focus initial extraction efforts on the most critical and most commonly present fields.
