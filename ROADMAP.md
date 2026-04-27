# Project Roadmap

## Roadmap Shift: Permit Packets + SolarAPP Approval Intelligence

**Original scope**: Extract and validate data from solar permit application packets.

**Evolved scope**: Extract and validate data from two document classes:
1. **Permit/application packets** (what we have now)
2. **SolarAPP-style approval/checklist documents** (newly identified)

This is not a redesign. This is a roadmap adjustment based on a real-world document class that unlocks additional value.

---

## Why SolarAPP Approval Documents Matter

SolarAPP+ (Solar Automated Permit Processing) generates structured approval and inspection checklists. These documents:
- Are more normalized than permit packets (standardized review outputs)
- Contain enriched metadata (approval IDs, AHJ identifiers, eligibility flags)
- Include electrical service detail that permit packets may omit or scatter
- Represent post-review truth (approved values vs. applicant-submitted values)
- Unlock validation logic that compares applicant data to approved data

**Business value**: If we can extract both permit packets and approval checklists, we can:
- Validate that submitted permits match approved plans
- Flag discrepancies between application and approval
- Build approval-readiness checks for new permits
- Extract service/interconnection details for more robust validation

---

## Field Families Unlocked by SolarAPP Documents

### Approval Metadata
- `approval_id` - unique approval identifier
- `ahj` - Authority Having Jurisdiction (may differ from jurisdiction field)
- `project_type` - residential, commercial, ground-mount, etc.
- `scope_of_work` - narrative or classification of what was approved

### Electrical Service and Interconnection
- `main_bus_amp_rating` - busbar rating (e.g., 225A)
- `main_breaker_amp_rating` - main breaker size (e.g., 200A)
- `utility_service_rating` - utility service size (may differ from panel rating)
- `grid_voltage` - nominal grid voltage (e.g., 120/240V, 208V, 480V)

### Equipment Detail (More Granular Than v1)
- `module_model` - already extracted, but approval docs may normalize it
- `module_manufacturer` - split from model (e.g., "LONGi" vs. "LONGi LR5-72HBD-550M")
- `inverter_architecture` - string, micro, hybrid, etc.
- `racking_system_model` - specific racking product
- `racking_system_manufacturer` - racking vendor

### System Size Split
- `system_size_ac_kw` - AC system size (inverter capacity)
- `system_size_dc_kw` - DC system size (array capacity)

Current `system_size_kw` is ambiguous (AC or DC). SolarAPP documents often include both.

---

## Phased Implementation Roadmap

### Phase 1: Current State (Complete)
- [x] Extract 10 fields from permit packets
- [x] Apply 6 deterministic validation rules
- [x] Evaluate against ground truth
- [x] Document failure modes

**Extracted fields:**
- project_address, contractor_name, jurisdiction
- system_size_kw, module_count, inverter_model
- battery_present, battery_model
- main_bus_amp_rating, main_breaker_amp_rating

**Validation rules:**
- required_core_fields_present
- battery_requires_battery_model, battery_model_requires_battery_present
- module_count_vs_system_size_reasonable
- inverter_model_required
- main_bus_vs_breaker_reasonable

### Phase 2: Service Panel Detail (In Progress)
Add remaining service panel fields:
- `grid_voltage` (string) - e.g., "120/240V 1-phase", "208V 3-phase"
- `utility_service_rating` (int) - utility service amperage
- `project_type` (enum) - residential, commercial, ground_mount, etc.

Add validation rules:
- `grid_voltage_format_reasonable` - validates voltage format
- `utility_service_vs_panel_reasonable` - utility_service ≥ main_breaker
- Update existing rules to use `project_type` for type-based thresholds

**Why now**:
- Completes service panel field family
- `project_type` unlocks type-based validation (residential vs commercial thresholds)
- Sets up SolarAPP metadata phase
- All fields are additive (no breaking changes)

**Estimated effort**: 2-4 days

### Phase 3: Approval Metadata and Document Class Detection
Add SolarAPP-specific fields:
- `approval_id` (string) - unique approval identifier
- `ahj` (string) - Authority Having Jurisdiction (more normalized than jurisdiction)
- `scope_of_work` (string) - narrative description of approved work
- `document_class` (enum) - permit_packet, solarapp_approval (internal metadata)

Note: `project_type` moved to Phase 2 (unlocks immediate validation value)

Implement document class detection:
- Identify permit packets vs. SolarAPP approval documents
- Route to appropriate extraction logic based on document class
- Tag outputs with document class for downstream processing

Add validation:
- Document class routing (not a validation rule, but enables different extraction paths)
- `project_type_influences_thresholds` - use project_type to adjust validation ranges

**Why next**:
- Enables SolarAPP document support
- `document_class` enables routing without breaking permit packet logic
- `ahj` is more normalized than `jurisdiction` for SolarAPP documents
- Sets up equipment completeness phase

**Estimated effort**: 3-5 days

### Phase 4: Equipment Completeness and Manufacturer Split
Add granular equipment fields:
- `module_model` (string) - if not already extracted
- `module_manufacturer` (string) - split from model
- `module_wattage` (int) - rated wattage per module (e.g., 440W)
- `inverter_manufacturer` (string) - split from model
- `inverter_architecture` (enum) - string, micro, central, hybrid
- `battery_manufacturer` (string) - split from model
- `racking_system_model` (string) - racking product model
- `racking_system_manufacturer` (string) - racking vendor

Add validation rules:
- `module_completeness` - model + manufacturer + count all present
- `inverter_completeness` - model + manufacturer + architecture present
- `battery_completeness` - if battery_present, then model + manufacturer present
- `racking_completeness` - model + manufacturer present
- `module_wattage_vs_system_size_reasonable` - module_count × module_wattage ≈ system_size_kw × 1000

**Why this order**:
- After SolarAPP metadata (document_class helps route manufacturer extraction)
- Before AC/DC split (module_wattage needs to know which system_size to compare against)
- Equipment completeness is high-value permit review check
- SolarAPP documents have normalized manufacturer fields

**Estimated effort**: 5-7 days

### Phase 5: System Size AC/DC Split (BREAKING CHANGE)
Split `system_size_kw` into:
- `system_size_ac_kw` (float) - AC system size (inverter capacity)
- `system_size_dc_kw` (float) - DC system size (array capacity)

Deprecate:
- `system_size_kw` (aliased to `system_size_dc_kw` during transition)

Add validation rules:
- `system_size_ac_vs_dc_reasonable` - DC/AC ratio typically 1.1-1.4
- `inverter_capacity_vs_ac_size` - inverter_rated_output_kw ≈ system_size_ac_kw
- Update `module_count_vs_system_size_reasonable` to use `system_size_dc_kw`

**Migration path**:
1. Add new fields alongside old field
2. Update all truth fixtures to include both fields
3. Update extraction logic to populate both when possible
4. Update validation logic to use new fields
5. Mark `system_size_kw` as deprecated in docs
6. Remove `system_size_kw` in Phase 6

**Why this order**:
- After equipment completeness (so we have module_wattage and inverter data)
- Disruptive change, do it when other fields are stable
- SolarAPP documents explicitly separate AC/DC
- Resolves long-standing ambiguity

**Estimated effort**: 3-5 days (migration work)

### Phase 6: Interconnection Detail and 120% Rule
Add interconnection fields:
- `pv_breaker_amp_rating` (int) - PV system breaker size
- `interconnection_method` (enum) - load_side, supply_side, line_side_tap

Add validation rules:
- `120_percent_rule_compliant` - main_bus × 1.20 ≥ main_breaker + pv_breaker
- `pv_breaker_vs_system_size_reasonable` - pv_breaker sized appropriately for system
- Remove deprecated `system_size_kw` field

**Why this order**:
- After AC/DC split (so we have accurate system_size_ac_kw for breaker sizing)
- After equipment completeness (so inverter capacity is known)
- 120% rule is critical electrical validation
- Completes service panel field family

**Estimated effort**: 3-4 days

### Phase 7+: Future Enhancements (Not Prioritized)
**Candidate fields:**
- Battery capacity (`battery_capacity_kwh`, `battery_power_rating_kw`)
- Contractor licensing (`contractor_license`, `contractor_license_class`)
- Structural/roof detail (`roof_pitch`, `roof_material`, detailed racking)
- Fire/rapid shutdown (`rapid_shutdown_method`, setback compliance)
- Inspection metadata (`inspector_name`, `inspection_date`)
- List-based equipment structures (if needed for complex systems)

**Why later**:
- Lower validation ROI than earlier phases
- More complex extraction logic
- Niche use cases
- Nice-to-have, not must-have

See `docs/field_roadmap.md` for comprehensive field universe and long-term planning.

---

## Schema Implications

### Required Changes for Phase 2
- Add `main_bus_amp_rating: Optional[int]`
- Add `main_breaker_amp_rating: Optional[int]`
- Add `grid_voltage: Optional[str]` (e.g., "120/240V", "208V 3-phase")

No breaking changes to existing fields.

### Required Changes for Phase 3
- Add `approval_id: Optional[str]`
- Add `ahj: Optional[str]`
- Add `project_type: Optional[str]`
- Add `scope_of_work: Optional[str]`
- Add `document_class: str` (e.g., "permit_packet", "solarapp_approval")

No breaking changes to existing fields.

### Required Changes for Phase 4
- Add `module_manufacturer: Optional[str]`
- Add `inverter_manufacturer: Optional[str]`
- Add `inverter_architecture: Optional[str]`
- Add `racking_system_model: Optional[str]`
- Add `racking_system_manufacturer: Optional[str]`

Existing `module_model` and `inverter_model` remain for backward compatibility.

### Required Changes for Phase 5 (Breaking)
- Deprecate `system_size_kw`
- Add `system_size_ac_kw: Optional[float]`
- Add `system_size_dc_kw: Optional[float]`

**Migration path**: Keep `system_size_kw` as alias to `system_size_dc_kw` during transition.

---

## Not Now: Scope Discipline

The following are deliberately out of scope until Phase 6+ is complete:

### Deferred to Phase 8+

**Detailed Owner/Applicant Info**
- Fields: property_owner_name, applicant_name, contractor_contact_phone, contractor_contact_email
- Why not yet: PII concerns, low validation value, names don't affect permit correctness

**SolarAPP Eligibility Prediction**
- Fields: solarapp_eligible (calculated), code_constraints (list), eligibility_score
- Why not yet: Requires deep SolarAPP domain logic, jurisdiction-specific rules, need 20+ SolarAPP samples

**Load Calculations and Demand Analysis**
- Fields: existing_load_kw, proposed_load_kw, load_calculation_method, demand_factor
- Why not yet: Complex electrical engineering, requires NEC Article 220 engine, hard to extract from worksheets

**Detailed Fire Code Compliance**
- Fields: setback_compliant, pathway_width_ft, ridge_setback_ft, labeling_compliant
- Why not yet: Fire code varies by jurisdiction, hard to validate without jurisdiction-specific rules

**Detailed Structural Calculations**
- Fields: dead_load_psf, live_load_psf, wind_load_psf, seismic_zone, structural_adequacy_verified
- Why not yet: Requires engineering domain knowledge, low ROI, often requires PE stamp

**Installation / Construction Tracking**
- Fields: installation_start_date, installation_completion_date, installer_crew_size, inspection_date
- Why not yet: Post-permit workflow, dates are hard to extract reliably, low value for permit review

**Multi-Document Reconciliation**
- Fields: permit_vs_approval_discrepancies, design_vs_asbuilt_changes
- Why not yet: Requires comparing multiple documents, need bidirectional diff logic, low ROI until multi-doc workflow established

### Never / Different Product Domain

**Financial / Incentive Fields**
- Fields: system_cost, rebate_amount, tax_credit_eligible, financing_type
- Why never: Out of scope for permit review, different business workflow

**Production Estimates and Performance**
- Fields: annual_production_estimate_kwh, shading_analysis_attached, azimuth, tilt_angle
- Why never: Not permit requirements, separate product (design review vs permit review)

**Warranty and Maintenance Info**
- Fields: module_warranty_years, inverter_warranty_years, workmanship_warranty_years, monitoring_system
- Why never: Not permit requirements, separate business workflow (sales/service)

These may be valuable in different contexts, but they are not permit review automation priorities.

---

## Recommended Next Implementation Step

**Complete Phase 2: Service Panel Detail**

Add exactly three fields:
1. `grid_voltage` (string) - e.g., "120/240V 1-phase", "208V 3-phase"
2. `utility_service_rating` (int) - utility service amperage
3. `project_type` (enum) - residential, commercial, ground_mount, carport, agricultural

Add validation rules:
1. `grid_voltage_format_reasonable` - validates voltage format (rejects nonsense like "999V")
2. `utility_service_vs_panel_reasonable` - utility_service_rating ≥ main_breaker_amp_rating
3. Update existing rules to use `project_type` for type-based thresholds (e.g., residential vs commercial panel sizing)

**Current Phase 2 progress**:
- [x] `main_bus_amp_rating` - extracted and validated
- [x] `main_breaker_amp_rating` - extracted and validated
- [x] `main_bus_vs_breaker_reasonable` - validation rule implemented
- [ ] `grid_voltage` - not yet implemented
- [ ] `utility_service_rating` - not yet implemented
- [ ] `project_type` - not yet implemented

**Why these three fields next**:
- Completes Phase 2 (service panel detail)
- All three are additive (no breaking changes)
- `grid_voltage` and `utility_service_rating` appear in SolarAPP approvals (sets up Phase 3)
- `project_type` unlocks type-based validation improvements immediately
- Natural progression: electrical service → project context

**Extraction approach**:
- `grid_voltage`: Look for patterns like `\d+/?\d*\s*V\s*(?:1-phase|3-phase)?`
- `utility_service_rating`: Similar to breaker/bus extraction, look for "utility service", "service rating"
- `project_type`: Look for keywords "residential", "commercial", "ground mount", normalize to enum

**Success criteria**:
- Extract all three fields from 2+ fixtures
- Grid voltage validates format (passes "120/240V", fails "999V")
- Utility service rating compared to main breaker (flags if utility < breaker)
- Project type enables threshold adjustments in existing rules
- All existing validation rules continue to pass

**Estimated effort**: 2-4 days

This completes Phase 2 and sets up Phase 3 (SolarAPP metadata).

---

## Measuring Progress

**Phase 1 complete** ✓: 10 fields, 6 rules, permit packets only
**Phase 2 complete**: 13 fields, 9 rules, permit packets with service panel validation
**Phase 3 complete**: 17 fields, 10 rules, permit packets + SolarAPP documents
**Phase 4 complete**: 25 fields, 14 rules, equipment completeness validation
**Phase 5 complete**: 26 fields, 16 rules, AC/DC system size validation (breaking change)
**Phase 6 complete**: 28 fields, 18 rules, 120% rule and full interconnection validation
**Phase 7+**: Additional fields as needed, no breaking changes expected

Each phase should take 2-7 days. Do not skip phases.

For comprehensive field planning, see `docs/field_roadmap.md`.
