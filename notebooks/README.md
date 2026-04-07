# Notebooks

This directory contains Jupyter notebooks for exploratory analysis and prototyping.

## Guidelines

**Use notebooks for**:
- Initial data exploration
- Prototyping extraction logic
- Visualizing results and metrics
- Debugging specific documents
- One-off analyses

**Do NOT use notebooks for**:
- Production pipeline logic (belongs in `src/`)
- Code that needs to be version controlled carefully
- Anything that will be run repeatedly in production
- Complex business logic

## Philosophy

Notebooks are great for exploration and communication, but they're not the core of the system. Once a technique is proven in a notebook, it should be refactored into a proper Python module in `src/`.

This keeps the codebase testable, maintainable, and reviewable.

## Naming Convention

Use descriptive names with dates:
- `2026-04-07_initial_pdf_exploration.ipynb`
- `2026-04-10_ocr_quality_analysis.ipynb`
- `2026-04-15_field_extraction_prototype.ipynb`

This makes it easy to see what was explored and when.

## Sharing Notebooks

When committing notebooks:
- Clear all outputs before committing (avoid bloating git history)
- Add markdown cells explaining what you're doing and why
- Include enough context that someone else (or future you) can understand it

Consider using `jupyter nbconvert --clear-output` to strip outputs before committing.
