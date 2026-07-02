# Architecture Review — July 2026

A full-system review of solar-permit-intelligence: current state, strengths, risks, target architecture, AI and data-model recommendations, roadmap, and execution plan.

Everything in Section 1 is verified directly from the code. Later sections separate observation from inference and recommendation.

---

## 1. The system as it exists today

### 1.1 Plain-English description

This is a **batch, command-line Python pipeline** that reads a solar permit PDF, extracts its text, guesses what each page is, pulls ~12 structured fields out of the text using regex label-matching, checks those fields against 7 deterministic consistency rules, and measures extraction accuracy against hand-labeled ground truth files.

Three things the README and CLAUDE.md are honest about, and this review must be too:

- **There is no AI in the system.** No LLM calls, no ML models, no embeddings, no prompts. Extraction is 100% regex and keyword heuristics (`src/extraction/extract_candidates.py`). The only dependencies are `pydantic` and `pypdf` (`pyproject.toml:11-14`).
- **There is no frontend, backend, API, or database.** Five CLI entry points, JSON files on disk. This matches the stated scope ("Not in Scope Yet", README.md:102-114).
- **There is no OCR.** Ingestion uses `pypdf`'s native text layer only (`src/ingestion/ingest_pdf.py:38-44`). A scanned permit produces empty text and the pipeline silently reports "no matching label found" rather than "this document has no text layer."

So the honest framing: this is a well-disciplined **deterministic document-extraction MVP with a real evaluation harness**, positioned to add AI later. That is a legitimate and defensible place to be — but the review questions about "AI workflow design," "API boundaries," and "database logic" mostly have the answer "does not exist yet," and the recommendations below are about *when and how* to introduce those layers, not how to fix them.

### 1.2 Architecture map

```
                    ┌─────────────────────────────────────────────┐
                    │  data/raw/*.pdf   (gitignored, local only)  │
                    └───────────────┬─────────────────────────────┘
                                    │
             ./.venv/bin/python -m src.ingestion.ingest_pdf
                                    │
                    ┌───────────────▼─────────────────────────────┐
                    │  data/processed/<doc>.json                  │
                    │  {document_id, pages[{page_number, text,    │
                    │   char_count}], metadata, page_count}       │
                    └───────┬───────────────────┬─────────────────┘
                            │                   │
        src.utils.inspect_processed      src.extraction.extract_candidates
        (page tags via keyword           (12 fields via LABEL_PATTERNS +
         heuristics — print only)         STOP_LABELS — print only,
                                          NOT persisted to disk)
                                                │
                            ┌───────────────────┼───────────────────┐
                            │                   │                   │
              src.validation.run_validation    │      src.evaluation.evaluate_extraction
              (re-runs extraction, applies     │      (re-runs extraction, compares to
               7 rules, prints PASS/FAIL/      │       data/labeled/<doc>_truth.json)
               REVIEW_REQUIRED)                │                   │
                                               │      src.evaluation.regression_check
                                               │      (loops all labeled fixtures,
                                               │       exits 1 unless 100% accuracy)
```

Note the shape: **ingestion is the only stage that persists output.** Extraction, validation, and evaluation are all print-to-terminal tools, and validation/evaluation each *re-run* extraction internally (`src/validation/run_validation.py:40`, `src/evaluation/evaluate_extraction.py:67`) rather than reading a saved artifact.

### 1.3 Modules and responsibilities

| Module | Responsibility | State |
|---|---|---|
| `src/ingestion/ingest_pdf.py` | PDF → per-page text JSON | Working |
| `src/utils/inspect_processed.py` | Page-role tagging (9 tag types, keyword lists) + human-readable dump | Working |
| `src/extraction/extract_candidates.py` | 12 fields via label patterns, stop labels, type-specific parsers | Working; 1,027 lines, the center of gravity |
| `src/validation/validate_fields.py` | 7 pure-function rules → `(status, explanation)` tuples | Working |
| `src/validation/run_validation.py` | CLI wrapper: extract + validate + print | Working |
| `src/evaluation/evaluate_extraction.py` | Extract + compare to truth JSON, per-field match + accuracy | Working |
| `src/evaluation/regression_check.py` | All-fixture accuracy sweep, exit code gate | Working (but see fixture risk) |
| `src/schemas.py` | Pydantic models: `ExtractedFields`, `ConfidenceScores`, `RuleResult`, `ProcessedDocument` | **Defined but never imported by any pipeline code** |
| `src/config.py` | Paths, thresholds, naming patterns | **Mostly dead — thresholds, patterns, log paths all unused** |
| `src/classification/`, `src/rules/` | Empty packages (`__init__.py` only) | Placeholders; the logic they name lives elsewhere |

### 1.4 Primary data flow

1. User runs `ingest_pdf data/raw/foo.pdf` → `data/processed/foo.json` with page-by-page text (`ingest_pdf.py:75-83`).
2. User runs `extract_candidates data/processed/foo.json`. For each of 12 fields (`extract_candidates.py:951`), the extractor: classifies pages as form/non-form via keyword list copied from the inspector (`extract_candidates.py:293-308`), searches label regexes per page, slices the text after the label until a field-specific stop label / generic next-label / double newline (`extract_value_after_label`, `extract_candidates.py:327-411`), then type-parses (float/int/amperage/voltage/boolean). Confidence is a hardcoded constant: 0.8 label match, 0.7 value-before-label bus fallback, 0.2 label-but-no-value, 0.0 no match.
3. Validation re-runs step 2, plucks `candidate_value` per field, and runs 7 rules (`validate_fields.py:363-417`).
4. Evaluation re-runs step 2 and compares to `data/labeled/foo_truth.json` with type-aware exact matching (`evaluate_extraction.py:87-143`).

### 1.5 Tech stack

- Python ≥3.10, `pydantic ≥2`, `pypdf ≥4`. Nothing else (`pyproject.toml`).
- No test framework, no CI, no linter config, no Docker, no server.
- Local venv, manual CLI invocation per `SESSION_START.md`.

### 1.6 Hidden assumptions baked into the current design

1. **PDFs have a native text layer.** No OCR path exists despite `docs/architecture.md:84-87` listing pytesseract as a planned v1 library. Scanned permits — a large share of real AHJ traffic — fail silently.
2. **Documents are label-then-value forms.** The whole extractor assumes "Label: value" text order; one fallback exists for value-before-label busbar ratings (`extract_amperage_before_bus_label`, `extract_candidates.py:582`). Tables, checkboxes, and diagram annotations are invisible.
3. **One true value per field per document.** `extract_candidates` keeps a single `best_result` per field and stops at the first ≥0.8 match (`extract_candidates.py:961-970`). Conflicting values on different pages — failure mode #2 in your own `docs/failure_log.md:59-70` — cannot be represented.
4. **Commands run from repo root.** Output and fixture paths are relative (`Path("data/processed")` at `ingest_pdf.py:78`; `Path("data/labeled")` at `regression_check.py:21-22`) even though `src/config.py` defines absolute anchored paths that nothing uses.
5. **US residential, English, largely California.** Hardcoded plausibility ranges (50–600A, 250–700W/module, 100–600V) and `docs/rules_v1.md:164` checking for "CA".
6. **Confidence is symbolic, not statistical.** The numbers 0.8/0.7/0.2 encode "which code path matched," not likelihood of correctness. `config.py:18-19` defines thresholds (0.7 / 0.85) that no code reads.
7. **The fixture set is small enough that 100% accuracy is a meaningful gate** (`regression_check.py:93-98`). True today; becomes actively harmful as the corpus grows (see §3.4).

---

## 2. Architectural strengths

Specific things worth preserving:

1. **Deterministic-first extraction with rules as pure functions.** Every rule in `validate_fields.py` takes plain values, returns `(status, human_explanation)`, and has its logic documented in the docstring. This is exactly the audit story a permitting product needs — an AHJ reviewer can read *why* a document was flagged. Most AI-first prototypes never achieve this and have to retrofit it.
2. **The `PASS / FAIL / REVIEW_REQUIRED` tri-state.** Distinguishing "wrong" from "cannot determine — human needed" (e.g. `validate_battery_requires_battery_model`, `validate_fields.py:34-39`) is the correct core primitive for human-in-the-loop review, and it's already threaded through every rule.
3. **A real evaluation culture.** Ground-truth labeling, per-field comparison, a regression sweep wired to an exit code (`regression_check.py`), and a failure log that contains an actual *observed, dated* failure entry with root-cause analysis (`docs/failure_log.md:163-174` — eligibility-cap text "busbar rating of 225A or less" extracted as a real rating). This eval-loop habit is the single most valuable asset in the repo; it's what will let you adopt LLM extraction safely later.
4. **Conservative, legible parsers.** `parse_grid_voltage` (`extract_candidates.py:617-663`) deliberately returns `None` for ambiguous "120/240" rather than guessing — "do not invent data, return review on ambiguity" is actually enforced in code, not just stated in CLAUDE.md.
5. **Stage boundaries that match a future service decomposition.** Ingest → classify → extract → validate → evaluate is the right cut. When this becomes a service, these become queue stages or API steps with almost no conceptual rework.
6. **Scope discipline in the docs.** `ROADMAP.md` has phased field families, an explicit migration plan for the one planned breaking change (AC/DC split, ROADMAP.md:153-180), and a "Not Now / Never" list with reasons (ROADMAP.md:255-303). That's product thinking, not just code.
7. **Minimal dependency surface.** Two runtime deps. Nothing to unwind later.
8. **Incremental git history.** Small commits, each one field or one rule, regression-checked before commit per `SESSION_START.md:163`. Good solo-builder hygiene.

Good instincts overall: the project resists the temptation to bolt on an LLM before having a measurement harness, which is the #1 failure mode of document-AI projects.

---

## 3. Biggest risks and weaknesses

Ranked by severity. "Fix now" = this week.

### 3.1 The regression safety net doesn't exist outside your laptop — **critical, fix now**

`.gitignore:56-61` excludes `data/raw/*`, `data/processed/*`, **and `data/labeled/*`**. The repo as cloned contains zero fixtures; `regression_check.py` finds nothing and returns "No fixtures found." Meanwhile `SESSION_START.md:104-107` claims labeled data is "version controlled" — it isn't. There are also no unit tests, no `tests/` directory, no pytest dependency, and no CI.

Why it matters: every refinement to the 175-line `STOP_LABELS` structure (`extract_candidates.py:118-290`) is a game of regex whack-a-mole where any change can silently break another field on another fixture. The regression sweep is the *only* thing catching that, and it lives on one machine. Lose the laptop, lose the safety net. It also means no CI can ever protect this repo until fixtures are committed.

Fix: commit the synthetic/fictional fixtures (they're named `fictional_*` — if genuinely synthetic, they're safe under your own data rules), or create a small committed set of synthetic processed-JSON + truth pairs. Then add pytest + GitHub Actions running `regression_check` plus unit tests.

### 3.2 `schemas.py` is fiction — the real data contract is untyped dicts — **high, fix now**

`src/schemas.py` defines `ExtractedFields`, `ConfidenceScores`, `RuleResult`, `ProcessedDocument` — and **no pipeline file imports any of them**. Worse, the schema has drifted from reality:

- `ExtractedFields` has `module_model` and `main_service_panel_rating` (`schemas.py:32,34`); the extractor extracts neither, and instead extracts `main_bus_amp_rating`, `main_breaker_amp_rating`, `utility_service_rating`, `grid_voltage` — none of which exist in the schema.
- `RuleResult` carries a `severity` field and `RuleStatus` enum; actual rules return bare string tuples with no severity (`validate_fields.py:16-65`).
- The inter-stage contract is actually `results["extractions"][field]["candidate_value"]` dict-shape, duplicated by hand in validation (`validate_fields.py:376-386`) and evaluation (`evaluate_extraction.py:90-91`).

Why it matters: the one file that claims to be the source of truth for your data model is wrong, and every consumer re-implements dict plucking. When you add the LLM extractor (which *must* validate structured output against a schema), you'll need this fixed anyway.

### 3.3 Extraction results are never persisted; downstream stages recompute — **high, fix now**

`extract_candidates.main()` prints and discards (`extract_candidates.py:988-1023`). Validation and evaluation each call `extract_candidates()` again. `config.py:35` defines `EXTRACTED_JSON_PATTERN` for a file that is never written; `docs/architecture.md:208-213` promises "intermediate outputs at every stage" for restart/debugging — not true for extraction, rules, or evaluation.

Why it matters: (a) you cannot audit "what did the system say about document X on date Y" — fatal for a permitting tool; (b) there is no record tying an output to the extractor version that produced it; (c) three tools re-do the same work; (d) the eval harness can't be run against a *stored* historical run to detect drift.

### 3.4 The 100%-accuracy regression gate incentivizes overfitting — **high, address soon**

`regression_check.py:93-98` returns failure unless accuracy is 100%. Combined with per-fixture hand-tuned stop labels (e.g. `battery_model` has a stop pattern for the literal string `"(removed from final scope)"` — `extract_candidates.py:222` — which can only have come from one specific fixture), the incentive structure is: add fixture → add bespoke regexes until 100% → repeat. Git history shows exactly this loop ("Refine utility service rating extraction to reduce false positives" appears twice: `8a941d3`, `d59a6df`).

Why it matters: this scales O(fixtures) in maintenance cost and will *not* generalize to fixture #30. The metric to manage is per-field precision/recall over a growing corpus with an accepted <100% target, plus the confidence system routing misses to review. Perfect fixture accuracy is the wrong objective for a system whose product story is "flag what we're unsure about."

### 3.5 No OCR and no text-layer detection → silent failure on scans — **high, soon**

`ingest_pdf.py` will happily produce a processed JSON of empty-text pages. Nothing downstream distinguishes "field absent" from "document unreadable." Minimum viable fix is not OCR itself — it's *detection*: if total chars/page is near zero, mark the document `needs_ocr` in the processed JSON and have extraction refuse to run rather than emit twelve 0.0-confidence nulls. Actual OCR (pytesseract or a vision LLM) can follow.

### 3.6 `battery_present` scans the whole page — **medium, soon**

Unlike every other field, `battery_present` runs `parse_boolean_value` over the *entire page text* (`extract_candidates.py:819-839`) at confidence 0.8. Any narrative like "no battery is proposed at this time" — or worse, instructional template text ("if a battery is included…") — decides the field. Your own failure log (#9) shows template text already poisons amperage fields; this field is even more exposed. It also short-circuits label-based battery extraction entirely, since the whole-page path returns before `LABEL_PATTERNS["battery_present"]` is ever consulted.

### 3.7 Duplication and dead structure — **medium, soon**

- Page-role heuristics exist twice: `HEURISTIC_RULES["top_level_form"]` (`inspect_processed.py:14-29`) and `TOP_LEVEL_FORM_KEYWORDS` (`extract_candidates.py:294-308`, comment admits "copied from inspection utility"). They will drift.
- `src/classification/` and `src/rules/` are empty packages while classification logic lives in `utils`/`extraction` and rules live in `src/validation/` — a package the architecture doc doesn't even mention (it says `src/rules/`, `docs/architecture.md:144`).
- `config.py` duplicates-and-contradicts code: module wattage bounds are 0.3–0.45 kW in config (`config.py:26-27`) but hardcoded 250–700W in the rule (`validate_fields.py:163-164`); confidence thresholds, file patterns, and log paths are all unused.

### 3.8 Documentation drift — **medium, soon**

`docs/rules_v1.md` defines 8 rules (`system_size_range`, `equipment_models_present`, `address_format_check`, `jurisdiction_present`…) of which several are unimplemented, while the code has rules (`utility_service_vs_panel_reasonable`, `main_bus_vs_breaker_reasonable`) the doc lacks. `docs/field_schema.md` says `module_model` is "Required: Yes" but it isn't extracted. `docs/architecture.md` describes per-stage outputs and error handling (`outputs/error_log.txt`, "failed documents are marked and skipped") that don't exist. For a repo whose CLAUDE.md demands "documentation reflects reality," the docs currently oversell by roughly one phase.

### 3.9 Evaluation semantics quietly flatter the numbers — **medium, soon**

`null == null` counts as an exact match everywhere (`evaluate_extraction.py:102-131`). A fixture where 4 of 12 fields are genuinely absent starts at 33% "accuracy" for free, and a lazy extractor that returns all nulls scores whatever fraction of truth is null. There's also no distinction between *missed* (extracted null, truth has value), *spurious* (extracted value, truth null), and *wrong* (both present, different) — three failure classes with very different product costs. A spurious battery rating on a permit is worse than a miss.

### 3.10 Error handling is aspirational — **low-medium, later**

Bare `except:` in metadata extraction (`ingest_pdf.py:33-34`), no logging anywhere despite `config.py:38-40` defining log paths, fail-fast promised in docs but not systematized. Fine at this scale; must be settled before any multi-document batch runner.

### 3.11 PII posture relies entirely on convention — **low now, high later**

Real permits carry homeowner names, addresses, phone numbers, signatures. Today safety = "don't commit raw docs" (gitignore + CLAUDE.md rules). The moment this touches a server, a database, or an LLM API, you need a deliberate answer: what leaves the machine, what's redacted, what's retained. Flagging now because it constrains the AI architecture below (e.g., which fields may be sent to a hosted model).

---

## 4. The next architecture (3–6 months)

**No rewrite.** The pipeline shape is right. The work is: make the implicit explicit (contracts, artifacts, runs), consolidate duplication, then add capability layers (OCR, LLM fallback, review queue, storage) in that order.

### 4.1 Target module layout

```
src/
├── schemas.py            # REAL contracts: PageText, ProcessedDocument,
│                         #   FieldCandidate, ExtractionRun, RuleResult,
│                         #   EvaluationRun — used by every stage
├── config.py             # only constants that are actually read
├── ingestion/
│   ├── ingest_pdf.py     # + text-layer detection → needs_ocr flag
│   └── ocr.py            # (later) OCR fallback
├── classification/
│   └── page_tags.py      # THE single home for page heuristics
│                         #   (inspect + extraction both import it)
├── extraction/
│   ├── fields.py         # FieldSpec table: name, type, labels,
│   │                     #   stop_labels, parser, max_len, search scope
│   ├── regex_extractor.py# today's engine, driven by FieldSpec
│   └── llm_extractor.py  # (later) fallback extractor, same output type
├── validation/
│   └── rules.py          # rules + severity, returning RuleResult
├── evaluation/
│   ├── evaluate.py       # reads persisted ExtractionRun (no re-extract)
│   └── regression.py
├── pipeline.py           # one command: pdf → processed → extracted →
│                         #   validated, each stage persisted with run_id
└── review/               # (later) review queue: list REVIEW_REQUIRED,
                          #   record corrections as data
tests/                    # pytest: parsers, rules, boundary detection
data/fixtures/            # COMMITTED synthetic processed+truth pairs
.github/workflows/ci.yml  # pytest + regression on every push
```

### 4.2 What lives where

- **Frontend:** nothing, for months. When a review UI is needed, start with the terminal (a `review` CLI listing REVIEW_REQUIRED items and recording corrections to JSONL). A web UI is justified only when a second human needs to review.
- **Backend/API:** none until an external consumer exists. When it does, a thin FastAPI wrapper over `pipeline.py` is a day of work *because* the stages already have clean contracts. Do not build it speculatively.
- **AI orchestration layer:** one module (`extraction/llm_extractor.py` + a `prompts/` dir). Not a framework. See §5.
- **Database:** files now; SQLite when the review workflow starts generating corrections (see §6). Postgres only with multi-user/server needs.
- **Reusable services:** none yet. The reusable *units* are FieldSpec, the rule library, and the eval harness — keep them import-clean (no I/O inside) so they can be lifted into a service later.

### 4.3 Delete / simplify / consolidate

- Delete dead config constants or wire them in — no third option (`config.py:18-19, 26-40`).
- Consolidate page heuristics into `classification/page_tags.py`; delete the copy in `extract_candidates.py:293-324`.
- Collapse the four parallel per-field structures (`LABEL_PATTERNS`, `STOP_LABELS`, `max_lengths` dict at `extract_candidates.py:347-360`, and the type dispatch in `clean_extracted_value`) into one `FieldSpec` dataclass table. This is not premature abstraction — it's removing a 4-way synchronization hazard that already spans 400 lines. Adding Phase 2's remaining fields becomes one table row instead of edits in four places.
- Reconcile or delete drifted docs (`rules_v1.md`, parts of `architecture.md`, `SESSION_START.md:106`).
- Either use `src/rules/` (move validation there to match docs) or update docs to bless `src/validation/`. Pick one; stop having both.

### 4.4 Abstractions to introduce — and to refuse

Introduce (each justified by a concrete current pain):
1. **FieldSpec** — kills the parallel-dict hazard.
2. **Persisted, versioned ExtractionRun** — audit + eval decoupling. Include `extractor_version` (git SHA is fine) and timestamps.
3. **RuleResult with severity** — the schema already promises it; reviewers need to sort critical vs info.
4. **An `Extractor` interface only when the second extractor (LLM) actually lands** — rule of two, not before.

Refuse: plugin registries, DI containers, generic pipeline orchestration frameworks, LangChain/agent frameworks, event buses, microservices, abstract rule engines. Your CLAUDE.md anti-overengineering list is correct; keep obeying it. At 10–100 documents/day, a for-loop is an orchestrator.

---

## 5. AI system design review

### 5.1 Current state, honestly

There are no prompts, no AI calls, no model outputs to validate, and therefore no hallucination, grounding, or prompt-versioning surface today. The "confidence scores" are code-path constants, not model confidences. Questions like "are AI calls isolated" are N/A.

That is not a criticism — building the deterministic baseline and eval harness *first* is the correct order, and it's rare. But two things are true simultaneously: (a) the project brands itself "AI engineering" while shipping regex, and (b) the regex approach is visibly hitting its ceiling (175 lines of stop labels, fixture-specific patterns, an observed template-text failure). The interesting question is *when* the regex treadmill costs more than an LLM's risks. You're close.

### 5.2 Where AI genuinely helps here — and where it must not go

**Use an LLM for:** field extraction from messy text. This is exactly the task LLMs beat regex at: layout variation, tables flattened to text, synonym labels, value-before-label phrasing, "N/A" vs blank vs "none" semantics. Your stop-label whack-a-mole is manual feature-engineering of what a model does natively.

**Never use an LLM for:** the validation rules. `main_breaker ≤ main_bus`, the 120% rule, battery consistency — these are law-and-physics checks that must be exact, explainable, and identical every run. `validate_fields.py` should remain deterministic forever. Same for evaluation math.

**Don't bother with:** agents, multi-step orchestration, retrieval/RAG. A permit packet is one document that fits in a context window; there is no corpus to retrieve from and no multi-tool decision for an agent to make. Adding agent machinery here would be resume-driven architecture.

### 5.3 Recommended AI architecture (concrete)

1. **LLM as fallback extractor, regex as primary.** For each field where the regex path yields confidence < 0.8 (or null), send the relevant page text to a model with a structured-output request. Regex stays first because it's free, instant, and deterministic on the easy 70%.
2. **Structured outputs validated by the (fixed) Pydantic schema.** The model returns `{value, source_page, source_quote}` per field; parse with `ExtractedFields`-derived models. Validation failure → null + REVIEW_REQUIRED, never a retry-until-it-parses loop.
3. **Grounding via mandatory span citation.** Require `source_quote` to be a verbatim substring of the page text and *verify that programmatically* (`quote in page_text`). If the quote doesn't appear, discard the value. This single check converts most hallucinations into review flags and gives you the audit trail ("value came from page 3: '…200A main breaker…'") that your rule engine already has.
4. **Same funnel, same eval.** LLM candidates flow into the identical `FieldCandidate` shape and are scored by the identical evaluation harness. Your first LLM milestone is a *report*: regex-only vs regex+LLM accuracy on the fixture set. The harness you already built is what makes LLM adoption safe — this is your structural advantage; use it.
5. **Prompt/version management: files, not platforms.** `prompts/extract_fields_v1.md` in git; record `{model_id, prompt_file, prompt_sha, temperature}` inside every persisted ExtractionRun. That's the whole system until you have A/B needs. No prompt-management SaaS.
6. **Human-in-the-loop path.** You already own the primitive (REVIEW_REQUIRED). Extend it: every LLM-sourced field below a confidence bar → review queue; every human correction stored as data (see §6). Corrections become (a) new labeled truth, (b) regression fixtures, (c) eventually few-shot examples. This flywheel is the product.
7. **Privacy constraint:** decide before the first API call which fields may leave the machine. Extraction requires sending page text (addresses, owner names) to a hosted model — for a portfolio MVP on synthetic docs, fine; for real AHJ documents, you need either a data-processing-appropriate API tier or local models. Write this down in `docs/` when you wire the first call.
8. **Later, not now:** vision-capable models for single-line diagrams and scanned pages (this also becomes your OCR answer — one vision call can replace the tesseract pipeline). Sequence it after text-based LLM extraction proves out on the eval set.

---

## 6. Database and data model review

### 6.1 Entities that exist today (implicitly, as JSON/dicts)

- **Document** (`data/processed/<id>.json`): id, source path, pages[].
- **FieldCandidate** (in-memory dict): field, page, matched label, value, symbolic confidence, note.
- **RuleResult** (in-memory tuple): status + explanation. No severity despite the schema and docs promising it.
- **GroundTruth** (`data/labeled/*_truth.json`): field → expected value.
- **EvaluationResult** (in-memory dict): per-field match + accuracy.

### 6.2 What's missing or unclear

- **Run** — the biggest gap. Nothing records "extractor version X processed document Y at time Z and produced W." Without it there is no auditability, no drift detection, no reproducing a past output. This matters more than any storage-engine choice.
- **Jurisdiction/AHJ as an entity.** Today jurisdiction is a string field. The product vision (per-jurisdiction rules, SolarAPP AHJ ids, ROADMAP Phase 3) needs it as a first-class thing with its own attributes eventually.
- **Correction / ReviewAction.** The review loop's output — "human said the real value is X" — has no home. This is the most valuable data the product will ever generate; model it early (even as JSONL).
- **DocumentClass** (permit_packet vs solarapp_approval) — planned Phase 3, correctly.
- **Multi-value fields.** One inverter model, one value per field. Real packets have conflicting/multiple values; the failure log already anticipates this. A `FieldCandidate` *list* per field (with one flagged `selected`) fixes both the conflict problem and the audit story at once.
- **Permit lifecycle** (submitted → reviewed → approved → inspected): not modeled at all, and *correctly* not — that's a workflow product decision, not a v1 schema need. But note the current model is document-centric, not project-centric; a "Project" that owns multiple documents (application + approval + revision) is the pivot point when you get there.

### 6.3 Recommendation

Stay file-based this month, but make the files *be* the entity model: persisted, schema-validated `ExtractionRun` JSON per run, corrections as append-only JSONL. Move to **SQLite** (stdlib, zero ops) when either (a) you're querying across >~50 documents ("which docs failed rule X"), or (b) the correction/review loop is live. The schema at that point:

```
documents(id, source_file, page_count, doc_class, needs_ocr, ingested_at)
extraction_runs(id, document_id, extractor_version, model_id?, prompt_sha?, created_at)
field_candidates(run_id, field, value_json, page, source_quote, confidence, method{regex|llm}, selected)
rule_results(run_id, rule, status, severity, message)
ground_truth(document_id, field, value_json, labeled_by, labeled_at)
corrections(id, run_id, field, old_value, new_value, reviewer, created_at)
jurisdictions(id, name, ahj_code)   -- when Phase 3 lands
```

Everything in it maps 1:1 to structures you already have; the migration is mechanical. Skip ORMs; `sqlite3` + your Pydantic models is enough.

---

## 7. Product roadmap from the architecture

### Immediate (this week)
1. **Commit synthetic fixtures + un-gitignore `data/labeled`** — the safety net must survive the laptop. Difficulty: trivial. Impact: critical. Done = fresh clone runs `regression_check` green.
2. **Persist extraction output; make validation/evaluation read it.** Difficulty: low. Impact: high (audit + decoupling). Done = `data/extracted/<id>_<run>.json` exists and no downstream tool calls `extract_candidates()` internally.
3. **Reconcile `schemas.py` with reality and use it.** Difficulty: low-medium. Impact: high. Done = extraction output is a validated Pydantic model; drifted fields removed or implemented.

### 1-week improvements
4. **pytest + GitHub Actions CI** running unit tests (parsers, boundary detection, each rule) + regression sweep. Depends on #1. Done = red X on a PR that breaks a fixture.
5. **Consolidate page heuristics into `src/classification/`**; delete the copy. Done = one import site.
6. **Doc reconciliation pass** (rules_v1, field_schema, architecture.md, SESSION_START). Done = docs describe only what exists.

### 2–4 weeks
7. **FieldSpec refactor** of the extractor (one table, one engine). Depends on #4 (tests protect the refactor). Done = adding a field touches one row + one fixture.
8. **Text-layer detection + `needs_ocr` flag**; refuse to extract from empty docs. Done = scanned PDF yields an explicit "unreadable" outcome, not 12 nulls.
9. **Eval upgrade:** per-field precision/recall; separate missed/spurious/wrong; stop counting null==null as success; drop the 100% gate in favor of a committed baseline file that CI compares against ("no field regresses"). Done = `regression_check` output shows per-field P/R vs baseline.
10. **Finish Phase 2 fields** (project_type; grid_voltage/utility_service already landed) on top of FieldSpec.

### 1–3 months
11. **LLM fallback extractor** per §5.3 (structured output, span verification, run metadata, eval comparison report). Depends on #2, #3, #9. Done = a table: accuracy regex-only vs hybrid, on ≥15 fixtures.
12. **Corpus expansion to 20–30 real/realistic documents** including SolarAPP approvals + document-class detection (Phase 3). This is what makes every metric meaningful.
13. **Review queue CLI + corrections log** (the HITL loop). Done = REVIEW_REQUIRED items listable; corrections persisted and replayable into truth files.
14. **SQLite persistence** per §6.3 once corrections exist.

### Longer-term bets
- **Permit-vs-approval reconciliation** (ROADMAP's multi-document diff) — this is the differentiated product feature; everything above feeds it.
- **Vision model for diagrams/scans** — unlocks the majority of real-world documents.
- **Jurisdiction rule packs** — deterministic rules parameterized per AHJ; the defensible moat (see §9).
- **Thin API + minimal review UI** — only when a second user exists.

### 7.a A note on CLAUDE.md
Several roadmap items (tests dir, CI, later SQLite/API) technically collide with CLAUDE.md's hard constraints ("no database unless explicitly requested," etc.). Treat this review as the trigger to *amend CLAUDE.md deliberately* at each stage boundary rather than drifting past it — it has served you well as a scope brake.

---

## 8. Developer execution plan — next 10 tasks in order

1. **Commit fixtures.** Edit `.gitignore` (keep `data/raw/*` ignored; allow `data/labeled/*.json` and a new `data/fixtures/`), add synthetic processed+truth pairs, fix `SESSION_START.md:106`.
   Commit: `Commit synthetic labeled fixtures so regression check works from a fresh clone`
   Validate: fresh clone → `regression_check` runs and reports.
2. **Add pytest with first unit tests** for `parse_numeric_value`, `parse_integer_value`, `parse_amperage_rating`, `parse_grid_voltage`, `parse_boolean_value`, and all 7 rules (pure functions — trivially testable). Files: `tests/test_parsers.py`, `tests/test_rules.py`, `pyproject.toml`.
   Commit: `Add pytest unit tests for value parsers and validation rules`
3. **Add CI.** `.github/workflows/ci.yml`: install, pytest, regression_check.
   Commit: `Add GitHub Actions CI running unit tests and fixture regression`
4. **Fix `schemas.py`** to match the 12 real fields + `FieldCandidate` + run metadata; delete or implement the drifted bits; validate extraction output through it. Files: `src/schemas.py`, `src/extraction/extract_candidates.py`.
   Commit: `Align schemas with implemented fields and validate extraction output`
5. **Persist extraction runs**; point `run_validation` and `evaluate_extraction` at the saved artifact (keep a `--reextract` convenience flag). Files: `extract_candidates.py`, `run_validation.py`, `evaluate_extraction.py`, `config.py`.
   Commit: `Persist extraction results per run and read them downstream`
6. **Consolidate page heuristics** into `src/classification/page_tags.py`; import from both call sites.
   Commit: `Move page heuristics to classification module and remove duplicate`
7. **FieldSpec refactor.** Introduce the dataclass table in `src/extraction/fields.py`; rewrite the engine to iterate specs; behavior-identical (CI + regression prove it). This is the refactor to do *before* adding more fields.
   Commit: `Refactor extractor around FieldSpec table with unchanged behavior`
8. **Constrain `battery_present`** to label-proximity (reuse the normal label path; whole-page scan only as a low-confidence 0.5 fallback). Add the failure-log #9 mitigations ("or less" cap rejection, Article-reference rejection) as parser tests.
   Commit: `Reduce battery_present and amperage false positives from narrative text`
9. **Eval semantics upgrade** per roadmap item 9 (P/R per field, missed/spurious/wrong, baseline-comparison gate).
   Commit: `Report per-field precision and recall and gate on baseline deltas`
10. **Text-layer detection** in ingestion (`needs_ocr` flag; extraction refuses unreadable docs with a clear message).
    Commit: `Detect missing PDF text layer and flag documents needing OCR`

Ordering rationale: 1–3 build the net; 4–5 fix the contracts everything else depends on; 6–7 are the refactors that must precede feature growth (CLAUDE.md's own rule); 8–10 are correctness improvements that are safe *because* 1–7 exist. The LLM extractor (§5.3) starts as task 11 — after this list, it's a one-module addition instead of a gamble.

---

## 9. Strategic advice

**Is the architecture heading the right direction?** Yes — with one caveat. The instincts (deterministic first, eval harness, review tri-state, scope discipline) are genuinely above-average; most people build the demo first and the measurement never. The caveat: you are one or two more fixtures away from the regex treadmill consuming all your momentum. The stop-label structure is already showing fixture-specific artifacts. Recognize the current phase's exit condition: regex has done its job — it forced you to build parsers, boundaries, and an eval harness. Its ceiling is the signal to move, not a bug to fix with more regex.

**Most valuable version of this product:** not "extract fields from permits" — extraction is becoming a commodity. The durable value is the *judgment layer*: deterministic, code-cited, jurisdiction-aware rule checking with an audit trail, wrapped around whatever extraction backend is current. Two buyers care: solar installers who want pre-submission checks ("this packet will bounce because the 120% rule fails") and AHJs who want intake triage. The ROADMAP's permit-vs-approval reconciliation is exactly the right differentiator — nobody's regex demo does that. Your rule library + correction dataset + eval harness compound over time; prompts don't.

**Stop doing:** hand-tuning stop labels per fixture; chasing 100% on the fixture gate; writing docs ahead of implementation (three docs currently describe features that don't exist — in a repo whose brand is honesty, drift is the one unforgivable sin); adding fields (pause Phase 2's tail until tasks 1–7 land).

**Double down on:** the evaluation harness (it's your license to adopt AI safely and your demo artifact); the failure log (entry #9 is the most convincing thing in the repo — an investor or hiring manager reads that and believes you); the REVIEW_REQUIRED loop (turn it into stored corrections — that's proprietary training data); corpus growth (30 messy real documents beat any architecture change for making this credible).

**What impresses users, investors, or agencies:** one honest table — "N real permit documents, per-field precision/recall, failure taxonomy, and here's the flagged-for-review queue with the exact source quote for every extracted value." Agencies in particular buy *auditability*, not accuracy claims: "every value cites its page and quote; every rule explains itself; every human correction is recorded" is a government-sales sentence. You are architecturally closer to being able to say that sentence than most funded startups in this space; §8 tasks 4–5 plus §5.3's span-verification make it literally true.

**What keeps this maintainable solo:** exactly what you're doing, plus the safety net you're missing. Small deps, boring code, one FieldSpec table instead of four dicts, CI that runs your regression on every push so future-you (or future-Claude-session) can't silently break past-you's work. The biggest solo-maintainer risk in this repo today isn't complexity — it's that the entire verification system lives untracked on one machine. Fix that first; everything else is compounding from a safe base.
