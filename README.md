# stagewise-coding-agent-fragility

Study of stage-wise instruction fragility in lightweight coding agents.

## Overview

This repository is organized around a focused research question:

> How do approximately meaning-preserving prompt perturbations affect a multi-step coding agent across different stages of a test-repair loop?

The project studies a lightweight coding workflow instead of a heavy agent framework. The intended loop is:

1. Read a programming task
2. Generate code
3. Run tests
4. Build or perturb a failure summary
5. Repair the code
6. Repeat until success or a fixed round limit

The current documentation is centered in [`docs/`](./docs):

- [`docs/report_en.md`](./docs/report_en.md): main English report
- [`docs/related_work_expanded.md`](./docs/related_work_expanded.md): copied source document with expanded related work

## Repository Structure

```text
stagewise-coding-agent-fragility/
├── README.md
├── .gitignore
├── pyproject.toml
├── configs/
├── docs/
├── logs/
├── results/
├── scripts/
├── src/
│   └── stagewise_coding_agent_fragility/
└── tests/
```

## Notes

- `logs/` is for local experiment output and should not be committed by default.
- `results/` is intended for curated tables, figures, and case studies.
- `docs/related_work_expanded.md` is copied from the project workspace as requested.
