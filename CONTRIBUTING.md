# Contributing

Thank you for contributing to Operational Impact Analysis.

This project is designed for reproducibility, traceability, and executive-level decision-making.  
All contributions must follow strict technical, analytical, and documentation standards.

---

## 1. Development Workflow

1. Create a new branch:
git checkout -b feat/<short-description>

2. Keep changes focused and minimal

3. Validate the pipeline:
python -m scripts.validate_all

4. Generate outputs to verify integrity:
python -m scripts.generate_dg_presentation_pro_es
python -m scripts.generate_executive_word_es

5. Open a Pull Request including:
- What changed
- Why it changed
- Evidence (outputs, logs, screenshots)

---

## 2. Project Structure Rules

Maintain strict separation of responsibilities:

- src/extract/ → data extraction (databases, connectors)
- src/transform/ → transformations (pure logic, KPIs, reconciliation)
- scripts/ → execution layer (orchestration)
- config/ → business rules and mappings
- docs/ → reference materials and documentation

---

## 3. Coding Standards

### Python

- Use pure functions whenever possible
- Avoid hidden side effects
- Explicit numeric conversion using pd.to_numeric
- Explicit datetime parsing
- Handle missing values defensively
- Keep functions small and readable

---

## 4. Documentation Rules (STRICT)

- All documentation must be:
  - Written in English
  - Structured in Markdown
- Do not mix languages
- Maintain professional tone

---

## 5. Commit Convention

Use standard prefixes:

- feat: new feature
- fix: bug fix
- docs: documentation changes
- refactor: code improvement
- test: validation logic

Examples:

feat: add waiter performance quadrant analysis  
fix: correct branch normalization before reconciliation  
docs: update methodology and KPI definitions

---

## 6. Validation Requirements

Before merging any change:

Run:

python -m scripts.validate_all  
python -m scripts.generate_dg_presentation_pro_es  
python -m scripts.generate_executive_word_es  

Ensure:

- No runtime errors
- Outputs are generated correctly
- Reconciliation results are consistent

---

## 7. Data Integrity Rules

- NEVER modify raw source data
- ALWAYS validate transformations end-to-end
- Reconciliation must be executed before reporting
- Do not bypass validation scripts

---

## 8. Adding New Metrics

1. Implement in src/transform/  
2. Document in METRICS.md  
3. Validate using scripts/validate_all.py  

---

## 9. Business Rules

- Must be defined in config/
- Must NOT be hardcoded in transformation logic

Examples:
- Branch normalization
- System migration flags
- Data exclusions

---

## 10. Security & Data Protection

- NEVER commit .env
- NEVER commit raw production exports
- /output/ must be ignored
- Do not expose sensitive data in logs

---

## 11. General Principle

This project is built for:

- Executive reporting (DG level)
- Data-driven decision making
- Full reproducibility

If a change improves:
- clarity
- traceability
- reliability

→ it is aligned with the project.