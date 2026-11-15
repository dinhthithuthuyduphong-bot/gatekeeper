"""Section 39 B: analysis registered in kaggle/preregistration_s39.md (0 USD, after the runs).

For each auditor, with the decision parsed by section 19 C's parse (scripts/sham_audit.py) and an
unparsed reply counted as "not attributed" (as scripts/make_numbers.py counts the paper's rows):
  sham_k / 25   sham skill blamed, with a Clopper-Pearson 95% interval;
  plain_k / 25  the same placebo pairs, no skill named;
  real share    attributed among the 52 real pairs, and the paper's misattribution lower bound
                max(0, share - U), U = the 95% task-cluster upper bound of section 21
                (results/section21.json, P_A.upper95_task_cluster).

  python kaggle/scripts/b39_analyse.py --prompts <b39_prompts.jsonl.gz> \
      --results kaggle/results/b39_results_*.jsonl --out kaggle/results/b39_analysis.json
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
from pathlib import Path

from scipy.stats import beta

# Note 39-2 (registered after 5 of 339 replies of session 1 were seen to fail parse, before any
# count was computed): a secondary reading takes "attributed": true/false from an unparsed reply.
LENIENT = re.compile(r'"attributed"\s*:\s*(true|false)', re.IGNORECASE)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from sham_audit import parse  # noqa: E402


def cp95(k: int, n: int) -> list[float]:
    lo = float(beta.ppf(0.025, k, n - k + 1)) if k > 0 else 0.0
    hi = float(beta.ppf(0.975, k + 1, n - k)) if k < n else 1.0
    return [lo, hi]


def decide(text: str, lenient: bool) -> tuple[bool, bool]:
    """(attributed, parsed) by section 19 C's parse; lenient also reads LENIENT if that fails."""
    d = parse(text)
    if d is not None:
        return bool(d.get("attributed")), True
    m = LENIENT.search(text or "") if lenient else None
    return (m is not None and m.group(1).lower() == "true"), False


def analyse(prompts: list[dict], results: list[dict], upper: float, lenient: bool) -> dict:
    cond = {p["sha256"]: p["condition"] for p in prompts}
    out = {"U": upper, "auditors": {}}
    for m in sorted({r["model"] for r in results}):
        rows = [r for r in results if r["model"] == m and r.get("ok")]
        att: dict[str, list[bool]] = {"real": [], "sham": [], "plain": []}
        unparsed = 0
        for r in rows:
            a, parsed = decide(r["response"], lenient)
            unparsed += not parsed
            att[cond[r["sha256"]]].append(a)
        e = {"n_ok": len(rows), "unparsed": unparsed}
        for c in ("sham", "plain"):
            k, n = sum(att[c]), len(att[c])
            e[c] = {"k": k, "n": n, "cp95": cp95(k, n) if n else None}
        n = len(att["real"])
        share = sum(att["real"]) / n if n else None
        e["real"] = {
            "k": sum(att["real"]),
            "n": n,
            "share": share,
            "lower_bound": max(0.0, share - upper) if n else None,
        }
        out["auditors"][m] = e
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts", required=True, type=Path)
    ap.add_argument("--results", required=True, type=Path, nargs="+")
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    prompts = [json.loads(x) for x in gzip.open(a.prompts, "rt")]
    results = [json.loads(x) for f in a.results for x in f.read_text().splitlines() if x.strip()]
    s21 = json.loads((ROOT / "results" / "section21.json").read_text())
    u = s21["P_A"]["upper95_task_cluster"]
    res = {
        "primary": analyse(prompts, results, u, lenient=False),
        "secondary_lenient_parse": analyse(prompts, results, u, lenient=True),
    }
    a.out.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
