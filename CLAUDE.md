# CLAUDE.md

## Project Overview

This repository is a focused 30-day AI engineering MVP for solar permit document intelligence.

The goal is to build a small but real system that can:

1. ingest solar permit PDFs or images,
2. inspect and preprocess them,
3. classify page/document types,
4. extract a defined set of structured fields,
5. apply deterministic validation rules,
6. evaluate results against labeled ground truth,
7. document failure modes clearly.

This is a portfolio-grade MVP, not a production platform.

---

## Primary Objective

Build an end-to-end pipeline that demonstrates real AI engineering on messy real-world permit documents.

Success means:
- the pipeline works on a small dataset,
- outputs are structured and inspectable,
- rule checks are deterministic and understandable,
- performance is measured,
- failure modes are documented honestly.

Perfect accuracy is **not** required.

---

## Current Phase

We are in the early implementation phase.

Current priorities:
1. ingestion
2. inspection/debugging utilities
3. page-level understanding
4. field extraction
5. rule evaluation
6. labeled comparison and reporting

Do not skip ahead into advanced architecture before the current phase is working.

---

## Hard Constraints

- Python-first project
- Keep implementations small, readable, and grounded
- Prefer direct, legible code over abstractions
- No frontend/UI unless explicitly requested later
- No Docker unless explicitly requested later
- No cloud deployment unless explicitly requested later
- No database unless explicitly requested later
- No framework-heavy architecture
- No premature optimization
- No fake “enterprise-grade” language
- No pretending features exist when they do not

---

## Anti-Overengineering Rules

Do **not** introduce any of the following unless explicitly justified by a real current need:

- plugin systems
- registries
- dependency injection frameworks
- abstract base classes for future hypothetical components
- generalized pipeline orchestration frameworks
- excessive config layers
- microservices
- background job systems
- API layers before core logic works
- ML classifiers before keyword/rule-based inspection is exhausted for the current phase

Always prefer the smallest implementation that moves the project forward.

---

## Coding Principles

- Write code for a serious solo builder, not a large team
- Keep functions focused and easy to read
- Prefer explicit behavior over clever abstractions
- Add comments where reasoning matters
- Keep names concrete and literal
- Fail clearly with useful error messages
- Make outputs inspectable
- Keep file and module structure simple

When adding code:
- explain what changed,
- explain why,
- explain how to run it,
- list exact files changed.

---

## Python Execution Rule

For any command that runs project Python modules, do not guess between `python` and `python3`.

Always use the repo virtual environment interpreter directly:

```bash
./.venv/bin/python -m <module>
```

Examples:

```bash
# Ingestion
./.venv/bin/python -m src.ingestion.ingest_pdf data/raw/sample.pdf

# Inspection
./.venv/bin/python -m src.utils.inspect_processed data/processed/sample.json

# Extraction
./.venv/bin/python -m src.extraction.extract_candidates data/processed/sample.json

# Evaluation
./.venv/bin/python -m src.evaluation.evaluate_extraction \
  data/processed/sample.json \
  data/labeled/sample_truth.json
```

---

## Documentation Principles

Documentation should:
- reflect reality,
- stay concrete,
- avoid hype,
- avoid vague AI buzzwords,
- avoid claiming the system is more advanced than it is.

Prefer phrases like:
- “extract page text”
- “apply deterministic rules”
- “compare against labeled truth”
- “log likely failure modes”

Avoid phrases like:
- “enterprise-ready”
- “intelligent orchestration”
- “scalable AI platform”
- “production-grade” unless truly warranted

---

## Scope of v1

Target fields currently include:
- project_address
- jurisdiction
- contractor_name
- system_size_kw
- module_count
- module_model
- inverter_model
- main_service_panel_rating
- battery_present
- battery_model

Initial deterministic rules include:
- required core fields present
- battery consistency
- system size reasonableness
- module/system correlation
- service panel adequacy
- equipment models present
- address format check
- jurisdiction present

---

## Preferred Development Sequence

Use this order unless explicitly directed otherwise:

1. ingest one document reliably
2. create utilities to inspect processed output
3. identify page roles with simple heuristics
4. extract a small number of fields
5. validate extracted data with deterministic rules
6. compare outputs to labeled truth
7. document failure cases
8. iterate

Do not jump to later stages until earlier stages are functioning.

---

## Data Handling Rules

- Assume permit documents may contain sensitive or identifying information
- Do not commit sensitive raw documents unless they are clearly safe, redacted, public, or synthetic
- Prefer redacted or public sample files for anything that may become public in GitHub
- Keep generated intermediate artifacts understandable and easy to inspect

---

## When Making Suggestions

Suggestions should be:
- practical,
- minimal,
- tied to the current stage,
- biased toward execution over speculation.

If proposing a dependency:
- choose the smallest reasonable dependency,
- explain why it is needed now,
- avoid adding multiple packages at once without justification.

---

## Response Style for This Repo

When assisting in this repo:
- be concise but concrete,
- say what is implemented vs not implemented,
- call out assumptions,
- identify risks honestly,
- favor momentum over theory.

When asked to implement something, do not silently expand scope.

---

## Immediate Project Priority

The current top priority is to build a trustworthy document understanding pipeline starting from:
- PDF ingestion,
- processed JSON inspection,
- page-level heuristics,
before advancing to extraction and validation.

Protect momentum. Keep it real. Keep it small.

## Development Principles

- Work in small, well-defined truth slices
- Respect field dependencies (gating vs dependent fields)
- Do not invent data — return review on ambiguity
- Prioritize legibility over cleverness
- Always explain logic in plain English
- Include edge cases and test suggestions
- Preserve existing working behavior unless explicitly changing it

<!-- dgc-policy-v11 -->
# Dual-Graph Context Policy

This project uses a local dual-graph MCP server for efficient context retrieval.

## MANDATORY: Always follow this order

1. **Call `graph_continue` first** — before any file exploration, grep, or code reading.

2. **If `graph_continue` returns `needs_project=true`**: call `graph_scan` with the
   current project directory (`pwd`). Do NOT ask the user.

3. **If `graph_continue` returns `skip=true`**: project has fewer than 5 files.
   Do NOT do broad or recursive exploration. Read only specific files if their names
   are mentioned, or ask the user what to work on.

4. **Read `recommended_files`** using `graph_read` — **one call per file**.
   - `graph_read` accepts a single `file` parameter (string). Call it separately for each
     recommended file. Do NOT pass an array or batch multiple files into one call.
   - `recommended_files` may contain `file::symbol` entries (e.g. `src/auth.ts::handleLogin`).
     Pass them verbatim to `graph_read(file: "src/auth.ts::handleLogin")` — it reads only
     that symbol's lines, not the full file.
   - Example: if `recommended_files` is `["src/auth.ts::handleLogin", "src/db.ts"]`,
     call `graph_read(file: "src/auth.ts::handleLogin")` and `graph_read(file: "src/db.ts")`
     as two separate calls (they can be parallel).

5. **Check `confidence` and obey the caps strictly:**
   - `confidence=high` -> Stop. Do NOT grep or explore further.
   - `confidence=medium` -> If recommended files are insufficient, call `fallback_rg`
     at most `max_supplementary_greps` time(s) with specific terms, then `graph_read`
     at most `max_supplementary_files` additional file(s). Then stop.
   - `confidence=low` -> Call `fallback_rg` at most `max_supplementary_greps` time(s),
     then `graph_read` at most `max_supplementary_files` file(s). Then stop.

## Token Usage

A `token-counter` MCP is available for tracking live token usage.

- To check how many tokens a large file or text will cost **before** reading it:
  `count_tokens({text: "<content>"})`
- To log actual usage after a task completes (if the user asks):
  `log_usage({input_tokens: <est>, output_tokens: <est>, description: "<task>"})`
- To show the user their running session cost:
  `get_session_stats()`

Live dashboard URL is printed at startup next to "Token usage".

## Rules

- Do NOT use `rg`, `grep`, or bash file exploration before calling `graph_continue`.
- Do NOT do broad/recursive exploration at any confidence level.
- `max_supplementary_greps` and `max_supplementary_files` are hard caps - never exceed them.
- Do NOT dump full chat history.
- Do NOT call `graph_retrieve` more than once per turn.
- After edits, call `graph_register_edit` with the changed files. Use `file::symbol` notation (e.g. `src/auth.ts::handleLogin`) when the edit targets a specific function, class, or hook.

## Context Store

Whenever you make a decision, identify a task, note a next step, fact, or blocker during a conversation, call `graph_add_memory`.

**To add an entry:**
```
graph_add_memory(type="decision|task|next|fact|blocker", content="one sentence max 15 words", tags=["topic"], files=["relevant/file.ts"])
```

**Do NOT write context-store.json directly** — always use `graph_add_memory`. It applies pruning and keeps the store healthy.

**Rules:**
- Only log things worth remembering across sessions (not every minor detail)
- `content` must be under 15 words
- `files` lists the files this decision/task relates to (can be empty)
- Log immediately when the item arises — not at session end

## Session End

When the user signals they are done (e.g. "bye", "done", "wrap up", "end session"), proactively update `CONTEXT.md` in the project root with:
- **Current Task**: one sentence on what was being worked on
- **Key Decisions**: bullet list, max 3 items
- **Next Steps**: bullet list, max 3 items

Keep `CONTEXT.md` under 20 lines total. Do NOT summarize the full conversation — only what's needed to resume next session.
