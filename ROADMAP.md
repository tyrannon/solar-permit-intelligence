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
- [x] Extract 8 fields from permit packets
- [x] Apply 5 deterministic validation rules
- [x] Evaluate against ground truth
- [x] Document failure modes

### Phase 2: Service and Interconnection Fields (Next)
Add fields that appear in both permit packets and SolarAPP documents:
- `main_bus_amp_rating`
- `main_breaker_amp_rating`
- `grid_voltage`

Add validation rules:
- `main_bus_vs_breaker_reasonable` - check 120% rule compliance
- `service_panel_adequacy` - verify panel can support PV + existing load

**Why now**: These fields appear in current permit fixtures and enable valuable electrical validation.

### Phase 3: Approval Metadata and Document Class Detection
Add SolarAPP-specific fields:
- `approval_id`
- `ahj`
- `project_type`
- `scope_of_work`

Implement document class detection:
- Identify permit packets vs. SolarAPP approval documents
- Route to appropriate extraction logic
- Tag outputs with document class

**Why next**: Unlocks ability to ingest SolarAPP documents without breaking permit packet logic.

### Phase 4: Equipment Completeness and Manufacturer Split
Add granular equipment fields:
- `module_manufacturer`
- `inverter_manufacturer`
- `racking_system_model`
- `racking_system_manufacturer`

Add validation rules:
- `module_completeness` - model + manufacturer + count all present
- `inverter_completeness` - model + manufacturer + architecture present
- `racking_completeness` - model + manufacturer present

**Why later**: Requires splitting existing fields and updating extraction logic, but adds equipment validation depth.

### Phase 5: System Size AC/DC Split
Split `system_size_kw` into:
- `system_size_ac_kw`
- `system_size_dc_kw`

Add validation rules:
- `system_size_ac_vs_dc_reasonable` - check DC/AC ratio (typically 1.1-1.4)
- `inverter_capacity_vs_ac_size` - verify inverter rating matches AC system size

**Why last**: Requires schema migration and updating all existing fixtures. High value but disruptive.

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

## Not Now

The following are deliberately out of scope until Phase 5 is complete:

- SolarAPP eligibility prediction (wait until we have multiple approval documents)
- Code constraint classification (too domain-specific, needs SME validation)
- Utility tariff analysis (separate problem domain)
- Load calculation validation (requires additional premise data)
- Structural/racking adequacy checks (requires engineering calcs)
- Permit timeline prediction (no training data)
- Automated permit generation (requires bidirectional logic)
- Multi-document reconciliation (wait for more SolarAPP samples)

These may be valuable later, but they are not the next best step.

---

## Recommended Next Implementation Step

**Implement Phase 2: Service and Interconnection Fields**

Add exactly three fields:
1. `main_bus_amp_rating`
2. `main_breaker_amp_rating`
3. `grid_voltage`

Add exactly two validation rules:
1. `main_bus_vs_breaker_reasonable` - verify 120% rule (main_breaker + pv_breaker ≤ main_bus × 1.20)
2. `service_panel_adequacy` - verify main_breaker ≥ 100A for residential, ≥ 200A for commercial (if project_type available)

**Why this next**:
- These fields appear in existing permit packet fixtures (low extraction risk)
- Enables important electrical validation (high value)
- No schema breaking changes (low disruption)
- Natural bridge to SolarAPP documents (these fields are prominent there)
- Small enough to complete in 1-2 days

**Success criteria**:
- Extract `main_bus_amp_rating` and `main_breaker_amp_rating` from 3+ fixtures
- `main_bus_vs_breaker_reasonable` rule passes on compliant permits, flags violations
- Validation output includes electrical service checks
- Existing validation rules continue to pass

This step sets up the infrastructure for SolarAPP documents without requiring them yet.

---

## Measuring Progress

**v1 complete**: 8 fields, 5 rules, permit packets only
**Phase 2 complete**: 11 fields, 7 rules, permit packets with electrical validation
**Phase 3 complete**: 15 fields, 7 rules, permit packets + SolarAPP documents
**Phase 4 complete**: 20 fields, 10 rules, equipment completeness validation
**Phase 5 complete**: 21 fields, 12 rules, AC/DC system size validation

Each phase should take 3-7 days. Do not skip phases.
