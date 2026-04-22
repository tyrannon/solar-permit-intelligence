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
│   ├── field_schema.md         # Target extraction fields
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

**Status**: Initial scaffolding for v1
**Date**: April 2026

The repository structure is in place. No extraction, classification, or rules logic has been implemented yet. This is the starting point.

## 30-Day Goal

By day 30, the system should:
- Ingest 10-20 real solar permit PDFs
- Classify document types with basic accuracy
- Extract 8-10 structured fields per permit
- Apply 5-8 deterministic validation rules
- Generate an evaluation report comparing extracted data to ground truth
- Document failure modes and extraction accuracy by field
- Have a clear plan for v2 improvements

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
