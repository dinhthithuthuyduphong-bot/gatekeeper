"""Verify cited works against arXiv and DBLP (TODO.md Phase 7 'Kiem tra tung trich dan').

The draft's 2026 preprints carry placeholder authors ("GSE Authors", ...). For each arXiv id we
fetch the real title, authors and first-version date; for peer-reviewed benchmarks we ask DBLP
for the venue. Runs in GitHub Actions; writes data/citations.json.
"""

from __future__ import annotations

import difflib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

# (key used in the paper / TODO, arXiv id, title the draft attributes, placeholder in refs?)
ARXIV = [
    # titles exactly as printed in the draft's reference list (docs/02-...reading-list.pdf)
    (
        "LTT [1]",
        "2110.01052",
        "Learn then test: Calibrating predictive algorithms to achieve risk control",
        False,
    ),
    (
        "CooperBench [6]",
        "2601.13295",
        "CooperBench: Measuring collaborative conflicts between coding agents",
        True,
    ),
    (
        "Formal skill verification [7]",
        "2605.23951",
        "Formal verification of learned agent skills and capability containment",
        True,
    ),
    (
        "GEM/MemState [8]",
        "2605.26252",
        "GEM/MemState: Dependency-aware correctness for agent memory",
        True,
    ),
    ("GSE [9]", "2608.06153", "GSE: Globally reusable skill evolution for coding agents", True),
    (
        "MemCoder [12]",
        "2603.13258",
        "MemCoder: Structured intent-to-code experience memory for coding agents",
        True,
    ),
    (
        "MemGovern [13]",
        "2601.06789",
        "MemGovern: Governed development histories as reusable experience cards",
        True,
    ),
    (
        "SWE-bench-Live [22]",
        "2505.23419",
        "SWE-bench-Live: A continuously updated benchmark for LLM-based software engineering",
        False,
    ),
    ("XRepoSkill", "2609.36807", "XRepoSkill", False),
    ("SWE-Skills-Bench", "2603.15401", "SWE-Skills-Bench", False),
    ("ASI", "2504.06821", "Inducing programmatic skills", False),
    ("CODESKILL", "2605.25430", "CODESKILL", False),
    ("Hierarchical Skill Evolution", "2610.35616", "Hierarchical skill evolution", False),
    ("SWE-bench", "2310.06770", "SWE-bench", False),
    ("SWE-Gym", "2412.21139", "SWE-Gym", False),
    ("SWE-smith", "2504.21798", "SWE-smith", False),
]
DBLP_TITLES = {
    "SWE-bench": "SWE-bench: Can Language Models Resolve Real-world Github Issues?",
    "SWE-Gym": "Training Software Engineering Agents and Verifiers with SWE-Gym",
    "SWE-smith": "SWE-smith: Scaling Data for Software Engineering Agents",
    "SWE-bench-Live": "SWE-bench Goes Live!",
    "BugsInPy": "BugsInPy: a database of existing bugs in Python programs",
    "Betting CS": "Estimating means of bounded random variables by betting",
    "Conformal risk control": "Conformal Risk Control",
    "OpenHands": "OpenHands: An Open Platform for AI Software Developers as Generalist Agents",
}
NS = {"a": "http://www.w3.org/2005/Atom"}
UA = {"User-Agent": "gatekeeper-citation-check/0.1 (research; GitHub Actions)"}


def _get(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def arxiv_lookup(ids: list[str]) -> dict[str, dict]:
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(
        {"id_list": ",".join(ids), "max_results": len(ids)}
    )
    root = ET.fromstring(_get(url, 60))
    out = {}
    for e in root.findall("a:entry", NS):
        aid = e.findtext("a:id", "", NS).rsplit("/", 1)[-1]
        base = aid.split("v")[0]
        title = " ".join((e.findtext("a:title", "", NS) or "").split())
        if not title or title.lower() == "error":
            continue
        out[base] = {
            "arxiv_id": aid,
            "title": title,
            "authors": [a.findtext("a:name", "", NS) for a in e.findall("a:author", NS)],
            "published": (e.findtext("a:published", "", NS) or "")[:10],
            "updated": (e.findtext("a:updated", "", NS) or "")[:10],
        }
    return out


def title_similarity(a: str, b: str) -> float:
    norm = lambda t: re.sub(r"[^a-z0-9 ]", " ", t.lower()).split()  # noqa: E731
    return round(difflib.SequenceMatcher(None, norm(a), norm(b)).ratio(), 3)


DBLP_MIRRORS = ("https://dblp.org", "https://dblp.uni-trier.de", "https://dblp.dagstuhl.de")


def dblp_lookup(title: str) -> list[dict]:
    q = urllib.parse.urlencode({"q": title, "format": "json", "h": 5})
    errors = []
    for base in DBLP_MIRRORS:
        try:
            raw = _get(f"{base}/search/publ/api?{q}")
            data = json.loads(raw)
            break
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{base}: {type(exc).__name__}: {str(exc)[:120]}")
            time.sleep(2)
    else:
        raise RuntimeError("; ".join(errors))
    hits = data.get("result", {}).get("hits", {}).get("hit", [])
    return [
        {
            "title": h["info"].get("title"),
            "venue": h["info"].get("venue"),
            "year": h["info"].get("year"),
            "type": h["info"].get("type"),
        }
        for h in hits
    ]


def s2_lookup(title: str) -> list[dict]:
    """Semantic Scholar fallback for the venue of a title."""
    q = urllib.parse.urlencode(
        {"query": title, "limit": 3, "fields": "title,venue,year,publicationVenue,externalIds"}
    )
    data = json.loads(_get(f"https://api.semanticscholar.org/graph/v1/paper/search?{q}"))
    return [
        {
            "title": d.get("title"),
            "venue": d.get("venue") or (d.get("publicationVenue") or {}).get("name"),
            "year": d.get("year"),
            "type": "semantic-scholar",
        }
        for d in data.get("data", [])
    ]


def main() -> int:
    result: dict = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    try:
        found = arxiv_lookup([a[1] for a in ARXIV])
        result["arxiv_status"] = "ok"
    except Exception as exc:  # noqa: BLE001
        found = {}
        result["arxiv_status"] = f"failed: {exc!r}"
    rows = []
    for key, aid, draft_title, placeholder in ARXIV:
        rec = found.get(aid)
        rows.append(
            {
                "key": key,
                "arxiv_id": aid,
                "draft_title": draft_title,
                "draft_uses_placeholder_authors": placeholder,
                "exists_on_arxiv": rec is not None,
                "title_similarity": title_similarity(draft_title, rec["title"]) if rec else None,
                **(rec or {}),
            }
        )
    result["arxiv"] = rows
    dblp = {}
    for k, t in DBLP_TITLES.items():
        try:
            dblp[k] = dblp_lookup(t)
        except Exception as exc:  # noqa: BLE001
            try:
                dblp[k] = s2_lookup(t) or [{"error": f"dblp failed ({exc}); s2: no hit"}]
            except Exception as exc2:  # noqa: BLE001
                dblp[k] = [{"error": f"dblp: {exc}; s2: {exc2!r}"}]
        time.sleep(3)  # be polite
    result["dblp"] = dblp
    Path("data").mkdir(exist_ok=True)
    Path("data/citations.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    for r in rows:
        print(
            f"{r['key']:<32} {r['arxiv_id']}  exists={r['exists_on_arxiv']}  "
            f"{r.get('title', '')[:70]}"
        )
    for k, v in dblp.items():
        print(f"DBLP {k}: {[(h.get('venue'), h.get('year')) for h in v[:3]]}")
    return 0 if result["arxiv_status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
