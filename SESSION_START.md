# Session Start Runbook

Quick reference for resuming work on the solar permit intelligence MVP.

---

## 1. Quick Start

```bash
cd ~/solar-permit-intelligence
source .venv/bin/activate
git status
```

**Terminal setup**:
- Window 1: Run `claude` for Claude Code
- Window 2: Keep open for direct shell commands

---

## 2. Recommended Terminal Setup

**Window 1: Claude Code**
- Interactive development with Claude
- File operations, code changes, git commits

**Window 2: Repo Shell**
- Run pipeline commands directly
- Quick inspection and debugging
- Git operations

**Why split**: Claude Code handles iterative development; shell window lets you run commands and inspect outputs without switching context.

---

## 3. Core Workflow Sequence

```
ingest → inspect → extract → evaluate → review mismatches → iterate → commit → push
```

1. **ingest**: Convert raw PDF to processed JSON
2. **inspect**: Review page-by-page content and tags
3. **extract**: Pull candidate field values
4. **evaluate**: Compare against ground truth
5. **review mismatches**: Understand extraction failures
6. **iterate**: Refine patterns/heuristics as needed
7. **commit**: Save meaningful progress
8. **push**: Sync to remote

---

## 4. Core Commands

### Ingest a raw PDF
```bash
./.venv/bin/python -m src.ingestion.ingest_pdf data/raw/<file>.pdf
```

### Inspect processed JSON
```bash
./.venv/bin/python -m src.utils.inspect_processed data/processed/<file>.json
```

### Extract candidate fields
```bash
./.venv/bin/python -m src.extraction.extract_candidates data/processed/<file>.json
```

### Evaluate against ground truth
```bash
./.venv/bin/python -m src.evaluation.evaluate_extraction \
  data/processed/<file>.json \
  data/labeled/<truth_file>.json
```

### Run regression check on all fixtures
```bash
./.venv/bin/python -m src.evaluation.regression_check
```

**Use this before commits** to verify all fixtures still pass at 100% accuracy.

---

## 5. File Locations

**`data/raw/`**
- Original PDF files (not committed to git if sensitive)
- Source documents for ingestion

**`data/processed/`**
- JSON output from ingestion
- Contains page-by-page text, metadata, character counts
- Generated automatically, can be regenerated

**`data/labeled/`**
- Ground truth JSON files for evaluation
- Hand-labeled expected field values
- Version controlled

---

## 6. Example Workflow

Using `fictional_solar_permit_packet.pdf`:

```bash
# 1. Ingest
./.venv/bin/python -m src.ingestion.ingest_pdf data/raw/fictional_solar_permit_packet.pdf

# 2. Inspect
./.venv/bin/python -m src.utils.inspect_processed data/processed/fictional_solar_permit_packet.json

# 3. Extract
./.venv/bin/python -m src.extraction.extract_candidates data/processed/fictional_solar_permit_packet.json

# 4. Evaluate
./.venv/bin/python -m src.evaluation.evaluate_extraction \
  data/processed/fictional_solar_permit_packet.json \
  data/labeled/fictional_solar_permit_packet_truth.json

# 5. Regression check (all fixtures)
./.venv/bin/python -m src.evaluation.regression_check
```

Review output to see which fields matched and which failed.

---

## 7. Git Workflow

```bash
# Check status
git status

# Stage changes
git add .

# Commit with clear message
git commit -m "Describe the change clearly"

# Push to remote
git push
```

**Current remote**: Uses HTTPS for push operations.

---

## 8. Good Habits

- Always activate `.venv` before running commands
- Re-ingest if the raw PDF changed
- Ensure ground truth files match current PDF version
- **Run regression check before commits** to verify all fixtures still pass
- Commit after meaningful milestones (working extraction, improved accuracy, etc.)
- Keep iterations small and testable
- Review `git status` before committing to avoid accidental commits

---

## 9. Troubleshooting

**Environment not activated**
```bash
# If commands fail with import errors
source .venv/bin/activate
```

**Extraction/evaluation mismatch**
- Stale processed JSON: Re-run ingestion
- Stale truth file: Update ground truth to match current PDF content
- Check that document IDs match between processed and truth files

**Git push issues**
- This repo uses HTTPS remote
- Ensure credentials are configured

---

## 10. Minimal Restart Checklist

```bash
cd ~/solar-permit-intelligence
source .venv/bin/activate
git status
git pull  # if working across machines
# Ready to work
```

Open two terminal windows, run `claude` in one, keep the other for shell commands.
