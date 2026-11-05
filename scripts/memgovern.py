"""MemGovern cell of the main experiment (docs/preregistration_main_draft.md sections 11d, 11e).

Uses MemGovern's OWN code and data at the pinned commit (QuantaAlpha/MemGovern@a845658): its
experience cards, its ChromaDB index, its embedding model and its retrieval server
(tools/experience_server.py) and agent tools (exp_search / exp_read). The repository has no LICENSE
file, so nothing of it is copied here: the workflow clones it, and this script imports its server.

The only change: cards from repositories of the cell's tasks are removed from the server's
collection and card table (no dates in the cards, so this is the leakage control; MemGovern's card
prompt itself targets "semantically similar issues across different repositories"). Search still
returns the number of results asked for.

  serve    run MemGovern's server with the filter (original arm: the agent calls the tools)
  static   B-M: one retrieval per task with the issue text, top_k cards -> guidance file
  orig     guidance file for the original arm: MemGovern's own retrieval step and tool docs
  check    feasibility check F1 on a static guidance sidecar
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

PINNED = "a8456580a4a6ea8de04755e958875cd549f43845"


def repo_of_instance(instance_id: str) -> str:
    """SWE-bench / SWE-bench-Live instance id 'owner__name-123' -> 'owner/name' (lower case)."""
    m = re.fullmatch(r"(.+?)__(.+)-\d+", instance_id)
    if not m:
        raise ValueError(f"not a SWE-bench instance id: {instance_id!r}")
    return f"{m.group(1)}/{m.group(2)}".lower()


def excluded_repos(instance_ids: Iterable[str]) -> set[str]:
    return {repo_of_instance(i) for i in instance_ids}


def filter_cards(cards: Mapping[str, Mapping[str, Any]], excluded: set[str]) -> dict:
    """Card table without cards of excluded repositories (case-insensitive)."""
    return {k: v for k, v in cards.items() if str(v.get("repo", "")).lower() not in excluded}


class FilteredCollection:
    """Wraps MemGovern's ChromaDB collection: query() drops results whose card is not in `kept`
    (the filtered card table; unknown ids are dropped too) and widens the request until
    `n_results` kept results are found or the collection is exhausted."""

    def __init__(self, inner: Any, kept: Mapping[str, Any]):
        self.inner = inner
        self.kept = kept

    def count(self) -> int:
        return self.inner.count()

    def query(self, query_texts: list[str], n_results: int, **kw: Any) -> dict:
        if len(query_texts) != 1:
            raise ValueError("MemGovern's server sends one query at a time")
        total = self.inner.count()
        ask = n_results
        while True:
            r = self.inner.query(query_texts=query_texts, n_results=min(ask, total), **kw)
            keep = [i for i, d in enumerate(r["ids"][0]) if d in self.kept]
            if len(keep) >= n_results or ask >= total:
                keep = keep[:n_results]
                return {
                    k: [[v[0][i] for i in keep]]
                    if isinstance(v, list) and v and v[0] is not None
                    else v
                    for k, v in r.items()
                }
            ask *= 4


def load_server(mg_root: Path, instance_ids: list[str]):
    """Import MemGovern's server module, initialise it, and install the filter."""
    data = mg_root / "data" / "agentic_exp_data_1220_13w_DSnewPrompt"
    os.environ.setdefault("DB_DIR", str(data / "chroma_db_experience"))
    os.environ.setdefault("JSON_DATA_PATH", str(data / "experience_data.json"))
    if "MODEL_PATH" not in os.environ:
        raise SystemExit("set MODEL_PATH to the local Qwen3-Embedding-0.6B snapshot")
    sys.path.insert(0, str(mg_root / "tools"))
    import experience_server as es  # MemGovern's own server (not copied here)

    if not es.init_service():
        raise SystemExit("MemGovern server failed to initialise")
    excl = excluded_repos(instance_ids)
    n0 = len(es.experience_data)
    es.experience_data = filter_cards(es.experience_data, excl)
    es.collection = FilteredCollection(es.collection, es.experience_data)
    print(f"[memgovern] cards {n0} -> {len(es.experience_data)} after excluding {len(excl)} repos")
    warm_up(es)
    return es


def warm_up(es) -> None:
    """MemGovern's exp_search client waits 10 s (urllib timeout=10 in exp_search.py). The embedding
    model loads in bfloat16, which is slow on CPU, and the first query is slower still: cast to
    float32 when the model is reachable, and run one query before the server answers /health."""
    import time

    emb = getattr(es.collection.inner, "_embedding_function", None)
    model = getattr(emb, "model", None)
    if model is not None and hasattr(model, "float"):
        emb.model = model.float()
        print("[memgovern] embedding model cast to float32")
    t0 = time.time()
    es.collection.query(query_texts=["warm-up query"], n_results=10)
    print(f"[memgovern] warm-up query {time.time() - t0:.1f} s")


def card_text(card: Mapping[str, Any]) -> str:
    return (
        f"Bug: {card.get('bug_description', '')}\nFix experience: {card.get('fix_experience', '')}"
    )


def static_guidance(es: Any, rows: list[dict], top_k: int) -> tuple[dict, dict]:
    """B-M: query = issue text, top_k cards per task. Returns ({id: text}, {id: [card ids]})."""
    text, used = {}, {}
    for r in rows:
        res = es.collection.query(query_texts=[r["problem_statement"]], n_results=top_k)
        ids = list(res["ids"][0])
        used[r["instance_id"]] = ids
        body = "\n\n".join(
            f"[{n}] {card_text(es.experience_data[i])}" for n, i in enumerate(ids, 1)
        )
        text[r["instance_id"]] = f"Past bug-fix experiences retrieved for this issue:\n\n{body}"
    return text, used


def orig_instructions(mg_root: Path) -> str:
    """MemGovern's retrieval step from its agent config and the docstrings of its two tools."""
    cfg = (mg_root / "config" / "dsv31t_agenticMemSearch_1220_13w.yaml").read_text()
    start = cfg.index("3. **Search and Retrieve Experience")
    end = cfg.index("4. Edit the sourcecode", start)
    step = "\n".join(line.strip() for line in cfg[start:end].strip().splitlines())
    import yaml

    docs = []
    for tool in ("exp_search", "exp_read"):
        spec = yaml.safe_load((mg_root / "tools" / tool / "config.yaml").read_text())["tools"]
        for name, t in spec.items():
            docs.append(f"`{t.get('signature', name)}`: {str(t.get('docstring', '')).strip()}")
    return step + "\n\nTools (shell commands):\n" + "\n".join(docs)


def check_static(
    used: Mapping[str, list[str]], cards: Mapping[str, Any], ids: list[str], top_k: int
) -> list[str]:
    """F1: every task has exactly top_k cards, all known and from no repository of the cell."""
    bad = []
    excl = excluded_repos(ids)
    for i in ids:
        got = used.get(i, [])
        if len(got) != top_k:
            bad.append(f"{i}: {len(got)} cards")
        for c in got:
            if c not in cards:
                bad.append(f"{i}: unknown card {c}")
            elif str(cards[c].get("repo", "")).lower() in excl:
                bad.append(f"{i}: card {c} from a repository of the cell")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["serve", "static", "orig", "check"])
    ap.add_argument("--mg-root", type=Path, required=True)
    ap.add_argument("--ids", type=Path, required=True, help='JSON {"instances": [...]}: the cell')
    ap.add_argument("--rows", type=Path, help="JSONL task rows (static)")
    ap.add_argument("--top-k", type=int, help="static: cards per task (no default, section 11d)")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--port", type=int)
    a = ap.parse_args()
    ids = json.loads(a.ids.read_text())["instances"]
    if a.cmd == "orig":
        text = orig_instructions(a.mg_root)
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps({i: text for i in ids}, indent=1))
        print(f"[memgovern] original-arm instructions: {len(text)} chars for {len(ids)} tasks")
        return 0
    if a.cmd == "check":
        used = json.loads(a.out.with_suffix(".cards.json").read_text())
        data = a.mg_root / "data" / "agentic_exp_data_1220_13w_DSnewPrompt" / "experience_data.json"
        bad = check_static(used, json.loads(data.read_text()), ids, a.top_k)
        print(f"[F1] {len(ids)} tasks, {len(bad)} problems")
        for b in bad[:20]:
            print("  ", b)
        return 1 if bad else 0
    es = load_server(a.mg_root, ids)
    if a.cmd == "serve":
        es.app.run(host="0.0.0.0", port=a.port)
        return 0
    if a.top_k is None:
        raise SystemExit("--top-k is required (no default)")
    want = set(ids)
    rows = [json.loads(x) for x in a.rows.read_text().splitlines() if x.strip()]
    rows = [r for r in rows if r["instance_id"] in want]
    if len(rows) != len(want):
        raise SystemExit(f"rows for {len(rows)} of {len(want)} tasks")
    text, used = static_guidance(es, rows, a.top_k)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(text, indent=1))
    a.out.with_suffix(".cards.json").write_text(json.dumps(used, indent=1))
    print(f"[memgovern] B-M guidance for {len(text)} tasks, top_k {a.top_k}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
