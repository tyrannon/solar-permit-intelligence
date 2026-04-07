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
