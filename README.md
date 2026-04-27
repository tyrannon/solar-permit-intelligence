# Solar Permit Intelligence

A focused document intelligence MVP for solar permit packets and SolarAPP approval documents. This system ingests solar-related PDFs, classifies document types, extracts structured data, validates results against deterministic rules, and evaluates performance against labeled truth data.

## Why This Project Matters

Solar permitting involves complex, semi-standardized documentation that varies by jurisdiction. This project targets two document classes:
1. **Permit/application packets** - submitted by contractors to AHJs
2. **SolarAPP approval documents** - structured approval/inspection checklists

Automating the extraction and validation of this data can:
- Reduce manual review time for solar installers
- Catch errors and missing information earlier in the process
- Validate submitted permits against approved plans
- Provide a concrete testbed for real-world document intelligence challenges

This project demonstrates practical AI engineering: handling messy PDFs, extracting structured data, applying business logic, and measuring accuracy against ground truth.

**See [ROADMAP.md](ROADMAP.md) for the phased implementation plan and rationale for the dual-document approach.**

## MVP Scope

This is a **30-day portfolio-grade MVP**, not an enterprise platform. The focus is on building a working end-to-end pipeline with clear evaluation metrics.

### Proposed Pipeline

```
ingestion → preprocessing → classification → extraction → rules → evaluation → reporting
```

1. **Ingestion**: Load PDFs and images from raw data directory
2. **Preprocessing**: Convert to processable format, handle multi-page docs
3. **Classification**: Identify document/page types (permit app, electrical diagram, site plan, etc.)
4. **Extraction**: Pull structured fields from classified documents
5. **Rules**: Apply deterministic validation rules to extracted data
6. **Evaluation**: Compare results against labeled truth set, measure accuracy
7. **Reporting**: Generate failure logs and performance metrics

### Folder Structure

```
solar-permit-intelligence/
├── README.md                    # This file
├── pyproject.toml              # Python project config
├── .gitignore                  # Git ignore rules
├── docs/                       # Documentation
│   ├── project_scope.md        # Detailed scope and constraints
│   ├── field_schema.md         # Current extracted fields (Phase 1-2)
│   ├── field_roadmap.md        # Comprehensive field universe (all phases)
│   ├── rules_v1.md             # Validation rules
│   ├── failure_log.md          # Template for tracking failures
│   └── architecture.md         # System design notes
├── data/                       # Data directories
│   ├── raw/                    # Original PDFs and images
│   ├── processed/              # Cleaned/normalized data
│   └── labeled/                # Ground truth labels
├── src/                        # Source code
│   ├── ingestion/              # File loading and preprocessing
│   ├── classification/         # Document type classification
│   ├── extraction/             # Field extraction logic
│   ├── rules/                  # Validation rules engine
│   ├── evaluation/             # Performance measurement
│   ├── utils/                  # Shared utilities
│   ├── schemas.py              # Pydantic data models
│   └── config.py               # Configuration constants
├── outputs/                    # Generated results and reports
└── notebooks/                  # Exploratory notebooks (use sparingly)
```

## Current Status

**Status**: Phase 1-2 implementation
**Date**: April 2026
**Progress**: 10 fields extracted, 6 validation rules, permit packets working

**Phase 1 (Complete)**:
- ✓ 10 core fields extracted (address, contractor, jurisdiction, system sizing, module/inverter/battery, service panel)
- ✓ 6 validation rules (core fields, battery consistency, module sizing, inverter required, service panel reasonableness)
- ✓ Evaluation against ground truth working
- ✓ Permit packet extraction functional

**Phase 2 (In Progress)**:
- ✓ Service panel fields (main_bus_amp_rating, main_breaker_amp_rating) extracted
- ✓ Service panel validation (main_bus_vs_breaker_reasonable) implemented
- [ ] Grid voltage extraction (next)
- [ ] Utility service rating extraction (next)
- [ ] Project type extraction (next)

**See [ROADMAP.md](ROADMAP.md) for phased implementation plan through Phase 7.**

## Project Goals

This project demonstrates practical AI engineering on messy real-world permit documents:
- Extract structured data from semi-structured PDFs
- Apply deterministic validation rules
- Evaluate extraction accuracy against ground truth
- Document failure modes clearly
- Support both permit packets and SolarAPP approval documents

Success means: **a working pipeline with measured performance, not perfect accuracy.**

## Not in Scope Yet

- Frontend/UI
- Docker containerization
- Cloud deployment
- Real-time processing
- Multi-user support
- Production-grade error handling
- Extensive testing infrastructure
- Database integration
- API endpoints

These may come later, but they're not the focus for the MVP.

## Getting Started

(Will be updated as implementation progresses)

```bash
# Install dependencies
pip install -e .

# (Future) Run pipeline
python -m src.pipeline
```

## License

Private project for portfolio demonstration.
