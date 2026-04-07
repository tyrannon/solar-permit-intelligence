# Failure Log

This document tracks specific failures encountered during pipeline execution. The goal is to identify patterns, prioritize fixes, and measure improvement over time.

## Log Template

Use this template when documenting failures:

```
### [YYYY-MM-DD] Failure #N

**Sample File**: `filename.pdf`
**Pipeline Stage**: ingestion | classification | extraction | rules | evaluation
**Issue**: Brief description of what went wrong
**Suspected Cause**: OCR error | wrong classification | table parsing | confidence | etc.
**Severity**: critical | high | medium | low
**Next Action**: What should be done to fix or mitigate this
**Status**: open | investigating | fixed | wontfix
```

---

## Logged Failures

(This section will be populated as failures are encountered during development and testing)

### Example Entry (Delete when real failures are logged)

**Sample File**: `example_permit_001.pdf`
**Pipeline Stage**: extraction
**Issue**: System size extracted as "8 kW" but should be "8.5 kW"
**Suspected Cause**: OCR misread decimal point as space
**Severity**: medium
**Next Action**: Improve OCR preprocessing, add confidence thresholding
**Status**: open

---

## Known Failure Modes (Anticipated)

These are likely failure modes we expect to encounter based on the problem domain. This list helps guide testing and error handling priorities.

### 1. OCR Misreads
**Description**: Tesseract or other OCR engines misread characters, especially in low-quality scans.

**Common Examples**:
- "0" vs "O"
- "1" vs "l" vs "I"
- Decimal points missed or added incorrectly
- Units concatenated with numbers ("8.5kW" → "85kW")

**Mitigation**:
- Preprocessing: deskew, denoise, contrast enhancement
- Postprocessing: regex validation, unit normalization
- Confidence thresholding

---

### 2. Conflicting Values on Different Pages
**Description**: Same field appears multiple times with different values (e.g., draft vs. final system size).

**Common Examples**:
- Original application lists 8.0 kW, revised diagram shows 8.5 kW
- Contractor name spelled differently on different forms

**Mitigation**:
- Page-level confidence tracking
- Prefer values from specific document types (e.g., official permit form over supplemental)
- Flag conflicts for manual review

---

### 3. Wrong Page Classification
**Description**: Classify a site plan as an electrical diagram, or vice versa.

**Common Examples**:
- Both document types contain similar layout elements
- Header/footer text misleading
- Low-quality scan makes visual features unreliable

**Mitigation**:
- Improve classification model training data
- Use multiple features (text + visual)
- Confidence thresholding

---

### 4. Table Parsing Issues
**Description**: Structured data in tables is mis-parsed or columns misaligned.

**Common Examples**:
- Equipment list: module model in one column, count in another, but parser merges them
- Multi-row entries treated as separate items
- Table headers not detected, data misinterpreted

**Mitigation**:
- Use specialized table extraction libraries (Camelot, Tabula, etc.)
- Validate column structure before extraction
- Fall back to regex-based extraction if table parsing fails

---

### 5. Low-Confidence Extraction
**Description**: Extraction completes but confidence scores are low, indicating uncertainty.

**Common Examples**:
- Poor image quality
- Unusual form layouts not seen in training data
- Ambiguous field labels

**Mitigation**:
- Reject extractions below confidence threshold
- Route to manual review
- Improve training data diversity

---

### 6. Unit Normalization Issues
**Description**: Fields extracted with incorrect or inconsistent units.

**Common Examples**:
- "8500W" vs. "8.5kW" (should normalize to kW)
- "200 Amps" vs. "200A" vs. "200" (should normalize to integer)
- Feet vs. meters on site plans

**Mitigation**:
- Postprocessing unit normalization
- Regex patterns to detect and convert units
- Store raw extracted value + normalized value

---

### 7. Missing Fields
**Description**: Required fields not found in document.

**Common Examples**:
- Jurisdiction only in letterhead, not in extractable text
- Battery model not listed because no battery present (need to infer)
- Contractor license number present but company name missing

**Mitigation**:
- Fallback extraction strategies (e.g., letterhead parsing)
- Field inference from other fields
- Manual review queue

---

### 8. Multi-Page Document Handling
**Description**: Information split across multiple pages, causing incomplete extraction.

**Common Examples**:
- Page 1 has applicant info, page 3 has system size
- Parser processes pages independently, loses context
- Page order incorrect in PDF

**Mitigation**:
- Document-level extraction (not page-level)
- Maintain context across pages
- Detect and correct page order issues

---

## Failure Metrics to Track

Once real failures are logged, track:
- **Failure rate by pipeline stage** (which stage fails most often?)
- **Failure rate by document source** (specific jurisdictions harder than others?)
- **Failure rate by field** (which fields extract poorly?)
- **Failure severity distribution** (how many are critical vs. low priority?)
- **Resolution rate** (how many failures get fixed over time?)

## Review Cadence

- Review failure log weekly during development
- Prioritize fixes based on frequency and severity
- Update extraction/classification logic based on patterns
- Archive resolved failures to separate document after v1 completion
