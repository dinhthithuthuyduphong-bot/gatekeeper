"""Tasks of a batched stage that are NOT done yet (python scripts/missing_tasks.py NAME TASKS_FROM).

Same rule as the batch driver's resume (run_batched_pilot.done_tasks): a task with an
infrastructure failure in any arm is not done. Counting the merged file's "instances" instead
would call a seed complete while infra-failed pairs are missing. Prints the count; exit 0."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_batched_pilot import RESULTS, done_tasks, task_list  # noqa: E402


def main() -> int:
    name, tasks_from = sys.argv[1], sys.argv[2]
    parts = sorted(RESULTS.glob(f"{name}-p[0-9][0-9].json"))
    missing = [t for t in task_list(tasks_from, []) if t not in done_tasks(parts)]
    print(len(missing))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
