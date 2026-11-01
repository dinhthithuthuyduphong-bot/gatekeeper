"""Verify cited works against arXiv and DBLP (TODO.md Phase 7 'Kiem tra tung trich dan').

The draft's 2026 preprints carry placeholder authors ("GSE Authors", ...). For each arXiv id we
fetch the real title, authors and first-version date; for peer-reviewed benchmarks we ask DBLP
for the venue. Runs in GitHub Actions; writes data/citations.json.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

# (key used in the paper / TODO, arXiv id, title the draft attributes, placeholder in refs?)
ARXIV = [
    ("LTT [1]", "2110.01052", "Learn then test", False),
    ("CooperBench [6]", "2601.13295", "CooperBench", True),
    ("Formal skill verification [7]", "2605.23951", "Formal verification of agent skills", True),
    ("GEM/MemState [8]", "2605.26252", "GEM/MemState", True),
    ("GSE [9]", "2608.06153", "Globally reusable skills for coding agents", True),
    ("MemCoder [12]", "2603.13258", "MemCoder", True),
    ("MemGovern [13]", "2601.06789", "MemGovern", True),
    ("SWE-bench-Live [22]", "2505.23419", "SWE-bench-Live", False),
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


def dblp_lookup(title: str) -> list[dict]:
    url = "https://dblp.org/search/publ/api?" + urllib.parse.urlencode(
        {"q": title, "format": "json", "h": 5}
    )
    hits = json.loads(_get(url)).get("result", {}).get("hits", {}).get("hit", [])
    return [
        {
            "title": h["info"].get("title"),
            "venue": h["info"].get("venue"),
            "year": h["info"].get("year"),
            "type": h["info"].get("type"),
        }
        for h in hits
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
                **(rec or {}),
            }
        )
    result["arxiv"] = rows
    dblp = {}
    for k, t in DBLP_TITLES.items():
        try:
            dblp[k] = dblp_lookup(t)
        except Exception as exc:  # noqa: BLE001
            dblp[k] = [{"error": repr(exc)}]
        time.sleep(1.5)  # be polite to DBLP
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
