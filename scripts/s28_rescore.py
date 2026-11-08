"""Section 28m step 2: rescore the saved agent patches of results/s28_manifest.json.gz (0 USD).

  python scripts/s28_rescore.py --rows a.jsonl b.jsonl --live-python ... --verified-python ... \
      --shard K --of N

Run on a GitHub runner (evaluation containers with full network, execution note 28m-1). This shard
takes the instances sorted by name at positions K, K+N, ...; each image is pulled once and
removed afterwards. Each patch is scored once under a fresh run id. Writes
results/s28_rescored_k<K>.json (resumable).
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gold_rescore import drop_image, failures  # noqa: E402
from run_pilot import image_name, prepull  # noqa: E402

from gatekeeper.harness import read_report, run_harness  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", nargs="+", type=Path, required=True)
    ap.add_argument("--live-python", required=True)
    ap.add_argument("--verified-python", required=True)
    ap.add_argument("--shard", type=int, required=True)
    ap.add_argument("--of", type=int, required=True)
    ap.add_argument("--manifest", type=Path, default=Path("results/s28_manifest.json.gz"))
    ap.add_argument("--out-dir", type=Path, default=Path("results"))
    a = ap.parse_args()
    rows, src = {}, {}
    for f in a.rows:
        for line in f.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                rows.setdefault(r["instance_id"], r)
                src.setdefault(r["instance_id"], f)
    with gzip.open(a.manifest, "rt") as fh:
        entries = json.load(fh)["entries"]
    iids = sorted({e["iid"] for e in entries})[a.shard :: a.of]
    out_f = a.out_dir / f"s28_rescored_k{a.shard}.json"
    out = json.loads(out_f.read_text()) if out_f.exists() else {}
    work = Path("runs/s28")
    work.mkdir(parents=True, exist_ok=True)
    for iid in iids:
        mine = [e for e in entries if e["iid"] == iid]
        todo = [e for e in mine if f"{e['exp']}|{e['name']}|{e['arm']}|{iid}" not in out]
        if not todo:
            continue
        row = rows[iid]
        live = (row.get("image") or "").startswith("starryzhang/")
        failed = prepull([row])
        for k, e in enumerate(todo):
            key = f"{e['exp']}|{e['name']}|{e['arm']}|{iid}"
            if failed:
                out[key] = {"error": f"image pull failed: {failed}"}
                continue
            preds = work / f"{iid}-{k}.json"
            preds.write_text(
                json.dumps(
                    {
                        iid: {
                            "model_name_or_path": "agent",
                            "instance_id": iid,
                            "model_patch": e["patch"],
                        }
                    }
                )
            )
            rid = f"s28-{iid}-{k}-{time.strftime('%Y%m%dT%H%M%S')}"
            kw = (
                {"namespace": "starryzhang", "python": a.live_python}
                if live
                else {"python": a.verified_python}
            )
            try:
                run_harness(str(preds), [iid], rid, 1, dataset=str(src[iid]), **kw)
            except SystemExit as exc:
                print(f"harness error {rid}: {exc}", flush=True)
            out[key] = {"run_id": rid, **failures(read_report(rid, "", iid))}
            out_f.write_text(json.dumps(out, indent=1) + "\n")
        print(f"[s28] {iid}: {len(todo)} patches", flush=True)
        drop_image(image_name(row))
    out_f.write_text(json.dumps(out, indent=1) + "\n")
    print("[s28] done", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
