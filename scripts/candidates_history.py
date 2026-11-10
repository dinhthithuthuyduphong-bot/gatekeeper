"""History rule of section 29 applied to every candidate of a gskill learning run (0 USD).

  python scripts/candidates_history.py --tar <tag>_learn_run.tar.gz \
      --out results/<tag>_candidates_history.json

Per candidate (GEPA order): bytes and the number of lines matching scripts/make_ablation.RULE.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from s30_analysis import candidates, history_lines  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tar", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    rows = [
        {"candidate": i, "bytes": len(c.encode()), "history_lines": history_lines(c)}
        for i, c in enumerate(candidates(a.tar))
    ]
    out = {
        "candidates": len(rows),
        "nonempty": sum(r["bytes"] > 0 for r in rows),
        "with_history_line": sum(r["history_lines"] > 0 for r in rows),
        "first_with_history_line": next((r["candidate"] for r in rows if r["history_lines"]), None),
        "rows": rows,
    }
    a.out.write_text(json.dumps(out, indent=1) + "\n")
    print({k: v for k, v in out.items() if k != "rows"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
