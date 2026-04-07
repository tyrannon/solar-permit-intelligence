# Architecture

This document describes the high-level system design for the solar permit intelligence MVP. The architecture is intentionally simple: a linear pipeline with clear stage boundaries.

## Design Principles

- **Linear pipeline**: Data flows through stages in order, no complex orchestration
- **Fail fast**: Errors at any stage should halt processing and log clearly
- **Modularity**: Each stage is independent and testable
- **Transparency**: Intermediate outputs at each stage for debugging
- **Simplicity**: No premature abstractions, no unnecessary frameworks

## Pipeline Overview

```
┌──────────────┐
│   Raw PDFs   │ (data/raw/)
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│   INGESTION      │ (src/ingestion/)
│  - Load PDFs     │
│  - Convert pages │
│  - Extract text  │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ CLASSIFICATION   │ (src/classification/)
│  - Page type     │
│  - Doc type      │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  EXTRACTION      │ (src/extraction/)
│  - Field parsing │
│  - OCR + regex   │
│  - Confidence    │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│     RULES        │ (src/rules/)
│  - Validation    │
│  - Consistency   │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│   EVALUATION     │ (src/evaluation/)
│  - Compare truth │
│  - Metrics       │
│  - Failure log   │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Output Report   │ (outputs/)
└──────────────────┘
```

## Stage Responsibilities

### Ingestion (`src/ingestion/`)

**Purpose**: Load raw documents and convert them into a processable format.

**Input**: PDF files in `data/raw/`

**Output**: Processed documents with:
- Per-page images (for visual analysis)
- Per-page text (from OCR or native PDF text)
- Document metadata (filename, page count, etc.)

**Key Tasks**:
- PDF loading
- Page splitting
- Text extraction (pypdf or pdfplumber)
- OCR if needed (Tesseract via pytesseract)
- Save intermediate outputs to `data/processed/`

**Key Libraries** (to be added in v1):
- pypdf or pdfplumber
- pytesseract
- Pillow

---

### Classification (`src/classification/`)

**Purpose**: Identify document types and page types to route extraction logic appropriately.

**Input**: Processed documents from ingestion

**Output**: Document with page classifications:
- Permit application form
- Electrical single-line diagram
- Site plan
- Equipment specification sheet
- Structural calculations
- Other/unknown

**Key Tasks**:
- Page-level classification (rule-based or simple ML)
- Document-level classification (aggregate page types)
- Confidence scoring

**Approach for v1**:
- Start with keyword/regex-based classification
- Look for headers, form numbers, visual patterns
- ML classification deferred unless necessary

---

### Extraction (`src/extraction/`)

**Purpose**: Extract structured fields from classified documents.

**Input**: Classified documents

**Output**: JSON objects matching the schema defined in `schemas.py`:
- Field values
- Confidence scores per field
- Source page references

**Key Tasks**:
- Field extraction using:
  - Regex patterns for known layouts
  - OCR + NER for unstructured text
  - Table parsing for equipment lists
- Unit normalization (kW, Amps, etc.)
- Confidence estimation

**Approach for v1**:
- Start with regex and keyword matching
- Use simple heuristics (e.g., "System Size" followed by number + "kW")
- Add ML-based NER if needed
- Store both raw extracted value and normalized value

---

### Rules (`src/rules/`)

**Purpose**: Validate extracted data against deterministic business logic.

**Input**: Extracted field data

**Output**: List of rule results:
- Rule name
- Status (PASS / FAIL / REVIEW_REQUIRED)
- Message
- Severity

**Key Tasks**:
- Run all validation rules defined in `rules_v1.md`
- Aggregate results
- Determine overall document status (pass / fail / needs review)

**Approach for v1**:
- Simple Python functions, one per rule
- Rules are stateless and independent
- No complex rule engine needed

---

### Evaluation (`src/evaluation/`)

**Purpose**: Compare extracted results to labeled ground truth and measure performance.

**Input**:
- Extracted data (from extraction + rules)
- Ground truth labels (from `data/labeled/`)

**Output**:
- Per-field accuracy metrics
- Confusion matrices for classification
- Rule validation accuracy
- Failure log entries
- Summary report

**Key Tasks**:
- Load ground truth labels
- Compare field-by-field
- Calculate precision, recall, accuracy per field
- Identify extraction errors and log them
- Generate human-readable report

**Approach for v1**:
- Ground truth stored as JSON files matching extraction schema
- Simple comparison logic (exact match, fuzzy match for strings)
- Metrics aggregated across all documents

---

## Data Flow Details

### File Naming Conventions

- Raw PDFs: `permit_001.pdf`, `permit_002.pdf`, etc.
- Processed data: `permit_001_processed.json` (contains pages, text, images paths)
- Classified data: `permit_001_classified.json` (adds page types)
- Extracted data: `permit_001_extracted.json` (field values + confidence)
- Rule results: `permit_001_rules.json` (validation outcomes)
- Ground truth: `permit_001_truth.json` (manually labeled)

### Intermediate Outputs

All stages write intermediate outputs to `data/processed/` or `outputs/` for:
- Debugging
- Incremental processing
- Pipeline restart without re-running earlier stages

### Error Handling

- Each stage catches exceptions and logs errors with context
- Failed documents are marked and skipped by downstream stages
- Errors logged to `outputs/error_log.txt`
- Pipeline continues processing remaining documents

---

## Module Structure

### `src/schemas.py`
Defines Pydantic models for all data structures:
- `ExtractedFields`: The 10 target fields
- `RuleResult`: Outcome of a single rule
- `ProcessedDocument`: Full document with all pipeline outputs
- Validation logic within models where appropriate

### `src/config.py`
Configuration constants:
- Directory paths
- File naming patterns
- Confidence thresholds
- Rule settings

### `src/utils/`
Shared utilities:
- File I/O helpers
- Logging setup
- Text normalization functions
- Common regex patterns

---

## Deployment Model (v1)

- **Execution**: Run locally via command line
- **Input**: Manually place PDFs in `data/raw/`
- **Output**: Review JSON results in `outputs/`
- **No API, no real-time processing, no web interface**

This is a batch processing pipeline for evaluation purposes.

---

## Future Considerations (v2+)

Not in scope for v1, but worth noting for future iterations:
- Parallel processing (process multiple documents concurrently)
- Incremental processing (resume from last completed stage)
- ML model training pipeline (if moving beyond regex extraction)
- API wrapper for external integration
- Database persistence (currently file-based)
- Monitoring and alerting
- Containerization (Docker)

---

## Summary

This architecture prioritizes:
1. **Simplicity**: Linear pipeline, no complex orchestration
2. **Transparency**: Intermediate outputs at every stage
3. **Modularity**: Clear boundaries between stages
4. **Debuggability**: Errors logged with context, easy to trace
5. **Iterability**: Easy to improve one stage without touching others

The goal is to ship a working end-to-end system quickly, measure performance, and learn what needs improvement.
