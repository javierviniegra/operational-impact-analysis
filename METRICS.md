---

## ✅ `CONTRIBUTING.md` (English, Markdown)

```markdown
# Contributing Guidelines

This repository is designed to be auditable and reproducible.
Contributions should preserve KPI parity with Power BI definitions and maintain the Totals vs Subtotals methodology.

---

## 1. Principles

- Do not commit credentials or sensitive data.
- Do not change KPI definitions without updating `METRICS.md`.
- Keep notebooks narrative-focused; place reusable logic in `src/`.
- All KPI calculations must be reproducible and validated.

---

## 2. Branching Strategy

Recommended branches:
- `main` (stable, validated outputs)
- `dev` (active development)
- `feature/<short-feature-name>` (new features)

---

## 3. Commit Messages

Use clear English commit messages, for example:
- `Initialize project documentation and structure`
- `Add purchases extraction (invoice-only inputs)`
- `Implement KPI: Cost of Cancellations`

---

## 4. Adding a New KPI

1. Add the KPI definition to `METRICS.md` (include DAX and tables).
2. Implement Python function in `src/transform/financial_kpis.py`.
3. Validate output matches Power BI for at least one known period.
4. Document any known edge cases.

---

## 5. Notebook Standards

- Use numbered notebooks to reflect the pipeline.
- Include a short executive summary at the top.
- Avoid embedding secrets or raw data exports in notebooks.

---

## 6. Output Rules

- Generated files go to `output/` and are not committed.
- Charts saved to `output/figures/`.
- Datasets saved to `output/datasets/`.

---

## 7. Code Style

- Keep functions small and explicit.
- Prefer clear naming over cleverness.
- Add docstrings for KPI functions, including VAT basis and filters.