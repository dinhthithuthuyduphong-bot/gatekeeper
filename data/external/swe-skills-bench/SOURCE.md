# SWE-Skills-Bench paired results (external data)

- Source: https://github.com/ControllableModel/SWE-Skills-Bench, file `results/final_results/ALL_combined_cells.csv`
- Commit: `4d3450d9216a590a8726fcb3604b5143daca776b` (2026-10-16)
- Paper: arXiv:2603.15401 (v2)
- License: MIT (copy in `LICENSE`, © 2026 Yi Zhang)
- Content: 3,920 rows = 4 agent×model configurations × 98 skills × 10 requirements; pass rate (%) on hidden tests without (`none`) and with (`one`) the skill.

**Use in this project:** only as *external pilot data* to estimate variance components, effect-size
distributions and context dependence (TODO.md Phase 3). It is **not** the evaluation benchmark
(TODO.md R13): tasks are requirement documents with hidden tests, skills are `SKILL.md` documents,
and the paper is a preprint. Loss here is `1 - pass_rate/100` (no PASS_TO_PASS split, so R = 0).
